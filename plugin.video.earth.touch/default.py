import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

__settings__ = xbmcaddon.Addon(id='plugin.video.earth.touch')
__language__ = __settings__.getLocalizedString
addon_version = __settings__.getAddonInfo('version')
home = xbmc.translatePath(__settings__.getAddonInfo('path'))
icon = os.path.join(home, 'icon.png')
default_fanart = os.path.join(home, 'fanart.jpg')
cache = StorageServer.StorageServer("earthtouch", 24)
base_url = 'http://www.earthtouch.tv'
debug = __settings__.getSetting('debug')
if debug == 'true':
    cache.dbg = True


def addon_log(string):
    if debug == 'true':
        xbmc.log("[addon.earthtouch-%s]: %s" %(addon_version, string))

def make_request(url):
        try:
            headers = {
                'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:16.0) Gecko/20100101 Firefox/16.0',
                'Referer' : base_url
                }
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            addon_log('We failed to open "%s".' % url)
            if hasattr(e, 'reason'):
                addon_log('We failed to reach a server.')
                addon_log('Reason: %s' %e.reason)
            if hasattr(e, 'code'):
                addon_log('We failed with error code - %s.' %e.code)
                xbmc.executebuiltin("XBMC.Notification(Earth-Touch,HTTP ERROR: "+str(e.code)+",5000,"+ICON+")")


def cache_shows():
        soup = BeautifulSoup(make_request(base_url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        homepage = {}
        latest = []
        img_tag = soup.find('img', attrs={'id': 'bgimg'})
        if img_tag:
            fanart = img_tag['src']
        else: fanart = default_fanart
        homepage['fanart'] = fanart
        latest_items = soup.find('div', attrs={'class': 'es-carousel'})('li')
        for i in latest_items:
            duration = i('span', attrs={'class': 'timestamp'})[0].string
            latest.append((i.h3.string, i.a['href'], i.img['src'], duration, i.blockquote.string))
        homepage['latest'] = latest
        featured = []
        featured_items = soup.find('div', attrs={'class': 'flex-container'})('a')
        for i in featured_items:
            title = i.h3.string
            thumb = i('img')[-1]['src']
            duration = i('span', attrs={'class': 'timestamp'})[0].string
            desc = i.p.string.strip()
            featured.append((title, i['href'], thumb, duration, desc))
        homepage['featured'] = featured
        channels = {}
        channel_items = soup.find('div', attrs={'class': 'channel-block'})('a')
        for i in channel_items:
            title = i.h3.string+' - '+i.small.string
            channels[title] = {}
            channels[title]['href'] = i['href']
        homepage['channels'] = channels
        for i in homepage['channels'].keys():
                channel_url = base_url+homepage['channels'][i]['href']
                soup = BeautifulSoup(make_request(channel_url), convertEntities=BeautifulSoup.HTML_ENTITIES)
                show_items = soup.findAll('div', attrs={'class': 'show-block'})
                show_list = []
                for s in show_items:
                        href = s.a['href'].rsplit('/', 2)[0]
                        show_list.append((s.h3.string, href, s.img['src'], s.p.string))
                homepage['channels'][i]['shows'] = show_list
        return homepage


def get_shows():
        data = cache.cacheFunction(cache_shows)
        fanart = base_url+data['fanart']
        addDir(__language__(30001), 'recent', icon, fanart, 4)
        channels = data['channels']
        for i in channels.keys():
            for s in channels[i]['shows']:
                title = s[0].encode('utf-8')
                desc = s[3].encode('utf-8').strip()
                addDir(title, base_url+s[1], base_url+s[2], fanart, 1, '', desc)
        xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')


def get_latest_episodes():
        data = cache.cacheFunction(cache_shows)
        for i in data['latest']:
            title = i[0].encode('utf-8')
            desc = i[4].encode('utf-8').strip()
            addDir(title, base_url+i[1], base_url+i[2], base_url+data['fanart'], 2, i[3], desc, True)
            xbmcplugin.setContent(int(sys.argv[1]), 'episodes')


def index_show(url, show_name):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        img_tag = soup.find('img', attrs={'class': 'slide-img'})
        if img_tag:
            fanart = img_tag['src']
        else:
            img_tag = soup.find('img', attrs={'id': 'bgimg'})
            if img_tag:
                fanart = img_tag['src']
            else:
                fanart = default_fanart
        items = soup('div', attrs={'class' : "es-carousel"})[0]('li')
        for i in items:
            desc = i('p')[-1].string.strip()
            duration = i.span.string
            addDir(i.h3.string.title(), base_url+i.a['href'], base_url+i.img['src'], base_url+fanart, 2, duration, desc, True)
            xbmcplugin.setContent(int(sys.argv[1]), 'episodes')


def resolve_url(url):
        data = make_request(url)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        path = ''
        success = False
        for i in soup('iframe'):
            try:
                id_key = i['id']
                if id_key.startswith('player_'):
                    # vid_id = id_key.split('_')[1]
                    vid_id = id_key.replace('player_', '')
                    path ='plugin://plugin.video.vimeo/?path=/root/explore/hd&action=play_video&videoid='+vid_id
                    success = True
                else:
                    addon_log('id_key: %s' %id_key)
                if success: break
            except: continue
        if not success:
            try:
                embed_link = re.findall('swfobject.embedSWF\("(.+?)",', data)[0]
            except:
                addon_log('NO MATCH')
                embed_link = None
            if embed_link:
                if 'youtube' in embed_link:
                    addon_log('YouTube: %s' %embed_link)
                    vid_id = embed_link.split('?')[0].split('/')[-1]
                    path = 'plugin://plugin.video.youtube/?action=play_video&videoid='+vid_id
                    success = True
                else:
                    addon_log('Not YouTube: %s' %embed_link)
        item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), success, item)


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


def get_length_in_minutes(length):
        l_split = length.split(':')
        minutes = int(l_split[-2])
        if int(l_split[-1]) >= 30:
            minutes += 1
        if len(l_split) == 3:
            minutes += (int(l_split[0]) * 60)
        if minutes < 1:
            minutes = 1
        return minutes


def addDir(name, url, iconimage, fanart, mode, duration='', description='', isplayable=False):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        isfolder = True
        if isplayable:
            if ':' in duration:
                duration = get_length_in_minutes(duration)
            liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description, "Duration": duration })
            liz.setProperty('IsPlayable', 'true')
            isfolder = False
        else:
            liz.setInfo(type="Video", infoLabels={ "Title": name, "Plot": description })
        liz.setProperty("Fanart_Image", fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isfolder)
        return ok


params=get_params()
url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

addon_log("Mode: "+str(mode))
addon_log("URL: "+str(url))
addon_log("Name: "+str(name))

if mode==None:
    get_shows()

elif mode==1:
    index_show(url, name)

elif mode==2:
    resolve_url(url)

elif mode==4:
    get_latest_episodes()

xbmcplugin.endOfDirectory(int(sys.argv[1]))
