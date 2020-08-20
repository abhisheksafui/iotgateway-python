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

    def __init__(self, name, type, device_id, contact):
        self.name = name
        self.type = type
        self.device_id = device_id
        self.contact = contact
        self.state = {}
        
    def sendGetRequest(self):

        msg = { 
            "MSG_TYPE" : "GET_REQUEST" ,
            "SERVICE_ARRAY" : [ { "SERVICE_TYPE" : self.type.name, "SERVICE_NAME" : self.name  } ]
        }

        self.contact.send(json.dumps(msg, indent=2))

    # def updateShadowState(self):
    
    #     request = iotshadow.UpdateNamedShadowRequest(
    #         thing_name=self.thing_name,
    #         shadow_name=self.device_id + "-" + self.name,
    #         state=iotshadow.ShadowState(reported = self.state)
    #     )

    #     future = self.shadow_client.publish_update_named_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
    #     # Ensure that publish succeeds
    #     try:
    #         future.result()
    #         print("Update request published.")
    #     except Exception as e:
    #         print("Failed to publish update request.")



    def onDeltaUpdate(self):
        pass

    def subscribeDelta(self, shadow_client):
        pass
