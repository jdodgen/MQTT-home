# MIT Licence copyright 2026 Jim dodgen
# install Mosquitto #this had some breakage 
TESTING=True
def install_script():
    '''
  600  sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
  601  sudo apt-get update
  602  sudo apt update
  603  sudo apt install --reinstall ca-certificates
  604  sudo update-ca-certificates
  605  sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
  610  sudo rm /etc/apt/sources.list.d/shiftkey-packages.list
  611  sudo apt clean
  612  sudo apt update
  613  sudo apt install -y mosquitto mosquitto-clients
  619  systemctl status mosquitto.service
'''

