import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json

__settings__ = xbmcaddon.Addon(id='plugin.video.fox.news')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )


def getCategories():
        addDir(__language__(30001),87485,2,icon)
        addDir(__language__(30002),0,1,icon)
        addDir(__language__(30003),1,1,icon)
        addDir(__language__(30004),2,1,icon)
        addDir(__language__(30005),3,1,icon)
        addDir(__language__(30006),4,1,icon)
        addDir(__language__(30007),5,1,icon)
        addDir(__language__(30008),6,1,icon)
        addDir(__language__(30009),7,1,icon)
        addDir(__language__(30010),8,1,icon)
        addDir(__language__(30011),9,1,icon)
        addDir(__language__(30012),10,1,icon)
        addDir(__language__(30013),11,1,icon)
        addDir(__language__(30014),12,1,icon)


def getSubcategories(url):
        url = int(url)
        req = urllib2.Request('http://video.foxnews.com')
        req.addheaders = [('Referer', 'http://foxnews.com'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        data = soup.find('div', attrs={'class' : 'playlist-2'})('ul')
        categories = data[url]
        for item in categories('a'):
            name = item['title']
            url=item['href']
            url = url.split('=')[1]
            u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=2&name="+urllib.quote_plus(name)
            ok=True
            liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=icon)
            liz.setInfo( type="Video", infoLabels={ "Title": name } )
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)


def getVideos(url):
        url='http://video.foxnews.com/v/feed/playlist/'+url+'.js?'
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://video.foxnews.com'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3')]
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
                desc = str(video['media-content']['media-description'])+' \n\n'+str(video['media-content']['mvn-airDate'])
            except:
                desc = ''
            name = name.replace('&amp;',' & ')
            url = url.replace('HIGH',__settings__.getSetting('video_quality'))
            duration = video['media-content']['mvn-duration']
            liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumb)
            liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot":desc, "Duration":duration} )
            ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)


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
    print ""
    getCategories()

elif mode==1:
    print ""+url
    getSubcategories(url)

elif mode==2:
    print ""+url
    getVideos(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))