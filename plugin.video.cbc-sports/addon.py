import xbmcaddon, urllib.request, urllib.parse, urllib.error, xbmcgui, xbmcplugin, urllib.request, urllib.error, urllib.parse, re, sys
from bs4 import BeautifulSoup
import html5lib
import json
from datetime import datetime, timedelta as td
import time


now = (str(datetime.utcnow() - td(hours=5)).split(' ')[0]).replace('-','/')
cbcnow = now.split('/')
now = cbcnow[1] + '/' + cbcnow[2] + '/' + cbcnow[0]

_addon = xbmcaddon.Addon()
_addon_path = _addon.getAddonInfo('path')
selfAddon = xbmcaddon.Addon(id='plugin.video.cbc-sports')
translation = selfAddon.getLocalizedString

defaultimage = 'special://home/addons/plugin.video.cbc-sports/resources/icon.png'
defaultfanart = 'special://home/addons/plugin.video.cbc-sports/resources/fanart.jpg'
defaultvideo = 'special://home/addons/plugin.video.cbc-sports/resources/icon.png'
defaulticon = 'special://home/addons/plugin.video.cbc-sports/resources/icon.png'
#baseurl = 'http://www.cbc.ca/sports'
baseurl = 'http://www.cbc.ca'
basefeed = 'http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?byGuid='
mp4base = 'http://main.mp4.cbc.ca/prodVideo/sports/'
#cbcfeedbase = 'http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?range=1-50&byCategoryIds='
cbcfeedbase = 'http://tpfeed.cbc.ca/f/ExhSPC/vms_5akSXx4Ng_Zn?range=1-'
cbcfeedbas2 = '&byCategoryIds='
cbcfeedpost = '&sort=pubDate|desc'
pluginhandle = int(sys.argv[1])
addon_handle = int(sys.argv[1])
confluence_views = [500,501,502,503,504,508]
plugin = 'CBC Sports'
notetime = int(xbmcaddon.Addon().getSetting('notetime')) * 1000


def CATEGORIES():
	dir30003 = translation(30003)
	dir30004 = translation(30004)
	dir30006 = translation(30006)
	dir30008 = translation(30008)
	hlimit = xbmcaddon.Addon().getSetting('hlimit')
	mlimit = xbmcaddon.Addon().getSetting('mlimit')
	alimit = xbmcaddon.Addon().getSetting('alimit')
	addDir(dir30003, 'http://www.cbc.ca/sports-content/v11/includes/json/schedules/broadcast_schedule.json', 1, defaultimage)
	addDir(dir30004, cbcfeedbase + hlimit + cbcfeedbas2 + '461602883775' + cbcfeedpost, 6, defaultimage)
	addDir(dir30006, cbcfeedbase + mlimit + cbcfeedbas2 + '461477443878' + cbcfeedpost, 6, defaultimage)
	addDir(dir30008, cbcfeedbase + alimit + cbcfeedbas2 + '461088323897' + cbcfeedpost, 6, defaultimage)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


#1
def INDEX(url):
	jresponse = urllib.request.urlopen(url)
	jdata = json.load(jresponse);i=0;n=0;pub=0
	item_dict = jdata
	llimit = xbmcaddon.Addon().getSetting('llimit')
	hnight = xbmcaddon.Addon().getSetting('hnight')
	pubevents = xbmcaddon.Addon().getSetting('pubevents')
	cbclog = int(xbmcaddon.Addon().getSetting('cbclog'))
	count = len(item_dict['schedule'])
	for item in jdata['schedule']:
		title = (jdata['schedule'][i]['ti'])
		if cbclog >= 1:
	    		xbmc.log('CBC Sports Index title: ' + str(title), xbmc.LOGINFO)
	    		xbmc.log('CBC Sports Index URL: ' + str(url), xbmc.LOGINFO)
		if cbclog == 2:
	    		xbmc.log('CBC Sports Index jdata: ' + str(jdata), xbmc.LOGINFO)
		onfirst = (jdata['schedule'][i]['on'][0])
		if 'Hockey Night' in title and hnight == 'false':
			i += 1
			continue
		if onfirst == 'tv':
			i += 1
			continue
		badurl = jdata['schedule'][i]['url']
		if '/sports' not in badurl and pubevents == 'true':
			title = title + '  [COLOR blue](Published)[/COLOR]'
			pub += 1
		etime = jdata['schedule'][i]['stt']
		sttime = jdata['schedule'][i]['end']
		if cbclog >= 1:
			xbmc.log('Live event title: ' + str(i), xbmc.LOGINFO)
		try:
			starttime = datetime.strptime(etime[:16],'%m/%d/%Y %H:%M')
			endtime = datetime.strptime(sttime[:16],'%m/%d/%Y %H:%M')
			iduration = (endtime - starttime).seconds
		except TypeError:         #  Python bug when trying to do strptime twice
			starttime = datetime(*(time.strptime(etime[:16],'%m/%d/%Y %H:%M')[0:6]))
			endtime = datetime(*(time.strptime(sttime[:16],'%m/%d/%Y %H:%M')[0:6]))
			iduration = (endtime - starttime).seconds
		#dtime = (etime.split(' ',1)[-1]).split(' ',1)[0]
		edate = etime.split(' ',1)[0]
		t1 = time.strptime(edate, "%m/%d/%Y")
		t2 = time.strptime(now, "%m/%d/%Y")		
		if t1 < t2:
			i += 1
			continue
		etime = etime.split(' ',1)[-1].upper()
		url = baseurl + jdata['schedule'][i]['url']
		if cbclog >= 1:
		    xbmc.log('Live event URL: ' + str(url), xbmc.LOGINFO)
		image = jdata['schedule'][i]['thumb']
		if edate == now:
			title = etime + ' - ' + title
		else:
			title = edate + ' - ' + etime + ' - ' + title
		i += 1				# track number of items iterated			
		if int(llimit) == 0 or n < int(llimit):
			addDir2(title, url, iduration, 2, image)
			n = n+1			#  track number of items displayed
		else:
			break
	if pubevents == 'true':
	    xbmc.log('CBC Sports live events published: ' + str(pub) + ' of ' + str(n) + ' events.', xbmc.LOGINFO)
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


#2
def IFRAME(name,url):
	cbclog = int(xbmcaddon.Addon().getSetting('cbclog'))
	if cbclog >= 1:
	    xbmc.log('CBC Sports Live Feed name: ' + str(name), xbmc.LOGINFO)
	    xbmc.log('CBC Sports URL: ' + str(url), xbmc.LOGINFO)
	if 'www.cbc.ca/sports' in url:		#  Check if valid URL is posted yet
	    xbmcgui.Dialog().notification(name, translation(30320), defaultimage, notetime, False)
	    return  
	rdata = str(get_html(url))
	#try: mediaId = re.compile("mediaId': '(.+?)'").findall(str(data))[0]
	if cbclog == 2:
	    xbmc.log('CBC Sports rdata: ' + str(rdata), xbmc.LOGINFO)

	try:					# primary mediaId parse
	    startpos = rdata.find('mediaId')
	    mediaId = rdata[startpos+8:startpos+21]
	except IndexError:             
	    xbmcgui.Dialog().notification(name, translation(30000), defaultimage, notetime, False)
	    return
	if cbclog >= 1:
	    xbmc.log('CBC Sports mediaId: ' + mediaId, xbmc.LOGINFO)

	try:					# primary mediaId verify int
	    mediaIdint = int(mediaId)
	except ValueError:			# alternate mediaId parse
	    altid_start = rdata.find('identifier')
	    mediaId = rdata[altid_start+13:altid_start+26]
	    if cbclog >= 1:
	        xbmc.log('CBC Sports alternate mediaId: ' + mediaId, xbmc.LOGINFO)

	try:					# alternate mediaId verify int
	    mediaIdint = int(mediaId)
	except ValueError:
	    xbmcgui.Dialog().notification(name, translation(30519), defaultimage, notetime, False)
	    return
	    
	furl = basefeed + mediaId
	jresponse = urllib.request.urlopen(furl)
	jdata = json.load(jresponse)
	if cbclog == 2:
	    xbmc.log('CBC Sports Live Schedule Playback response: ' + str(jdata), xbmc.LOGINFO)

	try:
	    smil_url = jdata['entries'][0]['content'][0]['url']
	except IndexError:             
	    xbmcgui.Dialog().notification(name, translation(30000), defaultimage, notetime, False)
	    if cbclog >= 1:
	        xbmc.log('CBC Sports Live Schedule entry count is 0 for event: ' + str(name), xbmc.LOGINFO)
	    return	

	smil = get_html(smil_url)
	contents = BeautifulSoup(smil,'html5lib')
	if cbclog >= 1:
	    xbmc.log('CBC Sports Live Schedule contents: ' + str(contents), xbmc.LOGINFO)
					
	if 'GeoLocationBlocked' in str(contents):		#  Check for blackout
	    xbmcgui.Dialog().notification(name, translation(30001), defaultimage, notetime, False)
	    return

	try:
		stream = (re.compile('video src="(.+?)"').findall(str(contents))[0]).replace('/z/','/i/').replace('manifest.f4m','master.m3u8')
	except IndexError:			#  Check if stream is available
		xbmcgui.Dialog().notification(name, translation(30000), defaultimage, notetime, False)
		return

	if cbclog >= 1:
	    xbmc.log('CBC Sports Live Schedule Playback stream: ' + str(stream), xbmc.LOGINFO)
	listitem = xbmcgui.ListItem(name)
	listitem.setArt({'thumb': defaultimage, 'icon': defaultimage})
	sdata = str(get_html(stream))

	try:
	    errfound = sdata.find('An error occurred')
	except IndexError:
            xbmcgui.Dialog().notification(name, translation(30010), defaultimage, notetime, False)
            return

	if errfound > -1:
		xbmcgui.Dialog().notification(name, translation(30010), defaultimage, notetime, False)
		return
	if cbclog >= 1:
	    xbmc.log('CBC Sports Live Schedule stream return data: ' + sdata, xbmc.LOGINFO)

	try:	
	    xbmc.Player().play( stream, listitem )
	except:              
	    xbmcgui.Dialog().notification(name, translation(30010), defaultimage, notetime, False)

	sys.exit()
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


#6
def VIDEOS(url):
	jresponse = urllib.request.urlopen(url)
	cbclog = int(xbmcaddon.Addon().getSetting('cbclog'))
	jdata = json.load(jresponse);i=0
	if cbclog >= 1:
	    xbmc.log('CBC Sports VIDEOS name: ' + str(url), xbmc.LOGINFO)
	if cbclog == 2:
	    xbmc.log('CBC Sports VIDEOS data ' + str(jdata), xbmc.LOGINFO)
	item_dict = jdata
	count = len(item_dict['entries'])
	for item in jdata['entries']:
		title = (jdata['entries'][i]['title'])
		url = jdata['entries'][i]['content'][0]['url']
		image = jdata['entries'][i]['defaultThumbnailUrl']
		vduration = int(jdata['entries'][i]['content'][0]['duration'])
		pubDate = jdata['entries'][i]['pubDate']
		aired = datetime.fromtimestamp(pubDate / 1000).strftime('%Y-%m-%d')
		plot = jdata['entries'][i]['description']
		vheight = int(jdata['entries'][i]['content'][0]['height'])
		vwidth = int(jdata['entries'][i]['content'][0]['width'])
		#xbmc.log('CBC Sports Live Schedule stream aired ' + aired, xbmc.LOGINFO)
		#xbmc.log('CBC Sports Live Schedule stream dplot ' + plot, xbmc.LOGINFO)
		#xbmc.log('CBC Sports Video height and width: ' + str(vheight) + ' '  + str(vwidth), xbmc.LOGINFO)
		addDir2(title, url, vduration, 7, image, aired, plot, vheight, vwidth);i=i+1
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
		

#7
def GET_STREAM(name,url):
	cbclog = int(xbmcaddon.Addon().getSetting('cbclog'))
	if cbclog >= 1:
	    xbmc.log('CBC Sports GET_STREAM name: ' + str(name), xbmc.LOGINFO)
	    xbmc.log('CBC Sports URL: ' + str(url), xbmc.LOGINFO)
	smil = get_html(url)
	contents = BeautifulSoup(smil,'html5lib')
	if cbclog >= 1:
	    xbmc.log('CBC Sports GET_STREAM contents: ' + str(contents), xbmc.LOGINFO)
	if 'GeoLocationBlocked' in str(contents):		#  Check for blackout
	    xbmcgui.Dialog().notification(name, translation(30001), defaultimage, notetime, False)
	    return
	stream = (re.compile('src="(.+?)"').findall(str(contents))[0])
	if mp4base not in stream:
		#stream = mp4base + stream
		stream = stream
	listitem = xbmcgui.ListItem(name)
	listitem.setArt({'thumb': defaultimage, 'icon': defaultimage})
	if cbclog >= 1:
	    xbmc.log('CBC Sports Live Schedule Playback stream: ' + str(stream), xbmc.LOGINFO)
	xbmc.Player().play( stream, listitem )
	sys.exit()
	xbmcplugin.endOfDirectory(int(sys.argv[1]))


#99
def play(url):
	item = xbmcgui.ListItem(path=url)
	return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def striphtml(data):
	p = re.compile(r'<.*?>')
	return p.sub('', data)


def sanitize(data):
	output = ''
	for i in data:
		for current in i:
			if ((current >= '\x20') and (current <= '\xD7FF')) or ((current >= '\xE000') and (current <= '\xFFFD')) or ((current >= '\x10000') and (current <= '\x10FFFF')):
			   output = output + current
	return output



def get_html(url):
	req = urllib.request.Request(url)
	req.add_header('User-Agent','User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:44.0) Gecko/20100101 Firefox/44.0')

	try:
		response = urllib.request.urlopen(req)
		code = response.getcode()
		cbclog = int(xbmcaddon.Addon().getSetting('cbclog'))
		if cbclog >= 1:
			xbmc.log('CBC Sports get_html code: ' + str(code), xbmc.LOGINFO)
		if code == 403:              
			xbmcgui.Dialog().notification(name, translation(30001), defaultimage, notetime, False)
			sys.exit()
		elif code == 22:              
			xbmcgui.Dialog().notification(name, translation(30010), defaultimage, notetime, False)
			sys.exit()	    
		html = response.read()
		response.close()
	except urllib.error.URLError:              
		xbmcgui.Dialog().notification(name, translation(30010), defaultimage, notetime, False)
		sys.exit()	 
	return html


def get_params():
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


def addDir(name, url, mode, iconimage, fanart=False, infoLabels=True):
	u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.parse.quote_plus(name) + "&iconimage=" + urllib.parse.quote_plus(iconimage)
	ok = True
	liz = xbmcgui.ListItem(name)
	liz.setInfo(type="Video", infoLabels={"Title": name})
	liz.setProperty('IsPlayable', 'true')
	if not fanart:
		fanart=defaultfanart
	liz.setArt({'thumb': iconimage, 'icon': iconimage, 'fanart': fanart})	
	ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
	return ok


def addDir2(name,url,duration,mode,iconimage, aired=False, plot=False, vheight=False, vwidth=False, fanart=False, infoLabels=False):
	u=sys.argv[0]+"?url="+urllib.parse.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.parse.quote_plus(name)
	ok=True
	liz = xbmcgui.ListItem(name)
	plot_text = ''
	if plot:
	    plot_text = plot
	else:
	    plot_text = name
	aired_text = ''
	if aired:
            aired_text = aired
	infoLabels={ "Title": name,
             "Aired": aired_text,
             "Year": aired_text.split('-',1)[0],
             "mediatype": 'episode',
             "Duration": duration,
             "Plot": plot_text }
	liz.setInfo( "video", infoLabels)	
	fanart=defaultfanart
	liz.setArt({'thumb': iconimage, 'icon': iconimage, 'fanart': fanart})
	if vheight and vwidth:
		aspect = float(float(vwidth) / float(vheight))
		video_info = {
			'aspect': aspect,
			'width': vwidth,
			'height': vheight,
			}
		liz.addStreamInfo('video', video_info)
	menuitem1 = translation(30011)
	menuitem2 = translation(30012)
	liz.addContextMenuItems([ (menuitem1, 'Container.Refresh'), (menuitem2, 'Action(ParentDir)')])
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
	return ok


def unescape(s):
	p = htmllib.HTMLParser(None)
	p.save_bgn()
	p.feed(s)
	return p.save_end()	


params = get_params()
url = None
name = None
mode = None
cookie = None

try:
	url = urllib.parse.unquote_plus(params["url"])
except:
	pass
try:
	name = urllib.parse.unquote_plus(params["name"])
except:
	pass
try:
	mode = int(params["mode"])
except:
	pass


if mode == None or url == None or len(url) < 1:
	CATEGORIES()
elif mode == 1:
	INDEX(url)
elif mode == 2:
	IFRAME(name,url)
elif mode == 6:
	VIDEOS(url)
elif mode == 7:
	GET_STREAM(name,url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
