import aiohttp
# MIT licenece copyright 2026 Jim dodgen
# converted from http.server with the help of Gemini 
#
from aiohttp import web
import asyncio
import io
import httpx
from PIL import Image
import time
import cfg
import sys

PORT = cfg.port
saved_images = {}
CACHE_LIFETIME = 15  # Seconds to keep images in cache

async def download_image_data_async(url_info):
    try:
        url = url_info["url"]
        user = url_info.get("user")
        pw = url_info.get("pw")
        rotate = url_info.get("rotate", 0)
        base_width = url_info.get("base_width", 0)
        
        # DigestAuth works the same in async
        auth = httpx.DigestAuth(user, pw) if user else None

        # Use AsyncClient for non-blocking requests
        async with httpx.AsyncClient(auth=auth) as client:
            response = await client.get(url)
            response.raise_for_status() 

        image_data = response.content
        
        if rotate or base_width:
            # Note: PIL/Pillow is a blocking library. 
            # For very heavy processing, you'd run this in a threadpool,
            # but for basic resizing, it's usually fine here.
            image_stream = io.BytesIO(image_data)
            img = Image.open(image_stream)
            debug_parts = []
            
            if base_width:
                debug_parts.append(f"resized {base_width}")
                width_percent = (base_width / float(img.size[0]))
                new_height = int((float(img.size[1]) * float(width_percent)))
                img = img.resize((base_width, new_height), Image.LANCZOS)
                
            if rotate:
                debug_parts.append(f"rotate {rotate}")
                img = img.rotate(rotate, expand=True)
            
            output_stream = io.BytesIO()
            img.save(output_stream, format="JPEG")
            
            if debug_parts:
                print(f"image: {' '.join(debug_parts)}")
                
            return output_stream.getvalue()
        return image_data

    except httpx.HTTPStatusError as e:
        print(f"Failed to download image. Status code: {e.response.status_code}")
        return None
    except Exception as e:
        print("Error during HTTP request:", e)
        return None

async def handle_image_request(request):
    """
    Aiohttp handler for incoming requests.
    """
    wanted = request.match_info['whole_path']
    print("request [%s]\n%s" % (wanted,request))
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
            print(f"Downloading new data for [{wanted}].")
            image_data = await download_image_data_async(cfg.image_urls[wanted])
            #image_data = await download_and_process_image_async(cfg.image_urls[wanted])
            
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
    app.add_routes([web.get(r'/{whole_path:.{10,30}}', handle_image_request)])

    print(f"Serving at port {PORT}")
    print(f"Open your browser to http://localhost:{PORT}")
    
    # Run the web application
    web.run_app(app, port=PORT, print=False)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n^C received, shutting down server.")
        # aiohttp handles cleanup internally when web.run_app exits
