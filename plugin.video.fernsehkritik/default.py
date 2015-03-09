# -*- coding: utf-8 -*-

import sys
import xbmcgui
import xbmcplugin
import urllib
import urllib2
import urlparse
import xmltodict
import re
from bs4 import BeautifulSoup

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
PLUGIN_NAME = "plugin.video.fernsehkritik"
opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

# cache for one hour
cache = StorageServer.StorageServer(PLUGIN_NAME, 1)
# disable cache for testing
#cache.delete("%")

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def log(msg):
    xbmc.log(PLUGIN_NAME + ": "+ msg.decode('ascii', 'ignore'), level=xbmc.LOGNOTICE)

def getLatestEp():
    response = opener.open("http://fernsehkritik.tv/feed")
    html=response.read()
    response.close()
    d=xmltodict.parse(html)
    return re.findall(r'\d+',d['rss']['channel']['item'][0]['link'])[0]

latest_ep=int(cache.cacheFunction(getLatestEp))

def getEpDetails(ep):
    for attempt in range(3):
        try:
            response = opener.open("http://fernsehkritik.tv/folge-"+str(ep)+"/play")
            html=response.read()
            response.close()
            soup = BeautifulSoup(html)        
            url = soup.find_all('source')[0]['src'] or ""
            title = soup.find('h3').contents[0] or ""
            return url, title
        except Exception as e:
            log("retry fetching episode "+str(ep))
            continue

    if (ep==latest_ep):
        return "","neueste Folge momentan nur im Abo"
    else:
        return "","Fehler beim Laden der Folge"

def addItems(start):
    if (start>latest_ep):
        start=latest_ep
    end = start-10
    if (end<0):
        end=0

    for ep in reversed(range(end+1,start+1)):
        url, title = cache.cacheFunction(getEpDetails, ep)
        listitem=xbmcgui.ListItem (title, iconImage='http://fernsehkritik.tv/images/magazin/folge'+str(ep)+'.jpg')
        listitem.setInfo( type="Video", infoLabels={ "title": title })
        #listitem.setProperty('IsPlayable', 'true')
        #listitem.addStreamInfo('video', {'duration': clip['duration']})
        xbmcplugin.addDirectoryItem(addon_handle, url, listitem,totalItems=start-end)

    if (end > 0):
        listitem=xbmcgui.ListItem("Weiter...")
        url = build_url({'id': start-10})
        xbmcplugin.addDirectoryItem(addon_handle, url, listitem, True)

xbmcplugin.setContent(addon_handle, "episodes")
id = ''.join(args.get('id', ""))
if id=="":
    addItems(latest_ep)
else:
    addItems(int(id))

xbmcplugin.endOfDirectory(addon_handle)
# Media Info View
xbmc.executebuiltin('Container.SetViewMode(504)')
