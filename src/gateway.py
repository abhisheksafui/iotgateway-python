from awscrt import io, mqtt
from awsiot import iotshadow, mqtt_connection_builder
import logging
from devicebrowser import IotBrowserInterface, IotBrowser
from servicebrowser import ServiceBrowser, ServiceBrowerInterface
import threading
import logging


class IotGateway(ServiceBrowerInterface):

    def __init__(self, **kwargs):

        self.thing_name = kwargs['thing_name']
        self.endpoint = kwargs['endpoint']
        self.root_ca_path = kwargs['root_ca_path']
        self.certificate_path = kwargs['certificate_path']
        self.private_key_path = kwargs['private_key_path']
        self.service_list = []

    def connect(self):

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

        self.mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.certificate_path,
            pri_key_filepath=self.private_key_path,
            client_bootstrap=client_bootstrap,
            ca_filepath=self.root_ca_path,
            client_id=self.thing_name,
            clean_session=False,
            keep_alive_secs=6)

        connected_future = self.mqtt_connection.connect()
        self.shadow_client = iotshadow.IotShadowClient(self.mqtt_connection)
        connected_future.result()

        logging.info("Connected to mqtt server.")


    def subscribe_device_topics(self):

        self_topic = "/" + self.thing_name
        self.subscribe(self_topic, self.on_message)

    def on_shadow_delta_updated(self, event):
        pass


    def subscribe_shadow_delta(self):

        print("Subscribing to Delta events...")
        delta_subscribed_future, _ = self.shadow_client.subscribe_to_shadow_delta_updated_events(
            request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(thing_name=self.thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.on_shadow_delta_updated)


        #delta_subscribed_future, _ = self.shadow_client.subscribe_to_named_shadow_delta_updated_events(
        #        request=iotshadow.NamedShadowDeltaUpdatedSubscriptionRequest(thing_name=self.thing_name,shadow_name=SHADOW_NAME),
        #        qos=mqtt.QoS.AT_LEAST_ONCE,
        #        callback=on_shadow_delta_update)

        #delta_subscribed_future.result()

        print("Subscribed to shadow delta. Waiting for delta event")


    def on_message(self, topic, payload, **kwargs):
        
        return
    def subscribe(self, topic, callback):

        logging.info("Subscribing to topic: {topic}".format(topic=topic))
        try:

            subscribe_future, _ = self.mqtt_connection.subscribe(
                topic=topic,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=callback)

            subscribe_result = subscribe_future.result()
            logging.info("Subscribed with {}".format(str(subscribe_result['qos'])))
        except Exception as e:
            logging.info(e)

    def on_service_discovered(self, service):
        self.service_list.append(service)

    def onServiceFound(self, service):
        pass

    def onServiceRemoved(self, service):
        pass



    def run(self):

        logging.info("Started..")
        service_browser = ServiceBrowser()
        service_browser.registerServiceBrowserInterface(self)
        service_browser.browse()
        
        deviceBrowser = IotBrowser() 
        deviceBrowser.registerIotBrowserInterface(service_browser)
        deviceBrowser.browse()  

        event = threading.Event()
        event.wait()     
