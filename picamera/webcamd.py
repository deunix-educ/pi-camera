#!../.venv/bin/python
# encoding: utf-8
#
# DD
import logging, argparse
from contrib.video_capture import VideoReader
from contrib.utils import yaml_load, gen_device_uuid, yaml_save


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_mqtt_configuration(mqtt_type='local'):
    settings = yaml_load('mqtt.yaml')
    return  settings[mqtt_type]


def load_configuration(conf_file):
    settings = yaml_load(conf_file)
    if not settings['camera']['uuid']:
        uuid = f'0x{gen_device_uuid()}'
        org = settings['camera']['org']
        settings['camera']['uuid'] = uuid
        settings['camera']['topic_base'] = f"{org}/{uuid}"
        settings['camera']['topic_subs']= [ [f"{org}/{uuid}/#", 0], ]
        yaml_save(conf_file, settings)
    return dict(conf_file=conf_file, **settings)


def main(conf_file):
    daemon = None
    try:
        config = load_configuration(conf_file)
        mqtt_type = config['camera'].get('mqtt')
        mqtt = load_mqtt_configuration(mqtt_type)
        daemon = VideoReader(mqtt, **config)
        daemon.start_services()
    except Exception as e:
        print(f'\nwebcamd error {e}')
    finally:
        if daemon:
            daemon.stop_services()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Webcam device")
    parser.add_argument("--config", default='config.yaml', help="Config yaml file path", required=False)
    #parser.add_argument("--mqtt", default='local', help="local, public or vpn", required=False)
    args = parser.parse_args()
    if args.config:
        main(args.config)


