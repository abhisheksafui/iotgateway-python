import socket
import service
import queue
import threading
import logging
import asyncio

class ServiceManagerInterface:

    def onServiceStateChange(self):
        pass 



class ServiceManager(asyncio.Protocol):

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.service_map = {}
        self.service_list = []

    def addService(self, device_id, s_name, s_type, addr):
        
        new_service = service.Service(s_name, s_type, device_id, addr)
        self.service_map.update({
            (device_id, s_name, s_type): { 'service' : new_service, 'queue' : queue.Queue() }
        })
        self.service_list.append(new_service)

            
  
    def getServiceState(self, service):

        msg = service.formGetRequest()
        data = msg.encode()

        self.transport.sendto(data, service.addr)


    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data, addr):
        message = data.decode()
        logging.info("Received UDP data %s from %s" %(message, addr))


    
    async def threadFunction(self):
        
        logging.info("Started Service Manager Thread")
        loop = asyncio.get_event_loop()

        transport, protocol = await loop.create_datagram_endpoint(self, local_addr=('0.0.0.0', 0))
        sock = transport.get_extra_info('socket')
        logging.info("Started listening to UDP events from Services")
        logging.info("Listening on {}".format(sock.getsockname()))


    def launch(self):

      
        thread = threading.Thread(target = self.threadFunction)
        thread.start()
       

        

