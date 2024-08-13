#!../.venv/bin/python
# encoding: utf-8
#
# DD
import logging, argparse
#import pyaudio
import soundcard as sc
from contrib.audio_capture import AudioReader
from contrib.utils import yaml_load, gen_device_uuid, yaml_save


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_mqtt_configuration(mqtt_type='local'):
    settings = yaml_load('mqtt.yaml')
    return  settings[mqtt_type]


def load_configuration(conf_file):
    settings = yaml_load(conf_file)

    if not settings['audio']['uuid']:
        default_mic = sc.default_microphone()
        settings['audio']['title'] = default_mic.name
        settings['audio']['channels'] = default_mic.channels
        uuid = f'0x{gen_device_uuid()}'
        org = settings['audio']['org']
        settings['audio']['uuid'] = uuid
        settings['audio']['topic_base'] = f"{org}/{uuid}"
        settings['audio']['topic_subs']= [ [f"{org}/{uuid}/#", 0], ]
        settings['audio']['duration'] = 10
        settings['audio']['rate'] = 44100
        settings['audio']['record'] = 0
        yaml_save(conf_file, settings)

    name = settings['audio']['title']
    audio = sc.get_microphone(name)
    return dict(device=audio, conf_file=conf_file, **settings)
    

def main(conf_file, mqtt_type):
    daemon = None
    try:
        mqtt = load_mqtt_configuration(mqtt_type)
        config = load_configuration(conf_file)
        
        daemon = AudioReader(mqtt, **config)
        daemon.start_services()

    except Exception as e:
        print(f'\n    audiocamd error {e}')
    finally:
        if daemon:
            daemon.stop_services()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Webcam device")
    parser.add_argument("--config", default='config.yaml', help="Config yaml file path", required=False)
    parser.add_argument("--mqtt", default='local', help="local or vpn", required=False)
    args = parser.parse_args()
    if args.config and args.mqtt:
        main(args.config, args.mqtt)

