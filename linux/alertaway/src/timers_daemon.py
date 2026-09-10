# MIT licence, copyright 2025,2026 Jim Dodgen
VERSION = 0.3

import time
import suntime
import datetime
from dateutil import tz
import asyncio
from aiomqtt import Client
# import multiprocessing
# import message
import http_common as config
import timers_tools
CFG = config.get_db_config()

xprint = print 
my_name = "[timers_daemon]"
def print(*args, **kwargs): 
    xprint(my_name, *args, **kwargs) 

async def sleep_until_one_second_after_midnight():
    now = datetime.datetime.now()
    target = now.replace(hour=0, minute=1, second=0, microsecond=0)
    if now >= target:
        target += datetime.timedelta(days=1)
    wait_seconds = (target - now).total_seconds()
    print(f"[sleep_until_one_second_after_midnight]Current time: {now.strftime('%H:%M:%S')}")
    print(f"[sleep_until_one_second_after_midnight]Sleeping ({wait_seconds/3600:.2f} hours) until: {target.strftime('%Y-%m-%d %H:%M:%S')}\n")
    await asyncio.sleep(wait_seconds)
    print("[sleep_until_one_second_after_midnight]Waking up! It is now 0:01")

def seconds_to_event(event_time):
    local_time = time.localtime()
    local_time_seconds_since_midnight = local_time.tm_hour * 3600 + local_time.tm_min * 60 + local_time.tm_sec
    seconds = event_time - local_time_seconds_since_midnight
    return seconds

async def wait_and_send(sunrize_seconds, sunset_seconds, lat_long, time_type, hour, minute, offset, topic, payload):
    print(f"task starting '{time_type}' {hour}:{minute} or {offset} [{topic}][{payload}]")
    match time_type:
        case "Sunset":
            print(f"sunset at this hour {sunset_seconds/3600}")
            seconds = seconds_to_event(sunset_seconds + (int(offset) * 60))
        case "Sunrise":
            print(f"sunrise at this hour {sunrize_seconds/3600}")
            seconds = seconds_to_event(sunrize_seconds + (int(offset) * 60))
        case _: 
            since_midnight = (int(minute) * 60) + (int(hour) * 3600) 
            print(f"hours since_midnight [{since_midnight/3600}]")
            seconds = seconds_to_event(since_midnight)
            
    print(f"hours until event [{seconds/3600}]")
    
    # CHANGED: >= 0 handles immediate/near-immediate execution better
    if seconds >= 0:
        print(f"async task sleeping [{topic}][{payload}]")
        try:
            await asyncio.sleep(seconds) 
        except asyncio.CancelledError:
            print(f"Task for [{topic}] cancelled because day changed.")
            raise

        max_attempts = 6
        for attempt in range(1, max_attempts + 1):
            try:
                async with Client(hostname=CFG["local_broker_ip"], port=CFG["local_broker_port"]) as client:
                    await client.publish(topic, payload)
                print(f"task time now [{datetime.datetime.now()}] sleep done, sent [{topic}][{payload}]")
                break
            except Exception as e:
                print(f"[{datetime.datetime.now()}] Failed to send to {topic}: {e}")
                # FIXED: Move backoff sleep inside the exception block and check threshold
                if attempt < max_attempts:
                    try:
                        await asyncio.sleep(10 * attempt)
                    except asyncio.CancelledError:
                        raise
    else:
        print(f"late_startup, not sleeping, exiting [{topic}][{payload}]")

async def process_timer(sunrize_seconds, sunset_seconds, lat_long, atime, task_list):
    topic =         atime["topic"]
    true_value =    atime["true_value"]
    false_value =   atime["false_value"]
    start_type =    atime["start_type"]
    start_hour =    atime["start_hour"]
    start_minute =  atime["start_minute"]
    start_offset =  atime["start_offset"]
    stop_type =     atime["stop_type"]
    stop_hour =     atime["stop_hour"]
    stop_minute =   atime["stop_minute"]
    stop_offset =   atime["stop_offset"]
    invert =        atime["invert"] 
    
    start_value = false_value if invert else true_value
    stop_value =  true_value  if invert else false_value
    
    # CHANGED: Track these tasks so we can destroy them at midnight
    t1 = asyncio.create_task(wait_and_send(sunrize_seconds, sunset_seconds, lat_long, start_type, start_hour, start_minute, start_offset, topic, start_value))
    t2 = asyncio.create_task(wait_and_send(sunrize_seconds, sunset_seconds, lat_long, stop_type,  stop_hour,  stop_minute,  stop_offset,  topic, stop_value))
    task_list.extend([t1, t2])

async def start_timers(lat_long, times, task_list):
    timetools = timers_tools.tools()
    (sunrize_seconds, sunset_seconds) = timetools.get_sunset_sunrise_since_midnight()
    for atime in times:
        print("start_timers starting:", atime["topic"])
        await process_timer(sunrize_seconds, sunset_seconds, lat_long, atime, task_list)

async def main():
    import database
    db = database.database(row_factory=True)
    
    # Container to hold current day's active scheduled sleep tasks
    current_day_tasks = []
    
    # Initial startup for day one
    await start_timers(config.get_db_config()["lat_long"], db.get_timers_for_today(), current_day_tasks)
    
    while True:
        await sleep_until_one_second_after_midnight()
        
        # CHANGED: Cancel all lingering sleeps from yesterday before pulling fresh rows
        print("Midnight reached. Purging yesterday's lingering scheduled tasks...")
        for task in current_day_tasks:
            if not task.done():
                task.cancel()
        
        # Clear out our tracker cache
        current_day_tasks.clear()
        
        # Load up fresh configs and spin up new clean tasks
        await start_timers(config.get_db_config()["lat_long"], db.get_timers_for_today(), current_day_tasks)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
