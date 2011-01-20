import xbmcplugin,xbmcgui,xbmcaddon
import urllib2,urllib,re,os
from BeautifulSoup import BeautifulSoup

__settings__ = xbmcaddon.Addon(id='plugin.video.cartoon.network')
__language__ = __settings__.getLocalizedString
__home__ = __settings__.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( __home__, 'resources/cn.png' ) )


def getShows():
		addDir(__language__(30000),'8a250ab0230ec20c012334ad4f650371',1,icon)
		url='http://www.cartoonnetwork.com/video/staged/CN2.configuration.xml'
		req = urllib2.Request(url)
		req.addheaders = [('Referer', 'http://www.cartoonnetwork.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.XML_ENTITIES)
		shows = soup('show')
		for show in shows:
				name = show['title']
				url = show['id']
				thumbnail = show['imageurl']
				if thumbnail=='http://i.cartoonnetwork.com/toon/video/repositorynull':
						thumbnail = icon
				addDir(name,url,1,thumbnail)


def getEpisodes(url):
		Aurl='http://www.cartoonnetwork.com/cnvideosvc2/svc/episodeSearch/getEpisodesByShow?networkName=CN2&id='+url+'&limit=500&offset=0'
		req = urllib2.Request(Aurl)
		req.addheaders = [('Referer', 'http://www.cartoonnetwork.com'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link, convertEntities=BeautifulSoup.XML_ENTITIES)
		shows = soup('episode')
		for show in shows:
				thumbnail = show['thumbnailurl']
				name = show['title']
				clipIDs = show('value')[0].string.split('#')
				if len(clipIDs) < 2:
						clipID = clipIDs
				episodetype = show['episodetype']
				videoUrl = 'stack://'
				if episodetype=='EPI-EPI':
						if len(clipIDs) > 1:
								for clipID in clipIDs:
										url = getClipUrl(clipID)
										url=url.replace('turnerios-f.akamaihd.net/i','ht2.cdn.turner.com').replace('iPhone_,lo,hi,.mp4.csmil/master.m3u8','CNVHD.flv')
										videoUrl += url + ' , '
								addLink(name+'  | '+__language__(30001),videoUrl[0:-3],thumbnail)
						else:
								url = getClipUrl(clipID[0])
								url=url.replace('turnerios-f.akamaihd.net/i','ht2.cdn.turner.com').replace('iPhone_,lo,hi,.mp4.csmil/master.m3u8','CNVHD.flv')
								addLink(name+'  | '+__language__(30001),url,thumbnail)
				if episodetype=='EPI-PRE':
						if len(clipIDs) > 1:
								for clipID in clipIDs:
										url = getClipUrl(clipID)
										url=url.replace('turnerios-f.akamaihd.net/i','ht2.cdn.turner.com').replace('iPhone_,lo,hi,.mp4.csmil/master.m3u8','CNVHD.flv')
										videoUrl += url + ' , '
								addLink(name+'  | '+__language__(30002),videoUrl[0:-3],thumbnail)
						else:
								url = getClipUrl(clipID[0])
								url=url.replace('turnerios-f.akamaihd.net/i','ht2.cdn.turner.com').replace('iPhone_,lo,hi,.mp4.csmil/master.m3u8','CNVHD.flv')
								addLink(name+'  | '+__language__(30002),url,thumbnail)
				elif episodetype=='CLI-CLI':
						url = getClipUrl(clipID[0])
						url=url.replace('turnerios-f.akamaihd.net/i','ht2.cdn.turner.com').replace('iPhone_,lo,hi,.mp4.csmil/master.m3u8','CNVHD.flv')
						addLink(name+'  | '+__language__(30003),url,thumbnail)


def getClipUrl(clipID):
		Surl='http://www.cartoonnetwork.com/cnvideosvc2/svc/episodeservices/getVideoPlaylist?networkName=CN2&id='+str(clipID)
		req = urllib2.Request(Surl)
		req.addheaders = [('Referer', 'http://www.cartoonnetwork.com/tools/media/cn_video_achievement.swf'),
				('Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)')]
		response = urllib2.urlopen(req)
		link=response.read()
		response.close()
		soup = BeautifulSoup(link)
		url = soup('ref')[0]['href']
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


def addLink(name,url,iconimage):
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
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
		getShows()
	
elif mode==1:
		print ""+url
		getEpisodes(url)

elif mode==2:
		print ""+url
		getClipUrl(clipID)

		
xbmcplugin.endOfDirectory(int(sys.argv[1]))				