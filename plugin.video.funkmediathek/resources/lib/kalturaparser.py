# -*- coding: utf-8 -*-
import json
import libmediathek3 as libMediathek

base = 'https://cdnapisec.kaltura.com/api_v3/index.php?service=multirequest'
apiVersion = '3.1'
expiry = '86400'
clientTag = 'kwidget%3Av2.47'
format = '1' 
ignoreNull = '1'
action = 'null'
#1:
one_service='session'
one_action='startWidgetSession'
one_widgetId='_1985051'
#kalsig = 'c86ae6f65c1780478e3c4bb1680f6599'#some md5

def getVideoUrl(entryId):
	url = base
	url += '&apiVersion=' + apiVersion
	url += '&expiry=' + expiry
	url += '&clientTag=' + clientTag
	url += '&format=' + format
	url += '&ignoreNull=' + ignoreNull
	url += '&action=' + action
	
	n = '1'
	url += '&'+n+':service=' + one_service
	url += '&'+n+':action=' + one_action
	url += '&'+n+':widgetId=' + one_widgetId
	
	n = '2'
	url += '&'+n+':ks=%7B1%3Aresult%3Aks%7D'
	#url += '&'+n+':contextDataParams:referrer=http%3A%2F%2Fplayer.kaltura.com%2FkWidget%2Ftests%2FkWidget.getSources.html%23__1985051%2C' + entryId
	url += '&'+n+':contextDataParams:referrer=https%3a%2f%2fwww.funk.net'
	url += '&'+n+':contextDataParams:objectType=KalturaEntryContextDataParams'
	url += '&'+n+':contextDataParams:flavorTags=all'
	url += '&'+n+':service=baseentry'
	url += '&'+n+':entryId=' + entryId
	url += '&'+n+':action=getContextData'
	
	n = '3'
	url += '&'+n+':action=list'
	url += '&'+n+':filter:entryIdEqual=' + entryId
	url += '&'+n+':filter:objectType=KalturaAssetFilter'
	url += '&'+n+':filter:statusEqual=2'
	url += '&'+n+':ks=%7B1%3Aresult%3Aks%7D'
	url += '&'+n+':pager:pageSize=50'
	url += '&'+n+':service=caption_captionasset'
	
	#url += '&kalsig=' + kalsig
	
	response = libMediathek.getUrl(url)
	libMediathek.log(response)
	j = json.loads(response)
	d = {}
	flavorIds = ''
	for flavorAsset in j[1]['flavorAssets']:
		flavorIds += flavorAsset['id'] + ','
	videoUrl = 'https://cdnapisec.kaltura.com/p/1985051/sp/198505100/playManifest/entryId/'+entryId+'/flavorIds/'+flavorIds[:-1]+'/format/applehttp/protocol/https/a.m3u8'
	videoUrl += '?referrer=aHR0cHM6Ly93d3cuZnVuay5uZXQ='
	d['media'] = []
	
	d['media'].append({'url':videoUrl, 'type':'HLS'})
	for object in j[2]['objects']:
		d['subtitle'] = []
		lang = object['languageCode']
		subUrl = 'https://cdnsecakmi.kaltura.com/api_v3/index.php/service/caption_captionAsset/action/serve/captionAssetId/' + object['id']
		d['subtitle'].append({'url':subUrl, 'type':'srt', 'lang':lang})
	return d