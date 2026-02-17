import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("192.168.253.253", 50000))
ipaddrx =  s.getsockname()[0]
with open("ipaddr.txt", "w") as text_file_out:
    text_file_out.write(ipaddrx)
print("(%s)" % (ipaddrx))

# Example
try:
    with open("ipaddr.txt", "r") as text_file:
        ipaddr = text_file.read()
except:
    ipaddr = None
print("[%s]" % (ipaddr))
    

