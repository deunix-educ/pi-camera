#
import json
import time, logging
import cv2, imutils
from threading import Thread, Event
from contrib.mqttc import MqttBase
import contrib.utils as utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RECORD_NONE = 0
RECORD_CONTINUOUS = 1
RECORD_MOTION_DETECTION = 2


class Topic(utils.TopicBase):
    topickeys = {'org': 0, 'uuid': 1, 'evt': 2, 'action': 3, 'ts': 3, 'counter': 4, 'lat': 5, 'lon': 6, 'fps': 7,  }


class VideoReader(MqttBase, Thread):

    def __init__(self, mqtt_settings, **settings):
        self.conf_file = settings.pop('conf_file', None)
        self.settings = settings
        topic_subs = self.args('topic_subs')
        topic_base =  self.args('topic_base')
        uuid = self.args('uuid')
        MqttBase.__init__(self, uuid=uuid, topic_base=topic_base ,topic_subs=topic_subs, **mqtt_settings)
        Thread.__init__(self, daemon=True)
        # options
        self.camid = self.args('camid')
        self.area = self.args('area')
        self.lat = self.args('lat')
        self.lon = self.args('lon')
        self.rotate = self.args('rotate')
        self.zoom = self.args('zoom')
        self.fps = self.args('fps')
        self.record = self.args('record')
        self.contour = self.args('contour')
        
        self.size = self.args('size')
        self.width, self.height = utils.dimensions(self.size)
        self.capture = None
        
        self.play = True
        self.counter = 0
        self.sleeping = False
        self.reader_stop = Event()
        
        
    def get_state(self, state):
        return 'play' if state else 'pause'
    
    
    def save_config(self, payload):
        self.record = self.set_args('record', int(payload.get('record', 0)))
        utils.yaml_save(self.conf_file, self.settings)
        logger.info(f"Save config record: {self.record}")
  
              
    def save_configuration(self, payload):
        try:     
            self.rotate = self.set_args('rotate', int(payload.get('rot', 0)))
            self.fps = self.set_args('fps', int(payload.get('fps', 5)))
            self.record = self.set_args('record', int(payload.get('record', 0)))
            self.zoom = self.set_args('zoom', float(payload.get('zoom', 1.0)))
            self.contour = self.set_args('contour', int(payload.get('cnt', 0)))
            self.save_config(payload)
        except Exception as e:
            logger.error(f"{e}")


    def args(self, k):
        return self.settings['camera'].get(k)


    def set_args(self, k, value):
        self.settings['camera'][k] = value
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
            #logger.info(f"Device publish: {topic}::{payload}")
            self._publish_message(topic, **payload)


    def publish_frame(self, frame):
        if self.topic_base and frame:
            topic = f"{self.topic_base}/jpg/{utils.ts_now(m=1000)}/{self.counter}/{self.lat}/{self.lon}/{self.fps}"
            #logger.info(f"Device publish frame: {topic}")
            self._publish_bytes(topic, frame)


    def makeReport(self):
        return dict(
            name=self.args('title'),
            sensor=self.args('sensor'),
            vendor=self.args('vendor'),
            model_id=self.args('model_id'),
            description=self.args('description'),
            org=self.args('org'),
            uuid=self.uuid,
            ip=self.args('ip'),
            service=self.args('service'),
            record=self.record,         
            options = json.dumps(dict(
                lat=self.lat,
                lon=self.lon,
                rot=int(self.rotate),
                zoom=self.zoom,
                fps=self.fps,
                mobile=self.args('mobile'),
                cnt=self.contour,
                state=self.get_state(self.play),
                sleeping=self.sleeping,
                )
            ),
        )


    def is_page_alive(self, timeout=5.0):
        Event().wait(timeout)
        if (self.pong_time-self.ping_time) < 0:
            if not self.record:
                self.play = False
                logger.info(f'Web page is not alive for {self.uuid}')
                self.sleeping = True
                self.publish('report', retain=True, **self.makeReport())


    def _on_log(self, mqttc, obj, level, string):
        if string.endswith('PINGRESP'):
            #logger.info(f'on_log: {self.uuid} {string}')
            self.pong_time, self.ping_time = 0, utils.ts_now(m=1000)
            self.publish('ping', ts=self.ping_time, **self.makeReport())            
            timer = Thread(target=self.is_page_alive, args=(5.0, ))
            timer.start()
            

    def _on_connect_info(self, info):
        logger.info(f'report: {self.uuid} {info}')
        self.sleeping = False
        self.publish('report', retain=True, **self.makeReport())


    def _on_message_callback(self, topic, payload):
        #print('_on_message_callback', topic, payload)
        evt = Topic.arg(topic, 'evt')
        if evt=='set':
            action = Topic.arg(topic, 'action')
            if action:
                if action == 'pause':
                    logger.info(f"Pause video {self.uuid}")
                    self.play = False
                elif action == 'play':
                    logger.info(f"Play video {self.uuid}")
                    self.play = True
                elif action == 'toggle':
                    self.play = False if self.play else True
                    logger.info(f"Video=={self.play} {self.uuid}")     
                elif action == 'save':
                    self.save_configuration(payload)
                    logger.info(f"Save config {self.uuid}: {payload}")
                self.sleeping = False
                self.publish('report', retain=True, **self.makeReport())
        elif evt=='rec':
            self.save_config(payload)
            self.sleeping = False
            self.publish('report', retain=True, **self.makeReport())
        elif evt=='pong':
            self.pong_time = payload.get('ts')


    def millis(self):
        return round(time.time() * 1000)


    def wait_for_frame(self, begin_t):
        duration = float((self.millis() - begin_t)/1000)
        sleep = 1/self.fps - duration
        if sleep > 0:
            Event().wait(sleep)


    def video_capture(self):
        self.capture = cv2.VideoCapture(self.camid)
        if self.capture.isOpened():
            #video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            #video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            return True
        return False


    def motion_detection(self, frame):
        self.detected = True
        if self.record==RECORD_MOTION_DETECTION:
            self.detected = False
            gray = imutils.resize(frame, width=500)
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if self.first_frame is None:
                self.first_frame = gray
                return None

            delta_frame = cv2.absdiff(self.first_frame, gray)
            threshold = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)[1]
            threshold = cv2.dilate(threshold, None, iterations=3)
            contours, _ = cv2.findContours(threshold.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                if cv2.contourArea(contour) < self.area:
                    continue           
                if not self.detected:
                    self.detected = True     
                    cv2.circle(frame, center=(20,20), radius=10, color=(0, 140, 255), thickness=7, lineType=8, shift=0)
                    
                if self.contour:
                    (x, y, w, h) = cv2.boundingRect(contour)         
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
        return frame


    def _get_jpg_frame(self, frame):
        (h, w, _) = frame.shape        
        r = float(self.zoom)
        frame = cv2.resize(frame, (int(w*r), int(h*r)) )
        if self.rotate != 0:
            frame = imutils.rotate(frame, angle=self.rotate)
        
        success, jpgframe = cv2.imencode('.jpg', frame)
        if success:
            jpgframe = jpgframe.tobytes()
            return jpgframe
        return None


    def publish_jpg_frame(self, frame):
        jpgframe = self._get_jpg_frame(frame)
        if jpgframe:
            self.publish_frame(jpgframe)
        return jpgframe

 
    def get_first_image(self):
        while not self.reader_stop.is_set():
            success, frame = self.capture.read()
            if success: 
                return self.publish_jpg_frame(frame) 
        return None
 
 
    def run(self):
        try:
            if not self.video_capture():
                raise Exception(f'VideoCapture device {self.camid} failed')
            logger.info(f"VideoCapture device {self.camid}")
            self.first_frame = None
            self.detected = False
            jpgframe = self.get_first_image()
            while not self.reader_stop.is_set():
                if self.play:
                    begin_t = self.millis()
                    success, frame_base = self.capture.read()
                    if success:  
                        frame = self.motion_detection(frame_base)
                        if frame is None:
                            continue

                        if self.detected:
                            frame_base = frame
                            self.counter += 1
                            self.first_frame = None
                            jpgframe = self.publish_jpg_frame(frame_base)
                    self.wait_for_frame(begin_t)
                else:
                    self.publish_frame(jpgframe)
                    Event().wait(1)

        except Exception as e:
            logger.error(f"video reader error {e}")
        finally:
            self.capture.release()   

