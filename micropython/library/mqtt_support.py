# asyncio package to insure stable connections to wifi and the MQTT broker
# MIT Licence Copyright Jim Dodgen 2025
# some parts (MsgQueue) (C) Copyright Peter Hinch 2017-2023.
# also released under the MIT licence.

import network
import time
import asyncio
from arobust import MQTTClient

ERROR_OK = 0
ERROR_AP_NOT_FOUND = 2
ERROR_BAD_PASSWORD = 3
ERROR_BROKER_CONNECT_FAILED =  4

# conditional formatted print replacement
# MIT License Copyright Jim Dodgen 2025
# if first string starts with a "." then the first word of the string is appended to the print_tag
# typically identifying the routine
# this needs to be pasted into your .py file
#
print_tag = "mqtt_support"
do_prints = True # usually set to False in production
def turn_on_prints(flag):  # true or false
    global do_prints
    do_prints=flag
raw_print = print # copy print
def print(first, *args, **kwargs): # replace print
    global do_prints
    if do_prints:
        f=None
        if isinstance(first, str) and first[0] == ".":
            f = first.split(" ",1)
        else:
            f = ["",first]
        try:
            if len(f) > 1:
                raw_print("["+print_tag+f[0]+"]", f[1], *args, **kwargs) # the copied real print
            else:
                raw_print("["+print_tag+f[0]+"]", *args, **kwargs) # the copied real print
        except:
            raise ValueError("xprint problem ["+print_tag+"]")

# simple queue for single put'er and single get'er thanks to Peter Hinch
class MsgQueue:
    def __init__(self, size):
        self._q = [0 for _ in range(max(size, 4))]
        self._size = size
        self._wi = 0
        self._ri = 0
        self._evt = asyncio.Event()
        self.discards = 0

    def put(self, *v):
        print(".MsgQueue", v)
        self._q[self._wi] = v
        self._evt.set()
        self._wi = (self._wi + 1) % self._size
        if self._wi == self._ri:  # Would indicate empty
            self._ri = (self._ri + 1) % self._size  # Discard a message
            self.discards += 1

    def empty(self):  # added by Jim Dodgen 2025
        #print(".MsgQueue empty ri wi", self._ri, self._wi)
        return True if self._ri == self._wi else False

    def __aiter__(self):
        return self

    async def __anext__(self):
        #print(".MsgQueue __anext__ ri wi", self._ri, self._wi)
        if self._ri == self._wi:  # Empty
            self._evt.clear()
            await self._evt.wait()
        r = self._q[self._ri]
        self._ri = (self._ri + 1) % self._size
        #print(".MsgQueue __anext__ return ", r)
        return r

class mqtt_support():
    def __init__(self, ssid=None, wifi_pw=None, problem_reporter=None, broker=None, broker_password=None, broker_user=None, subscriptions=None, publish_retains=None, queue_len=10):
        self._sta_if = network.WLAN(network.STA_IF)
        self.queue = MsgQueue(queue_len)
        self.error_queue = MsgQueue(5)
        self.debug = False
        self._ssid=ssid
        self._wifi_pw=wifi_pw
        self._broker_password = broker_password
        self._broker_user=broker_user
        self._broker=broker
        self._problem_reporter = problem_reporter
        self.client = None
        self.wifi_up = asyncio.Event()
        self.broker_up = asyncio.Event()
        self.subscriptions = subscriptions
        self.pub_retains = publish_retains
        asyncio.create_task(self.monitor_wifi())  # connects and reconnects as needed
        asyncio.create_task(self.process_incoming_messages())

    async def monitor_wifi(self):
        print(".monitor_wifi starting")
        while True:
            print(".monitor_wifi making connection")
            self.wifi_disconnect()
            wifi = self._sta_if
            wifi.active(True)
            self.wifi_up.clear()
            self.broker_up.clear()
            #self.broker_connected.clear()
            print(".monitor_wifi wifi.connecting to [",self._ssid,"][", self._wifi_pw, "]")
            try:
                wifi.connect(self._ssid, self._wifi_pw)
                print(".monitor_wifi status", wifi.status())
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
                print(".monitor_wifi exception doing wifi.connect status[]", wifi.status(),"]")
            if (wifi.status() == network.STAT_WRONG_PASSWORD):
                self.error_queue.put(ERROR_BAD_PASSWORD)
                await asyncio.sleep(10)
                continue
            elif (wifi.status() == network.STAT_NO_AP_FOUND):
                self.error_queue.put(ERROR_AP_NOT_FOUND)
                await asyncio.sleep(10)
                continue
            print(".monitor_wifi wifi.connect wifi.status", wifi.status())
            for i in range(10):  # Break out on fail or success. Check once per sec.
                await asyncio.sleep(1)
                # Loop while connecting or no IP
                print(".monitor_wifi loop wifi.status", wifi.status(), i)
                if wifi.isconnected():
                    ipcfg = wifi.ifconfig()
                    print('.monitor_wifi ip = ' + ipcfg[0])
                    print(".monitor_wifi isconnected so break")
                    break
            if wifi.status() == network.STAT_GOT_IP:  # 1001
                print(".monitor_wifi STAT_GOT_IP wait for disconnect")
                ipcfg = wifi.ifconfig()
                print('.monitor_wifi ip = ' + ipcfg[0])
                cnt=0
                while not wifi.isconnected():
                    print(".monitor_wifi waiting for isconnected", wifi.status())
                    await asyncio.sleep(1)
                    cnt += 1
                    if cnt > 10:
                        break
                print(".monitor_wifi wifi.isconnected", wifi.isconnected())
            else:  # Timeout: still in connecting state
                await asyncio.sleep(2)
                continue
            if  wifi.isconnected():
                raw_print("\n+++ monitor_wifi connected, now monitoring +++\n")
                # it is ok to start mqtt connection
                self.wifi_up.set()  # ok for broker connect
                self.error_queue.put(ERROR_OK)
                while True:
                    #print(".monitor_wifi waiting for disconnect")
                    if not wifi.isconnected():
                        print(".monitor_wifi connection broken")
                        self.error_queue.put(ERROR_AP_NOT_FOUND)
                        break
                    #print(".monitor_wifi sleeping 5")
                    await asyncio.sleep(5)
            else:  # looks like it never connected
                print(".monitor_wifi not intialy connected very odd")

    def wifi_disconnect(self):  # API. See https://github.com/peterhinch/micropython-mqtt/issues/60
        # self._close()
        try:
            self._sta_if.disconnect()  # Disconnect Wi-Fi to avoid errors
        except OSError:
            print(".wifi_disconnect Wi-Fi not started, no problem")
        self._sta_if.active(False)

    async def process_incoming_messages(self):
        while True:
            await self.broker_up.wait()
            await self.client.check_msg()
            await asyncio.sleep(0.1)

    async def broker(self):
        try:
            print(".broker connect waiting")
            await self.wifi_up.wait() #wait for wifi to connect
            self.client = MQTTClient(
                client_id=b"testing ssh read problem",
                server=self._broker,
                port=0,
                user=self._broker_user,
                password=self._broker_password,
                keepalive=7200,
                ssl=True,
                ssl_params={'server_hostname': self._broker})
            self.client.set_callback(self._queue_message)
            self.client.subscribe_topics(self.subscriptions)
            self.client.retain_pub_topics(self.pub_retains)
            self.client.set_error_queue(self.error_queue)
            print(".broker now looping for connect")
            while True:
                await asyncio.sleep(10)
                try:
                    print(".broker client.connect")
                    await self.client.always_connect()
                except:
                    print(".broker not connecting")
                    self.error_queue.put(ERROR_BROKER_CONNECT_FAILED)
                else:
                    print(".broker connected")
                    self.broker_up.set()
                    self.error_queue.put(ERROR_OK)
                    break
            print(".broker connected")

            return self.client
        except asyncio.CancelledError:
            print(".broker asyncio cancelled")
            # clean up here
            self.client.disconnect()

    def _queue_message(self, topic, value):
        print("._queue_message:", topic, value)
        self.queue.put(topic, value)
        print("._queue_message: done")


