import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.zapiks')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by')
home = __settings__.getAddonInfo('path')


def categories():
    if sort==__language__(30013):
        u = '/premium_1.php'
        addDir(__language__(30000),'http://www.zapiks.com/_surf_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/surf.png' ) ))
        addDir(__language__(30001),'http://www.zapiks.com/_snowboard_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/snowboard.png' ) ))
        addDir(__language__(30002),'http://www.zapiks.com/_mountainbike_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/vtt.png' ) ))
        addDir(__language__(30003),'http://www.zapiks.com/_bmx_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/bmx.png' ) ))
        addDir(__language__(30004),'http://www.zapiks.com/_skate_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/skate.png' ) ))
        addDir(__language__(30005),'http://www.zapiks.com/_ski_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/ski.png' ) ))
    else:
        if sort==__language__(30010):
            u = '1'
        if sort==__language__(30012):
            u = '/alltimebuzzed_1.php'
        if sort==__language__(30011):
            u = '/popular_1.php'
        addDir(__language__(30000),'http://www.zapiks.com/surf_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/surf.png' ) ))
        addDir(__language__(30001),'http://www.zapiks.com/snowboard_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/snowboard.png' ) ))
        addDir(__language__(30002),'http://www.zapiks.com/mountainbike_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/vtt.png' ) ))
        addDir(__language__(30003),'http://www.zapiks.com/bmx_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/bmx.png' ) ))
        addDir(__language__(30004),'http://www.zapiks.com/skate_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/skate.png' ) ))
        addDir(__language__(30005),'http://www.zapiks.com/ski_'+u,1,xbmc.translatePath( os.path.join( home, 'resources/images/ski.png' ) ))


def indexPage(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link=response.read()
    soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
    videos = soup.findAll('div', attrs={'class' : "media_thumbnail medium"})
    for video in videos:
        try:
            url = video('a')[0]['href']
            name = video('a')[0]['title']
            thumb = video('img')[0]['src']
            addLink(name,'http://www.zapiks.com'+url,2,thumb)
        except:
            pass
    try:
        nextPage = soup.find('span', attrs={'class' : "next"})('a')[1]['href']
        addDir(__language__(30006),'http://www.zapiks.com'+nextPage,1,'special://home/addons/plugin.video.zapiks/resources/images/next.png')
    except:
        pass


def videoLinks(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    soup = BeautifulSoup(link)
    vid = soup.find('link', attrs={'rel' : "video_src"})['href']
    vidId = vid[-5:]
    req = urllib2.Request('http://www.zapiks.com/view/index.php?file='+vidId+'&lang=fr')
    req.addheaders = [('Referer', 'http://www.zapiks.com'),
            ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
    response = urllib2.urlopen(req)
    link=response.read()
    response.close()
    soup = BeautifulSoup(link)
    url = soup.find('file').string
    item = xbmcgui.ListItem(path=url)
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


def addLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty("IsPlayable","true")
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
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

if mode==None or url==None or len(url)<1:
        print ""
        categories()

elif mode==1:
        print ""+url
        indexPage(url)

elif mode==2:
        print ""
        videoLinks(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
