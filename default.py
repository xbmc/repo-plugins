#
#      Copyright (C) 2013
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with XBMC; see the file COPYING.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import urllib
import urllib2
import re
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import os
import json

ADDONID  = 'plugin.audio.pureradio'
TITLE    = 'PureRadio.One'
URL      = 'http://listento.pureradio.one/pureradio.pls'
URL64    = 'http://listento.pureradio.one:8000'
URL128   = 'http://listento.pureradio.one:8000/pure_128'
URL192   = 'http://listento.pureradio.one:8000/pure_192'
PODCASTS = 'http://www.spreaker.com/show/{0}/episodes/feed'

ADDON    = xbmcaddon.Addon(ADDONID)
HOME     = ADDON.getAddonInfo('path')
VERSION  = ADDON.getAddonInfo('version')
GETTEXT  = ADDON.getLocalizedString

ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')

_PLAYNOW  = 100
_PLAY128  = 101
_PLAY192  = 102
_PODCASTS = 103

_PLAYPODCAST = 200


def DialogOK(title, line1, line2, line3):
    xbmcgui.Dialog().ok(title, line1, line2, line3)

	
def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION
    if prev != curr:
		ADDON.setSetting('VERSION', curr)
	
	
def getURL(url):
	if url==1:
		return URL64
	elif url==2:
		return URL128
	elif url==3:
		return URL192
	else:
		return URL
	
	
def clean(name):	
    name = name.replace('&#233;', 'e')
    return name.strip()
	

def Play(url=0):
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()    
    pl.add(getURL(url))
    xbmc.Player().play(pl)

	
def addDir(name, mode, isFolder):
	name = clean(name)
	thumbnail = ICON
	u         = sys.argv[0] + '?mode=' + str(mode)        
	liz       = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)
	liz.setProperty('Fanart_Image', FANART)
	xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)
	
	
def AddPodcast(name, link):
    thumbnail = ICON#'DefaultPlaylist.png'

    u   = sys.argv[0]
    u  += '?url='  + urllib.quote_plus(link)
    u  += '&mode=' + str(_PLAYPODCAST)
    u  += '&name=' + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)
	
def ShowPodcasts():
	shows = (1721942,1757189)
	for show in shows:
		response = urllib2.urlopen(PODCASTS.format(show)).read()   
		response = response.replace('\n','')

		match = re.compile('<item><title>(.+?)</title><link>.+?</link>.+?<enclosure url="(.+?)</enclosure>').findall(response)

	for name, link in match:
		AddPodcast(name, link.split('?')[0])

def PlayPodcast(name, link):
    link = link.split('"')[0]

    thumbnail = ICON#'DefaultPlaylist.png'
        
    liz = xbmcgui.ListItem(name, iconImage = thumbnail, thumbnailImage = thumbnail)
    liz.setInfo('music', {'Title': name})
    liz.setProperty('mimetype', 'audio/mpeg')
    liz.setProperty('IsPlayable', 'true')

    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()   
    pl.add(link, liz)

    xbmc.Player().play(pl)
					
					
def Main():   
	CheckVersion()
	addDir(GETTEXT(30045), _PLAYNOW,     False)
	addDir(GETTEXT(30046), _PLAY128,     False)
	addDir(GETTEXT(30047), _PLAY192,     False)
	#   addDir(GETTEXT(30031), _REQUEST,     True)
	addDir(GETTEXT(30040), _PODCASTS,    True)
	# auto play option
	play = ADDON.getSetting('PLAY')=='true'
	if play and not xbmc.Player().isPlayingAudio():
		Play()
		
def get_params(path):
    params = {}
    path   = path.split('?', 1)[-1]
    pairs  = path.split('&')

    for pair in pairs:
        split = pair.split('=')
        if len(split) > 1:
            params[split[0]] = urllib.unquote_plus(split[1])

    return params


params = get_params(sys.argv[2])
mode   = None

try:    mode=int(params['mode'])
except: pass

if mode == _PLAYNOW:
    ADDON.setSetting('STREAM', str(mode == _PLAYNOW).lower())
    Play()
elif mode == _PLAY128:
    ADDON.setSetting('STREAM', str(mode == _PLAY128).lower())
    Play(2)
elif mode == _PLAY192:
    ADDON.setSetting('STREAM', str(mode == _PLAY192).lower())
    Play(3)
elif mode == _PODCASTS:
	ShowPodcasts()
elif mode == _PLAYPODCAST:
    try:
        name = params['name']
        url  = params['url']
        PlayPodcast(name, url)
    except:
        pass
else:
    Main()

    
xbmcplugin.endOfDirectory(int(sys.argv[1]))