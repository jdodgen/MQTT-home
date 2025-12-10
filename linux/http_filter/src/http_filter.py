# I passed this to google's AI
'''make me a very lightweght python  web server to simply forward html request to a different ip and port written in python3'''
#
# and got this which is pretty complete
# it does need some very minor modifications because all the CONSTANTS are contained in an imported configuration file.
# Other than that it look good, a bit over kill at times.
# should you trus AI generated code?  well NO!
# you need it certified by a software engineer or other domain experts.
# never trust code written by untrusted parties
# lines had to change are noted by FIX comments
#

from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
# import tunnel_cfg

Configuration for the forwarding server
# FIX FORWARD_TO_HOST = 'target_ip_or_hostname'  # e.g., '127.0.0.1' or 'example.com'
# FIX FORWARD_TO_PORT = 8080                     # e.g., 80 or 8080
FORWARD_TO_HOST = 'localhost'  # e.g., '127.0.0.1' or 'example.com'
FORWARD_TO_PORT = 80

# Configuration for the proxy server itself
PROXY_HOST = '0.0.0.0'  # Listen on all available interfaces
PROXY_PORT = 8000       # Port for the proxy server to listen on

FORWARD_TO_HOST = 'target_ip_or_hostname'  # e.g., '127.0.0.1' or 'example.com'
FORWARD_TO_PORT = 8080                     # e.g., 80 or 8080

# Configuration for the proxy server itself
PROXY_HOST = '0.0.0.0'  # Listen on all available interfaces
PROXY_PORT = 8000       # Port for the proxy server to listen on

class ForwardingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward_request('GET')

    def do_POST(self):
        self.forward_request('POST')

    def do_PUT(self):
        self.forward_request('PUT')

    def do_DELETE(self):
        self.forward_request('DELETE')

    def forward_request(self, method):
        # Construct the target URL
        target_url = f"http://{FORWARD_TO_HOST}:{FORWARD_TO_PORT}{self.path}"

        # Prepare headers for forwarding (optional: copy all original headers)
        headers = {key: value for key, value in self.headers.items()}
        # Remove connection-specific headers that might cause issues with forwarding
        headers.pop('Host', None)
        headers.pop('Connection', None)
        headers.pop('Content-Length', None) # requests library handles this

        # Prepare body for POST/PUT requests
        body = None
        if method in ['POST', 'PUT']:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

        try:
            # Make the request to the target server
            response = requests.request(
                method,
                target_url,
                headers=headers,
                data=body,
                allow_redirects=False, # Handle redirects manually if needed
                stream=True # Stream response for large files
            )

            # Forward the response back to the client
            self.send_response(response.status_code)
            for header, value in response.headers.items():
                # Avoid forwarding hop-by-hop headers
                if header.lower() not in ['content-encoding', 'transfer-encoding', 'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization', 'te', 'trailers', 'upgrade']:
                    self.send_header(header, value)
            self.end_headers()

            # Stream the content of the response
            for chunk in response.iter_content(chunk_size=8192):
                self.wfile.write(chunk)

        except requests.exceptions.RequestException as e:
            self.send_error(500, f"Error forwarding request: {e}")

def run_server():
    server_address = (PROXY_HOST, PROXY_PORT)
    httpd = HTTPServer(server_address, ForwardingHandler)
    print(f"Starting proxy server on {PROXY_HOST}:{PROXY_PORT}")
    print(f"Forwarding requests to {FORWARD_TO_HOST}:{FORWARD_TO_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
