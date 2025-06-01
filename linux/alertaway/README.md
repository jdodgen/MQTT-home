This is a conversion in progress.    
Original written Perl around 2011.  
This conversion is now using mqtt-home   
Removing all the zigbee/xbee and wemo/fauxmo stuff, which is now done buy home-broker   
alertaway runs a few forked processes and communicates through POSIX message queues for both Perl and Python.     
See [http://alertaway.com/archive] for the orignal concept

Progress:
currently working on mqtt_processor.py
Updatingthe database with both mqtt configuration as well as the callbacks   
from the subscribes.   
This has pulled in a modified db.pm as well as some common python code   

