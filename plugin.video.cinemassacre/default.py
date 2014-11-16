# Copyright 2014 cdwertmann

import sys
import xbmcgui
import xbmcplugin
import urllib
import urllib2
import urlparse
import hmac
import hashlib
import base64
import os
import binascii
import time
import xmltodict
from datetime import datetime, date
from types import *

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
PLUGIN_NAME = "plugin.video.cinemassacre"

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

# cache for one hour
cache = StorageServer.StorageServer(PLUGIN_NAME, 1)

def video_id(value):
    """
    Examples:
    - http://youtu.be/SA2iWivDJiE
    - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    - http://www.youtube.com/embed/SA2iWivDJiE
    - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    """
    query = urlparse.urlparse(value)
    if query.hostname == 'youtu.be':
        return query.path[1:]
    if query.hostname in ('www.youtube.com', 'youtube.com'):
        if query.path == '/watch':
            p = urlparse.parse_qs(query.query)
            return p['v'][0]
        if query.path[:7] == '/embed/':
            return query.path.split('/')[2]
        if query.path[:3] == '/v/':
            return query.path.split('/')[2]
    # fail?
    return None

def get_signature(key, msg):
    return base64.b64encode(hmac.new(key, msg, hashlib.sha1).digest())

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def log(msg):
    xbmc.log(PLUGIN_NAME + ": "+ str(msg), level=xbmc.LOGNOTICE)

def getContent():
    devicetoken=binascii.b2a_hex(os.urandom(32))
    deviceuid=binascii.b2a_hex(os.urandom(20)).upper()
    signature=get_signature(os.urandom(20),os.urandom(20))
    timestamp=datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    URL="http://cinemassacre.screenwavemedia.com/AppServer/SWMAppFeed.php?appname=Cinemassacre&appversion=1.5.8&devicetoken="+devicetoken+"&deviceuid="+deviceuid+"&lastupdateid=0&timestamp="+timestamp+"&signature="+signature
    log(URL)
    req = urllib2.Request(URL)
    response = urllib2.urlopen(req)
    xml=response.read()
    response.close()
    return xmltodict.parse(xml)['document']

def getCategories(content,id):
    items = []
    if id=="":
        listitem=xbmcgui.ListItem("- All videos sorted by date -", iconImage="DefaultFolder.png")
        url = build_url({'id': "all"})
        items.append((url, listitem, True))

    if id=="all":
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_DATE)
    else:
        xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_LABEL)

    for cat in content['MainCategory']:
        if cat['@parent_id'] == id:
            #if cat['@activeInd'] == "N": continue
            listitem=xbmcgui.ListItem(cat['@name'], iconImage="DefaultFolder.png")
            url = build_url({'id': cat['@id']})
            items.append((url, listitem, True))
    
    if id!="" or id=="all":
        count=0
        for clip in content['item']:
            if clip['movieURL']=="" or clip['@activeInd'] == "N": continue
            cat_tag=clip['categories']['category']
            cat=None
            if type(cat_tag)==DictType:
                if cat_tag['@id']==id: cat=[cat_tag['@id']]
            elif type(cat_tag)==ListType:
                for c in cat_tag:
                    if c['@id']==id: cat=c['@id']

            if not cat and id!="all": continue
            url = clip['movieURL']
            if not "http" in url:
                url = "http://video1.screenwavemedia.com/Cinemassacre/smil:"+url+".smil/playlist.m3u8"
            elif "youtube.com" in url:
                url = "plugin://plugin.video.youtube/?action=play_video&videoid="+video_id(url)
            date=None
            airdate=None
            if clip['pubDate']:
                # python bug http://stackoverflow.com/questions/2609259/converting-string-to-datetime-object-in-python
                d=clip['pubDate'][:-6]
                # python bug http://forum.xbmc.org/showthread.php?tid=112916
                try:
                    d=datetime.strptime(d, '%a, %d %b %Y %H:%M:%S')
                except TypeError:
                    d=datetime(*(time.strptime(d, '%a, %d %b %Y %H:%M:%S')[0:6]))

                date=d.strftime('%d.%m.%Y')
                airdate=d.strftime('%Y-%m-%d')
            count+=1
            listitem=xbmcgui.ListItem (clip['title'], thumbnailImage=clip['smallThumbnail'], iconImage='DefaultVideo.png')
            listitem.setInfo( type="Video", infoLabels={ "title": clip['title'], "plot": clip['description'], "aired": airdate, "date": date, "count": count})
            listitem.setProperty('IsPlayable', 'true')
            listitem.addStreamInfo('video', {'duration': clip['duration']})
            items.append((url, listitem, False))

    xbmcplugin.addDirectoryItems(addon_handle,items)


xbmcplugin.setContent(addon_handle, "episodes")
id = ''.join(args.get('id', ""))
content = cache.cacheFunction(getContent)
getCategories(content, id)

xbmcplugin.endOfDirectory(addon_handle)
# Media Info View
xbmc.executebuiltin('Container.SetViewMode(504)')
