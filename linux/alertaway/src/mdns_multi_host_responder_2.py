#!/usr/bin/env python3
import asyncio
import socket
import sys
from zeroconf import IPVersion, ServiceInfo, Zeroconf, RecordUpdateListener

def get_local_ip():
    """Gets the main local IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# --- YOUR CUSTOM ACTION GOES HERE ---
def handle_collision(collided_name):
    """
    This function triggers automatically if another device on the 
    network is already using your hostname.
    """
    print(f"\n[!!!] ALERT: Name collision detected for '{collided_name}'!")
    print("[!!!] Another server is already using this hostname.")
    
    # Example Actions you could script here:
    # - Send an MQTT alert message to a backup broker
    # - Write an error to a custom status file
    # - Blink a GPIO hardware LED
    # - sys.exit(1) # Un-comment if you want the systemd service to crash/stop safely
    
    print("[*] Custom action executed successfully.\n")


class CollisionListener:
    """Listens for Zeroconf registration state changes."""
    def __init__(self, alias):
        self.alias = alias

    def run_action(self, zc, type_, name, state_change):
        # StateChange.Collision is triggered when a name is already taken on the network
        from zeroconf import StateChange
        if state_change == StateChange.Collision:
            cleaned_name = name.split('._http')[0] if '._http' in name else name
            handle_collision(cleaned_name)


async def main():
    local_ip = get_local_ip()
    packed_ip = socket.inet_aton(local_ip)

    print(f"[*] Detecting local IP: {local_ip}")
    print("[*] Registering mDNS hostnames with collision tracking...")

    zc = Zeroconf(ip_version=IPVersion.V4Only)

    hosts = [
        {"name": "alertaway.local.", "alias": "AlertAway Gateway"},
        {"name": "home-broker.local.", "alias": "Home Broker MQTT"},
    ]

    infos = []

    for host in hosts:
        info = ServiceInfo(
            type_="_http._tcp.local.",
            name=f"{host['alias']}._http._tcp.local.",
            addresses=[packed_ip],
            port=80,
            server=host["name"],
            properties={},
        )
        
        # Attach the collision listener to this specific service registration
        listener = CollisionListener(host['alias'])
        
        # Register service with the listener tracking its state updates
        zc.register_service(info, cooperating_listeners=[listener.run_action])
        infos.append(info)
        print(f" -> Monitoring & Responding to: {host['name'].rstrip('.')}")

    print("\n[+] mDNS responder running. Monitoring network conflicts...")

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("\n[-] Shutting down mDNS responder...")
    finally:
        for info in infos:
            zc.unregister_service(info)
        zc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
