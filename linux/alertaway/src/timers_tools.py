import time
import suntime
import timezonefinder
import zoneinfo
import datetime
import http_common as config

class tools:
    def __init__(self, row_factory=True):
        try: 
            lat_long = config.get_db_config()["lat_long"]
            (lat, lon) = lat_long.split(",")
            lat_str, lon_str = lat_long.split(",")
            latitude = float(lat_str.strip())
            longitude = float(lon_str.strip())
            try:
                _tf = timezonefinder.TimezoneFinder()
                self.timezone_str = _tf.timezone_at(lng=longitude, lat=latitude)
                if self.timezone_str: 
                    self.sun = suntime.Sun(latitude, longitude)
                    self.local_tz = zoneinfo.ZoneInfo(self.timezone_str)
            except (ValueError, AttributeError):
                raise ValueError("invalid: no timezone") 
        except (ValueError, AttributeError):
                raise ValueError("invalid: expected format 'lat, lon'.")  
            

    def get_sunset_sunrise_since_midnight(self):
            today = datetime.datetime.now()
            sunrise_utc = self.sun.get_sunrise_time(today)
            sunset_utc =  self.sun.get_sunset_time(today)
            sunrise_local = sunrise_utc.astimezone(self.local_tz)
            sunset_local =  sunset_utc.astimezone(self.local_tz)
            local_date =  sunrise_local.date()
            midnight_local = datetime.datetime.combine(local_date, datetime.time.min, tzinfo=self.local_tz)
            # The modulo % 86400 instantly turns negative offsets into a positive 24-hour count
            seconds_in_a_day = 24 * 60 * 60  # 86400
            
            sunrise_seconds = int((sunrise_local - midnight_local).total_seconds()) % seconds_in_a_day
            sunset_seconds = int((sunset_local - midnight_local).total_seconds()) % seconds_in_a_day
            #print(f"sunrise Hours since midnight: {sunrise_seconds / 3600:.2f}")
            #print(f"sunset Hours since midnight: {sunset_seconds / 3600:.2f}")
            
            self.sunrise_str = sunrise_local.strftime('%H:%M')
            print(f"[timers_tools]Sunrise:  {self.sunrise_str}")
            self.sunset_str = sunset_local.strftime('%H:%M')
            print(f"[timers_tools]Sunset:   {self.sunset_str}")
            return(sunrise_seconds,sunset_seconds)
        
    # def get_sunset_sunrise_since_midnight(self):
    
        # # sun = suntime.Sun(float(lat), float(lon))
        # # todays_date = datetime.date.today()
        # # todays_datetime = datetime.datetime.combine(todays_date, datetime.time(0, 0))
        # # local_tz = tz.gettz()
        # # sunrise = sun.get_local_sunrise_time(todays_datetime, local_tz)
        # # sunset =  sun.get_local_sunset_time(todays_datetime, local_tz)
        # # #print("sunrise",  sunrise)
        # # if sunset < sunrise: # fix a bug in suntime
                # # sunset += datetime.timedelta(days=1)
        # #print("sunset",  sunset)
        # today_date = datetime.date.today()
        # print("date.today", today_date)
        # midnight_utc = datetime.datetime.combine(today_date, datetime.time.min, tzinfo=self.local_tz)
        # print("midnight_utc", midnight_utc)
        # unix_timestamp_at_midnight = midnight_utc.timestamp()
        # sunrise_since_midnight =      self.sunrise_utc.timestamp() - unix_timestamp_at_midnight
        # #print("sunrise at this hour", sunrise_since_midnight/60/60)
        # sunset_since_midnight =       self.sunset_utc.timestamp()  - unix_timestamp_at_midnight
        # #print("sunset at this hour",  sunset_since_midnight/60/60)
        # return(sunrise_since_midnight, sunset_since_midnight)

# from datetime import datetime
# from suntime import Sun
# from timezonefinder import TimezoneFinder
# from zoneinfo import ZoneInfo

# # 1. Your single coordinate string (comma-separated)
# coord_string = "34.2083, -117.1084"

# # 2. Split by the comma and convert both pieces to floats
# lat_str, lon_str = coord_string.split(",")
# latitude = float(lat_str.strip())
# longitude = float(lon_str.strip())

# # 3. Use the variables exactly like before
# tf = TimezoneFinder()
# timezone_str = tf.timezone_at(lng=longitude, lat=latitude)

# if timezone_str:
    # sun = Sun(latitude, longitude)
    # today = datetime.now()
    
    # sunrise_utc = sun.get_sunrise_time(today)
    # sunset_utc = sun.get_sunset_time(today)
    
    # local_tz = ZoneInfo(timezone_str)
    # sunrise_local = sunrise_utc.astimezone(local_tz)
    # sunset_local = sunset_utc.astimezone(local_tz)
    
    # print(f"Location: {latitude}, {longitude}")
    # print(f"Timezone: {timezone_str}")
    # print(f"Sunrise:  {sunrise_local.strftime('%I:%M:%S %p')}")
    # print(f"Sunset:   {sunset_local.strftime('%I:%M:%S %p')}")

# from datetime import datetime
# from suntime import Sun
# from timezonefinder import TimezoneFinder
# from zoneinfo import ZoneInfo

# # 1. Define your location coordinates
# latitude = 34.2083
# longitude = -117.1084

# # 2. Automatically find the timezone name from coordinates
# tf = TimezoneFinder()
# timezone_str = tf.timezone_at(lng=longitude, lat=latitude)

# if timezone_str is None:
    # print("Could not determine timezone for these coordinates.")
# else:
    # # 3. Initialize the Sun object
    # sun = Sun(latitude, longitude)
    # today = datetime.now()
    
    # # 4. Fetch UTC times
    # sunrise_utc = sun.get_sunrise_time(today)
    # sunset_utc = sun.get_sunset_time(today)
    
    # # 5. Convert to the dynamically discovered timezone
    # local_tz = ZoneInfo(timezone_str)
    # sunrise_local = sunrise_utc.astimezone(local_tz)
    # sunset_local = sunset_utc.astimezone(local_tz)
    
    # # 6. Print the results
    # print(f"Timezone: {timezone_str}")
    # print(f"Sunrise:  {sunrise_local.strftime('%I:%M:%S %p')}")
    # print(f"Sunset:   {sunset_local.strftime('%I:%M:%S %p')}")




if __name__ == "__main__":
   timetools = tools()
   (srise, sset) =timetools.get_sunset_sunrise_since_midnight()
   print(f"today: aftermidnight hours\n sunrises: {srise/60/60}\n and sets: {sset/60/60}")
   print(f"timetools.timezone_str '{timetools.timezone_str}'")
   print(f"timetools.sunrise_str '{timetools.sunrise_str}'")
   print(f"timetools.sunset_str '{timetools.sunset_str}'")
