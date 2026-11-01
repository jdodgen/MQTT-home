# MIT licence copyright 2026 Jim Dodgen
"""
notes to disable old system
# Stop the mDNS broadcast immediately
sudo systemctl stop avahi-daemon.service avahi-daemon.socket

# Disable the service so it stays silent if the system reboots
sudo systemctl disable avahi-daemon.service avahi-daemon.socket
sudo systemctl status avahi-daemon.service
"""

import asyncio
import socket
from zeroconf import IPVersion, ServiceInfo
from zeroconf.asyncio import AsyncZeroconf  # Use AsyncZeroconf for asyncio code

def get_local_ip():
    """Gets the main local IP address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not need to be reachable, used to find local interface
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

async def main():
    local_ip = get_local_ip()
    packed_ip = socket.inet_aton(local_ip)
    
    print(f"[*] Detecting local IP: {local_ip}")
    print("[*] Registering mDNS hostnames...")
    
    # Initialize the asynchronous variant of Zeroconf
    aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)
    
    # Define the custom .local addresses
    hosts = [
        {"name": "alertaway.local.", "alias": "AlertAway-Gateway"},
        {"name": "home-broker.local.", "alias": "Home-Broker-MQTT"},
    ]
    
    infos = []
    try:
        for host in hosts:
            info = ServiceInfo(
                type_="_http._tcp.local.",
                name=f"{host['alias']}._http._tcp.local.",
                addresses=[packed_ip],
                port=80,
                server=host["name"],
                properties={},
            )
            # Await the async registration method instead of using the synchronous one
            await aiozc.async_register_service(info)
            infos.append(info)
            print(f" -> Responding to: {host['name'].rstrip('.')} ({host['alias']})")

        print("\n[+] mDNS responder running. Press Ctrl+C to exit.")
        
        # Keep the script alive indefinitely
        while True:
            await asyncio.sleep(3600)
            
    except asyncio.CancelledError:
        print("\n[-] Shutting down mDNS responder...")
    finally:
        # Cleanly unregister services using the async context
        print("\n[-] Unregistering services...")
        for info in infos:
            await aiozc.async_unregister_service(info)
        await aiozc.async_close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
