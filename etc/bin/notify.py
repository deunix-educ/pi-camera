#!.venv/bin/python
# pip install notify-py
#
from notifypy import Notify

notification = Notify()
notification.title = "Cool Title"
notification.message = "Even cooler message."
notification.icon = "img/sms-logo.png"
notification.audio = "img/incoming-chat.wav"

notification.send(block=True)