import asyncio
import logging
import time
import threading

# class Timer:
    
#     def __init__(self, timeout, callback, args):
#         self._timeout = timeout
#         self._callback = callback
#         self._args = args
#         self._cancel = False
        
        
#     async def _job(self):
#         logging.info("_job")
#         while(self._cancel == False):
#             await asyncio.sleep(self._timeout)
#             self._callback(self._args)

        
#     def _start(self):
#         logging.info("_start")
#         self._task = self.loop.create_task(self._job())
#         logging.info("_start end")

#     def start(self, loop):

#         self.loop = loop
#         loop.call_soon(self._start)
       

#     def cancel(self):
#         self._cancel = True
#         return self._task


class Timer:
    
    def __init__(self, timeout, callback, args):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._cancel = False
        self._task = None
        self._repeat = False

    async def _job(self):

        #logging.info("_job called")
        await asyncio.sleep(self._timeout)
        #logging.info("_job calling callback")
        self._callback(self, self._args)
        #logging.info("_job callback finished")
        if self._repeat == True:
          self.repeat()

    def _start(self):
        #logging.info("_start called ")
        self._task = self._loop.create_task(self._job())

    def start(self, loop=None, repeat=False):
        #logging.info("start called")
        self._loop = loop
        self._repeat=repeat
        loop.call_soon_threadsafe(self._start)

    def repeat(self):
        self._start()



def test_timer(value):
       logging.info("{}: Hello from timer callback".format(value["count"]))
       value["count"] += 1
       
   

def thread_func(loop):
    
  logging.info("Thread launched..")
  asyncio.set_event_loop(loop)
  logging.info("Starting loop forever..")
  loop.run_forever()


if __name__ == "__main__":
    
  logging.basicConfig(format='%(levelname)s:%(asctime)s [%(thread)d] - %(message)s', level=logging.INFO)
  logging.info("Hello from main thread!!")
  loop = asyncio.new_event_loop()
  t = threading.Thread(target=thread_func, args=(loop,))
  t.start()
  a = { "count" : 1}
  timer = Timer(1,test_timer,a)
  timer.start(loop, repeat=True)
  #t.join(10)

    