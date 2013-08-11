import urllib
import urllib2
import httplib
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup
from pyamf import remoting
from traceback import print_exc

addon = xbmcaddon.Addon(id='plugin.video.nascar')
home = xbmc.translatePath(addon.getAddonInfo('path'))
icon = os.path.join(home, 'icon.png')
fanart = os.path.join(home, 'fanart.jpg')
addon_version = addon.getAddonInfo('version')
debug = addon.getSetting('debug')


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.nascar-%s]: %s" %(addon_version, string))


def make_request(url):
        try:
            headers = {
                'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:19.0) Gecko/20100101 Firefox/19.0',
                'Referer' : 'http://www.nascar.com/en_us/sprint-cup-series.html'
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


def get_video_items(url, featured=False):
        data = make_request(url)
        if data:
            soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
            if featured:
                items = soup.find('div', attrs={'class': "featuredVideos"})('article')
            else:
                items = soup.find('div', attrs={'class': "articlesList"})('article')
            addon_log('video_items: %s' %len(items))
            for i in items:
                if featured:
                    title = i('a')[1].string
                    item_id = i.img['data-ajax-post-data'].split('&')[0].split('=')[1]
                    thumb = i.img['data-resp-url']
                else:
                    title = i.img['alt']
                    item_id = i.span['data-ajax-post-data'].split('=')[1]
                    thumb = i.img['data-original']
                u=sys.argv[0]+'?mode=resolve_url&url='+urllib.quote_plus(item_id)
                liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=thumb)
                liz.setInfo(type="Video", infoLabels={"Title": title})
                liz.setProperty('IsPlayable', 'true')
                liz.setProperty("Fanart_Image", fanart)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=False)
            load_more = soup.find('a', attrs={'title': 'LOAD MORE'})
            if load_more:
                u=sys.argv[0]+'?mode=page&url='+urllib.quote_plus('http://www.nascar.com'+load_more['data-href'])
                liz=xbmcgui.ListItem('Load More', iconImage="DefaultVideo.png", thumbnailImage=icon)
                liz.setProperty("Fanart_Image", fanart)
                xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)


def resolve_url(item_id):
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
            body=[bc_const, bc_playerID, item_id, bc_publisherID],
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
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]
        return param


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

addon_log('URL: %s' %url)
addon_log('Mode: %s' %mode)

if mode==None:
    sort = {
        'series': ['', 'sprint-cup-series/', 'nationwide-series/', 'camping-world-truck-series/'],
        'time': ['365', '30', '7' ,'1'],
        'sort': ['recent', 'popular']
        }
    videos_url = (
        'http://www.nascar.com/en_us/%snews-media.all.0.videos.all.all.%s.%s.all.html'
        %(sort['series'][int(addon.getSetting('series'))],
        sort['time'][int(addon.getSetting('time'))],
        sort['sort'][int(addon.getSetting('sort'))])
        )
    if addon.getSetting('series') == '0':
        base_url = 'http://www.nascar.com/en_us/sprint-cup-series.html'
    else:
        base_url = (
            'http://www.nascar.com/en_us/%s.html'
            %sort['series'][int(addon.getSetting('series'))][:-1]
            )
    addon_log('base_url: '+base_url)
    addon_log('videos_url: '+videos_url)
    if addon.getSetting('featured') == 'true':
        get_video_items(base_url, True)
    get_video_items(videos_url)

elif mode=="resolve_url":
    resolve_url(url)

elif mode=="page":
    get_video_items(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))