
import http.server
import socketserver
import requests
from PIL import Image
import time
import io
import cfg

PORT = 9004
saved_images = {}
class MyRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        wanted = self.path[1:]
        #print("request: [%s]" % (wanted))
        if wanted == "favicon.ico":
            self.send_error(404, message=None, explain=None)    
        elif wanted in cfg.image_urls:
            print("good one [%s]" % ( wanted))
            self.send_response(200)
            now = time.time()
            
            if wanted in saved_images and saved_images[wanted]["when_downloaded"]+15 >  now:  # TBD seconds or less old we reuse it
                #print("a>b", saved_images[wanted]["when_downloaded"]+15, now)
                pass
            else:
                # try:
                    # print("a<b", saved_images[wanted]["when_downloaded"]+15, now)
                # except:
                    # print("new saved_images")
                image_bytes = download_image_data(cfg.image_urls[wanted])
                one_to_save = {"image":  image_bytes, "when_downloaded":  now, "length":  str(len(image_bytes))}
                saved_images[wanted] = one_to_save
            self.send_header("Content-type", "image/jpeg")
            self.send_header("Content-Length", saved_images[wanted]["length"])
            self.end_headers()
            self.wfile.write(saved_images[wanted]["image"])
        else:   # not in the list
            self.send_error(403, message=None, explain=None)
        
        
def download_image_data(url_info):  # version 2 added resize base_width
    #print("download_image_data", url_info)
    try:
        url = url_info["url"]
        user = url_info.get("user", None)
        pw = url_info.get("pw", None)
        rotate = url_info.get("rotate", 0)
        base_width = url_info.get("base_width", 0)
        if user:
            # print("download_image_data doing auth[%s][%s]" % (user, pw))
            response = requests.get(url, auth=requests.auth.HTTPDigestAuth(user, pw))
        else:
            response = requests.get(url)
        if response.status_code == 200:
            image_data = response.content # Read the content as bytes
            response.close()
            #print("image_data len", len(image_data));
            if rotate or base_width:
                image_stream = io.BytesIO(image_data)
                img = Image.open(image_stream)
                if base_width:
                    width_percent = (base_width / float(img.size[0]))
                    new_height = int((float(img.size[1]) * float(width_percent)))
                    new_size = (base_width, new_height)

                    # Resize and save
                    img = img.resize(new_size, Image.LANCZOS)
                    # resized_img.save(output_path, "JPEG", quality=90)
                if rotate:
                    img = img.rotate(rotate, expand=True)
                output_stream = io.BytesIO()
                img.save(output_stream, format="jpeg")
                return output_stream.getvalue()
            #print("returning image size[%s]" % (str(len(image_data))))
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
