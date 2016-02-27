#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin,xbmcaddon, xbmc
import urlfetch
from BeautifulSoup import BeautifulSoup
import json
import re

plugin = Plugin()

def getLink(uri):

    m = re.search(r'\/([^\/]+)\.html$',uri)

    if m == None :
        return None
    zid = m.group(1)

    uri_check = 'http://luanxt.tk/Demo/mp3-tv.php?ZID=' + zid

    #get cookie & csrf
    result = urlfetch.fetch(
        uri_check,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })

    info = json.loads(result.content)

    link = 'http://' + info['response']['other_url']['Video720']

    return link
