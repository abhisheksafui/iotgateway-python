
from zeroconf import ServiceBrowser, Zeroconf
import logging
import threading
import ipaddress
import abc

class IotBrowserInterface(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def onDeviceAdded(self, name, ip, port):
        pass
    @abc.abstractmethod
    def onDeviceRemoved(self, name):
        pass

class IotBrowser:

    listeners = []

    def __init__(self):
        self.zeroconf = Zeroconf()
        self.listeners = []

    def registerIotBrowserInterface(self, intf):
        self.listeners.append(intf)

    def remove_service(self, zeroconf, type, name):
        logging.info("Service %s removed" % (name))
        for listner in self.listeners:
            listner.onDeviceRemoved(name)

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        #logging.info("Service %s added, service info: %s" % (name, info))

        ip = ipaddress.IPv4Address(info.addresses[0])
        #logging.info("Addresses Discovered: {}".format(ipaddress.IPv4Address(ip[0])))
        logging.info("\t * Name: {}, Address {}:{}".format(info.name, str(ip), info.port))

        for listener in self.listeners:
            listener.onDeviceAdded(name, str(ip), info.port)

    def browse(self):
        self.browser = ServiceBrowser(self.zeroconf, "_iot._udp.local.", self)
        logging.info("Started browsing for _iot._udp.local.")

        


if __name__ == "__main__":

    logging.basicConfig(format='%(levelname)s:%(asctime)s - %(message)s', level=logging.INFO)
    logging.info("Started.")
    #browser = IotBrowser()
    #browser.browse()

    event=threading.Event()
    event.wait()
