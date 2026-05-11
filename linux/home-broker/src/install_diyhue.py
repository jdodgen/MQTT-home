# MIT Licence copyright 2026 jim dodgen

install_script =
"""
   # Manual Code Installation

   # 1. Clone the Repo:
   sudo cd /opt
   sudo git clone https://github.com/diyhue/diyHue.git
   cd diyHue/BridgeEmulator

   # 2. Install Dependencies: Ensure you have Python 3 and the required libraries installed:

   sudo pip3 install ws4py requests astral paho-mqtt

   # 3. Run Manually: Execute the main script with root privileges to allow it to bind to port 80:

   sudo python3 HueEmulator.py

   # Configure MQTT Broker [4] 
   # To connect diyHue to your broker, you must edit the config.json file. 
   # This file is typically created in the directory where you run the emulator after the first start/

   # 1. Ctrl + C  the HueEmulator.
   
   # 2. Edit config.json: Locate the mqtt section and fill in your broker details:

   "mqtt": {
       "enabled": true,
       "mqttServer": "127.0.0.1", 
       "mqttPort": 1883,
       "mqttUser": "",
       "mqttPassword": "",
       "discoveryPrefix": "alertaway"
   }

   # now the discovery topic is "alertaway/light/[friendly_name]/config" 
   

"""
