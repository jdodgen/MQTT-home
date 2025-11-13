## MIT license copyright 2025 Jim Dodgen
# Power Change Notifier common routines  

import esp
import gc
import os
import asyncio
import machine
import tm1640
import umail
import cfg
import alert_handler
from mqtt_as import MQTTClient

# conditional formatted print
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[pcn]", *args, **kwargs) # the copied real print

def print_flash_usage():
    stat = os.statvfs('/')
    total_size = stat[1] * stat[2]
    free_space = stat[0] * stat[3]
    used_space = total_size - free_space
    print("Flash: total %d used %s free %d" % (total_size,used_space,free_space,))
    flash_size = esp.flash_size()
    flash_user_start = esp.flash_user_start()
    print("ESP flash: total %d used  %d free %d" % (flash_size, flash_user_start, flash_size-flash_user_start))
    
# show PSRAM messages.
async def _memory(self):
    while True:
        await asyncio.sleep(20)
        gc.collect()
        print("RAM free %d alloc %d" % (gc.mem_free(), gc.mem_alloc(),))  
        
def get_8x8_matrix(string):
    try:
        item = cfg.tm1640_chars[string] # might be a full word match like boot1
    except:
        try:
            item = cfg.tm1640_chars[string[0]] # Just lookup the first char
        except:
            print("get_8x8_matrix not found in cfg.tm1640_chars", string)
            item = cfg.tm1640_chars["?"]
    #print("get_8x8_matrix [%s] returning [%s]" % (string,item))
    return item  
    
class display8x8:
    def __init__(self, clk=14, dio=13, bright=7):
        if clk is None:
            self.ignore = True
            return
        else:
            self.ignore = False
        self.tm = tm1640.TM1640(clk=machine.Pin(clk), dio=machine.Pin(dio))
        # all LEDs bright
        self.tm.brightness(bright)

    def write(self, bit_map):
        if self.ignore is False:
            self.tm.write(bit_map)

async def do_single_led(single_led_queue):
    led = alert_handler.alert_handler(cfg.big_led_pin, None, onboard_led_pin=cfg.onboard_led_pin)
    async for cmd,  in single_led_queue:
        while not single_led_queue.empty(): # flush the queue, use last item
            async for cmd, in single_led_queue:
                break
        print("do_single_led [%s]" % (cmd,))
        if cmd == "all_off":
            led.turn_off()
        elif cmd == "boot":
            led.turn_on()
            await asyncio.sleep(1)
            led.turn_off()
        elif cmd == "sensor_down":
            led.turn_on()
        else:
            flash_count = 4
            if cmd == "wifi":
                flash_count = 2
            elif cmd == "broker":
                flash_count = 3
            elif cmd == "outage":
                flash_count = 6
            while single_led_queue.empty():
                await led.async_flash(count=flash_count, duration=0.5, ontime=0.5)
                await asyncio.sleep(1)

class do_8x8_list:
    def __init__(self, led_8x8_queue):
        self.led_8x8_queue = led_8x8_queue
        self.d=display8x8(clk=cfg.clock8X8_pin, dio=cfg.data8x8_pin, bright=cfg.brightness8x8)
        self.question_mark = get_8x8_matrix("?")
        self.turn_off = get_8x8_matrix("all_off")
        self.d.write(self.turn_off)

    async def write(self, topic_list):
        #print("do_8x8_list.write", topic_list)
        # first convert to 8x8
        char_matrix = []
        for topic_and_dry_contact in topic_list:
            (topic, dry_contact) = topic_and_dry_contact
            if isinstance(topic, str):
                # parse topic get letter
                try:
                    ident = topic.split("/")[2]
                except:
                    ident = topic
                #print("do_8x8_list ident", ident)
                matrix_list = get_8x8_matrix(ident)
                if dry_contact:
                    matrix_list[0] = 0x80
                char_matrix.append(matrix_list)
            else:
                char_matrix.append(self.question_mark)  # error
        await asyncio.sleep(0)
        while True: # displays letters until another message arrives
            for char8x8 in char_matrix:
                self.d.write(char8x8)
                await asyncio.sleep(0.5)
                self.d.write(self.turn_off)
                await asyncio.sleep(0.2)
            if not self.led_8x8_queue.empty():  # this loops until another msg availble
                break
            await asyncio.sleep(1)

#  asyncio task to display information
async def led_8x8_display(led_8x8_queue):
    # wait for an error
    error_code = 0
    next_code = 0
    list8x8 = do_8x8_list(led_8x8_queue)
    async for msg_list, in led_8x8_queue:
        while not led_8x8_queue.empty(): # flush the queue, use last item
            async for msg_list, in led_8x8_queue:
                break
        #print("led_8x8_display [%s] type [%s]" % (msg_list, type(msg_list)))
        #if isinstance(msg_list, list): # a list of strings to display on 8x8 led matrix
        await list8x8.write(msg_list)
        #else:
            #await list8x8.write(["?",])

async def up_so_subscribe(client, led_8x8_queue, single_led_queue, topics):
    while True:
        await client.up.wait()
        client.up.clear()
        print('doing subscribes', topics)
        led_8x8_queue.put((("all_off",False), ))
        single_led_queue.put("all_off")
        for topic in topics:
            await client.subscribe(topic)
        print("emailing startup")
        await send_email("PCN Starting", boilerplate)

async def down_report_outage(client, led_8x8_queue, single_led_queue):
    while True:
        await client.down.wait()
        client.down.clear()
        print('got outage')
        led_8x8_queue.put((("wifi",False),))
        single_led_queue.put("5")
        
boilerplate = '''Starting up:
Flashing LED error codes
It displays a flashing single LED and optionaly a LED character.
If the LED square is expanding or just one LED flash --- Sarting up

flashing/display counts are as follows:
2 flashes, ERROR_AP_NOT_FOUND or ERROR_BAD_PASSWORD
3 flashes, ERROR_BROKER_LOOKUP_FAILED or ERROR_BROKER_CONNECT_FAILED
5 flashes, Runtime connection failure, standby, re-connecting.

Outage/alert issues are reported by:
The LED is solid on and/or one or more "sensors letters" scroll by. 
This indicates an alert usualy an outage.
If the LED is out or screen is blank, Indicates all is normal and no alerts. 
The sensor does NOT do any flashes when just waiting or an outage, it is passive. 
The Other sensors will tell you if it fails. 
'''
        
async def send_email(subject, body, cluster_id_only=False):
    try:
        smtp = umail.SMTP('smtp.gmail.com', 465, ssl=True)
        await asyncio.sleep(0)
        smtp.login(cfg.gmail_user, cfg.gmail_password)
        await asyncio.sleep(0)
        smtp.to(cfg.send_messages_to, mail_from=cfg.gmail_user)
        id = cfg.cluster_id if cluster_id_only else cfg.pretty_name
        print("our id [%s]" % (id,))
        smtp.write("Subject:%s, %s\n\n%s\n" % (subject, id,  body,))
        await asyncio.sleep(0)
        smtp.send()
        await asyncio.sleep(0)
        smtp.quit()
    except Exception as e:
            print("email failed", e)
# make first connection
# mqtt_as requires a good connection to the broker/server at startup
# it recovers and notifies automaticly
#    
async def make_first_connection(config, led_8x8_queue, single_led_queue):
    got_connection = False
    print("checking for good wifi", cfg.wifi)
    while True:
        # Even though mqtt_as automaticly reconnects an initial connection is required
        for w in cfg.wifi:  # a list of lists each "w" is (ssid,password)
            print("trying ...", w)
            config['ssid'] = w[0]
            config['wifi_pw'] = w[1]
            client = MQTTClient(config)
            # print("switch is",sw.test())
            try:
                await client.connect()
            except Exception as e:
                print("connection problem [", e,);
                try:
                    x=client._addr
                    print("we have ip address broker not connecting", client._addr)
                    led_8x8_queue.put((("?", False),("broker", False),)) # report 3 flashes
                    single_led_queue.put("broker")
                except:
                    print("wifi failed no ip address")
                    led_8x8_queue.put((("?",False),("wifi",False),))  # report 2 flashes
                    single_led_queue.put("wifi")
                await asyncio.sleep(cfg.wifi_sleep)
            else:
                print("ip address", client._addr)
                got_connection = True
                break
        if got_connection == True:
            break
    return client
