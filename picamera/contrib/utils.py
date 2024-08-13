'''
Created on 20 avr. 2022

@author: denis
'''
import json, yaml
import importlib
from datetime import datetime
from decimal import Decimal
import string, secrets
import uuid, socket


class TopicBase:
    topickeys = {}
    
    def __init__(self, topics):
        self.topics = topics.split('/') or []

    def get(self, k):
        try:
            return self.topics[self.topickeys.get(k)]
        except:
            pass
        return None
    
    @classmethod
    def arg(cls, topic, k):
        topics = topic.split('/') or []
        return topics[cls.topickeys.get(k)]



def yaml_load(f):
    with open(f, 'r') as stream:
        return yaml.safe_load(stream)
    return {}


def yaml_save(f, context):
    with open(f, 'w') as stream:
        yaml.dump(context, stream, default_flow_style = False)



def bitread(b, bitpos):
    return (b>>bitpos) & 0x1


def get_fqdn():
    return socket.getfqdn()


def get_uuid():
    return str(hex(uuid.getnode()))[2:]


def ts_now(m=1):
    now = datetime.now().timestamp()*m
    return int(now)


def random_num(n=16):
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for i in range(n))  # @UnusedVariable

def random_chars(n=6):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(n))  # @UnusedVariable


def get_apikey(n=32):
    chars = 'abcdefgh01234ijklABCD4567EFGHIJKLmnopqrstuvwxyz0123456789MNOPQRS789TUVWXYZ'
    return ''.join(secrets.choice(chars) for i in range(n))  # @UnusedVariable


def str_to_float(n, default='NaN'):
    try:
        return float(str(n).strip().replace(',', '.'))
    except:
        return default

def str_to_int(n, default='NaN'):
    try:
        return int(str(n).strip())
    except:
        return default

def gps_conv(s, n=1000000, default='NaN'):
    try:
        return str( int(Decimal(s)*n) )
    except:
        return default


def conv_gps(v, default=None):
    try:
        if v == 'NaN':
            raise
        return float(Decimal(v)/1000000)
    except:
        return default


def js_serialize_array_to_dict(jsarray):
    d = {}
    for f in json.loads(jsarray):
        name = f.get('name')
        value = f.get('value')
        if name:
            d[name] = value
    return d


def get_instance_class(module):
    modulename, classname = module.rsplit(".", 1)
    return getattr(importlib.import_module(modulename), classname)


def gen_keywords(s):
    c = s.replace(',', ' ').replace('+', ' ')
    return [ w.strip() for w in c.split(' ') if w]


def gen_device_uuid(n=19):
    return hex(int(random_num(n)))[2:]

def get_device_uuid(n=19):
    return f'0x{gen_device_uuid(n)}'

def dimensions(s):
    w, h = s.split('x')
    return int(w), int(h)


def dim_to_size(w, h):
    return f'{w}x{h}'

