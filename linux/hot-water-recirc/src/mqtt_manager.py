import time
import const
import paho.mqtt.client as mqtt
import feature_alert
import feature_button
import mqtt_hello

our_name = "hot_water_controller"
our_description ="tankless water heater recirc controller"

alert  = feature_alert.feature(our_name, publish=True)
butt = feature_button.feature("Alarm_button", subscribe = True)

xprint = print # copy print
my_name = "mqtt_manager"
def print(*args, **kwargs): # replace print
    # return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

class mqtt_manager:
    def __init__(self, flow_commands_q, who):
        self.flow_commands_q = flow_commands_q
        # self.mqtt_messages=MQTT_messages.MQTT_messages(device_dictionaries.hot_water_controler_device())

        #self.jhw_led=MQTT_master.MQTT_jhw_led()
        #mqttBroker ="mqtt.eclipseprojects.io"
        self.client = mqtt.Client() # mqtt.CallbackAPIVersion.VERSION2)
        try:
            print("connecting to [%s]" % (const.broker))
            self.client.connect(const.broker)
            print ("connect requested", const.broker)
        except:
            print ("could not connect", const.broker)
            # the loop will try later
        print("home/process/starting")
        self.client.on_connect=self.on_connect
        self.client.on_message=self.on_message
        self.client.loop_start()

    def publish_command(self, topic, payload):
        print("publish_command: topic [%s] payload [%s]" % (topic, payload,))
        self.client.publish(topic, payload=payload)

    def on_connect(self, client, userdata, flags, rc):
        print("on_connect connected")
        mqtt_hello.raw_send_hello(client, our_name, our_description,
            alert.get(),
            butt.get(),
            )
        client.subscribe(butt.topic())
        client.subscribe(mqtt_hello.hello_request_topic)
        print("on_connect initial button subscribe[%s]" % (butt.topic,))

    def on_message(self, client, userdata, message):
        print(">>> on_message received message topic[%s] payload[%s] <<<" % (message.topic, message.payload,))
        if (message.topic == mqtt_hello.hello_request_topic):
            mqtt_hello.raw_send_hello(client, our_name, our_description,
                alert.get(),
                butt.get()
                )
        elif message.topic == butt.topic():
            # the act of pushing button on remote thing
            # any input means a press.
            # print("on_button client[%s] userdata[%s]" % (client, userdata,))
            print(">>>> on_button received mesaage topic[%s] payload[%s]  <<<<" % (message.topic, message.payload,))
            if self.flow_commands_q.full():
                print("on_button >>>>> queue full cant put <<<<<< ")
                # should add a message to watchdog about the problem
            else:
                self.flow_commands_q.put([const.mqtt,0], block=False)
                print("on_button >> after q.put")

# this task is running as a seperate process
# publishing flow state on or off
def task(shared, flow_commands_q, reciever):
    #print("child_name")
    #for i in range(1, 5):
        #print(const.ColorRED,child_name,const.ColorEND)
    shared = shared
    mqtt_man=mqtt_manager(flow_commands_q,"jhw")
    #  we set up the button reception here I assume it is on change?
    count = 0
    while True:
        try:
            if (reciever.poll(const.children_sleep_time)):
                data = reciever.recv_bytes()
                print("poll returned =")  # data)
            else:
                print("poll pipe timed out")
        except:
            print("pipe broke")
            pass
        # message or timeout causes a send
        #print("mqtt_manager", time.ctime())
        #print("mqtt_manager pump [%s] on [%s]" % (shared[const.pump], const.pump_on,))
        repeat = 1 #default normal a time-out send
        #if (got_message == True):  # this is more importaint came from the pipe
            #repeat = const.broadcast_repeat
        if (shared[const.pump] == const.turn_pump_on):
            #for _ in range(repeat):
            mqtt_man.publish_command(alert.topic(),alert.payload_on())
        else:
            #for _ in range(repeat):
            mqtt_man.publish_command(alert.topic(),alert.payload_off())

# for testing
if __name__ == "__main__":
    import array
    import multiprocessing
    #shared = array.array('i',[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    shared = array.array('i',[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])
    child_notify_q = multiprocessing.Queue(5)
    reciever, sender =  multiprocessing.Pipe(duplex=False)
    children = multiprocessing.Process(target=task, args=(shared, child_notify_q, reciever))
    children.start()


    import alarm_button_simulator
    print("testing, simulate being a remote jhw_led device")
    alarm_button_simulator.button_with_led()   # this runs forever
    time.sleep(10000)




