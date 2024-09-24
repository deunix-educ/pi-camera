# pi-camera
mqtt device for webcam and django-automation


#### Installation
Clone or download the code from https://github.com/deunix-educ/pi-camera

        git clone git@github.com:deunix-educ/pi-camera.git
        or
        tar xzfv pi-camera-main.zip
        mv pi-camera-main pi-camera 
        cd pi-camera

- In etc directory we find:

    - bin: some utilities
    - conf: example configuration for a pi
    - install: example system installation for a pi
    
- Install the following packages:

        sudo apt update
        sudo apt -y install build-essential git supervisor
        sudo apt -y python3-dev python3-pip python3-venv
        sudo cp /etc/supervisor/supervisord.conf /etc/supervisor/supervisord.conf.old
        sudo cat >> /etc/supervisor/supervisord.conf << EOF
        [inet_http_server]
        port=*:9001
        username=root
        password=toor
        EOF

- Change the rights of the following files

        chmod +x picamera/*.py
        chmod +x etc/bin/*.sh

- Install the python virtual environment (in .venv)

        etc/bin/venv-install etc/install/requirements.txt

- Finally install the service supervisor configuration file

        sudo cp etc/conf/camera_service.conf /etc/supervisor/conf.d/
        sudo supervisorctl reread && sudo supervisorctl update

#### How it works

        cd camera

- Modify and copy config_example.yaml and mqtt_example.yaml

        cp config_example.yaml config.yaml
        cp mqtt_example.yaml mqtt.yaml
        ./webcamd.py
        or
        ./audiocamd.py