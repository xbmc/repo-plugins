import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.funny.or.die')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by').replace(' ','_').lower()
sort_time = __settings__.getSetting('sort_time').replace(' ','_').lower()
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )


def categories():
        addDir(__language__(30000),'http://www.funnyordie.com/browse/videos/all/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30001),'http://www.funnyordie.com/browse/videos/all/exclusives/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30002),'http://www.funnyordie.com/browse/videos/all/immortal/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30003),'http://www.funnyordie.com/browse/videos/animation/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30004),'http://www.funnyordie.com/browse/videos/animals/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30005),'http://www.funnyordie.com/browse/videos/clean_comedy/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30006),'http://www.funnyordie.com/browse/videos/dumb_people/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30007),'http://www.funnyordie.com/browse/videos/fails/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30008),'http://www.funnyordie.com/browse/videos/memes/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30009),'http://www.funnyordie.com/browse/videos/kids/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30010),'http://www.funnyordie.com/browse/videos/mashups/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30011),'http://www.funnyordie.com/browse/videos/music/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30012),'http://www.funnyordie.com/browse/videos/news_fails/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30013),'http://www.funnyordie.com/browse/videos/nostalgia/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30014),'http://www.funnyordie.com/browse/videos/nsfw/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30015),'http://www.funnyordie.com/browse/videos/parody/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30016),'http://www.funnyordie.com/browse/videos/politics/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30017),'http://www.funnyordie.com/browse/videos/rants/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30018),'http://www.funnyordie.com/browse/videos/real_life/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30019),'http://www.funnyordie.com/browse/videos/recaps/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30020),'http://www.funnyordie.com/browse/videos/sketch/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30021),'http://www.funnyordie.com/browse/videos/sports/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30022),'http://www.funnyordie.com/browse/videos/stand_up/all/'+sort+'/'+sort_time,1,icon)
        addDir(__language__(30023),'http://www.funnyordie.com/browse/videos/web_series/all/'+sort+'/'+sort_time,1,icon)


def getRequest(url):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:9.0.1) Gecko/20100101 Firefox/9.0.1',
                   'Referer' : 'http://www.funnyordie.com/browse/videos'}
        req = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(req)
        link = response.read()
        response.close()
        return link


def index(url, play=False):
        if play == True:
            playlist = xbmc.PlayList(1)
            playlist.clear()
        link = getRequest(url)
        link = link.replace("\\",'').replace('\n','').replace("\'",'')
        items = re.compile('<div class="detailed_vp">(.+?)</a></div></div>').findall(link)
        if len(items) < 1:
            items = re.compile('<div class="detailed_vp">(.+?)</a>n</div></div>').findall(link)
        for i in items:
            name = re.compile('title="(.+?)"').findall(i)[0].replace('&amp;','&').replace('&quot;','"').replace('&apos;',"'")
            try:
                thumb = re.compile('class="thumbnail" height="90" src="(.+?)"').findall(i)[0].replace('medium','fullsize')
            except:
                try:
                    thumb = re.compile('class="thumbnail" src="(.+?)"').findall(i)[0]
                except:
                    thumb = ''
            vid_id = re.compile('data-viewkey="(.+?)"').findall(i)[0][1:]
            try:
                duration = re.compile('<span class="duration">(.+?)</span>').findall(i)[0]
            except:
                duration = ''
            if not play == True:
                addLink(name, vid_id, duration, 2, thumb)
            else:
                url = get_smil(vid_id)
                info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
                playlist.add(url, info)
        try:
            page_num = re.compile('next_page = (.+?);').findall(link)[0]
            page = '?page='+page_num
            if not 'more' in url:
                url = url.replace('videos','more/videos')
            url = url.split('?page')[0]+page
            addDir(__language__(30031), url, 1, xbmc.translatePath( os.path.join( home, 'resources', 'next.png' ) ))
        except: pass
        if play == True:
            xbmc.executebuiltin('playlist.playoffset(video,0)')


def playVid(url):
        url = get_smil(url)
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def addToPlayList(name, url, iconimage):
        url = get_smil(url)
        info = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        playlist = xbmc.PlayList(1)
        playlist.add(url, info)


def get_smil(id):
        link = getRequest("http://www.funnyordie.com/player/"+id+"?v=3")
        soup = BeautifulSoup(link)
        title = soup.find('title').string
        stream_list = soup.findAll('stream')
        if len(stream_list) < 1:
            stream = soup.find('location').contents[0]
            return stream
        else:
            if __settings__.getSetting('video_quality') == '0':
                return stream_list[0].file.contents[0]
            if __settings__.getSetting('video_quality') == '1':
                return stream_list[1].file.contents[0]


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


def addLink(name,url,duration,mode,iconimage,showcontext=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Duration": duration } )
        liz.setProperty('IsPlayable', 'true')
        if showcontext:
            contextMenu = [(__language__(30033),'XBMC.Container.Update(%s?url=%s&mode=3&name=%s&iconimage=%s)' %(sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name), urllib.quote_plus(iconimage)))]
            liz.addContextMenuItems(contextMenu)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,totalItems=20)
        return ok


def addDir(name,url,mode,iconimage,showcontext=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        if showcontext:
            contextMenu = [(__language__(30032),'XBMC.Container.Update(%s?url=%s&mode=4)' %(sys.argv[0], urllib.quote_plus(url)))]
            liz.addContextMenuItems(contextMenu)
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
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    categories()

elif mode==1:
    print ""+url
    index(url)

elif mode==2:
    print ""
    playVid(url)

elif mode==3:
    print ""
    addToPlayList(name, url, iconimage)

elif mode==4:
    print ""
    index(url, True)

xbmcplugin.endOfDirectory(handle=int(sys.argv[1]))