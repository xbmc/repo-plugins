#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import re
import os
import json as _json
import time
import socket
import HTMLParser
import urllib
import urllib2
import datetime
import xbmcplugin
import xbmcgui
import xbmcaddon
import xml.etree.ElementTree as ET
from random import randint

addonID = 'plugin.video.southpark_unofficial'
addon = xbmcaddon.Addon(id=addonID)
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
icon = xbmc.translatePath('special://home/addons/'+addonID+'/icon.png')
defaultFanart = xbmc.translatePath('special://home/addons/'+addonID+'/fanart.jpg')
defaultImgDir = xbmc.translatePath('special://home/addons/'+addonID+'/imgs/')
forceViewMode = True
audio_pos = int(addon.getSetting('audio_lang'))
playrandom = addon.getSetting('playrandom') == "true"
audio = ["en","es","de"]
audio = audio[audio_pos]
mainweb_geo = ["southpark.cc.com","southpark.cc.com","www.southpark.de"]
fullep_geo = ["/full-episodes/","/episodios-en-espanol/","/alle-episoden/"]
pageurl_geo = ["southparkstudios.com","southparkstudios.com","southpark.de"]
mediagen_geo = ["player","player","video-player"]
rtmp_geo = ["rtmpe://viacommtvstrmfs.fplive.net:1935/viacommtvstrm","rtmpe://viacommtvstrmfs.fplive.net:1935/viacommtvstrm","rtmpe://cp75298.edgefcs.net/ondemand"]
mediagenopts_geo = ["&suppressRegisterBeacon=true&lang=","&suppressRegisterBeacon=true&lang=","&device=Other&aspectRatio=16:9&lang="]
geolocation_pos = int(addon.getSetting('geolocation'))
geolocation = ["US","UK","ES","DE","IT"]
geolocation = geolocation[geolocation_pos]
cc_settings = addon.getSetting('cc') == "true"
viewMode = str("504")
addonpath = xbmc.translatePath('special://temp/temp')
if not os.path.isdir(addonpath):
	os.mkdir(addonpath, 0755)


def index():
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    content = ""
    content = getUrl("http://"+mainweb_geo[audio_pos])
    if "/messages/geoblock/" in content or "/geoblock/messages/" in content:
        notifyText(translation(30002), 7000)
	
    addDir(translation(30005), "Featured", 'list', icon)
    addLink(translation(30006), "Random", 'list', icon)
    addLink(translation(30013), "Search", 'list', icon)
    for i in range(1, 20):
        addDir(translation(30007)+" "+str(i), str(i), 'list', defaultImgDir+str(i)+".jpg")
    xbmcplugin.endOfDirectory(pluginhandle)


def list(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    if url == "Featured":
        jsonrsp = getUrl(getCarousel())
        promojson = _json.loads(jsonrsp)
        for episode in promojson['results']:
            if episode['_availability'] == "banned":
				addLink(episode['title'] + " [Banned]" , "banned", 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
            elif episode['_availability'] == "beforepremiere":
				addLink(episode['title'] + " [Premiere]", "beforepremiere", 'play', episode['images'], "Premiere in " + getTimer(episode['originalAirDate']) +"\n" + episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
            else:
				addLink(episode['title'], episode['itemId'], 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
    elif url == "Random":
		notifyText(translation(30003), 2000)
		rand = getUrl("http://"+mainweb_geo[audio_pos]+fullep_geo[audio_pos]+"random")
		rand = rand.split("<link rel=\"canonical\" href=\"")[1].split("\" />")[0]
		where = "http://"+mainweb_geo[audio_pos]+fullep_geo[audio_pos]+"s"
		rand = rand.split(where)[1].split("-")[0]
		rand = rand.split("e")
		if audio == "de":
			# sp.de returns a JS instead of a JSON so i need to convert it
			jsonrsp = getUrl("http://www.southpark.de/feeds/carousel/video/e3748950-6c2a-4201-8e45-89e255c06df1/30/1/json/!airdate/season-"+str(int(rand[0]))).decode('utf-8')
			#jsonrsp = JStoJSON(jsonrsp)
			#jsonrsp = toUSJSON(jsonrsp)
		else:
			# cc.com is the ony one with jsons so descriptions will be in english
			jsonrsp = getUrl("http://southpark.cc.com/feeds/carousel/video/06bb4aa7-9917-4b6a-ae93-5ed7be79556a/30/1/json/!airdate/season-"+str(int(rand[0]))+"?lang="+audio)
		seasonjson = _json.loads(jsonrsp)
		ep = int(rand[1])-1
		episode = seasonjson['results'][ep]
		if playrandom:
			if episode['_availability'] == "banned":
				episode = seasonjson['results'][0]
			playEpisode(episode['itemId'], episode['title'], episode['images'])
		else:
			if episode['_availability'] == "banned":
				addLink(episode['title'] + " [Banned]" , "banned", 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
			elif episode['_availability'] == "beforepremiere":
				addLink(episode['title'] + " [Premiere]", "beforepremiere", 'play', episode['images'], "Premiere in " + getTimer(episode['originalAirDate']) +"\n" + episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
			else:
				addLink(episode['title'], episode['itemId'], 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
    elif url == "Search":
		keyboard = xbmc.Keyboard('')
		keyboard.doModal()
		if (keyboard.isConfirmed()):
			text = keyboard.getText().lower()
			jsonrsp = getUrl("http://southpark.cc.com/feeds/carousel/search/81bc07c7-07bf-4a2c-a128-257d0bc0f4f7/14/1/json/" + text.replace(' ', '+'))
			xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)
			seasonjson = _json.loads(jsonrsp)
			for episode in seasonjson['results']:
				if episode['_availability'] == "banned":
					addLink(episode['title'] + " [Banned]" , "banned", 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
				elif episode['_availability'] == "beforepremiere":
					addLink(episode['title'] + " [Premiere]", "beforepremiere", 'play', episode['images'], "Premiere in " + getTimer(episode['originalAirDate']) +"\n" + episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
				else:
					addLink(episode['title'], episode['itemId'], 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
    else:
        xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_EPISODE)
        if audio == "de":
			jsonrsp = getUrl("http://www.southpark.de/feeds/carousel/video/e3748950-6c2a-4201-8e45-89e255c06df1/30/1/json/!airdate/season-"+url).decode('utf-8')
			#jsonrsp = JStoJSON(jsonrsp)
			#jsonrsp = toUSJSON(jsonrsp)
        else:
			jsonrsp = getUrl("http://southpark.cc.com/feeds/carousel/video/06bb4aa7-9917-4b6a-ae93-5ed7be79556a/30/1/json/!airdate/season-"+url+"?lang="+audio)
        seasonjson = _json.loads(jsonrsp)
        for episode in seasonjson['results']:
            if episode['_availability'] == "banned":
				addLink(episode['title'] + " [Banned]" , "banned", 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
            elif episode['_availability'] == "beforepremiere":
				addLink(episode['title'] + " [Premiere]", "beforepremiere", 'play', episode['images'], "Premiere in " + getTimer(episode['originalAirDate']) +"\n" + episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
            else:
				addLink(episode['title'], episode['itemId'], 'play', episode['images'], episode['description'], episode['episodeNumber'][0]+episode['episodeNumber'][1], episode['episodeNumber'][2]+episode['episodeNumber'][3],episode['originalAirDate'])
    xbmcplugin.endOfDirectory(pluginhandle)
    xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def playEpisode(url, title, thumbnail):
	if url == "banned":
		notifyText(translation(30011), 7000)
		return
	elif url == "beforepremiere":
		notifyText(translation(30014), 7000)
		return
	mediagen = getMediagen(url)
	if len(mediagen) == 0:
		notifyText(translation(30011), 7000)
		return
	notifyText(translation(30009) + " " + encode(title), 3000)
	rtmp = ""
	pageUrl = "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.11.3.swf?uri=mgid:arc:episode:"+pageurl_geo[audio_pos]+":"+url
	pageUrl += "&type=network&ref=southpark.cc.com&geo="+ geolocation +"&group=entertainment&network=None&device=Other&networkConnectionType=None"
	pageUrl += "&CONFIG_URL=http://media.mtvnservices.com/pmt-arc/e1/players/mgid:arc:episode:"+pageurl_geo[audio_pos]+":/context4/config.xml"
	pageUrl += "?uri=mgid:arc:episode:"+pageurl_geo[audio_pos]+":"+url+"&type=network&ref="+mainweb_geo[audio_pos]+"&geo="+ geolocation
	pageUrl += "&group=entertainment&network=None&device=Other&networkConnectionType=None"
	playpath = ""
	parts = str(len(mediagen))
	if audio == "de" and len(mediagen) <= 1:
		notifyText(translation(30011), 7000)
		return
	player = xbmc.Player()
	ccs = []
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	playlist.clear()
	i = 0
	for media in mediagen:
		data = getVideoData(media)
		rtmpe = data[0]
		if len(rtmpe) == 0:
			parts = str(len(mediagen)-1)
			continue
		cc = data[2]
		best = len(rtmpe)-1
		rtmpgeo = audio_pos
		if audio == "de" and "viacomccstrm" in rtmpe[best]:
			rtmpgeo = 0
		playpath = ""
		rtmp = rtmpe[best]
		if "viacomccstrm" in rtmpe[best]:
			playpath = "mp4:"+rtmpe[best].split('viacomccstrm/')[1]
			rtmp = rtmp_geo[0]#rtmpe[best].split('viacomccstrm/')[0]+'viacomccstrm/'
		videoname = title + " (" + str(i+1) + " of " + parts +")"
		li = xbmcgui.ListItem(videoname, iconImage=thumbnail, thumbnailImage=thumbnail)
		li.setInfo('video', {'Title': videoname})
		li.setProperty('conn', "B:0")
		if playpath != "":
			li.setProperty('PlayPath', playpath)
		li.setProperty('flashVer', "WIN 19,0,0,185")
		li.setProperty('pageUrl', pageUrl)
		li.setProperty('SWFPlayer', "http://media.mtvnservices.com/player/prime/mediaplayerprime.2.11.3.swf")
		li.setProperty("SWFVerify", "true")
		if cc != "" and cc_settings:
			fname = os.path.join(addonpath, "subtitle_"+str(i)+"_"+str(parts)+".vtt")
			subname = saveSubs(fname, cc)
			if subname != "":
				ccs.append(subname)
		playlist.add(url=rtmp, listitem=li, index=i)
		i += 1
	player.play(playlist)
	for s in xrange(1):
		if player.isPlaying():
			break
		time.sleep(1)
	if not player.isPlaying():
		notifyText(translation(30004), 4000)
		player.stop()
	pos = -1
	if pos != playlist.getposition():
		pos = playlist.getposition()
		if cc_settings and len(ccs) >= playlist.size():
			player.setSubtitles(ccs[pos])
			player.showSubtitles(cc_settings)
		else:
			print "["+addonID+"] missing some vtt subs..."

	while pos < playlist.size() and player.isPlaying():
		while player.isPlaying():
			time.sleep(0.05)
			if pos != playlist.getposition():
				pos = playlist.getposition()
				if cc_settings and len(ccs) >= playlist.size():
					player.setSubtitles(ccs[pos])
					player.showSubtitles(cc_settings)
				else:
					print "["+addonID+"] missing some vtt subs..."
		time.sleep(10)
	return

def translation(id):
    return encode(addon.getLocalizedString(id))
	
def notifyText(text, time=5000):
	utext = encode(text)
	uaddonname = encode(addon.getAddonInfo('name'))
	utime = encode(str(time))
	uicon = encode(icon);
	notification = 'Notification(%s, %s, %s, %s)' % (uaddonname, utext, utime, uicon)
	xbmc.executebuiltin(notification)

def getUrl(url):
	link = ""
	try:
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:25.0) Gecko/20100101 Firefox/25.0')
		response = urllib2.urlopen(req)
		link = response.read()
		response.close()
	except urllib2.URLError:
		notifyText(translation(30010), 3000)
		raise
	return link

def addLink(name, url, mode, iconimage, desc="", season="", episode="", date=""):
    if "?" in iconimage:
		pos = iconimage.index('?') - len(iconimage)
		iconimage = iconimage[:pos]
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+mode+"&title="+name+"&thumbnail="+iconimage
    convdate = ""
    if date != "":
		try:
			convdate = datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M:%S')
		except ValueError:
			convdate = date
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc, "Season": season, "Episode": episode, "Aired": convdate})
    liz.setProperty("fanart_image", defaultFanart)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addDir(name, url, mode, iconimage="DefaultFolder.png"):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty("fanart_image", defaultFanart)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

def getCarousel():
##	html = getUrl("http://southpark.cc.com/")
#	html = html.split("</section><section class=")
#	data_url = html[1].split("data-url=\"")
#	data_url = data_url[1]
#	data_url = data_url.split("\"")[0]
#	carousel = data_url.split("{resultsPerPage}/{currentPage}/json/{sort}")[0]
#	carousel += "14/1/json/airdate"
#	carousel += data_url.split("{resultsPerPage}/{currentPage}/json/{sort}")[1]
	return "http://southpark.cc.com/feeds/carousel/video/351c1323-0b96-402d-a8b9-40d01b2e9bde/30/1/json/!airdate/promotion-0?lang="+audio

def getMediagen(id):
	feed = ""
	feed = getUrl("http://"+mainweb_geo[audio_pos]+"/feeds/video-player/mrss/mgid:arc:episode:"+pageurl_geo[audio_pos]+":"+id+"?lang="+audio)
	root = ET.fromstring(feed)
	mediagen = []
	if sys.version_info >=  (2, 7):
		for item in root.iter('{http://search.yahoo.com/mrss/}content'):
			if item.attrib['url'] != None:
				mediagen.append(unescape(item.attrib['url']))
	else:
		for item in root.getiterator('{http://search.yahoo.com/mrss/}content'):
			if item.attrib['url'] != None:
				mediagen.append(unescape(item.attrib['url']))
	return mediagen

def getVideoData(mediagen):
	xml = ""
	if audio == "de":
		mediagen += "&deviceOsVersion=4.4.4&acceptMethods=hls";
		mediagen = mediagen.replace('{device}', 'Android')
	print mediagen
	xml = getUrl(mediagen)
	root = ET.fromstring(xml)
	rtmpe = []
	duration = []
	captions = ""
	if sys.version_info >=  (2, 7):
		for item in root.iter('src'):
			if item.text != None and not "intros" in item.text:
				if audio == "es":
					rtmpe.append(item.text)
				elif not "acts/es" in item.text:
					rtmpe.append(item.text)
		for item in root.iter('rendition'):
			if item.attrib['duration'] != None:
				duration.append(int(item.attrib['duration']))
		for item in root.iter('typographic'):
			if item.attrib['src'] != None and item.attrib['format'] == "vtt":
				captions = item.attrib['src']
	else:
		for item in root.getiterator('src'):
			if item.text != None and not "intros" in item.text:
				if audio == "es":
					rtmpe.append(item.text)
				elif not "acts/es" in item.text:
					rtmpe.append(item.text)
		for item in root.getiterator('rendition'):
			if item.attrib['duration'] != None:
				duration.append(int(item.attrib['duration']))
		for item in root.getiterator('typographic'):
			if item.attrib['src'] != None and item.attrib['format'] == "vtt":
				captions = item.attrib['src']
	return [rtmpe,duration,captions]

def saveSubs(fname, stream):
	data = unescape(getUrl(stream))
	output = open(fname,'wb')
	output.truncate()
	output.write(data)
	output.close()
	return stream

def getTimer(premiere):
	try:
		diff = int(premiere) - int(time.time())
	except ValueError:
		date = time.strptime(premiere, "%d.%m.%Y") # 30.09.2015
		diff = int(time.mktime(date)) - int(time.time())
		
	if diff < 0:
		diff = 0;
	days = int(diff/86400)
	hours = int((diff%86400)/3600)
	mins =  int((diff%3600)/60)
#	secs = int(diff % 60)
	return "%02dd %02dh %02dm" % (days, hours, mins)

def encode(string):
	try:
		return string.encode('UTF-8','replace')
	except UnicodeError:
		return string
   
	
def JStoJSON(s):
	s = re.sub("/\*([\s\S]*?)\*/", "", s)
	s = s.replace('\n', '')
	s = s.replace("{","{'")
	s = s.replace(":", "':")
	s = s.replace(",", ",'")
	s = s.replace(",' ", ", ")
	s = s.replace(", ]", "]")
	s = s.replace("http':", "http:")
	s = s.replace("{'", '{"')
	s = s.replace("'}", '"}')
	s = s.replace("':'", '":"')
	s = s.replace("','", '","')
	s = s.replace("':", '":')
	s = s.replace('": ', "': ")
	s = s.replace('":-', "':-")
	s = s.replace("\\'", "'")
	return s
	
def toUSJSON(s):
	if s[2] == 's' and s[3] == 'e':
		s = s.replace('{"season":', '')
		s = s[:-1]
	s = s.replace('"episode"', '"results"')
	s = s.replace('"available"', '"_availability"')
	s = s.replace('"donotair"', '"banned"')
	s = s.replace('"thumbnail_larger"', '"images"')
	s = s.replace('"id"', '"itemId"')
	s = s.replace('"episodenumber"', '"episodeNumber"')
	s = s.replace('"airdate"', '"originalAirDate"')
	return s

def unescape(s):
	htmlCodes = [["'", '&#39;'],['"', '&quot;'],['', '&gt;'],['', '&lt;'],['&', '&amp;']]
	for code in htmlCodes:
		s = s.replace(code[1], code[0])
	return s

def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
eptitle = urllib.unquote_plus(params.get('title', ''))
epthumbnail = urllib.unquote_plus(params.get('thumbnail', ''))

if mode == 'list':
    list(url)
elif mode == 'play':
    playEpisode(url, eptitle, epthumbnail)
else:
    index()
