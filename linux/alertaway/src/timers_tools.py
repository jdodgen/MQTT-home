import time
import suntime
import datetime
import http_common as config

class sunrise_sunset:
    def __init__(self, row_factory=True): 
        self.lat_long = config.get_db_config()["lat_long"]
        
def get_sunset_sunrise(lat_long):
    (lat, lon) = lat_long.split(",")
    sun = suntime.Sun(float(lat), float(lon))
    todays_date = datetime.date.today()
    todays_datetime = datetime.datetime.combine(todays_date, datetime.time(0, 0))
    local_tz = tz.gettz()
    sunrise = sun.get_local_sunrise_time(todays_datetime, local_tz)
    sunset =  sun.get_local_sunset_time(todays_datetime, local_tz)
    #print("sunrise",  sunrise)
    if sunset < sunrise: # fix a bug in suntime
            sunset += datetime.timedelta(days=1)
    #print("sunset",  sunset)
    today_date = datetime.date.today()
    #print("date.today", today_date)
    midnight_utc = datetime.datetime.combine(today_date, datetime.time.min, tzinfo=local_tz)
    #print("midnight_utc", midnight_utc)
    unix_timestamp_at_midnight = midnight_utc.timestamp()
    sunrise_since_midnight =      sunrise.timestamp() - unix_timestamp_at_midnight
    #print("sunrise at this hour", sunrise_since_midnight/60/60)
    sunset_since_midnight =       sunset.timestamp()  - unix_timestamp_at_midnight
    #print("sunset at this hour",  sunset_since_midnight/60/60)
    return(sunrise_since_midnight, sunset_since_midnight)

from datetime import datetime
from suntime import Sun
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

# 1. Your single coordinate string (comma-separated)
coord_string = "34.2083, -117.1084"

# 2. Split by the comma and convert both pieces to floats
lat_str, lon_str = coord_string.split(",")
latitude = float(lat_str.strip())
longitude = float(lon_str.strip())

# 3. Use the variables exactly like before
tf = TimezoneFinder()
timezone_str = tf.timezone_at(lng=longitude, lat=latitude)

if timezone_str:
    sun = Sun(latitude, longitude)
    today = datetime.now()
    
    sunrise_utc = sun.get_sunrise_time(today)
    sunset_utc = sun.get_sunset_time(today)
    
    local_tz = ZoneInfo(timezone_str)
    sunrise_local = sunrise_utc.astimezone(local_tz)
    sunset_local = sunset_utc.astimezone(local_tz)
    
    print(f"Location: {latitude}, {longitude}")
    print(f"Timezone: {timezone_str}")
    print(f"Sunrise:  {sunrise_local.strftime('%I:%M:%S %p')}")
    print(f"Sunset:   {sunset_local.strftime('%I:%M:%S %p')}")

from datetime import datetime
from suntime import Sun
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

# 1. Define your location coordinates
latitude = 34.2083
longitude = -117.1084

# 2. Automatically find the timezone name from coordinates
tf = TimezoneFinder()
timezone_str = tf.timezone_at(lng=longitude, lat=latitude)

if timezone_str is None:
    print("Could not determine timezone for these coordinates.")
else:
    # 3. Initialize the Sun object
    sun = Sun(latitude, longitude)
    today = datetime.now()
    
    # 4. Fetch UTC times
    sunrise_utc = sun.get_sunrise_time(today)
    sunset_utc = sun.get_sunset_time(today)
    
    # 5. Convert to the dynamically discovered timezone
    local_tz = ZoneInfo(timezone_str)
    sunrise_local = sunrise_utc.astimezone(local_tz)
    sunset_local = sunset_utc.astimezone(local_tz)
    
    # 6. Print the results
    print(f"Timezone: {timezone_str}")
    print(f"Sunrise:  {sunrise_local.strftime('%I:%M:%S %p')}")
    print(f"Sunset:   {sunset_local.strftime('%I:%M:%S %p')}")




if __name__ == "__main__":
    main()
