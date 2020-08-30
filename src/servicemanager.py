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

class DeviceManagerInterface:
    
    @abc.abstractmethod
    def onDeviceMessage(self, message):
        pass


class ServiceManager(threading.Thread, asyncio.Protocol, DeviceManagerInterface):

    def __init__(self):

        self.service_map = {}
        self.service_list = []
        self.transport = None
        self.smi_register = []
        self.device_map = {}
        threading.Thread.__init__(self)

    def addServiceMessageInterface(self, inteface):
        self.smi_register.append(inteface)

    def addService(self, new_service):
                
        self.service_list.append(new_service)
        timer = Timer(5, self.sendServiceGetRequest, new_service)
        self.service_map.update({
            (new_service.device_id, new_service.name, new_service.type): 
            { 'service' : new_service, 'timer': timer }
        })
        timer.start(self.loop,repeat=True)

    def removeService(self, service):
        logging.info("Removing Service: {}".format(service))
        try:
            self.service_list.remove(service)
            tup = (service.device_id, service.name, service.type)
            smap =  self.service_map.pop(tup)
            timer = smap['timer']
            timer.stop()

        except Exception as e:
            logging.error("Error removing device: {}".format(e))


    def routeDeviceRequest(self, service, request):


        try:
            dt = (service.device_id, service.addr)     
            dm = self.device_map.get(dt)

            if dm == None:
                logging.debug("Creating DM: {}".format(dt))
                dm = DeviceManager(service.device_id, service.addr, self.loop)
                dm.register(self)
                dm.start()
                self.device_map.update({dt: dm})
                logging.debug("Device Map: {}".format(self.device_map))
            
            dm.queueMessage(request)      
        except Exception as e:
            print(e)

    def sendServiceGetRequest(self, timer, s):
        """
        This method is called from periodic timer, running in Service Manager thread for each service, 
        to refresh the state of the device. Since each device has multiple services, multiple requests 
        may get queued up at iot device with small memory. So these requests should be queued in gateway
        and sent one at a time
        """

        #put the request in the queue
        msg = s.formGetRequest()
        self.routeDeviceRequest(s, msg)
        

    
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

    def processDeviceMessage(self, message):
        try:
            logging.debug("Received UDP data %s" %(message))

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
            logging.error("Exception in processDeviceMessage {}".format(e))

    def onDeviceMessage(self, message):

        self.processDeviceMessage(message)




class DeviceManager(asyncio.Protocol):
    """
    Send and receives messages to and from an IOT device. 
    Every discovered service belongs to a device, identified by 
    device id and ip,port. Sending any message to the service 
    means sending message to the device. 

    Purpose of this class is to queue the messages to be send to 
    the device and send them one message a time, waiting for a 
    response from the device.
    """

    def __init__(self, device_id, addr, loop):
        self._listeners = []
        self._device_id = device_id
        self._addr = addr
        self._loop = loop
        self._queue = asyncio.Queue(loop=loop)
        self._transport = None
        self._resp_cond = asyncio.Condition(loop=loop)
        self._respose = None
        self._miss_count = 0
        
        #self._last_activity = time.time()

    
    def start(self):
        cor =  self._loop.create_datagram_endpoint(lambda : self, local_addr=('0.0.0.0', 0))
        self._datagram_task = self._loop.create_task(cor)
        self._dequeue_task = self._loop.create_task(self.deviceQueueHandler())
        self._on_connection_made = self._loop.create_future()


    def register(self, listener):
        self._listeners.append(listener)

    def connection_made(self, transport):
        self._transport = transport
        sock = transport.get_extra_info('socket')
        logging.debug("Listening for Device {} on {}".format(self._device_id, sock.getsockname()))
        self._on_connection_made.set_result(True)

    def datagram_received(self, data, addr):
        logging.debug("Received data from device {}".format(self._device_id))
        msg = data.decode()
        logging.debug("Data: {}".format(msg))
        self._respose = msg
        self._loop.create_task(self.signalQueueHandler())
        
    def queueMessage(self, request):
        self._queue.put_nowait(request)

    async def signalQueueHandler(self):
        logging.debug("Signalling condition for device: {}".format(self._device_id))
        async with self._resp_cond:
            logging.debug("Aquired self._resp_cond for signalling")
            self._resp_cond.notify()

    async def deviceQueueHandler(self):
        try:
            #wait for connection to be complete
            await self._on_connection_made
            logging.debug("Connection made. Proceeding to dequeue..")
            while True:
                logging.debug("Before queue.get()")
                msg = await self._queue.get()
                logging.debug("After queue.get()")
                #msg_type = msg.get(ServiceMsgKeys.MSG_TYPE)

                try_count = 0
                

                while try_count < 3:   
                    m = json.dumps(msg).encode()
                    logging.debug("{}. Sending to {} : {}".format(try_count, 
                    self._addr, m))  

                    self._transport.sendto(m , self._addr) 
                    logging.debug("Sent")
                    try_count += 1
                    try:
                        logging.debug("waiting for self._resp_cond")
                        async with self._resp_cond:
                            logging.debug("Aquired self._resp_cond")
                            #await asyncio.wait_for(self._resp_cond.wait(), timeout=1, loop=self._loop)
                            future = self._loop.create_task(self.wait_on_condition_with_timeout(self._resp_cond, 1))
                            await future
                            #await self._resp_cond.wait_for()
                            #response received
                            #TODO: match the request and response
                            # if self._respose[ServiceMsgKeys.MSG_TYPE] == 
                            logging.info("Response received {}".format(self._respose))
                            
                            for l in self._listeners:
                                l.onDeviceMessage(self._respose)

                            self._miss_count = 0
                            self._respose = None
                            break

                    except asyncio.TimeoutError:
                        logging.info("Request timeout")
                        self._miss_count += 1
                    except Exception as e:
                        logging.error("Caught exception in waiting for condition {}".format(e))

                self._queue.task_done()
        except Exception as e:
            logging.error(e)


    async def wait_on_condition_with_timeout(self , condition: asyncio.Condition, timeout: float) -> bool:
        loop = self._loop

        # Create a future that will be triggered by either completion or timeout.
        waiter = loop.create_future()

        # Callback to trigger the future. The varargs are there to consume and void any arguments passed.
        # This allows the same callback to be used in loop.call_later and wait_task.add_done_callback,
        # which automatically passes the finished future in.
        def release_waiter(*_):
            if not waiter.done():
                waiter.set_result(None)

        # Set up the timeout
        timeout_handle = loop.call_later(timeout, release_waiter)

        # Launch the wait task
        wait_task = loop.create_task(condition.wait())
        wait_task.add_done_callback(release_waiter)

        try:
            await waiter  # Returns on wait complete or timeout
            if wait_task.done():
                return True
            else:
                raise asyncio.TimeoutError()

        except (asyncio.TimeoutError, asyncio.CancelledError):
            # If timeout or cancellation occur, clean up, cancel the wait, let it handle the cancellation,
            # then re-raise.
            wait_task.remove_done_callback(release_waiter)
            wait_task.cancel()
            await asyncio.wait([wait_task])
            raise

        finally:
            timeout_handle.cancel()