import sys, xbmc, xbmcgui, xbmcplugin, urllib, urllib2, urlparse, re, string, os, traceback, time, datetime, xbmcaddon

import simplejson as json
import brightcove

# GadgetReactor
# http://www.gadgetreactor.com/portfolio/sgtv

__addon__	      = xbmcaddon.Addon('plugin.video.sgtv')
__addonname__ = __addon__.getAddonInfo('name')
__language__  = __addon__.getLocalizedString
__thumbpath__ = os.path.join( __addon__.getAddonInfo( 'path' ), 'resources', 'media')

def openUrl(url):
	retries = 0
	while retries < 2:
		try:
			req = urllib2.Request(url.encode('utf-8'), None, {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'})
			content = urllib2.urlopen(req)
			if content.info().getheader('Content-Encoding') == 'gzip':
				buf = StringIO( content.read())
				f = gzip.GzipFile(fileobj=buf)
				data = f.read()
			else:
				data=content.read()
			content.close()
			data = str(data).replace('\n','')
			return data
			
		except urllib2.HTTPError,e:
			if e.code == 500:
				dialog = xbmcgui.Dialog()
				ok = dialog.ok(__addon__, __language__(32000))
				main()
			retries += 1
			time.sleep(2)
			continue
		else:
			break


def openJson(url):
	req = urllib2.Request(url, None, {'user-agent':'Mozilla/Firefox'})
	opener = urllib2.build_opener()
	f = opener.open(req)
	data = json.load(f)	
	return data
	
def main():
	
	addXBMCItem (__language__(30000), os.path.join(__thumbpath__, 'newest.png'), "?mode=getEpisodes&channel=new&show=all", True)
	addXBMCItem (__language__(30001), os.path.join(__thumbpath__, 'channel5.jpg'), "?mode=loadChannel&channel=channel5", True)
	addXBMCItem (__language__(30002), os.path.join(__thumbpath__, 'channel8.jpg'), "?mode=loadChannel&channel=channel8", True)
	addXBMCItem (__language__(30003), os.path.join(__thumbpath__, 'channelu.jpg'), "?mode=loadChannel&channel=channelu", True)
	addXBMCItem (__language__(30004), os.path.join(__thumbpath__, 'cna.png'), "?mode=loadYoutube&user=channelnewsasia", True)
	addXBMCItem (__language__(30005), os.path.join(__thumbpath__, 'okto.png'), "?mode=loadChannel&channel=okto", True)
	addXBMCItem (__language__(30006), os.path.join(__thumbpath__, 'suria.gif'), "?mode=loadChannel&channel=suria", True)
	addXBMCItem (__language__(30007), os.path.join(__thumbpath__, 'vasantham.jpg'), "?mode=loadChannel&channel=vasantham", True)
	addXBMCItem (__language__(30008), os.path.join(__thumbpath__, 'viddsee.png'), "?mode=loadViddsee&page=0&type=popular", True)
	addXBMCItem (__language__(30009), os.path.join(__thumbpath__, 'wahbanana.jpg'), "?mode=loadYoutube&user=wahbanana", True)
	xbmc.executebuiltin("Container.SetViewMode(500)")
	
def addXBMCItem(name, thumbnail, action_url, isFolder, Fanart_Image=None, infoLabels=None):
	if isFolder:
		li=xbmcgui.ListItem (name,iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
		li.setProperty('Fanart_Image', Fanart_Image)
		u=sys.argv[0]+action_url
	else:
		li=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
		li.setInfo( type="Video", infoLabels=infoLabels )
		li.setProperty('IsPlayable', 'true')
		u=action_url		
	if Fanart_Image is not None:
		li.setProperty('Fanart_Image', Fanart_Image)
		
	xbmcplugin.addDirectoryItem(addon_handle,u,li,isFolder)
	

def channelShows(channel):
	data=openUrl("http://xin.msn.com/en-sg/video/catchup/")		
	showlist  = re.compile('<div data-tabkey="tab-(\d+)".*?homepage\|%s\|tab\|(.*?)\|.+?:&quot;(.+?)&quot' % (channel)).findall(data)

	for tab, show, thumb in showlist:
		image = 'http:'+ thumb.replace('&amp;','&')
		addXBMCItem (htmlParse(show), image, "?mode=getEpisodes&channel="+channel+"&show="+show+"&tab=tab-"+tab, True)

	xbmc.executebuiltin("Container.SetViewMode(500)")

def channelYoutube(user):
	if user == "channelnewsasia":
		infoLabels={ "Title": "CNA @ Live Broadcast" }
		addXBMCItem ("CNA @ Live Broadcast", os.path.join(__thumbpath__, 'cna.png'), 'http://cna_hls-lh.akamaihd.net/i/cna_en@8000/index_584_av-b.m3u8?sd=10&dw=50&rebase=on&e=870c0c22a42f4c5a', False, infoLabels=infoLabels)	
	
	youtube_url = "http://gdata.youtube.com/feeds/api/users/" + user + "/uploads?v=2&alt=json"
	data = openJson (youtube_url)
		
	for entry in data["feed"]["entry"]:
		title = entry["title"]["$t"]
		video_id = entry["media$group"]["yt$videoid"]["$t"]
		desc = entry["media$group"]["media$description"]["$t"]
		image = "http://img.youtube.com/vi/" + video_id + "/0.jpg"
		infoLabels={ "Title": title , "Plot" : desc }
		addXBMCItem (title, image, "plugin://plugin.video.youtube/?path=root/video&action=play_video&videoid=" + video_id, False, infoLabels=infoLabels)

	try: 
		i = data["feed"]["openSearch$startIndex"]["$t"]
		max = data["feed"]["openSearch$totalResults"]["$t"]
	except:
		i = max = 0
		
def resolveVimeo(url):

	videodata=openUrl(url)
	match=re.compile('"profile".+?"url":"(.+?)",.+?bitrate":(.+?),"').findall(videodata)
	x=0
	for url_quality, bitrate in match:
		if int(bitrate) > x: 
			video_url=url_quality
			x=int(bitrate)	
	listitem = xbmcgui.ListItem(path=video_url)
	listitem.setInfo(type='Video', infoLabels= xbmc.getInfoLabel("ListItem.InfoLabel"))
	xbmcplugin.setResolvedUrl(addon_handle, succeeded=True, listitem=listitem)

def channelViddsee(page, type):
#	type examples: | popular | genre/drama | genre/comedy |  
	viddsee_url = "https://www.viddsee.com/v1/browse/"+type+"?current_page="+page+"&per_page=12"
	data = openJson(viddsee_url)
	
	for video in data["videos"]:		
		infoLabels=	{
					"title": video["title"], 
					"plot": htmlParse(video["description_long"]),
					"plotoutline": video["description_short"],
					"genre": video["genres"],
					"year": video["year"],
					"votes": video["rating"]["ext_likes"],
					"rating": video["rating"]["rating_like"],
					"duration": video["duration"],													
					}
		video_url = video["embed_url"];		
		if "vimeo" in video_url:
			u=sys.argv[0]+"?mode=resolveVimeo&url="+urllib.quote_plus(video_url)
		elif "youtube" in video_url:
			video_url = video_url.split('embed/')[1]
			u="plugin://plugin.video.youtube/?path=root/video&action=play_video&videoid=" + video_url
		else:
			u = ""
		addXBMCItem (video["title"], video["thumbnail_url"], u, False, video["photo_large_url"], infoLabels)			
		
	page = str(int(page)+1)
	addXBMCItem (__language__(31000), os.path.join(__thumbpath__, "viddsee.png"), "?mode=loadViddsee&page="+page+"&type="+type, True)	
	
def getEpisodes(channel, show, tab):
	data=openUrl("http://xin.msn.com/en-sg/video/catchup/")

	if "new" in channel:
		episodelist = re.compile('<li.+?href="(.+?)".+?:&quot;(.+?)&quot.+?<h4>(.+?)</h4>.+?"duration">(.+?)<.+?</li>').findall(data)	

	else:
		episodechunk  = re.compile('class="section tabsection horizontal".+?data-section-id="%s".+?<div data-tabkey="%s"(.+?)</ul>' % (channel, tab)).search(data).group(1)
		episodelist = re.compile('<li.+?href="(.+?)".+?:&quot;(.+?)&quot.+?<h4>(.+?)</h4>.+?"duration">(.+?)<.+?</li>').findall(episodechunk)

	for episode_url, thumb, title, time in episodelist:
		episode_url = "http://xin.msn.com" + episode_url
		title=htmlParse(title)									
		
		image = 'http:'+ thumb.replace('&amp;','&')
		infoLabels={'Title': title, 'Duration':time}
		u=sys.argv[0]+"?mode=resolveMSN&url="+urllib.quote_plus(episode_url)
		addXBMCItem (title, image, u, False, infoLabels=infoLabels)	
		
	xbmc.executebuiltin("Container.SetViewMode(500)")	

def htmlParse(str):
	str=str.replace('\\x3a', ':')
	str=str.replace('\\x2f', '/')	
	str=re.sub('&amp;','&',str)
	str=re.sub('&#39;',"'",str)
	str=str.replace('&quot;', '"')
	str=str.replace('&#187;', '-')
	str=str.replace('&#160;', ':')
	str=re.sub(r'<.*?>','', str)
	return str
			
def resolveMSN(url):
	progress = xbmcgui.DialogProgress()
	progress.create("SG!TV", __language__(31002)) # Finding Link
	progress.update(25, __addonname__, __language__(31002))
	videodata=openUrl(url)
	match=re.compile("{&quot;formatCode&quot;:&quot;(...)&quot;,&quot;url&quot;:&quot;(.+?)&quot;,").findall(videodata)
	progress.update(50, __addonname__, __language__(31003)) # Progress
	x=0
	for formatcode, url_quality in match:
		if int(formatcode) > x: 
			video_url=url_quality
			x=int(formatcode)
	progress.update(70, __addonname__, __language__(31003))
	#
	#for brightcove media, big thanks to Scotty Roscoe
	#
	html=videodata.replace('\r','').replace("&#39;","'").replace('&quot;','"')
	if 'brightcove' in html:
		blob = re.compile('<div class="wcvideoplayer" data-adpagegroups=(.+?)</div>').search(html).group(1)
		videoId = re.compile('"providerId":"(.+?)"').search(blob).group(1)
		video_url = brightcove.getBrightCoveUrl(videoId)
	
	video_url=htmlParse(video_url)
	listitem = xbmcgui.ListItem(path=video_url)
	listitem.setInfo(type='Video', infoLabels= xbmc.getInfoLabel("ListItem.InfoLabel"))

	progress.update(99, __addonname__,  __language__(31004)) # Ready to Play
	progress.close()
	
	xbmcplugin.setResolvedUrl(addon_handle, succeeded=True, listitem=listitem)
	
args = urlparse.parse_qs(sys.argv[2][1:])

mode = args.get('mode', None)
addon_handle = int(sys.argv[1])
xbmcplugin.setContent(addon_handle, 'tvshows')

if mode==None:
	name = 'Channels'
	main()
elif mode[0]=='loadYoutube':
	user = args['user'][0]
	channelYoutube(user)
elif mode[0] =='loadChannel':
	channel = args['channel'][0]
	channelShows(channel)
elif mode[0]=='loadViddsee':
	page = args['page'][0]
	type = args['type'][0]
	channelViddsee(page, type)
elif mode[0]=='getEpisodes':
	channel = args['channel'][0]
	show = args['show'][0]
	tab = args['tab'][0]
	getEpisodes(channel, show, tab)	
elif mode[0]=='resolveMSN':
	url = args['url'][0]
	resolveMSN(url)
elif mode[0]=='resolveVimeo':
	url = args['url'][0]
	resolveVimeo(url)
	
xbmcplugin.endOfDirectory(addon_handle)
