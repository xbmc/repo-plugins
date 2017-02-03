# -*- coding: utf-8 -*-
import libmediathek3 as libMediathek
import xbmcplugin
import json
import mediathekxmlservice as xmlservice
import re
import HTMLParser

translation = libMediathek.getTranslation
parser = HTMLParser.HTMLParser()

baseUrl = 'http://phoenix.de/php/appinterface/appdata.php'
rssUrl = 'http://www.phoenix.de/bibliothek/rss'

def main():
	response = libMediathek.getUrl(baseUrl + '?c=videorubriken')
	j = json.loads(response)
	l = []
	for result in j['results']:
		d = {}
		d['_name'] = result['name']
		d['url'] = baseUrl + '?c=videos&rub=' + str(result['id'])
		d['mode'] = 'listVideos'
		d['_type'] = 'dir'
		l.append(d)
	d = {}
	d['_name'] = translation(31041)
	d['mode'] = 'listRss'
	d['_type'] = 'dir'
	l.append(d)
	return l
	
def listVideos():
	response = libMediathek.getUrl(params['url'])
	j = json.loads(response)
	l = []
	for video in j['videos']:
		d = {}
		d['_name'] = video['title']
		d['_plot'] = video['title']
		d['_epoch'] = video['datesec']
		if video['image_ipad'] != '':
			id = video['image_ipad'].split('.')[-2]
			d['_thumb'] = video['image_ipad'].replace(id,str(int(id) - 1))
		d['url'] = 'http://www.phoenix.de/php/mediaplayer/data/beitrags_details.php?ak=web&id=' + str(video['id'])
		d['mode'] = 'play'
		d['_type'] = 'video'
		l.append(d)		
	return l
	
def listRss():
	response = libMediathek.getUrl(rssUrl)
	items = re.compile('<item>(.+?)</item>', re.DOTALL).findall(response.decode('iso-8859-1'))
	l = []
	for item in items:
		#the encoding is fucked up
		#i'm not gonna fix this mess by hand
		d = {}
		#d['_airedISO8601'] = re.compile('<pubDate>(.+?)</pubDate>').findall(item)[0]
		d['_name'] = parser.unescape(re.compile('<title>(.+?)</title>').findall(item)[0])
		d['_channel'] = re.compile('<itunes:author>(.+?)</itunes:author>').findall(item)[0]
		d['_plot'] = parser.unescape(re.compile('<itunes:summary>(.+?)</itunes:summary>', re.DOTALL).findall(item)[0])
		d['url'] = 'http://www.phoenix.de/php/mediaplayer/data/beitrags_details.php?ak=web&id=' + re.compile('<guid>(.+?)</guid>').findall(item)[0].decode('ISO-8859-1')
		d['mode'] = 'play'
		d['_type'] = 'video'
		l.append(d)
		
	return l
	
def play():
	return xmlservice.getVideoUrl(params['url'])

modes = {
'main': main,
'listVideos': listVideos,
'listRss': listRss,
'play': play
}	

def list():	
	global params
	params = libMediathek.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	
	mode = params.get('mode','main')
	
	if mode == 'play':
		libMediathek.play(play())
	else:
		l = modes.get(mode,main)()
		libMediathek.addEntries(l)
		xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)	
list()