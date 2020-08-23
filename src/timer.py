import asyncio
import logging
import time

class Timer:
    
    def __init__(self, timeout, callback, args):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._cancel = False
        
        
    async def _job(self):
        logging.info("_job")
        while(self._cancel == False):
            await asyncio.sleep(self._timeout)
            self._callback(self._args)

        
    def _start(self):
        logging.info("_start")
        self._task = self.loop.create_task(self._job())
        logging.info("_start end")

    def start(self, loop):

        self.loop = loop
        loop.call_soon(self._start)
       

    def cancel(self):
        self._cancel = True
        return self._task


class SingleRunTimer:

    def __init__(self, timeout, callback, args):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._cancel = False
        self._task = None

    async def _job(self):

        await asyncio.sleep(self._timeout)
        self._callback(self, self._args)

    def _start(self):
        self._task = self._loop.create_task(self._job())

    def start(self, loop):
        self._loop = loop
        loop.call_soon_threadsafe(self._start)

    def repeat(self):
        self._start()


def test_timer(value):
       logging.info("{}: Hello from timer callback".format(value["count"]))
       value["count"] += 1
       

async def test(loop):
    i = { "count" : 1}
    t = Timer(1, test_timer, i)
    t.start(loop)
    logging.info("Started timer. Waiting..")
    await asyncio.sleep(5)
    await t.cancel()
    #logging.info("result = {}".format(result) )
    #await asyncio.shield(t._task)

    # try:
    #     await t._task
    # except:
    #     pass

def single_run_timer_cb(timer, value):
    logging.info("{}: Hello from SingleRunTimer callback".format(value["count"]))
    value["count"] += 1

    if(value["count"] <= 3 ):
        timer.repeat()


async def test_single_run(loop):
    i = { "count" : 1}
    t = SingleRunTimer(1, single_run_timer_cb, i)
    t.start(loop)
    logging.info("Started timer. Waiting..")
    await asyncio.sleep(5)
    
    

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    logging.info("Testing timer")
    
    loop = asyncio.get_event_loop()
    #t = loop.create_task(test())
    loop.run_until_complete(test_single_run(loop))
    