from awscrt import io, mqtt
from awsiot import iotshadow, mqtt_connection_builder
import logging
from devicebrowser import IotBrowserInterface, IotBrowser
from servicebrowser import ServiceBrowser, ServiceBrowerInterface
import threading
import logging
import servicemanager as SM
from functools import partial


class IotGateway(ServiceBrowerInterface, SM.ServiceManagerInterface):

    def __init__(self, **kwargs):

        self.thing_name = kwargs['thing_name']
        self.endpoint = kwargs['endpoint']
        self.root_ca_path = kwargs['root_ca_path']
        self.certificate_path = kwargs['certificate_path']
        self.private_key_path = kwargs['private_key_path']
        self.service_list = []
        self.service_map = {}

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

        logging.info("Subscribing to Delta events...")
        delta_subscribed_future, _ = self.shadow_client.subscribe_to_shadow_delta_updated_events(
            request=iotshadow.ShadowDeltaUpdatedSubscriptionRequest(thing_name=self.thing_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=self.on_shadow_delta_updated)


        #delta_subscribed_future, _ = self.shadow_client.subscribe_to_named_shadow_delta_updated_events(
        #        request=iotshadow.NamedShadowDeltaUpdatedSubscriptionRequest(thing_name=self.thing_name,shadow_name=SHADOW_NAME),
        #        qos=mqtt.QoS.AT_LEAST_ONCE,
        #        callback=on_shadow_delta_update)

        delta_subscribed_future.result()

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


    def onShadowDeltaUpdate(self, service, delta_event):
        
        logging.info("Received Shadow delta for service: {}".format(service))
        state = delta_event.state
        timestamp = delta_event.timestamp
        version = delta_event.version
        logging.info("state: {}".format(state))
        logging.info("timestamp: {}".format(timestamp))
        logging.info("version: {}".format(version))

        

    def onServiceFound(self, service):
        logging.info("Service Added: name=%s, type=%s"%(service.name, service.type))
        self.service_list.append(service)
        self.publishState() 
        self.sm.addService(service)

        service_tuple = (service.device_id, service.name, service.type)
        tmp_list = list(service_tuple)
        shadow_name = "-".join(tmp_list)

        logging.info("Subscribing to named shadow Delta events: %s" % shadow_name)
        delta_subscribed_future, topic = self.shadow_client.subscribe_to_named_shadow_delta_updated_events(
            request=iotshadow.NamedShadowDeltaUpdatedSubscriptionRequest(
                thing_name=self.thing_name,shadow_name=shadow_name),
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=partial(self.onShadowDeltaUpdate, service))

        try:
            result = delta_subscribed_future.result()
        except Exception as e:
            logging.error("Error subscribing delta %s" % e)
        logging.info("Subscribed to service delta")
        self.service_map.update({service_tuple: {}})
        self.service_map[service_tuple].update({"service" : service, "shadow_topic": topic})
            
    def onServiceRemoved(self, service):
        logging.info("Service Removed: name=%s, type=%s"%(service.name, service.type))
        self.service_list.remove(service)
        self.publishState()
        self.sm.removeService(service)
        service_tuple = (service.device_id, service.name, service.type)
        topic = self.service_map[service_tuple]["shadow_topic"]
        self.mqtt_connection.unsubscribe(topic=topic)

    def publishState(self):
        #Update thing state corresponding to the gateway 
        sa = []
        for s in self.service_list:
            sd = { 'SERVICE_TYPE': s.type, 'SERVICE_NAME': s.name}
            sa.append(sd)

        msg = { 'services' : sa, 'service_count': len(sa) }

        request = iotshadow.UpdateShadowRequest(
            thing_name=self.thing_name,
            state=iotshadow.ShadowState(reported = msg)
        )

        future = self.shadow_client.publish_update_shadow(request, mqtt.QoS.AT_LEAST_ONCE)
        # Ensure that publish succeeds
        try:
            future.result()
            print("Update request published.")
        except:
            print("Failed to publish update request.")

    def onServiceStateChange(self, service):
        logging.info("Updating Service State to Service Shadow")


    def run(self):

        logging.info("Started..")

        self.sm = SM.ServiceManager()
        self.sm.addServiceMessageInterface(self)
        self.sm.start()

        logging.info("Connecting to AWS Shadow: ")
        self.connect()

        service_browser = ServiceBrowser()
        service_browser.registerServiceBrowserInterface(self)
        service_browser.browse()
        
        deviceBrowser = IotBrowser() 
        deviceBrowser.registerIotBrowserInterface(service_browser)
        deviceBrowser.browse()  

        

        event = threading.Event()
        event.wait()     
