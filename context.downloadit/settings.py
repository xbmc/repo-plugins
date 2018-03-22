#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import xbmc
import xbmcaddon
import xbmcgui,xbmcvfs
import xbmcplugin
import time,urllib

addon = xbmcaddon.Addon()   
addon_handle = int(sys.argv[1]) 
translation = addon.getLocalizedString


def debug(content):
    log(content, xbmc.LOGDEBUG)
    
def notice(content):
    log(content, xbmc.LOGNOTICE)

def log(msg, level=xbmc.LOGNOTICE):
    addon = xbmcaddon.Addon()
    addonID = addon.getAddonInfo('id')
    xbmc.log('%s: %s' % (addonID, msg), level) 
    
def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

    
def addDir(name, url, mode, thump, desc="",page=1,nosub=0,type="items"):   
  u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&page="+str(page)+"&nosub="+str(nosub)+"&type="+str(type)
  ok = True
  liz = xbmcgui.ListItem(name)  
  liz.setArt({ 'fanart' : thump })
  liz.setArt({ 'thumb' : thump })
  liz.setArt({ 'banner' : "" })
  liz.setArt({ 'fanart' : "" })
  liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": desc})
	
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
  return ok

params = parameters_string_to_dict(sys.argv[2])  
mode = urllib.unquote_plus(params.get('mode', ''))
    
if mode is '':
     addDir(translation(30011),"Settings","Settings","")
     xbmcplugin.endOfDirectory(addon_handle,succeeded=True,updateListing=False,cacheToDisc=True) 
else:
  # Wenn Settings ausgewählt wurde
  if mode == 'Settings':
          addon.openSettings()