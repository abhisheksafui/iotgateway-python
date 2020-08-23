from devicebrowser import IotBrowserInterface
import abc
from service import Service
import threading
import json
import logging
import socket

BUFFSIZ=1024

class ServiceBrowerInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def onServiceFound(self, service):
        pass

    @abc.abstractmethod
    def onServiceRemoved(self, service):
        pass

class ServiceBrowser(IotBrowserInterface):
    BUFFSIZ = 1024

    def __init__(self):
        self.devices = {}
        self.device_ip_port_map = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listeners = []
        
    def registerServiceBrowserInterface(self, service_interface):
        self.listeners.append(service_interface)

    def queryDeviceServices(self, ip, port):

        msg = { "MSG_TYPE" : "SERVICES_REQUEST" }
        msg_str = json.dumps(msg)
        self.sock.sendto(msg_str.encode('utf-8'), (ip, port))
        logging.info("Sent SERVICES_REQUEST to {ip}:{port}".format(ip=ip, port=port))

    def onDeviceAdded(self, name, ip, port):
        """ Store name to ip,port mapping and (ip,port) to dict of name 
        and service mapping.
        
        devices is dict for handling mdns device events that identifies 
        device by name. This name is mapped to ip,port.
        
        device_ip_port is a dict used in communications with the device, 
        on receiving messages from the device
        """

        self.devices[name] = dict(ip = ip, port = port)
        self.device_ip_port_map.update({(ip, port) : { "name" : name }})
        self.queryDeviceServices(ip,port)
    
    def onDeviceRemoved(self, name):
        device = self.devices.get(name)
        if device is None:
            logging.error("Device {name} not found".format(name=name))
            return
        ip = device.get("ip")
        port = device.get("port")
        services = self.device_ip_port_map[(ip,port)].get("services")
        if services is None:
            logging.info("Device has no services")
            return
        
        for service in services:
            for listner in self.listeners:
                listner.onServiceRemoved(service)

    def parseDeviceMessage(self, msg, addr, port, sock):
        json_msg = json.loads(msg.decode())
        logging.info("Received Message from {addr}:\n {json_msg}".format(addr=addr,json_msg=json_msg))

        msg_type = json_msg.get("MSG_TYPE")
        device_id = json_msg.get("DEVICE_ID")

        if msg_type is not None:
            services = json_msg.get("SERVICES")
            
            for s in services:
                type = s.get("SERVICE_TYPE")
                name = s.get("SERVICE_NAME")

                new_service = Service(name, type, device_id, (addr,port))
                self.device_ip_port_map[(addr,port)].update({"services": [new_service]})

                for listner in self.listeners:
                    listner.onServiceFound(new_service)


    def listenToDevices(self):
        
        is_running = True

        while is_running:
            msg, (addr, port) = self.sock.recvfrom(BUFFSIZ)
            self.parseDeviceMessage(msg, addr, port, self.sock)

    def browse(self):

        thread = threading.Thread(target=self.listenToDevices)
        thread.start()