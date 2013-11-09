#!/usr/bin/python
# -*- coding: latin-1 -*-
"""
    This ia part of the xbmc addon MusicVideos by pcd@et-view-support.com
    Copyright (C) 2013

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import xbmc,xbmcaddon,xbmcplugin,xbmcgui
import sys
import urllib, urllib2
import time
import re
from htmlentitydefs import name2codepoint as n2cp
import httplib
import urlparse
from os import path, system
import socket
from urllib2 import Request, URLError, urlopen
from urlparse import parse_qs
from urllib import unquote_plus



thisPlugin = int(sys.argv[1])
addonId = "plugin.video.musicvideos"
addon = xbmcaddon.Addon(addonId)
dataPath = xbmc.translatePath('special://profile/addon_data/%s' % (addonId))
translation = addon.getLocalizedString
if not path.exists(dataPath):
       cmd = "mkdir -p " + dataPath
       system(cmd)
       
Host = "http://www.musicvideos.com/"

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	return link
	
def showOptions():
        Options = []
        Options.append([translation(30001), "Categories"])
        Options.append([translation(30002), "Top_20_Charts"])
        for option in Options:
                url1 = option[1]
                name = option[0]
                pic = " "
		addDirectoryItem(name, {"name":name, "url":url1, "mode":1}, pic)  
	xbmcplugin.endOfDirectory(thisPlugin)	

def showContent(name, url):
        content = getUrl(Host)
#        print "content A =", content
        if url == "Categories":
                n1 = content.find("<!-- end of categories-list -->", 0)
                content = content[:n1]  
                regexcat = 'div class="option item.*?div class="option-wrapper"><a href="(.*?)">(.*?)</a'
                match = re.compile(regexcat,re.DOTALL).findall(content)
#                print "match =", match
                for url, name in match:
                        url1 = "http://www.musicvideos.com" + url
                        pic = " "
                        addDirectoryItem(name, {"name":name, "url":url1, "mode":2}, pic)
                xbmcplugin.endOfDirectory(thisPlugin)
                
        elif url == "Top_20_Charts":
                n1 = content.find("<h2>Top 20 Music Videos by Genre</h2>", 0)
                n2 = content.find("</div>", n1)
                content = content[n1:n2]
                regexcat = '<li><a href="(.*?)">(.*?)</a'
                match = re.compile(regexcat,re.DOTALL).findall(content)
                for url, name in match:
                        url1 = "http://www.musicvideos.com" + url
                        pic = " "
                        addDirectoryItem(name, {"name":name, "url":url1, "mode":7}, pic)
	        xbmcplugin.endOfDirectory(thisPlugin)
	
def getVideos(name1, urlmain):
	content = getUrl(urlmain)
	regexvideo = '<div class="item">.*?div class="item-wrapper.*?div class="thumbnail"><a href="(.*?)"><img src="(.*?)".*?div class="shorttitle"><a href.*?">(.*?)</'
	match = re.compile(regexvideo,re.DOTALL).findall(content)
        for url, pic, name in match:
                 url1 = "http://www.musicvideos.com" + url 
	         addDirectoryItem(name, {"name":name, "url":url1, "mode":3}, pic)
	name = translation(30003)
	addDirectoryItem(name, {"name":name, "url":urlmain, "mode":4}, pic)
        xbmcplugin.endOfDirectory(thisPlugin)
        
def getVideos2(name1, urlmain):
        xurl = urlmain + "?s=31"  
	content = getUrl(xurl)
	regexvideo = '<div class="item">.*?div class="item-wrapper.*?div class="thumbnail"><a href="(.*?)"><img src="(.*?)".*?div class="shorttitle"><a href.*?">(.*?)</'
	match = re.compile(regexvideo,re.DOTALL).findall(content)
        for url, pic, name in match:
                 url1 = "http://www.musicvideos.com" + url 
	         addDirectoryItem(name, {"name":name, "url":url1, "mode":3}, pic)
	name = translation(30003)
	addDirectoryItem(name, {"name":name, "url":urlmain, "mode":5}, pic)
        xbmcplugin.endOfDirectory(thisPlugin)
        		
def getVideos3(name1, urlmain):
        xurl = urlmain + "?s=46"  
	content = getUrl(xurl)
	regexvideo = '<div class="item">.*?div class="item-wrapper.*?div class="thumbnail"><a href="(.*?)"><img src="(.*?)".*?div class="shorttitle"><a href.*?">(.*?)</'
	match = re.compile(regexvideo,re.DOTALL).findall(content)
        for url, pic, name in match:
                 url1 = "http://www.musicvideos.com" + url 
	         addDirectoryItem(name, {"name":name, "url":url1, "mode":3}, pic)
	name = translation(30003)
	addDirectoryItem(name, {"name":name, "url":urlmain, "mode":6}, pic)
        xbmcplugin.endOfDirectory(thisPlugin)
        
def getVideos4(name1, urlmain):
        xurl = urlmain + "?s=61"  
	content = getUrl(xurl)
	regexvideo = '<div class="item">.*?div class="item-wrapper.*?div class="thumbnail"><a href="(.*?)"><img src="(.*?)".*?div class="shorttitle"><a href.*?">(.*?)</'
	match = re.compile(regexvideo,re.DOTALL).findall(content)
        for url, pic, name in match:
                 url1 = "http://www.musicvideos.com" + url 
	         addDirectoryItem(name, {"name":name, "url":url1, "mode":3}, pic)
        xbmcplugin.endOfDirectory(thisPlugin)
        
def getVideos5(name1, urlmain):
        xurl = urlmain  
	content = getUrl(xurl)
	regexvideo = '<div class="item">.*?div class="item-wrapper.*?div class="thumbnail"><a href="(.*?)"><img src="(.*?)".*?div class="shorttitle"><a href.*?">(.*?)</'
	match = re.compile(regexvideo,re.DOTALL).findall(content)
        for url, pic, name in match:
                 url1 = "http://www.musicvideos.com" + url 
	         addDirectoryItem(name, {"name":name, "url":url1, "mode":3}, pic)
        xbmcplugin.endOfDirectory(thisPlugin)
                
def playVideo(name, url):
	   global thisPlugin

           n1 = url.find(".html", 0)
           n2 = url.rfind("/", 0, n1)
           vid = url[(n2+1):n1]
           vid = vid + "&amp;feature=youtube_gdata"
           mrl = getVideoUrl(vid)
           video = name
           video = video.replace("_", " ")
           pic = "DefaultFolder.png"
           li = xbmcgui.ListItem(name,iconImage="DefaultFolder.png", thumbnailImage=pic)
           player = xbmc.Player()
           player.play(mrl, li)

std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}  
def getVideoUrl(vid):
#Part of this routine is based on the enigma2 plugin MyTube
		VIDEO_FMT_PRIORITY_MAP = {
			'38' : 1, #MP4 Original (HD)
			'37' : 2, #MP4 1080p (HD)
			'22' : 3, #MP4 720p (HD)
			'18' : 4, #MP4 360p
			'35' : 5, #FLV 480p
			'34' : 6, #FLV 360p
		}
		video_url = None
		video_id = vid
		watch_url = 'http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id
		watchrequest = Request(watch_url, None, std_headers)
		watchvideopage = urlopen(watchrequest).read()

		for el in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
			info_url = ('http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el))
			request = Request(info_url, None, std_headers)
			infopage = urlopen(request).read()
			videoinfo = parse_qs(infopage)
			if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
					break

		if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
			if 'reason' not in videoinfo:
                                pass
			else:
				reason = unquote_plus(videoinfo['reason'][0])
			return video_url

		video_fmt_map = {}
		fmt_infomap = {}
		if videoinfo.has_key('url_encoded_fmt_stream_map'):
			tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',')
		else:
			tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
		for fmtstring in tmp_fmtUrlDATA:
			fmturl = fmtid = fmtsig = ""
			if videoinfo.has_key('url_encoded_fmt_stream_map'):
				try:
					for arg in fmtstring.split('&'):
						if arg.find('=') >= 0:
							key, value = arg.split('=')
							if key == 'itag':
								if len(value) > 3:
									value = value[:2]
								fmtid = value
							elif key == 'url':
								fmturl = value
							elif key == 'sig':
								fmtsig = value
								
					if fmtid != "" and fmturl != "" and fmtsig != ""  and VIDEO_FMT_PRIORITY_MAP.has_key(fmtid):
						video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl), 'fmtsig': fmtsig }
						fmt_infomap[int(fmtid)] = "%s&signature=%s" %(unquote_plus(fmturl), fmtsig)
					fmturl = fmtid = fmtsig = ""

				except:
				        pass	
 					
			else:
				(fmtid,fmturl) = fmtstring.split('|')
			if VIDEO_FMT_PRIORITY_MAP.has_key(fmtid) and fmtid != "":
				video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = { 'fmtid': fmtid, 'fmturl': unquote_plus(fmturl) }
				fmt_infomap[int(fmtid)] = unquote_plus(fmturl)
		if video_fmt_map and len(video_fmt_map):
			best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
			video_url = "%s&signature=%s" %(best_video['fmturl'].split(';')[0], best_video['fmtsig'])

		return video_url

def addDirectoryItem(name, parameters={},pic=""):
    li = xbmcgui.ListItem(name,iconImage="DefaultFolder.png", thumbnailImage=pic)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=True)


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

params = parameters_string_to_dict(sys.argv[2])
name =  str(params.get("name", ""))
url =  str(params.get("url", ""))
url = urllib.unquote(url)
mode =  str(params.get("mode", ""))

if not sys.argv[2]:
	ok = showOptions()
else:
	if mode == str(1):
		ok = showContent(name, url)
	elif mode == str(2):
		ok = getVideos(name, url)	
	elif mode == str(3):
		ok = playVideo(name, url)	
	elif mode == str(4):
		ok = getVideos2(name, url)	
	elif mode == str(5):
		ok = getVideos3(name, url)
	elif mode == str(6):
		ok = getVideos4(name, url)
	elif mode == str(7):
		ok = getVideos5(name, url)
		








