# -*- coding: utf-8 -*-
import requests
import json

base = 'https://www.phoenix.de/response/template/'


def parseMain():
	j = requests.get(f'{base}sendungseite_overview_json').json()
	result = {'items':[],'pagination':{'currentPage':0}}
	for item in j['content']['items']:
		d = {'type':'dir', 'params':{'mode':'listVideos'}, 'metadata':{'art':{}}}
		d['metadata']['name'] = item['titel']
		d['metadata']['plot'] = item['typ']
		d['metadata']['art']['thumb'] = f'https://www.phoenix.de{item["bild_m"]}'
		d['params']['id'] = item['link'].split('-')[-1].split('.')[0]
		result['items'].append(d)
	return result
	
def parseVideos(id):
	j = requests.get(f'{base}vod_main_json?id={id}').json()
	result = {'items':[],'pagination':{'currentPage':0}}
	if j is not None:
		for item in j:
			d = {'type':'video', 'params':{'mode':'playVideo'}, 'metadata':{'art':{}}}
			d['metadata']['name'] = item['title']
			d['metadata']['plot'] = item['text_vorspann']
			d['metadata']['art']['thumb'] = 'https://www.phoenix.de' + item['thumbnail_medium']['systemurl_gsid'].replace('thumbnail_medium','thumbnail_large')
			d['params']['smubl'] = item['smubl']
			result['items'].append(d)
	return result
	
def getVideoUrl(smubl):
	j = requests.get(f'https://tmd.phoenix.de/tmd/2/ngplayer_2_3/vod/ptmd/phoenix/{smubl}').json()
	for prio in j['priorityList']:
		if prio['formitaeten'][0]['mimeType'] == 'application/x-mpegURL':
			for quality in prio['formitaeten'][0]['qualities']:
				if quality['quality'] == 'auto':
					url = quality['audio']['tracks'][0]['uri']
	return {'media':[{'url':url, 'type':'video', 'stream':'HLS'}]}