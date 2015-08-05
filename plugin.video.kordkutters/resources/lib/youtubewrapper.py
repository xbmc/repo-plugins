#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
 Author: enen92 

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
import urllib
import json
import re
import os
import sys
import math
import xbmcaddon
import xbmcplugin
from common_variables import *
from directory import *

#get list of playlists
def get_playlists():
	url = 'https://www.googleapis.com/youtube/v3/playlists?part=snippet,contentDetails&channelId='+channel_id+'&maxResults=50&key='+youtube_api_key
	raw = urllib.urlopen(url)
	resp = json.load(raw)
	raw.close()
	totalplaylists = len(resp["items"])
	for playlist in resp["items"]:
		playlist_id = playlist["id"]
		thumb = playlist["snippet"]["thumbnails"]["high"]["url"]
		label = playlist["snippet"]["title"]
		addDir('[B]'+label.encode('utf-8')+'[/B]',playlist_id,1,thumb,1,totalplaylists,token='')
	return

#get list of live videos
def get_live_videos():
	list_of_tupple_items = []
	
	url = 'https://www.googleapis.com/youtube/v3/search?eventType=live&part=snippet&channelId='+channel_id+'&type=video&maxResults=50&key='+youtube_api_key
	raw = urllib.urlopen(url)
	resp = json.load(raw)
	raw.close()
	if resp["items"]:
		video_ids = []
		for item in resp["items"]:
			videoid = item["id"]["videoId"]
			video_ids.append(videoid)
		video_ids = ','.join(video_ids)
		url_api = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id='+video_ids+'&key='+youtube_api_key
		raw = urllib.urlopen(url_api)
		resp = json.load(raw)
		raw.close()
		
		for item in resp["items"]:
			title = item["snippet"]["title"]
			plot = item["snippet"]["description"]
			thumb = item["snippet"]["thumbnails"]["high"]["url"]
			aired = item["snippet"]["publishedAt"]
			videoid = item["id"]
			episode = re.findall('(\d+)',title)
						
			try: 
				aired = re.compile('(.+?)-(.+?)-(.+?)T').findall(aired)[0]
				date = aired[2] + '.' + aired[1] + '.' + aired[0]
				aired = aired[0]+'-'+aired[1]+'-'+aired[2]
			except: 
				aired = ''
				date = ''
			
			infolabels = {'plot':plot.encode('utf-8'),'tvshowtitle':tvshowtitle,'title':title.encode('utf-8'),'originaltitle':title.encode('utf-8'),'aired':aired,'date':date,'status':status,'cast':cast,'episode':episode,'playcount':0}
			
			#Video and audio info
			video_info = { 'codec': 'avc1', 'aspect' : 1.78 }
			audio_info = { 'codec': 'aac', 'language' : 'en' }
			try:
				if item["contentDetails"]["definition"].lower() == 'hd':
					video_info['width'] = 1280
					video_info['height'] = 720
					audio_info['channels'] = 2
				else:
					video_info['width'] = 854
					video_info['height'] = 480
					audio_info['channels'] = 1
				try:
					if xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality.ask') == 'false' and xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality') != '3' and xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality') != '4':
						video_info['width'] = 854
						video_info['height'] = 480
						audio_info['channels'] = 1
				except: pass	
			except:
				video_info['width'] = 854
				video_info['height'] = 480
				audio_info['channels'] = 1		
			
			#build and append item
			tupple = build_episode_item(title.encode('utf-8'),videoid,5,thumb,1,infolabels,video_info,audio_info)
			list_of_tupple_items.append(tupple)
		
		if list_of_tupple_items:
			number_of_items = len(list_of_tupple_items)
			xbmcplugin.addDirectoryItems(int(sys.argv[1]), list_of_tupple_items,totalItems=number_of_items)
			add_sort_methods()
				
		xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	else:
		msgok(translate(30000),translate(30002))
		sys.exit(0)
		
#Get uploads playlist id and return the list of all videos videos uploaded by the channel user
def get_all_youtube_uploads():
	url_api = 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id='+channel_id+'&key='+youtube_api_key
	raw = urllib.urlopen(url_api)
	resp = json.load(raw)
	raw.close()
	if "items" in resp.keys():
		try:
			uploads_playlist = resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
			return_youtubevideos('all',uploads_playlist,'',1)
		except:
			sys.exit(0)
	else:
		sys.exit(0)
	return

#Get list of vod videos
def return_youtubevideos(name,url,token,page):
	items_per_page = int(selfAddon.getSetting('items_per_page'))
	list_of_tupple_items = []

	if page != 1:
		url_api = 'https://www.googleapis.com/youtube/v3/playlistItems?part=id,snippet,contentDetails&maxResults='+str(items_per_page)+'&playlistId='+url+'&key='+youtube_api_key +'&pageToken='+token
	else:
		url_api = 'https://www.googleapis.com/youtube/v3/playlistItems?part=id,snippet,contentDetails&maxResults='+str(items_per_page)+'&playlistId='+url+'&key='+youtube_api_key

	raw = urllib.urlopen(url_api)
	resp = json.load(raw)
	raw.close()
	try: nextpagetoken = resp["nextPageToken"]
	except: nextpagetoken = ''
	try: availablevideos = resp["pageInfo"]["totalResults"]
	except: availablevideos = 1
	returnedVideos = resp["items"]
	totalvideos = len(returnedVideos)
	totalpages = int(math.ceil((float(availablevideos)/items_per_page)))
	video_ids = []
	if returnedVideos:
		for video in returnedVideos:
			videoid = video["contentDetails"]["videoId"]
			video_ids.append(videoid)
		video_ids = ','.join(video_ids)
		url_api = 'https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id='+video_ids+'&key='+youtube_api_key
		raw = urllib.urlopen(url_api)
		resp = json.load(raw)
		raw.close()
		returnedVideos = resp["items"]
		
		for video in returnedVideos:
			title = video["snippet"]["title"]
			plot = video["snippet"]["description"]
			aired = video["snippet"]["publishedAt"]
			thumb = video["snippet"]["thumbnails"]["high"]["url"]
			videoid = video["id"]
			#process duration
			duration_string = video["contentDetails"]["duration"]
			try: duration = return_duration_as_seconds(duration_string)
			except: duration = '0'
			try: 
				aired = re.compile('(.+?)-(.+?)-(.+?)T').findall(aired)[0]
				date = aired[2] + '.' + aired[1] + '.' + aired[0]
				aired = aired[0]+'-'+aired[1]+'-'+aired[2]
			except: 
				aired = ''
				date = ''
			try:
				if episode_playlists:
					if url in episode_playlists:
						episode = re.compile('(\d+)').findall(title)[0]
					else: episode = ''
				else: episode = ''
			except: episode = ''
			#playcount
			if os.path.exists(os.path.join(watchedfolder,str(videoid)+'.txt')) : playcount = 1
			else: playcount = 0
		
			infolabels = {'plot':plot.encode('utf-8'),'aired':aired,'date':date,'tvshowtitle':tvshowtitle,'title':title.encode('utf-8'),'originaltitle':title.encode('utf-8'),'status':status,'cast':cast,'duration':duration,'episode':episode,'playcount':playcount}
			
			#Video and audio info
			video_info = { 'codec': 'avc1', 'aspect' : 1.78 }
			audio_info = { 'codec': 'aac', 'language' : 'en' }
			try:
				if video["contentDetails"]["definition"].lower() == 'hd':
					video_info['width'] = 1280
					video_info['height'] = 720
					audio_info['channels'] = 2
				else:
					video_info['width'] = 854
					video_info['height'] = 480
					audio_info['channels'] = 1
				try:
					if xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality.ask') == 'false' and xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality') != '3' and xbmcaddon.Addon(id='plugin.video.youtube').getSetting('kodion.video.quality') != '4':
						video_info['width'] = 854
						video_info['height'] = 480
						audio_info['channels'] = 1
				except: pass	
			except:
				video_info['width'] = 854
				video_info['height'] = 480
				audio_info['channels'] = 1		
			
			#build and append item
			tupple = build_episode_item(title.encode('utf-8'),videoid,5,thumb,page,infolabels,video_info,audio_info)
			list_of_tupple_items.append(tupple)

	if list_of_tupple_items:
		number_of_items = len(list_of_tupple_items)
		xbmcplugin.addDirectoryItems(int(sys.argv[1]), list_of_tupple_items,totalItems=number_of_items)
	
		add_sort_methods()
	if totalpages > 1 and (page+1) <= totalpages:
		addDir('[B]'+translate(30010)+'[/B] '+str(page)+'/'+str(totalpages),url,1,os.path.join(artfolder,'next.png'),page+1,1,token=nextpagetoken)
	xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
	return

#Play a youtube video given the video_id	
def play_youtube_video(url):
	video_url = 'plugin://plugin.video.youtube?path=/root/video&action=play_video&videoid='+url
	item = xbmcgui.ListItem(path=video_url)
	xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
	player = KKPlayer(mainurl=url)
	player.play(video_url,item)
	while player._playbackLock:
		player._trackPosition()
		xbmc.sleep(1000)
	return
	
#receives a duration string and returns the duration in seconds (as string)
def return_duration_as_seconds(string):
	totalseconds = 0
	hours = re.findall('(\d+)H',string)
	minutes = re.findall('(\d+)M',string)
	seconds = re.findall('(\d+)S',string)
	if hours: totalseconds += 3600*int(hours[0])
	if minutes: totalseconds += 60*int(minutes[0])
	if seconds: totalseconds += int(seconds[0])
	return str(totalseconds)
	

