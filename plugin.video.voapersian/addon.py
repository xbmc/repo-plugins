"""
    VOA Persian Kodi Plugin - written by Ali Jannatpour (google me)
    My First Plugin and I hate python!

    Credits:
	http://kodi.wiki/view/Audio-video_add-on_tutorial
	https://www.codecademy.com/glossary/python
	http://kodi.wiki/view/List_of_built-in_functions
	http://kodi.wiki/view/HOW-TO:Write_python_scripts
"""

import xbmcplugin,xbmcgui,xbmcaddon
import urllib,urlparse,urllib2,re,os,cookielib,string
from BeautifulSoup import BeautifulSoup
import json
from urlparse import urljoin

# plugin constants

__plugin__ = "VOA Persian"
__author__ = "alij"
__url__ = ""
__credits__ = "Kodi Wikis"
__version__ = "0.7.0"


# global data

addon = xbmcaddon.Addon('plugin.video.voapersian')
addonname = addon.getAddonInfo('name')
addon_handle = int(sys.argv[1])
path = addon.getAddonInfo('path')
base = sys.argv[0]
args = urlparse.parse_qs(sys.argv[2][1:])

icon = xbmc.translatePath(os.path.join(path, 'icon.png'))

# parameters

__site_baseurl = "http://ir.voanews.com/"

# global code

#xbmcplugin.setContent(addon_handle, 'movies')

cookies = cookielib.CookieJar()
http_request = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookies))

#utility functions

def alert(msg):
	dialog = xbmcgui.Dialog()
	dialog.ok(addonname, msg)

def getDOM(url):
	resp = http_request.open(url)
	return BeautifulSoup(resp.read())

def play(video):
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	playlist.clear()
	playlist.add(video)
	xbmc.Player().play(playlist)
	return True

def additem(title, url, icon, isfolder, isplayable):
	li = xbmcgui.ListItem(title)
	li.setInfo(type='Video', infoLabels={'Title' : title})
	if not(icon == None):
		li.setThumbnailImage(icon)
	if isplayable == True:
		li.setProperty("IsPlayable","true")
	if isfolder == None:
		isfolder = True
	xbmcplugin.addDirectoryItem(handle=addon_handle,
				    url=url,
                	            listitem=li,
                                    isFolder=isfolder)

def addEOI():
	xbmcplugin.endOfDirectory(addon_handle)

# general functions

def build_url(query):
    return base + '?' + urllib.urlencode(query)

def getArg(key):
	val = args.get(key, None)
	return None if val == None else val[0]

# site specific functions

def getPrograms():
	result = []
	node = getDOM(urljoin(__site_baseurl, "/programindex.html"))
	node = node.find("div", {"class" : "programlist"}).findAll("h4")
	for link in node:
		link = link.find("a")
		url = link['href']
		title = link.text
		entitle = re.search('(?<=/archive/)[^/]*', link['href']).group(0)
		entitle = entitle.replace('-', ' ')
		entitle = entitle.replace('_', ' ')
		entitle = entitle.capitalize()
		link = link.parent.parent.parent
		img = link.find('img')['src']
		result.append({'title': title, 'entitle': entitle, 'img': img, 'url': url})
	#result.sort(key=lambda i: i['title'], reverse=False)
	return result

def getVideoLinks(container_url):
	result = []
	node = getDOM(urljoin(__site_baseurl, container_url))
	node = node.find("div", {"id" : "programZonesItems"})
	if not(node == None):
		node = node.findAll("div", {"class" : "date black"})
	for link in node:
		if not(link is None or link.text is None):
			title = link.text
			url = link.parent.findNext('a')['href']
			img = link.parent.findNext('a').findNext('img')['src']
			result.append({'title': title, 'img': img, 'url': url})
	return result

def resolveVideo(page_url):
	node = getDOM(urljoin(__site_baseurl, page_url))
	link = node.find("meta", {"name" : "twitter:player:stream"})
	if link is None or link['content'] is None:
		alert('Error retrieving the video file')
		return None
	return link['content']

def getLiveLink():
	"""
	url = "/" # alt '/info/tv-guide/2822.html'
	node = getDOM(urljoin(__site_baseurl, url))
	link = node.find("a", {"class" : "itv_icon"})
	if not(link == None):
		url = link['href']
	"""
	url = '/media/videotube/86.html?rnd=20532'
	node = getDOM(urljoin(__site_baseurl, url))
	link = node.find("div", {"class" : "content_media"})
	if not(link == None):
		link = link.findAll('script')[0].find(text=True)
		link = link[link.find("configFilePath")+15:]
		link = link[:min(link.find(","),link.find("}"))]
		link = link.replace("\'","")
		link = link.replace(":","")
		link = link.replace(" ","")
		link = urllib2.unquote(link).decode('utf-8')
	# DEBUG '/flashxml/InternetTV.aspx?id=86&mode=auto&stamp=20150725155618'
	if not (link == None):
		url = link 
		node = getDOM(urljoin(__site_baseurl, url))
	link = node.find('media', {"type" : "video"})['playbackurl']
	# DEBUG 'rtmp://cp233584.live.edgefcs.net/live/LIVE_IPTV_VOA_PNN@119414'
	return link

# main

def main():
	if not (getArg('voa-folder') is None):
		"""
		additem(title='Latest آخرين برنامه', 
			url=build_url({"voa-link": getArg('voa-folder')}), 
			icon=icon, isfolder=False, isplayable=False)
		"""
		vidoes = getVideoLinks(getArg('voa-folder'))
		for v in vidoes:
			additem(title=v['title'], 
				url=build_url({"voa-link": v['url']}), 
				icon=v['img'], isfolder=False, isplayable=False)
		addEOI()
	elif (getArg('voa-link') is None):
		"""
		additem(title='Live TV پخش زنده', 
			url=getLiveLink(), 
			icon=icon, isfolder=False, isplayable=True)
		"""
		progs = getPrograms()
		for p in progs:
			additem(title=p['entitle'] + ' ' + p['title'], 
				url=build_url({"voa-folder": p['url']}),
				icon=p['img'], isfolder=True, isplayable=False)
		addEOI()
	else:
		play(resolveVideo(getArg('voa-link')))
	return True
	
try:
	main()
except:
	alert('Error retrieving data from VOA Persian website')
