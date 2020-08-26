import socket
import service
import queue
import threading
import logging
import asyncio
from timer import Timer
import json

class ServiceManagerInterface:

    def onServiceStateChange(self):
        pass 

def tf(a,b):
    logging.info("tf")

class ServiceManager(threading.Thread, asyncio.Protocol):

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.service_map = {}
        self.service_list = []
        self.transport = None
        threading.Thread.__init__(self)

    def addService(self, new_service):
                
        self.service_list.append(new_service)
        timer = Timer(5, self.sendServiceGetRequest, new_service)
        self.service_map.update({
            (new_service.device_id, new_service.name, new_service.type): 
            { 'service' : new_service, 'queue' : queue.Queue(), 'timer': timer }
        })
        timer.start(self.loop,repeat=True)
            
    def sendServiceGetRequest(self, timer, s):
        
        msg = s.formGetRequest()
        logging.info("Sending request: {}".format(msg))
        logging.info("Sending to: {}".format(s.addr))
        data = json.dumps(msg).encode()
        self.transport.sendto(data, s.addr)

    
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        logging.info("Started listening to UDP events from Services")
        logging.info("Listening on {}".format(sock.getsockname()))

    def datagram_received(self, data, addr):
        message = data.decode()
        logging.info("Received UDP data %s from %s" %(message, addr))

    def threadFunction(self):

        logging.info("Started Service Manager Thread")
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        cor =  self.loop.create_datagram_endpoint(lambda : self, local_addr=('0.0.0.0', 0))
        self.loop.create_task(cor)
        
        self.loop.run_forever()

    def run(self):

        logging.info("Started Service Manager Thread")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        cor =  self.loop.create_datagram_endpoint(lambda : self, local_addr=('0.0.0.0', 0))
        self.loop.create_task(cor)
        
        self.loop.run_forever()

        

