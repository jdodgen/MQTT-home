# MIT Licence copyright 2026 Jim dodgen
# systemd install of AlertAway processes
# it is assumed that zigbee2mqtt and Mosquitto are installed in systemd 
# see z2m_mosquitto.py for terminal commands
#
import os
TESTING = False
PYTHON_FILES = os.getcwd()
DATA_FILES = PYTHON_FILES
#
systemd_path = "/etc/systemd/system"
#
# alertaway independent processes
modules = [
    
    ("alertaway-main_http",                 "main_http.py",         "HTTP Server & UI", 10),
    ("alertaway-timers-http",               "timers_http.py",       "Maintain timers", 1),
    ("alertaway-voice-http",                "voice_http.py",        "Maintain Voices", 1),
    ("alertaway-events_http",               "events_http.py",       "Maintain email events", 10),
    ("alertaway-triggers-http",             "triggers_http.py",      "Maintain triggers", 10),
    ("alertaway-config-http",                "config_http.py",      "Maintain configuration", 10),
    ("alertaway-camera-http",                "camera_http.py",      "Maintain cameras", 10),
    ("alertaway-email-http",                 "email_http.py",       "Maintain emails", 10),
    
    ("alertaway-timers-daemon",             "timers_daemon.py",     "Monitoring Timers ", 10),
    ("alertaway-triggers-daemon",           "triggers_daemon.py",   "Trigger & Event Logic", 10),
    ("alertaway-send_emails_daemon",        "send_emails_daemon.py","Email Notifications", 10),
    ("alertaway-fauxmo_manager",            "fauxmo_manager.py",    "Runs fauxmo/WeMo", 10),
    ("alertaway-mqtt_service_task",         "mqtt_service_task.py", "MQTT Integration", 10), 
]

def generate_files():
    # 1. Generate the systemd Master Target File
    target_name = "alertaway.target"
    wants = " ".join([f"{m[0]}.service" for m in modules])
    target_content = f"""[Unit]
Description=AlertAway Home Broker Master Stack
Wants=mosquitto.service zigbee2mqtt.service {wants}

[Install]
WantedBy=multi-user.target
"""
    if TESTING:
        print(target_content)
    else:
        with open(f"{systemd_path}/{target_name}", "w") as f:
            f.write(target_content)
        print(f"Created: {target_name}")

    # 2. Generate Individual Service Files
    for name, script, desc , RestartSec in modules:
        addl_services  =  None  if script == "main.py" else "main_py.service"
        service_content = f"""[Unit]
Description=AlertAway Module: {desc}
PartOf=alertaway.target
After=network.target {addl_services}

[Service]
ExecStart=/usr/bin/python3 {PYTHON_FILES}/{script}
WorkingDirectory={DATA_FILES}
Restart=always
RestartSec={RestartSec}
User=jim
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=alertaway.target
"""
        file_name = f"{systemd_path}/{name}.service"
        if TESTING:
            print(service_content)
        else:
            with open(file_name, "w") as f:
                f.write(service_content)
                print(f"Created: {file_name}")

if __name__ == "__main__":
    generate_files()
    print("\nNext steps:")
    print(f"1. Move these files to {systemd_path}")
    print("2. Run: sudo systemctl daemon-reload")
    print("3. Run: sudo systemctl enable --now alertaway.target")
