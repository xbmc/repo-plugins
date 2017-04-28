# -*- coding: utf-8 -*-
import os, sys
import urllib, urlparse, json
import xbmcgui, xbmcplugin, xbmcaddon
import requests
from register import device

def build_url(query):
	"""Returns builds query url."""
	return base_url + '?' + urllib.urlencode(query)

def categories():
	"""Returns list of categories""" 
	requestCategories = requests.get(api_base_url + 'categories/?lang=en&uid=' + api_key)
	categories = requestCategories.json()
	return categories

def channels():
	"""Returns list of channels"""
	requestChannels = requests.get(api_base_url + 'channels/?uid=' + api_key)
	channels = requestChannels.json()
	return channels

def category_videos(name,current_page_number):
	"""Returns list of vidoes (25 per page) inside selected category"""
	for category in categories:
		if category[lang_api_prop] == name:
			skip = int(current_page_number) * 25
			category_id = category['ID']
			request_category_videos = requests.get(api_base_url + 'category/?id=' + category_id + '&skip=' + str(skip) + '&uid=' + api_key)
			videos = request_category_videos.json()
        return videos 

def search_videos():
	"""Returns search results vidoes"""
        search_heading = addon.getLocalizedString(30206)
	keyboard = xbmc.Keyboard()
        keyboard.setHeading(search_heading)
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		query = keyboard.getText()
		if query is None or len(str(query)) == 0:
			return
	else:
		return
	sort_videos = addon.getSetting('sort_videos')
	asc_order = addon.getSetting('asc_order')	
	request_search_videos = requests.get(api_base_url + 'videos/?query=' + query + '&order=' + str(sort_videos) + '&uid=' + api_key + '&asc=' + str(int(bool(asc_order))))
	videos = request_search_videos.json()
	return videos 

def category_video_count(category_id):
	"""Returns total number of videos inside the category"""
	request_category_video_count = requests.get(api_base_url + 'category/count/?id=' + category_id + '&uid=' + api_key)
	category_video_count = request_category_video_count.json()
	return category_video_count

def video_url_description(video_id):
	"""Returns video description"""
	request_video_url_description = requests.get(api_base_url + 'video/?id=' + video_id + '&uid=' + api_key).json()
	extract_keys = ['stream_url', 'opis']
	video_url_description = dict((k, request_video_url_description[k]) for k in extract_keys if k in request_video_url_description)
	return video_url_description

def recommended_videos():
	"""Returns list of recommended videos. The number of videos can be defined inside settings. Default is 20."""
	num_recommends = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('num_recommends')
	request_recommended_videos = requests.get(api_base_url + 'recommended/?number=' + str(num_recommends) + '&uid=' + api_key)
	videos = request_recommended_videos.json()
	return videos 

def list_search_or_recommended_videos(videos):
	if videos == None:
		return
	else:	
		for video in videos:
			category_id = video['ID_kategorija']
			name = video['naslov']
			video_id = video['ID']
			genre = video['kategorija']
			duration = reduce(lambda x, y: x*60+y, [int(i) for i in (video['trajanje'].replace(':',',')).split(',')])
			video_info = video_url_description(video_id)
			try:
				header = urllib.urlencode({'Referer':'https://meduza.carnet.hr'})
				url = video_info['stream_url'] +'|'+ header
				description = video_info['opis'].encode('utf-8')
			except KeyError:
				url = ''
				description = addon.getLocalizedString(30207)
				pass		
			image = video['slika']
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':image})
			li.setInfo( type="Video", infoLabels={ 
							"Plot": description, 
							"Genre": genre,
							"Duration": duration,
							"mediatype":"video"
								})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)
	
def list_category_videos(videos,current_page_number,foldername):
	if not videos:
		li_translate = addon.getLocalizedString(30208)
		li = xbmcgui.ListItem(li_translate, iconImage='DefaultVideo.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		for video in videos:
			category_id = video['ID_kategorija']
			video_num = category_video_count(category_id)['count']
			name = video['naslov']
			video_id = video['ID']
			duration = reduce(lambda x, y: x*60+y, [int(i) for i in (video['trajanje'].replace(':',',')).split(',')])
			video_info = video_url_description(video_id)
			header = urllib.urlencode({'Referer':'https://meduza.carnet.hr'})
			url = video_info['stream_url'] +'|'+ header
			image = video['slika']
			description = video_info['opis'].encode('utf-8')
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':image})
			li.setInfo( type="Video", infoLabels={ 
								"Plot": description, 
								"Duration": duration,
								"mediatype":"video"
								})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		pages_num = video_num / 25
		if int(current_page_number) < pages_num:
			int_current_page_number = int(current_page_number)
			int_current_page_number += 1
			current_page_number = str(int_current_page_number)
			url = build_url({'mode': 'folder', 'foldername': foldername, 'pagenumber': current_page_number})
			li = xbmcgui.ListItem('> Next Page (' + str(int_current_page_number + 1) + ')', iconImage="DefaultFolder.png")
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)		
		xbmcplugin.endOfDirectory(addon_handle)
		
def start_channel(channel_id,channel_video_count):
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	player = xbmc.Player()
	playlist.clear()
	requestChannel = requests.get(api_base_url + 'channel/?id=' + channel_id + '&uid=' + api_key)
	channel = requestChannel.json()
	channel_index = channel['index']
	schedule = channel['raspored']
	channel_offset = channel['offset']
	schedule_gen = ((i, j) for i, j in enumerate(schedule))
	for i, j in schedule_gen:
	        li = xbmcgui.ListItem(j['naslov'])
		li.setArt({'thumb':j['slika']})
		itemArgs = {
                'title': j['naslov'].encode('utf-8'),
                'plot': j['opis'].encode('utf-8'),
		'mediatype':'video',
                'tracknumber': i 
            	}
		li.setInfo('video', itemArgs)
		playlist.add(url=j['stream_url'],listitem=li)
        player.play(item=playlist,startpos=channel_index)
	player.seekTime(channel_offset)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
#set as video addon
xbmcplugin.setContent(addon_handle, 'videos')

addon=xbmcaddon.Addon('plugin.video.carnet-meduza')
api_base_url = 'https://meduza.carnet.hr/index.php/api/'
category_image_base_url = 'https://meduza.carnet.hr/uploads/images/categories/'
# api_key == device_id from register (import) device == uid
api_key = addon.getSetting('apikey')

mode = args.get('mode', None)

dir_recommends = addon.getLocalizedString(30201)
dir_categories = addon.getLocalizedString(30202)
dir_channels = addon.getLocalizedString(30203)
dir_search = addon.getLocalizedString(30204)
dir_settings = addon.getLocalizedString(30205)

# get api lang property (en|hr)
active_lang = xbmc.getLanguage()
if active_lang == 'Croatian':
	lang_api_prop = 'naziv'
else:
	lang_api_prop = 'naziv_en'

if mode is None:
    url = build_url({'mode': 'folder', 'foldername': dir_recommends})
    li = xbmcgui.ListItem(dir_recommends)
    li.setArt({'icon':'DefaultVideo.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': dir_categories})
    li = xbmcgui.ListItem(dir_categories) 
    li.setArt({'icon':'DefaultAddonVideo.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': dir_channels})
    li = xbmcgui.ListItem(dir_channels) 
    li.setArt({'icon':'DefaultAddonTvInfo.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': dir_search, 'foldername': dir_search})
    li = xbmcgui.ListItem(dir_search) 
    li.setArt({'icon':'DefaultAddonsSearch.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	
    url = build_url({'mode': dir_settings, 'foldername': dir_settings})
    li = xbmcgui.ListItem(dir_settings)
    li.setArt({'icon':'DefaultAddonProgram.png'})
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
	if args['foldername'][0].decode('utf-8') == dir_recommends:
		videos =  recommended_videos()
		list_search_or_recommended_videos(videos)

	elif args['foldername'][0].decode('utf-8') == dir_categories:
		categories = categories()
		categoryGen = (category for category in categories if category['naziv'] != 'YouTube')
		for category in categoryGen:
			active_lang = xbmc.getLanguage()
			name = category[lang_api_prop].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			categoryImage = category_image_base_url + category['slika']
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':categoryImage})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		xbmcplugin.endOfDirectory(addon_handle)

	elif args['foldername'][0].decode('utf-8') == dir_channels:
		channels = channels()
		for channel in channels:
			name = channel['naziv'].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			channelImage = channel.get('slika','')
			li = xbmcgui.ListItem(name)
			li.setArt({'icon':channelImage})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)

	else:
		categories = categories()
		channels = channels()
		foldername = args['foldername'][0]
		#api response is 'list of dictionaries' so using lambda is nice way of checking for values
		if filter(lambda name: name[lang_api_prop] == foldername.decode('utf-8'), categories):
			current_page_number = args.get('pagenumber',['0'])[0]
			videos =  category_videos(foldername.decode('utf-8'),current_page_number)
			list_category_videos(videos,current_page_number,foldername.decode('utf-8'))
		else:
			channel = filter(lambda name: name['naziv'] == foldername.decode('utf-8'), channels)
			channel_id = channel[0]['ID'].encode('utf-8')
			channel_video_count = channel[0]['emisije'].encode('utf-8')
			start_channel(channel_id,channel_video_count)

elif mode[0] == dir_search:
	videos = search_videos()
	list_search_or_recommended_videos(videos)

elif mode[0] == dir_settings:		
	xbmcaddon.Addon().openSettings()	
else:
	pass

