import abc
import socket
import enum
import json
from devicebrowser import IotBrowserInterface
   
class ServiceMsgKeys(enum.Enum):
    MSG_TYPE = "MSG_TYPE"
    SERVICE_ARRAY = "SERVICES"
    SERVICE_TYPE = "SERVICE_TYPE"
    SERVICE_NAME = "SERVICE_NAME"

class Service:

    def __init__(self, name, type, device_id, addr):
        self.name = name
        self.type = type
        self.device_id = device_id
        self.addr = addr
        self.state = {}
        
    def formGetRequest(self):

        msg = { 
            ServiceMsgKeys.MSG_TYPE.value : "GET_REQUEST" ,
            ServiceMsgKeys.SERVICE_ARRAY.value : [ { "SERVICE_TYPE" : self.type, "SERVICE_NAME" : self.name  } ]
        }

        return msg

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


