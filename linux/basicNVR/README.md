This is raw code from a working system.    
I placed the code here to open source under MIT licence.       
Also a github is a better place for source_verson control.   
   
Planned changes:      
implement pass through streaming in ["motion"](https://motion-project.github.io/index.html)  including
An upgrade of [motion](https://motion-project.github.io/index.html) to [motionplus](https://github.com/Motion-Project/motionplus)    
Find or make a html tool to build a "motion control mask" used by "motion".      
Convert internal communication from http to mqtt.      
Make the http interfaces prettier.  
Create cool html stuff for basicNVR.com.
   
The current system has been running solid for years, only rebooting when being updated.    
current system is 7 IP cameras most PoE.        
running on a Intel J5005 8Gb,  Ubuntu 18.04. 


basicNVR.com domain is registered.  Note that he web site is not active, see: "planned changes". 

The system has evolved from using USB webcams and COAX connected surplus CCTV cameras to now only ONVIF/RTSP cameras.   
"motion" is doing the heavy lifting. basicNVR configures "motion" where to drop the files and how to record the location in a sqlite database.
It automaticly deletes old stuff when the disk gets full.
Simple user interface for browsing cameras over time.
Admin has a different interface for configuration.    
It serves jpgs via HTTP to alertaway as well as a web page.

to be continued ...







 
