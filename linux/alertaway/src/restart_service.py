import subprocess

def restart(service_name):
    try:
        # Calls: sudo systemctl restart your_service.service
        subprocess.run(['sudo', 'systemctl', 'restart', service_name], check=True)
        print(f"[restart_service] Service {service_name} restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[restart_service] Error restarting service: {e}")

if __name__ == '__main__':
    restart_service("zigbee2mqtt")
