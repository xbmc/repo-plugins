import urllib
import urllib2
import httplib
import re
import os
from traceback import print_exc
from urlparse import urlparse, parse_qs

from BeautifulSoup import BeautifulSoup
from pyamf import remoting

import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_icon = addon.getAddonInfo('icon')
fanart = addon.getAddonInfo('fanart')
addon_version = addon.getAddonInfo('version')
debug = addon.getSetting('debug')
base_url ='http://www.nascar.com'


def addon_log(string):
    if debug == 'true':
        try:
            log_message = string.encode('utf-8', 'ignore')
        except:
            log_message = 'addonException: addon_log: %s' %format_exc()
        xbmc.log("[%s-%s]: %s" %(addon_id, addon_version, log_message), level=xbmc.LOGNOTICE)


def make_request(url):
    try:
        headers = {
            'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20100101 Firefox/31.0',
            'Referer' : base_url + '/en_us/sprint-cup-series/news-media.sprint-cup-series.videos.html'
            }
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        if response.geturl() != url:
            addon_log('Redirect URL: %s' %response.geturl())
        data = response.read()
        response.close()
    except urllib2.URLError, e:
        addon_log(('We failed to open "%s".' % url))
        if hasattr(e, 'reason'):
            addon_log(('We failed to reach a server.'))
            addon_log(('Reason: %s' %e.reason))
        if hasattr(e, 'code'):
            addon_log(('We failed with error code - %s.' %e.code))
        data = None
    return data


def get_video_items(url):
    data = make_request(url)
    if data:
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        for i in soup('article'):
            title = i.a['title']
            u=sys.argv[0]+'?mode=resolve_url&url='+urllib.quote_plus(base_url + i('p')[1].a['href'])
            liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage = i.img['data-original'])
            liz.setInfo(type="Video", infoLabels={"Title": title, "Plot": i.p.string})
            liz.setProperty('IsPlayable', 'true')
            liz.setProperty("Fanart_Image", fanart)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
        load_more = soup.find('a', attrs={'class': 'loadMore'})
        if load_more:
            u=sys.argv[0]+'?mode=page&url='+urllib.quote_plus('http://www.nascar.com'+load_more['data-href'])
            liz=xbmcgui.ListItem('Load More', iconImage="DefaultVideo.png", thumbnailImage=addon_icon)
            liz.setProperty("Fanart_Image", fanart)
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
                

def get_video_id(url):
    soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
    video_id = soup.find('img', attrs={'class': 'mediaThumb'})['data-ajax-post-data'].lstrip('mediavideoid=')
    return video_id


def resolve_url(item_url):
        ## Credit to AddonScriptorDE for the bc code
        ## https://github.com/AddonScriptorDE/plugin.video.redbull_tv
        quality = int(addon.getSetting('quality'))
        bc_playerID = 2033674580001
        bc_publisherID = 1677257476001
        bc_const = 'efa14670a843335eedd6c1e1acc8b2c4c4e342db'
        conn = httplib.HTTPConnection("c.brightcove.com")
        envelope = remoting.Envelope(amfVersion=3)
        envelope.bodies.append(("/1", remoting.Request(
            target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById",
            body=[bc_const, bc_playerID, get_video_id(item_url), bc_publisherID],
            envelope=envelope)))
        conn.request("POST", "/services/messagebroker/amf?playerId=" + str(bc_playerID),
                     str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
        response = conn.getresponse().read()
        response = remoting.decode(response).bodies[0][1].body
        renditions = sorted(response['renditions'], key=lambda k: int(k['encodingRate']), reverse=True)
        q_type = None
        for i in range(len(renditions)):
            if quality > 0:
                try:
                    ok = renditions[quality]['defaultURL']
                    if ok:
                        q_type = quality
                    else: raise
                except:
                    quality = (quality -1)
                    addon_log('quality not avaliable')
                if q_type:
                    break
            else:
                q_type = quality
                break
        path = renditions[q_type]['defaultURL'].split('&')[0]
        path += ' playpath=%s' %renditions[q_type]['defaultURL'].split('&')[1]
        item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)



def get_params():
    p = parse_qs(sys.argv[2][1:])
    for i in p.keys():
        p[i] = p[i][0]
    return p


params=get_params()

url=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    mode=urllib.unquote_plus(params["mode"])
except:
    pass

addon_log('Mode: %s, URL: %s' %(mode, url))

if mode==None:
    if addon.getSetting('series') == '0':
        videos_url = '/en_us/sprint-cup-series/news-media/jcr:content/mediaList.loadMore.sprint-cup-series.videos.0.html'
    elif addon.getSetting('series') == '1':
        videos_url = '/en_us/nationwide-series/news-media/jcr:content/mediaList.loadMore.nationwide-series.videos.0.html'
    elif addon.getSetting('series') == '2':
        videos_url = '/en_us/camping-world-truck-series/news-media/jcr:content/mediaList.loadMore.camping-world-truck-series.videos.1.html'
    get_video_items(base_url + videos_url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

elif mode=="resolve_url":
    resolve_url(url)

elif mode=="page":
    get_video_items(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
