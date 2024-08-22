from ipcqueue import posixmq
import time
import threading
import message




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
    msg = message(q) # MQTT connection tool# 
    home_MQTT_devices = "home/MQTTdevices/configuration"  
    msg.subscribe(home_MQTT_devices)
    while True:
        (action, topic, payload) = q.get()
        if (action == "callback"):
            if (topic == home_MQTT_devices):
                check_and_refresh_devices(payload)
            else:
                # now processing a device callback action
                update_device_state(topic,payload)


    msg.publish("message_unit_test/demo_wall/set", '{"state": "on"}')
    msg.publish("message_unit_test/jake/set", '{"state": "on"}')
    msg.subscribe("message_unit_test/joe/")
    msg.subscribe("message_unit_test/jake/#")
    msg.subscribe("message_unit_test/motion/#")
    msg.subscribe("message_unit_test/demo_wall/#")
    time.sleep(2) # prettier  output
    # this handles callbacks from above
    while True:
        msg = q.get()
        print("message_unit_test: q.get()", msg)

def check_and_refresh_devices(payload):
    pass

def update_device_state(topic,state):
    pass