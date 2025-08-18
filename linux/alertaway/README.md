This is a conversion in progress.    
Original written Perl around 2011.  
This conversion is now using mqtt-home   
Removing all the zigbee/xbee and wemo/fauxmo stuff, which is now done buy home-broker   
alertaway runs a few forked processes and communicates through POSIX message queues for both Perl and Python.     
See [http://alertaway.com] for the orignal concept

Progress:
Testing message queue between python and the perl code.
event driven Photo mailer being converted to mqtt and python
17-Aug-2025   
aav6 - is the current working version     
src - is the deveopment area.



