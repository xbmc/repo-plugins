#
#      Copyright (C) 2013 Sean Poyser
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
#  The code was originally based on the XBMC Last.FM - SlideShow by divingmule
#  (script.image.lastfm.slideshow) also released under the 
#  GNU General Public License
#

import urllib
import urllib2
import os
import xbmcaddon
import xbmc
import sys

import random
import re


#if sys.version_info >=  (2, 7):
#    import json
#else:
#    import simplejson as json 

import json
if not 'load' in dir(json):
    import simplejson as json


ADDON     = xbmcaddon.Addon(id='plugin.audio.ramfm')
HOME      = ADDON.getAddonInfo('path')
ICON      = os.path.join(HOME, 'icon.png')
GETSTRING = ADDON.getLocalizedString

global MODULES
MODULES = None

def Start():
    Restart()


def Restart():
    if not xbmc.Player().isPlayingAudio():
        xbmc.executebuiltin("XBMC.Notification("+GETSTRING(30000)+","+GETSTRING(30001)+",5000,"+ICON+")")      
        Reset()
        return

    artist = GetArtist()

    if artist != '':
        Initialise()

    while True:
        xbmc.sleep(1000)
        if artist == '' or artist != GetArtist():
            break
        if not xbmc.Player().isPlayingAudio():
            break 
    Restart()


def Reset():
    players = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method":"Player.GetActivePlayers", "id": 1}'))
    p = players['result']

    id = -1
    for player in p:
        if player['type'] == 'picture':
            id = player['playerid']
            xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.Stop", "params": {"playerid":%i}, "id": 1}' % id)

    if id != -1:
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Clear", "params": {"playlistid":%i}, "id": 1}' % id)


def AddImages(images):
    items =[]
    for image in images:
        if not xbmc.Player().isPlayingAudio():
            return
        if '\'' in image:
            continue
        image = urllib.unquote_plus(image)    
        item  = '{ "jsonrpc": "2.0", "method": "Playlist.Add", "params": { "playlistid": 2 , "item": {"file": "%s"} }, "id": 1 }' % image
        try:
            items.append(item.encode('ascii'))
            xbmc.executeJSONRPC(str(items[-1]).replace("'",""))
        except:
            pass 

    #print 'Adding - %d valid images ' % len(items)
    

def GetModuleImages(module, artist = None):
    images = []

    if not artist:
        artist = GetArtist()

    if artist == '':
        return images

    if not MODULES:
        ImportModules()

    try:
        if module.upper() == 'ALL':
            for module in MODULES:
                images += GetModule(module).GetImages(artist)
        else:
            module = GetModule(module)
            if module:
                images = module.GetImages(artist)
    except:
        pass

    return images


def GetImages(artist):
    module = ADDON.getSetting('NEW_TALKSHOW')
    images = GetModuleImages(module, artist)

    #print 'Total number of images found = %d' % len(images)

    if len(images) > 50:
        images = images[:50]

    random.shuffle(images)
    #print images
    return images


def Initialise():
    artist = GetArtist()

    #print "Initialising slideshow for %s" % artist

    xbmc.executebuiltin("XBMC.Notification("+GETSTRING(30000)+","+GETSTRING(30004)+" "+artist.replace(',', '')+",5000,"+ICON+")")        

    images = GetImages(artist)

    if not ShowImages(images):
        xbmc.executebuiltin("XBMC.Notification("+GETSTRING(30000)+","+GETSTRING(30002)+" "+artist+",5000,"+ICON+")")
        Reset()

        
def ShowImages(images):  
    xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.Clear", "params": {"playlistid":2}, "id": 1}')
    if len(images) == 0:
        return False

    if len(images) <= 5:
        AddImages(images)
        return DoPlaylist()
   
    AddImages(images[:5])
    if not DoPlaylist():
        return False

    AddImages(images[5:])
    if not DoPlaylist():
        return False

    return True


def DoPlaylist(): 
    playlist = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Playlist.GetItems", "params": {"playlistid":2}, "id": 1}'))

    try:
        if playlist['result']['limits']['total'] > 0:
            players = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Player.GetActivePlayers", "id": 1}'))
            found = False

            for i in players['result']:
                if i['type'] == 'picture':
                    found = True
                else: continue

            if not found:
                play = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Player.Open","params":{"item":{"playlistid":2}} }')
    except:
        return False

    return True       


def GetArtist():
    artist = ''

    try:
        artist = xbmc.Player().getMusicInfoTag().getArtist()
    except:
        pass
        
    if len(artist) < 1: 
        try:    artist = xbmc.Player().getMusicInfoTag().getTitle().split(' - ')[0]
        except: pass

    return artist


def TestModule(module, artist):
    images = []

    print '*************************************************'
    print 'RAM FM Slideshow TEST'
    print 'Search %s for %s' % (module, artist)

    images = GetModuleImages(module, artist)

    print '**** Total number of images found = %d ****' % len(images)
    print images
    print '**** Total number of images found = %d ****' % len(images)
    print '*************************************************'


def GetModule(name):
    try:    return MODULES[name]
    except: return None
        

def ImportModules():
    global MODULES
    MODULES = dict()

    libPath = os.path.join(HOME, 'lib')
    sys.path.insert(0, libPath)

    module = []

    import glob
    lib   = os.path.join(HOME, 'lib', '*.py')
    files = glob.glob(lib)
    for name in files:
        name = name.rsplit(os.sep, 1)[1]
        if name.rsplit('.', 1)[1] == 'py':
            module.append(name .rsplit('.', 1)[0])

    modules = map(__import__, module)

    for module in modules:
        MODULES[module.__name__] = module

if __name__ == '__main__':
    #TestModule('HTBackdrops', 'Whitney Houston')
    Start()