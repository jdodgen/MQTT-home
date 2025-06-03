# mqtt_as.py Asynchronous version of umqtt.robust
# (C) Copyright Peter Hinch 2017-2023.
# Released under the MIT licence.

# Pyboard D support added also RP2/default
# Various improvements contributed by Kevin Köck.
# added more error handling - Jim Dodgen
# now forked into a lite version. 
# Tested on ESP32-S2

import gc
import usocket as socket
import ustruct as struct

gc.collect()
from ubinascii import hexlify
import uasyncio as asyncio

gc.collect()
from utime import ticks_ms, ticks_diff, time
from uerrno import EINPROGRESS, ETIMEDOUT, ENOTCONN

gc.collect()
from micropython import const
from machine import unique_id, soft_reset
import network

gc.collect()
from sys import platform, maxsize

VERSION = (0, 7, 2)

# self.error values returned with .status()
# also used to cause error LED codes
ERROR_OK = 0
ERROR_AP_NOT_FOUND = 2
ERROR_BAD_PASSWORD = 3
ERROR_BROKER_LOOKUP_FAILED = 4
ERROR_BROKER_CONNECT_FAILED =  5
ERROR_IDLE = 6


# Default short delay for good SynCom throughput (avoid sleep(0) with SynCom).
_DEFAULT_MS = const(20)
_SOCKET_POLL_DELAY = const(20)  # 100ms added greatly to publish latency

# Legitimate errors while waiting on a socket. See uasyncio __init__.py open_connection().
ESP32 = platform == "esp32"
RP2 = platform == "rp2"
if ESP32:
    # https://forum.micropython.org/viewtopic.php?f=16&t=3608&p=20942#p20942
    BUSY_ERRORS = [EINPROGRESS, ETIMEDOUT, 118, 119, 116, -116]  # Add in weird ESP32 errors
elif RP2:
    BUSY_ERRORS = [EINPROGRESS, ETIMEDOUT, -110]
else:
    BUSY_ERRORS = [EINPROGRESS, ETIMEDOUT]

ESP8266 = platform == "esp8266"
PYBOARD = platform == "pyboard"

# this turns off the prints
do_prints = False
def turn_on_prints(flag):
    global do_prints
    do_prints=flag
    
# conditional print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    global do_prints
    if not do_prints:
        return # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    try:
        xprint("[mqtt_asl]", *args, **kwargs) # the copied real print
    except:
        raise ValueError("xprint problem ["+msg+"]")

# Default "do little" coro for optional user replacement
async def eliza(*_):  # e.g. via set_wifi_handler(coro): see test program
    await asyncio.sleep_ms(_DEFAULT_MS)

# Default problem_reporter
async def default_problem_reporter(error):
    try:
        xprint("default_problem_reporter",error)
    except:
        xprint("default_problem_reporter error broke")
    print("default_problem_reporter done")

class MsgQueue:
    def __init__(self, size):
        self._q = [0 for _ in range(max(size, 4))]
        self._size = size
        self._wi = 0
        self._ri = 0
        self._evt = asyncio.Event()
        self.discards = 0

    def put(self, *v):
        self._q[self._wi] = v
        self._evt.set()
        self._wi = (self._wi + 1) % self._size
        if self._wi == self._ri:  # Would indicate empty
            self._ri = (self._ri + 1) % self._size  # Discard a message
            self.discards += 1

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._ri == self._wi:  # Empty
            self._evt.clear()
            await self._evt.wait()
        r = self._q[self._ri]
        self._ri = (self._ri + 1) % self._size
        return r


config = {
    "client_id": hexlify(unique_id()),
    "server": None,
    "port": 0,
    "user": "",
    "password": "",
    "keepalive": 60,
    "ping_interval": 0,
    "ssl": False,
    "ssl_params": {},
    "response_time": 10,
    "clean_init": True,
    "clean": True,
    "max_repubs": 4,
    "will": None,
    "subs_cb": lambda *_: None,
    "wifi_coro": eliza,
    "connect_coro": eliza,
    "ssid": None,
    "wifi_pw": None,
    "queue_len": 0,
    "gateway" : False,
    "problem_reporter" : default_problem_reporter,
}

class MQTTException(Exception):
    pass


def pid_gen():
    pid = 0
    while True:
        pid = pid + 1 if pid < 65535 else 1
        yield pid


def qos_check(qos):
    if not (qos == 0 or qos == 1):
        raise ValueError("Only qos 0 and 1 are supported.")


# MQTT_base class. Handles MQTT protocol on the basis of a good connection.
# Exceptions from connectivity failures are handled by MQTTClient subclass.
class MQTT_base:
    REPUB_COUNT = 0  # TEST
    #DEBUG = False

    def __init__(self, config):
        self._events = config["queue_len"] > 0
        # MQTT config
        self._client_id = config["client_id"]
        self._user = config["user"]
        self._pswd = config["password"]
        self._problem_reporter = config["problem_reporter"]
        print("self._problem_reporter", self._problem_reporter)
        self._keepalive = config["keepalive"]
        if self._keepalive >= 65536:
            raise ValueError("invalid keepalive time")
        self._response_time = config["response_time"] * 1000  # Repub if no PUBACK received (ms).
        self._max_repubs = config["max_repubs"]
        self._clean_init = config["clean_init"]  # clean_session state on first connection
        self._clean = config["clean"]  # clean_session state on reconnect
        will = config["will"]
        if will is None:
            self._lw_topic = False
        else:
            self._set_last_will(*will)
        # WiFi config
        self._ssid = config["ssid"]  # Required for ESP32 / Pyboard D. Optional ESP8266
        self._wifi_pw = config["wifi_pw"]
        self._ssl = config["ssl"]
        self._ssl_params = config["ssl_params"]
        # Callbacks and coros
        if self._events:
            #self.up = asyncio.Event()
            #self.down = asyncio.Event()
            self.queue = MsgQueue(config["queue_len"])
        else:  # Callbacks
            self._cb = config["subs_cb"]
            self._user_wifi_handler = config["wifi_coro"]
            self._user_connect_handler = config["connect_coro"]
        # Network
        self.port = config["port"]
        if self.port == 0:
            self.port = 8883 if self._ssl else 1883
        self.server = config["server"]
        if self.server is None:
            raise ValueError("no server specified.")
        self._sock = None
        self._sta_if = network.WLAN(network.STA_IF)
        self._sta_if.active(True)
        self.newpid = pid_gen()
        self.rcv_pids = set()  # PUBACK and SUBACK pids awaiting ACK response
        self.last_rx = ticks_ms()  # Time of last communication from broker
        #
        self.sock_lock = asyncio.Lock()
        self.wifi_up = asyncio.Event()
        self.broker_connected = asyncio.Event()
        self.connection_lost = False
        self.last_pingresp = time()+1000

    def _set_last_will(self, topic, msg, retain=False, qos=0):
        qos_check(qos)
        if not topic:
            raise ValueError("Empty topic.")
        self._lw_topic = topic
        self._lw_msg = msg
        self._lw_qos = qos
        self._lw_retain = retain

    def _timeout(self, t):
        diff = ticks_diff(ticks_ms(), t)
        timed_out = diff > self._response_time
        #print ("_timeout timed_out[",timed_out,"] diff[", diff, "] start time[", t, "]")
        return timed_out

    async def _as_read(self, n, sock=None):  # OSError caught by superclass
        if sock is None:
            sock = self._sock
        # Declare a byte array of size n. That space is needed anyway, better
        # to just 'allocate' it in one go instead of appending to an
        # existing object, this prevents reallocation and fragmentation.
        data = bytearray(n)
        buffer = memoryview(data)
        size = 0
        t = ticks_ms()
        while size < n:
            con = self.isconnected()
            time_out = self._timeout(t)
            print("_as_read isconnected[", con, "]timeout[", time_out,"]")
            if time_out or not con:
                print("_as_read timed out")
                raise OSError(-1, "Timeout on socket read")
            try:
                msg_size = sock.readinto(buffer[size:], n - size)
            except OSError as e:  # ESP32 issues weird 119 errors here
                print("_as_read error: ", e)
                msg_size = None
                if e.args[0] not in BUSY_ERRORS:
                    raise
            if msg_size == 0:  # Connection closed by host
                raise OSError(-1, "Connection closed by host")
            if msg_size is not None:  # data received
                size += msg_size
                t = ticks_ms()
                self.last_rx = ticks_ms()
            await asyncio.sleep_ms(_SOCKET_POLL_DELAY)
        return data

    async def _as_write(self, bytes_wr, length=0, sock=None):
        print("_as_write [", bytes_wr,"]")
        if sock is None:
            sock = self._sock
        # Wrap bytes in memoryview to avoid copying during slicing
        bytes_wr = memoryview(bytes_wr)
        if length:
            bytes_wr = bytes_wr[:length]
        t = ticks_ms()
        while bytes_wr:
            con = self.isconnected()
            time_out = self._timeout(t) 
            print("_as_write time_out[",time_out,"] isconnected()[",con,"] self._isconnected[",self._isconnected,"]")
            if time_out or not con: 
                raise OSError(-1, "Timeout on socket write")
            try:
                n = sock.write(bytes_wr)
                if not n:
                    raise
                print("_as_write  write returned ", n)
            except OSError as e:  # ESP32 issues weird 119 errors here
                n = 0
                
                if e.args[0] not in BUSY_ERRORS:
                    raise
            except Exception as e:
                print("_as_write sock.write() ---- failed:", e)
                pass

            if n:
                t = ticks_ms()
                bytes_wr = bytes_wr[n:]
            await asyncio.sleep(1)
            #await asyncio.sleep_ms(_SOCKET_POLL_DELAY)

    async def _send_str(self, s):
        await self._as_write(struct.pack("!H", len(s)))
        await self._as_write(s)

    async def _recv_len(self):
        n = 0
        sh = 0
        while 1:
            res = await self._as_read(1)
            b = res[0]
            n |= (b & 0x7F) << sh
            if not b & 0x80:
                return n
            sh += 7

    async def _broker_connect(self, clean):
        print("_broker_connect starting IP[",self._addr,"]" ) 
        self.error = 0
        try:
            self._sock.close()
        except:
            pass
        self._sock = socket.socket()
        self._sock.setblocking(False)
        self._sock.settimeout(10)
        try:
            self._sock.connect(self._addr)
        except OSError as e:
            print("_broker_connect exception %s " % (e.args[0]))
            if e.args[0] not in BUSY_ERRORS:
                raise
        await asyncio.sleep_ms(_DEFAULT_MS)
        print("_broker_connect socket created")
        if self._ssl:
            import ussl as ssl
            self._sock = ssl.wrap_socket(self._sock, **self._ssl_params)
        premsg = bytearray(b"\x10\0\0\0\0\0")
        msg = bytearray(b"\x04MQTT\x04\0\0\0")  # Protocol 3.1.1

        sz = 10 + 2 + len(self._client_id)
        msg[6] = clean << 1
        if self._user:
            sz += 2 + len(self._user) + 2 + len(self._pswd)
            msg[6] |= 0xC0
        if self._keepalive:
            msg[7] |= self._keepalive >> 8
            msg[8] |= self._keepalive & 0x00FF
        if self._lw_topic:
            sz += 2 + len(self._lw_topic) + 2 + len(self._lw_msg)
            msg[6] |= 0x4 | (self._lw_qos & 0x1) << 3 | (self._lw_qos & 0x2) << 3
            msg[6] |= self._lw_retain << 5

        i = 1
        while sz > 0x7F:
            premsg[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        premsg[i] = sz
        self._isconnected = True
        print("_broker_connect now doing write 1")
        await self._as_write(premsg, i + 2)
        print("_broker_connect now doing write 2")
        await self._as_write(msg)
        await self._send_str(self._client_id)
        print("_broker_connect now doing _lw_topic")
        if self._lw_topic:
            await self._send_str(self._lw_topic)
            await self._send_str(self._lw_msg)
        if self._user:
            await self._send_str(self._user)
            await self._send_str(self._pswd)
        
        print("_broker_connect Await CONNACK")
        # read causes ECONNABORTED if broker is out; triggers a reconnect.
        resp = await self._as_read(4)
        print("_broker_connect Connected to broker resp", resp)  # Got CONNACK
        if resp[3] != 0 or resp[0] != 0x20 or resp[1] != 0x02:  # Bad CONNACK e.g. authentication fail.
            print("_broker_connect bad CONNACK") 
            raise OSError(-1, f"Connect fail: 0x{(resp[0] << 8) + resp[1]:04x} {resp[3]} (README 7)")
        print("\n\n++++ broker connected ++++\n")

    async def _ping(self):
        async with self.sock_lock:
            try:
                await self._as_write(b"\xc0\0")
            except Exception as e:
                print("_ping exception",e)

    def _close(self):
        if self._sock is not None:
            self._sock.close()

    def wifi_disconnect(self):  # API. See https://github.com/peterhinch/micropython-mqtt/issues/60
        self._close()
        try:
            self._sta_if.disconnect()  # Disconnect Wi-Fi to avoid errors
        except OSError:
            print("wifi_disconnect Wi-Fi not started, no problem")
        self._sta_if.active(False)

    async def _await_pid(self, pid):
        t = ticks_ms()
        while pid in self.rcv_pids:  # local copy
            if self._timeout(t) or not self.isconnected():
                break  # Must repub or bail out
            await asyncio.sleep_ms(100)
        else:
            return True  # PID received. All done.
        return False

    # qos == 1: coro blocks until wait_msg gets correct PID.
    # If WiFi fails completely subclass re-publishes with new PID.
    async def publish(self, topic, msg, retain, qos):
        pid = next(self.newpid)
        if qos:
            self.rcv_pids.add(pid)
        async with self.sock_lock:
            await self._publish(topic, msg, retain, qos, 0, pid)
        if qos == 0:
            return

        count = 0
        while 1:  # Await PUBACK, republish on timeout
            if await self._await_pid(pid):
                return
            # No match
            if count >= self._max_repubs or not self.isconnected():
                raise OSError(-1)  # Subclass to re-publish with new PID
            async with self.sock_lock:
                await self._publish(topic, msg, retain, qos, dup=1, pid=pid)  # Add pid
            count += 1
            self.REPUB_COUNT += 1

    async def _publish(self, topic, msg, retain, qos, dup, pid):
        pkt = bytearray(b"\x30\0\0\0")
        pkt[0] |= qos << 1 | retain | dup << 3
        sz = 2 + len(topic) + len(msg)
        if qos > 0:
            sz += 2
        if sz >= 2097152:
            raise MQTTException("Strings too long.")
        i = 1
        while sz > 0x7F:
            pkt[i] = (sz & 0x7F) | 0x80
            sz >>= 7
            i += 1
        pkt[i] = sz
        await self._as_write(pkt, i + 1)
        await self._send_str(topic)
        if qos > 0:
            struct.pack_into("!H", pkt, 0, pid)
            await self._as_write(pkt, 2)
        await self._as_write(msg)

    # Can raise OSError if WiFi fails. Subclass traps.
    async def subscribe(self, topic, qos, marker=0):
        print("super subscribe [", topic, "] marker[",marker,"] _sock[", self._sock,"]")
        pkt = bytearray(b"\x82\0\0\0")
        pid = next(self.newpid)

        self.rcv_pids.add(pid)
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic) + 1, pid)
        async with self.sock_lock:
            await self._as_write(pkt)
            await self._send_str(topic)
            await self._as_write(qos.to_bytes(1, "little"))

        if not await self._await_pid(pid):
            raise OSError(-1)

    # Can raise OSError if WiFi fails. Subclass traps.
    async def unsubscribe(self, topic):
        pkt = bytearray(b"\xa2\0\0\0")
        pid = next(self.newpid)
        self.rcv_pids.add(pid)
        struct.pack_into("!BH", pkt, 1, 2 + 2 + len(topic), pid)
        async with self.sock_lock:
            await self._as_write(pkt)
            await self._send_str(topic)

        if not await self._await_pid(pid):
            raise OSError(-1)

    # Wait for a single incoming MQTT message and process it.
    # Subscribed messages are delivered to a callback previously
    # set by .setup() method. Other (internal) MQTT
    # messages processed internally.
    # Immediate return if no data available. Called from ._handle_msg().
    async def wait_msg(self):
        print("wait_msg start  _sock[", self._sock,"]")
        res = None
        try:
            res = self._sock.read(1)  # Throws OSError on WiFi fail
            #res = await self._as_read(1)
        except OSError as e:
            print("wait_msg error:", e)
            if e.errno == ENOTCONN:
                print("wait_msg  lost connection, notify manage_broker")
                self.connection_lost = True
                await asyncio.sleep(1)
            if e.args[0] in BUSY_ERRORS:  # Needed by RP2
                await asyncio.sleep_ms(0)
                print("wait_msg: BUSY_ERRORS")
                return
            raise
        print("wait_msg first byte", res)
        if res is None:
            print("wait_msg res == none")
            return
        if res == b"":
            raise OSError(-1, "Empty response")

        if res == b"\xd0":  # PINGRESP
            await self._as_read(1)  # Update .last_rx time
            print("wait_msg got a pingresp")
            self.last_pingresp = time()
            return
        op = res[0]

        if op == 0x40:  # PUBACK: save pid
            sz = await self._as_read(1)
            if sz != b"\x02":
                raise OSError(-1, "Invalid PUBACK packet")
            rcv_pid = await self._as_read(2)
            pid = rcv_pid[0] << 8 | rcv_pid[1]
            if pid in self.rcv_pids:
                self.rcv_pids.discard(pid)
            else:
                raise OSError(-1, "Invalid pid in PUBACK packet")

        if op == 0x90:  # SUBACK
            resp = await self._as_read(4)
            if resp[3] == 0x80:
                raise OSError(-1, "Invalid SUBACK packet")
            pid = resp[2] | (resp[1] << 8)
            if pid in self.rcv_pids:
                self.rcv_pids.discard(pid)
            else:
                raise OSError(-1, "Invalid pid in SUBACK packet")

        if op == 0xB0:  # UNSUBACK
            resp = await self._as_read(3)
            pid = resp[2] | (resp[1] << 8)
            if pid in self.rcv_pids:
                self.rcv_pids.discard(pid)
            else:
                raise OSError(-1)

        if op & 0xF0 != 0x30:
            return
        sz = await self._recv_len()
        topic_len = await self._as_read(2)
        topic_len = (topic_len[0] << 8) | topic_len[1]
        topic = await self._as_read(topic_len)
        sz -= topic_len + 2
        if op & 6:
            pid = await self._as_read(2)
            pid = pid[0] << 8 | pid[1]
            sz -= 2
        msg = await self._as_read(sz)
        retained = op & 0x01
        if self._events:
            print("wait_msg [", topic, "]")
            self.queue.put(topic, msg, bool(retained))
        else:
            self._cb(topic, msg, bool(retained))
        if op & 6 == 2:  # qos 1
            pkt = bytearray(b"\x40\x02\0\0")  # Send PUBACK
            struct.pack_into("!H", pkt, 2, pid)
            await self._as_write(pkt)
        elif op & 6 == 4:  # qos 2 not supported
            raise OSError(-1, "QoS 2 not supported")


# MQTTClient class. Handles issues relating to connectivity.


class MQTTClient(MQTT_base):
    def __init__(self, config):
        super().__init__(config)
        self._isconnected = False  # Current connection state
        self._in_connect = False
        self._has_connected = False  # Define 'Clean Session' value to use.
        self.error = 0
        self._addr = None
        self.do_subscribes = False
     
        self.debug = False
        #
        if ESP8266:
            import esp
            esp.sleep_type(0)  # Improve connection integrity at cost of power consumption.

    async def wifi_connect(self, quick=False):
        print("wifi_connect started quick[",quick,"]")
        s = self._sta_if
        if ESP8266:
            print("wifi_connect ESP8266")
            if s.isconnected():  # 1st attempt, already connected.
                return
            s.disc
            s.active(True)
            s.connect()  # ESP8266 remembers connection.
            for _ in range(10):
                if (s.status() != network.STAT_CONNECTING):  # Break out on fail or success. Check once per sec.
                    break
                await asyncio.sleep(1)
            
            if (
                s.status() == network.STAT_CONNECTING
            ):  # might hang forever awaiting dhcp lease renewal or something else
                s.disconnect()
                await asyncio.sleep(1)
            if not s.isconnected() and self._ssid is not None and self._wifi_pw is not None:
                s.connect(self._ssid, self._wifi_pw)
                while (
                    s.status() == network.STAT_CONNECTING
                ):  # Break out on fail or success. Check once per sec.
                    await asyncio.sleep(1)
        else:
            #s.disconnect()
            s.active(True)
            if RP2:  # Disable auto-sleep.
                # https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
                # para 3.6.3
                s.config(pm=0xA11140)
            print("wifi_connect s.connect to [",self._ssid,"][", self._wifi_pw, "]")
            try:
                s.connect(self._ssid, self._wifi_pw)
            except:
                """
                STAT_IDLE - no connection, no activities-1000
                STAT_CONNECTING - Connecting-1001
                STAT_WRONG_PASSWORD - Failed due to password error-202
                STAT_NO_AP_FOUND - Failed, because there is no access point reply,201
                STAT_GOT_IP - Connected-1010
                STAT_ASSOC_FAIL - 203
                STAT_BEACON_TIMEOUT - Timeout-200
                STAT_HANDSHAKE_TIMEOUT - Handshake timeout-204
                """
                print("wifi_connect exception doing s.connect status[]", s.status(),"]")
            if (s.status() == network.STAT_WRONG_PASSWORD):
                self.error = ERROR_BAD_PASSWORD 
                raise                    
            elif (s.status() == network.STAT_NO_AP_FOUND):
                self.error = ERROR_AP_NOT_FOUND
                raise
            print("wifi_connect s.connect s.status", s.status())
            for i in range(10):  # Break out on fail or success. Check once per sec.
                await asyncio.sleep(1)
                # Loop while connecting or no IP
                print("wifi_connect loop s.status", s.status(), i)
                if s.isconnected():
                    print("wifi_connect isconnected so break")
                    break
                if ESP32:
                    #if s.status() != network.STAT_CONNECTING:  # 1001
                        #print("wifi STAT_CONNECTING break")
                    if s.status() == network.STAT_GOT_IP:  # 1001
                        print("wifi_connect STAT_GOT_IP break")
                        cnt=0
                        while not s.isconnected():
                            print("wifi_connect waiting for isconnected", s.status())
                            await asyncio.sleep(1)
                            cnt += 1
                            if cnt > 10:

                                break
                        break
                elif PYBOARD:  # No symbolic constants in network
                    if not 1 <= s.status() <= 2:
                        break
                elif RP2:  # 1 is STAT_CONNECTING. 2 reported by user (No IP?)
                    if not 1 <= s.status() <= 2:
                        break
            else:  # Timeout: still in connecting state
                print("wifi_connect waitloop no breaks, disconnect")
                s.disconnect()
                await asyncio.sleep(1)
        print("wifi_connect checking connection")
        if not s.isconnected():  # Timed out
            print("wifi_connect connect timed out")
            raise OSError("wifi_connect connect timed out")
        if not quick:  # Skip on first connection only if power saving
            # Ensure connection stays up for a few secs.
            print("wifi_connect Checking WiFi integrity not quick")
            for _ in range(5):
                connected = s.isconnected()
                print("wifi_connect connected[", connected,"]")
                if not connected:
                    raise OSError("wifi_connect Connection Unstable")  # in 1st 5 secs
                await asyncio.sleep(1)
            print("++++ Got reliable wifi connection ++++")

    # this is designed to run as a asyncio task
    # it insures a wifi connecton and reconnections
    # wifi_up.wait() is used by monitor_broker to know if we are wifi connected
    async def monitor_wifi(self):
        print("monitor_wifi starting")
        while True:
            print("monitor_wifi making wifi connection")
            self.wifi_disconnect()
            wifi = self._sta_if
            wifi.active(True)
            self.wifi_up.clear()
            self.broker_connected.clear()

            if RP2:  # Disable auto-sleep.
                # https://datasheets.raspberrypi.com/picow/connecting-to-the-internet-with-pico-w.pdf
                # para 3.6.3
                wifi.config(pm=0xA11140)
            print("monitor_wifi wifi.connect to [",self._ssid,"][", self._wifi_pw, "]")
            try:
                wifi.connect(self._ssid, self._wifi_pw)
            except:
                """
                STAT_IDLE - no connection, no activities-1000
                STAT_CONNECTING - Connecting-1001
                STAT_WRONG_PASSWORD - Failed due to password error-202
                STAT_NO_AP_FOUND - Failed, because there is no access point reply,201
                STAT_GOT_IP - Connected-1010
                STAT_ASSOC_FAIL - 203
                STAT_BEACON_TIMEOUT - Timeout-200
                STAT_HANDSHAKE_TIMEOUT - Handshake timeout-204
                """
                print("monitor_wifi exception doing wifi.connect status[]", wifi.status(),"]")
            if (wifi.status() == network.STAT_WRONG_PASSWORD):
                await self._problem_reporter(ERROR_BAD_PASSWORD, repeat=60)
                continue                 
            elif (wifi.status() == network.STAT_NO_AP_FOUND):
                await self._problem_reporter(ERROR_AP_NOT_FOUND, repeat=5)
                continue
            print("monitor_wifi wifi.connect wifi.status", wifi.status())
            for i in range(10):  # Break out on fail or success. Check once per sec.
                await asyncio.sleep(1)
                # Loop while connecting or no IP
                print("monitor_wifi loop wifi.status", wifi.status(), i)
                if wifi.isconnected():
                    print("monitor_wifi isconnected so break")
                    break
                if ESP32:
                    if wifi.status() == network.STAT_GOT_IP:  # 1001
                        print("monitor_wifi STAT_GOT_IP break")
                        cnt=0
                        while not wifi.isconnected():
                            print("monitor_wifi waiting for isconnected", wifi.status())
                            await asyncio.sleep(1)
                            cnt += 1
                            if cnt > 10:

                                break
                        break
                elif PYBOARD:  # No symbolic constants in network
                    if not 1 <= wifi.status() <= 2:
                        break
                elif RP2:  # 1 is STAT_CONNECTING. 2 reported by user (No IP?)
                    if not 1 <= wifi.status() <= 2:
                        break
            else:  # Timeout: still in connecting state
                await asyncio.sleep(2)
                continue
            if  wifi.isconnected():  
                print("\n\n+++ monitor_wifi connected, now monitoring +++\n")
                self.wifi_up.set()  # ok for broker connect
                while True:
                    if not wifi.isconnected():
                        print("monitor_wifi connection broken")
                        break
                    await asyncio.sleep(5)
            else:  # looks like it never connected 
                print("monitor_wifi not intialy connected very odd")
                pass
    # 
    async def monitor_broker(self):
        while True:
            self._isconnected = False
            self.connection_lost = False
            await self.wifi_up.wait() # blocks until wifi connected see: monitor_wifi()
            self.broker_connected.clear() # this cause others to wait
            await self.get_broker_ip_port()
            print("monitor_broker brokers IP[", self._addr, "]")
            if self.error: # 
                await self._problem_reporter(self.error, repeat=10)
            else:
                try: 
                    await self._broker_connect(True)  # Connect with clean session
                except Exception as e:
                    self._close()
                    #self._in_connect = False  # Caller may run .isconnected()
                    print("monitor_broker  _broker_connect failed",e) 
                    self.error =  ERROR_BROKER_CONNECT_FAILED
                    await self._problem_reporter(self.error) 
                else:
                    print("monitor_broker _broker_connect - success, socket [", self._sock,"]")
                    self.do_subscribes = True # tells app to subscribe/resubscribe
                    self.connection_lost = False
                    
                    self._isconnected = True
                    time_between_pings = self._keepalive
                    max_ping_wait= time_between_pings*6
                    self.last_pingresp =  time() # this get changed by wait_msg PINGRESP
                    self.broker_connected.set() # now pub/subs can run
                    while  not self.connection_lost: # make sure broker is connected  
                        net_seconds = time() - self.last_pingresp
                        print("monitor_broker net_seconds", net_seconds)
                        if net_seconds >  max_ping_wait:
                            print(" too much ping wait")
                            break
                        try:
                            await self._ping()  # when this fails connection has been lost
                            print("monitor_broker ping returned")
                        except:
                            print("/n/nmonitor_broker ping broke/n")
                            break
                        await asyncio.sleep(time_between_pings)
    
    async def get_broker_ip_port(self):
        # Note this blocks if DNS lookup occurs. Do it once to prevent
        # blocking during later internet outage:
        self.error = 0
        print("get_broker_ip_port [" ,self.server,":",self.port,"]")
        try:
            self._addr = socket.getaddrinfo(self.server, self.port)[0][-1]
            print("++++ get_broker_ip_port == [", self._addr,"] ++++")
        except:
            print("get_broker_ip_port getaddrinfo lookup failed")
            self._addr = None
            self.error = ERROR_BROKER_LOOKUP_FAILED
        

    # asyncio task runs forever 
    # handles incoming messages wait_msg put them in the queue.
    async def _handle_msg(self):
        while True:  
            try:
                async with self.sock_lock:
                    print("_handle_msg got sock_lock")
                    await self.broker_connected.wait()
                    print("_handle_msg: broker is connected")
                    try:
                        await self.wait_msg()  # Immediate return if no message             
                    except OSError as e:
                        print("_handle_msg error: from wait_msg",e)
                        pass
            except OSError as e:
                print("_handle_msg error: from lock", e)
                pass
            await asyncio.sleep_ms(_DEFAULT_MS)  # Let other tasks get lock

    
    def isconnected(self):
        #if self._in_connect:  # Disable low-level check during .connect()
            #return True
        #if self._isconnected and not self._sta_if.isconnected():  # It's going down.
            #self._reconnect()
        return self._isconnected

    async def subscribe(self, topic, qos=0):
        print("subscribe ", topic)
        qos_check(qos)
        while 1:
            await self.broker_connected.wait()
            try:
                print("doing super")
                return await super().subscribe(topic, qos)
            except OSError as e:
                if e.errno == ENOTCONN:
                    print("subscribe  lost connection, notify manage_broker")
                    self.connection_lost = True
                    await asyncio.sleep(1)
                print("subscribe error",e)
                pass
            await asyncio.sleep(1)

            # self._reconnect()  # Broker or WiFi fail.

    async def unsubscribe(self, topic):
        while 1:
            await self.broker_connected.wait()
            try:
                return await super().unsubscribe(topic)
            except OSError as e:
                if e.errno == ENOTCONN:
                    print("unsubscribe  lost connection, notify manage_broker")
                    self.connection_lost = True
                    await asyncio.sleep(1)
                print("unsubscribe error",e)
                pass
            await asyncio.sleep(1)

    async def publish(self, topic, msg, retain=False, qos=0):
        qos_check(qos)
        print("publish [", topic, "]")
        while 1:
            await self.broker_connected.wait()
            try:
                return await super().publish(topic, msg, retain, qos)
            except OSError as e:
                if e.errno == ENOTCONN:
                    print("publish  lost connection, notify manage_broker")
                    self.connection_lost = True
                    await asyncio.sleep(1)
                print("publish error",e)
                pass
            # self._reconnect()  # Broker or WiFi fail.

    def status(self):
        return self.error
