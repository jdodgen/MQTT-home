# ESP32-S2 setup information
This is a ubuntu/linux Deployment
Other OS's will have differences.
```
# when USB connected: 
# Press AND HOLD the button labelled 0
# then press the RESET button, then release both
# and it should appear as a serial device.
# This is common to all ESP32-S2's, it's not just "S2 Mini" board.
# note USB port/dev/ttyACM0 will need to have permission
#
# this makes things simpler so do this and logout and in
sudo usermod -a -G dialout $USER
```

# linux  install tools 
```
sudo pip install esptool --break-system-packages
sudo apt install picocom 
sudo pip install adafruit-ampy --break-system-packages
```
this is here for cut and paste
```
sudo chmod 666 /dev/ttyACM0
```
download the latest ESP32_GENERIC bin and copy the location to be used in [src/install.py](src/install.py)
does this work?
```
esptool.py --port /dev/ttyACM0 erase_flash
esptool.py --chip esp32s2 --port /dev/ttyACM0 write_flash -z 0x1000 ../ESP32_GENERIC_S2-20240105-v1.22.1.bin
picocom -b 115200 /dev/ttyACM0
```
The above works, so flash code to the mc   
after configuring [src/install.py](src/install.py)
