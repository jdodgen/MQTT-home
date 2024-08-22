from ipcqueue import posixmq
import time
#testing Perl QueueManger.pm to have it handle python pickled messages  as well as perl "Storable"
#send to perl example 
# rq= posixmq.Queue('/ReceiveQueue')
# while True:
#     print("sending message")
#     rq.put({"name": "python water_sensor_2", "value": "foobar to you"})
#     print(rq.qsize())
#     time.sleep(4)

receive from perl example
rq= posixmq.Queue('/SendQueue')
while True:
    print("sending message")
    try:
        msg = rq.get(timeout=None)
    except:
        print("problem getting message")
    print(rq.qsize())
    print(msg)
