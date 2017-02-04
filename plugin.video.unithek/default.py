# -*- coding: utf-8 -*-


import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib

import threading

import libmediathek3 as libMediathek

import lib3sat
import libard
import libbr
import libdaserste
import libhr
import libkika
import libmdr
import libndr
import libsr
import libswr
import libwdr
import libzdf

translation = libMediathek.getTranslation

log = libMediathek.log
import time
t = time.time() * 1000

	
def logtime():
	xbmc.log(str(time.time() * 1000 - t))

def listMain():
	l = []
	l.append({'_name':translation(31031), 'mode':'listMV', '_type':'dir'})
	l.append({'_name':translation(31032), 'mode':'listAZ', '_type':'dir'})
	l.append({'_name':translation(31033), 'mode':'listDateChannels', '_type':'dir'})
	return l
	
def listMV():
	l = []
	l += libard.getMostViewed()
	l += libzdf.getMostViewed()[:50]
	libMediathek.sortAZ()
	return l

def listAZ():
	l = []
	t1 = threading.Thread(target=getA)
	t2 = threading.Thread(target=getZ)
	t1.start()
	t2.start()
	t1.join()
	t2.join()
	l += la
	l += lz
	libMediathek.sortAZ()
	return l
	
def getA():
	global la
	la = libard.libArdListShows()
	
def getZ():
	global lz
	lz = libzdf.libZdfListAZ()
	
def listDateChannels():
	l = []
	l.append({'name':'3sat', 'mode':'lib3satListDate', '_type':'dir'})
	l.append({'name':'ARD-Alpha', 'mode':'libBrListChannelDate', 'channel':'ARD-Alpha', '_type':'dir'})
	l.append({'name':'BR', 'mode':'libBrListChannelDate', 'channel':'BR', '_type':'dir'})
	l.append({'name':'Das Erste', 'mode':'libDasErsteListDate', '_type':'dir'})
	l.append({'name':'HR', 'mode':'libHrListDate', '_type':'dir'})
	l.append({'name':'KiKa', 'mode':'libKikaListDate', '_type':'dir'})
	l.append({'name':'MDR', 'mode':'libMdrListDate', '_type':'dir'})
	#l.append({'name':'MDR', 'mode':'libArdListChannelDate', 'channel':'MDR', '_type':'dir'})
	l.append({'name':'NDR', 'mode':'libNdrListDate', '_type':'dir'})
	l.append({'name':'One', 'mode':'libArdListChannelDate','channel':'One', '_type':'dir'})
	#l.append({'name':'Phoenix', 'mode':'libZdfListChannelDate', 'channel':'phoenix', '_type':'dir'})
	l.append({'name':'RB', 'mode':'libArdListChannelDate','channel':'RB', '_type':'dir'})
	l.append({'name':'RBB', 'mode':'libArdListChannelDate','channel':'RBB', '_type':'dir'})
	l.append({'name':'SR', 'mode':'libSrListDate', '_type':'dir'})
	l.append({'name':'SWR', 'mode':'libSwrListDate', '_type':'dir'})
	l.append({'name':'Tagesschau24', 'mode':'libArdListChannelDate','channel':'tagesschau24', '_type':'dir'})
	l.append({'name':'WDR', 'mode':'libWdrListDate', '_type':'dir'})
	l.append({'name':'ZDF', 'mode':'libZdfListChannelDate', 'channel':'zdf', '_type':'dir'})
	l.append({'name':'ZDF Info', 'mode':'libZdfListChannelDate', 'channel':'zdfinfo', '_type':'dir'})
	l.append({'name':'ZDF Neo', 'mode':'libZdfListChannelDate', 'channel':'zdfneo', '_type':'dir'})
	return l
	
def list():	
	global params
	params = libMediathek.get_params()
	global pluginhandle
	pluginhandle = int(sys.argv[1])
	
	mode = params.get('mode','listMain')
	xbmc.log(mode)
	if mode.startswith('lib3sat') or mode.startswith('xml'):
		lib3sat.list()
	elif mode.startswith('libArd'):
		libard.list()
	elif mode.startswith('libBr'):
		libbr.list()
	elif mode.startswith('libDasErste'):
		libdaserste.list()
	elif mode.startswith('libHr'):
		libhr.list()
	elif mode.startswith('libKika'):
		libkika.list()
	elif mode.startswith('libMdr'):
		libmdr.list()
	elif mode.startswith('libNdr'):
		libndr.list()
	elif mode.startswith('libSr'):
		libsr.list()
	elif mode.startswith('libSwr'):
		libswr.list()
	elif mode.startswith('libWdr'):
		libwdr.list()
	elif mode.startswith('libZdf'):
		libzdf.list()
	else:
		l = modes.get(mode,listMain)()
		libMediathek.addEntries(l)
		xbmcplugin.endOfDirectory(int(sys.argv[1]),cacheToDisc=True)	
		
modes = {
	'listDateChannels': listDateChannels,
	'listAZ': listAZ,
	'listMV': listMV,
	}
list()