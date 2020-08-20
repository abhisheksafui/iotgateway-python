
from gateway import IotGateway
import logging
from devicebrowser import IotBrowser
from servicebrowser import ServiceBrowser

THING_NAME="RaspberryPiZero"
MY_IOT_END_POINT = '/home/pi/endpoint'
KEY_DIR_PATH = '/home/pi/certificates/'
ROOT_CA_PATH = KEY_DIR_PATH + 'AmazonRootCA1.pem'
PRIVATE_KEY_PATH = KEY_DIR_PATH + 'ab079d4a90-private.pem.key'
CERTIFICATE_PATH = KEY_DIR_PATH + 'ab079d4a90-certificate.pem.crt' 


def init():

    #Initialize logging
    logging.basicConfig(format='%(levelname)s:%(asctime)s - %(message)s', level=logging.INFO)
    logging.info("Started.")

if __name__ == "__main__":

    init()

    with open(MY_IOT_END_POINT,"r") as f:
        endpoint = f.read().strip()

    logging.info("Endpoint: %s" % endpoint)
    gateway = IotGateway(
        endpoint=endpoint,
        root_ca_path=ROOT_CA_PATH,
        certificate_path=CERTIFICATE_PATH,
        private_key_path=PRIVATE_KEY_PATH,
        thing_name=THING_NAME)

    gateway.run()

  