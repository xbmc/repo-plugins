#
#      Copyright (C) 2013- Sean Poyser
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

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import urllib
import urllib2

import re

import datetime
import time

import os

import quicknet


ADDONID  = 'plugin.audio.ramfm'
ADDON    =  xbmcaddon.Addon(ADDONID)
HOME     =  ADDON.getAddonInfo('path')
TITLE    =  ADDON.getAddonInfo('name')
VERSION  =  ADDON.getAddonInfo('version')
PODCASTS = 'http://www.spreaker.com/show/816525/episodes/feed'
ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')
GETTEXT  =  ADDON.getLocalizedString

URL   = 'http://ramfm.org/ram.pls'

#Pls file
#NumberOfEntries=3
#File1=http://usa3-vn.mixstream.net:8018
#File2=http://uk2-vn.webcast-server.net:8018
#File3=http://uk1-vn.mixstream.net:9866
#Title1=RAM FM Eighties Hit Radio 64kbps AACP
#Title2=RAM FM Eighties Hit Radio 128kbps MP3
#Title3=RAM FM Eighties Hit Radio 192kbps MP3
#Version=2


_PLAYNOW_HI  = 192
_PLAYNOW_MED = 128
_PLAYNOW_LO  = 64
_REQUEST     = 200
_LETTER      = 300
_TRACK       = 400
_RECORD      = 500
_PODCASTS    = 700
_PLAYPODCAST = 800

MODE_FREE   = 1000
MODE_SONG   = 1100
MODE_ARTIST = 1200
MODE_IGNORE = 1300


def DialogOK(title, line1, line2, line3):
    xbmcgui.Dialog().ok(title, line1, line2, line3)

def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    #if prev == '0.0.0':
    DialogOK(TITLE + ' - ' + VERSION, GETTEXT(30017), GETTEXT(30018) , GETTEXT(30019)+' :-)')


def DownloaderClass(url, dest, dp): 
    dp.update(0, GETTEXT(30020), dest, GETTEXT(30021))   
    urllib.urlretrieve(url, dest, lambda nb, bs, fs: _pbhook(nb, bs, fs, dp))
 

def _pbhook(numblocks, blocksize, filesize, dp,):
    try:
        percent = (numblocks * 5) % 100
        dp.update(percent)
        #dp.update(0)
    except:
        pass

    if dp.iscanceled(): 
        raise Exception('Canceled')


def GetRecordPath():
    downloadFolder = ADDON.getSetting('RECORD_FOLDER')

    if ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, GETTEXT(30022), 'files', '', False, False, downloadFolder)
	if downloadFolder == '' :
	    return None

    if downloadFolder is '':
        DialogOK(TITLE, '', GETTEXT(30023), GETTEXT(30024))
	ADDON.openSettings() 
	downloadFolder = ADDON.getSetting('RECORD_FOLDER')

    if downloadFolder == '' and ADDON.getSetting('ASK_FOLDER') == 'true':
        dialog = xbmcgui.Dialog()
	downloadFolder = dialog.browse(3, GETTEXT(30022), GETTEXT(30025), '', False, False, downloadFolder)	

    if downloadFolder == '' :
        return None

    if ADDON.getSetting('ASK_FILENAME') == 'true':
        kb = xbmc.Keyboard(TITLE, GETTEXT(30026))
	kb.doModal()
	if kb.isConfirmed():
	    filename = kb.getText()
	else:
	    return None
    else:
        filename = TITLE

    filename = re.sub('[:\\/*?\<>|"]+', '', filename)
    filename = filename + '.mp3'

    return os.path.join(downloadFolder, filename)


def Record():
    dest = GetRecordPath()
    if dest == None or dest == '':
        return
    
    dp = xbmcgui.DialogProgress()
    dp.create(TITLE)

    try:
        DownloaderClass(getURL(), dest, dp)
    except Exception as e:
        if str(e) == 'Canceled':
            pass   
    dp.close()


def Play():
    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()    
    pl.add(getURL())

    xbmc.Player().play(pl)


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

def ShowPodcasts():
    response = urllib2.urlopen(PODCASTS).read()   
    response = response.replace('\n','')

    match = re.compile('<item><title>(.+?)</title><link>.+?</link>.+?<enclosure url="(.+?)</enclosure>').findall(response)

    for name, link in match:
        AddPodcast(clean(name), link.split('?')[0])


def AddPodcast(name, link):
    thumbnail = ICON#'DefaultPlaylist.png'

    u   = sys.argv[0]
    u  += '?url='  + urllib.quote_plus(link)
    u  += '&mode=' + str(_PLAYPODCAST)
    u  += '&name=' + urllib.quote_plus(name)
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)


def GetRecent(response):
    recent = []

    match = re.compile('color="CCDDDD"><b>(.+?)</b>').findall(response)   
    for artist in match:
        recent.append(artist)
            
    return recent


def Request():
    addLetter('0-9')
    for i in range(65, 91):
        addLetter(chr(i))


def IsLive():
    try:
        #for live show titles see : http://ramfm.org/momentum/cyan/guide.php
        title = xbmc.Player().getMusicInfoTag().getTitle().lower()
    except:
        title = '' 
   
    shows = []
    shows.append('Eighties Flash Back') #Monday
    shows.append('Ladies Night')        #Monday - Verified
    shows.append('Big Eighties Show')   #Tuesday
    shows.append('Night Show')          #Wednesday / Sunday - Verified
    shows.append('Dancing Dave')        #Thursday - Verified
    shows.append('Eighties Wonderland') #Friday
    shows.append('Happy Hour')          #Saturday
    shows.append('Eighties Request')    #Sunday - Verified
    shows.append('Chat Request')        #

    #genre = xbmc.getInfoLabel('MusicPlayer.Genre')
    #xbmc.log('Genre = %s' % genre)

    for show in shows:
        if show.lower() in title:
            return True
 
    return False
   

def IsPlayingRAM():
    try:
        if not xbmc.Player().isPlayingAudio():
            return False

        pl   = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)[0]
        resp = quicknet.getURL(URL, 1800)

        if pl.getfilename()[:-1] in resp:
            return True

    except:
        pass

    return False


def Exit():
    import sys
    sys.exit()
    

def IsPlaying(message):
    if IsPlayingRAM():
        return True

    dialog = xbmcgui.Dialog()
    if dialog.yesno(TITLE, message,  GETTEXT(30027), '', GETTEXT(30028), GETTEXT(30029)) == 1:
        Exit()
        return False    

    Play()
    return xbmc.Player().isPlayingAudio()


def RequestLetter(letter):
    if not IsPlaying(GETTEXT(30030)):
        return

    if letter == '0-9':
        url = 'http://ramfm.org/momentum/cyan/playlist0.php'
    else:
        url = 'http://ramfm.org/momentum/cyan/playlist%s.php' % letter

    response = quicknet.getURL(url, 1800)

    hide = ADDON.getSetting('HIDE').lower() == 'true'

    images = {}
    tracks = []

    items = response.split('<!-- start')[1:]
    for item in items:
        item = item.replace(' (& ', ' (& ')

        while '&nbsp;&nbsp;' in item:
            item = item.replace('&nbsp;&nbsp;', '&nbsp;')

        item = item.replace('&nbsp;', ' ')

        mode = MODE_FREE

        if '<i>song recently played</i>' in item:
            mode = MODE_IGNORE if hide else MODE_SONG
        if '<i>artist recently played</i>' in item:
            mode = MODE_IGNORE if hide else MODE_ARTIST

        title = None

        if mode == MODE_FREE:                      
            match     = re.compile('.+?<a href="javascript:request\((.+?)\)" title="(.+?)">.+?<h2>(.+?)</h2>.+?-->').findall(item)[0]
            info      = match[0]
            title     = match[1]
            artist    = match[2].split('-', 1)[0].strip()
            image     = ''
            available = True
            
        if mode == MODE_ARTIST or mode == MODE_SONG:
            match     = re.compile('.+?title="(.+?)">.+?<p>(.+?)</p></header></a></section><!-- end song recently played / artists recently played -->').findall(item)[0]
            info      = match[0]
            title     = match[1].rsplit('(', 1)[0].strip()
            artist    = match[1].split('-', 1)[0].strip()
            image     = ''
            available = False

        if not title:
            continue

        if image != 'na.gif':
            images[artist] = image

        tracks.append([artist, title, image, info, available])

    titles = ['']

    tracks.sort()

    for track in tracks:
        artist    = track[0]
        title     = track[1]
        image     = track[2]
        info      = track[3]
        available = track[4]

        if title in titles:
            continue

        titles.append(title)

        if image == 'na.gif':
            try:    image = images[artist]
            except: pass
       
        if available:
            addAvailable(title, artist, image, info)
        else:
            addUnavailable(title, artist, image, info)


def clean(name):
    name = name.replace('&#233;', 'e')
    name = name.replace('&amp;',  '&')

    return name.strip()



def addAvailable(title, artist, image, request):
    #image = 'http://ramfm.org/artistpic/%s' % image.replace(' ', '%20')
    image = ICON   
    name  = title

    if name.startswith('Request'):
        name  = name.split('Request', 1)[-1]

    name = clean(name)
    
    id   = request.split(',')[0]
    ip   = request.split('\'')[1]
    port = request.split('\'')[3]

    u    = sys.argv[0] 
    u   += '?url='  + urllib.quote_plus('http://www.ramfm.org/req/request.php?songid=%s&samport=%s&samhost=%s' %  (id, port, ip))
    u   += '&mode=' + str(_TRACK)        
    liz  = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)


def addUnavailable(title, artist, image, reason):
    xbmc.log('title %s'  % title)
    xbmc.log('artist %s' % artist)
    xbmc.log('image %s'  % image)
    xbmc.log('reason %s' % reason)
    #image  = 'http://ramfm.org/artistpic/%s' % image.replace(' ', '%20')
    image = ICON   
    name   = title + '[I] (%s)[/I]' % reason
    name   = '[COLOR=FFFF0000]' + name + '[/COLOR]'
    name   = clean(name)  
        
    u    = sys.argv[0] 
    u   += '?mode=' + str(mode)
    liz  = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False) 


def getURL():
    kbps = ADDON.getSetting('STREAM')
    if kbps == 'true': # for backward compatible
        kbps = '192'
    if kbps == 'false': # for backward compatible
        kbps = '64'

    try:
        lines = urllib2.urlopen(URL).readlines()

        for line in lines:
            try:
                items = line.split('=', 1)
                attr  = items[0].lower()

                if attr.startswith('title') and kbps in items[1]:
                    attr = attr.replace('title', 'file')
                    for line in lines:
                        if line.lower().startswith(attr):
                            return line.split('=', 1)[-1].strip()                

            except:
                pass

    except:
        pass

    return URL



def RequestURL(url):  
    if not IsPlaying(GETTEXT(30030)):
        return

    try:    response = urllib2.urlopen(url).read()
    except: return ShowError(GETTEXT(30050))

    
    failed = 'SongRequester Fail' in response

    if failed:
        text = re.compile('reason given:<br />(.+?)</font>').findall(response)[0]
        if 'please wait about' in response:
            try:
                wait  = re.compile('about (.+?) minutes').findall(response)[0]
                text += '[CR]' + GETTEXT(30049)  % str(int(wait))
            except:
                pass

        return ShowError(text)

    DialogOK(GETTEXT(30031), GETTEXT(30032), GETTEXT(30033), GETTEXT(30031))


def ShowError(text):
    DialogOK(GETTEXT(30031), GETTEXT(30034), GETTEXT(30035), text)
            

def Main():   
    CheckVersion()

    addDir(GETTEXT(30051), _PLAYNOW_HI,   False)
    addDir(GETTEXT(30052), _PLAYNOW_MED,  False)
    addDir(GETTEXT(30053), _PLAYNOW_LO,   False)
    addDir(GETTEXT(30037), _RECORD,       False)
    addDir(GETTEXT(30031), _REQUEST,      True)
    addDir(GETTEXT(30040), _PODCASTS,     True)

    play = ADDON.getSetting('PLAY')=='true'
    if play and not xbmc.Player().isPlayingAudio():
        Play()



def addLetter(letter):
    thumbnail = ICON#'DefaultPlaylist.png'
    u         = sys.argv[0]
    u        += '?letter=' + letter
    u        += '&mode='   + str(_LETTER)
    liz       = xbmcgui.ListItem(letter, iconImage=thumbnail, thumbnailImage=thumbnail)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)


def addDir(name, mode, isFolder):
    name = clean(name)
    thumbnail = ICON
    u         = sys.argv[0] + '?mode=' + str(mode)        
    liz       = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setProperty('Fanart_Image', FANART)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)

   
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

try:    mode = int(params['mode'])
except: pass


if mode == _PLAYNOW_HI or mode == _PLAYNOW_MED or mode == _PLAYNOW_LO:
    ADDON.setSetting('STREAM', str(mode))
    Play()


elif mode == _RECORD:
    Record()


elif mode == _REQUEST:
    if IsPlaying(GETTEXT(30030)):
        xbmc.sleep(500)
        if IsLive():
            DialogOK(GETTEXT(30031), GETTEXT(30046), GETTEXT(30047), GETTEXT(30048))
            #xbmc.executebuiltin('Container.Update(%s,replace)' % sys.argv[0])
            Exit()
        else:
            Request()


elif mode == _LETTER:
    if 'letter' in params:
        RequestLetter(params['letter'])
    else:
        Exit()


elif mode == _TRACK:    
    RequestURL(params['url'])


elif mode == _PODCASTS:
    ShowPodcasts()


elif mode == _PLAYPODCAST:
    try:
        name = params['name']
        url  = params['url']
        PlayPodcast(name, url)
    except:
        pass


elif mode == MODE_SONG:
    ShowError(GETTEXT(30043))


elif mode == MODE_ARTIST:
    ShowError(GETTEXT(30044))


else:
    Main()

    
xbmcplugin.endOfDirectory(int(sys.argv[1]))