
#sudo visudo -f /etc/sudoers.d/python-restart
#jim ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart alertaway*.service


import subprocess

def restart(service_name):
    try:
        # Calls: sudo systemctl restart your_service.service
        subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=True)
        result = f"[restart_service] Service {service_name} restarted successfully."
    except subprocess.CalledProcessError as e:
        result = f"[restart_service] Error restarting service: [{service_name}] {e}"
    return result
if __name__ == '__main__':
    print(f"result: {restart("alertaway-timers-daemon")}")
