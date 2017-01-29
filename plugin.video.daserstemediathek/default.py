# -*- coding: utf-8 -*-
#"""
import libdaserste

libdaserste.list()
"""


import libDasErste
import utils
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import libMediathek2
__settings__ = xbmcaddon.Addon()
CACHEFILE = xbmc.validatePath(xbmc.translatePath(__settings__.getAddonInfo('profile')+"cache.json"))


def main():
	xbmc.log('#####Main')
	#"#""
	if utils.f_check_existance(CACHEFILE) and 'mode' in params:
		xbmc.log('stub')
		return True
	elif utils.f_check_existance(CACHEFILE):
	"#""
	if utils.f_check_existance(CACHEFILE):
		sub = True
		xbmc.log(str(params))
		#if 'id' in params:
		#	#parsedicts(dProxy)
		#	return play()
		
		dProxy = retrive()
		xbmc.log('retive')
		videoList = dProxy['videoList']
		url = dProxy['next']['url']
		i = len(videoList)# + 1
	else:
		sub = False
		xbmc.log('new')
		url = 'http://www.daserste.de/dasersteapp/app/index~series_serial-beckmannHashtag_types-sendung,sendebeitrag_pageNumber-0.json'
		dProxy = {}
		n = {}
		dProxy['next'] = n
		videoList = []
		i = 0
		
	lvidlist = len(videoList)
		
	l = libDasErste.getVideo(url)
	xbmc.log(str(l))
	for d in l:
		if d['type'] == 'nextPage':
			dProxy['next']['url'] = 'http://www.daserste.de/dasersteapp/app/index~series_serial-beckmannHashtag_types-sendung,sendebeitrag_pageNumber-1.json'
		else:
			d2 = {}
			d2['_name'] = d['name']
			d2['_plot'] = d['plot']
			d2['_thumb'] = d['thumb']
			xbmc.log(d['url'])
			d2['url'] = d['url']
			d2['mode'] = 'play'
			#d2['mode'] = 'main'
			d2['_type'] = 'video'
			#d2['id'] = str(i)
			i += 1
			videoList.append(d2)
	dProxy['next']['url'] = 'http://www.daserste.de/dasersteapp/app/index~series_serial-beckmannHashtag_types-sendung,sendebeitrag_pageNumber-1.json'
	dProxy['videoList'] = videoList
	parsedicts(dProxy)
	write(dProxy)
	return sub,lvidlist
	
"""
"""
def play():
	dProxy = retrive()
	xbmc.log('###########ids')
	xbmc.log(str(len(dProxy['videoList'])))
	xbmc.log(params['id'])
	if len(dProxy['videoList']) < int(params['id']) + 1:
		xbmc.log('#####videostub')
		xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=False)	
		#listitem = xbmcgui.ListItem()
		#xbmcplugin.setResolvedUrl(pluginhandle, False, listitem)
		return True"""
"""
def play():
	#dProxy = retrive()
	xbmc.log('##########################play')
	xbmc.log(params['url'])
	vidUrl = libDasErste.getVideoUrl(params['url'])
	#listitem = xbmcgui.ListItem(label='HORRIBLEHACK',path=vidUrl)
	#xbmc.Player().play(vidUrl, listitem)
	#xbmcplugin.endOfDirectory(int(sys.argv[1]),succeeded=False)
	#vidUrl = libDasErste.getVideoUrl(dProxy['videoList'][int(params['id'])]['_url'])
	listitem = xbmcgui.ListItem(path=vidUrl)
	xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	return False,False
def parsedicts(dProxy):
	libMediathek2.addEntries(dProxy['videoList'])
	libMediathek2.addEntries([{'_name':'next','_type':'dir','id':str(len(dProxy['videoList'])),'mode':'main'}])
	
def stub():
	l = libDasErste.getVideo('http://www.daserste.de/dasersteapp/app/index~series_serial-beckmannHashtag_types-sendung,sendebeitrag_pageNumber-0.json')
	#xbmc.log()
	
def write(dProxy):
	data = json.dumps(dProxy)
	utils.f_write(CACHEFILE,data)
def add(l):
	l2 = json.loads(utils.f_open(CACHEFILE))
	l = l + l2
	data = json.dumps(l)
	utils.f_write(CACHEFILE,data)
def retrive():
	return json.loads(utils.f_open(CACHEFILE))
	
def list():	
	xbmc.log("xbmc.getInfoLabel('System.CurrentControl')")
	xbmc.log(xbmc.getInfoLabel('System.CurrentControl'))
	modes = {
	'play':play
	}
	global params
	params = libMediathek2.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	
	if not params.has_key('mode'):
		isSubfolder,lvidlist = main()
	else:
		isSubfolder,lvidlist = modes.get(params['mode'],main)()
	if isSubfolder:
		xbmcplugin.endOfDirectory(int(sys.argv[1]),updateListing=True,cacheToDisc=True)
	else:
		xbmcplugin.endOfDirectory(int(sys.argv[1]))	
	xbmc.log('##########wnd')
	#wnd = xbmcgui.Window(xbmcgui.getCurrentWindowId())
	#p = wnd.getControl(wnd.getFocusId()).getSelectedPosition()
	#xbmc.log(str(p)+'#')
	#xbmc.log(xbmc.getInfoLabel('System.CurrentControl'))
	try:
		wnd = xbmcgui.Window(xbmcgui.getCurrentWindowId())
		wnd.getControl(wnd.getFocusId()).selectItem(0)
		wnd.getControl(wnd.getFocusId()).selectItem(lvidlist+1)
	except: pass
list()
#"""