# _*_ coding: utf-8 _*_
import json
import urllib.request as request
from xml.etree import ElementTree as ET

def retrieve_podcasts(url):
    """ This function return a dictonary of podcast items """
    return ET.fromstring(request.urlopen(url=url, timeout=20).read().decode('utf-8'))
