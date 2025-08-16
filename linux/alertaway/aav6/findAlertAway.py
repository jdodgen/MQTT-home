import tkinter as tk
from tkinter import simpledialog, messagebox, Text, INSERT, END
import http.client, socket, os
import platform    # For getting the operating system name
import subprocess
import ipaddress
import json
import concurrent.futures
import webbrowser
import time

active_hosts= {"active_ip_addrs": []}
inactive_hosts= {"inactive_ip_addrs": []}
jhw_servers = []
ADDRESS_RANGE = range(1,255)


def check_port_80(url, timeout=10):
    """
      makes a http request to given url:port
      and returns status: True/False and message: 'OK'/'Connection refused'print
    """
    #print ("found :", url,"now connect port 80")
    h = http.client.HTTPConnection(url, 80, timeout=timeout)
    status = False
    try:
        h.request('GET','/whoareyou')
        r = h.getresponse()
        msg = str(r.reason) + ' ' + str(r.status)
        # OK 
        if r.status == 200:
            print(url,  end='', flush=True)
            chunk = r.read(20)
            print("---- returned", chunk)
            if (chunk == b'alertaway'):
                #print("---- got one", url);
                status = True
    except (socket.error) as e:
        msg = e.strerror
    except:
        msg = 'Unexpected error'
    #print("result = ", msg, url)
    return status, url + ':' + ' ' + str(msg)

def get_subnet():
   ip = '127.0.0.1'
   try:
       ip = socket.gethostbyname(socket.gethostname())
   except (socket.error) as e:
       s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
       s.connect(("8.8.8.8", 80))
       ip = s.getsockname()[0]
       s.close()      
   base = ip[0:ip.rfind('.')+1]
   ROOT = tk.Tk()
   ROOT.withdraw()
   ROOT.geometry('350x200')
   text = Text(ROOT)
   text.insert(INSERT, "Hello.....")
   text.insert(END, "Bye Bye.....")
   text.pack()
# the input dialog
   subnet = simpledialog.askstring(title="fastFindHotWater",
                                  prompt="Subnet to Search?:",
                                  initialvalue=base)
   #ROOT.withdraw()                               
   #print ("Use Local?", base)
   #subnet = input()
   if len(subnet) == 0:
       subnet=base
   else:
       if subnet[-1] != '.':
           subnet = subnet + "."       
   messagebox.showwarning("","Working ...")
   #print("using ... ", subnet)
   return subnet


def pingda(ip_addr):
    #print ("Checking:", ip_addr)
    param = '-n' if platform.system().lower()=='windows' else '-c'
    command = ['ping', param, "1", "-w", "100", ip_addr]
    try:
        subprocess.check_output(command)
        active_hosts["active_ip_addrs"].append(ip_addr)
    except:
        ##inactive_hosts["inactive_ip_addrs"].append(ip_addr)
        progress = '.'      
    else:
        progress = '+'
        try:
            status, message = check_port_80(ip_addr)
            if status:
                jhw_servers.append(ip_addr)
        except:
            ##print("check 80 failed")
            pass
    #print(progress, end='', flush=True)

def get_neighbor_ips(ip):
    print("base is: ", ip)
    """ Get all neighbor IP's for given IP """
    ips = []  
    for extension in ADDRESS_RANGE:
        neighbor = ip + str(extension)
        # exclude current ip
        if neighbor != ip:
            ips.append(neighbor)
        #print("IP's ",neighbor) 
    return ips

    
#network = ipaddress.ip_network(input("Enter the network to scan : "))
#


subnet_ip = get_subnet()
ips = get_neighbor_ips(subnet_ip)
print('Searching LAN for "Jeds hot water" controller')    
executor = concurrent.futures.ThreadPoolExecutor(254)

ping_hosts = [executor.submit(pingda, str(ip)) for ip in ips]

concurrent.futures.wait(ping_hosts,return_when=concurrent.futures.ALL_COMPLETED)

if (len(jhw_servers) == 0):
    messagebox.showerror('fastFindHotWater', "No controlers were found, check to see if WIFI is set correct.")
    print("\nERROR: no controlers were found, check to see if WIFI is set correct.")
    #input()
else:
    for ip in jhw_servers:
        webbrowser.open('http://'+str(ip))
        print("\nFound ", ip)
    time.sleep(3)
