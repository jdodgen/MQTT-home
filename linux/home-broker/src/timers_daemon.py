# MIT licence 2025 Jim Dodgen
import time
import suntime
import datetime
from dateutil import tz
import asyncio
import cfg
# import mqtt_manager
import message
import database

xprint = print # copy print
my_name = "[timers_daemon]"
def print(*args, **kwargs): # replace print
    #return  # comment/uncomment to turn print on off
    # do whatever you want to do
    #xprint('statement before print')
    xprint(my_name, *args, **kwargs) # the copied real print

async def sleep_until_one_second_after_midnight():
    now = datetime.datetime.now()
    # zero out so at 1 minute after last midnight
    target = now.replace(hour=0, minute=1, second=0, microsecond=0)
    #
    # If it's already past 0:01 today, set target to 0:01 tomorrow
    if now >= target:
        target += datetime.timedelta(days=1)
    # Calculate the number of seconds to wait
    wait_seconds = (target - now).total_seconds()
    print(f"[sleep_until_one_second_after_midnight]Current time: {now.strftime('%H:%M:%S')}")
    print(f"[sleep_until_one_second_after_midnight]Sleeping until: {target.strftime('%Y-%m-%d %H:%M:%S')} ({wait_seconds:.2f} seconds)")
    #print("[sleep_until_one_second_after_midnight]sleep_until_one_second_after_midnight hours", wait_seconds/60/60) 
    await asyncio.sleep(wait_seconds)
    print("[sleep_until_one_second_after_midnight]Waking up! It is now 0:01")

def get_sunset_sunrise(lat_long):
    (lat, lon) = lat_long.split(",")
    sun = suntime.Sun(float(lat), float(lon))
    today_date = datetime.date.today()
    local_tz = tz.gettz() 
    sunrise = sun.get_local_sunrise_time(today_date, local_tz)
    sunset =  sun.get_local_sunset_time(today_date, local_tz)
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
    
# def time_string_to_seconds(time_str):
    # #Converts an H:M:S string to seconds since midnight.
    # hms = time_str.split(':')
    # if len(hms) == 1:
        # h =int(hms[0])
        # m = 0
        # s = 0
    # elif len(hms) == 2:
        # h = int(hms[0])
        # m = int(hms[1])
        # s = 0
    # elif len(hms) == 3:
        # h = int(hms[0])
        # m = int(hms[1])
        # s = int(hms[2])
    # return (h * 3600) + (m * 60) + s

def seconds_to_event(event_time):
    local_time = time.localtime()
    local_time_seconds_since_midnight = local_time.tm_hour * 3600 + local_time.tm_min * 60 + local_time.tm_sec
    #print("hours since midnight", local_time_seconds_since_midnight/60/60)
    seconds = event_time - local_time_seconds_since_midnight
    return seconds

async  def wait_and_send(time_type, hour, minute, offset, topic, payload): 
    print("[[", time_type, hour, minute, offset, topic, payload, "]]")
    match time_type:
        case "Sunset":
            (x, since_midnight) = get_sunset_sunrise(cfg.lat_long)
            print("sunset at this hour",  since_midnight/60/60)
            seconds = seconds_to_event(since_midnight + (int(offset) * 60))
        case "Sunrise":
            (since_midnight, x) = get_sunset_sunrise(cfg.lat_long)
            print("sunrise at this hour", since_midnight/60/60)
            seconds = seconds_to_event(since_midnight + (int(offset) * 60)) 
        case _: # default must be just a time in 24 hour format
            since_midnight = (int(minute) * 60) + (int(hour) * 3600) #time_string_to_seconds(time)
            print("type since_midnight[%s] time_wanted_hours[%s]", (type(since_midnight),since_midnight,)) # since_midnight/60/60,))
            seconds = seconds_to_event(since_midnight)
    print("hours until event", seconds/60/60)
    if seconds > 0:
        await asyncio.sleep(seconds) # we are sleeping until timer starts or stops
        # client.publish(topic, payload)
        message.publish_single(topic, payload, my_parent="timers_daemon")
        print("task [%s] sleep done,s time to plublish" % (time_type,  datetime.datetime.now()))
        print(time_type, hour, minute, offset, topic, payload)
    else:
        print("task [%s] can't start or stop before now: %s" % (time_type, datetime.datetime.now()))
        
async def process_timer(atime):
    print("task started:\n", atime)
    topic =         atime["topic"]
    true_value =    atime["true_value"]
    false_value =   atime["false_value"]
    days =          atime["days"]
    start_type =    atime["start_type"]
    start_hour =    atime["start_hour"]
    start_minute =  atime["start_minute"]
    start_offset =  atime["start_offset"]
    stop_type =     atime["stop_type"]
    stop_hour =     atime["stop_hour"]
    stop_minute =   atime["stop_minute"]
    stop_offset =   atime["stop_offset"]
    await asyncio.create_task(wait_and_send(start_type, start_hour, start_minute, start_offset, topic, true_value)) #  ON
    await asyncio.create_task(wait_and_send(stop_type,  stop_hour,  stop_minute,  stop_offset,  topic, false_value)) # OFF
   
async def start_timers(times):
    for atime in times:
        print(atime)
        await process_timer(atime)
        #asyncio.create_task(process_timer(atime, "start", cfg.timer[t]["start"]))
        #asyncio.create_task(wait_and_send(atime, "stop",  cfg.timer[t]["stop"]))
    
async def main():
    # debugging  stuff
    # event_time_string = "21:00"
    # result = time_string_to_seconds(event_time_string)
    # print(f"date hh:mm:ss to  {event_time_string}: {result/60/60} hours.")
    # seconds = seconds_to_event(result)
    # print("hours until event", seconds/60/60)
    # (srise, sset) = get_sunset_sunrise("34.206081324130004, -117.14301072256056")
    # print("sunrise at this hour", srise/60/60)
    # print("sunset at this hour",  sset/60/60)
    # end
    
    # client = mqtt_manager.mqtt_manager()
    db = database.database(row_factory=True)
    await start_timers(db.get_timers_for_today())
    while True:
        await sleep_until_one_second_after_midnight()
        await start_timers(db.get_timers_for_today())
        await asyncio.sleep(1)
        
        
    

if __name__ == "__main__":
    # Run the main coroutine as the entry point of the asyncio program
    asyncio.run(main())
