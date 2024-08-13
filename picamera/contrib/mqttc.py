#
# mqtt service
#
import json, time, logging, ssl
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MqttBase(object):
    def __init__(self, **p):
        super().__init__()
        self.host           = p.get('host')
        self.port           = p.get('port')
        self.username       = p.get('username')
        self.password       = p.get('password')
        self.keepalive      = p.get('keepalive')
        self.use_ssl        = p.get('use_ssl', False)
        self.ca_cert        = p.get('ca_cert')
        self.tls_version    = p.get('tls_version', ssl.PROTOCOL_TLSv1_2)
        self.subscriptions  = [(topic, qos) for topic, qos in p.get('topic_subs', [])]
        self.unsubs         = self.client_get_unsubs()
        self.topic_base     = p.get('topic_base', '')
        self.uuid =  p.get('uuid')

        self.on_message_callback = p.get('on_messages', self._on_message_callback)
        self.on_bytes_callback = p.get('on_bytes', self._on_bytes_callback)
        # mqtt Client
        self.client = mqtt.Client()
        if self.username:
            self.client.username_pw_set(username=self.username, password=self.password)
        if self.use_ssl and self.ca_cert:
            self.client.tls_set(ca_certs=self.ca_cert, tls_version=self.tls_version)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log

    def client_get_unsubs(self):
        return [topic for topic, _ in self.subscriptions ]


    def client_set_subscriptions(self):
        self.client.unsubscribe(self.client_get_unsubs())
        self.client.subscribe(self.subscriptions)
        logger.info(f"\n    client_set_subscription {self.subscriptions}")


    def client_add_subscriptions(self, subs=[]):
        self.subscriptions += subs
        self.subscriptions = list(set(self.subscriptions))


    def _publish_message(self, topic, **payload):
        try:
            qos = payload.pop('qos', 0)
            retain = payload.pop('retain', False)
            if not payload:
                payload = ''
            message = json.dumps(payload)
            self.client.publish(topic, payload=message.encode('utf-8'), qos=qos, retain=retain)
        except Exception as e:
            logger.error(e)


    def _publish_bytes(self, topic, payload, **conf):
        try:
            qos = conf.pop('qos', 0)
            retain = conf.pop('retain', False)
            self.client.publish(topic, payload=payload, qos=qos, retain=retain)
        except Exception as e:
            logger.error(f"\n    _publish_bytes error: {e}")


    def _on_log(self, mqttc, obj, level, string):  # @UnusedVariable
        pass


    def _on_connect_info(self, info):
        logger.info(info)


    def _on_connect(self, client, userdata, flags, rc):
        msg = f"\n    {client._client_id} connected\n    status {rc}\n    host={self.host}:{self.port}\n    username={self.username}"
        try:
            if rc:
                raise
            self.client_set_subscriptions()
            self._on_connect_info(msg)
        except Exception as e:
            logger.error(f"\n    _on_connect error {e}")


    def _on_disconnect(self, client, userdata, rc):
        logger.info(f"\n    Disconnected: {client._client_id} with status {rc}")
        try:
            j = 3
            for i in range(j):
                #client.unsubscribe(self.unsubs)
                try:
                    client.reconnect()
                    break
                except Exception as e:
                    if i < j:
                        logger.warn(e)
                        time.sleep(1)
                        continue
                    else:
                        raise
        except Exception as e:
            logger.error(f"\n    _on_disconnect error {e}")


    def _on_stop_mqtt(self):
        pass


    def _on_message_callback(self, topic, payload):
        pass


    def _on_bytes_callback(self, topic, payload):
        pass


    def _on_message(self, client, userdata, message):
        try:
            try:
                payload = json.loads(message.payload.decode("utf-8"))
                self.on_message_callback(message.topic, payload)
            except:
                self.on_bytes_callback(message.topic, message.payload)

        except Exception as e:
            logger.error(f"\n    _on_message error {e}\n    {message.topic} {message.payload[:80]}")


    def connectMQTT(self):
        self.client.connect_async(self.host, self.port, self.keepalive)


    def startMQTT(self):
        self.connectMQTT()
        self.client.loop_forever()


    def stopMQTT(self):
        self._on_stop_mqtt()
        self.client.disconnect()

