# Copyright 2014 cdwertmann

import urllib2
import xmltodict
import os,binascii
from datetime import datetime, date, time

import hmac
import hashlib
import base64

def get_signature(key, msg):
    return base64.b64encode(hmac.new(key, msg, hashlib.sha1).digest())

devicetoken=binascii.b2a_hex(os.urandom(32))
deviceuid=binascii.b2a_hex(os.urandom(20)).upper()
signature=get_signature(os.urandom(20),os.urandom(20))
timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")

URL="http://cinemassacre.screenwavemedia.com/AppServer/SWMAppFeed.php?appname=Cinemassacre&appversion=1.5.8&devicetoken="+devicetoken+"&deviceuid="+deviceuid+"&lastupdateid=0&timestamp="+timestamp+"&signature="+signature

print URL

def getContent():
    req = urllib2.Request(URL)
    response = urllib2.urlopen(req)
    xml=response.read()
    response.close()
    return xml

# f = open('test.xml', 'r')
# xml = f.read

d = xmltodict.parse(getContent())['document']

for cat in d['MainCategory']:
    if cat['@parent_id']:
        print cat['@name']

