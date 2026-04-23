# MIT licence copyright 2026 jim dodgen
# common thing used by the http tools
#

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

# DB_NAME = "devices.db"
# EMAIL_PORT = 8087
# CONFIG_PORT = 8086
# CAM_PORT = 8085
# EVENTS_PORT = 8084
# TRIGGERS_PORT = 8083
# TIMERS_PORT = 8082
# MAIN_PORT = 8081
# z2m is at 8080
# testing
EMAIL_PORT = 8080
CONFIG_PORT = 8080
CAM_PORT = 8080
EVENTS_PORT = 8080
TRIGGERS_PORT = 8080
TIMERS_PORT = 8080
MAIN_PORT = 8080
def ports():
    return {
    "config_port":  CONFIG_PORT, 
    "events_port":  EVENTS_PORT,
    "cam_port":     CAM_PORT,
    "email_port":   EMAIL_PORT,
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

def http_vars():
    return {
    "my_ip": get_ip(), 
    "ports": ports(), 
    "style": STYLE,
    }
