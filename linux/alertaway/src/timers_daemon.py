# MIT licence, copyright 2025,2026 Jim Dodgen
version = 0.2

import time
import suntime
import datetime
from dateutil import tz
import asyncio
import multiprocessing
import message
#import paho.mqtt.publish as publish
from aiomqtt import Client
import http_common as config
import timers_tools
CFG = config.get_db_config()

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
    print(f"[sleep_until_one_second_after_midnight]Sleeping  ({wait_seconds/60/60:.2f} hours) until: {target.strftime('%Y-%m-%d %H:%M:%S')}\n")
    #print("[sleep_until_one_second_after_midnight]sleep_until_one_second_after_midnight hours", wait_seconds/60/60)
    await asyncio.sleep(wait_seconds)
    print("[sleep_until_one_second_after_midnight]Waking up! It is now 0:01")

def seconds_to_event(event_time):
    local_time = time.localtime()
    local_time_seconds_since_midnight = local_time.tm_hour * 3600 + local_time.tm_min * 60 + local_time.tm_sec
    #print("hours since midnight", local_time_seconds_since_midnight/60/60)
    seconds = event_time - local_time_seconds_since_midnight
    #print("event_time",event_time/60/60, "seconds left", local_time_seconds_since_midnight/60/60)
    return seconds

async  def wait_and_send(sunrize_seconds,sunset_seconds,lat_long, time_type, hour, minute, offset, topic, payload):
    print(f"task starting '{time_type}' {hour}:{minute} or {offset} [{topic}][{payload}]")
    match time_type:
        case "Sunset":
            print(f"sunset at this hour {sunset_seconds/60/60}")
            seconds = seconds_to_event(sunset_seconds + (int(offset) * 60))
        case "Sunrise":
            print(f"sunrise at this hour {sunrize_seconds/60/60}")
            seconds = seconds_to_event(sunrize_seconds + (int(offset) * 60))
        case _: # default must be just a time in 24 hour format
            since_midnight = (int(minute) * 60) + (int(hour) * 3600) #time_string_to_seconds(time)
            print(f"hours since_midnight [{since_midnight/60/60}]")
            seconds = seconds_to_event(since_midnight)
    print(f"hours until event [{seconds/60/60}]")
    if seconds > 0:
        print(f"async task sleeping [{topic}][{payload}]")
        await asyncio.sleep(seconds) # we are sleeping until timer starts or stops
        # client.publish(topic, payload)
        max_attempts = 6
        for attempt in range(1, max_attempts + 1):
            try:
                async with Client(hostname=CFG["local_broker_ip"], port=CFG["local_broker_port"]) as client:
                    await client.publish(topic, payload)
                print(f"task time now [{datetime.datetime.now()}] sleep done, sent [{topic}][{payload}]")
                break
            except Exception as e:
                # Prevent a network hiccup from crashing the whole daemon
                print(f"[{datetime.datetime.now()}] Failed to send to {topic}: {e}")
            await asyncio.sleep(10*attempt)
    else:
        print(f"late_startup, not sleeping, exiting [{topic}][{payload}]")

async def process_timer(sunrize_seconds, sunset_seconds,lat_long, atime):
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
    invert =        atime["invert"] #  if True/1 then off followed by on turn device off for a period of time
    start_value = false_value if invert else true_value
    stop_value =  true_value  if invert else false_value
    
    asyncio.create_task(wait_and_send(sunrize_seconds, sunset_seconds, lat_long, start_type, start_hour, start_minute, start_offset, topic, start_value)) #  ON typicaly
    asyncio.create_task(wait_and_send(sunrize_seconds, sunset_seconds, lat_long, stop_type,  stop_hour,  stop_minute,  stop_offset,  topic, stop_value)) # OFF

async def start_timers(lat_long, times):
    timetools = timers_tools.tools()
    (sunrize_seconds, sunset_seconds) = timetools.get_sunset_sunrise_since_midnight()
    for atime in times:
        print("start_timers starting:", atime["topic"])
        await process_timer(sunrize_seconds, sunset_seconds, lat_long, atime)

async def main():
    import database
    db = database.database(row_factory=True)
    await start_timers(config.get_db_config()["lat_long"], db.get_timers_for_today())
    while True:
        await sleep_until_one_second_after_midnight()
        await start_timers(config.get_db_config()["lat_long"], db.get_timers_for_today())
        await asyncio.sleep(1)

if __name__ == "__main__":
    # Run the main coroutine as the entry point of the asyncio program
    asyncio.run(main())
