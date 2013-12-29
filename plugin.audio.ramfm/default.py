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


import urllib
import urllib2
import re
import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
import datetime
import time
import os
import nowplaying
import common

ADDONID  = 'plugin.audio.ramfm'
ADDON    = xbmcaddon.Addon(ADDONID)
HOME     = ADDON.getAddonInfo('path')
TITLE    = 'RAM FM Eighties Hits'
VERSION  = '1.0.16'
URL      = 'http://ramfm.org/ram.pls'
PODCASTS = 'http://www.spreaker.com/show/816525/episodes/feed'
ICON     =  os.path.join(HOME, 'icon.png')
FANART   =  os.path.join(HOME, 'fanart.jpg')
GETTEXT  = ADDON.getLocalizedString


_PLAYNOW     = 100
_REQUEST     = 200
_LETTER      = 300
_TRACK       = 400
_RECORD      = 500
_TALKSHOW    = 600
_PODCASTS    = 700
_PLAYPODCAST = 800
_NOWPLAYING  = 900

_UNAVAILABLE_TRACK  = 2000
_UNAVAILABLE_ARTIST = 3000


def CheckVersion():
    prev = ADDON.getSetting('VERSION')
    curr = VERSION

    if prev == curr:
        return

    ADDON.setSetting('VERSION', curr)

    if prev == '0.0.0':
        d = xbmcgui.Dialog()
        d.ok(TITLE + ' - ' + VERSION, GETTEXT(30017), GETTEXT(30018) , GETTEXT(30019)+' :-)')


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
        d = xbmcgui.Dialog()
	d.ok(TITLE, '', GETTEXT(30023), GETTEXT(30024))
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

    pls  = urllib2.urlopen(URL).read().replace('\n','')
    info = re.compile('File1=(.+?)Title1=(.+?)Length1=').findall(pls)
    url  = info[0][0]
    
    dp = xbmcgui.DialogProgress()
    dp.create(TITLE)

    try:
        DownloaderClass(url, dest, dp)
    except Exception as e:
        if str(e) == 'Canceled':
            pass   
    dp.close()


def StartNowPlaying():
    app = None
    try:
        app = nowplaying.NowPlaying()
        app.doModal()   
    except Exception, e:
        pass

    if app:
        del app


def StartTalkShow():
    #path = os.path.join(ADDON.getAddonInfo('path'), 'talkshow.py')
    #xbmc.executebuiltin('XBMC.RunScript(%s)' % path)
    import talkshow
    talkshow.Start()


def Play():
    slideshow = (ADDON.getSetting('AUTO') == 'true')

    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    pl.clear()    
    pl.add(URL)

    if slideshow:
        #necessary otherwise XBMC gets stuck
        #showing "Working" notification
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    xbmc.Player().play(pl)

    if slideshow:
        xbmc.sleep(1000)
        StartTalkShow()


def PlayPodcast(name, link):
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
        AddPodcast(name, link.split('?')[0])


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


def IsPlayingRAM():
    if not xbmc.Player().isPlayingAudio():
        return False

    pl         = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    label      = pl[0].getLabel().upper()
    return label == 'RAM FM EIGHTIES HIT RADIO'
    

def IsPlaying(message):
    if IsPlayingRAM():
        return True

    dialog = xbmcgui.Dialog()
    if dialog.yesno(TITLE, message,  GETTEXT(30027), '', GETTEXT(30028), GETTEXT(30029)) == 1:
        return False    

    Play()
    return xbmc.Player().isPlayingAudio()


def RequestLetter(letter):
    if not IsPlaying(GETTEXT(30030)):
        return

    if letter == '0-9':
        url = 'http://ramfm.org/requests/playlist0.php'
    else:
        url = 'http://ramfm.org/requests/playlist%s.php' % letter

    response = common.GetHTML(url)

    recent   = GetRecent(response.split('Recently Requested...')[0])
    response = response.split('Search Artist by Last Name')[1]
    hide     = ADDON.getSetting('HIDE')=='true'

    response = response.split('<img src="http://ramfm.org/artistpic/')

    for item in response:
        if 'javascript' in item:
            addAvailable(item, recent)            
        elif not hide:
            addUnavailable(item)


def addUnavailable(item):
    match = re.compile('(.+?)" width.+?&nbsp;&nbsp;(.+?)&nbsp;-&nbsp;(.+?)&nbsp;\(<i>(.+?)</i>\)<br').findall(item)

    for item in match:
        image  = 'http://ramfm.org/artistpic/%s' % item[0]
        image  = image.replace(' ', '%20')   
        artist = item[1]
        title  = item[2]
        reason = item[3]

        mode = _UNAVAILABLE_TRACK
        if 'artist' in reason:
            mode = _UNAVAILABLE_ARTIST       

        name   = artist + ' - ' + title + '[I] (%s)[/I]' % reason
        name   = '[COLOR=FFFF0000]' + name + '[/COLOR]'  
        
        u    = sys.argv[0] 
        u   += '?mode=' + str(mode)
        liz  = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)

        xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)
        

def addAvailable(item, recent):
    match = re.compile('(.+?)" width.+?&nbsp;&nbsp;(.+?)&nbsp;-&nbsp;(.+?)<br.+?javascript:request\((.+?)\)"').findall(item)

    for item in match:
        artist   = item[1]
        isRecent = artist in recent        
        if isRecent and hide:
            continue
        addRequest(item, isRecent)   


def addRequest(request, isRecent):
    image   = 'http://ramfm.org/artistpic/%s' % request[0]
    image   = image.replace(' ', '%20')   
    artist  = request[1]
    title   = request[2]
    details = request[3]

    name = artist + ' - ' + title
    if isRecent:
        name = '[COLOR=FFFF0000]' + name + '[/COLOR]'  

    id   = details.split(',')[0]
    ip   = details.split('\'')[1]
    port = details.split('\'')[3]

    u    = sys.argv[0] 
    u   += '?url='  + urllib.quote_plus('http://www.ramfm.org/req/request.php?songid=%s&samport=%s&samhost=%s' %  (id, port, ip))
    u   += '&mode=' + str(_TRACK)        
    liz  = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)

    xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = u, listitem = liz, isFolder = False)



def RequestURL(url):  
    if not IsPlaying(GETTEXT(30030)):
        return

    response = urllib2.urlopen(url).read()  
    
    failed = 'SongRequester Fail' in response

    if failed:
        match = re.compile('reason given:<br />(.+?)</font>').findall(response)
        ShowError(match[0])
        return        

    xbmcgui.Dialog().ok(GETTEXT(30031), GETTEXT(30032), GETTEXT(30033), GETTEXT(30031))


def ShowError(text):
    xbmcgui.Dialog().ok(GETTEXT(30031), GETTEXT(30034), GETTEXT(30035), text)
            

def Main():   
    CheckVersion()

    addDir(GETTEXT(30036), _PLAYNOW,     False)
    addDir(GETTEXT(30037), _RECORD,      False)
    addDir(GETTEXT(30031), _REQUEST,     True)
    addDir(GETTEXT(30038), _NOWPLAYING,  False)
    addDir(GETTEXT(30039), _TALKSHOW,    False)
    addDir(GETTEXT(30040), _PODCASTS,    True)

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
    thumbnail = ICON
    u         = sys.argv[0] + '?mode=' + str(mode)        
    liz       = xbmcgui.ListItem(name, iconImage=thumbnail, thumbnailImage=thumbnail)

    liz.setProperty('Fanart_Image', FANART)

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder)

   
def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
           params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param



params = get_params()
mode   = None


try:
    mode=int(params['mode'])
except:
    pass


if mode == None:
    Main()

elif mode == _PLAYNOW:
    Play()

elif mode == _RECORD:
    Record()

elif mode == _REQUEST:
    if IsPlaying(GETTEXT(30030)):
        Request()

elif mode == _LETTER:
    try:
        letter=urllib.unquote_plus(params['letter'])
        RequestLetter(letter)
    except:
        pass

elif mode == _TALKSHOW:
    #if IsPlaying(GETTEXT(30041)):
    StartTalkShow()


elif mode == _TRACK:    
    try:
        url=urllib.unquote_plus(params['url'])
        RequestURL(url)
    except:
        pass

elif mode == _PODCASTS:
    ShowPodcasts()


elif mode == _PLAYPODCAST:
    try:
        name = urllib.unquote_plus(params['name'])
        url  = urllib.unquote_plus(params['url'])
        PlayPodcast(name, url)
    except:
        pass


elif mode == _UNAVAILABLE_TRACK:
    ShowError(GETTEXT(30043))


elif mode == _UNAVAILABLE_ARTIST:
    ShowError(GETTEXT(30044))


elif mode == _NOWPLAYING:
    if IsPlaying(GETTEXT(30042)):
        doEnd = False
        StartNowPlaying()
    
try:    
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
except:
    pass
