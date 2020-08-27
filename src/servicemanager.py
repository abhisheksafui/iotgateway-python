import socket
from service import Service, ServiceMsgKeys, ServiceMsgTypes
import queue
import threading
import logging
import asyncio
from timer import Timer
import json
import abc

class ServiceManagerInterface:

    @abc.abstractmethod
    def onServiceStateChange(self, service):
        pass 

def tf(a,b):
    logging.info("tf")

class ServiceManager(threading.Thread, asyncio.Protocol):

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.service_map = {}
        self.service_list = []
        self.transport = None
        self.smi_register = []
        threading.Thread.__init__(self)

    def addServiceMessageInterface(self, inteface):
        self.smi_register.append(inteface)

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
        logging.debug("Sending request: {}".format(msg))
        logging.debug("Sending to: {}".format(s.addr))
        data = json.dumps(msg).encode()
        self.transport.sendto(data, s.addr)

    
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        logging.info("Started listening to UDP events from Services")
        logging.info("Listening on {}".format(sock.getsockname()))

    def datagram_received(self, data, addr):

        try:

            message = data.decode()
            logging.debug("Received UDP data %s from %s" %(message, addr))

            msg_dict = json.loads(message)
            device_id = msg_dict.get(ServiceMsgKeys.DEVICE_ID.value)
            msg_type =  msg_dict.get(ServiceMsgKeys.MSG_TYPE.value) 

            if msg_type == ServiceMsgTypes.GET_RESPONSE.value:

                for s in msg_dict.get(ServiceMsgKeys.SERVICE_ARRAY.value, {}):
                    name = s.get(ServiceMsgKeys.SERVICE_NAME.value)
                    type = s.get(ServiceMsgKeys.SERVICE_TYPE.value)
                    state = s.get(ServiceMsgKeys.SERVICE_STATE.value)
                    s_map = self.service_map[(device_id, name, type)]
                    service = s_map.get("service")
                    
                    if service == None:
                        logging.warn("Service not found: ({} {} {})".format(device_id, name, type))
                        continue

                    if service.state != state:
                        logging.info("Service state changed ")
                        service.setState(state)
                        for r in self.smi_register:
                            r.onServiceStateChange(service)


        except Exception as e:
            logging.error("Exception in datagram_receive processing {}".format(e))




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

        

