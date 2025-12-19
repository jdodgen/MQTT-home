# MIT license copyright 2025 Jim Dodgen
# simple_emailer is built off of Power Change Notifier
# this publishes "power" message
# requires only a MQTT Broker. Local or in the Cloud
#
VERSION = (1, 0, 1)

from mqtt_manager import mqtt_manager
import cfg
import time

#client = None
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return # comment/uncomment to turn print on off
    xprint("[pcn_health]", *args, **kwargs) # the copied real print 

def main():
    client = mqtt_manager(None)
    while True:
        client.publish_command(cfg.publish,"up")
        time.sleep(30)

############ startup ###############
print("run __name__ = %s" %__name__)
if __name__ == "__main__":
    main()
print("exiting, should not get here")
