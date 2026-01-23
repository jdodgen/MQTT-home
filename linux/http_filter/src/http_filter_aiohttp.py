import aiohttp
from aiohttp import web
import asyncio
import io
from PIL import Image
import time
import cfg  # Assuming cfg.py exists and defines PORT, image_urls
import sys

# Define PORT and saved_images dictionary globally
PORT = cfg.port
saved_images = {}
CACHE_LIFETIME = 15  # Seconds to keep images in cache

async def download_and_process_image_async(url_info):
    """
    Asynchronously downloads an image and performs resizing/rotating if specified.
    """
    url = url_info["url"]
    user = url_info.get("user", None)
    pw = url_info.get("pw", None)
    rotate = url_info.get("rotate", 0)
    base_width = url_info.get("base_width", 0)

    auth = aiohttp.BasicAuth(user, pw) if user and pw else None

    # Use aiohttp ClientSession for asynchronous network requests
    async with aiohttp.ClientSession(auth=auth) as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()  # Read the content as bytes
                else:
                    print(f"Failed to download image. Status code: {response.status}")
                    return None

        except aiohttp.ClientError as e:
            print(f"Error during HTTP request to {url}: {e}")
            return None

    # Image processing with Pillow (synchronous part, consider running in executor if complex)
    if rotate or base_width:
        image_stream = io.BytesIO(image_data)
        img = Image.open(image_stream)
        
        if base_width:
            width_percent = (base_width / float(img.size[0]))
            new_height = int((float(img.size[1]) * float(width_percent)))
            new_size = (base_width, new_height)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            print(f"Resized image to {new_size}")

        if rotate:
            img = img.rotate(rotate, expand=True)
            print(f"Rotated image by {rotate} degrees")

        output_stream = io.BytesIO()
        # Save processed image back to bytes
        img.save(output_stream, format="JPEG")
        return output_stream.getvalue()
    
    return image_data

async def handle_image_request(request):
    """
    Aiohttp handler for incoming requests.
    """
    wanted = request.match_info.get('image_name', "")

    if wanted == "favicon.ico":
        return web.Response(status=404)
    
    if wanted in cfg.image_urls:
        now = time.time()
        
        # Check cache
        if wanted in saved_images and saved_images[wanted]["when_downloaded"] + CACHE_LIFETIME > now:
            print(f"Serving {wanted} from cache.")
            image_data = saved_images[wanted]["image"]
        else:
            # Asynchronously download and process the image
            print(f"Downloading new data for {wanted}.")
            image_data = await download_and_process_image_async(cfg.image_urls[wanted])
            
            if image_data is None:
                return web.Response(status=500, text="Could not download source image.")

            # Update cache
            saved_images[wanted] = {
                "image": image_data,
                "when_downloaded": now,
                "length": str(len(image_data))
            }
        
        # Return the response with appropriate headers
        return web.Response(
            body=image_data,
            content_type='image/jpeg',
            headers={'Content-Length': saved_images[wanted]["length"]}
        )
    else:
        # Not in the allowed list
        return web.Response(status=403, text="Access Denied")

def main():
    """Starts the aiohttp server."""
    app = web.Application()
    # Define a route for handling image requests
    app.add_routes([web.get('/{image_name}', handle_image_request)])

    print(f"Serving at port {PORT}")
    print(f"Open your browser to http://localhost:{PORT}/<image_name>")
    
    # Run the web application
    web.run_app(app, port=PORT, print=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n^C received, shutting down server.")
        # aiohttp handles cleanup internally when web.run_app exits
