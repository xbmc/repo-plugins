#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.

import os, re, sys
import urllib, urllib2, HTMLParser
import xbmcgui, xbmcplugin, xbmcaddon
import xml.etree.ElementTree as ET

pluginhandle	= int(sys.argv[1])
addon			= xbmcaddon.Addon()
pluginid		= addon.getAddonInfo('id')
translation		= addon.getLocalizedString
path_plugin		= xbmc.translatePath(addon.getAddonInfo('path')).decode("utf-8")
path_icon		= path_plugin + '/icon.png'

user_agent		= 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'
url_base		= 'http://www.gameone.de'
url_year		= url_base + '/tv/year/'
url_podcast		= url_base + '/feed/podcast.xml'
url_episode		= 'http://www.gameone.de/api/mrss/mgid%3Agameone%3Avideo%3Amtvnn.com%3Atv_show-'
url_swf			= 'http://www.gameone.de/flash/g2player_2.1.9.beta3.swf'


def log(message, lvl=xbmc.LOGNOTICE):
	message = (pluginid + ': %s' % message).encode('utf-8')
	xbmc.log(msg=message, level=lvl)
	
def parse_html_string(string):
	parser = HTMLParser.HTMLParser()
	string = parser.unescape(string)
	return string

def build_url(string):
	return sys.argv[0] + '?' + urllib.urlencode(string)


def get_parameters(string):
	''' Convert parameters in a URL to a dict. '''
	
	parameters = {}
	if string:
		if (string[:1] == '?'):
			parameter_pairs = string[1:].split('&')
			for i in parameter_pairs:
				parameter_split = i.split('=')
				if (len(parameter_split) == 2):
					parameters[parameter_split[0]] = urllib.unquote(parameter_split[1])
				else:
					log('Couldn\'t split parameters correctly (wrong amount of array elements) [Elements: ' + len(parameter_split) + ' | String:' + string + ']', xbmc.LOGERROR)
		else:
			url_split = string.split('?')
			if (len(url_split) == 2):
				parameter_pairs = url_split[1].split('&')
				for i in parameter_pairs:
					parameter_split = i.split('=')
					if (len(parameter_split) == 2):
						parameters[parameter_split[0]] = urllib.unquote(parameter_split[1])
					else:
						log('Couldn\'t split parameters correctly (wrong amount of array elements) [Elements: ' + len(parameter_split) + ' | String:' + string + ']', xbmc.LOGERROR)
			else:
				log('Couldn\'t split parameters correctly (wrong amount of array elements) [Elements: ' + len(parameter_split) + ' | String:' + string + ']', xbmc.LOGERROR)
	return parameters


def parse_content(string, pattern=False, dotall=False):
	''' Extract contents with regex from either a website or a comitted string. If no regex pattern is passed, the whole content is returned. '''
	
	log('Start parsing content...', xbmc.LOGDEBUG)
	
	if (len(re.findall('http[s]?://', string[:8])) >= 1 or string[:4] == 'www.'):
		log('URL passed, scraping from URL: ' + string, xbmc.LOGDEBUG)
		
		req = urllib2.Request(string)
		req.add_header('User-Agent', user_agent)
		response = urllib2.urlopen(req)
		content = response.read()
		response.close()
		if isinstance(content,str):
			content = content.decode('utf-8')
	else:
		log('Content passed, skip scraping...', xbmc.LOGDEBUG)
		content = string	
	
	if (pattern != False):
		log('Expression: ' + str(pattern), xbmc.LOGDEBUG)
		if (dotall == True):
			match = re.compile(pattern, re.DOTALL).findall(content)
		else:
			match = re.compile(pattern).findall(content)
		log(str(len(match)) + ' matches', xbmc.LOGDEBUG)
		return match
	else:
		log('No expression found, returning whole content.', xbmc.LOGDEBUG)
		return content


def add_menu_item(type, name, url, mode, thumbIMG='', fanart=''):
	''' Add an item to the XBMC GUI. '''
	
	if not thumbIMG and addon.getSetting(id='showlogo') == 'true':
		thumbIMG = path_icon
	
	name = parse_html_string(name)
	
	if (type == 'ITEMTYPE_DIRECTORY' or type == 'ITEMTYPE_DUMMY_DIR'):
		iconIMG = 'DefaultFolder.png'
	elif (type == 'ITEMTYPE_VIDEO' or type == 'ITEMTYPE_DUMMY_VID'):
		iconIMG = 'DefaultVideo.png'
			
	list_item = xbmcgui.ListItem(name, iconImage=iconIMG, thumbnailImage=thumbIMG)
	#list_item.setInfo( type="Video", infoLabels={ "Title": name } )
	list_item.setProperty('fanart_image', fanart)
	if (type == 'ITEMTYPE_VIDEO'):
		list_item.setProperty('Video', 'true')
		list_item.setProperty('IsPlayable', 'true')
	
	url = sys.argv[0] + '?mode=' + str(mode) + '&url=' + urllib.quote_plus(url)
	 
	if (type == 'ITEMTYPE_DIRECTORY'):
		return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=list_item, isFolder=True)
	else:
		return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=list_item)



class plugin_structure():
	
	def show_menu_root(self):
		add_menu_item('ITEMTYPE_DIRECTORY', translation(30101), url_base + '/tv',		'show_menu_tv')
		add_menu_item('ITEMTYPE_DIRECTORY', translation(30102), url_base + '/blog',		'show_menu_blog')
		add_menu_item('ITEMTYPE_DIRECTORY', translation(30104), url_podcast,			'show_menu_podcasts')
		
		if addon.getSetting(id='showsettings') == 'true':
			add_menu_item('ITEMTYPE_DUMMY_DIR', translation(30100), '', 'show_settings')
		
		xbmcplugin.endOfDirectory(handle=pluginhandle)
	
	
	def show_settings(self):
		return xbmc.executebuiltin('Addon.OpenSettings(' + pluginid + ')')
	
	
	#CATEGORY: TV
	def show_menu_tv(self):
		log('Indexing years of TV episodes', xbmc.LOGDEBUG)
		
		match_years = parse_content(url, '<a href="/tv\?year=([0-9]{4})">[0-9]{4}</a>', True)
		for year in match_years:
			add_menu_item('ITEMTYPE_DIRECTORY', year, url_year + year, 'show_menu_tv_episodes')
			
		xbmcplugin.endOfDirectory(handle=pluginhandle)
	
	
	def show_menu_tv_episodes(self):
		log('Indexing TV episodes: ' + url, xbmc.LOGDEBUG)
		
		match_episodes = parse_content(url, '''<a href="/tv/([0-9]+)" class="image_link"><img.+?/><noscript><img src="(.+?)".+?/></noscript></a>\n<h5>\n<a href=\'.+?\' title=['"](.+?)['"]>''', True)
		for episode,thumbnail,title in match_episodes:
			title = translation(30002) + ' ' + episode + ' - ' + title
			add_menu_item('ITEMTYPE_VIDEO', title, url_episode + episode, 'play_tv_episode', thumbnail)
		
		xbmcplugin.endOfDirectory(handle=pluginhandle)
	
	
	def play_tv_episode(self):
		log('Playing TV episode: ' + url, xbmc.LOGNOTICE)
		
		match_video_xml = parse_content(url, "<media:content.+?url='(.+?)'></media:content>")
		for video_xml_url in match_video_xml:
			match_video = str(parse_content(video_xml_url))
			xml_root = ET.fromstring(match_video)
			
			dict_resolutions = {}
			for stream in xml_root.findall('./video/item/rendition'):
				dict_resolutions[int(stream.attrib.get('height'))] = stream.find('src').text
			
			log('Selecting stream quality: ' + str(resolutions.SETTINGS.get(int(addon.getSetting(id='videoquality')))), xbmc.LOGDEBUG)
			video_file = dict_resolutions.get(resolutions.SETTINGS.get(int(addon.getSetting(id='videoquality'))))
			if video_file == None:
				log('Couldn\'t select stream quality: ' + str(resolutions.SETTINGS.get(int(addon.getSetting(id='videoquality')))) + ', falling back to highest.', xbmc.LOGNOTICE)
				video_file = dict_resolutions[max(dict_resolutions)]
			
			video_url = video_file + ' swfurl=' + url_swf + ' swfvfy=true' + ' pageUrl=www.gameone.de app=ondemand?ovpfv=2.1.4'
			
			item = xbmcgui.ListItem(path=video_url)
			return xbmcplugin.setResolvedUrl(pluginhandle, True, item)

		xbmcplugin.endOfDirectory(handle=pluginhandle)
	
	
	
	#CATEGORY: BLOG
	def show_menu_blog(self):
		log('Indexing blog categories: ' + url, xbmc.LOGDEBUG)
		
		add_menu_item('ITEMTYPE_DIRECTORY', translation(30200), url, 'show_menu_blog_entries')
		
		match_teasers = parse_content(url, '<ul class="teasers">(.+?)</ul>', True)
		for teaser in match_teasers:
			match_categories = parse_content(teaser, '<a title="(.+?)" href="(.+?)">.+?<img.+?src="(.+?)"', True)
			for category,url_category,thumbnail in match_categories:
				add_menu_item('ITEMTYPE_DIRECTORY', category, url_base + url_category, 'show_menu_blog_entries', thumbnail)
		
		xbmcplugin.endOfDirectory(handle=pluginhandle)
	
	
	def show_menu_blog_entries(self):
		log('Indexing blog entries: ' + url, xbmc.LOGDEBUG)

		match_posts	= parse_content(url, '<li class="post teaser_box teaser".+?<div class=\'overlay\'.+?<a href="(.+?)">(.+?)</a>.+?<a class=\'image_link\' href=\'.+?\'>\n<img .+?src="(.+?)"', True)
		match_next	= parse_content(url, '<a class="next_page" rel="next" href="(.+?)">', True)
		
		for post_url,title,thumbnail in match_posts:
			match_content		= parse_content(url_base + post_url)
			match_videoposts	= parse_content(match_content, '<div class="player_swf".+?', True)
			match_blogpages		= parse_content(match_content, '<a class="forwards" href="(.+?)">', True)
			video_amount = len(match_videoposts)
			pages_amount = len(match_blogpages)
			
			if video_amount == 1:
				if pages_amount == 0:
					match_video_id = parse_content(match_content, 'video_meta-(.+?)"')
					add_menu_item('ITEMTYPE_VIDEO', title, match_video_id[0], 'play_blog_video', thumbnail)
				else:
					add_menu_item('ITEMTYPE_DIRECTORY', title, url_base + post_url, 'show_menu_blog_videos', thumbnail)
			elif video_amount>1:
				add_menu_item('ITEMTYPE_DIRECTORY', title, url_base + post_url, 'show_menu_blog_videos', thumbnail)
		
		for url_next in match_next:
			add_menu_item('ITEMTYPE_DIRECTORY', translation(30001), url_base + url_next, 'show_menu_blog_entries')
		
		xbmcplugin.endOfDirectory(handle=pluginhandle)
		
		
	def show_menu_blog_videos(self):
		log('Indexing blog videos: ' + url, xbmc.LOGDEBUG)
		
		match_content 	= parse_content(url)
		match_video		= parse_content(match_content, 'video_meta-(.+?)"')
		match_thumb		= parse_content(match_content, '"image", "(.+?)"', True)
		match_title		= parse_content(match_content, '<p><strong>(.+?)</strong>', True)
		match_next		= parse_content(match_content, '<a class="forwards" href="(.+?)">')
		
		i = 0
		for video_id in match_video:
			try: title = match_title[i]
			except: title = translation(30003)
			if title[-1:] == ':':
				title = title[:-1]
			add_menu_item('ITEMTYPE_VIDEO', title, video_id, 'play_blog_video', match_thumb[i])
			i = i + 1
		
		for url_next in match_next:
			add_menu_item('ITEMTYPE_DIRECTORY', translation(30001), url_next, 'show_menu_blog_videos')
			
		xbmcplugin.endOfDirectory(handle=pluginhandle)


	def play_blog_video(self):
		log('Playing blog video: ' + url, xbmc.LOGNOTICE)
		
		url_video = self.get_video(url)
		item = xbmcgui.ListItem(path=url_video)
		xbmcplugin.setResolvedUrl(pluginhandle, True, item)
		
		xbmcplugin.endOfDirectory(handle=pluginhandle)
		
		
	
	#CATEGORY: PODCASTS
	def show_menu_podcasts(self):
		log('Indexing podcasts: ' + url)
		
		match_content	= parse_content(url, '</image>.+?</rss>', True)[0]
		match_podcasts	= parse_content(match_content, '<title>(.+?)</title>.+?<feedburner:origLink>(.+?)</feedburner:origLink>', True)
		
		for title,url_podcast in match_podcasts:
			add_menu_item('ITEMTYPE_VIDEO', title, url_podcast, 'play_media')
		
		xbmcplugin.endOfDirectory(handle=pluginhandle)
		
		
	#GENERAL FUNCTIONS:
	def play_media(self, url_media=''):
		log('Playing media: ' + url_media, xbmc.LOGNOTICE)
		
		if not url_media:
			url_media = url
			
		item = xbmcgui.ListItem(path=url_media)
		xbmcplugin.setResolvedUrl(pluginhandle, True, item)
		#xbmc.Player().play(url_media, item)


	def get_video(self, video_id):
		log('Scraping video ID: ' + url, xbmc.LOGDEBUG)
		
		match_video = str(parse_content('http://riptide.mtvnn.com/mediagen/' + video_id))
		xml_root = ET.fromstring(match_video)
		
		dict_resolutions = {}
		for stream in xml_root.findall('./video/item/rendition'):
			dict_resolutions[int(stream.attrib.get('height'))] = stream.find('src').text
		
		log('Selecting stream quality: ' + str(resolutions.SETTINGS.get(int(addon.getSetting(id='videoquality')))), xbmc.LOGDEBUG)
		video_file = dict_resolutions.get(resolutions.SETTINGS.get(int(addon.getSetting(id='videoquality'))))
		if video_file == None:
			log('Couldn\'t select stream quality: ' + str(resolutions.SETTINGS.get(int(addon.getSetting(id='videoquality')))) + ', falling back to highest.', xbmc.LOGNOTICE)
			video_file = dict_resolutions[max(dict_resolutions)]
			
		return video_file + ' swfurl=' + url_swf + ' swfvfy=true' + ' pageUrl=www.gameone.de app=ondemand?ovpfv=2.1.4'

		
class resolutions():
	''' This class shouldn't be instantiated. '''
	
	SETTINGS		= { 0 : 270,
						1 : 360,
						2 : 720		}

# Get parameters
parameters	= get_parameters(sys.argv[2]) 
url			= parameters.get('url')
mode		= parameters.get('mode')

navigate = plugin_structure()

if not sys.argv[2]:
	navigate.show_menu_root()
else:
	try:
		mode_splitted = mode.split('!')
		call_func	= getattr(navigate,mode_splitted[0])
		try:
			call_func(mode_splitted[1])
		except:
			call_func()
	except:
		log('Error: Failed executing function! [Mode: ' + mode + ']', xbmc.LOGERROR)
