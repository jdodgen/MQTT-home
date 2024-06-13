# client test program to retreve zigbee22mqtt devices jason and display it
import message # from home-broker
import zlib
import queue
import json
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#

# publish this to CAUSE a refresh of the device data
request_MQTT_Devices = "home/MQTTdevices/get"   # must be == to config version
publish_payload = "server_test_example"  # payload is used to indicate who did the request

# this will result in a callback with the device data
subscribed_MQTTDevices = "home/MQTTdevices/configuration"

# sample process fetching all devices with MQTT pub/sub strings
# as well as other device information
# is using tools devloped for home-broker
def task():
    q = queue.Queue()
    msg = message.message(q) 
    # This just loops publishing requests and subscribing for stuff back
    # when the queue times out it resends the set of pub/sub just for stress tersting
    # It is ued to load test home-broker
    cnt = 0
    while True:
        cnt += 1
        if cnt > 100000:
            break
        try:
            item = q.get(timeout=2) 
        except queue.Empty:
            #imed out so now get devices
            msg.publish(request_MQTT_Devices, publish_payload)
            msg.subscribe(subscribed_MQTTDevices)
            continue  
        except:  # not sure anything is left
            continue
        command = item[0]
        print("Item from queue cmd[%s]" % command)
        if command == "callback":
            topic = item[1]
            payload = item[2]
            print("Item from queue topic[%s] payload[%s]" % (topic, payload,))
            if topic == subscribed_MQTTDevices: # reply topic   
                devices(zlib.decompress(payload))
                pass
        elif command == "connected":
            msg.publish(request_MQTT_Devices, publish_payload)
            msg.subscribe(subscribed_MQTTDevices)

# simple device dump
# # designed to load/update two tables
# a devices table and a features table
# a device has 1 or more features.
# Each feature contains the proper pub/sub strings
# no status information is included or ever will be.  
def devices(jason_bytes):
    dev= json.loads(jason_bytes)
    all_devices = dev["devices"]
    for d in all_devices:
        print(d)
    all_features = dev["features"]
    for f in all_features:
        print(f)

if __name__ == "__main__":
    task()
