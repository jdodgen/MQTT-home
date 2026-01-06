import time
import paho.mqtt.client as mqtt
import ssl
import cfg

xprint = print # copy print
my_name = "[mqtt_manager]"
def print(*args, **kwargs): # replace print
    #return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

class mqtt_manager:
    def __init__(self):
        self.client = mqtt.Client()
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
        try:
            print("connecting to [%s]" % (cfg.broker))
            self.client.connect(cfg.broker,8883)
            print ("connected")
        except:
            print ("could not connect")
            exit()
        print("starting")
        self.client.loop_start()
        
    def publish(self, topic, payload):
        self.client.publish(topic, payload)
        print("Publshed t[%s], p[%s]" % (topic, payload))

# for testing
if __name__ == "__main__":
    client = mqtt_manager()
    client.publish("home/test/test", "test")
    time.sleep(10000)




