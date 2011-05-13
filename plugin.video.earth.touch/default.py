import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.earth.touch')
__language__ = __settings__.getLocalizedString
videoq = __settings__.getSetting('video_quality')

def CATEGORIES():
		if videoq==__language__(30011):
			addDir(__language__(30000),'http://feeds2.feedburner.com/earth-touch_featured_720p_commentary',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30001),'http://feeds2.feedburner.com/earth-touch_featured_720p',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30003),'http://feeds2.feedburner.com/WeeklyMarinePodcast-hd',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30004),'http://feeds2.feedburner.com/moremi_podcast_720',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30002),'http://feeds2.feedburner.com/earth-touch_podcast_720p',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30005),'http://feeds2.feedburner.com/kids-hd',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
		elif videoq==__language__(30012):
			addDir(__language__(30000),'http://feeds2.feedburner.com/earth-touch_featured_480p_commentary',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30001),'http://feeds2.feedburner.com/earth-touch_featured_480p',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30003),'http://feeds2.feedburner.com/WeeklyMarinePodcast-ipod',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30002),'http://feeds2.feedburner.com/earth-touch_podcast_480p',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30004),'http://feeds2.feedburner.com/moremi_podcast_ipod',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30005),'http://feeds2.feedburner.com/kids-ipod',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
		else:
			addDir(__language__(30000),'http://feeds2.feedburner.com/earth-touch_featured_720p_commentary',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30001),'http://feeds2.feedburner.com/earth-touch_featured_720p',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30003),'http://feeds2.feedburner.com/WeeklyMarinePodcast-hd',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30004),'http://feeds2.feedburner.com/moremi_podcast_720',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30002),'http://feeds2.feedburner.com/earth-touch_podcast_720p',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			addDir(__language__(30005),'http://feeds2.feedburner.com/kids-hd',1,'http://podcast.earth-touch.com/i/podcast/ET_IT3.jpg')
			
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
        response = urllib2.urlopen(req)
        link=response.read()
        code=re.sub('\r','',link)
        code=re.sub('\n',' ',code)
        code=re.sub('\t',' ',code)
        code=re.sub('  ','',code)
        code=re.sub('\xe2\x80\x93','',code)
        code=re.sub('\xe2\x80\x99s','',code)
        response.close()
        plot=re.compile('<itunes:summary>(.+?)</itunes:summary>').findall(code)
        del plot[0]
        date=re.compile('<pubDate>(.+?)</pubDate>').findall(code)
        match=re.compile('<media:content url="(.+?)"').findall(code)
        if len(match)<1:
            match=re.compile('<enclosure url="(.+?)"').findall(code)
        name=re.compile('<item><title>(.+?)</title>').findall(code)
        icon=re.compile('/&gt;&lt;img src="(.+?)"').findall(code)   
        for index in range(len(match)):
                 	addLink(name[index],match[index],icon[index],plot[index],date[index])
    	 
       
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




def addLink(name,url,iconimage,plot,date):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name,"Plot":plot,"Date Published":date})
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
        
elif mode==2:
        print ""+url
        INDEXWEB(url)
		
xbmcplugin.endOfDirectory(int(sys.argv[1]))
