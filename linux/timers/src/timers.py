# MIT licence 2025 Jim Dodgen
import time
import suntime
import datetime
from dateutil import tz

(lat, lon) = "34.206081324130004, -117.14301072256056".split(",")

#time_since_midnight/60/60)
#warsaw_lat = 51.21
#warsaw_lon = 21.01

sun = suntime.Sun(float(lat), float(lon))
today_date = datetime.date.today()
local_tz = tz.gettz() 


sunrise = sun.get_local_sunrise_time(today_date, local_tz)
sunset =  sun.get_local_sunset_time(today_date, local_tz)
print("sunrise",  sunrise)
if sunset < sunrise: # fix a bug in suntime
        sunset += datetime.timedelta(days=1)
print("sunset",  sunset)


# 1. Get today's date
today_date = datetime.date.today()
print("date.today", today_date)
# 2. Combine the date with the minimum time (midnight)
#    and specify the UTC timezone
midnight_utc = datetime.datetime.combine(today_date, datetime.time.min, tzinfo=local_tz)
print("midnight_utc", midnight_utc)
unix_timestamp_at_midnight = midnight_utc.timestamp()
sunrise_since_midnight =      sunrise.timestamp() - unix_timestamp_at_midnight
print("sunrise at this hour", sunrise_since_midnight/60/60)
sunset_since_midnight =       sunset.timestamp()  - unix_timestamp_at_midnight
print("sunset at this hour",  sunset_since_midnight/60/60)

def seconds_since_midnight_from_string(time_str):
    """
    Converts an H:M:S string to seconds since midnight.
    """
    hms = time_str.split(':')
    if len(hms) == 1:
        h =int(hms[0])
        m = 0
        s = 0
    elif len(hms) == 2:
        h = int(hms[0])
        m = int(hms[1])
        s = 0
    elif len(hms) == 3:
        h = int(hms[0])
        m = int(hms[1])
        s = int(hms[2])
    
    return (h * 3600) + (m * 60) + s

def seconds_to_event(event_time):
    local_time = time.localtime()
    print(f"Local Time: {time.strftime('%Y-%m-%d %H:%M:%S %Z', local_time)}")
    local_time_seconds_since_midnight = local_time.tm_hour * 3600 + local_time.tm_min * 60 + local_time.tm_sec
    print("hours since midnight", local_time_seconds_since_midnight/60/60)
    seconds = event_time - local_time_seconds_since_midnight
    return seconds

event_time_string = "16:00"
result = seconds_since_midnight_from_string("16:00")
print(f"Manual calculation seconds_since_midnight {event_time_string}: {result/60/60} hours.")

seconds = seconds_to_event(result)
print("hours until event", seconds/60/60)

    


