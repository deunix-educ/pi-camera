#
import json
import logging
from threading import Thread, Event
from contrib.mqttc import MqttBase
import contrib.utils as utils
from scipy.io.wavfile import write as wav_write

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RECORD_NONE = 0
RECORD_CONTINUOUS = 1

class Topic(utils.TopicBase):
    topickeys = { 'org': 0, 'uuid': 1, 'evt': 2,  'action': 3, 'ts': 3, 'counter': 4, 'lat': 5, 'lon': 6,  }


class AudioReader(MqttBase, Thread):

    def __init__(self, mqtt,  **settings):
        self.conf_file = settings.pop('conf_file', None)
        self.audio = settings.pop('device', None)
        self.settings = settings
        topic_subs = self.args('topic_subs')
        topic_base =  self.args('topic_base')
        uuid = self.args('uuid')
        MqttBase.__init__(self, uuid=uuid, topic_base=topic_base ,topic_subs=topic_subs, **mqtt)
        Thread.__init__(self, daemon=True)
        self.mqtt = self.args('mqtt')
        self.lat = utils.gps_conv(self.args('lat'))
        self.lon = utils.gps_conv(self.args('lon'))        
        self.lon = self.args('lon')
        self.title = self.args('title')
        self.channels = self.args('channels')
        self.rate = self.args('rate')
        self.duration = self.args('duration')
        self.record = self.args('record')

        self.play = True
        self.counter = 0
        self.reader_stop = Event()

    def save_config(self, payload):
        self.record = self.set_args('record', int(payload.get('rec', 0)))
        utils.yaml_save(self.conf_file, self.settings)        

    def save_configuration(self, payload):
        self.channels = self.set_args('channels', int(payload.get('channels', 1)))
        self.rate = self.set_args('rate', int(payload.get('rate',8000 )))        
        self.duration = self.set_args('duration', int(payload.get('duration', 15)))
        self.mqtt = self.set_args('mqtt', int(payload.get('mqtt', 'local')))
        self.save_config(payload)
        #self.record = self.set_args('record', int(payload.get('rec', 0)))
        #return utils.yaml_save(self.conf_file, self.settings)

    def args(self, k):
        return self.settings['audio'].get(k)


    def set_args(self, k, value):
        self.settings['audio'][k] = value
        return value


    def start_services(self):
        self.start()
        self.startMQTT()

    def stop_services(self):
        self.reader_stop.set()
        self.stopMQTT()

    def publish(self, evt, **payload):
        if self.topic_base:
            topic = f'{self.topic_base}/{evt}'
            #logger.info(f"Device publish {topic}")
            self._publish_message(topic, **payload)


    def publish_frame(self, frame):
        # origine/uuid/wav/ts/counter/lat/lon
        if self.topic_base:
            params = f'{self.counter}/{self.lat}/{self.lon}'
            topic = f"{self.topic_base}/wav/{utils.ts_now(m=1000)}/{params}"
            self._publish_bytes(topic, frame)


    def makeReport(self):
        return dict(
            name=self.title,
            sensor=self.args('sensor'),
            vendor=self.args('vendor'),
            model_id=self.args('model_id'),
            description=self.args('description'),
            org=self.args('org'),
            uuid=self.uuid,
            ip=self.args('ip'),
            service=self.args('service'),
            record=self.record > 0,

            options = json.dumps(dict(
                rec = self.record,
                lat=self.args('lat'),
                lon=self.args('lon'),
                channels=self.channels,
                mobile=self.args('mobile'),
                rate=self.rate,
                duration=self.duration,
                state='play' if self.play else 'pause',
                mqtt=self.mqtt,
                )
            ),
        )


    def _on_connect_info(self, info):
        logger.info(f'report: {self.uuid} {info}')
        self.publish('report', retain=True, **self.makeReport())


    def _on_message_callback(self, topic, payload):
        #print('_on_message_callback', topic, payload)
        evt = Topic.arg(topic, 'evt')
        if evt=='set':
            action = Topic.arg(topic, 'action')
            if action == 'pause':
                logger.info(f"Pause {self.uuid}")
                self.play = False
            elif action == 'play':
                logger.info(f"Play {self.uuid}")
                self.play = True
            elif action == 'toggle':
                self.play = False if self.play else True
                logger.info(f"Audio=={self.play} {self.uuid}")                        

            elif action == 'save':
                logger.info(f"Save config {self.uuid}")
                self.save_configuration()
            self.publish('report', retain=True, **self.makeReport())
        elif evt=='rec':
            self.save_config(payload)             

    def frame_capture(self, mic,number_of_frames ):
        data = mic.record(numframes=number_of_frames)
        wav_write('tmp.wav', self.rate, data)
        with open('tmp.wav', 'rb') as f:
            buffer = f.read()
            return buffer


    def run(self):
        try:
            with self.audio.recorder(samplerate=self.rate) as mic:           
                number_of_frames = self.rate * self.duration
                logger.info(f"AudioCapture device {self.title} rate:{self.rate} channels:{self.channels} {number_of_frames} frames")
                
                while not self.reader_stop.is_set():                
                    if self.play:               
                        buffer = self.frame_capture(mic, number_of_frames)                
                        if buffer:
                            self.counter += 1                            
                            self.publish_frame(buffer)
                    else:
                        Event().wait(1)
        except Exception as e:
            logger.error(f"audio reader error {e}")

