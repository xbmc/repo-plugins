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

import json

import re

import datetime
import time

import os

import cache


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


_PLAYNOW_320 = 320
_PLAYNOW_HI  = 192
_PLAYNOW_MED = 128
_PLAYNOW_LO  = 64
_REQUEST     = 200
_LETTER      = 300
_TRACK       = 400
_RECORD      = 500
_PODCASTS    = 700
_PLAYPODCAST = 800

MODE_FREE        = 1000
MODE_UNAVAILABLE = 1100
MODE_IGNORE      = 1200


URL_320 = 'http://ramfm.shoutcaststream.com:8513'
URL_192 = 'http://uk1-vn.mixstream.net:9866'
URL_128 = 'http://uk2-vn.webcast-server.net:8018'
URL_64  = 'http://usa3-vn.mixstream.net:8018'

DEFAULTS = {}
DEFAULTS['URL_320'] = URL_320
DEFAULTS['URL_192'] = URL_192
DEFAULTS['URL_128'] = URL_128
DEFAULTS['URL_64']  = URL_64



def DialogOK(title, line1='', line2='', line3=''):
    xbmcgui.Dialog().ok(title, str(line1), str(line2), str(line3))


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    #if prev == '0.0.0':
    DialogOK('%s - %s' % (TITLE, VERSION), GETTEXT(30017), GETTEXT(30018), '%s :-)' % GETTEXT(30019))


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

    match = re.compile('<item><title>(.+?)</title><link>.+?</link>.+?<enclosure url="(.+?)".+?:image href="(.+?)"').findall(response)

    for name, link, image in match:
        addDir(name, _PLAYPODCAST, image, image, isFolder=False, url=link)


def GetRecent(response):
    recent = []

    match = re.compile('color="CCDDDD"><b>(.+?)</b>').findall(response)   
    for artist in match:
        recent.append(artist)
            
    return recent


def Request():
    addDir('0-9', _LETTER, ICON, FANART, True)
    for i in range(65, 91):
        addDir(chr(i), _LETTER, ICON, FANART, True)


def IsLive():
    try:
        #for live show titles see : http://ramfm.org/momentum/cyan/guide.php
        title = xbmc.Player().getMusicInfoTag().getTitle().lower()
    except:
        title = '' 

    shows = []
    shows.append('Looby Lush')          #Monday
    shows.append('Eighties Flash Back') #Monday
    shows.append('Ladies Night')        #Monday - Verified
    shows.append('Big Eighties Show')   #Tuesday
    shows.append('Night Show')          #Wednesday / Sunday - Verified
    shows.append('Dancing Dave')        #Thursday - Verified
    shows.append('Eighties Wonderland') #Friday
    shows.append('Happy Hour')          #Saturday
    shows.append('Eighties Request')    #Sunday - Verified
    shows.append('Chat Request')        #
    shows.append('Wayne & Dave')        #Friday
    shows.append('Berlin Calling')

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

        resp = cache.getURL(URL, 1800)

        pl       = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)[0]
        filename = pl.getfilename()

        if filename[:-1] in resp:
            return True

        if filename == URL_320:
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
        url = 'http://ramfm.org/momentum/cyan/playlist.php?q=0'
    else:
        url = 'http://ramfm.org/momentum/cyan/playlist.php?q=%s' % letter

    response = cache.getURL(url, 1800)

    hide = ADDON.getSetting('HIDE').lower() == 'true'

    images = {}
    tracks = []

    items = response.split('<!-- start')[1:]
    for item in items:
        item = item.replace(' (& ', ' (& ')

        item = item.replace('&nbsp;', ' ')

        while '  ' in item:
            item = item.replace('  ', ' ')

        mode = MODE_FREE

        if '<i>song recently played</i>' in item:
            mode = MODE_IGNORE if hide else MODE_UNAVAILABLE
        if '<i>artist recently played</i>' in item:
            mode = MODE_IGNORE if hide else MODE_UNAVAILABLE

        title = None

        if mode == MODE_FREE:
            try:                    
                match     = re.compile('<a href="javascript:request\((.+?)\)" title="(.+?)">').findall(item)[0]
                title     = match[1]
                info      = match[0]
                match     = re.compile('<h2>(.+?)</h2>').findall(item)
                artist    = match[0].split(' - ', 1)[0].strip()
                
                try:
                    image = re.compile("<img src='(.+?)'").findall(artist)[0]
                except Exception as e:
                    image = 'na.gif'

                artist = artist.rsplit('>', 1)[-1].strip()

                available = True
            except:
                continue

        if mode == MODE_UNAVAILABLE:
            try:
                match         = re.compile('title="(.+?)">').findall(item) #.+?<p>(.+?)</p></header></a></section><!-- end song recently played /  artists recently played -->').findall(item)[0]
                info          = match[0]
                match         = re.compile('<p>(.+?)</p>').findall(item)[0]
                title         = match.rsplit('(', 1)[0].strip()
                artist, title = title.split(' - ', 1)
                artist        = artist.strip()    
                title         = title.strip() 

                try:
                    image = re.compile("<img src='(.+?)'").findall(artist)[0]
                except Exception as e:
                    image = 'na.gif'

                artist = artist.rsplit('>', 1)[-1].strip()

                available = False

            except Exception as e:
                continue

        if not title:
            continue

        if '/na.gif' not in image:
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


        if '/na.gif' in image:
            try:    image = images[artist]
            except: image = ICON
       
        if available:
            addAvailable(title, artist, image, info)            
        else:
            addUnavailable(title, artist, image, info)


def clean(name):
    name = name.replace('&#233;', 'e')
    name = name.replace('&amp;',  '&')

    return name.strip()


def fixImage(image):
    image = image.replace(' ', '%20')
    return image


def addAvailable(title, artist, image, request):
    image  = fixImage(image)
    fanart = image 
 
    name = title

    if name.startswith('Request'):
        name  = name.split('Request', 1)[-1]

    name = '%s - %s' % (artist, name)
    
    id   = request.split(',')[0]
    ip   = request.split('\'')[1]
    port = request.split('\'')[3]

    url = 'http://www.ramfm.org/req/request.php?songid=%s&samport=%s&samhost=%s' %  (id, port, ip)

    addDir(name, _TRACK, image, fanart, isFolder=False, url=url)


def addUnavailable(title, artist, image, reason):
    image = fixImage(image)
    fanart = image 
  
    name = title + '[I] (%s)[/I]' % reason
    name = '%s - %s' % (artist, name)
    name = clean(name)
    name = '[COLOR=FFFF0000]' + name + '[/COLOR]'

    addDir(name, MODE_UNAVAILABLE, image, fanart, isFolder=False, reason=reason)
        

def getURL():
    kbps = ADDON.getSetting('STREAM')
    if kbps == 'true': # for backward compatible
        kbps = '192'
    if kbps == 'false': # for backward compatible
        kbps = '64'

    response = cache.getURL('http://ramfm.org/sam_files/streams.txt', maxSec=86400)

    streams = json.loads(response)

    key = 'URL_%s' % kbps

    if key in streams:
        return streams[key]

    try:    return DEFAULTS[key]
    except: pass

    return ''


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
            

def MainMenu():   
    CheckVersion()

    addDir(GETTEXT(30054), _PLAYNOW_320, ICON, FANART, False)
    addDir(GETTEXT(30051), _PLAYNOW_HI,  ICON, FANART, False)
    addDir(GETTEXT(30052), _PLAYNOW_MED, ICON, FANART, False)
    addDir(GETTEXT(30053), _PLAYNOW_LO,  ICON, FANART, False)
    addDir(GETTEXT(30037), _RECORD,      ICON, FANART, False)
    addDir(GETTEXT(30031), _REQUEST,     ICON, FANART, True)
    addDir(GETTEXT(30040), _PODCASTS,    ICON, FANART, True)

    play = ADDON.getSetting('PLAY')=='true'
    if play and not xbmc.Player().isPlayingAudio():
        Play()


def addDir(name, mode, thumbnail, fanart, isFolder, **kwargs):
    name = clean(name)

    u = []
    u.append(sys.argv[0])

    u.append('?mode=')
    u.append(str(mode))

    u.append('&name=')
    u.append(urllib.quote_plus(name))

    for key in kwargs:
        u.append('&%s=' % key)
        u.append(urllib.quote_plus(str(kwargs[key])))

    u = ''.join(u)
    
    liz = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    art = {}
    art['thumb']     = thumbnail
    art['poster']    = thumbnail
    art['banner']    = thumbnail
    art['clearart']  = thumbnail
    art['clearlogo'] = thumbnail
    art['icon']      = thumbnail
    art['landscape'] = thumbnail
    art['fanart']    = fanart
    liz.setArt(art) 
 
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


def main():
    params = get_params(sys.argv[2])
    mode   = None

    try:    mode = int(params['mode'])
    except: pass


    if mode in [_PLAYNOW_HI, _PLAYNOW_MED, _PLAYNOW_LO, _PLAYNOW_320]:
        ADDON.setSetting('STREAM', str(mode))
        Play()


    elif mode == _RECORD:
        Record()


    elif mode == _REQUEST:
        if IsPlaying(GETTEXT(30030)):
            xbmc.sleep(500)
            if IsLive():
                DialogOK(GETTEXT(30031), GETTEXT(30046), GETTEXT(30047), GETTEXT(30048))
                Exit()
            else:
                Request()


    elif mode == _LETTER:
        RequestLetter(params['name'])


    elif mode == _TRACK:    
        RequestURL(params['url'])


    elif mode == _PODCASTS:
        ShowPodcasts()


    elif mode == _PLAYPODCAST:
        PlayPodcast(params['name'], params['url'])
        

    elif mode == MODE_UNAVAILABLE:
        ShowError(params['reason'])


    else:
        MainMenu()


main()    
xbmcplugin.endOfDirectory(int(sys.argv[1]))