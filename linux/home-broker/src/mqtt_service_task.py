import message
import multiprocessing
import queue
from multiprocessing import Queue 
import devices_to_json
import load_zigbee_data
import load_IP_device_data
import sys
import zlib
import time
import const
import mqtt_hello
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
def task(q):
    print("queue  passed in type[%s]" % type(q))
    msg = message.message(q, my_parent=my_name)

    msg.subscribe(const.home_MQTTdevices_get)  # from unretained recepter for a refress 
    msg.subscribe(const.zigbee2mqtt_bridge_devices)  # from retained fresh zigbees
    msg.subscribe(mqtt_hello.hello_subscribe_pattern) # catch IoT configurations
    print("hello_request topic [%s]" % ( mqtt_hello.hello_request_topic, ))
    msg.publish(mqtt_hello.hello_request_topic, b"hello please") # ask for configs to be publised in format of "hello_subscribe_pattern"
    last_time_zigbee_refreshed = 0.0
    compressed_json = None
    while True:
        try:
            item = q.get(timeout=const.mqtt_service_q_timeout) 
        except queue.Empty:
            print("queue timed out:  empty")
            #msg.subscribe(const.home_MQTTdevices_get)
            msg.subscribe(mqtt_hello.hello_subscribe_pattern)
            continue
        except Exception as e: 
            print("unhandled exception", e)
            continue
        command = item[0]
        print("Item from queue [%s] [%s]" % (command, item[1]))
        if command == "callback":
            topic = item[1]
            payload = item[2]
            print("callback topic[%s] payload[%s]" % (topic, payload,))
            if topic == const.zigbee2mqtt_bridge_devices: # this get fufulled when z2m detects changes
                load_zigbee_data.load_database_from_zigbee(payload)
                raw_json = devices_to_json.devices_to_json()
                text_size = sys.getsizeof(raw_json)
                compressed_json = zlib.compress(bytes(raw_json, "utf-8"))
                compressed_size = sys.getsizeof(compressed_json)
                print(" json size[%s] compressed[%s]" % (text_size, compressed_size))
                msg.publish(const.home_MQTT_devices, compressed_json, retain=True)  # now we publish/retain for othert apps
            elif topic == const.home_MQTTdevices_get: # refresh of devices requested
                # this causes a "subscribe to get the zigbee devices" and a "publish to request IP devices"
                # IP devices will take a while or even be non existant 
                # we avoid excessive database refreshes and mqtt traffic
                # by not refreshing the data every time
                # this might wan to be logged the payload contains the source of the request
                # to find a missbehaving thing
                # If found we can filter by name TBD 
                now = time.time()
                if last_time_zigbee_refreshed + const.zigbee_refresh_seconds < now:   # ignore excess calls
                    last_time_zigbee_refreshed = now
                    msg.subscribe(const.zigbee2mqtt_bridge_devices)  # this ia a re-subscribe of the zigbee2mqtt devices causinga refresh 
                    msg.publish(mqtt_hello.hello_request_topic, b"publish hello please")
                else: # has not changed much so we did not rebuild it. publish will cause it to be sent to subscribers
                    msg.publish(const.home_MQTT_devices, compressed_json, retain=True) 
            else:
                t = topic.split("/")
                home = t[0]
                address = t[1]
                hello = t[2]
                print("task: home[%s] address[%s] hello{%s] payload[%s]" % (home, address, hello, payload))
                if home == "home"and hello == "hello": # refresh of devices requested
                    load_IP_device_data.load_IP_device(payload)
        elif command == "connected":
            print("connected")
            #msg.subscribe(home_MQTTdevices_get)
            #msg.subscribe(hello_subscribe)
        else:
            print(" unknown cmd")

def start_MQTT_service_task(mqtt_queue):
    p = multiprocessing.Process(target=task, args=(mqtt_queue,))
    p.start()
    return p

def stop_MQTT_service_task(p):
    p.terminate()
    while p.is_alive():
        print("MQTT wont die")
        time.sleep(0.1)
    p.join()
    p.close()

# unit test code 
if __name__ == "__main__":
    q = Queue()
    task(q)
    #start_MQTT_service_task(mqtt_queue)
    time.sleep(100)
