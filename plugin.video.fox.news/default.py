import urllib
import urllib2
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
import xbmcvfs
import StorageServer
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json

__settings__ = xbmcaddon.Addon(id='plugin.video.fox.news')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
cache = StorageServer.StorageServer("FoxNews", 24)


def getCategories():
        addDir(__language__(30001),0,1,icon)
        addDir(__language__(30002),1,1,icon)
        addDir(__language__(30003),2,1,icon)
        addDir(__language__(30004),3,1,icon)
        addDir(__language__(30005),4,1,icon)
        addDir(__language__(30006),5,1,icon)
        addDir(__language__(30007),6,1,icon)
        addDir(__language__(30008),7,1,icon)
        addDir(__language__(30009),8,1,icon)
        addDir(__language__(30010),9,1,icon)
        addDir(__language__(30011),10,1,icon)
        addDir(__language__(30012),11,1,icon)
        addDir(__language__(30013),12,1,icon)
        addDir(__language__(30014),13,1,icon)


def subcat_cache():
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:9.0.1) Gecko/20100101 Firefox/9.0.1',
                   'Referer' : 'http://foxnews.com'}
        req = urllib2.Request('http://video.foxnews.com',None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        return(link, 200)


def getSubcategories(url):
        soup = BeautifulSoup(cache.cacheFunction(subcat_cache)[0], convertEntities=BeautifulSoup.HTML_ENTITIES)
        data = soup.find('div', attrs={'class' : 'playlist-2'})('ul')
        categories = data[int(url)]
        for item in categories('a'):
            name = item['title']
            url=item['href']
            if url == '#':
                url = '87485'
            else:
                url = url.split('-')[-1]
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=2&name="+urllib.quote_plus(name)
            ok=True
            liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=icon)
            liz.setInfo( type="Video", infoLabels={ "Title": name } )
            contextMenu = [(__language__(30019),'RunPlugin(%s?url=%s&mode=3&play=True)' %(sys.argv[0], urllib.quote_plus(url)))]
            liz.addContextMenuItems(contextMenu)
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)


def getVideos(url, play=False):
        if play:
            playlist = xbmc.PlayList(1)
            playlist.clear()
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:9.0.1) Gecko/20100101 Firefox/9.0.1',
                   'Referer' : 'http://video.foxnews.com'}
        req = urllib2.Request('http://video.foxnews.com/v/feed/playlist/'+url+'.js?',None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        data = json.loads(link)
        videos = data['channel']['item']
        for video in videos:
            name = video['media-content']['mvn-shortDescription']
            url = video['media-content']['mvn-fnc_mp4']
            thumb = video['media-content']['media-thumbnail']
            try:
                desc = str(video['media-content']['media-description'])+' \n\n'+str(video['media-content']['mvn-airDate'].split('T')[0])
            except:
                desc = ''
            name = name.replace('&amp;',' & ')
            url = url.replace('HIGH',__settings__.getSetting('video_quality'))
            duration = video['media-content']['mvn-duration']
            if play:
                info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
                playlist.add(url, info)
            else:
                liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
                liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot":desc, "Duration":duration} )
                ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        if play:
            xbmc.executebuiltin('playlist.playoffset(video,0)')


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+str(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok


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


xbmcplugin.setContent(int(sys.argv[1]), 'movies')

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
try:
    play=eval(params["play"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
    print ""
    getCategories()

elif mode==1:
    print ""
    getSubcategories(url)

elif mode==2:
    print ""
    getVideos(url)

elif mode==3:
    print ""
    getVideos(url, True)

xbmcplugin.endOfDirectory(int(sys.argv[1]))