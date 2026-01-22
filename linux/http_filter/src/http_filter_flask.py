# AI converted http_filter.py 
from flask import Flask, send_file, Response, abort, request
import requests
from PIL import Image
import time
import io
import cfg # Assuming cfg.py has image_urls and download_image_data

app = Flask(__name__)
saved_images = {} # Cache for downloaded images

# Helper function (you need to define this in your cfg or here)
# def download_image_data(url_info): ... (as in your original code)

# Mock download_image_data for demonstration if cfg isn't available
def download_image_data(url_info):
    print(f"Downloading from {url_info['url']}")
    try:
        response = requests.get(url_info['url'], auth=(url_info.get("user"), url_info.get("pw")) if url_info.get("user") else None)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

# Assume cfg.image_urls is like: {"image1": {"url": "...", "user": "...", "pw": "..."}, ...}
# For testing, you might define it:
if 'cfg' not in globals():
    class MockConfig:
        image_urls = {
            "image1": {"url": "https://picsum.photos/id/237/200/300.jpg"},
            "image2": {"url": "https://picsum.photos/id/238/300/200.jpg"},
        }
    cfg = MockConfig()

@app.route('/<string:image_name>')
def get_image(image_name):
    # Handle favicon request
    if image_name == "favicon.ico":
        abort(404) # Flask's way to send 404

    # Check if allowed
    if image_name not in cfg.image_urls:
        abort(403) # Forbidden

    now = time.time()
    # Check cache (15 seconds validity)
    if image_name in saved_images and saved_images[image_name]["when_downloaded"] + 15 > now:
        # Cache hit
        img_data = saved_images[image_name]["image"]
        img_length = saved_images[image_name]["length"]
    else:
        # Cache miss or expired, download new image
        image_info = cfg.image_urls[image_name]
        img_bytes = download_image_data(image_info)

        if img_bytes is None:
            abort(500) # Internal Server Error if download fails

        img_length = len(img_bytes)
        saved_images[image_name] = {
            "image": img_bytes,
            "when_downloaded": now,
            "length": img_length
        }
        img_data = img_bytes

    # Return the image using Flask's Response object
    return Response(img_data, mimetype='image/jpeg', headers={'Content-Length': str(img_length)})

if __name__ == '__main__':
    # Run on a specific port, e.g., 9004, matching your original test port
    app.run(port=cfg.port if hasattr(cfg, 'port') else 9004, debug=True)
