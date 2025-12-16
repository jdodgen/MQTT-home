
import http.server
import socketserver
from PIL import Image
import cfg

PORT = 9004

class MyRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests by sending a custom HTML reply."""
        # 1. Send the HTTP status code (200 OK)
        self.send_response(200)

        # 2. Set response headers
        self.send_header("Content-type", "text/html")
        # End the headers section of the response
        self.end_headers()
        # 3. Write the response body
        # Content must be encoded to bytes before writing to the wfile
        response_content = f"""
        <html>
        <head><title>Simple HTTP Server Reply</title></head>
        <body>
        <p>whee  This is a custom response from the server.</p>
        <p>You accessed path: <strong>{self.path}</strong></p>
        </body>
        </html>
        """
        self.wfile.write(response_content.encode("utf-8"))
        #
        print("path [%s]" % (self.path[1:]))
        if self.path[1:] in cfg.image_urls:
            url_info = cfg.image_urls[self.path[1:]]
            url = url_info["url"]
            user = url_info.get("user", None)
            pw = url_info.get("pw", None)
            rotate = url_info.get("rotate", 0)
            img_bytes = download_image_data(url_info)
            self.send_header("Content-type", "image/jpeg")
            self.send_header("Content-Length", str(len(img_bytes)))
            self.end_headers()
            self.wfile.write(img_bytes)
        
        
def download_image_data(url_info):
    print("download_image_data", url_info)
    try:
        url = url_info["url"]
        user = url_info.get("user", None)
        pw = url_info.get("pw", None)
        rotate = url_info.get("rotate", 0)
        if user:
            # print("download_image_data doing auth[%s][%s]" % (user, pw))
            response = requests.get(url, auth=requests.auth.HTTPDigestAuth(user, pw))
        else:
            response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content # Read the content as bytes
            response.close()
            #print("image_data len", len(image_data));
            if rotate:
                image_stream = io.BytesIO(image_data)
                img = Image.open(image_stream)
                image_data_rotated = img.rotate(rotate, expand=True)
                output_stream = io.BytesIO()
                image_data_rotated.save(output_stream, format="jpeg")
                return output_stream.getvalue()
            return image_data
        else:
            print("Failed to download image. Status code:", response.status_code)
            image_data = None
            response.close() 
            return None
    except Exception as e:
        image_data = None
        print("Error during HTTP request:", e)
        return None             
        

def run_server():
    """Starts the custom HTTP server."""
    # Use TCPServer with the custom request handler
    with socketserver.TCPServer(("", PORT), MyRequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        print(f"Open your browser to http://localhost:{PORT}")
        try:
            # Keep the server running indefinitely until interrupted
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n^C received, shutting down server")
            httpd.server_close()

if __name__ == "__main__":
    run_server()
