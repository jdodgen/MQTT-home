from universal_mqtt_as import config, MQTTClient, asyncio
import feature_alert
import feature_button
import mqtt_hello
import mqtt_cfg

import alert_handler


our_name = "Alarm_button"

# esp32-s2 mini pins
led_pin = 3
piezo_pin = 11
button_pin = 7

alert  = feature_alert.feature("hot_water_controller",subscribe = True)
butt   = feature_button.feature(our_name, publish=True)

# Local configuration
config['server'] = mqtt_cfg.server
# Required on Pyboard D and ESP32. On ESP8266 these may be omitted (see above).
config['ssid'] = mqtt_cfg.ssid
config['wifi_pw'] = mqtt_cfg.wifi_pw

ah=alert_handler.alert_handler(led_pin=led_pin, piezo_pin=piezo_pin)
ah.flash(count=2) # lets you know it has booted

async def callback(topic_in, msg_in, retained):
    topic = topic_in.decode('utf-8')
    msg = msg_in.decode('utf-8')
    print("callback: topic[%s]" % (topic,))
    if (topic == alert.topic()):
        print((topic, msg, retained))
        if (msg == alert.payload_on()):
            ah.turn_on()
        else:
            ah.turn_off()
    elif (topic == mqtt_hello.hello_request_topic):
        print("callback hello_request")
        await say_hello(client)

async def say_hello(client):
 # who am I sends a hello 
    await mqtt_hello.send_hello(client, our_name, 
            "visual and audio notifier with push button", 
            alert.feature_json(), 
            butt.feature_json(),
            )
    
async def conn_han(client):
    print("conn_handler called")
    await client.subscribe(alert.topic())
    await client.subscribe(mqtt_hello.hello_request_topic)  
    await say_hello(client)
   
async def main(client):
    btn=button.button(button_pin)
    while True:
        print("checking client connection")
        try:
            await client.connect()
        except Exception as e: 
            print(e)
            await asyncio.sleep(1)
        else:
            break
    while True:
        await asyncio.sleep(0.3)
        if (btn.test() == 0):
            await client.publish(butt.topic(), butt.payload_on())

config['subs_cb'] = callback
config['connect_coro'] = conn_han

MQTTClient.DEBUG = True  # Optional: print diagnostic messages
client = MQTTClient(config)
try:
    asyncio.run(main(client))
finally:
    client.close()  # Prevent LmacRxBlk:1 errors
