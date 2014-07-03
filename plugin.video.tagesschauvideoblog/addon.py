# -*- coding: utf-8 -*-

#Copyright (C) 2013 Fiona Schmidtke, Niclas Hoyer
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
import urllib2,urllib,re,feedparser,HTMLParser

addon = xbmcaddon.Addon()
localize = addon.getLocalizedString

plugin = Plugin()

tagesschauURL = 'http://www.tagesschau.de/'

h264regexp  = re.compile('http:\/\/[^"]+webl\.h264\.mp4')
videoregexp = re.compile(re.escape(tagesschauURL)+'ausland\/videoblog\/[^"]+')

blogsregexp      = re.compile('Startseite Videoblog(.*)subressort', re.MULTILINE|re.DOTALL)
blogurlregexp    = re.compile('a href="(\/videoblog\/[^"]+)"')
blogtitleregexp  = re.compile('">([^<]+)<\/a><\/li>')
entriesregexp    = re.compile('a\thref="(\/videoblog\/[^"]+)">\n[^\n]*\n<h4 class="headline">([^<]*)<\/h4>', re.MULTILINE|re.DOTALL)
teaserregexp     = re.compile('img[^>]+src="(\/multimedia\/bilder\/[^"]+teaser+[^"]+)')

def removeNonAscii(s):
	return "".join(i for i in s if ord(i)<128)

def parseTitle(title):
	if title.startswith('Videoblog: '):
		title = title[11:]
	elif title.startswith('Videoblog '):
		title = title[10:]
	title = title.replace('&#034;','"');
	return title

def getVideoPageUrl(desc):
	match = videoregexp.search(desc)
	return match.group(0)

def getH264Video(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html = response.read()
	response.close()
	match = h264regexp.search(html)
	if match == None:
		return None
	return match.group(0)

def getBlogs():
	req = urllib2.Request(tagesschauURL+'videoblog/index.html')	
	response = urllib2.urlopen(req)
	html = response.read()
	response.close()
	match = blogsregexp.search(html)
	text = match.group(0)
	matchUrl = blogurlregexp.findall(text)
	matchTitle = blogtitleregexp.findall(text)
	h = HTMLParser.HTMLParser()
	objs = []
	i = 0
	for url in matchUrl:
		obj = {
			'title': h.unescape(matchTitle[i]),
			'url': tagesschauURL+url
		}
		objs.append(obj)
		i = i + 1
	return objs

def getEntries(url):
	req = urllib2.Request(url)
	response = urllib2.urlopen(req)
	html = response.read()
	response.close()
	entries = entriesregexp.findall(html)
	teasers = teaserregexp.findall(html)
	objs = []
	i = 0
	for entry in entries:
		obj = {
			'title': parseTitle(entry[1]),
			'url': tagesschauURL+entry[0],
			'teaser': tagesschauURL+teasers[i]
		}
		objs.append(obj)
		i = i + 1
	return objs

@plugin.route('/')
def index():
	item = {
		'label': localize(32002),
		'path': plugin.url_for('show_newest')
	}
	item2 = {
		'label': localize(32001),
		'path': plugin.url_for('show_all')
	}
	return [item, item2]

@plugin.route('/newest/')
def show_newest():
	try:
		feed = feedparser.parse('http://meta.tagesschau.de/tag/videoblog/feed')
		items = []
		for entry in feed.entries:
			item = {
				'label': parseTitle(entry.title),
				'path': getH264Video(getVideoPageUrl(entry.description)),
				'is_playable': True
			}
			if item['path'] == None:
				continue
			items.append(item)
			
		return items
	except:
		return []

@plugin.route('/blogs/')
def show_all():
	try:
		items = []
		blogs = getBlogs()
		for blog in blogs:
			item = {
				'label': blog['title'],
				'path': plugin.url_for('show_blog', blog=urllib.quote(blog['url']))
			}
			items.append(item)
			
		return items
	except:
		return []

@plugin.route('/blogs/<blog>')
def show_blog(blog):
	try:
		items = []
		url = urllib.unquote(blog)
		entries = getEntries(url)
		for entry in entries:
			item = {
				'label': entry['title'],
				'path': getH264Video(entry['url']),
				'icon': entry['teaser'],
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
