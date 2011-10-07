import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.audio.twit')
__language__ = __settings__.getLocalizedString
home = __settings__.getAddonInfo('path')
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )


def categories():
        addLink(__language__(30000),'http://twit.am/listen',3,xbmc.translatePath( os.path.join( home, 'resources', 'live.png' ) ))
        addDir(__language__(30001),'http://twit.tv/show/this-week-in-tech',1,'http://leoville.tv/podcasts/coverart/twit600audio.jpg')
        addDir(__language__(30002),'http://twit.tv/show/tech-news-today',1,'http://leoville.tv/podcasts/coverart/tnt600audio.jpg')
        addDir(__language__(30003),'http://twit.tv/show/fourcast',1,'http://leoville.tv/podcasts/coverart/fc600audio.jpg')
        addDir(__language__(30004),'http://twit.tv/show/ipad-today',1,'http://leoville.tv/podcasts/coverart/ipad600audio.jpg')
        addDir(__language__(30005),'http://twit.tv/show/all-about-android',1,'http://leo.am/podcasts/coverart/aaa600audio.jpg')
        addDir(__language__(30006),'http://twit.tv/show/tech-history-today',1,'http://leoville.tv/podcasts/coverart/tht600audio.jpg')
        addDir(__language__(30007),'http://twit.tv/show/this-week-in-google',1,'http://leoville.tv/podcasts/coverart/twig600audio.jpg')
        addDir(__language__(30008),'http://twit.tv/show/windows-weekly',1,'http://leoville.tv/podcasts/coverart/ww600audio.jpg')
        addDir(__language__(30009),'http://twit.tv/show/macbreak-weekly',1,'http://leoville.tv/podcasts/coverart/mbw600audio.jpg')
        addDir(__language__(30010),'http://twit.tv/show/triangulation',1,'http://leoville.tv/podcasts/coverart/tri600audio.jpg')
        addDir(__language__(30011),'http://twit.tv/show/twit-photo',1,'http://leoville.tv/podcasts/coverart/photo144.jpg')
        addDir(__language__(30012),'http://twit.tv/show/the-tech-guy',1,'http://leoville.tv/podcasts/coverart/ttg600audio.jpg')
        addDir(__language__(30013),'http://twit.tv/show/security-now',1,'http://leoville.tv/podcasts/coverart/sn600audio.jpg')
        addDir(__language__(30014),'http://twit.tv/show/the-social-hour',1,'http://leoville.tv/podcasts/coverart/tsh600audio.jpg')
        addDir(__language__(30015),'http://twit.tv/show/weekly-daily-giz-wiz',1,'http://leoville.tv/podcasts/coverart/dgw600audio.jpg')
        addDir(__language__(30016),'http://twit.tv/show/nsfw',1,'http://leoville.tv/podcasts/coverart/nsfw600audio.jpg')
        addDir(__language__(30017),'http://twit.tv/show/dr-kikis-science-hour',1,'http://leoville.tv/podcasts/coverart/dksh600audio.jpg')
        addDir(__language__(30018),'http://twit.tv/show/floss-weekly',1,'http://leoville.tv/podcasts/coverart/floss600audio.jpg')
        addDir(__language__(30019),'http://twit.tv/show/this-week-in-law',1,'http://leoville.tv/podcasts/coverart/twil600audio.jpg')
        addDir(__language__(30020),'http://twit.tv/show/twit-live-specials',1,'http://leoville.tv/podcasts/coverart/specials600audio.jpg')
        addDir(__language__(30021),'http://twit.tv/show/home-theater-geeks',1,'http://leoville.tv/podcasts/coverart/htg600audio.jpg')
        addDir(__language__(30022),'http://twit.tv/show/frame-rate',1,'http://leoville.tv/podcasts/coverart/fr600audio.jpg')
        addDir(__language__(30023),'http://twit.tv/show/this-week-in-computer-hardware',1,'http://leoville.tv/podcasts/coverart/twich600audio.jpg')
        addDir(__language__(30024),'http://twit.tv/show/ham-nation',1,'http://leoville.tv/podcasts/coverart/hn144audio.jpg')
        addDir(__language__(30025),'http://twit.tv/show/futures-in-biotech',1,'http://leoville.tv/podcasts/coverart/fib600audio.jpg')
        addDir(__language__(30026),'http://twit.tv/show/this-week-in-radio-tech',1,'http://static.mediafly.com/publisher/images/ab7b2412afa84674971e4c93665d0e06/icon-600x600.png')


def index(url,iconimage):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup.findAll('div', attrs={'class' : 'view-content'})[3]('div', attrs={'class' : 'field-content'})
        for i in items:
            name = i.a.string
            url = i.a['href']
            addLink(name,url,2,iconimage)
        try:
            page = 'http://twit.tv'+soup('li', attrs={'class' : "pager-next"})[0].a['href']
            addDir('Next Page',page,1,iconimage)
        except:
            pass


def getAudio(url):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        item = xbmcgui.ListItem(path = soup('a', attrs={'class' : "audio download"})[0]['href'])
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def playLive(url):
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
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Audio", infoLabels={ "Title": name} )
        liz.setProperty('IsPlayable', 'true')
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Audio", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
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
    print ""
    index(url,iconimage)

elif mode==2:
    print ""
    getAudio(url)

elif mode==3:
    print ""
    playLive(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))