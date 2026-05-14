#AlertAway startup/monitor process
'''MIT License Copyright (c) 2023,2024,2026 Jim Dodgen
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

#import load_zigbee_data
#import const
import database
import socket
import time
import os
import http_common as config

#
# conditional print
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#

def send_ssdp_alive(new_ip, bridge_uuid):
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900
    
    # This matches the Hue Bridge format Alexa expects
    msg = (
        "NOTIFY * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        "CACHE-CONTROL: max-age=100\r\n"
        f"LOCATION: http://{new_ip}:80/description.xml\r\n"
        "NTS: ssdp:alive\r\n"
        "NT: upnp:rootdevice\r\n"
        f"USN: uuid:{bridge_uuid}::upnp:rootdevice\r\n"
        "\r\n"
    )
    print(msg)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.sendto(msg.encode('utf-8'), (SSDP_ADDR, SSDP_PORT))

if __name__ == "__main__":
    # not working os.nice(-1)   # HTTP thread needs this
    print("AlertAway starting: Version[%s]" % (config.VERSION,))
    #
    db = database.database() #just to get tables created if needed
    db.close()
    print("database initilized if needed")
    #
    curr_ip = ""
    while True:
        ip = config.get_ip()
        if curr_ip != ip:
            curr_ip = ip
            send_ssdp_alive(ip, config.get_uuid())
        time.sleep(config.WATCHDOG_TIMER)  # testing 10 , a little longer in production
        
        
