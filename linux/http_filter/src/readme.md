# AI generated versions of my: http_filter_http_server.py
An interesting experiment to see what Gemni would come up with.
This started because the http_server python was failing when hit with "unusual" requests. http_server is not meant to be used in a production environment, My bad. the
conversion was done by simply asking Gemni to convert the base http_filter_http_server.py to the other http versions. 
none of them worked as generated. I ended up using aiohttp with httpx for the download of the jpg
## versions
* flask - 
* waitress
* aiohttp
* http.server
