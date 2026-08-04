# you must set this up change jim to the user running the systemd processes
#sudo visudo -f /etc/sudoers.d/python-restart
#jim ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart alertaway*
#jim ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart mosquitto

import subprocess

def restart(service_name):
    try:
        # Calls: sudo systemctl restart your_service.service
        subprocess.run(['/usr/bin/sudo', '/usr/bin/systemctl', 'restart', service_name], check=True)
        result = f"{service_name} restarted "
    except subprocess.CalledProcessError as e:
        result = f"Error restarting service: [{service_name}] {e}"
    return result
