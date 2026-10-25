#!/usr/bin/env python3
"""
# Stop the mDNS broadcast immediately
sudo systemctl stop avahi-daemon.service avahi-daemon.socket

# Disable the service so it stays silent if the system reboots
sudo systemctl disable avahi-daemon.service avahi-daemon.socket

sudo systemctl status avahi-daemon.service
"""
import asyncio
import socket
from zeroconf import IPVersion, ServiceInfo, Zeroconf


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

    zc = Zeroconf(ip_version=IPVersion.V4Only)

    # Define the custom .local addresses
    # Note: Zeroconf requires the trailing dot in the registration parameters
    hosts = [
        {"name": "alertaway.local.", "alias": "AlertAway Gateway"},
        {"name": "home-broker.local.", "alias": "Home Broker MQTT"},
    ]

    infos = []

    for host in hosts:
        # We register a dummy HTTP service matching the hostname targeting port 80
        info = ServiceInfo(
            type_="_http._tcp.local.",
            name=f"{host['alias']}._http._tcp.local.",
            addresses=[packed_ip],
            port=80,
            server=host["name"],
            properties={},
        )
        zc.register_service(info)
        infos.append(info)
        print(f" -> Responding to: {host['name'].rstrip('.')}")

    print("\n[+] mDNS responder running. Press Ctrl+C to exit.")

    try:
        # Keep the script alive indefinitely
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        print("\n[-] Shutting down mDNS responder...")
    finally:
        # Cleanly unregister services on exit
        for info in infos:
            zc.unregister_service(info)
        zc.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
