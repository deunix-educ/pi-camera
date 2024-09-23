#!/bin/bash
echo
echo "--- Installation des fichiers de configuration"
echo

BASE=$(pwd)

if [ $EUID -ne 0 ]; then
  echo "Lancer en root: # $0" 1>&2
  exit 1
fi

apt update
#apt upgrade

apt install supervisor v4l-utils python3-pip python3.11-venv python3-dev 

# rpi4 rpi3 venv
# apt install libopenjp2-7 libavcodec-dev libavformat-dev libswscale-dev liblapack-dev libgtk-3-dev libatlas-base-dev

# rpi, orangepi, eeepc:i386
#apt install supervisor python3-pip python3.11-venv python3-opencv python3-paho-mqtt python3-yaml v4l-utils python3-scipy
#pip3 install imutils --break-system-packages


# supervisor http access
if [ ! -e "/etc/supervisor/supervisord.conf.old" ]; then
cp /etc/supervisor/supervisord.conf /etc/supervisor/supervisord.conf.old

cat >> /etc/supervisor/supervisord.conf << EOF
[inet_http_server]
port=*:9001
username=root
password=toor
EOF
fi

echo
echo "--- Fin d'installation "
echo
