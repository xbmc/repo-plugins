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
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath(os.path.join(home, 'icon.png'))
videoq = __settings__.getSetting('video_quality')
cache = StorageServer.StorageServer("earthtouch", 24)
base = 'http://www.earth-touch.com'


def make_request(url):
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://www.earth-touch.com'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification(Earth-Touch,HTTP ERROR: "+str(e.code)+",5000,"+ICON+")")


def cache_shows():
        soup = BeautifulSoup(make_request(base+'/shows/'), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'class' : 'show-block'})
        shows = []
        for i in items:
            thumb = i.img['src']
            name = i.h3.string
            desc = i.p.string.strip()
            href = i('a', attrs={'class' : 'linkout'})[0]['href']
            shows.append((name,href,thumb,desc))
        return(str(shows))


def get_shows():
        for i in eval(cache.cacheFunction(cache_shows)):
            addDir(i[0], base+i[1], 1, base+i[2], i[3])
        addDir('Podcasts', '', 4, xbmc.translatePath(os.path.join(home, 'resources', 'podcasts_icon.png')))


def index_show(url, show_name):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('div', attrs={'class' : "es-carousel"})[0]('li')
        for i in items:
            episode = i.h3.string
            name = show_name + ': '+ episode.title()
            desc = i('p')[-1].string.strip()
            duration = i.span.string
            thumb = i.img['src']
            href = i.a['href']
            addPlayableLink(name, base+href, desc, duration, base+thumb, 2)
            
            
def resolve_url(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        vid_id = soup.iframe['id'].split('_')[1]
        path ='plugin://plugin.video.vimeo/?path=/root/explore/hd&action=play_video&videoid='+vid_id
        item = xbmcgui.ListItem(path=path)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    
    
def podcasts():
        thumb = xbmc.translatePath(os.path.join(home, 'resources', 'podcasts_icon.png'))
        feed = 'http://feeds2.feedburner.com/'
        if videoq==__language__(30011):
            addDir(__language__(30000),feed+'earth-touch_featured_720p_commentary', 5, thumb)
            addDir(__language__(30001),feed+'earth-touch_featured_720p', 5, thumb)
            addDir(__language__(30003),feed+'WeeklyMarinePodcast-hd', 5, thumb)
            addDir(__language__(30004),feed+'moremi_podcast_720', 5, thumb)
            addDir(__language__(30002),feed+'earth-touch_podcast_720p', 5, thumb)
            addDir(__language__(30005),feed+'kids-hd', 5, thumb)
        elif videoq==__language__(30012):
            addDir(__language__(30000),feed+'earth-touch_featured_480p_commentary', 5, thumb)
            addDir(__language__(30001),feed+'earth-touch_featured_480p', 5, thumb)
            addDir(__language__(30003),feed+'WeeklyMarinePodcast-ipod', 5, thumb)
            addDir(__language__(30002),feed+'earth-touch_podcast_480p', 5, thumb)
            addDir(__language__(30004),feed+'moremi_podcast_ipod', 5, thumb)
            addDir(__language__(30005),feed+'kids-ipod', 5, thumb)
        else:
            addDir(__language__(30000),feed+'earth-touch_featured_720p_commentary', 5, thumb)
            addDir(__language__(30001),feed+'earth-touch_featured_720p', 5, thumb)
            addDir(__language__(30003),feed+'WeeklyMarinePodcast-hd', 5, thumb)
            addDir(__language__(30004),feed+'moremi_podcast_720', 5, thumb)
            addDir(__language__(30002),feed+'earth-touch_podcast_720p', 5, thumb)
            addDir(__language__(30005),feed+'kids-hd', 5, thumb)
            
def index_podcasts(url):
        soup = BeautifulStoneSoup(make_request(url), convertEntities=BeautifulStoneSoup.XML_ENTITIES)
        items = soup('li', attrs={'class' : "regularitem"})
        for i in items:
            name = i.a.string
            thumb = i.img['src']
            media_url = i.p.a['href']
            try:
                desc = i.div.p.string
            except: desc = ''
            addLink(name,media_url,thumb,desc)
         
       
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


def addLink(name,url,iconimage,plot):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":plot})
        liz.setProperty('mimetype', 'video')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addPlayableLink(name,url,plot,duration,iconimage,mode):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": plot, "Duration": duration })
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage,desc=''):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": desc } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
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

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
    get_shows()
       
elif mode==1:
    index_show(url, name)
        
elif mode==2:
    resolve_url(url)
        
elif mode==4:
    podcasts()
        
elif mode==5:
    index_podcasts(url)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))
