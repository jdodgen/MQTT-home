# AI converted from http_filter.py
import requests
from PIL import Image
import time
import io
import cfg
from waitress import serve # Import serve

PORT = cfg.port # Assuming cfg.port is defined
saved_images = {}

def download_image_data(url_info):
    # (Your existing download_image_data function here)
    try:
        url = url_info["url"]
        user = url_info.get("user", None)
        pw = url_info.get("pw", None)
        # ... (rest of your download logic)
        # For demonstration, returning placeholder data if it fails or is incomplete
        # In your real code, this should return image bytes
        print(f"Downloading from {url}") # Placeholder
        # Example: Fetching an actual image for testing
        response = requests.get(url_info["url"])
        response.raise_for_status() # Raise an exception for bad status codes
        return response.content # Return actual image bytes
    except requests.RequestException as e:
        print(f"Error downloading {url_info['url']}: {e}")
        return None # Or handle error appropriately

def application(environ, start_response):
    """WSGI application entry point"""
    path = environ.get('PATH_INFO', '').lstrip('/')
    status = '200 OK'
    headers = [('Content-type', 'image/jpeg')]
    
    if path == "favicon.ico":
        status = '404 Not Found'
        start_response(status, [('Content-type', 'text/plain')])
        return [b'Not Found']

    if path in cfg.image_urls:
        now = time.time()
        if path in saved_images and saved_images[path]["when_downloaded"] + 15 > now:
            pass # Use cached image
        else:
            image_bytes = download_image_data(cfg.image_urls[path])
            if image_bytes:
                one_to_save = {"image": image_bytes, "when_downloaded": now, "length": str(len(image_bytes))}
                saved_images[path] = one_to_save
            else:
                status = '500 Internal Server Error'
                start_response(status, [('Content-type', 'text/plain')])
                return [b'Error fetching image']
        
        # Ensure we have data before sending headers
        if path in saved_images:
            image_data = saved_images[path]["image"]
            headers.append(('Content-Length', saved_images[path]["length"]))
            start_response(status, headers)
            return [image_data] # Must be bytes
        else:
            status = '500 Internal Server Error'
            start_response(status, [('Content-type', 'text/plain')])
            return [b'Error processing image']
    else:
        status = '403 Forbidden'
        start_response(status, [('Content-type', 'text/plain')])
        return [b'Forbidden']

if __name__ == '__main__':
    print(f"Starting Waitress server on port {PORT}")
    serve(application, host='0.0.0.0', port=PORT)
