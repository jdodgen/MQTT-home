from ipcqueue import posixmq
import time
import threading
import message
import json




# testing Perl QueueManger.pm to have it handle python pickled messages  as well as perl "Storable"
# send to perl example 
# rq= posixmq.Queue('/ReceiveQueue')
# while True:
#     print("sending message")
#     rq.put({"name": "python water_sensor_2", "value": "foobar to you"})
#     print(rq.qsize())
#     time.sleep(4)

# receive from perl example
# rq= posixmq.Queue('/SendQueue')
# while True:
#     print("sending message")
#     try:
#         msg = rq.get(timeout=None)
#     except:
#         print("problem getting message")
#     print(rq.qsize())
#     print(msg)

def device_features_task():  # keep device features updated in the data base 
    # handle the subscribe to the home-broker devices
    # for each subscribe callback compare to last
    # update differences only NO state information
    import message
    import queue 
    q = queue.Queue() # callbacks are sent here
    msg = message.message(q) # MQTT connection tool# 
    current_devices = "home/MQTTdevices/configuration"  # current devices
    msg.subscribe(current_devices)
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            if (topic == current_devices):
                check_and_refresh_devices(payload)
            else:
                update_device_state(topic,payload)


    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # prettier  output
    # this handles callbacks from above

def check_and_refresh_devices(payload):
    unzipped = zlib.decompress(payload)
    devices_dictionary = json.loads(unzipped)
    all_devices(devices_dictionary)


# simple device dump/print
# # designed to load/update two tables
# a devices table and a features table
# a device has 1 or more features.
# Each feature contains the proper pub/sub strings
# no status information is included or ever will be.  
def all_devices(jason_bytes):
    all_devices = dev["devices"]
    for d in all_devices:
        print(d)
    all_features = dev["features"]
    for f in all_features:
        print(f)


def update_device_state(topic,state):
    pass

if __name__ == "__main__":
    device_features_task()