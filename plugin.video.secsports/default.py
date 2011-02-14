import urllib,urllib2,re,xbmcplugin,xbmcgui,xbmcaddon
from BeautifulSoup import BeautifulSoup

#SEC Sports - by divingmule.

__settings__ = xbmcaddon.Addon(id='plugin.video.secsports')
__language__ = __settings__.getLocalizedString


def CATEGORIES():
		addDir(__language__(30000),'http://www.secdigitalnetwork.com/SECVIDEO/OnDemandVideos.aspx',1,'special://home/addons/plugin.video.secsports/icon.png')
		addDir(__language__(30001),'http://www.secdigitalnetwork.com/SECVIDEO/OnDemandVideos/TabId/862/CategoryId/124/FB-Current-Season.aspx',1,'special://home/addons/plugin.video.secsports/icon.png')
		addDir(__language__(30014),'http://www.secdigitalnetwork.com/SECVIDEO/OnDemandVideos/TabId/862/CategoryId/186/Mens-Basketball.aspx',1,'special://home/addons/plugin.video.secsports/icon.png')
		addDir(__language__(30015),'http://www.secdigitalnetwork.com/SECVIDEO/OnDemandVideos/TabId/862/CategoryId/185/Womens-Basketball.aspx',1,'special://home/addons/plugin.video.secsports/icon.png')
		addDir(__language__(30016),'http://www.secdigitalnetwork.com/SECVIDEO/OnDemandVideos/TabId/862/CategoryId/55/Volleyball.aspx',1,'special://home/addons/plugin.video.secsports/icon.png')
		addDir(__language__(30017),'http://www.secdigitalnetwork.com/SECVIDEO/OnDemandVideos/TabId/862/CategoryId/89/Soccer.aspx',1,'special://home/addons/plugin.video.secsports/icon.png')
		addDir(__language__(30002),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/70/Alabama.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/Alabama_Logo2.jpg')
		addDir(__language__(30003),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/75/Kentucky.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/University-of-Kentucky.jpg')
		addDir(__language__(30004),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/80/Tennessee.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/logo-university-of-tennessee.jpg')
		addDir(__language__(30005),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/74/Georgia.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/University-of-Georgia.jpg')
		addDir(__language__(30006),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/79/South-Carolina.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/south20carolina20logo.jpg')
		addDir(__language__(30007),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/72/Auburn.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/auburn-university.jpg')
		addDir(__language__(30008),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/78/Mississippi-State.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/MississippiStateBulldogs.jpg')
		addDir(__language__(30009),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/81/Vanderbilt.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/vanderbilt_universitypng.jpg')
		addDir(__language__(30010),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/73/Florida.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/UF_Signature1.jpg')
		addDir(__language__(30011),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/71/Arkansas.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/arkansasrazorback23.png')
		addDir(__language__(30012),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/77/Ole-Miss.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/olemiss.jpg')
		addDir(__language__(30013),'http://www.secdigitalnetwork.com/VIDEO/OnDemandVideos/TabId/862/CategoryId/76/LSU.aspx',1,'http://i129.photobucket.com/albums/p223/racefan68/sec/LSU.jpg')
		
			
def INDEX(url):
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.secdigitalnetwork.com'),
						('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		videos = soup.findAll('div', attrs={'class' : "video_element"})
		for video in videos:
				url = video('a')[0]['href']
				print '!!!!!!!!!!!!!!'+url
				thumbnail = video('a')[0].next['src']
				if thumbnail[0]=='/':
						thumbnail = 'http://www.secdigitalnetwork.com'+thumbnail
				name = video('a')[1].next
				videoUrl = getVideoUrl(url,thumbnail)
				print '$$$$$$$$$'+videoUrl
				addLink(name,videoUrl,thumbnail)


def getVideoUrl(url,thumbnail):
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.secdigitalnetwork.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		try:
				videoTag = soup.find('div', attrs={'id' : "dnn_player"})('span')[1].next['src']
				url=re.compile('video=(.+?)&image=.+?').findall(videoTag)
				url = str(url[0])
		except (IndexError, TypeError):
				print 'no videoTag'
				url = thumbnail
				url = thumbnail.replace('_preview.jpg','_sec-cms-mp4-s3.flv')
		return url

		
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


def addLink(name,url,thumbnail):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz,totalItems=16)
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
