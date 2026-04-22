# MIT licence copyright 2026 jim dodgen
import socket
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

DB_NAME = "devices.db"
EMAIL_PORT = 8080
CONFIG_PORT = 8080
CAM_PORT = 8080
EVENTS_PORT = 8080

def ports():
    return {
    "config_port":  CONFIG_PORT, 
    "events_port":  EVENTS_PORT,
    "cam_port":     CAM_PORT,
    "email_port":   EMAIL_PORT,
    }
