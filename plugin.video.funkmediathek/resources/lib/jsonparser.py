# -*- coding: utf-8 -*-
import json
import libmediathek3 as libMediathek
base = 'https://www.funk.net/api/v4.0'
webbase = 'https://www.funk.net/data/'

fanart = libMediathek.fanart

types = {
'format':'formats',
'series':'series',
}

#v3.0
#auth = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbCIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxzZWFyY2gtYXBpIn0.q4Y2xZG8PFHai24-4Pjx2gym9RmJejtmK6lMXP5wAgc'
#v3.1
#auth = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbC12Mi4wIiwic2NvcGUiOiJzdGF0aWMtY29udGVudC1hcGksY3VyYXRpb24tc2VydmljZSxzZWFyY2gtYXBpIn0.SGCC1IXHLtZYoo8PvRKlU2gXH1su8YSu47sB3S4iXBI'
auth = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoid2ViYXBwLXYzMSIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxuZXh4LWNvbnRlbnQtYXBpLXYzMSx3ZWJhcHAtYXBpIn0.mbuG9wS9Yf5q6PqgR4fiaRFIagiHk9JhwoKES7ksVX4'

#auth = 'eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbCIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxzZWFyY2gtYXBpIn0.'
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbCIsInNjb3BlIjoic3RhdGljLWNvbnRlbnQtYXBpLGN1cmF0aW9uLWFwaSxzZWFyY2gtYXBpIn0.q4Y2xZG8PFHai24-4Pjx2gym9RmJejtmK6lMXP5wAgc
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnROYW1lIjoiY3VyYXRpb24tdG9vbC12Mi4wIiwic2NvcGUiOiJzdGF0aWMtY29udGVudC1hcGksY3VyYXRpb24tc2VydmljZSxzZWFyY2gtYXBpIn0.SGCC1IXHLtZYoo8PvRKlU2gXH1su8YSu47sB3S4iXBI
header = 	{
			'Authorization':auth,
			'Accept-Encoding':'gzip',
			}

def parseMain():
	onlySeries = libMediathek.getSetting('skipToSeries') == 'true'
	response = libMediathek.getUrl(webbase+'/static/channels',False)
	j = json.loads(response)
	l = []
	if not 'list' in j:
		return l
	for item in j['list']:
		if not 'type' in item:
			continue
		elif item['type'] == 'format' or item['type'] == 'series':
			try:
				d = {}
				d['_name'] = item['title']
				if 'publicationDate' in item:
					d['_airedISO8601'] = item['publicationDate']
				if 'shortDescription' in item:
					d['_plot'] = item['shortDescription']
				if 'description' in item:
					d['_plot'] = item['description']
				if 'imageSquare' in item:
					imgurl = base + '/thumbnails/' + item['imageSquare'] + '?quality=85&width=200'
					d['_thumb'] = imgurl
				if 'imageOrigin' in item and item['imageOrigin'] != None:
					imgurl = base + '/thumbnails/' + item['imageOrigin'] + '?quality=85'
					d['_fanart'] = imgurl
				else:
					d['_fanart'] = fanart
				d['_type'] = 'dir'
				d['id'] = item['alias']
				if item['type'] == 'series':
					d['mode'] = 'listSeasons'
					if 'imageSquare' in item:
						d['fallbackimage'] = item['imageSquare']
				elif item['type'] == 'format':
					d['mode'] = 'listVideos'
				
				l.append(d)
			except:
				libMediathek.log(json.dumps(item))
		elif item['type'] == 'archiveformat':
			continue
		else:
			continue
	for item in j['list']:
		if 'type' in item and item['type'] == 'archiveformat':
			d = {}
			d['_name'] = item['title']
			if 'imageLandscape' in item:
				imgurl = base + '/thumbnails/' + item['imageSquare'] + '?quality=85&width=244'
				d['_thumb'] = imgurl
			if 'imageOrigin' in item and item['imageOrigin'] != None:
				imgurl = base + '/thumbnails/' + item['imageOrigin'] + '?quality=85'
				d['_fanart'] = imgurl
			else:
				d['_fanart'] = fanart
			d['id'] = item['alias']
			d['_type'] = 'dir'
			d['mode'] = 'listVideos'
			l.append(d)
	return l
	
	
def parseSeasons(id, params):
	#response = libMediathek.getUrl(base+'/content/playlists/filter/?channelId=' + id + '&secondarySort=alias,ASC',header)
	#https://www.funk.net/api/v3.1/webapp/playlists/byChannelAlias/alles-liebe-annette?sort=language,ASC
	url = webbase + 'seasons/byChannelAlias/' + id
	response = libMediathek.getUrl(url,False)
	j = json.loads(response)
	l = []
	#libMediathek.log(response)
	for item in j['list']:
		d = {}
		d['_name'] = item['title']
		if 'shortDescription' in item:
			d['_plot'] = item['shortDescription']
		if 'description' in item:
			d['_plot'] = item['description']
		if 'fallbackimage' in params:
			imgurl = base + '/thumbnails/' + params['fallbackimage'] + '?quality=85&width=244'
			d['_thumb'] = imgurl
		d['_type'] = 'season'
		d['id'] = item['alias']
		d['mode'] = 'listEpisodes'
		l.append(d)
	return l
	
def parseEpisodes(id):
	#response = libMediathek.getUrl(base+'/content/playlists/'+id+'/videos/?size=100&secondarySort=episodeNr,ASC',header)
	#https://www.funk.net/api/v3.1/webapp/videos/byPlaylistAlias/alles-liebe-annette-staffel-1?filterFsk=false&size=100&sort=episodeNr,ASC
	url = base+'/webapp/videos/byPlaylistAlias/'+id+'?filterFsk=false&size=100&sort=episodeNr,ASC'
	url = webbase + 'videos/bySeasonAlias/' + id
	response = libMediathek.getUrl(url,False)
	j = json.loads(response)
	l = []
	for item in j['list']:
		d = {}
		d['_name'] = item['title']
		if 'shortDescription' in item:
			d['_plot'] = item['shortDescription']
		if 'description' in item:
			d['_plot'] = item['description']
		d['_duration'] = item['duration']
		if 'imageLandscape' in item:
			imgurl = base + '/thumbnails/' + item['imageLandscape'] + '?quality=85&width=244'
			d['_thumb'] = imgurl
		if 'seasonNr' in item:
			# workaround bug in script.module.libmediathek3/lib/libmediathek3listing.py:addEntries():74
			season = str(item['seasonNr'])
			d['_Season'] = season
			d['_season'] = season
		if 'episodeNr' in item:
			d['_episode'] = str(item['episodeNr'])
		if 'fsk' in item:
			d['_mpaa'] = str(item['fsk'])
		d['_type'] = 'episode'
		d['sourceId'] = str(item['entityId'])
		d['mode'] = 'play'
		l.append(d)
	return l
	
def parseVideos(id):
	#https://www.funk.net/api/v3.0/content/videos/filter?channelId=auf-einen-kaffee-mit-moritz-neumeier&page=0&size=20
	#response = libMediathek.getUrl(base+'/content/videos/filter?channelId='+id+'&page=0&size=100',header)
	#https://www.funk.net/api/v3.1/webapp/playlists/byChannelAlias/auf-einen-kaffee-mit-moritz-neumeier?sort=language,ASC
	#https://www.funk.net/api/v3.1/webapp/videos/byChannelAlias/auf-einen-kaffee-mit-moritz-neumeier?filterFsk=false&sort=creationDate,desc&page=0&size=20
	url = webbase + 'videos/byChannelAlias/'+id
	response = libMediathek.getUrl(url,False)
	j = json.loads(response)
	l = []
	for item in j['list']:
		d = {}
		d['_name'] = item['title']
		if 'shortDescription' in item:
			d['_plot'] = item['shortDescription']
		if 'publicationDate' in item:
			d['_airedISO8601'] = item['publicationDate']
		if 'description' in item:
			d['_plot'] = item['description']
		if 'imageLandscape' in item:
			imgurl = base + '/thumbnails/' + item['imageLandscape'] + '?quality=85&width=244'
			d['_thumb'] = imgurl
		d['_duration'] = item['duration']
		d['_type'] = 'video'
		d['sourceId'] = str(item['entityId'])
		d['mode'] = 'play'
		l.append(d)
	return l
