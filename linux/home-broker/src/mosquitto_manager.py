# mosquitto_manager
# a subroutine library to support mosquitto
# currently this does nothing just a task that sleeps in a loop
# future mods should more management
# For now it just forces mosquitto to reload config
# see cfg below to change
#
import os, signal
import time
import const
from  pgrep import pgrep
import multiprocessing
#
# conditional print
import os 
my_name = os.path.basename(__file__).split(".")[0]
xprint = print # copy print
def print(*args, **kwargs): # replace print
    #return
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
def print_always(*args, **kwargs): # replace print
    xprint("["+my_name+"]", *args, **kwargs) # the copied real print
#
#
def start_mosquitto_task():
    p = multiprocessing.Process(target=task)
    p.start()
    return p

def is_mosquitto_alive():
    result = pgrep("mosquitto")
    if not result:
        print("mosquitto not running")
        return None
    else:
        return result[0]

def reload_config():
    mos_config = open(const.mosquitto_file_path, "w")
    n = mos_config.write(const.mosquitto_configuration)
    mos_config.close()
    pid = is_mosquitto_alive()
    if not pid:
        return False
    print("mosquitto pid[%s]" % (pid,))
    os.kill(pid, signal.SIGHUP)   # tells mosquitto to reload config
    return True

def task():
    # this allows us to control mosquitto
    # If sleeping a reboot was expected to refresh mosquitto
    # if a wake then we are now trying to start and stop mosquitto
    result = reload_config()
    if not result:
        print("reload_config detected mosquitto is not running")
    while True:
        # mosquitto happer when run as a service to this is just here to drop the config
        # I need a signal or something to get a re-read from mosquitto. for now just need a reboot
        #subprocess.run(["/usr/sbin/mosquitto", "-c", const.mosquitto_file_path,]) # '-v'])
        ## never returns, I hope :)
        #print("mosquitto exited, waiting and restarting")
        # future will be 
        time.sleep(const.mosquitto_sleep_seconds)   # asleep as you see Zzzzzzzz

if __name__ == "__main__":
    #reload_config()
    task()
    time.sleep(11111)
