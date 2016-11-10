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

import os
import urllib
import urllib2
import re

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

ADDONID  = 'plugin.audio.pureradio'
TITLE    = 'PureRadio.One'

# urls
URLPLS   = 'http://listento.pureradio.one/pureradio.pls'
URL064   = 'http://listento.pureradio.one/8000/'
URL128   = 'http://listento.pureradio.one:8000/pure_128'
URL192   = 'http://listento.pureradio.one:8000/pure_192'
PODCASTS = 'http://www.spreaker.com/show/{0}/episodes/feed'

# addon information
ADDON    = xbmcaddon.Addon(ADDONID)
HOME     = ADDON.getAddonInfo('path')
VERSION  = ADDON.getAddonInfo('version')
GETTEXT  = ADDON.getLocalizedString
ICON     =  getAddonInfo("icon")
FANART   =  getAddonInfo("fanart")

# modes
_PLAYNOW  = 100
_PODCASTS = 110
_PLAYPODCAST = 111


def DialogOK(title, line1, line2, line3):
    xbmcgui.Dialog().ok(title, line1, line2, line3)


def checkVersion():    
    prev = ADDON.getSetting('VERSION')
    curr = VERSION
            
    # version update for future usage
    if prev != curr:
        ADDON.setSetting('VERSION', curr)


def getURL(stream):
    # convert selection box items into urls    
    if stream=="64kbps":
        return URL064
    if stream=="128kbps":
        return URL128
    elif stream=="192kbps":
        return URL192
    else: 
        return URLPLS
    
    
def clean(name):
    name = name.replace('&#233;', 'e')
    return name.strip()


def Play():
    # retrieve preferred quality
    stm = ADDON.getSetting('STREAM')
    # retrieve url
    url = getURL(stm)
    
    # create playlist
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()
    pl.add(url)

    xbmc.Player().play(pl)


def autoPlay():
    # auto play option
    if ADDON.getSetting('PLAY')=='true':
        if not xbmc.Player().isPlayingAudio():
          Play()


def createMenu():
    # add menu items
    addDir(GETTEXT(30001), _PLAYNOW, False)
    addDir(GETTEXT(30002), _PODCASTS, True)


def addDir(name, mode, isFolder):
    name = clean(name)
    thumbnail = ICON

    u = sys.argv[0] + '?mode=' + str(mode)        

    li = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)
    li.setProperty('Fanart_Image', FANART)
    
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=li, isFolder=isFolder)


    
def AddPodcast(name, link):
    thumbnail = ICON#'DefaultPlaylist.png'

    u   = sys.argv[0]
    u  += '?url='  + urllib.quote_plus(link)
    u  += '&mode=' + str(_PLAYPODCAST)
    u  += '&name=' + urllib.quote_plus(name)
    
    li = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)
    
    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = li, isFolder = False)


def ShowPodcasts():
	response = urllib2.urlopen(PODCASTS.format(1757189)).read()   
	response = response.replace('\n','')

	match = re.compile('<item><title>(.+?)</title><link>.+?</link>.+?<enclosure url="(.+?)</enclosure>').findall(response)

	for name, link in match:
		AddPodcast(name, link.split('?')[0])


def PlayPodcast(name, link):
    link = link.split('"')[0]

    thumbnail = ICON#'DefaultPlaylist.png'
        
    li = xbmcgui.ListItem(name, iconImage = thumbnail, thumbnailImage = thumbnail)
    li.setInfo('music', {'Title': name})
    li.setProperty('mimetype', 'audio/mpeg')
    li.setProperty('IsPlayable', 'true')

    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()   
    pl.add(link, li)

    xbmc.Player().play(pl)
    

def Main():
    checkVersion()
    createMenu()
    autoPlay()


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

try:
    mode=int(params['mode'])
except:
    pass

#stream play is selected
if mode == _PLAYNOW:
    Play()
# podcasts folder is selected
elif mode == _PODCASTS:
    ShowPodcasts()
# play podcast is selected
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
