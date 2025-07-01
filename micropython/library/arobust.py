import asimple
import asyncio

# conditional formatted print replacement
# MIT License Copyright Jim Dodgen 2025
# if first string starts with a "." then the first word of the string is appended to the print_tag
# typically identifying the routine
# this needs to be pasted into your .py file
#
print_tag = "robust"
do_prints = True # usually set to False in production
#
def turn_on_prints(flag):  # true or false
    global do_prints
    do_prints=flag
raw_print = print # copy print
def print(first, *args, **kwargs): # replace print
    global do_prints
    if do_prints:
        f=None
        if isinstance(first, str) and first[0] == ".":
            f = first.split(" ",1)
        else:
            f = ["",first]
        try:
            if len(f) > 1:
                raw_print("["+print_tag+f[0]+"]", f[1], *args, **kwargs) # the copied real print
            else:
                raw_print("["+print_tag+f[0]+"]", *args, **kwargs) # the copied real print
        except:
            raise ValueError("xprint problem ["+print_tag+"]")


class MQTTClient(asimple.MQTTClient):
    list_of_topics = None
    list_of_pubs = None

    def set_error_queue(self,q):
        self.error_queue = q

    def subscribe_topics(self, list_of_topics):
        self.list_of_topics = list_of_topics

    async def _send_subscribes(self):
        print("._send_subscribes sending", self.list_of_topics)
        for topic in self.list_of_topics:
            print("_send_subscribes super [", topic, "]")
            try:
                await self.subscribe(topic)
            except OSError as e:
                print("._send_subscribes OSError", e)

    def retain_pub_topics(self, list_of_pubs):
        self.list_of_pubs = list_of_pubs

    async def _send_retain_pub(self):
        print("._send_retain_pub sending", self.list_of_pubs)
        if self.list_of_pubs:
            for topic, payload in self.list_of_pubs:
                super().publish(topic, payload, retain=True)

    async def always_connect(self, new=False):
        i = 0
        while True:
            try:
                result = super().connect(clean_session=False)
                await asyncio.sleep(2)
            except OSError as e:
                print(".always_connect OSError", e)
                i += 1
                await asyncio.sleep(5)
            else:
                print(".always_connect sending subscribes and retains", self.list_of_topics, self.list_of_pubs)
                await self._send_subscribes()
                await self._send_retain_pub()
                print(".always_connect subs&pubs sent")
                self.error_queue.put(0)
                return result


    async def publish(self, topic, msg, retain=False, qos=0):
        ret = None
        while True:
            try:
                print(".publish [", topic, "][", msg, "]")
                ret = super().publish(topic, msg, retain, qos)
            except OSError as e:
                print(".publish failed so do always_connect",e)
                self.error_queue.put(4) # ERROR_BROKER_CONNECT_FAILED =  4
                await self.always_connect()
                await asyncio.sleep(1)
            else:
                return ret

    async def wait_msg(self):
        print(".wait_msg")
        ret = None
        while True:
            try:
                print(".wait_msg super")
                ret = await super().wait_msg()
            except OSError as e:
                print(".wait_msg got eror",e,"trying again")
                await asyncio.sleep(1)
                await self.always_connect()
            else:
                return ret

    async def check_msg(self, attempts=2):
        #print(".check_msg")
        ret = None
        while True:
            # self.sock.setblocking(False)
            try:
                # return self.wait_msg()
                ret =  await super().wait_msg()
            except OSError as e:
                await asyncio.sleep(1)
                await self.always_connect()
            else:
                return ret

