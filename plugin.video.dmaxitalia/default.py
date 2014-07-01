import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import os, sys
import httplib, urllib, urllib2, urlparse

import StorageServer

from BeautifulSoup import BeautifulSoup

from pyamf import remoting

addon = xbmcaddon.Addon(id='plugin.video.dmaxitalia')
thisPlugin = int(sys.argv[1])
baseUrl = "http://www.dmax.it"
urlShows = "http://www.dmax.it/video/programmi/"


height = 1080;#268|356|360|400|572|576
const_str = "ef59d16acbb13614346264dfe58844284718fb7b"
const_playerID = 1752666798001;
const_publisherID = 1265527910001;
const_playerKey = "AQ~~,AAABJqdXbnE~,swSdm6mQzrEWC8U2s8_PyL570J6HePbQ"
isThumbnailsScanEnabled = addon.getSetting('thumbnails_scan')
thumbnailsCacheDays = addon.getSetting('thumbnails_cache_time')
videoMaxBitrate = addon.getSetting('video_max_bitrate')
autostartVideoInSeconds = addon.getSetting('video_autostart_time')

thumbnailsCache = StorageServer.StorageServer("plugin.video.dmaxitalia", 24*int(thumbnailsCacheDays))

def loadPage(url):
	print "Load: " + url
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:29.0) Gecko/20100101 Firefox/29.0')
	response = urllib2.urlopen(req)
	link = response.read()
	response.close()
	return link

def addDirectoryItem(label, url, mode, iconImage):
	url = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	li = xbmcgui.ListItem(label, iconImage="DefaultFolder.png", thumbnailImage=iconImage)
	li.setInfo(type="Video", infoLabels={"title": label})
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=url, listitem=li, isFolder=True)
	
def addLinkItem(label, url, mode, iconImage, description="", duration=""):
	url = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	li = xbmcgui.ListItem(label, iconImage="DefaultVideo.png", thumbnailImage=iconImage)
	li.setInfo(type="Video", infoLabels={"title": label, "plot": description, "duration": str(round(int(duration)/60,0))})
	if duration:
		li.addStreamInfo("video", {"duration": int(duration)})
	li.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=url, listitem=li, isFolder=False) 

def getShows():
	global thisPlugin
	page = loadPage(urlShows)
	soup = BeautifulSoup(page)
	featured_show = soup.find('li', 'overlay large')
	show_title = featured_show.find('h3').string
	split_link = featured_show.find('a')['href'].split('/')
	show_link = split_link[3] + "/altri-video/"
	show_thumbnail = baseUrl + featured_show.find('img')['src']
	addDirectoryItem(show_title, show_link, "show", show_thumbnail)
	alpha_shows = soup.findAll('div', 'allshows')
	for each_alpha in alpha_shows:
		shows_list = each_alpha.findAll('li')
		for show in shows_list:
			link = show.find('a')
			show_title = link.string
			show_link = link['href'] + "altri-video/"
			if isThumbnailsScanEnabled == "true":
				show_thumbnail = thumbnailsCache.cacheFunction(getShowThumbnail, urlShows + link['href'])
			else:
				show_thumbnail = ""
			addDirectoryItem(show_title, show_link, "show", show_thumbnail)
	xbmcplugin.addSortMethod(thisPlugin, xbmcplugin.SORT_METHOD_LABEL)
	xbmcplugin.endOfDirectory(thisPlugin)

def getShowThumbnail(link):
	page = loadPage(link)
	soup = BeautifulSoup(page)
	show_banner = soup.find('div', 'overlay extralarge')
	show_thumbnail = baseUrl + show_banner.find('img')['src']
	return show_thumbnail

def getEpisodes(link):
	global thisPlugin
	page = loadPage(urlShows + link + "?sort=date&lonform=")  
	soup = BeautifulSoup(page)
	episodes_list = soup.find('ol', 'list medium').findAll('li')
	previousPage = soup.find(title="Precedente")
	nextPage = soup.find(title="Successivo")
	if previousPage is not None:
		parsed_link = urlparse.urlparse(link)
		episode_link = parsed_link[0] + parsed_link[1] + parsed_link[2] + previousPage['href']
		addDirectoryItem("Precedenti", episode_link, "previous_page", "")
	for episode in episodes_list:
		episode_title = episode.find('h3').string
		episode_link = episode.find('a')['href']
		episode_thumbnail = episode.find('img')['src']
		episode_description = episode.find('p').string
		split_duration = episode.find('time').string.split(':')
		duration_in_seconds = int(split_duration[0])*60+int(split_duration[1])
		episode_duration = duration_in_seconds
		addLinkItem(episode_title, episode_link, "episode", episode_thumbnail, episode_description, episode_duration)
	if nextPage is not None:
		parsed_link = urlparse.urlparse(link)
		episode_link = parsed_link[0] + parsed_link[1] + parsed_link[2] + nextPage['href']
		addDirectoryItem("Successivi", episode_link, "next_page", "")
	xbmcplugin.endOfDirectory(thisPlugin)

def watchEpisode(link):
	page = loadPage(baseUrl + link)
	soup = BeautifulSoup(page)
	videoID = soup.find('param', {'name': '@videoPlayer'})['value']
	playBrightCoveStream(videoID)
	xbmc.sleep(int(autostartVideoInSeconds)*1000)
	xbmc.executebuiltin('XBMC.PlayerControl(Play)')

def playBrightCoveStream(videoID):
	playerID = const_playerID
	publisherID = const_publisherID
	const = const_str
	conn = httplib.HTTPConnection("c.brightcove.com")
	envelope = remoting.Envelope(amfVersion=3)
	envelope.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[const, playerID, videoID, publisherID], envelope=envelope)))
	conn.request("POST", "/services/messagebroker/amf?playerId=" + str(playerID), str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
	response = conn.getresponse().read()
	response = remoting.decode(response).bodies[0][1].body
	streamUrl = ""
	for item in sorted(response['renditions'], key=lambda item: item['encodingRate'], reverse=False):
		encRate = item['encodingRate']
		if encRate < videoMaxBitrate:
			streamUrl = item['defaultURL']
	if streamUrl.find("http://") == 0:
		listItem = xbmcgui.ListItem(path=streamUrl+"?videoId="+videoID+"&lineUpId=&pubId="+str(publisherID)+"&playerId="+str(playerID)+"&affiliateId=&v=&fp=&r=&g=")
	else:
		url = streamUrl[0:streamUrl.find("&")]
		playpath = streamUrl[streamUrl.find("&")+1:]
		listItem = xbmcgui.ListItem(path=url+"playpath="+playpath)
	xbmcplugin.setResolvedUrl(thisPlugin, True, listItem)

def getParams():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
                                
        return param

if not sys.argv[2]:
	getShows()
else:
	params = getParams()
	print params['mode']
	if params['mode'] == "show":
		getEpisodes(urllib.unquote(params['url']))
	elif params['mode'] == "episode":
		watchEpisode(urllib.unquote(params['url']))
	elif params['mode'] == "next_page":
		getEpisodes(urllib.unquote(params['url']))
	elif params['mode'] == "previous_page":
		getEpisodes(urllib.unquote(params['url']))
	else:
		getShows()
