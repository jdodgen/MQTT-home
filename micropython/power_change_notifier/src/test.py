import network
import utime
from umqtt.simple import MQTTClient

def cback(t,m): # call back
    print("call back:", t, p)
    
def connectMQTT():
    client = MQTTClient(client_id=b"jims_test",
        server=broker,
        port=0,
        user=user,
        password=password,
        keepalive=7200,
        ssl=True,
        ssl_params={'server_hostname': broker})
    client.connect()
    client.set_callback(cback)
    return client
    
### start ###
ssid = "danger"
password = "will roberson"
broker="26d590584befaf4655dsewa81048787c9d32f80.s1.eu.hivemq.cloud"  #'home-broker.local'
user = "change"
password = "password"
wifi = network.WLAN(network.STA_IF)
wifi.active(True)
try:
    wifi.connect(self._ssid, self._wifi_pw)
    if (wifi.status() == network.STAT_WRONG_PASSWORD):
        print("ERROR_BAD_PASSWORD")               
    elif (wifi.status() == network.STAT_NO_AP_FOUND):
        print("ERROR_AP_NOT_FOUND")
    print("wifi.connect wifi.status", wifi.status())
except:
    print("exception doing wifi.connect status[]", wifi.status(),"]")

### now test mqtt/ssl
topic="test_topic"
value="test_value"  
 
client = connectMQTT() 
client.subscribe(topic)
client.publish(topic, value)
utime.sleep(60)



