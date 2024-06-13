import socket
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("192.168.253.253", 50000))
    return s.getsockname()[0]

print(get_ip_address())

Not sure why they did this but paho-mqtt 2.0.0 breaks ALL existing implementations.
more info here
https://github.com/eclipse/paho.mqtt.python/releases/tag/v2.0.0