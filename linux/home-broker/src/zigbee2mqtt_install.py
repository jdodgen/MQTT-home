# MIT Licence copyright 2026 Jim dodgen
# install z2m and Mosquitto 
TESTING=False
systemd_path = "/etc/systemd/system"

def install_script():
    '''
    # bash commands will error
    # usualy run one command at a time
    #
    
    sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa

    sudo apt-get update

    # Install latest nodejs from snap store
    # The --classic argument is required here as Node.js needs full access to your system in order to be useful.
    # You can also use the --channel=XX argument to install a legacy version where XX is the version you want to install (we need 14+).
    
    sudo snap install node --classic
    
    corepack enable
    
    # if above fails then try a different way
    sudo npm install -g corepack
    
    corepack enable

    # Verify node has been installed
    # If you encounter an error at this stage and used the snap store instructions, adjust the BIN path as follows:
    ## PATH=$PATH:/snap/node/current/bin
    # then re-verify Node.js as above
    
    node --version

    # Set up Node.js repository, install Node.js and required dependencies.
    # NOTE 1: Older i386 hardware can work with [unofficial-builds.nodejs.org](https://unofficial-builds.nodejs.org/download/release/v20.9.0/ e.g. Version 20.9.0 should work.
    # NOTE 2: For Ubuntu see installing through Snap below.
    
    sudo apt-get install -y curl
    
    sudo curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    
    sudo apt-get install -y nodejs git make g++ gcc libsystemd-dev
    
    corepack enable

    # Verify that the correct Node.js version has been installed
    
    node --version  # Should output LTS versions V20.x or newer

    # Create a directory for zigbee2mqtt and set your user as owner of it
    
    sudo mkdir /opt/zigbee2mqtt
    
    sudo chown -R ${USER}: /opt/zigbee2mqtt

    # Clone Zigbee2MQTT repository
    
    git clone --depth 1 https://github.com/Koenkk/zigbee2mqtt.git /opt/zigbee2mqtt

    # Install dependencies (as user "pi")
    
    cd /opt/zigbee2mqtt
    
    pnpm install --frozen-lockfile

    # test with 
    
    cd /opt/zigbee2mqtt
    pnpm start
    
    # need serial port to the zigbee dongle
    
    ls -l /dev/serial/by-id
    # returns somthing like this: 
    
    serial_port = "usb-Silicon_Labs_CP2102N_USB_to_UART_Bridge_Controller_188d8292a693eb118170194f3d98b6d1-if00-port0"
    
    # dialout liets you use the ports
    sudo usermod -a -G dialout $USER
    
    edit opt/zigbee2mqtt/data/configuration.yaml
    add 
    serial:
       port: /dev/serial/by-id/usb-Texas_Instruments_TI_CC2652P_Unit_Identifier_Here
    '''
    
z2m_service = '''
[Unit]
Description=zigbee2mqtt
After=network.target mosquitto.service
# If z2m can't talk to Mosquitto, it will crash, so we require it
Requires=mosquitto.service

[Service]
Environment=NODE_ENV=production
ExecStart=/usr/local/bin/pnpm start
WorkingDirectory=/opt/zigbee2mqtt
StandardOutput=journal
StandardError=journal
Restart=always
RestartSec=10s
User=jim

[Install]
WantedBy=multi-user.target
'''
    
file_name = f"{systemd_path}/zigbee2mqtt.service"
# if TESTING:
    # print(z2m_service)
# else:
    # with open(file_name, "w") as f:
        # f.write(z2m_service)
        # print(f"Created: {file_name}")
        
        
        
import subprocess

def write_as_root(content, filepath):
    # Use 'sudo tee' to write to a file owned by root
    process = subprocess.Popen(['sudo', 'tee', filepath], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    process.communicate(input=content)

write_as_root(z2m_service, file_name)

print("Run: sudo systemctl daemon-reload")
print("Run: sudo systemctl enable --now zigbee2mqtt.service")
