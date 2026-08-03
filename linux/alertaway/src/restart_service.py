# you must set this up change jim to the user running the systemd processes
#sudo visudo -f /etc/sudoers.d/python-restart
#jim ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart alertaway*

import subprocess

def restart(service_name):
    try:
        # Calls: sudo systemctl restart your_service.service
        subprocess.run(['/usr/bin/sudo', '/usr/bin/systemctl', 'restart', service_name], check=True)
        result = f"[restart_service] Service {service_name} restarted successfully."
    except subprocess.CalledProcessError as e:
        result = f"[restart_service] Error restarting service: [{service_name}] {e}"
    return result
