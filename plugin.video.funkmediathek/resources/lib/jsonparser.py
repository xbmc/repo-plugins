# -*- coding: utf-8 -*-
import json
import libmediathek3 as libMediathek
base = 'https://api.funk.net/v1.1'

auth = '29ad11c93ad19f816de90c1c8ae4ec0354c6b5e4ec5b3965f125248cfa60bfe1'
fanart = libMediathek.fanart

header = 	{
			'Authorization':auth[::-1],
			'User-Agent':'okhttp/3.2.0',
			'Accept-Encoding':'gzip',
			'Host':' api.funk.net',
			}

types = {
'format':'formats',
'series':'series',
}

def parse(url):
	response = libMediathek.getUrl(url,header)
	j = json.loads(response)
	l = []
	if 'includes' in j:
		part = 'includes'
	else:
		part = 'data'
	for item in j[part]:
		if item['type'] == 'series' or item['type'] == 'format':
			d = _parseSeries(item,types[item['type']])
			if d:
				l.append(d)
		elif item['type'] == 'video':
			l.append(_parseVideo(item))
		else:
			libMediathek.log('unkown type: '+item['type'])
	return l
	
def _parseSeries(j,type):
	d = {}
	if 'name' in j['attributes']:
		if j['attributes']['name'] == 'funk Livestream': return False
		d['_name'] = j['attributes']['name']
	else:
		if j['attributes']['title'] == 'funk Livestream': return False
		d['_name'] = j['attributes']['title']
	if 'thumbnail' in j['attributes']:
		d['_thumb'] = j['attributes']['thumbnail']
	else:
		d['_thumb'] = fanart
	if type == 'series':
		d['_fanart'] = fanart
	if 'description' in j['attributes']:
		d['_plot'] = _cleanPlot(j['attributes']['description'])
	d['_airedISO8601'] = j['attributes']['createdAt']
	d['url'] = base + '/content/'+type+'/' + j['id'] + '?should_filter=false'#
	d['_rating'] = str(j['attributes']['kickKeepRatio'] * 10)
	d['mode'] = 'listDir'
	d['_type'] = 'season'
	return d

def _parseVideo(j):
	d = {}
	d['_name'] = j['attributes']['title']
	
	d['_thumb'] = j['attributes']['image']['url']
	if 'text' in j['attributes']:
		d['_plot'] = _cleanPlot(j['attributes']['text'])
		while '\n\n\n' in d['_plot']:
			d['_plot'] = d['_plot'].replace('\n\n\n','\n\n')
	d['_duration'] = str(j['attributes']['duration'])
	if 'season' in j['attributes']:
		d['_season'] = j['attributes']['season']
	if 'episode' in j['attributes']:
		d['_episode'] = j['attributes']['episode']
		d['_type'] = 'episode'
	else:
		d['_type'] = 'video'
	if 'fsk' in j['attributes']:
		d['_mpaa'] = 'FSK ' + str(j['attributes']['fsk'])
	
	d['_airedISO8601'] = j['attributes']['createdAt']
	
	d['sourceId'] = j['attributes']['sourceId']
	d['mode'] = 'play'
	return d
	
def _cleanPlot(plot):
	plot = plot.replace('<p>','')
	plot = plot.replace('</p>','')
	plot = plot.replace('<h4>','')
	plot = plot.replace('</h4>','')
	while '  ' in plot:
		plot = plot.replace('  ',' ')
	#plot = plot.replace('\n ','')
	return plot
	