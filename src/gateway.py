from awscrt import io, mqtt
from awsiot import iotshadow, mqtt_connection_builder


class IotGateway:

    def __init__(self, **kwargs):

        self.thing_name = kwargs['thing_name']
        self.endpoint = kwargs['endpont']
        self.root_ca_path = kwargs['root_ca_path']
        self.certificate_path = kwargs['certifcate_path']
        self.private_key_path = kwargs['private_key_path']

    def connect(self):

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootStrap(event_loop_group, host_resolver)

        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.certificate_path,
            pri_key_filepath=self.private_key_path,
            client_bootstrap=client_bootstrap,
            ca_filepath=self.root_ca_path,
            client_id=self.thing_name,
            clean_session=False,
            keep_alive_secs=6)

        connected_future = mqtt_connection.connect()
        self.shadow_client = iotshadow.IotShadowClient(mqtt_connection)
        connected_future.result()
