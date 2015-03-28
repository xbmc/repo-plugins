# -*- coding: utf-8 -*-

#Copyright (C) 2015 Fiona Schmidtke
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program. If not, see <http://www.gnu.org/licenses/>.

from xbmcswift2 import Plugin, xbmc, xbmcgui, xbmcaddon
from bs4 import BeautifulSoup
import urllib2,urllib,json,re

addon = xbmcaddon.Addon()
localize = addon.getLocalizedString

plugin = Plugin()

baseURL  = 'http://www.sportschau.de'
videoURL = baseURL + '/video/index.html'
liveURL  = baseURL + '/ticker/index.html'

jsonurlregexp  = re.compile('\'mcUrl\':\'([^\']*json)\'')

def getVideoEntryFromJson(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	json_data = response.read()
	response.close()
	data = json.loads(json_data)
	url =  data['_mediaArray'][1]['_mediaStreamArray'][0]['_stream'][0]
	return {
		'icon': data['_previewImage'],
		'url': url
	}

def getEntryFromHtml(box):
	obj = None
	titleEl = box.select("h4.headline")
	if titleEl:
		title = titleEl[0].get_text()
		imgEl = box.select("img.img")
		mediaLink = box.select("a.mediaLink")
		if mediaLink:
			data = mediaLink[0].get("data-ctrl-player")
			if data:
				match = jsonurlregexp.search(data)
				url = match.group(1)
				if url:
					obj = {
						'title': title.strip(),
						'url': baseURL+url
					}
					if imgEl:
						obj['icon'] = baseURL + imgEl[0].get('src')
	return obj

def getEntries(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html = BeautifulSoup(response.read())
	response.close()
	boxes = html.select("div.teaser")
	objs = []
	for box in boxes:
		obj = getEntryFromHtml(box)
		if obj:
			objs.append(obj)
		links = box.select(".linklist a")
		for link in links:
			elTitle = link.get_text().strip().split('|')
			title = elTitle[0]
			if 'video' in elTitle[1]:
				other = getEntries(baseURL+link.get('href'))
				objs.extend(other)
	return objs

def getStreams():
	req = urllib2.Request(liveURL)
	response = urllib2.urlopen(req)
	html = BeautifulSoup(response.read())
	response.close()
	sideboxes = html.select("div.sectionC .box")
	objs = []
	for box in sideboxes:
		dateEl = box.select("h3.ressort")
		if dateEl:
			date = dateEl[0].get_text().strip()
			links = box.select(".linklist a")
			for link in links:
				elTitle = link.get_text().strip().split('|')
				title = elTitle[0] + localize(30003)+' '+date
				if 'video' in elTitle[1]:
					videos = getEntries(baseURL+link.get('href'))
					if videos:
						video = videos[0]
						if video['url']:
							obj = {
								'title': title,
								'url': video['url'],
								'icon': video['icon']
							}
							objs.append(obj)
		obj = getEntryFromHtml(box)
		if obj:
			objs.append(obj)
	return objs

def getGroups():
	req = urllib2.Request(videoURL)
	response = urllib2.urlopen(req)
	html = BeautifulSoup(response.read())
	response.close()
	naviHtml = html.select(".clubNavi .entry a")
	objs = []
	for group in naviHtml:
		if group.get("href"):
			obj = {
				'title': group.get_text(),
				'url': baseURL+group.get("href")
			}
			objs.append(obj)
	return objs

@plugin.route('/')
def index():
	item = {
		'label': localize(30002),
		'path': plugin.url_for('show_live')
	}
	item2 = {
		'label': localize(30001),
		'path': plugin.url_for('show_videos')
	}
	return [item, item2]

@plugin.route('/live/')
def show_live():
	try:
		items = []
		streams = getStreams()
		for stream in streams:
			video = getVideoEntryFromJson(stream['url'])
			icon  = video['icon']
			item = {
				'label': stream['title'],
				'path': video['url'],
				'icon': icon,
				'thumbnail': icon,
				'is_playable': True
			}
			items.append(item)

		return items
	except:
		return []

@plugin.route('/videos/')
def show_videos():
	try:
		items = []
		groups = getGroups()
		for group in groups:
			item = {
				'label': group['title'],
				'path': plugin.url_for('show_video', group=urllib.quote(group['url']))
			}
			items.append(item)
		return items
	except:
		return []

@plugin.route('/videos/<group>')
def show_video(group):
	try:
		items = []
		url = urllib.unquote(group)
		entries = getEntries(url)
		for entry in entries:
			video = getVideoEntryFromJson(entry['url'])
			icon = video['icon']
			if entry['icon']:
				icon = entry['icon']
			item = {
				'label': entry['title'],
				'path': video['url'],
				'icon': icon,
				'thumbnail': icon,
				'is_playable': True
			}
			if item['path'] == None:
				continue
			items.append(item)
		return items
	except:
		return []

if __name__ == '__main__':
	plugin.run()
