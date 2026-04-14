import time
import paho.mqtt.client as mqtt
import ssl
import cfg

xprint = print # copy print
my_name = "mqtt_manager"

xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    #xprint("send_emails args type", type(args))
    #if isinstance(args, tuple):
        #xprint ("args are a tuple", args)
    #xprint("send_emails args", args)
    try:
        if isinstance(args, tuple) :
            #xprint("tuple", args)
            area, comment = args[0].split(None,1)
            try: 
                comment += " "+" ".join(list(args[1:]))
            except Exception as e:
                #xprint(f"join exception {e}")
                exit()
            #xprint(f"area[{area}] comment[{comment}]")
            #area = args[0]
            # xprint("???", args)
            #comment = ""
        else:
            area, comment = args[0].split(None,1)    
        #area, comment = args[0].split(None,1)
        xprint("["+my_name+"/"+area+"]",comment, **kwargs)
    except:
        #xprint("except")
        xprint(f"[{my_name}]", *args, **kwargs) # the copied real print
        
# for topic in cfg.topics.keys():
            # print("on_connect subscribed to", topic, "dogpoo") 
# exit()
class mqtt_manager:
    def __init__(self, email_q):
        self.email_q = email_q
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        print(f"__init__ cfg.user[{cfg.user}], cfg.password [{cfg.password}]")
        self.client.username_pw_set(cfg.user, cfg.password)
        # Configure TLS/SSL settings
        # You can adjust cert_reqs based on your security requirements:
        # ssl.CERT_REQUIRED: Server must provide a valid certificate issued by a trusted CA.
        # ssl.CERT_OPTIONAL: Server may provide a certificate.
             # ca_certs=ca_certs_path, # Uncomment and set if you have a specific CA certificate
         # Or a higher version like ssl.PROTOCOL_TLS
       # ssl.CERT_NONE: No server certificate verification.
        #self.client.tls_set(cert_reqs=ssl.CERT_OPTIONAL) 
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        while True:
            print(f"__init__ connecting to [{cfg.broker}]-[{cfg.default_port}]")
            try:
                self.client.connect(cfg.broker,cfg.default_port)
                print ("__init__ connected")
                break
            except:
                print (f"__init__ could not connect to broker [{cfg.broker}],[{cfg.default_port}]")
                time.sleep(5)
        print("__init__ setting callbacks")
        self.client.on_connect=self.on_connect
        self.client.on_message=self.on_message
        self.client.loop_start()

    def publish_command(self, topic, payload):
        print("publish_command topic [%s] payload [%s]" % (topic, payload,))
        self.client.publish(topic, payload=payload)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print("on_connect connected, doing subscribes")
        for topic in cfg.topics.keys():
            print("on_connect subscribed:", topic)
            client.subscribe(topic)

    def on_message(self, client, userdata, message):
        print(f"on_message received message topic[{message.topic}] payload[{message.payload}]")
        if self.email_q.full():
            print("on_message >>>>> queue full can not put <<<<<< ")
            # should add a message to watchdog about the problem
        else:
            self.email_q.put([message.topic, message.payload], block=False)
            #print("on_message >> after email_q.put")

# this task is running as a seperate process
# publishing flow state on or off
# def task(shared, email_q, reciever):
    # #print("child_name")
    # #for i in range(1, 5):
        # #print(const.ColorRED,child_name,const.ColorEND)
    # shared = shared
    # mqtt_man=mqtt_manager(email_q)
    # #  we set up the button reception here I assume it is on change?
    # count = 0
    # while True:
        # try:
            # if (reciever.poll(const.children_sleep_time)):
                # data = reciever.recv_bytes()
                # print("poll returned =")  # data)
            # else:
                # print("poll pipe timed out")
        # except:
            # print("pipe broke")
            # pass
        # # message or timeout causes a send
        # #print("mqtt_manager", time.ctime())
        # #print("mqtt_manager pump [%s] on [%s]" % (shared[const.pump], const.pump_on,))
        # repeat = 1 #default normal a time-out send
        # #if (got_message == True):  # this is more importaint came from the pipe
            # #repeat = const.broadcast_repeat
        # if (shared[const.pump] == const.turn_pump_on):
            # #for _ in range(repeat):
            # mqtt_man.publish_command(alert.topic(),alert.payload_on())
        # else:
            # #for _ in range(repeat):
            # mqtt_man.publish_command(alert.topic(),alert.payload_off())

# for testing
if __name__ == "__main__":
    import multiprocessing
    q = multiprocessing.Queue(5)
    client = mqtt_manager(q)
    while True:
        print(" testing returned: ", q.get())
    # import array
    #  0)import multiprocessing
    # #shared = array.array('i',[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0])
    # shared = array.array('i',[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1])
    # child_notify_q = multiprocessing.Queue(5)
    # reciever, sender =  multiprocessing.Pipe(duplex=False)
    # children = multiprocessing.Process(target=task, args=(shared, child_notify_q, reciever))
    # children.start()


    # import alarm_button_simulator
    # print("testing, simulate being a remote jhw_led device")
    # alarm_button_simulator.button_with_led()   # this runs forever
    time.sleep(10000)




