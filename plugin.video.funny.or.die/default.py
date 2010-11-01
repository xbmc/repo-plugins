import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.funny.or.die')
__language__ = __settings__.getLocalizedString
sort = __settings__.getSetting('sort_by')

		
def CATEGORIES():
        addDir(__language__(30000),'http://www.funnyordie.com/browse/videos/all/exclusives/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30001),'http://www.funnyordie.com/browse/videos/all/immortal/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30002),'http://www.funnyordie.com/browse/videos/stand_up/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30003),'http://www.funnyordie.com/browse/videos/animation/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30004),'http://www.funnyordie.com/browse/videos/web_series/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30005),'http://www.funnyordie.com/browse/videos/nsfw/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30006),'http://www.funnyordie.com/browse/videos/sketch/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30007),'http://www.funnyordie.com/browse/videos/sports/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30008),'http://www.funnyordie.com/browse/videos/clean_comedy/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30009),'http://www.funnyordie.com/browse/videos/politics/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30010),'http://www.funnyordie.com/browse/videos/music/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30011),'http://www.funnyordie.com/browse/videos/parody/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30012),'http://www.funnyordie.com/browse/videos/real_life/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')
        addDir(__language__(30013),'http://www.funnyordie.com/browse/videos/all/all/'+sort,1,'http://public0.ordienetworks.com/images/funny_or_die.gif?f85d7543')

		
def INDEX(url):
        req = urllib2.Request(url)
        req.addheaders = [('Referer', 'http://www.funnyordie.com/videos'),
                          ('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        link=link.replace('&quot;','"').replace('&amp;','&')
        match=re.compile('<a href="/videos/(.+?)/.+?" class=".+?" title=".+?"><img alt=".+?" class=".+?" height="90" src="(.+?)" title="(.+?)" width="124" />').findall(link)
        for url,thumbnail,name in match:
                addLink(name,'http://videos0.ordienetworks.com/videos/'+url+'/sd.flv',thumbnail)
        page=re.compile('Previous</span>.+?<span class="current">.+?</span> <a href="(.+?)" rel="next">.+?</a>').findall(link)
        if len(page)<1:
		    page=re.compile('Previous</a> <a href=".+?" rel="prev start">.+?</a> <span class="current">.+?</span> <a href="(.+?)" rel="next">.+?</a>').findall(link)
        if len(page)<1:
		    page=re.compile('Previous</a>.+?<a href=".+?" rel="start">.+?</a> <a href=".+?" rel="prev">.+?</a> <span class="current">.+?</span> <a href="(.+?)"').findall(link)
        for url in page:
                addDir('Next Page','http://www.funnyordie.com'+url,1,'')

                
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


def addLink(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, } )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
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
        CATEGORIES()
       
elif mode==1:
        print ""+url
        INDEX(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
