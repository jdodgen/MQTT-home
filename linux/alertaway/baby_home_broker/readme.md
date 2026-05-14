
# NanoPI-NEO LTS MQTT Broker
Download:  h3-sd-friendlycore-xenial-4.14-armhf-20210618.img.gz see [friendlyelec](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_NEO#UbuntuCore_16.04)   
This is built off of Ubuntu 16.04 LTS,  I think it is the most solid distro for the NEO.  When installed below the MicroSD cards need no configuration.
Just plug it into the back of your router. 
The MQTT Broker is found as ```home-broker.local``` on the subnet.  

Un zip and use  "raspberry pi installer" or "Win32 Disk Imager"  to create your MicroSD boot card.
If you plan on replicating the MicroSD cards. I find that it is best to creat a master MicroSD that is smaller that the replicated ones.
This is because SD cards of a stated size can be sightly different. If the target is smaller it will eventualy crash.     

plug everything into the NEO including the LAN. Now you have to find its IP address 
Search for ip with nmap one time with it plugged in and another with it unplugged.

connect via ssh or putty
Login: pi password pi
first change password
```
passwd
sudo apt -y update
sudo  apt upgrade
sudo hostnamectl set-hostname home-broker
sudo vi /etc/hosts
```
Change line ```127.0.1.1   NanoPi-NEO``` to ```127.0.1.1   home-broker```
you can use npi-config if it came with your distro.    
good to reboot after changing host name
Only install  mosquitto, a MQTT broker and add an config file
```
sudo apt -y install mosquitto
sudo vi  /etc/mosquitto/conf.d/home-broker.conf
```
Paste this in
```
allow_anonymous true
listener 1883
log_dest none
autosave_interval 0
autosave_on_changes false
```
```ESC :w``` to save the file.    
Our use the editor of your choice      

Now check out the config for cut and paste errors:
```
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
```
Avahi helps with multicast DNS and IoT MQTT discovery
```
sudo apt -y install avahi-daemon
sudo shutdown now
```
Shut it down and use  "Win32 Disk Imager" or equivlent to back it up
Now you can make copies. Just use a identical or larger MicroSD card. 

## Now you have a MQTT broker
anything that can ping it can use it.



