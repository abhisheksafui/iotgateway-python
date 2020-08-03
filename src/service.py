import abc
import socket
import enum
import json
from devicebrowser import IotBrowserInterface

class Contact:
    @abc.abstractmethod
    def send(self, msg):
        pass

class IpAddressContact(Contact):

    def __init__(self, ip, port, socket=None):
        self.ip = ip 
        self.port = port
        self.sock = socket

        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


    def send(self, msg):
        self.sock.sendto(msg, (self.ip, self.port))

class ServiceType(enum.Enum):
    SWITCH=1,
    DIMMER=2


class Service:

    def __init__(self, name, type, contact):
        self.name = name
        self.type = type
        self.contact = contact
        


    def prepare_get_message(self):
        msg = \
        { 
            "MSG_TYPE" : "GET_REQUEST" ,
            "SERVICE_ARRAY" : [ { "SERVICE_TYPE" : self.type.name, "SERVICE_NAME" : self.name  } ]
        }
        return json.dumps(msg, indent=2)

    def sendGetRequest(self, state):

        msg = self.prepare_get_message()
        self.contact.send(msg)

    def setState(self,state):
        pass

