# Copyright 2015 Jonathan DeMarks
# Licensed under the Apache License, Version 2.0

import threading
import urllib,urllib2,urlparse,base64
import xbmcplugin,xbmcaddon,xbmcgui,sys
import simplejson as json

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')
vres = xbmcplugin.getSetting(addon_handle, 'video_res')
if vres not in ['0','1','2','3']: vres = '0'
video_res = [720,480,360,180][int(vres)]
subtitles = xbmcplugin.getSetting(addon_handle, 'subtitles')
print 'subtitles: ' + subtitles

addon = xbmcaddon.Addon()
__language__ = addon.getLocalizedString
language = addon.getSetting('language')
if len('' + language) < 1: language = 'E'

def build_url(query):
	return base_url + '?' + urllib.urlencode(query)

def get_json(url):
	data = urllib2.urlopen(url).read().decode('utf-8')
	return json.loads(data)

def b64_encode_object(obj):
	js = json.dumps(obj)
	b64 = base64.b64encode(js)
	return b64

def b64_decode_object(str):
	js = base64.b64decode(str)
	obj = json.loads(js)
	return obj

def build_folders(subcat_ary):
	isStreaming = mode[0] == 'Streaming'
	for s in subcat_ary:
		url = build_url({'mode': s.get('key')})
		li = xbmcgui.ListItem(s.get('name'))
		if 'rph' in s['images']:
			li.setIconImage(s['images']['rph'].get('md'))
			li.setThumbnailImage(s['images']['rph'].get('md'))
		if 'pnr' in s['images']:
			li.setProperty('fanart_image', s['images']['pnr'].get('md'))
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=(isStreaming == False))

def get_video_metadata(file_ary):
	videoFiles = []
	for r in file_ary:
		sqr_img = ''
		wide_img = ''
		if 'sqr' in r['images']: sqr_img = r['images']['sqr'].get('md')
		elif 'cvr' in r['images']: sqr_img = r['images']['cvr'].get('md')
		if 'pnr' in r['images']: wide_img = r['images']['pnr'].get('md')
		videos = sorted([x for x in r['files'] if x['frameHeight'] <= video_res], reverse=True)
		if subtitles == 'false': videos = [x for x in videos if x['subtitled'] == False]
		print videos
		video = videos[0]
		videoFiles.append({'id':r['guid'],'video':video['progressiveDownloadURL'],'wide_img':wide_img,'sqr_img':sqr_img,'title':r.get('title'),'dur':r.get('duration')})
	return videoFiles

def build_basic_listitem(file_data):
	li = xbmcgui.ListItem(file_data['title'])
	li.setIconImage(file_data['wide_img'])
	li.setThumbnailImage(file_data['sqr_img'])
	li.addStreamInfo('video', {'duration':file_data['dur']})
	li.setProperty('fanart_image', file_data['wide_img'])
	return li

def build_media_entries(file_ary):
	for v in get_video_metadata(file_ary):
		li = build_basic_listitem(v)

		bingeAction = 'XBMC.RunPlugin(' + build_url({'mode':'watch_from_here','from_mode':mode[0],'first':v['id']}) + ')'

		file_data = b64_encode_object(v)
		addToPlaylistAction = 'XBMC.RunPlugin(' + build_url({'mode':'add_to_playlist','file_data':file_data}) +')'

		li.addContextMenuItems([(__language__(30010), bingeAction),(__language__(30011), addToPlaylistAction)], replaceItems=True)
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=v['video'], listitem=li)

def process_top_level():
	url = 'http://mediator.jw.org/v1/categories/' + language + '?'
	cats_raw = urllib2.urlopen(url).read().decode('utf-8')
	categories = json.loads(cats_raw)

	for c in categories['categories']:
		if len(c.get('description')) > 0:
			url = build_url({'mode': c.get('key')})
			li = xbmcgui.ListItem(c.get('name'))
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

	url = build_url({'mode': 'languages'})
	li = xbmcgui.ListItem(__language__(30005))
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	xbmcplugin.endOfDirectory(addon_handle)

def build_playlist(file_ary, first):
	added = 0
	current = float(0)
	foundStartEp = False

	metadata = get_video_metadata(file_ary)
	total = float(len(metadata))

	dl = xbmcgui.DialogProgress()
	dl.create(__language__(30006), __language__(30007))

	pl = xbmc.PlayList(1)
	pl.clear()

	for item in reversed(metadata):
		dl.update(int(current / total * 100))
		if item['id'] == first: foundStartEp = True
		if foundStartEp == True:
			added += 1
			li = xbmcgui.ListItem(item['title'], iconImage=item['sqr_img'])
			li.setThumbnailImage(item['sqr_img'])
			pl.add(item['video'], li)
		current += 1.0
	dl.close()

	if added > 0:
		xbmc.Player().play(pl)
	else:
		xbmcgui.Dialog().ok(__language__(30008), __language__(30009))
	return pl

def process_sub_level(sub_level, create_playlist, from_id):
	info = get_json('http://mediator.jw.org/v1/categories/' + language + '/' + sub_level + '?&detailed=1')
	if create_playlist == False:
		if 'subcategories' in info['category']: build_folders(info['category']['subcategories'])
		if 'media' in info['category']: build_media_entries(info['category']['media'])
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		pl = build_playlist(info['category']['media'], from_id)
		xbmc.Player().play(pl)

def process_streaming():
	info = get_json('http://mediator.jw.org/v1/schedules/' + language + '/Streaming')
	for s in info['category']['subcategories']:
		if s['key'] == mode[0]:
			pl = xbmc.PlayList(1)
			pl.clear()
			for item in get_video_metadata(s['media']):
				li = xbmcgui.ListItem(item['title'], iconImage=item['sqr_img'])
				li.setThumbnailImage(item['sqr_img'])
				pl.add(item['video'], li)
			xbmc.Player().play(pl)
			xbmc.Player().seekTime(s['position']['time'])
			xbmc.executebuiltin('PlayerControl(RepeatAll)')
			return

def get_languages():
	info = get_json('http://mediator.jw.org/v1/languages/' + language + '/web')
	for l in info['languages']:
		url = build_url({'mode': 'set_language', 'language': l['code']})
		li = xbmcgui.ListItem(l['vernacular'] + ' / ' + l['name'])
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=False)
	xbmcplugin.endOfDirectory(addon_handle)

def set_language(language):
	language = language
	addon.setSetting('language', language)
	xbmc.executebuiltin('Action(ParentDir)')

def add_to_playlist(file_data):
	data = b64_decode_object(file_data)

	pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	li = build_basic_listitem(data)

	pl.add(url=data['video'], listitem=li)

mode = args.get('mode', None)

if mode is None: process_top_level()
elif mode[0] == 'languages': get_languages()
elif mode[0] == 'set_language': set_language(args.get('language')[0])
elif mode[0] == 'watch_from_here': process_sub_level(args.get('from_mode')[0], True, args.get('first')[0])
elif mode[0] == 'add_to_playlist': add_to_playlist(args.get('file_data')[0])
elif (mode[0].startswith('Streaming') and len(mode[0]) > 9): process_streaming()
else: process_sub_level(mode[0], False, 0)
