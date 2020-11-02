# _*_ coding: utf-8 _*_
import json
import urllib.request as request
from xml.etree import ElementTree as ET

stream_url = 'https://pureradio.one/stream'
podcast_url = 'https://pureradio.one/spreaker'

# functions with web interface
def retrieve_streamurl():
    """ This function return the stream url """
    return json.loads(request.urlopen(stream_url).read().decode('utf-8'))

def retrieve_podcasturl():
    """ This function return the podcast url """
    return json.loads(request.urlopen(podcast_url).read().decode('utf-8'))

def retrieve_podcasts(url):
    """ This function return a dictonary of podcast items """
    return ET.fromstring(request.urlopen(url=url, timeout=20).read().decode('utf-8'))
