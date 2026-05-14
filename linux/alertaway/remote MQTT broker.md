# this is the install on a VPS running ubuntu

```
sudo apt install mosquitto
```

## create config
```
sudo vi /etc/mosquitto/conf.d/home_broker.conf
```   
paste this:
```
listener 1883
password_file /etc/mosquitto/password_file
log_dest none
autosave_interval 0
autosave_on_changes false
```   

```i``` to insert   
then paste above   
```<ESC>:wq``` to save and exit

Check it
```
more /etc/mosquitto/conf.d/home_broker.conf
```

# create a user and password
```
sudo mosquitto_passwd -c /etc/mosquitto/password_file <user> <password>

sudo systemctl restart mosquitto

sudo systemctl status mosquitto
```
