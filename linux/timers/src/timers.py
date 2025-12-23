# MIT licence 2025 Jim Dodgen
import time
import suntime

(lat, lon) = "34.206081324130004, -117.14301072256056".split(",")

#time_since_midnight/60/60)
#warsaw_lat = 51.21
#warsaw_lon = 21.01

sun = suntime.Sun(float(lat), float(lon))
today_sr = sun.get_sunrise_time()
today_ss = sun.get_sunset_time()
print("sun rise",  type(today_sr))



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
print("minutes until event", seconds/60)
    


