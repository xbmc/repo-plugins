# _*_ coding: utf-8 _*_

import urllib.request as request
from xml.etree import ElementTree as ET

# functions with web interface
def retrieve_streamurl():
    return """http://pureradio.one:8000/"""

def retrieve_podcasturl():
    return """http://www.spreaker.com/show/1757189/episodes/feed"""

def retrieve_podcasts(url):
    return ET.fromstring(request.urlopen(url=url, timeout=20).read().decode('utf-8'))
