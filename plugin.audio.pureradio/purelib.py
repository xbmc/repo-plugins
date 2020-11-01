
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import os
import sys

import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET


ADDONID      = 'plugin.audio.pureradio'
ADDON        = xbmcaddon.Addon(ADDONID)
ADDON_HANDLE = int(sys.argv[1])

HOME         = ADDON.getAddonInfo('path')
AUDIO_ICON   = "DefaultAudio.png"
FOLDER_ICON  = "DefaultFolder.png"
FANART       = os.path.join(HOME,'resources','fanart.jpg')

PLAYSTREAM  = 100
PODCASTS    = 101
PLAYPODCAST = 102

URL         = "http://listento.pureradio.one/pureradio.pls"
PODCASTURL  = 'http://www.spreaker.com/show/1757189/episodes/feed'

params = {}

def check_autoPlay():
    if (ADDON.getSetting('PLAY')=='true'):
        playStream()    

def playStream():
    # music item
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    # clear playlist
    pl.clear()
    # add url item 
    pl.add(URL)
    # play the item
    xbmc.Player().play(pl)

def createMenu():
    # create items
    addDir(ADDON.getLocalizedString(30001),PLAYSTREAM, AUDIO_ICON, False)
    addDir(ADDON.getLocalizedString(30002),PODCASTS, FOLDER_ICON, True)
    # close folder object
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
def addDir(name, action, icon, isFolder):
    # create url (play mode)
    u = sys.argv[0] 
    u += '?action=' + str(action) 
    #create listitem 
    li = xbmcgui.ListItem(name)
    # set icon and fanart
    li.setArt({'Icon': icon,'Fanart': FANART})   
    # add to folder
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=li, isFolder=isFolder)

def getPodcasts():
    # create audio playlist
    xbmcplugin.setContent(int(sys.argv[1]), 'audio')
    # retreive spreaker XML
    response = urllib.request.urlopen(url=PODCASTURL, timeout=20).read().decode('utf-8')
    # make a XML tree and iterate through items
    root = ET.fromstring(response)
    for item in root.iter('item'):
        addPodcast(item[0].text,item[4].attrib['url'], item[8].attrib['href'])
    # close folder object
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def addPodcast(name,link,icon):
    # retrieve icon or do not (to save bandwidth)
    if (ADDON.getSetting('SHOW_PODCAST_IMAGES')=='false'):
        icon = AUDIO_ICON
    # create url (url,mode and name)
    u   = sys.argv[0]
    u  += '?url='  + urllib.parse.unquote(link)
    u  += '&action=' + str(PLAYPODCAST)
    u  += '&name=' + urllib.parse.unquote(name)
    u  += '&icon=' + icon 
    # create listitem with name
    li = xbmcgui.ListItem(name)
    # set track title from name and add properties
    try:
        # expected format "date - artist - show"
        date,title = name.split(' - ', 1)
        li.setInfo("music",{"artist":date.strip(),"title": title.strip(),"album":"Pureradio.One"})
    except:
        li.setInfo("music",{"artist": name, "album":"Pureradio.One"})
    # set icon and fanart
    li.setArt({'Icon': icon,'Fanart':FANART})
    # add to folder
    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = li, isFolder = False)    

def playPodcast(name, link, icon):
    #create list item
    li = xbmcgui.ListItem(name)
    # add properties
    li.setInfo('music', {'Title': name})
    li.setProperty('mimetype', 'audio/mpeg')
    li.setProperty('IsPlayable', 'true')
    li.setArt({'Icon': icon})
    # create playlist item
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    # clear playlist
    pl.clear()   
    # add item to playlist
    pl.add(link, li)
    # play item
    xbmc.Player().play(pl)


def get_params(path):
    # expected format ?action=number&property=value%anotherproperty=anothervalue
    path   = path.split('?', 1)[-1]
    pairs  = path.split('&')
    # iterate throught pairs
    for pair in pairs:
        split = pair.split('=')
        if len(split) > 1:
            params[split[0]] = urllib.parse.unquote(split[1])
    # return params object
    return params  

def setAction(action):
    # determine action
    if (action == PLAYSTREAM):
        playStream()
    # podcasts folder is selected
    elif (action == PODCASTS):
        getPodcasts()
    # play podcast is selected
    elif action == PLAYPODCAST:
        playPodcast(params['name'],params['url'],params['icon'])

def init():
    # retrieve params
    params = get_params(sys.argv[2])
    # check params are filled
    if bool(params):
        setAction(int(params['action']))
    else:
        createMenu()
        check_autoPlay()
