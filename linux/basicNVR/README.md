# basicNVR a symplified low overhead recorder
      
### Summary:

basicNVR is a lightweight Network Video Recorder (NVR) built around the popular motion software.    
It simplifies recording and managing video streams from IP cameras.    
It offers features like:    
Motion detection recording    
File management with automatic deletion    
SQLite database for recording information    
User interface for browsing recordings    
Admin interface for configuration    
HTTP access for streaming JPEGs (used by AlertAway)    
   
### Current Status:

The system is currently running successfully for several years on an Intel J5005 machine with Ubuntu 18.04.   
It manages 7 PoE IP cameras.   
The website (basicNVR.com) is registered but not yet active.    
   
### Planned Changes:

Implement pass-through streaming in motion (possibly using motionplus)     
Develop a tool (HTML) for creating "motion control masks"    
Switch internal communication from HTTP to MQTT (a lightweight messaging protocol)    
Improve the user interface    
Design website content for basicNVR.com    
### Additional Notes:

The system has gone through several iterations, starting with USB webcams and coaxial CCTV cameras before transitioning to fully utilizing ONVIF/RTSP cameras.   








 
