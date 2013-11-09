#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import re
import sys
import xbmcplugin
import xbmcgui
import xbmcaddon
import base64
import socket


socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.extreme-vidz')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
viewMode = settings.getSetting("viewMode")
view = ["list", "thumbnail"]
viewMode = view[int(viewMode)]
VideoQuality = settings.getSetting("VideoQuality")
qual = ["Ask", "SD", "HD"]
VideoQuality = qual[int(VideoQuality)]
xbmc.log('Running platform is '+sys.platform)
xbmc.log('Running Python version is '+sys.version)
matches = []


# Suggested view codes for each type from different skins (initial list thanks to xbmcswift2 library)
ALL_VIEW_CODES = {
    'list': {
        'skin.confluence': 50, # List
        'skin.aeon.nox': 50, # List
        'skin.droid': 50, # List
        'skin.quartz': 50, # List
        'skin.re-touched': 50, # List
    },
    'thumbnail': {
        'skin.confluence': 500, # Thumbnail
        'skin.aeon.nox': 500, # Wall
        'skin.droid': 51, # Big icons
        'skin.quartz': 51, # Big icons
        'skin.re-touched': 500, #Thumbnail
        'skin.confluence-vertical': 500,
        'skin.jx720': 52,
        'skin.pm3-hd': 53,
        'skin.rapier': 50,
        'skin.simplicity': 500,
        'skin.slik': 53,
        'skin.touched': 500,
        'skin.transparency': 53,
        'skin.xeebo': 55,
    },
}


def index():
    addDir(translation(30001), "http://extreme-vidz.com/bmx", 'sortDirection', "")
    addDir(translation(30002), "http://extreme-vidz.com/mtb", 'sortDirection', "")
    addDir(translation(30003), "http://extreme-vidz.com/Inline", 'sortDirection', "")
    addDir(translation(30004), "http://extreme-vidz.com/Surf", 'sortDirection', "")
    addDir(translation(30005), "http://extreme-vidz.com/Ski", 'sortDirection', "")
    addDir(translation(30006), "http://extreme-vidz.com/snow", 'sortDirection', "")
    addDir(translation(30007), "http://extreme-vidz.com/Skateboard", 'sortDirection', "")
    addDir(translation(30008), "http://extreme-vidz.com/Graffiti", 'sortDirection', "")
    addDir(translation(30009), "http://extreme-vidz.com/category/genre/Auto", 'sortDirection', "")
    addDir(translation(30010), "http://extreme-vidz.com/category/genre/Wakeboard", 'sortDirection', "")
    addDir(translation(30011), "http://extreme-vidz.com/category/genre/Climbing", 'sortDirection', "")
    addDir(translation(30012), "http://extreme-vidz.com/category/genre/MotoX", 'sortDirection', "")
    addDir(translation(30016), "http://extreme-vidz.com/top100", 'listListVideos', "")
    addDir(translation(30020), "", 'search', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def sortDirection(url):
    urlFree = url+"/free"
    urlDVD = url+"/dvd"
    urlAll = url+"/all"
    addDir(translation(30013), urlFree, 'listCatVideos', "")
    addDir(translation(30014), urlDVD, 'listCatVideos', "")
    addDir(translation(30015), urlAll, 'listListVideos', "")
    #addLink(translation(30017), url, 'playAll', "")
    listVideos(url,'<div class="relative".*?<img src="([^"]+)".*?<a href="([^<]+)">([^<]+)</a>')
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        set_view(viewMode)
		
		
def listVideos(url, pattern):
    data = getUrl(url)

    global matches
    matches = re.compile(pattern,re.DOTALL).findall(data)
    print matches
	
    #addLink(translation(30017), url, 'playAll', "")

    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        '''xbmc.log('TITULO: '+scrapedtitle)
        xbmc.log('THUMB: '+scrapedthumbnail)
        xbmc.log('URL: '+scrapedurl)'''
        scrapedtitle = cleanTitle(scrapedtitle)
        addLink(scrapedtitle, 'http://extreme-vidz.com'+scrapedurl, 'playVideo', scrapedthumbnail)

    xbmcplugin.endOfDirectory(pluginhandle)
	
    if forceViewMode:
        set_view(viewMode)


def search():
    keyboard = xbmc.Keyboard('', translation(30020))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        listVideos('http://extreme-vidz.com/search/node/'+search_string,'<dt class="title">(.*?)<a href="http://extreme-vidz.com([^<]+)">([^<]+)</a>')


def playVideo(url):
    content = getUrl(url)
    xbmc.log("playVideo(url='%s')" % url)

    (video_id, video_source) = find_videos(content)
	
    if video_source == 'vimeo':
        quality = getQuality()
        listitem = getVideo(video_id, video_source, quality)
    else:
        listitem = getVideo(video_id, video_source, quality="")
    
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
		
	
def getVideo(video_id, video_source, quality):
    if video_source == 'youtube':
        if '2.4.6' in sys.version:
	        listitem = xbmcgui.ListItem(path='plugin://video/youtube/?path=/root/video&action=play_video&videoid='+video_id)
        else:
            listitem = xbmcgui.ListItem(path='plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid='+video_id)
    elif video_source == 'vimeo':
		if '2.4.6' in sys.version:
			listitem = xbmcgui.ListItem(path='plugin://video/vimeo/?path=/root/explore/hd&action=play_video&videoid='+video_id+'&quality='+quality)
		else:
			listitem = xbmcgui.ListItem(path='plugin://plugin.video.vimeo/?path=/root/explore/hd&action=play_video&videoid='+video_id+'&quality='+quality)
			
    return listitem	

def playAll(url):
    xbmc.log("playAll ["+url+"]")

    quality = getQuality()
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
	
    for scrapedthumbnail, scrapedurl, scrapedtitle in matches:
        content = getUrl('http://extreme-vidz.com'+scrapedurl)
        (video_id, video_source) = find_videos(content)
        listitem = getVideo(video_id, video_source, quality)
        listitem.setInfo(type="Video", infoLabels={"Title": scrapedtitle})
        playlist.add('http://extreme-vidz.com'+scrapedurl, listitem)

    player_type = xbmc.PLAYER_CORE_AUTO
    xbmcPlayer = xbmc.Player(player_type)
    xbmcPlayer.play(playlist)


def getQuality():
	if VideoQuality == "Ask":
		 quality = userSelectsVideoQuality()
	elif VideoQuality == "SD":
		quality = "sd"
	elif VideoQuality == "HD":
		quality = "720p"
	else:
		quality = "sd"

	return quality


def userSelectsVideoQuality():
	items = [("720p", "HD"),("sd", "SD")]
	choices = []
			
	if len(items) > 1:             
		for (quality, message) in items:
			choices.append(message)

		dialog = xbmcgui.Dialog()
		selected = dialog.select(translation(30101), choices)

		if selected > -1:
			(quality, message) = items[selected]
			return quality
	
	return "sd"


def cleanTitle(title):
    title = title.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&#039;", "'").replace("&quot;", "\"").replace("&szlig;", "ß").replace("&ndash;", "-")
    title = title.replace("&Auml;", "Ä").replace("&Uuml;", "Ü").replace("&Ouml;", "Ö").replace("&auml;", "ä").replace("&uuml;", "ü").replace("&ouml;", "ö")
    title = title.strip()
    return title


def getUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:14.0) Gecko/20100101 Firefox/14.0.1')
    response = urllib2.urlopen(req)
    link = response.read()
    response.close()
    return link
	
	
def find_videos(content):
    match = ""
    found = set()
    video_source = ""

    #"http://www.youtube.com/embed/TxMWDksFDhk?rel=0
    pattern  = 'youtube.com/embed/([0-9A-Za-z_-]{11})'
    matches = re.compile(pattern,re.DOTALL).findall(content)

    for match in matches:
        if match not in found:
            xbmc.log("Youtube video id="+match)
            found.add(match)
            video_source = 'youtube'
        else:
            xbmc.log("Duplicated Youtube id="+match)
            	
    #"http://player.vimeo.com/video/17555432?title=0&amp;byline=0&amp;portrait=0
    pattern  = 'player.vimeo.com/video/([0-9]+)'
    matches = re.compile(pattern,re.DOTALL).findall(content)

    for match in matches:
        if match not in found:
            xbmc.log("Vimeo video id="+match)
            found.add(match)
            video_source = 'vimeo'
        else:
            xbmc.log("Duplicated Vimeo id="+match)
            
    #"http://vimeo.com/17555432
    pattern  = 'vimeo.com/([0-9]+)'
    matches = re.compile(pattern,re.DOTALL).findall(content)

    for match in matches:
        if match not in found:
            xbmc.log("Vimeo video id="+url)
            found.add(match)
            video_source = 'vimeo'
        else:
            xbmc.log("Duplicated Vimeo id="+url)
            
    return (match, video_source)


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok
	

def set_view(view_mode, view_code=0):
    xbmc.log("set_view view_mode='"+view_mode+"', view_code="+str(view_code))

    # Reads skin name
    skin_name = xbmc.getSkinDir()
    xbmc.log("set_view skin_name='"+skin_name+"'")

    try:
        if view_code==0:
            xbmc.log("set_view view mode is "+view_mode)
            view_codes = ALL_VIEW_CODES.get(view_mode)
            view_code = view_codes.get(skin_name)
            xbmc.log("set_view view code for "+view_mode+" in "+skin_name+" is "+str(view_code))
            xbmc.executebuiltin("Container.SetViewMode("+str(view_code)+")")
        else:
            xbmc.log("set_view view code forced to "+str(view_code))
            xbmc.executebuiltin("Container.SetViewMode("+str(view_code)+")")
    except:
        xbmc.log("Unable to find view code for view mode "+str(view_mode)+" and skin "+skin_name)

	

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if isinstance(url, type(str())):
    url = urllib.unquote_plus(url)

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listCatVideos':
    listVideos(url, '<li class="views-row views-row.*?<img src="([^"]+)".*?<a href="([^<]+)">([^<]+)</a>')
elif mode == 'listListVideos':
    listVideos(url, '<td class="views-field views-field-title">(.*?)<a href="([^<]+)">([^<]+)</a>')
elif mode == 'sortDirection':
    sortDirection(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playAll':
    playAll(url)
elif mode == 'search':
    search()
else:
    index()
