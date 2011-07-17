import urllib,urllib2,re,os
import xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.audio.twit')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')

def CATEGORIES():
        addLinkLive(__language__(30000),'http://twit.am/listen',__home__+'/icon.png')	
        addDir(__language__(30001),'http://twit.tv/twit',1,'http://leoville.tv/podcasts/coverart/twit600audio.jpg')
        addDir(__language__(30002),'http://twit.tv/tnt',1,'http://leoville.tv/podcasts/coverart/tnt600audio.jpg')
        addDir(__language__(30003),'http://twit.tv/hn',1,'http://leoville.tv/podcasts/coverart/hn144audio.jpg')
        addDir(__language__(30004),'http://twit.tv/ipt',1,'http://leo.am/ipad600audio.jpg')
        addDir(__language__(30005),'http://twit.tv/aaa',1,'http://leo.am/podcasts/coverart/aaa600audio.jpg')
        addDir(__language__(30006),'http://twit.tv/tsh',1,'http://leoville.tv/podcasts/coverart/tsh600audio.jpg')
        addDir(__language__(30007),'http://twit.tv/tri',1,'http://leo.am/tri600audio.jpg')
        addDir(__language__(30008),'http://twit.tv/twig',1,'http://leoville.tv/podcasts/coverart/twig600audio.jpg')
        addDir(__language__(30009),'http://twit.tv/ww',1,'http://leoville.tv/podcasts/coverart/ww600audio.jpg')
        addDir(__language__(30010),'http://twit.tv/mbw',1,'http://leoville.tv/podcasts/coverart/mbw600audio.jpg')
        addDir(__language__(30011),'http://twit.tv/photo',1,'http://leo.am/photo144audio.jpg')
        addDir(__language__(30012),'http://twit.tv/fourcast',1,'http://leo.am/fc600audio.jpg')
        addDir(__language__(30013),'http://twit.tv/ttg',1,'http://leoville.tv/podcasts/coverart/ttg600audio.jpg')
        addDir(__language__(30014),'http://twit.tv/DGW',1,'http://leoville.tv/podcasts/coverart/dgw600audio.jpg')
        addDir(__language__(30015),'http://twit.tv/sn',1,'http://leoville.tv/podcasts/coverart/sn600audio.jpg')
        addDir(__language__(30016),'http://twit.tv/twirt',1,'http://leoville.tv/podcasts/coverart/twirt144audio.jpg')
        addDir(__language__(30017),'http://twit.tv/nsfw',1,'http://leoville.tv/podcasts/coverart/nsfw600audio.jpg')
        addDir(__language__(30018),'http://twit.tv/twich',1,'http://leoville.tv/podcasts/coverart/twich600audio.jpg')
        addDir(__language__(30019),'http://twit.tv/fr',1,'http://leo.am/fr600audio.jpg')
        addDir(__language__(30020),'http://twit.tv/htg',1,'http://leoville.tv/podcasts/coverart/htg600audio.jpg')
        addDir(__language__(30021),'http://twit.tv/specials',1,'http://leoville.tv/podcasts/coverart/specials600audio.jpg')
        addDir(__language__(30022),'http://twit.tv/kiki',1,'http://leoville.tv/podcasts/coverart/dksh600audio.jpg')
        addDir(__language__(30023),'http://twit.tv/FLOSS',1,'http://leoville.tv/podcasts/coverart/floss600audio.jpg')
        addDir(__language__(30024),'http://twit.tv/twil',1,'http://leoville.tv/podcasts/coverart/twil600audio.jpg')
        addDir(__language__(30025),'http://twit.tv/FIB',1,'http://leoville.tv/podcasts/coverart/fib600audio.jpg')
        addDir(__language__(30026),'http://twit.tv/gtt',1,'http://leo.am/gtt600audio.jpg')
        addDir(__language__(30027),'http://twit.tv/natn',1,'http://leoville.tv/podcasts/coverart/tsh600audio.jpg')
        addDir(__language__(30028),'http://twit.tv/cgw',1,'http://leo.am/cgw600audio.jpg')


def INDEX(url,iconimage):
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://twit.tv/'),
                ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        shows = soup.findAll('div', attrs={'class' : "podcast-meta"})
        del shows[-1]
        for show in shows:
            try:
                name = show('a')[0].string+' - '+show('p')[0].string
            except:
                name = show('a')[0].string
            url = 'http://twit.tv'+show('a')[0]['href']
            addLink(name,url,2,iconimage)
        page=re.compile('<div class="episode-prevnext clearfix"><a href=".+?" class="episode-next pager-prev active"><span>Next</span></a><a href="(.+?)" class="episode-prev pager-next active"><span>Prev</span></a></div>').findall(link)
        if len(page)<1:
            page=re.compile('<span>Next</span></span><a href="(.+?)" class="episode-prev pager-next active">').findall(link)
        for url in page:
                addDir('Next Page','http://twit.tv'+url,1,'')

def getURL(url):
        req = urllib2.Request(url)
        req.addheaders = [('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        url = soup.find('div', attrs={'class' : 'download'})('a')[0]['href']
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

def addLinkLive(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultAudio.png", thumbnailImage=iconimage)
        liz.setInfo( type="Audio", infoLabels={ "Title": name } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok

def addLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Audio", infoLabels={ "Title": name} )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
        liz.setInfo( type="Audio", infoLabels={ "Title": name } )
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
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None or url==None or len(url)<1:
    print ""
    CATEGORIES()

elif mode==1:
    print ""+url
    INDEX(url,iconimage)
        
elif mode==2:
    print ""+url
    getURL(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))