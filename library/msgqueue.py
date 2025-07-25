import asyncio
# simple queue for single put'er and single get'er thanks to Peter Hinch
class MsgQueue:
    def __init__(self, size):
        self._q = [0 for _ in range(max(size, 4))]
        self._size = size
        self._wi = 0
        self._ri = 0
        self._evt = asyncio.Event()
        self.discards = 0

    def put(self, *v):
        print(".MsgQueue", v)
        self._q[self._wi] = v
        self._evt.set()
        self._wi = (self._wi + 1) % self._size
        if self._wi == self._ri:  # Would indicate empty
            self._ri = (self._ri + 1) % self._size  # Discard a message
            self.discards += 1

    def empty(self):  # added by Jim Dodgen 2025
        #print(".MsgQueue empty ri wi", self._ri, self._wi)
        return True if self._ri == self._wi else False

    def __aiter__(self):
        return self

    async def __anext__(self):
        #print(".MsgQueue __anext__ ri wi", self._ri, self._wi)
        if self._ri == self._wi:  # Empty
            self._evt.clear()
            await self._evt.wait()
        r = self._q[self._ri]
        self._ri = (self._ri + 1) % self._size
        #print(".MsgQueue __anext__ return ", r)
        return r
