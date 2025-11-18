import socket
import time
from sshtunnel import SSHTunnelForwarder 

ssh_host = 'your_remote_server_ip'
ssh_user = 'your_ssh_username'
ssh_port = 22
ssh_pkey = '/path/to/your/private/key' # or 
cfg.ssh_password='your_password'
local_port = 8000
remote_server_port = 8080
our_ip = "127.0.0.1" 
  

def start_ssh_tunnel():
    """Starts the SSH tunnel in a background thread."""
    try:
        server = SSHTunnelForwarder(
            (cfg.ssh_host, cfg.ssh_port),
            ssh_username=cfg.ssh_user,
            if cfg.ssh_pkey:
                ssh_pkey=cfg.ssh_pkey, # Use this line if using key authentication
            elif cfg.ssh_password:
                ssh_password=cfg.ssh_password, # Use this line if using password authentication
            remote_bind_address=(cfg.remote_ip, cfg.remote_server_port),
            local_bind_address=(cfg.our_ip, cfg.local_port)
        )
        server.start()
        print(f"SSH tunnel established: Local {cfg.our_ip}:{cfg.local_port} -> Remote {cfg.remote_ip}:{cfg.remote_server_port}")
        return server
    except Exception as e:
        print(f"Error starting SSH tunnel: {e}")
        return None

def get_request_and send_data():
    # Connect to the local port, the tunnel handles the rest
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((cfg.our_ip, cfg.local_port))
        print(f"[CLIENT] Connected to tunnel on {cfg.our_ip}:{cfg.local_port}")
        while True:
            request = s.recv(1024).decode('utf-8') # read request
            #check last one if less than cfg.request_delay time" response" it
            #look it up in cfg
            #request it into response""
            s.sendall(response)
        s.shutdown(socket.SHUT_WR) # Signal end of sending data

if __name__ == "__main__":
    tunnel = start_ssh_tunnel()
    if tunnel:
        try:
            # Give the tunnel a moment to set up
            time.sleep(1)
            send_image_and_receive("your_local_image.jpg") # Replace with your image path
        finally:
            tunnel.stop()
            print("[CLIENT] SSH tunnel closed.")
