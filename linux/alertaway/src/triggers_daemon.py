# MIT License Copyright 2026 Jim Dodgen

import asyncio
import aiomqtt

xprint = print 
my_name = "[triggers_daemon]"
def print(*args, **kwargs): 
    xprint(my_name, *args, **kwargs) 

class AsyncTriggersDaemon:
    def __init__(self):
        self.triggers = {}
        self.db = None      # Replace with your async DB client
        self.client = None  # Replace with your async MQTT client

    def load_triggers(self):
        db = database.database(row_factory=True)
        raw_triggers = db.get_all_triggers()
        db.close()
        self.triggers.clear()
        for t in raw_triggers:
            pub_topic = t["ptopic"]
            pub_payload = t["pub_payload"].encode()
            sub_topic = t["stopic"]
            sub_payload = t["sub_payload"].encode()
            if sub_topic not in self.triggers:
                self.triggers[sub_topic] = {}
            if sub_payload not in self.triggers[sub_topic]:
                self.triggers[sub_topic][sub_payload] = []  
            self.triggers[sub_topic][sub_payload].append([pub_topic, pub_payload])
        print(f"Trigger structure updated: {self.triggers}")

    async def handle_message(self, topic: str, payload: bytes):
        """Processes incoming MQTT messages without blocking other tasks."""
        if topic not in self.triggers:
            return

        if payload in self.triggers[topic]:
            print(f"Processing topic: {topic} with payload: {payload}")
            things_to_pub = self.triggers[topic][payload]
            
            # Publish all target messages concurrently
            tasks = [
                self.client.publish(pub_topic, pub_payload) 
                for pub_topic, pub_payload in things_to_pub
            ]
            await asyncio.gather(*tasks)
        else:
            print(f"Unknown payload for topic {topic}: {payload}")

    async def mqtt_loop(self):
        reconnect_delay = 1  # Start with a 1-second delay on disconnect
        while True:
            try:
                print("Connecting to MQTT broker...")
                async with aiomqtt.Client("localhost") as client:
                    self.client = client
                    self.load_triggers()
                    
                    for sub_topic in self.triggers:
                        await client.subscribe(sub_topic)
                    
                    # Connection successful, reset the backoff delay
                    reconnect_delay = 1
                    print("MQTT connection established and topics subscribed.")

                    async for message in client.messages:
                        try:
                            # Inner try/except: A bad message shouldn't drop the connection
                            await self.handle_message(message.topic.value, message.payload)
                        except Exception as msg_err:
                            print(f"Error processing message on {message.topic}: {msg_err}", exc_info=True)
            except aiomqtt.MqttError as net_err:
                # Handle expected network/broker drops
                print(f"MQTT connection lost: {net_err}. Retrying in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)  # Exponential backoff up to 1 minute
            except Exception as critical_err:
                # Handle completely unexpected bugs (e.g., database failures during load_triggers)
                print(f"Unexpected daemon error: {critical_err}", exc_info=True)
                await asyncio.sleep(5)  # Safe delay before trying to boot up again

async def main():
    daemon = AsyncTriggersDaemon()
    await daemon.mqtt_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Daemon stopped safely.")
