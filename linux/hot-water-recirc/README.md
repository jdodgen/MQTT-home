//configuration
install 32 bit lite Rpi os

using the "raspberry pi imager"
make selections then after "next"
press "edit settings"
set host name "hot-water"
set all the general tab to your stuff
and in services tab enable SSL
then apply settings make image

insert sdcard, 
boot and login from console

// save ip address for putty/filezilla later if you forget host name 
// or running on another subnet
// access it host name like this http://hot-water.local if on your subnet
// if it is a different subnet then you will need the IP address

ip a

raspi-config

reduce GPU memory to as small as it will let you
system options > boot autologin > Console Autologin
resize filesystem

reboot

// updating the system is easer using putty or simular
// from your workstation

sudo apt update
sudo apt upgrade

sudo apt install sqlite3
sudo apt install pip
sudo apt install python3-gevent
sudo apt install python3-flask
sudo apt install python3-paho-mqtt

// add to end of .bashrc
// note don't do the "sudo reboot" until it is working
// note the "back quotes" on the echo
sleep 10
sudo python3 main.py
sudo echo `date` >> bootlog
sudo reboot

// now system is built and needs the controler code

// send the following files using sftp (filezilla)
// from "water_heater_recirc/Python" directory
// to /home/<username>/ 

main.py
mqtt_manager.py
database.py
const.py
run_pump_cycle.py
rpi_interface.py
web_server.py
index_html.py
status_html.py
MQTT_messages.py
device_dictionaries.py

// Best to test first from putty and not via a boot
// just to see if all workstation










