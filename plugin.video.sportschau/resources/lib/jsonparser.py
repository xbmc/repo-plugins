# -*- coding: utf-8 -*-
import requests

base = 'https://exporte.wdr.de/SportschauAppServer'


def getStreams(url):
	j = requests.get(url).json()
	result = {'items':[]}
	for item in j['items']:
		title = item['title'].split(', ')[-1]
		for teaser in item['teasers']:
			if teaser['_links']['target']['type'] != 'ExternalLink':
				d = {'type':'video', 'params':{'mode':'playStream'}, 'metadata':{}}
				tmpname = teaser['title'].split('|',1)[-1][1:]
				d['metadata']['name'] = title + ' - ' + tmpname[0].upper()+tmpname[1:]
				d['metadata']['plot'] = teaser['description']
				d['params']['url'] = teaser['_links']['target']['href']
				day,month = title.split('.')
				d['metadata']['date'] = day+'.'+month.replace(' ','')+'.2019'
				t = teaser['title'].split('ab')[-1].replace(' ','').replace('Uhr','').split('.')
				if len(t) == 1:
					d['metadata']['airedtime'] = t[0]+':00'
				else:
					d['metadata']['airedtime'] = t[0]+':'+t[1]
				for image in teaser['image']['images']:
					if image['formatName'] == 'TeaserAufmacher':
						d['metadata']['art'] = {'thumb': image['imageUrl']}
				result['items'].append(d)
	return result

def getStream(url):
	j = requests.get(url).json()
	if 'type' in j and j['type'] == 'audio/mpeg':
		return {'media':[{'url':j['url'], 'type':'audio', 'stream':'audio'}]}
	else:
		return {'media':[{'url':j['entries'][0]['url'], 'type':'video', 'stream':'HLS'}]}