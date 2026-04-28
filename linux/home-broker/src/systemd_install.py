import os

init_service="alertaway-main.service"

# Define your modular components
modules = [
    ("alertaway-http",    "main_http.py", "HTTP Server & UI"),
    ("alertaway-timers",  "timers_daemon.py", "Timer Logic"),
    ("alertaway-triggers", "triggers_daemon.py", "Trigger & Event Logic"),
    ("alertaway-emailer", "simple_emailer_daemon.py", "Email Notifications"),
    ("alertaway-mqtt", "mqtt_service_task.py", "MQTT Integration")
]

# Base directory for your project
install_path = "/opt/alertaway"
systemd_path = "/etc/systemd/system"

def generate_files():
    # 1. Generate the Master Target File
    target_name = "alertaway.target"
    wants = " ".join([f"{m[0]}.service" for m in modules])
    target_content = f"""[Unit]
Description=AlertAway Home Broker Master Stack
Wants=mosquitto.service zigbee2mqtt.service {wants}

[Install]
WantedBy=multi-user.target
"""
    with open(target_name, "w") as f:
        f.write(target_content)
    print(f"Created: {target_name}")

    # 2. Generate Individual Service Files
    for name, script, desc in modules:
        service_content = f"""[Unit]
Description=AlertAway Module: {desc}
PartOf=alertaway.target
After=network.target {addl_services}

[Service]
ExecStart=/usr/bin/python3 {install_path}/{script}
WorkingDirectory={install_path}
Restart=always
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=alertaway.target
"""
        file_name = f"{name}.service"
        with open(file_name, "w") as f:
            f.write(service_content)
        print(f"Created: {file_name}")

if __name__ == "__main__":
    generate_files()
    print("\nNext steps:")
    print(f"1. Move these files to {systemd_path}")
    print("2. Run: sudo systemctl daemon-reload")
    print("3. Run: sudo systemctl enable --now alertaway.target")
