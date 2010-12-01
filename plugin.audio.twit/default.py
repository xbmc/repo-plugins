import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon

__settings__ = xbmcaddon.Addon(id='plugin.video.twit')
__language__ = __settings__.getLocalizedString

def CATEGORIES():
	addLinkLive(__language__(30017),'http://twit.am/listen','special://home/addons/plugin.video.twit/icon.png')	
	addDir(__language__(30000),'http://twit.tv/twit',1,'http://static.mediafly.com/publisher/images/ba85558acd844c7384921f9f96989a37/icon-600x600.png')
	addDir(__language__(30001),'http://twit.tv/tnt',1,'http://static.mediafly.com/publisher/images/9ff0322cc0444e599a010cdb9005d90a/icon-600x600.png')
	addDir(__language__(30002),'http://twit.tv/fourcast',1,'http://static.mediafly.com/publisher/images/f7f40bcf20c742cfb55cbccb56c2c68c/icon-600x600.png')
	addDir(__language__(30003),'http://twit.tv/ipt',1,'http://static.mediafly.com/publisher/images/201bc64beb6b4956971650fd1462a704/icon-600x600.png')
	addDir(__language__(30004),'http://twit.tv/gtt',1,'http://static.mediafly.com/publisher/images/0cc717b3cc94406a885e5df42cac2b13/icon-600x600.png')
	addDir(__language__(30005),'http://twit.tv/twig',1,'http://static.mediafly.com/publisher/images/8248233e64fc4c68b722be0ec75d637d/icon-600x600.png')
	addDir(__language__(30006),'http://twit.tv/ww',1,'http://static.mediafly.com/publisher/images/ad659facf4cb4fe795b595d9b4275daf/icon-600x600.png')
	addDir(__language__(30007),'http://twit.tv/mbw',1,'http://static.mediafly.com/publisher/images/a24b7b336fb14a2ba3f1e31223f622ac/icon-600x600.png')
	addDir(__language__(30008),'http://twit.tv/ttg',1,'http://static.mediafly.com/publisher/images/d51aaf03dcfe4502a49e885d4201c278/icon-600x600.png')
	addDir(__language__(30009),'http://twit.tv/sn',1,'http://static.mediafly.com/publisher/images/1ac666ad22d940239754fe953207fb42/icon-600x600.png')
	addDir(__language__(30010),'http://twit.tv/natn',1,'http://static.mediafly.com/publisher/images/7f7185fe4b564de7a6c79f8f57bb59eb/icon-600x600.png')
	addDir(__language__(30011),'http://twit.tv/DGW',1,'http://static.mediafly.com/publisher/images/72acf86f350b40c5b5fd132dcacc78be/icon-600x600.png')
	addDir(__language__(30012),'http://twit.tv/nsfw',1,'http://static.mediafly.com/publisher/images/54f4a471ae6c418d89647968a2ea9c91/icon-600x600.png')
	addDir(__language__(30013),'http://twit.tv/kiki',1,'http://static.mediafly.com/publisher/images/c9ed18a67b134406a4d5fd357db8b0c9/icon-600x600.png')
	addDir(__language__(30014),'http://twit.tv/floss',1,'http://static.mediafly.com/publisher/images/06cecab60c784f9d9866f5dcb73227c3/icon-600x600.png')
	addDir(__language__(30015),'http://twit.tv/twil',1,'http://static.mediafly.com/publisher/images/b2911bcc34174461ba970d2e38507340/icon-600x600.png')
	addDir(__language__(30016),'http://twit.tv/specials',1,'http://static.mediafly.com/publisher/images/eed22d09b9524474ac49bc022b556b2b/icon-600x600.png')
	addDir(__language__(30022),'http://twit.tv/htg',1,'http://leoville.tv/podcasts/coverart/htg600audio.jpg')
	addDir(__language__(30023),'http://twit.tv/fr',1,'http://static.mediafly.com/publisher/images/5a081f72180e41939e549ec7d12be24d/icon-600x600.png')
	addDir(__language__(30024),'http://twit.tv/twich',1,'http://leoville.tv/podcasts/coverart/twich600audio.jpg')
	addDir(__language__(30025),'http://twit.tv/FIB',1,'http://leoville.tv/podcasts/coverart/fib600audio.jpg')
	addDir(__language__(30026),'http://twit.tv/twif',1,'http://leo.am/podcasts/coverart/twif600audio.jpg')
	addDir(__language__(30027),'http://twit.tv/cgw',1,'http://static.mediafly.com/publisher/images/e974ef72d2134d7b91c2908e8ceb5850/icon-600x600.png')	

def INDEX(url):
	req = urllib2.Request(url)
	req.addheaders = [('Referer', 'http://twit.tv/'),
			('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	link=link.replace('&amp;','').replace('#039;',"'").replace('amp;','').replace('quot;','"')
	match=re.compile('<h3 class="podcast-date">(.+?)</h3>\n    <h2><a href="(.+?)" title="(.+?)" alt=".+?">.+?</a></h2>\n    <p>(.+?)</p>\n').findall(link)
	for date,url,name,desc in match:		
		addLink(name,'http://twit.tv'+url,2,date,desc,'special://home/addons/plugin.video.twit/icon.png')
	page=re.compile('<div class="episode-prevnext clearfix"><a href=".+?" class="episode-next pager-prev active"><span>Next</span></a><a href="(.+?)" class="episode-prev pager-next active"><span>Prev</span></a></div>').findall(link)
	if len(page)<1:
		page=re.compile('<span>Next</span></span><a href="(.+?)" class="episode-prev pager-next active">').findall(link)
	for url in page:
			addDir('Next Page','http://twit.tv'+url,1,'')

def VIDEOLINKS(url, name):
	req = urllib2.Request(url)
	req.addheaders = [('Referer', 'http://twit.tv/'),
			('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	link=link.replace(' ','')
	match=re.compile('<divclass="download"><ahref="(.+?)">DownloadAudio</a></div>').findall(link)
	for url in match:
		play=xbmc.Player().play(url)
		
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

def addLink(name,url,mode,date,desc,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultAudio.png", thumbnailImage=iconimage)
	description = desc + "\n \n Published: " + date
	liz.setInfo( type="Audio", infoLabels={ "Title": name,"Plot":description,"Date": date } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
	return ok

def addDir(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
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
	VIDEOLINKS(url, name)

xbmcplugin.endOfDirectory(int(sys.argv[1]))