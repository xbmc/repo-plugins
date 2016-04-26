import sys, xbmc, xbmcgui, xbmcplugin, urllib, urllib2, urlparse, re, string, os, traceback, time, datetime, xbmcaddon
import simplejson as json

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
	f.close()
	return data

def openXml(url):
	req = urllib2.Request(url, None, {'user-agent':'Mozilla/Firefox'})
	opener = urllib2.build_opener()
	data = opener.open(req)
	return data

def main():

	addXBMCItem (__language__(30000), os.path.join(__thumbpath__, 'newest.png'), "?mode=getNewest&channel=catchup-listing", True)
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
		li=xbmcgui.ListItem (name)
		li.setProperty('Fanart_Image', Fanart_Image)
		li.setArt({'thumb': thumbnail, 'poster': thumbnail})
		u=sys.argv[0]+action_url
	else:
		li=xbmcgui.ListItem(name)
		li.setInfo( type="Video", infoLabels=infoLabels )
		li.setArt({'thumb': thumbnail, 'poster': thumbnail})
		li.setProperty('IsPlayable', 'true')
		u=action_url

	xbmcplugin.addDirectoryItem(addon_handle,u,li,isFolder)

def channelShows(channel, page=0):
	if channel == "channel5":
		geturl = "http://tv.toggle.sg/en/blueprint/servlet/toggle/bandlist?id=5211104&navigationId=5006598&channelId=331441&pageIndex="
	elif channel == "channel8":
		geturl = "http://tv.toggle.sg/en/blueprint/servlet/toggle/bandlist?id=5183464&navigationId=5006610&channelId=331442&pageIndex="
	elif channel == "channelu":
		geturl = "http://tv.toggle.sg/en/blueprint/servlet/toggle/bandlist?id=5184730&navigationId=5006618&channelId=331443&pageIndex="
	elif channel == "suria":
		geturl = "http://tv.toggle.sg/en/blueprint/servlet/toggle/bandlist?id=5185064&navigationId=5006594&channelId=331445&pageIndex="
	elif channel == "vasantham":
		geturl = "http://tv.toggle.sg/en/blueprint/servlet/toggle/bandlist?id=5185200&navigationId=5006602&channelId=331446&pageIndex="
	elif channel == "okto":
		geturl = "http://tv.toggle.sg/en/blueprint/servlet/toggle/bandlist?id=5184922&navigationId=5006614&channelId=331444&pageIndex="
	geturl = geturl+str(page)+"&pageSize=18&isPortrait=0&sortBy=START_DATE&filterJson=%7B%7D&filterText"
	data=openUrl(geturl)
	showlist  = re.compile('img src="(.*?)".+?a href="(.+?)">(.+?)<\/a>').findall(data)

	for image, url, show in showlist:
		if "http" not in image:
			image = "http://tv.toggle.sg" + image
		addXBMCItem (htmlParse(show), image, "?mode=getEpisodes&channel="+channel+"&show="+show+"&tab="+url+"&page=0", True)

	pagination = re.compile ('pagination\'\),(.+?), (.+?), paginateLabel').search(data)
	current_page = int( pagination.group (1) )
	max_page = int ( pagination.group (2) )
	if current_page < max_page:
		page = str(current_page + 1)
		addXBMCItem (__language__(31000), "", "?mode=loadChannel&channel="+channel+"&page="+page, True)

	xbmc.executebuiltin("Container.SetViewMode(500)")

def newestToggle(channel):
	data=openUrl("http://video.toggle.sg/en/%s" % channel)
	showlist  = re.compile('srcset="(.+?)".+?href="(.+?)">(.+?)<').findall(data)

	for image, url, show in showlist:
		if "http" not in image:
			image = "http://video.toggle.sg" + image
		u=sys.argv[0]+"?mode=resolveMSN&url="+urllib.quote_plus(url)
		addXBMCItem (htmlParse(show), image, u, False, infoLabels="")

	xbmc.executebuiltin("Container.SetViewMode(500)")

def channelYoutube(user):
	if user == "channelnewsasia":
		infoLabels={ "Title": "CNA @ Live Broadcast" }
		addXBMCItem ("CNA @ Live Broadcast", os.path.join(__thumbpath__, 'cna.png'), 'http://cna_hls-lh.akamaihd.net/i/cna_en@8000/index_584_av-b.m3u8?sd=10&dw=50&rebase=on&e=870c0c22a42f4c5a', False, infoLabels=infoLabels)

	youtube_url = "https://www.youtube.com/feeds/videos.xml?user=" + user
	xbmc.log (youtube_url, xbmc.LOGNOTICE)
	data = openUrl (youtube_url)

	showlist  = re.compile('<media\:title>(.+?)<.+?\/v\/(.+?)\?.+?url="(.+?)".+?description>(.+?)<').findall(data)

	for title, url, image, desc in showlist:
		infoLabels=	{
					"title": title,
					"plot": htmlParse(desc),
					}
		addXBMCItem (title, image, "plugin://plugin.video.youtube/?path=root/video&action=play_video&videoid=" + url, False, infoLabels=infoLabels)

def resolveVimeo(url):

	videodata=openUrl(url)
	print url
	print "HELLO_WORLD"
	match=re.compile('width":(.+?),.+?url":"(.+?)"').findall(videodata)
	x=0
	for bitrate, url_quality in match:
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

def getEpisodes(channel, show, tab, page):
	data=openUrl(tab + "/episodes")
	meta = re.compile('10, 0,  (.+?), (.+?), (.+?)\);',re.DOTALL).search(data)
#	print meta.group(1)
#	print meta.group(2)
#	print meta.group(3)
	data = openUrl ("http://tv.toggle.sg/en/blueprint/servlet/toggle/paginate?pageSize=10&pageIndex="+str(page)+"&contentId="+meta.group(1)+"&navigationId="+meta.group(2)+"&"+meta.group(3)+"=1")

	episodechunk  = re.compile('<li>(.*?)<\/li>').findall(data)

	for chunk in episodechunk:
		episodelist = re.compile('img src="(.+?)".+?.+?item__tags(.+?)<\/div>.+?href="(.+?)">(.+?)<\/a>.+?<p>(.+?)<\/p>').search(chunk)
		try:
			vip_status = episodelist.group(2)
			if "vip" not in vip_status:
				episode_url = episodelist.group(3)
				title = episodelist.group(4)
				desc = episodelist.group(5)
				image = episodelist.group(1)
				infoLabels={'Title': title}
				infoLabels=	{
					"title": title,
					"plot": desc,
					}
				u=sys.argv[0]+"?mode=resolveMSN&url="+urllib.quote_plus(episode_url)
				addXBMCItem (title, image, u, False, infoLabels=infoLabels)
		except:
			print "No file found"
			print episodelist
	pagination = re.compile ('pagination\'\),(.+?), (.+?), paginateLabel').search(data)
	current_page = int( pagination.group (1) )
	max_page = int ( pagination.group (2) )
	if current_page < max_page:
		page = str(current_page + 1)
		addXBMCItem (__language__(31000), "", "?mode=getEpisodes&channel="+channel+"&show="+show+"&tab="+tab+"&page="+page, True)

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
	id = url.split("/")[-1]

	progress.update(25, __addonname__, __language__(31002))

	vid_url = "http://toggleplayer-1410100339.ap-southeast-1.elb.amazonaws.com/v0.30/mwEmbed/mwEmbedFrame.php?&wid=_27017&uiconf_id=8413350&entry_id="+id+"&flashvars[ks]=0&flashvars[logo]=undefined&flashvars[toggle.sgPlus]=false&flashvars[vast]=%7B%22htmlCompanions%22%3A%22video-companion-ad-320-100-in-flash%3A320%3A100%22%7D&flashvars[multiDrm]=%7B%22plugin%22%3Atrue%2C%22isClear%22%3Atrue%7D&flashvars[localizationCode]=en&flashvars[autoPlay]=true&flashvars[proxyData]=%7B%22initObj%22%3A%7B%22Locale%22%3A%7B%22LocaleLanguage%22%3A%22%22%2C%22LocaleCountry%22%3A%22%22%2C%22LocaleDevice%22%3A%22%22%2C%22LocaleUserState%22%3A0%7D%2C%22Platform%22%3A0%2C%22SiteGuid%22%3A0%2C%22DomainID%22%3A%220%22%2C%22UDID%22%3A%22%22%2C%22ApiUser%22%3A%22tvpapi_147%22%2C%22ApiPass%22%3A%2211111%22%7D%2C%22MediaID%22%3A%22"+id+"%22%2C%22iMediaID%22%3A%22"+id+"%22%2C%22picSize%22%3A%22640X360%22%7D&playerId=SilverlightContainer&forceMobileHTML5=true&urid=2.29.1.10&callback="

	html=openUrl(vid_url)
	print vid_url
	progress.update(50, __addonname__, __language__(31003)) # Progress
	html = re.compile('kalturaIframePackageData = (.+?)};',re.DOTALL).search(html).group(1)
	html = html+'}'
	html = html.replace('\\','')
	a = json.loads(html)
	a = a['entryResult']['meta']
	options = a['partnerData']['Files']
	u =''
	for option in options:
		print option['URL']
		if "mp4" in option['URL'] or "MP4" in option['URL']:
			if "http" in option['URL']:
				u = option['URL']
				break

	if u == "":
		for option in options:
			if option['Format'] == 'STB Main':
				u = option['URL']
				break

			if option['Format'] == 'Android':
				u = option['URL']
				break

			if option['Format'] == 'iPhone Main':
				u = option['URL']
				break

	progress.update(70, __addonname__, __language__(31003))
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xbmcgui.ListItem(path = u))

	progress.update(99, __addonname__,  __language__(31004)) # Ready to Play
	progress.close()

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
	try:
		page = args['page'][0]
	except:
		page = 0
	channelShows(channel, page)
elif mode[0] =='getNewest':
	channel = args['channel'][0]
	newestToggle(channel)
elif mode[0]=='loadViddsee':
	page = args['page'][0]
	type = args['type'][0]
	channelViddsee(page, type)
elif mode[0]=='getEpisodes':
	channel = args['channel'][0]
	show = args['show'][0]
	tab = args['tab'][0]
	page = args['page'][0]
	getEpisodes(channel, show, tab, page)
elif mode[0]=='resolveMSN':
	url = args['url'][0]
	resolveMSN(url)
elif mode[0]=='resolveVimeo':
	url = args['url'][0]
	resolveVimeo(url)

xbmcplugin.endOfDirectory(addon_handle)
