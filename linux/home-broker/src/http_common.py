# MIT licence copyright 2026 jim dodgen
# common thing used by the http tools
#
import socket
import sqlite3

def get_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
# production ports
# DB_NAME = "devices.db"
# EMAIL_PORT = 8087
# CONFIG_PORT = 8086
# CAM_PORT = 8085
# EVENTS_PORT = 8084
# TRIGGERS_PORT = 8083
# TIMERS_PORT = 8082
# MAIN_PORT = 80
# Z2M_PORT is at 8080
#
# testing ports
#
Z2M_PORT = 8080
EMAIL_PORT = 8080
CONFIG_PORT = 8080
CAM_PORT = 8080
EVENTS_PORT = 8080
TRIGGERS_PORT = 8080
TIMERS_PORT = 8080
HTTP_MAIN_PORT = 8080
DB_NAME = "devices.db"
# end testing ports

DB_TIMEOUT = 120 
BROKER_MQTT_PORT = 1883
BASE_FAXMO_PORT = 56000
MQTT_KEEPALIVE = 120

MOSQUITTO_FILE_PATH = "/etc/mosquitto/mosquitto.conf"
ZIGBEE_REFRESH_SECONDS = 30
MOSQUITTO_SLEEP_SECONDS = 1000 # change when checking for termination in future versions
ZIGBEE2MQTT_BRIDGE_DEVICES = "zigbee2mqtt/bridge/devices"
MQTT_SERVICE_Q_TIMEOUT = 60*60*4   # seconds every four hours if it times out then zb/ip devices are refreshed and "home/MQTT_devices" is published
HOME_MQTT_DEVICES = "home/MQTTdevices/configuration"  # Normalized json of ALL devices.  home-broker "publish reatain"s this for other apps it has all the zb and ip devices unified
WATCH_DOG_QUEUE_TIMEOUT = 20
FAUXMO_DEFAULT_DIR = "/etc/fauxmo"  
FAUXMO_CONFIG_FILE_PATH = FAUXMO_DEFAULT_DIR+"/config.json"
MQTTPLUGIN = "mqttplugin.py"
FAUXMO_SLEEP_SECONDS = 240 # wake up every 4 minutes, Zzzzzz
MOSQUITTO_FILE_PATH = "/etc/mosquitto/mosquitto.conf"
VERSON = "2.0"

def ports():
    return {
    "config_port":  CONFIG_PORT, 
    "events_port":  EVENTS_PORT,
    "cam_port":     CAM_PORT,
    "email_port":   EMAIL_PORT,
    "triggers_port": TRIGGERS_PORT,
    "timers_port": TIMERS_PORT,
    "http_main_port": HTTP_MAIN_PORT,
    }

STYLE = '''
body { font-family: sans-serif; margin: 20px; line-height: 1.6; }
nav { background: #334; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
nav a { color: white; text-decoration: none; margin-right: 15px; padding: 5px 10px; }
nav a:hover { background: #555; border-radius: 3px; }
.active { background: #007bff; border-radius: 3px; }
table { width: 100%; border-collapse: collapse; margin-top: 10px; }
th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
th { background-color: #f4f4f4; }
.refill-area { background: #f9f9f9; padding: 15px; border: 1px solid #ccc; border-radius: 5px; }
'''

def get_db_config():
    """Retrieves all configuration fields as a dictionary."""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM config WHERE id = 0")
            row = cursor.fetchone()
            # Convert the Row object into a standard dictionary
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
        
def mosquitto_configuration():
    cfg = get_db_config()
    return  """# created by mosquitto_manager.py
# text in http_common.py listener from db
allow_anonymous true
listener """+str(cfg["broker_mqtt_port"])+"\nlog_dest none"

#print(mosquitto_configuration())

def nav_section():
    my_ip = get_ip()
    nav =  {"nav_section": f'''
    <h1>AlertAway Toolbox</h1>
    <nav>
        <a href="http://{ my_ip }:{ CONFIG_PORT }">Configuation</a>
        <a href="http://{ my_ip }:{ HTTP_MAIN_PORT }">MQTT Devices</a>
        <a href="http://{ my_ip }:{ HTTP_MAIN_PORT }/zigbee2mqtt">zigbee2mqtt</a>
        <a href="http://{ my_ip }:{ EVENTS_PORT }">Events</a>
        <a href="http://{ my_ip }:{ TRIGGERS_PORT }">Triggers</a>
        <a href="http://{ my_ip }:{ TIMERS_PORT }">Timers</a>
        <a href="http://{ my_ip }:{ CAM_PORT }">Cameras</a>
        <a href="http://{ my_ip }:{ EMAIL_PORT }">Emails</a>
    </nav>
    '''}
    #print(nav)
    return nav

def http_vars():
    return {
    "my_ip": get_ip(), 
    "ports": ports(), 
    "style": STYLE,
    }
