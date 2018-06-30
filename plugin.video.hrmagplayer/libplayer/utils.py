#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
from libplayer.http import HttpRetriever

def extractParameters(actions):
    ret = None
    if actions != '':
        actions = actions[1:]
        actionStrs = actions.split('&')
        for action in actionStrs:
            pair = action.split('=')
            if len(pair) > 1:
                if ret == None:
                    ret = dict() 
                ret[pair[0]] = pair[1]
    return ret

def getVideoLink(url):
    http = HttpRetriever()
    page = http.get(url)
    video = None
    
    # HR3 video
    ix = page.find('type="video/mp4')
    if ix != -1:
        ix = page.find('src="', ix)
        if ix != -1:
            ex = page.find('"', ix + 5)
            video = page[ix+5:ex]
    # Check for WDR video
    ix = page.find('//wdrmedien')   
    if ix != -1:
        ex = page.find(chr(34), ix)
        if ex != -1:
            video = 'https:' + page[ix:ex]
          
    return video

def getShowId(context, index):
    return context['showList'][index]['id']

def getShowIndex(context, id):
    shows = len(context['showList'])
    for show in range(0, shows):
        if context['showList'][show]['id'] == id:
            return show
    return -1

def encode(string):
    return urllib.quote_plus(string)
    
def decode(string):
    return urllib.unquote_plus(string)

def isDebug(context):
    if 'debug' in context:
        return context['debug']
    else:
        return False

