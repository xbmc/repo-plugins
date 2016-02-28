#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xbmcswift2 import Plugin,xbmcaddon, xbmc
import urlfetch
from BeautifulSoup import BeautifulSoup
import json
import re
import urllib

plugin = Plugin()

crawurl = 'https://fptplay.net/livetv'

def getLinkById(id = None, quality = "3"):

    #if id.startswith('https://') :
    #    #is event
    #    id = getChannelIdFromEventLink(id)
    #if id == None :
    #    return None


    #get cookie & csrf
    result = urlfetch.fetch(
        crawurl,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })

    #m = re.search(r"name=\"_token\" content=\"(.+)\"",result.content)

    #if m == None :
    #    return None
    #csrf = m.group(1)

    cookie='laravel_session=' + result.cookies.get('laravel_session') + ";"
    csrf = urllib.unquote(result.cookies.get('token'))
    #plugin.log.info(csrf)
    result = urlfetch.post(
        'https://fptplay.net/show/getlinklivetv',
        data={"id": id,
            "quality": quality,
            "mobile": "web",
			"type" : "newchannel"
            },
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
                'X-Requested-With':'XMLHttpRequest',
                'Referer':'https://fptplay.net/livetv',
                'x-csrf-token': csrf,
                'cookie':cookie
                }
        )
    plugin.log.info(result.content)
    if result.status_code != 200 :
        return None

    info = json.loads(result.content)

    return info['stream']

def getLink(uri = None, quality = "3"):

    #get cookie & csrf
    result = urlfetch.fetch(
        uri,
        headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'
            })

    #m = re.search(r"name=\"_token\" content=\"(.+)\"",result.content)

    #if m == None :
    #    return None
    #csrf = m.group(1)

    m = re.search(r"var id = '([^']+)';",result.content)
    if m == None :
        return None
    id = m.group(1)
    
    cookie='laravel_session=' + result.cookies.get('laravel_session') + ";"
    csrf = urllib.unquote(result.cookies.get('token'))
    
    result = urlfetch.post(
        'https://fptplay.net/show/getlinklivetv',
        data={"id": id,
            "quality": quality,
            "mobile": "web",
			"type" : "newchannel"
            },
        headers={'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36',
                'X-Requested-With':'XMLHttpRequest',
                'Referer':'https://fptplay.net/livetv',
                'x-csrf-token': csrf,
                'cookie':cookie
                }
        )

    if result.status_code != 200 :
        return None

    info = json.loads(result.content)

    return info['stream']

