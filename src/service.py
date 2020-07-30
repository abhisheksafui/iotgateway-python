import abc

class Contact:
    @abc.abstractmethod
    def send(self, msg)

class IpAddressContact(Contact):

    def __init__(self, ip, port)
        self.ip = ip 
        self.port = port
    def send(self):
        pass

class Service:

    def __init__(self, name, type, contact):
        self.name = name
        self.type = type
        self.contact = contact

    def getState(self, state):
        pass
    def setState(self,state):
        pass