#
#       Copyright (C) 2014-
#       Sean Poyser (seanpoyser@gmail.com)
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
import os

import urllib
import re

import quicknet
import player
import favourite
import history
import utils
import cache
import sfile

ADDONID  = utils.ADDONID
ADDON    = utils.ADDON
HOME     = utils.HOME
ROOT     = utils.ROOT
PROFILE  = utils.PROFILE
VERSION  = utils.VERSION
ICON     = utils.ICON


FANART   = utils.FANART
SEARCH   = utils.SEARCH
BLANK    = 'NULL'

GETTEXT  = utils.GETTEXT
TITLE    = utils.TITLE
FRODO    = utils.FRODO
GOTHAM   = utils.GOTHAM
HELIX    = utils.HELIX

FILENAME      = utils.FILENAME
FOLDERCFG     = utils.FOLDERCFG


PLAYMEDIA_MODE      = utils.PLAYMEDIA_MODE
ACTIVATEWINDOW_MODE = utils.ACTIVATEWINDOW_MODE
RUNPLUGIN_MODE      = utils.RUNPLUGIN_MODE
ACTION_MODE         = utils.ACTION_MODE

MANUAL_CMD = 'SF_MANUAL_CMD_'

#Display name no longer configurable
#DISPLAYNAME = ADDON.getSetting('DISPLAYNAME') 
#if not DISPLAYNAME:
#    DISPLAYNAME = 'Kodi'
DISPLAYNAME = 'Kodi'

# -----Addon Modes ----- #
_IGNORE                = -10
_MAIN                  = -2
_SUPERSEARCH           = 0
_SUPERSEARCHDEF        = 10
_EXTSEARCH             = 25 #used to trigger new Super Search from outside of addon
_SEPARATOR             = 50
_SETTINGS              = 100
_VIEWTYPE              = 150
_ADDTOXBMC             = 200
_XBMC                  = 300
_FOLDER                = 400
_NEWFOLDER             = 500
_PLAYMEDIA             = 600
_ACTIVATEWINDOW        = 650
_ACTIVATEWINDOW_XBMC   = 660
_ACTIVATESEARCH        = 675
_REMOVEFOLDER          = 700
_REMOVEFAVE            = 800
_RENAMEFOLDER          = 900
_RENAMEFAVE            = 1000
_THUMBFAVE             = 1500
_THUMBFOLDER           = 1600
_PLAYBACKMODE          = 1700
_EDITTERM              = 1900
_EDITFOLDER            = 2000
_EDITFAVE              = 2100
_SECURE                = 2200
_UNSECURE              = 2300
_PLAYLIST              = 2400
_COLOURFOLDER          = 2500
_COLOURFAVE            = 2600
_RECOMMEND_KEY         = 2700
_RECOMMEND_KEY_A       = 2710
_RECOMMEND_IMDB        = 2800
_PLAYTRAILER           = 2900
_EDITSEARCH            = 3000
_IMPORT                = 3100
_IPLAY                 = 3200
_PLAYLISTFILE          = 3300 
_PLAYLISTITEM          = 3400 
_PLAYLISTBROWSE        = 3500
_DELETEPLAYLIST        = 3600
_COPY_TO_SF            = 3700
_COPY_TO_SF_ITEM       = 3800
_PLAYPLAYLIST          = 3900
_URLPLAYLIST           = 4000
_HISTORYSHOW           = 4100
_HISTORYADD            = 4200
_HISTORYREMOVE         = 4300
_MANUAL                = 4400
_CUT                   = 4500
_COPY                  = 4600
_PASTE                 = 4700
_CUTFOLDER             = 4800
_COPYFOLDER            = 4900
_PASTEFOLDER           = 5000
_IEXPLORE              = 5100
_PLAY_FILE             = 5200
_PLAY_FOLDER           = 5300
_PLAY_SUPER_FOLDER     = 5400
_PLAY_SUPER_FOLDER_EXT = 5450


# --------------------- Addon Settings --------------------- #
SHOWNEW               = ADDON.getSetting('SHOWNEW')               == 'true'
SHOWXBMC              = ADDON.getSetting('SHOWXBMC')              == 'true'
SHOWIMPORT            = ADDON.getSetting('SHOWIMPORT')            == 'true'
SHOWSEP               = ADDON.getSetting('SHOWSEP')               == 'true'
SHOWSS                = ADDON.getSetting('SHOWSS')                == 'true'
SHOW_FANART           = ADDON.getSetting('SHOW_FANART')           == 'true'
SHOWRECOMMEND         = ADDON.getSetting('SHOWRECOMMEND')         == 'true'
PLAY_PLAYLISTS        = ADDON.getSetting('PLAY_PLAYLISTS')        == 'true'
METARECOMMEND         = ADDON.getSetting('METARECOMMEND')         == 'true'
SYNOPSRECOMMEND       = ADDON.getSetting('SYNOPSRECOMMEND')       == 'true'
RECOMMENDAUTO         = ADDON.getSetting('RECOMMENDFIRST')        == 'true'
INHERIT               = ADDON.getSetting('INHERIT')               == 'true'
REMOTE                = ADDON.getSetting('REMOTE')                == 'true'
SHOWIPLAY             = ADDON.getSetting('SHOWIPLAY')             == 'true'
SHOWIHISTORY          = ADDON.getSetting('SHOWREMEMBER')          == 'true'
SHOWIEXPLORE          = ADDON.getSetting('SHOWIEXPLORE')          == 'true'
COPY_PLAYLISTS        = ADDON.getSetting('COPY_PLAYLISTS')        == 'true'
ALLOW_PLAYLIST_DELETE = ADDON.getSetting('ALLOW_PLAYLIST_DELETE') == 'true'
DISABLEMOVIEVIEW      = ADDON.getSetting('DISABLEMOVIEVIEW')      == 'true'
ALPHA_SORT            = ADDON.getSetting('ALPHA_SORT')            == 'true'
LABEL_NUMERIC         = ADDON.getSetting('LABEL_NUMERIC')         == 'true'
DEBUG                 = ADDON.getSetting('DEBUG')                 == 'true'
DLG_MENU              = ADDON.getSetting('CONTEXT_STYLE')         == '1'
DEFAULT_FANART        = ADDON.getSetting('DEFAULT_FANART')

VIEWTYPE              = int(ADDON.getSetting('VIEWTYPE'))
CONTENTTYPE           = ADDON.getSetting('CONTENTTYPE')


ART_LANDSCAPE = int(ADDON.getSetting('ART_LANDSCAPE'))
ART_BANNER    = int(ADDON.getSetting('ART_BANNER'))
ART_POSTER    = int(ADDON.getSetting('ART_POSTER'))


CONTENTTYPES = {}
CONTENTTYPES[GETTEXT(35029)] = 'files'
CONTENTTYPES[GETTEXT(35030)] = 'songs'
CONTENTTYPES[GETTEXT(35031)] = 'artists'
CONTENTTYPES[GETTEXT(35032)] = 'albums'
CONTENTTYPES[GETTEXT(35033)] = 'movies'
CONTENTTYPES[GETTEXT(35034)] = 'tvshows'
CONTENTTYPES[GETTEXT(35035)] = 'episodes'
CONTENTTYPES[GETTEXT(35036)] = 'musicvideos'
CONTENTTYPES[GETTEXT(35037)] = ''


if ADDON.getSetting('SHOW_STARTUP_TXT') == 'true':
    utils.DialogOK(ADDON.getSetting('STARTUP_TXT'))
    ADDON.setSetting('SHOW_STARTUP_TXT', 'false')


if REMOTE:
    LOCATION = len(ADDON.getSetting('LOCATION')) > 0
else:
    LOCATION = False

if DEFAULT_FANART == '1':
    FANART = ADDON.getSetting('DEFAULT_IMAGE')

if DEFAULT_FANART == '2':
    FANART = BLANK

CONTENTMODE   = False
ISEARCH_EMPTY = '__iSearch__'

NUMBER_SEP = ' | '
# ---------------------------------------------------------- #

utils.CheckVersion()


global nItem
nItem = 0

global separator
separator = False

global currentFolder
currentFolder = PROFILE


def main():
    addMainItems()

    parseFolder(PROFILE)


def setViewType():
    #logic to obtain viewtype inspired by lambda
    path  = 'special://skin/'
    addon = os.path.join(path, 'addon.xml')
    xml   = sfile.read(addon).replace('\n','').replace('\t','')

    try:    src = re.compile('defaultresolution="(.+?)"').findall(xml)[0]
    except: src = re.compile('<res.+?folder="(.+?)"').findall(xml)[0]

    types = ['MyVideoNav.xml', 'MyMusicNav.xml', 'MyPrograms.xml', 'Includes_View_Modes.xml', 'IncludesViews.xml']
    views = []

    for type in types:
        view = os.path.join(path, src, type)
        view = sfile.read(view).replace('\n','').replace('\t','')
        try:
            view = re.compile('<views>(.+?)</views>').findall(view)[0].split(',')
            for v in view:
                v = int(v)
                if v not in views:
                    views.append(v)
        except:
            pass

    for view in views:
        label = xbmc.getInfoLabel('Control.GetLabel(%d)' % view)
        if label:
            ADDON.setSetting('VIEWTYPE', str(view))
            return True

    return False


def addSuperSearch():
    global separator

    if not SHOWSS:
        return

    separator = False        
    addDir(GETTEXT(30054), _SUPERSEARCH, thumbnail=SEARCH, isFolder=True, infolabels={'plot':GETTEXT(30195)})
    separator = True


def addNewFolderItem(path):
    global currentFolder

    currentFolder = path

    global separator
    if SHOWNEW:
        separator = False
        addDir(GETTEXT(30004), _NEWFOLDER, path=path, thumbnail=ICON, isFolder=False, infolabels={'plot':GETTEXT(30199)})
        separator = True


def addSeparatorItem(menu=None):
    global separator
    separator = False        
    if SHOWSEP:
        addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False, menu=menu)


def populatePasteMenu(menu):
    global currentFolder

    type = xbmcgui.Window(10000).getProperty('SF_TYPE').lower()

    if len(type) == 0:
        return

    folder = 'folder' in type.lower()
    cut    = 'cut'    in type.lower()

    src = xbmcgui.Window(10000).getProperty('SF_FOLDER')

    if folder:
        if cut and currentFolder == xbmcgui.Window(10000).getProperty('SF_FILE'):
            return
        menu.append((GETTEXT(30182), 'XBMC.RunPlugin(%s?mode=%d&paste=%s)' % (sys.argv[0], _PASTEFOLDER, urllib.quote_plus(currentFolder))))
        return

    if src == currentFolder:
        return

    menu.append((GETTEXT(30179), 'XBMC.RunPlugin(%s?mode=%d&paste=%s)' % (sys.argv[0], _PASTE, urllib.quote_plus(currentFolder))))


def addGlobalMenuItem(menu, item, ignore, label, thumbnail, u, keyword):
    if mode == _FOLDER or mode == _MAIN or mode == _XBMC:
        populatePasteMenu(menu)        
            
    if not ignore:
        addFavouriteMenuItem(menu, label, thumbnail, u, keyword)

    if mode != _XBMC:
        cmd = '%s?mode=%d' % (sys.argv[0], _XBMC)
        label = GETTEXT(30040) % DISPLAYNAME
        menu.append((label, 'XBMC.Container.Update(%s)' % cmd))

        if mode == _FOLDER or mode == _MAIN:
            path = thepath
            if path == '':
                path = PROFILE
            menu.append((GETTEXT(30004), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _NEWFOLDER, urllib.quote_plus(path))))

            menu.append((GETTEXT(30166), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _MANUAL, urllib.quote_plus(path))))

    menu.append((GETTEXT(30204), 'XBMC.RunPlugin(%s?mode=%d)' % (sys.argv[0], _VIEWTYPE)))

    menu.append((GETTEXT(30005), 'XBMC.RunPlugin(%s?mode=%d)' % (sys.argv[0], _SETTINGS)))

    addon = utils.findAddon(item)

    if addon == None or addon == ADDONID:
        return

    label = utils.getSettingsLabel(addon)
        
    menu.append((label, 'XBMC.RunPlugin(%s?mode=%d&addon=%s)' % (sys.argv[0], _SETTINGS, urllib.quote_plus(addon))))


def addFavouriteMenuItem(menu, name, thumb, cmd, keyword):
    if mode == _XBMC:
        return

    if len(name) < 1:
        return

    label = GETTEXT(30006) % DISPLAYNAME
    menu.append((label, 'XBMC.RunPlugin(%s?mode=%d&name=%s&thumb=%s&cmd=%s&keyword=%s)' % (sys.argv[0], _ADDTOXBMC, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(cmd), urllib.quote_plus(keyword))))


def getCurrentWindowId():
    winID = xbmcgui.getCurrentWindowId()
    tries = 10

    while winID == 10000 and tries > 0:
        xbmc.sleep(100)
        tries -= 1
        winID = xbmcgui.getCurrentWindowId()

    return winID if winID != 10000 else 10025


def addToXBMC(name, thumb, cmd,  keyword):
    p = get_params(cmd.replace('?', '&'))

    if LABEL_NUMERIC:
        name = name.split(NUMBER_SEP, 1)[-1]

    try: 
        mode = int(p['mode'])
        if mode == _FOLDER:
            label = urllib.unquote_plus(p['label'])
            path  = urllib.unquote_plus(p['path'])
            path  = utils.convertToHome(path)
            cmd   = '%s?label=%s&mode=%d&path=%s' % (sys.argv[0], label, _FOLDER, urllib.quote_plus(path))
    except:
        mode = _IGNORE

    cmd = '"%s"' % cmd   
    
    folder    = mode == _FOLDER
    search    = mode == _SUPERSEARCH
    edit      = mode == _EDITTERM
    activate  = mode == _ACTIVATESEARCH
    activateW = mode == _ACTIVATEWINDOW
    recommend = mode == _RECOMMEND_KEY or mode == _RECOMMEND_IMDB
    iPlay     = mode == _IPLAY
    history   = mode == _HISTORYSHOW
    playSF    = mode == _PLAY_SUPER_FOLDER
    isSF      = cmd.startswith('"plugin://%s' % ADDONID)

    isCached = False
    if activateW:
        isCached = utils.DialogYesNo(GETTEXT(30207))

    try:    fanart = urllib.unquote_plus(p['fanart'])
    except: fanart = ''

    if activate:
        cmd = urllib.unquote_plus(p['cmd'])
    elif isCached or playSF:
        cmd = 'PlayMedia(%s)' % cmd
    elif isSF:
        cmd = cmd.replace('+', '%20')
        cmd = 'ActivateWindow(%d,%s,return)' % (getCurrentWindowId(), cmd)
        if activateW:
            cmd = cmd.replace('mode=%d' % _ACTIVATEWINDOW, 'mode=%d' % _ACTIVATEWINDOW_XBMC) 
    else:
        fanart = ''
        cmd    = 'PlayMedia(%s)' % cmd

    if search:
        name = GETTEXT(30054)

    if edit:
        name = GETTEXT(30054)
        cmd  = cmd.replace('&mode=%d' % _EDITTERM, '&mode=%d' % _SUPERSEARCH)

    if recommend:
        name = GETTEXT(30088)

    if search and ('keyword' not in cmd):
        find    = '&mode=%d' % _SUPERSEARCH
        replace = '%s&keyword=%s' % (find, ISEARCH_EMPTY)

        cmd = cmd.replace(find, replace)
        if not cmd.lower().endswith(',return)'):
            cmd = cmd[:-1] + ',return)'

    if folder:
        thumbnail, fanart = getFolderThumb(path)
        #cmd = favourite.addFanart(cmd, fanart)

    cmd = favourite.addFanart(cmd, fanart)

    keyword = urllib.unquote_plus(keyword)
    if len(keyword) > 0:
        name += ' - %s' % keyword
   
    fave = [name, thumb, cmd]

    file = os.path.join('special://profile', FILENAME)

    #if it is already in there don't add again
    if favourite.findFave(file, cmd)[0]:
        return False    

    faves = favourite.getFavourites(file, validate=False)

    faves.append(fave)

    favourite.writeFavourites(file, faves)

    return True


def refresh():
    xbmc.executebuiltin('Container.Refresh')
    #xbmc.executebuiltin('Container.Refresh(%s)' % (sys.argv[0] + sys.argv[2]))


def removeAutoplay(path):
    cfg  = os.path.join(path, FOLDERCFG)
    clearParam('AUTOPLAY', cfg)

    refresh()


def addAutoplay(path):
    cfg  = os.path.join(path, FOLDERCFG)
    setParam('AUTOPLAY', 'True', cfg)

    refresh()


def addLock(path, name):
    title    = GETTEXT(30079) % name
    password = getText(title, text='', hidden=True)

    if not password:
        return False

    md5 = utils.generateMD5(password)

    cfg  = os.path.join(path, FOLDERCFG)
    setParam('LOCK', md5, cfg)

    return True


def removeLock(path,name):
    title    = GETTEXT(30078) % name
    password = getText(title, text='', hidden=True)

    if not password:
        return False

    md5 = utils.generateMD5(password)

    cfg  = os.path.join(path, FOLDERCFG)
    lock = getParam('LOCK', cfg)

    if lock != md5:
        utils.DialogOK(GETTEXT(30080))
        return False

    clearParam('LOCK', cfg)
    utils.DialogOK(GETTEXT(30081))

    return True


def unlocked(path, lock=None):
    if not lock:
        folderConfig = os.path.join(path, FOLDERCFG)
        lock = getParam('LOCK', folderConfig)

    if not lock:
        return True

    if cache.exists(path):
        return True

    return False


def unlock(path):
    folderConfig = os.path.join(path, FOLDERCFG)
    lock = getParam('LOCK', folderConfig)

    if unlocked(path, lock):
        return True
    
    md5 = checkPassword(path, lock)

    if len(md5) == 0:
        return False

    if md5 == 'ERROR':
        utils.DialogOK(GETTEXT(30080))
        return False

    periods = [0, 1, 5, 15]
    setting = int(ADDON.getSetting('CACHE'))
    period  = periods[setting]

    cache.add(path, period)

    return True


def checkPassword(path, lock=None):
    if not lock:
        folderConfig = os.path.join(path, FOLDERCFG)
        lock = getParam('LOCK', folderConfig)

    title  = GETTEXT(30069) % path.rsplit(os.sep, 1)[-1]
    unlock = getText(title, hidden=True)

    if not unlock:
        return ''

    md5   = utils.generateMD5(unlock)
    match = md5 == lock

    if not match:
        return 'ERROR'

    return md5


def showXBMCFolder():
    global currentFolder
    currentFolder = 'special://profile'
    file = os.path.join(currentFolder, FILENAME)
    parseFile(file)


def cleanForSort(text):
    text = text[0]
    text = text.lower()
    text = utils.Clean(text)
    return text


def parseFile(file, sortorder=0, label_numeric=None, index=0):
    if sortorder == 0:
        sortorder = 1 if ALPHA_SORT else 2

    global separator
    faves = favourite.getFavourites(file)

    if label_numeric == None:
        label_numeric = LABEL_NUMERIC

    text = GETTEXT(30099) % DISPLAYNAME if mode == _XBMC else GETTEXT(30068)

    if sortorder == 1: #ALPHA_SORT:
         faves = sorted(faves, key=lambda x: cleanForSort(x))

    for fave in faves:
        label  = fave[0]
        thumb  = fave[1]
        cmd    = fave[2]
        fanart = favourite.getFanart(cmd)
        desc   = favourite.getOption(cmd, 'desc')

        manualUnset = MANUAL_CMD in cmd

        infolabel = {'plot':desc}
  
        menu  = []
        menu.append((text, 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s&name=%s&thumb=%s)' % (sys.argv[0], _EDITFAVE, urllib.quote_plus(file), urllib.quote_plus(cmd), urllib.quote_plus(label), urllib.quote_plus(thumb))))


        if not PLAY_PLAYLISTS:
            import playlist
            if playlist.isPlaylist(cmd):
                menu.append((GETTEXT(30084), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _PLAYLIST, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        menu.append((GETTEXT(30178), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _COPY, urllib.quote_plus(file), urllib.quote_plus(cmd))))
        #menu.append((GETTEXT(30177), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _CUT, urllib.quote_plus(file),  urllib.quote_plus(cmd))))

        type     = _ACTIVATEWINDOW
        isFolder = True

        if manualUnset:
            type     = _IGNORE
            isFolder = False
        elif 'playmedia(' in cmd.lower():
            type     = _PLAYMEDIA
            isFolder = False

        label, index = addPrefixToLabel(index, label, label_numeric)

        addDir(label, type, cmd=cmd, thumbnail=thumb, isFolder=isFolder, menu=menu, fanart=fanart, infolabels=infolabel)

    separator = len(faves) > 0


def getPrefix(index):
    index += 1
    prefix = str(index) + NUMBER_SEP
    if index < 10:
        prefix = '0' + prefix
    return prefix, index


def addPrefixToLabel(index, label, addPrefix=None):
    if addPrefix == None:
        addPrefix = LABEL_NUMERIC

    if not addPrefix:
        return label, index

    prefix, index = getPrefix(index)

    locn = -1

    SEARCHING = 0
    INELEMENT = 1  
    BODY      = 2  
    mode = SEARCHING

    for c in label:
        locn += 1
        if mode == SEARCHING:
            if c is '[':           
                mode = INELEMENT
            else:
                mode = BODY

        elif mode == INELEMENT:
            if c is ']':
                mode = SEARCHING

        if mode == BODY:
            break
        
    label = label[:locn] + prefix + label[locn:]
    return label, index


def getFolderThumb(path, isXBMC=False):
    cfg    = os.path.join(path, FOLDERCFG)
    cfg    = getParams(cfg)
    thumb  = getParam('ICON',   cfg)
    fanart = getParam('FANART', cfg)

    if thumb and fanart:
        return thumb, fanart

    if isXBMC:
        thumb  = thumb  if (thumb  != None) else 'DefaultFolder.png'
        fanart = fanart if (fanart != None) else FANART
        return thumb, fanart    

    if not INHERIT:
        thumb  = thumb  if (thumb  != None) else ICON
        fanart = fanart if (fanart != None) else FANART
        return thumb, fanart

    if not unlocked(path):
        thumb  = thumb  if (thumb  != None) else ICON
        fanart = fanart if (fanart != None) else FANART
        return thumb, fanart

    faves = favourite.getFavourites(os.path.join(path, FILENAME), 1)   

    if len(faves) < 1:
        thumb  = thumb  if (thumb  != None) else ICON
        fanart = fanart if (fanart != None) else FANART
        return thumb, fanart

    tFave = faves[0][1]
    fFave = favourite.getFanart(faves[0][2])

    thumb  = thumb  if (thumb  != None) else tFave
    fanart = fanart if (fanart != None) else fFave

    fanart = fanart if (fanart and len(fanart) > 0) else FANART

    return thumb, fanart


def addMainItems():
    if mode != _MAIN:
        return

    global separator

    addSuperSearch()

    if SHOWIEXPLORE:
        separator = False
        folder    = 'DefaultFolder.png'
        addDir(GETTEXT(30225), _IEXPLORE, thumbnail=folder, isFolder=True, infolabels={'plot':GETTEXT(30227)})
        separator = True


    if SHOWIPLAY:
        separator = False

        thumbnail = 'DefaultVideoPlaylists.png'
        fanart    = ''

        label = GETTEXT(30146) % DISPLAYNAME
        addDir(label, _IPLAY, thumbnail=thumbnail, isFolder=True, fanart=fanart, infolabels={'plot':GETTEXT(30196)})
        separator = True

    addNewFolderItem(PROFILE)


    if SHOWXBMC:
        separator = False

        thumbnail, fanart = getFolderThumb(PROFILE, True)

        label = GETTEXT(30040) % DISPLAYNAME
        addDir(label, _XBMC, thumbnail=thumbnail, isFolder=True, fanart=fanart, infolabels={'plot':GETTEXT(30197)})
        separator = True


    if SHOWIMPORT and LOCATION:
        separator = False

        thumbnail = 'DefaultFile.png'
        fanart    = ''

        addDir(GETTEXT(30125), _IMPORT, thumbnail=thumbnail, isFolder=False, fanart=fanart, infolabels={'plot':GETTEXT(30198)})
        separator = True 


def playSuperFolder(path, id):
    if path:
        file = os.path.join(path, FILENAME)
    else:
        file = os.path.join(PROFILE, FILENAME)

    faves = favourite.getFavourites(file)

    if ALPHA_SORT:
         faves = sorted(faves, key=lambda x: cleanForSort(x))

    items = []

    for fave in faves:
        label  = fave[0]
        thumb  = fave[1]
        cmd    = fave[2]

        try:
            cmd = re.compile('"(.+?)"').search(cmd).group(1)
            cmd = favourite.removeSFOptions(cmd)
            items.append([label, cmd, thumb])
        except:
            pass

    utils.log('Play Super Folder - Items')
    utils.log(items)

    utils.playItems(items, id)


def playFolder(folder):
    if sfile.isfile(folder):
         folder = sfile.getfolder(folder)

    files = utils.parseFolder(folder, subfolders=False)

    items = []
    for file in files:
        items.append([file[0], file[1]])

    utils.playItems(items)


def playFile(filename): 
    #cmd = 'PlayMedia(%s)' % path
    #xbmc.executebuiltin(cmd)

    items = [[sfile.getfilename(filename), filename]]
    utils.playItems(items)
  

def iExplore(path=None):
    file   = 'DefaultMovies.png'
    folder = 'DefaultFolder.png'

    if not path: 
        path = xbmcgui.Dialog().browse(3, GETTEXT(30226), 'files', '', False, False) 

    try:    items = utils.parseFolder(path)
    except: items = []

    index = 0

    for item in items:
        label  = item[0]
        url    = item[1].replace('\\', '/')
        isFile = item[2]

        title = label
        label, index = addPrefixToLabel(index, label)

        menu = []
            
        if isFile:
            menu.append((GETTEXT(30230), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _PLAY_FOLDER, urllib.quote_plus(url))))
            menu.append((GETTEXT(30047), 'XBMC.RunPlugin(%s?mode=%d&path=%s&label=%s&thumb=%s)' % (sys.argv[0], _COPY_TO_SF_ITEM, urllib.quote_plus(url), urllib.quote_plus(title), urllib.quote_plus(file))))
            addDir(label, _PLAY_FILE, path=url, thumbnail=file, isFolder=False, menu=menu, infolabels={'plot':GETTEXT(30229) % title})
        else:
            menu.append((GETTEXT(30231), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _PLAY_FOLDER, urllib.quote_plus(url))))
            menu.append((GETTEXT(30047), 'XBMC.RunPlugin(%s?mode=%d&path=%s&label=%s&thumb=%s)' % (sys.argv[0], _COPY_TO_SF, urllib.quote_plus(url), urllib.quote_plus(title), urllib.quote_plus(folder))))
            addDir(label, _IEXPLORE, path=url, thumbnail=folder, isFolder=True, menu=menu, infolabels={'plot':GETTEXT(30228) % title})
 

def parseFolder(folder):
    global separator
    global currentFolder

    currentFolder = folder

    try:    current, dirs, files = sfile.walk(folder)
    except: return
   
    dirs = sorted(dirs, key=str.lower)

    folderConfig  = os.path.join(folder,  FOLDERCFG)
    folderConfig  = getParams(folderConfig)
    label_numeric = getParam('NUMERICAL', folderConfig)
    sortorder     = getParam('SORT',      folderConfig)

    if label_numeric:
        label_numeric = label_numeric.lower() == 'true'
    else:
        label_numeric = LABEL_NUMERIC

    try:    sortorder = int(sortorder)
    except: sortorder = 0

    index = 0

    for dir in dirs:
        path = os.path.join(current, dir)

        folderConfig = os.path.join(path, FOLDERCFG)

        visible = 'true' if DEBUG else getParam('VISIBLE', folderConfig)
        if visible and visible.lower() == 'false':
            continue

        folderConfig = getParams(folderConfig)

        lock      = getParam('LOCK',     folderConfig)
        colour    = getParam('COLOUR',   folderConfig)
        desc      = getParam('DESC',     folderConfig)
        autoplay  = getParam('AUTOPLAY', folderConfig)
        
        infolabel = None
        if desc:
            infolabel = {'plot':desc}
    
        menu = []

        menu.append((GETTEXT(30067), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _EDITFOLDER, urllib.quote_plus(path), urllib.quote_plus(dir))))

        if autoplay:
            menu.append((GETTEXT(30235), 'XBMC.Container.Update(%s?mode=%d&path=%s)' % (sys.argv[0], _FOLDER, urllib.quote_plus(path))))
        else:
            menu.append((GETTEXT(30232), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _PLAY_SUPER_FOLDER, urllib.quote_plus(path))))

        #if lock: #lock is now on Edit Super Folder menu
        #    menu.append((GETTEXT(30077), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _UNSECURE, urllib.quote_plus(path), urllib.quote_plus(dir))))
        #else:
        #    menu.append((GETTEXT(30076), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _SECURE,   urllib.quote_plus(path), urllib.quote_plus(dir))))

        thumbnail, fanart = getFolderThumb(path)       

        if not lock:
            menu.append((GETTEXT(30181), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _COPYFOLDER, urllib.quote_plus(path))))
            #menu.append((GETTEXT(30180), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _CUTFOLDER,  urllib.quote_plus(path))))        

        if label_numeric:
            prefix, index = getPrefix(index)
            dir = prefix + dir

        if colour:
            dir = '[COLOR %s]%s[/COLOR]' % (colour, dir)
        
        mode       = _PLAY_SUPER_FOLDER if autoplay else _FOLDER
        isFolder   = not autoplay
        isPlayable = not isFolder
        
        addDir(dir, mode, path=path, thumbnail=thumbnail, isFolder=isFolder, menu=menu, fanart=fanart, infolabels=infolabel, isPlayable=isPlayable)

    if len(dirs) > 0:
        separator = True

    file = os.path.join(folder, FILENAME)

    parseFile(file, sortorder, label_numeric, index)


def getParams(file):
    params = {}

    try:
        config = []
        config = sfile.readlines(file)
    except Exception, e:
        return None

    for line in config:
        items = line.split('=', 1)
        try:    params[items[0]] = items[1]
        except: pass

    return params


def getParam(param, cfg):
    if isinstance(cfg, dict):
        try:    return cfg[param]
        except: return None
        
    try:
        config = []
        config = sfile.readlines(cfg)
    except Exception, e:
        return None

    param  += '='
    for line in config:
        if line.startswith(param):
            return line.split(param, 1)[-1].strip()
    return None


def clearParam(param, file):
    setParam(param, '', file)


def setParam(param, value, file):
    config = []
    try:
        param  = param.upper() + '='
        config = sfile.readlines(file)
    except:
        pass

    value = str(value)
        
    copy = []
    for line in config:
        line = line.strip()
        if (len(line) > 0) and (not line.startswith(param)):
            copy.append(line)

    if len(value) > 0:
        copy.append(param + value)

    f = sfile.file(file, 'w')

    for line in copy:
        f.write(line)
        f.write('\n')
    f.close()


def getColour():
    filename = os.path.join(HOME, 'resources', 'colours', 'Color.xml')

    if not sfile.exists(filename):
        return None

    menu = [[GETTEXT(30087), 'SF_RESET']]

    f = sfile.readlines(filename)
    for line in f:
        if 'name' in line:
            name = line.split('"')[1]            
            menu.append(['[COLOR %s]%s[/COLOR]' % (name, name), name])

    if len(menu) < 2:
        return None

    import menus
    if DLG_MENU:
        option = menus.selectMenu(GETTEXT(30086), menu)
    else:
        option = menus.showMenu(ADDONID, menu)


    #option = menus.selectMenu(GETTEXT(30086), menu)
                 
    if option < 0:
        return None

    return option


def getText(title, text='', hidden=False, allowEmpty=False):
    if text == None:
        text = ''

    kb = xbmc.Keyboard(text.strip(), title)
    kb.setHiddenInput(hidden)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    text = kb.getText().strip()

    if (len(text) < 1) and (not allowEmpty):
        return None

    return text


def getImage():
    root  = HOME.split(os.sep, 1)[0] + os.sep    
    image = xbmcgui.Dialog().browse(2,GETTEXT(30044), 'files', '', False, False, root)
    
    if image and image != root:
        return image

    return None


def getSkinImage():
    image = ''

    skin = xbmc.getSkinDir().lower()
    icon = os.path.join(HOME, 'resources', skin, 'icons')

    items = ['Super Favourite']

    if sfile.exists(icon):
        f = sfile.file(icon, 'r')
        for line in f:
            items.append(line.strip())
        f.close()

        if (len(items) > 1) and utils.DialogYesNo(GETTEXT(30046)):
            import imagebrowser
            return imagebrowser.getImage(ADDONID, items)

    return getImage()


def removeFanartFolder(path):
    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('FANART', '', folderConfig)
    return True


def removeThumbFolder(path):
    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('ICON', '', folderConfig)
    return True


def fanartFolder(path,image=None):
    if not image:
        image = getImage()

    if not image:
        return False
    
    image = utils.convertToHome(image)

    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('FANART', image, folderConfig)
    return True


def thumbFolder(path, image=None):
    if not image:
       image = getImage()

    if not image:
        return False

    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('ICON', utils.convertToHome(image), folderConfig)
    return True


def removeThumbFave(file, cmd):
    fave, index, nFaves = favourite.findFave(file, cmd)

    if len(fave[1]) < 1:
        return False

    fave[1] = ''

    favourite.updateFave(file, fave)
    return True


def removeFanartFave(file, cmd):
    fave, index, nFaves = favourite.findFave(file, cmd)

    fave[2] = favourite.updateSFOption(cmd, 'fanart', '')


    favourite.updateFave(file, fave)
    return True


def fanartFave(file, cmd, image=None):
    if not image:
        image = getImage()

    if not image:
        return False

    fave, index, nFaves = favourite.findFave(file, cmd)

    fave[2] = favourite.addFanart(fave[2], image)

    return favourite.updateFave(file, fave)


def thumbFave(file, cmd, image=None):
    if not image:
        image = getImage()

    if not image:
        return False

    fave, index, nFaves = favourite.findFave(file, cmd)
    fave[1] = image

    return favourite.updateFave(file, fave)


def getFolder(title):
    return utils.GetFolder(title)


def createNewFolder(current):
    text = utils.fileSystemSafe(getText(GETTEXT(30013)))
    if not text:
        return False

    folder = os.path.join(current, text)
    if sfile.exists(folder):
        utils.DialogOK('', GETTEXT(30014) % text)
        return False

    sfile.makedirs(folder)
    return True


def changePlaybackMode(file, cmd):
    OPTION = 'mode'

    try:    mode = int(favourite.getOption(cmd, OPTION))
    except: mode = 0

    playMedia      = GETTEXT(30142)
    activateWindow = GETTEXT(30143)
    runPlugin      = GETTEXT(30144)

    if mode == PLAYMEDIA_MODE:
        playMedia = '[COLOR selected]%s[/COLOR]' % playMedia

    if mode == ACTIVATEWINDOW_MODE:
        activateWindow = '[COLOR selected]%s[/COLOR]' % activateWindow

    if mode == RUNPLUGIN_MODE:
        runPlugin = '[COLOR selected]%s[/COLOR]' % runPlugin

    options = []
    options.append([playMedia,      PLAYMEDIA_MODE])
    options.append([activateWindow, ACTIVATEWINDOW_MODE])
    options.append([runPlugin,      RUNPLUGIN_MODE])

    import menus
    if DLG_MENU:
        option = menus.selectMenu(GETTEXT(30052), options)
    else:
        option = menus.showMenu(ADDONID, options)

    if option == mode:
        return False

    if option == -1:
        return False

    fave, index, nFaves = favourite.findFave(file, cmd)

    if len(fave[2]) < 1:
        return False

    fave[2] = favourite.updateSFOption(fave[2], OPTION, option)

    favourite.updateFave(file, fave)
    return True
    


def editFolder(path, name):
    cfg       = os.path.join(path, FOLDERCFG)
    cfg       = getParams(cfg)

    thumb     = getParam('ICON',     cfg)
    fanart    = getParam('FANART',   cfg)
    lock      = getParam('LOCK',     cfg)
    autoplay  = getParam('AUTOPLAY', cfg)
    sortorder = getParam('SORT',     cfg)

    hasThumb  = thumb  and len(thumb)  > 0
    hasFanart = fanart and len(fanart) > 0

    REMOVE       = 0
    RENAME       = 1
    CHOOSETHUMB  = 2
    PASTETHUMB   = 3
    CHOOSEFANART = 4
    PASTEFANART  = 5
    REMOVETHUMB  = 6
    REMOVEFANART = 7
    DESCRIPTION  = 8
    PASTEDESC    = 9
    COLOUR       = 10
    LOCK         = 11
    AUTOPLAY     = 12
    SORTORDER    = 13

    thumb_clip  = xbmcgui.Window(10000).getProperty('SF_THUMB')
    fanart_clip = xbmcgui.Window(10000).getProperty('SF_FANART')
    desc_clip   = xbmcgui.Window(10000).getProperty('SF_DESCRIPTION')

    options = []
    options.append([GETTEXT(30011), REMOVE])
    options.append([GETTEXT(30012), RENAME])

    #lock/unlock
    label = GETTEXT(30077) if lock else GETTEXT(30076) 
    options.append([label, LOCK])

    #autoplay
    label = GETTEXT(30234) if autoplay else GETTEXT(30233)
    options.append([label, AUTOPLAY])

    #sortorder
    options.append([GETTEXT(30237), SORTORDER])
 
    #description
    options.append([GETTEXT(30194), DESCRIPTION])
    if len(desc_clip) > 0:
        options.append([GETTEXT(30212), PASTEDESC])

    #thumb
    options.append([GETTEXT(30043), CHOOSETHUMB])

    if len(thumb_clip) > 0:
        options.append([GETTEXT(30210), PASTETHUMB])

    if hasThumb:
        options.append([GETTEXT(30097), REMOVETHUMB])

    #fanart
    options.append([GETTEXT(30107), CHOOSEFANART])

    if len(fanart_clip) > 0:
        options.append([GETTEXT(30211), PASTEFANART])

    if hasFanart:
        options.append([GETTEXT(30108), REMOVEFANART])

    options.append([GETTEXT(30085), COLOUR])

    import menus
    if DLG_MENU:
        option = menus.selectMenu(name, options)
    else:
        option = menus.showMenu(ADDONID, options)

    if option == REMOVE:
        return removeFolder(path)

    if option == RENAME:
        return renameFolder(path)

    if option == DESCRIPTION:
        return editFolderDescription(path, name)

    if option == PASTEDESC:
        return editFolderDescription(path, name, desc_clip)

    if option == CHOOSETHUMB:
        return thumbFolder(path)

    if option == PASTETHUMB:
        return thumbFolder(path, thumb_clip)

    if option == CHOOSEFANART:
        return fanartFolder(path)

    if option == PASTEFANART:
        return fanartFolder(path, fanart_clip)

    if option == REMOVETHUMB:
        return removeThumbFolder(path)

    if option == REMOVEFANART:
        return removeFanartFolder(path)

    if option == COLOUR:
        return colourFolder(path)

    if option == LOCK:
        dir = sfile.getfilename(path)
        if lock:
            removeLock(path, name)
        else:
            addLock(path, name)
        refresh()

    if option == AUTOPLAY:
        if autoplay:
            removeAutoplay(path)
        else:
            addAutoplay(path)

    if option == SORTORDER:
        setFolderSortOrder(path, sortorder)


    return False


def setFolderSortOrder(path, current):
    try:    current = int(current)
    except: current = 0

    config = GETTEXT(30238) # 0
    alpha  = GETTEXT(30239) # 1
    manual = GETTEXT(30240) # 2

    if current == 0:
        config = '[COLOR selected]%s[/COLOR]' % config

    if current == 1:
        alpha = '[COLOR selected]%s[/COLOR]' % alpha

    if current == 2:
        manual = '[COLOR selected]%s[/COLOR]' % manual

    options = []
    options.append([config, 0])
    options.append([alpha,  1])
    options.append([manual, 2])

    import menus
    if DLG_MENU:
        option = menus.selectMenu(GETTEXT(30237), options)
    else:
        option = menus.showMenu(ADDONID, options)

    if option == current:
        return False

    if option == -1:
        return False

    cfg = os.path.join(path, FOLDERCFG)

    setParam('SORT', option, cfg)
    

def editFave(file, cmd, name, thumb):
    fanart    = favourite.getFanart(cmd)
    hasThumb  = len(thumb)  > 0
    hasFanart = len(fanart) > 0
    hasMode   = cmd.startswith('PlayMedia')

    UP           = 0
    DOWN         = 1
    COPY         = 2
    MOVE         = 3
    REMOVE       = 4
    RENAME       = 5
    DESCRIPTION  = 6
    PASTEDESC    = 7
    CHOOSETHUMB  = 8
    PASTETHUMB   = 9
    CHOOSEFANART = 10
    PASTEFANART  = 11
    REMOVETHUMB  = 12
    REMOVEFANART = 13
    COLOUR       = 14
    PLAYBACKMODE = 15
    MANUALEDIT   = 16

    thumb_clip  = xbmcgui.Window(10000).getProperty('SF_THUMB')
    fanart_clip = xbmcgui.Window(10000).getProperty('SF_FANART')
    desc_clip   = xbmcgui.Window(10000).getProperty('SF_DESCRIPTION')

    path = sfile.getfolder(file)
    cfg  = os.path.join(path, FOLDERCFG)

    try:    sortorder = int(getParam('SORT', cfg))
    except: sortorder = 0

    if sortorder == 0:
        sortorder = 1 if ALPHA_SORT else 2

    options = []

    if sortorder == 2:
        options.append([GETTEXT(30041), UP])
        options.append([GETTEXT(30042), DOWN])

    options.append([GETTEXT(30007), COPY])
    options.append([GETTEXT(30008), MOVE])
    options.append([GETTEXT(30009), REMOVE])
    options.append([GETTEXT(30010), RENAME])

    #description
    options.append([GETTEXT(30194), DESCRIPTION])
    if len(desc_clip) > 0:
        options.append([GETTEXT(30212), PASTEDESC])

    #thumb
    options.append([GETTEXT(30043), CHOOSETHUMB])

    if len(thumb_clip) > 0:
        options.append([GETTEXT(30210), PASTETHUMB])

    if hasThumb:
        options.append([GETTEXT(30097), REMOVETHUMB])

    #fanart
    options.append([GETTEXT(30107), CHOOSEFANART])

    if len(fanart_clip) > 0:
        options.append([GETTEXT(30211), PASTEFANART])

    if hasFanart:
        options.append([GETTEXT(30108), REMOVEFANART])

    options.append([GETTEXT(30085), COLOUR])

    if hasMode:
        options.append([GETTEXT(30052), PLAYBACKMODE])

    options.append([GETTEXT(30168), MANUALEDIT])

    import menus
    if DLG_MENU:
        option = menus.selectMenu(name, options)
    else:
        option = menus.showMenu(ADDONID, options)

    if option == UP:
        return favourite.shiftFave(file, cmd, up=True)

    if option == DOWN:
        return favourite.shiftFave(file, cmd, up=False)

    if option == COPY:
        return copyFave(file, cmd)

    if option == MOVE:
        return moveFave(file, cmd)

    if option == REMOVE:
        return favourite.removeFave(file, cmd)

    if option == RENAME:
        return renameFave(file, cmd)

    if option == DESCRIPTION:
        return editDescription(file, cmd, name)

    if option == PASTEDESC:
        return editDescription(file, cmd, name, desc_clip)

    if option == CHOOSETHUMB:
        return thumbFave(file, cmd)

    if option == PASTETHUMB:
        return thumbFave(file, cmd, thumb_clip)

    if option == CHOOSEFANART:
        return fanartFave(file, cmd)

    if option == PASTEFANART:
        return fanartFave(file, cmd, fanart_clip)

    if option == REMOVETHUMB:
        return removeThumbFave(file, cmd)

    if option == REMOVEFANART:
        return removeFanartFave(file, cmd)

    if option == COLOUR:
        return colourFave(file, cmd)

    if option == PLAYBACKMODE:
        return changePlaybackMode(file, cmd)

    if option == MANUALEDIT:
        return manualEdit(file, cmd, name, thumb)

    return False


def editFolderDescription(path, name, desc=None):
    cfg  = os.path.join(path, FOLDERCFG)

    if desc == None:
        desc = getParam('DESC', cfg)
        desc = getText(name, text=desc, hidden=False, allowEmpty=True)

    if desc == None:
        return False

    setParam('DESC', desc, cfg)

    return True


def editDescription(file, cmd, name, desc=None):
    fave, index, nFaves = favourite.findFave(file, cmd)
    if not fave:
        return False

    if desc == None:
        desc = favourite.getOption(cmd, 'desc')
        desc = getText(name, text=desc, hidden=False, allowEmpty=True)

    if desc == None:
        return False

    fave[2] = favourite.updateSFOption(cmd, 'desc', desc)

    favourite.updateFave(file, fave)
    return True


def manualEdit(file, _cmd, name='', thumb='', editName=True):
    cmd = _cmd
    if editName:
        name = getText(GETTEXT(30021), name, allowEmpty=True)

        if name == None:
            return False

    type = manualType(name, cmd)
    if type < 0:
        return False

    windowID    = '-1'
    originalID  = ''
    if type == ACTIVATEWINDOW_MODE:
        windowID, originalID = getWindowID(cmd, name)
            
    if windowID == '0':
        return False

    newCmd = ''

    manualUnset = MANUAL_CMD in cmd

    title = GETTEXT(30170) % name
 
    if manualUnset:
        newCmd = getText(title, '', allowEmpty=True)
    else:
        if type == ACTION_MODE:
            cmd = cmd.split('ExecuteBuiltin("', 1)[-1]
            cmd = cmd.rsplit('")')[0]
        else:
            cmd = re.compile('\((.+?)\)').search(cmd).group(1)

        cmd = cmd.lower()

        if _cmd.lower().startswith('activatewindow'):
            if cmd == originalID:
                cmd = ''
            else:
                cmd = cmd.split(',', 1)[-1].strip()  

        if cmd.endswith(',return'):
            cmd = cmd[:-7]

        if cmd.startswith('&quot;'):
            cmd = cmd[6]
        if cmd.endswith('&quot;'):
            cmd = cmd[:-6]
        if cmd.startswith('"'):
            cmd = cmd[1:]
        if cmd.endswith('"'):
            cmd = cmd[:-1]

        if cmd.lower() == 'return':
            cmd = ''

        cmd = cmd.replace('"', '')

        newCmd = getText(title, cmd, allowEmpty=True)

    if newCmd == None:
        return False

    newCmd = buildManualFave(type, newCmd, windowID)

    fave = []
    fave.append(name)
    fave.append(thumb)
    fave.append(newCmd)

    return favourite.replaceFave(file, fave, _cmd)


def buildManualFave(type, cmd, windowID='-1'):   
    if type == ACTIVATEWINDOW_MODE:
        if cmd:
            return 'ActivateWindow(%s,"%s",return)' % (windowID, cmd) 
        else:
            return 'ActivateWindow(%s,return)' % (windowID) 

    if len(cmd) == 0:
        return getDefaultManualCmd()

    if type == PLAYMEDIA_MODE:
        return 'PlayMedia("%s")' % cmd

    elif type == RUNPLUGIN_MODE:
        cmd = cmd.replace(',', '","')
        return 'RunScript("%s")' % cmd

    elif type == ACTION_MODE:
        return 'ExecuteBuiltin("%s")' % cmd


    return getDefaultManualCmd()


def getWindowID(cmd, name):
    try:
        originalID = re.compile('activatewindow\((.+?),').search(cmd.lower()).group(1)
    except:
        try:    originalID = re.compile('activatewindow\((.+?)\)').search(cmd.lower()).group(1)
        except: originalID = ''

    try:
        if len(name) > 0:
            title = GETTEXT(30175) % name
        else:
            title = GETTEXT(30176)

        windowID = getText(title, originalID )

        if windowID:
            return windowID, originalID
    except:
        pass

    return '0', originalID


def colourise(cmd, type, action):
    if cmd.lower().startswith(type):
        action = '[COLOR selected]%s[/COLOR]' % action

    return action


def manualType(name, cmd):
    title          = GETTEXT(30169) % name
    playMedia      = colourise(cmd, 'playmedia',      GETTEXT(30172))
    activateWindow = colourise(cmd, 'activatewindow', GETTEXT(30173))
    runScript      = colourise(cmd, 'runscript',      GETTEXT(30174))
    action         = colourise(cmd, 'executebuiltin', GETTEXT(30193))

    options = []
    options.append([playMedia,      PLAYMEDIA_MODE])
    options.append([activateWindow, ACTIVATEWINDOW_MODE])
    options.append([runScript,      RUNPLUGIN_MODE])
    options.append([action,         ACTION_MODE])

    import menus
    option = menus.selectMenu(title, options)
    #if DLG_MENU:
    #    option = menus.selectMenu(title, options)
    #else:
    #    option = menus.showMenu(ADDONID, options)

    return option


def manualAdd(folder):
    name = getText(GETTEXT(30021), '', allowEmpty=True)

    if name == None:
        return False

    cmd   = getDefaultManualCmd()
    thumb = ''

    file  = os.path.join(folder, FILENAME)
    return manualEdit(file, cmd, name, thumb, editName=False)


def getDefaultManualCmd():
    id = int(ADDON.getSetting('MANUAL_ID'))
    ADDON.setSetting('MANUAL_ID', str(id+1))

    return MANUAL_CMD + str(id)


def editSearch(file, cmd, name, thumb):
    fanart    = favourite.getFanart(cmd)
    hasThumb  = len(thumb) > 0
    hasFanart = len(fanart) > 0

    UP           = 0
    DOWN         = 1
    RENAME       = 2
    CHOOSETHUMB  = 3
    PASTETHUMB   = 4
    CHOOSEFANART = 5
    PASTEFANART  = 6
    REMOVETHUMB  = 7
    REMOVEFANART = 8
    COLOUR       = 9

    thumb_clip  = xbmcgui.Window(10000).getProperty('SF_THUMB')
    fanart_clip = xbmcgui.Window(10000).getProperty('SF_FANART')

    options = []


    if not ALPHA_SORT:
        options.append([GETTEXT(30041), UP])
        options.append([GETTEXT(30042), DOWN])

    options.append([GETTEXT(30010), RENAME])

    #thumb
    options.append([GETTEXT(30043), CHOOSETHUMB])

    if len(thumb_clip) > 0:
        options.append([GETTEXT(30210), PASTETHUMB])

    if hasThumb:
        options.append([GETTEXT(30097), REMOVETHUMB])


    #fanart
    options.append([GETTEXT(30107), CHOOSEFANART])

    if len(fanart_clip) > 0:
        options.append([GETTEXT(30211), PASTEFANART])    

    if hasFanart:
        options.append([GETTEXT(30108), REMOVEFANART])

    options.append([GETTEXT(30085), COLOUR])

    import menus
    if DLG_MENU:
        option = menus.selectMenu(name, options)
    else:
        option = menus.showMenu(ADDONID, options)

    if option == UP:
        return favourite.shiftFave(file, cmd, up=True)

    if option == DOWN:
        return favourite.shiftFave(file, cmd, up=False)

    if option == RENAME:
        return renameFave(file, cmd)

    if option == CHOOSETHUMB:
        return thumbFave(file, cmd)

    if option == PASTETHUMB:
        return thumbFave(file, cmd, thumb_clip)

    if option == REMOVETHUMB:
        return removeThumbFave(file, cmd)

    if option == CHOOSEFANART:
        return fanartFave(file, cmd)

    if option == PASTEFANART:
        return fanartFave(file, cmd, fanart_clip)

    if option == REMOVEFANART:
        return removeFanartFave(file, cmd)

    if option == COLOUR:
        return colourFave(file, cmd)

    return False


def renameFolder(path):
    label = path.rsplit(os.sep, 1)[-1]
    title = label

    try:    text  = utils.fileSystemSafe(getText(GETTEXT(30015) % title, label))
    except: title = utils.fix(title)

    if not text:
        return False

    root = path.rsplit(os.sep, 1)[0]
    newName = os.path.join(root, text)

    sfile.rename(path, newName)

    return True


def colourFolder(path):
    colour = getColour()

    if not colour:
        return False

    cfg  = os.path.join(path, FOLDERCFG)

    if colour == 'SF_RESET':
        clearParam('COLOUR', cfg)
    else:
        setParam('COLOUR', colour, cfg)

    return True


def removeFolder(path):
    label = path.rsplit(os.sep, 1)[-1]
    label = utils.fix(label)
    if not utils.DialogYesNo(GETTEXT(30016) % label, GETTEXT(30017), GETTEXT(30018)):
        return False

    sfile.rmtree(path)
    return True


def moveFave(file, cmd):
    if not copyFave(file, cmd, move=True):
        return False

    return favourite.removeFave(file, cmd)


def copyFave(file, cmd, move=False):
    copy, index, nFaves = favourite.findFave(file, cmd)
    if not copy:
        return False

    text = GETTEXT(30020) if move else GETTEXT(30019)

    folder = getFolder(text)
    if not folder:
        return False
  
    file  = os.path.join(folder, FILENAME)
    return favourite.copyFave(file, copy)


def renameFave(file, cmd):
    fave, index, nFaves = favourite.findFave(file, cmd)
    if not fave:
        return False

    newName = getText(GETTEXT(30021), text=fave[0], allowEmpty=True)

    if newName == None:
        return False

    return favourite.renameFave(file, cmd, newName)


def decolourize(text):
    text = re.sub('\[COLOR (.+?)\]', '', text)
    text = re.sub('\[/COLOR\]',      '', text)
    return text


def colourFave(file, cmd):
    colour = getColour()

    if not colour:
        return False

    copy = []
    faves = favourite.getFavourites(file)
    for fave in faves:
        if favourite.equals(fave[2], cmd):
            fave[0]   = decolourize(fave[0])
            if colour != 'SF_RESET': 
                fave[0] = '[COLOR %s]%s[/COLOR]' % (colour, fave[0])

        copy.append(fave)

    favourite.writeFavourites(file, copy)

    return True


def getTVDB(imdb):
    try:
        import json

        if not imdb.endswith('?'):
            imdb = imdb + '?'

        url  = 'http://api.themoviedb.org/3/find/%sapi_key=57983e31fb435df4df77afb854740ea9&external_source=imdb_id' % imdb
        html = quicknet.getURL(url, maxSec=5*86400, agent='Firefox')
        jsn  = json.loads(html)  

        thumbnail = BLANK
        fanart    = FANART

        movies = jsn['movie_results']
        tvs    = jsn['tv_results']

        source = None
        if len(movies) > 0:
            source = movies[0]
        elif len(tvs) > 0:
            source = tvs[0]

        if source:
            try:    thumbnail = 'http://image.tmdb.org/t/p/w342' + source['poster_path']
            except: pass

            try:    fanart = 'http://image.tmdb.org/t/p/w780' + source['backdrop_path']
            except: pass

        return thumbnail,  fanart

    except:
        pass

    return BLANK, FANART


def getMeta(grabber, name, type, year=None, season=None, episode=None, imdb=None):
    infoLabels = {}

    imdb = imdb.replace('/?', '')

    if year=='':
        year = None

    if year == None:
        try:    year = re.search('\s*\((\d\d\d\d)\)',name).group(1)
        except: year = None

    if year is not None:
        name = name.replace(' ('+year+')','').replace('('+year+')','')
        
    if 'movie' in type:
        meta = grabber.get_meta('movie', name, imdb, None, year, overlay=6)

        infoLabels = {'rating': meta['rating'],'trailer_url': meta['trailer_url'],'duration': meta['duration'],'genre': meta['genre'],'mpaa':"rated %s"%meta['mpaa'],'plot': meta['plot'],'title': meta['title'],'writer': meta['writer'],'cover_url': meta['cover_url'],'director': meta['director'],'cast': meta['cast'],'fanart': meta['backdrop_url'],'tmdb_id': meta['tmdb_id'],'year': meta['year']}

    elif 'tvshow' in type:
        meta = grabber.get_episode_meta(name, imdb, season, episode)
        infoLabels = {'rating': meta['rating'],'genre': meta['genre'],'mpaa':"rated %s"%meta['mpaa'],'plot': meta['plot'],'title': meta['title'],'cover_url': meta['cover_url'],'fanart': meta['backdrop_url'],'Episode': meta['episode'],'Aired': meta['premiered']}

    return infoLabels


def getMovieMenu(infolabels, menu=None):    
    if not menu:
        menu = []

    if len(infolabels) == 0:
        return menu

    menu.append((GETTEXT(30090), 'Action(Info)'))

    try:
        if 'trailer_url' in infolabels and len(infolabels['trailer_url']) > 0:   
            menu.append((GETTEXT(30091), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _PLAYTRAILER,  urllib.quote_plus(infolabels['trailer_url']))))          
    except:
        pass

    return menu


def hasIMDBRecommendations(imdb):
    url  = 'http://imdb.com/title/%s' % imdb
    html = quicknet.getURL(url, maxSec=86400, agent='Firefox')

    items = re.compile('<div class="rec_details".+?<a href="/title/(.+?)/?ref_=tt_rec_tt"><b>(.+?)</b></a>.+?<div class="rec-outline">(.+?)</p>').findall(html)

    return len(items) > 0


def recommendIMDB(imdb, keyword, fallback=True):
    grabber = None
    if METARECOMMEND:
        try:
            from metahandler import metahandlers
            grabber = metahandlers.MetaData()
        except:
            pass

    url  = 'http://imdb.com/title/%s' % imdb
    html = quicknet.getURL(url, maxSec=86400, agent='Firefox')

    items = re.compile('<div class="rec_details".+?<a href="/title/(.+?)/?ref_=tt_rec_tt"><b>(.+?)</b></a>.+?<div class="rec-outline">(.+?)</p>').findall(html)

    if len(items) == 0 and fallback:
        return recommendKey(keyword, RECOMMENDAUTO)

    count = 0

    infolabels = {}

    for item in items:
        imdb      = item[0]
        name      = item[1]

        thumbnail = BLANK
        fanart    = FANART

        if grabber:
            #thumbnail,  fanart = getTVDB(imdb)
            infolabels = getMeta(grabber, '', 'movie', year=None, imdb=imdb)
            thumbnail  = infolabels['cover_url']
            fanart     = infolabels['fanart']

        try:
            outline = utils.RemoveTags(item[2]).strip() if grabber else None
            if outline:
                if ('plot' not in infolabels) or (not infolabels['plot']):
                    infolabels['plot'] = outline
                if SYNOPSRECOMMEND:
                    name += ' - [I]%s[/I]' % utils.unescape(utils.fix(infolabels['plot']))

            menu = getMovieMenu(infolabels)
            getHistoryItem(menu, name, thumbnail, fanart, False)

            name, count = addPrefixToLabel(count, name)

            addDir(name, _SUPERSEARCH, thumbnail=thumbnail, isFolder=True, menu=menu, fanart=fanart, keyword=name, imdb=imdb, infolabels=infolabels, totalItems=len(items))

        except:
            pass

    return count

    
def recommendKey(keyword, autoRecommend):
    grabber = None
    if METARECOMMEND:
        try:
            from metahandler import metahandlers
            grabber = metahandlers.MetaData()
        except:
            pass

    url  = 'http://m.imdb.com/find?q=%s' % keyword.replace(' ', '+') #use mobile site as less data
    html = quicknet.getURL(url, maxSec=86400, agent='Apple-iPhone/')

    items = re.compile('<div class="title">.+?<a href="/title/(.+?)/">(.+?)</a>(.+?)</div>').findall(html)

    infolabels = {}

    index = 0

    for item in items:
        imdb = item[0]
        name = item[1]

        if autoRecommend:
            autoRecommend = hasIMDBRecommendations(imdb)

        if 'video game' in item[2].lower():
            continue

        label = name + ' ' + item[2].strip()

        thumbnail = BLANK
        fanart    = FANART

        if grabber:
            #thumbnail,  fanart = getTVDB(imdb)
            infolabels = getMeta(grabber, name, 'movie', year=None, imdb=imdb)
            thumbnail  = infolabels['cover_url']
            fanart     = infolabels['fanart'] 

            if SYNOPSRECOMMEND: 
                if ('plot' in infolabels) and (infolabels['plot']):
                    label += ' - [I]%s[/I]' % utils.unescape(infolabels ['plot'])

        menu = getMovieMenu(infolabels)
        getHistoryItem(menu, name, thumbnail, fanart, False)

        label, index = addPrefixToLabel(index, label)

        if autoRecommend:
            autoRecommend = False
            addDir(label, _RECOMMEND_KEY_A,  thumbnail=thumbnail, isFolder=True, menu=menu, fanart=fanart, keyword=name, infolabels=infolabels)
            if recommendIMDB(imdb, keyword, fallback=False) > 0:
                return
        else:
            addDir(label, _SUPERSEARCH, thumbnail=thumbnail, isFolder=True, menu=menu, fanart=fanart, keyword=name, imdb=imdb, infolabels=infolabels, totalItems=len(items))
    

def editSearchTerm(_keyword):
    keyword = getText(GETTEXT(30057), _keyword)

    if (not keyword) or len(keyword) < 1:
        keyword = _keyword

    winID = xbmcgui.getCurrentWindowId()
    cmd   = 'ActivateWindow(%d,"%s?mode=%d&keyword=%s")' % (winID, sys.argv[0], _SUPERSEARCH, keyword)
    activateWindowCommand(cmd)   


def externalSearch():
    xbmcplugin.endOfDirectory(int(sys.argv[1])) 

    keyword = ''

    kb = xbmc.Keyboard(keyword, GETTEXT(30054))
    kb.doModal()
    if kb.isConfirmed():
        keyword = kb.getText()

        cmd = '%s?mode=%d&keyword=%s' % (sys.argv[0], _SUPERSEARCH, keyword)
        xbmc.executebuiltin('XBMC.Container.Refresh(%s)' % cmd)


def iHistoryBrowse():
    items = history.browse()
    items = sorted(items, key=lambda x: x[0].lower())

    index = 0

    for item in items:
        label  = item[0]
        thumb  = item[1]
        fanart = favourite.getFanart(item[2])

        menu = []

        menu.append((GETTEXT(30165) % label, 'XBMC.RunPlugin(%s?mode=%d&name=%s)' % (sys.argv[0], _HISTORYREMOVE, urllib.quote_plus(label))))

        desc = GETTEXT(30200) % label

        text, index = addPrefixToLabel(index, label)

        addDir(text, _SUPERSEARCH, thumbnail=thumb, isFolder=True, fanart=fanart, keyword=label, menu=menu, infolabels={'plot':desc})

    return False


def iHistoryAdd(keyword, image, fanart):
    return history.add(keyword, image, fanart)


def iHistoryRemove(name):
    return history.remove(name)


def iPlay():
    #add browse item
    #addDir(GETTEXT(30148), _PLAYLISTBROWSE, thumbnail='DefaultMusicPlaylists.png', isFolder=False) 

    import playlist

    nItems = 0

    folder = os.path.join(ROOT, 'PL')
    sfile.makedirs(folder)

    #parse SF folder   
    nItems += addPlaylistItems(playlist.parseFolder(folder), 'DefaultMusicVideos.png', delete=True)

    #parse SF list 
    file = os.path.join(folder, FILENAME)

    playlists = favourite.getFavourites(file, validate=False)
    items = []
    for playlist in playlists:
        name  = playlist[0]
        thumb = playlist[1]
        cmd   = playlist[2]
        items.append([cmd, name, thumb])

    nItems += addPlaylistItems(items, delete=True)

    #parse Kodi folders    
    folder  = 'special://profile/playlists'
    nItems += addPlaylistItems(playlist.parseFolder(os.path.join(folder, 'video')), 'DefaultMovies.png',      delete=ALLOW_PLAYLIST_DELETE)
    nItems += addPlaylistItems(playlist.parseFolder(os.path.join(folder, 'music')), 'DefaultMusicSongs.png',  delete=ALLOW_PLAYLIST_DELETE)
    nItems += addPlaylistItems(playlist.parseFolder(os.path.join(folder, 'mixed')), 'DefaultMusicVideos.png', delete=ALLOW_PLAYLIST_DELETE)

    return nItems > 0


def addPlaylistItems(items, thumbnail='DefaultMovies.png', delete=False):
    for item in items:
        path  = item[0]
        title = item[1]
        if len(item) > 2:
            thumbnail = item[2]

        menu = []

        #browse
        cmd = '%s?mode=%d' % (sys.argv[0], _PLAYLISTBROWSE)
        #menu.append((GETTEXT(30148), 'XBMC.Container.Update(%s)' % cmd))
        menu.append((GETTEXT(30148), 'XBMC.RunPlugin(%s)' % cmd))

        #browse for URL
        cmd = '%s?mode=%d' % (sys.argv[0], _URLPLAYLIST)
        #menu.append((GETTEXT(30153), 'XBMC.Container.Update(%s)' % cmd))
        menu.append((GETTEXT(30153), 'XBMC.RunPlugin(%s)' % cmd))

        #menu.append((GETTEXT(30084), 'XBMC.PlayMedia(%s)' % path))
        menu.append((GETTEXT(30084), 'XBMC.RunPlugin(%s?mode=%d&cmd=%s)' % (sys.argv[0], _PLAYLIST, urllib.quote_plus(path))))

        if delete:
            menu.append((GETTEXT(30150), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _DELETEPLAYLIST, urllib.quote_plus(path))))

        menu.append((GETTEXT(30047), 'XBMC.RunPlugin(%s?mode=%d&path=%s&label=%s&thumb=%s)' % (sys.argv[0], _COPY_TO_SF, urllib.quote_plus(path), urllib.quote_plus(title), urllib.quote_plus(thumbnail))))
        

        addDir(title, _PLAYLISTFILE, path=path, thumbnail=thumbnail, menu=menu) 

    return len(items)


def iPlaylistDelete(path):
    #delete from SF list of Playlists
    folder    = os.path.join(ROOT, 'PL')
    file      = os.path.join(folder, FILENAME)
    playlists = favourite.getFavourites(file, validate=False)
    updated   = []

    for playlist in playlists:
        if playlist[2] != path:
            updated.append(playlist)

    if len(updated) < len(playlists):
        favourite.writeFavourites(file, updated)
        return True

    if sfile.exists(path):
        utils.DeleteFile(path)
        return True

    return False


def iPlaylistItem(path, title='', thumb='DefaultMovies.png'):
    #if currently in program menu play directly
    if xbmcgui.getCurrentWindowId() == 10001:        
        liz = xbmcgui.ListItem(title, iconImage=thumb, thumbnailImage=thumb)
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(path, liz)
        xbmc.Player().play(pl)
        return

    item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)


def iPlaylistURL(url):
    try:    html = quicknet.getURL(url, maxSec=600, tidy=False)
    except: html = ''
    
    nItems = addItems(html.split('\n'))

    if nItems == 0:
        utils.DialogOK(GETTEXT(30155), url)
        return False

    return True


def iPlaylistFile(path):    
    if not sfile.exists(path):
        return iPlaylistURL(path)

    playlist = sfile.readlines(path)

    return addItems(playlist)


def addItems(playList): 
    import playlist
    items = playlist.parse(playList)

    nItem = len(items)

    for item in items:
        menu  = []
        title = item[0]
        path  = item[1]

        isAudio = title.lower().endswith('.mp3')
        if isAudio:
            title = title.replace('.mp3', '')
            thumb = ICON #'DefaultAudio.png'
        else:
            thumb = ICON #'DefaultFile.png'

        title = utils.unescape(title).strip()

        menu.append((GETTEXT(30047), 'XBMC.RunPlugin(%s?mode=%d&path=%s&label=%s&thumb=%s)' % (sys.argv[0], _COPY_TO_SF_ITEM, urllib.quote_plus(path), urllib.quote_plus(title), urllib.quote_plus(thumb))))

        isPlayable = xbmcgui.getCurrentWindowId() != 10001

        addDir(title, _PLAYLISTITEM, path=path, thumbnail=thumb, isFolder=False, menu=menu, totalItems=nItem, isPlayable=isPlayable)


    return nItem > 0
        

def iPlaylistURLBrowse():
    valid = False
    text  = 'http://'

    while not valid:
        text = getText(GETTEXT(30153), text)

        if not text:
            return False

        if text == 'http://':
            return

        try:    html = quicknet.getURL(text, maxSec=0, tidy=False)
        except: html = ''

        items = parse(html.split('\n'))
        valid = len(items) > 0

        if not valid:
            utils.DialogOK(GETTEXT(30155), text)
        
    name = getText(GETTEXT(30156))

    if not name:
        return False

    if COPY_PLAYLISTS:
        name += '.m3u'
        file  = os.path.join(ROOT, 'PL', name)
        f = sfile.file(file, 'w')
        f.write(html)
        f.close()
        return True

    cmd   = text
    thumb = 'DefaultFile.png'
    addPlaylistToSF(name, cmd, thumb) 

    return True


def iPlaylistBrowse():
    import playlist
    playlist = playlist.getPlaylist()

    if not playlist:
        return False

    folder = os.path.join(ROOT, 'PL')
    sfile.makedirs(folder)

    if COPY_PLAYLISTS:
        try:
            import shutil
            shutil.copy(playlist , folder)
            return True
        except:
            return False
    
    name  = playlist.rsplit(os.sep, 1)[-1].rsplit('.', 1)[0]
    cmd   = playlist
    thumb = 'DefaultMovies.png'

    return addPlaylistToSF(name, cmd, thumb)


def addPlaylistToSF(name, cmd, thumb):
    folder = os.path.join(ROOT, 'PL')
    sfile.makedirs(folder)

    file  = os.path.join(folder, FILENAME)

    cmd = utils.convertToHome(cmd)

    if favourite.findFave(file, cmd)[0]:
        return False

    playlist = [name, thumb, cmd]

    playlists = favourite.getFavourites(file, validate=False)
    playlists.append(playlist)
    favourite.writeFavourites(file, playlists)

    return True


def copyToSF(cmd, title, thumb, playMedia):
    folder = utils.GetFolder(title)
    if not folder:
        return

    copy = ['', '', '']

    copy[0] = title
    copy[1] = thumb

    if playMedia:
        copy[2] = 'PlayMedia("%s")' % path
    else:
        copy[2] = 'ActivateWindow(10025,"%s",return)' % cmd

    file = os.path.join(folder, FILENAME)
    favourite.copyFave(file, copy)


def shortenText(text, length):
    text = utils.fix(text)
    text = text.strip()

    if len(text) <= length:
        return text

    short = ''
    for c in text:
        short += c
        if len(short) == length:
            break

    short += '...'
    return short


def getHistoryItem(menu, keyword, image, fanart, refresh):
    #NOTE the SF@V is to workaround a bug in XBMC where the string is erroneously converted to lowercase when the menu item triggers
 
    refresh = 'true' if refresh else 'false'

    historyItem = None
    if SHOWIHISTORY and not history.contains(keyword):
        label = GETTEXT(30164) % shortenText(keyword, 10)
        historyItem = (label, 'RunPlugin(%s?mode=%d&keyword=%s&image=%s&fanart=%s&refresh=%s)' % (sys.argv[0], _HISTORYADD, urllib.unquote_plus(keyword), urllib.unquote_plus(image.replace('/', 'SF@V')), urllib.unquote_plus(fanart.replace('/', 'SF@V')), refresh))
        menu.append(historyItem)

    return historyItem

            
def superSearch(keyword='', image=SEARCH, fanart=FANART, imdb=''):
    if len(keyword) < 1:
        kb = xbmc.Keyboard(keyword, GETTEXT(30054))
        kb.doModal()
        if kb.isConfirmed():
            keyword = kb.getText()

            if len(keyword) < 1:
                keyword = ISEARCH_EMPTY

            if len(keyword) > -1:
                mode = _SUPERSEARCH
                cmd  = '%s?mode=%d&keyword=%s&image=%s&fanart=%s' % (sys.argv[0], mode, keyword, image, fanart)
                xbmc.executebuiltin('XBMC.Container.Update(%s)' % cmd)
                return False

    if len(keyword) < 1:
        return

    if keyword == ISEARCH_EMPTY:
        keyword = ''

    if not SHOW_FANART:
        fanart = BLANK

    keyword = keyword.split(' - [I]', 1)[0]
    
    if keyword.startswith('tt'): #assume IMDB number
        url  = 'http://m.imdb.com/title/%s/' % keyword
        html = quicknet.getURL(url)

        try:
            keyword = re.compile('<meta property=\'og:title\' content="(.+?)"').search(html).group(1)
            keyword = utils.Clean(keyword)
            keyword = utils.unescape(keyword)
            keyword = utils.fix(keyword)
        except:
            pass
      
    editItem = (GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITTERM, keyword))

    menu = []    
    menu.append(editItem)

    historyItem = getHistoryItem(menu, keyword, image, fanart, True)

    infolabels = {}

    grabber = None
    if METARECOMMEND:
        try:
            from metahandler import metahandlers
            grabber = metahandlers.MetaData()
        except:
            pass

    if grabber and len(imdb) > 0:  
        imdb = imdb.replace('/?', '')      
        infolabels = getMeta(grabber, '', 'movie', year=None, imdb=imdb)
        getMovieMenu(infolabels, menu)
    
    addDir(GETTEXT(30066) % keyword.strip(), _EDITTERM, thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword, infolabels=infolabels)

    #reset menu
    menu = []
    menu.append(editItem)
    if historyItem:
        menu.append(historyItem)

    addSeparatorItem(menu)

    index = 0

    if SHOWIHISTORY and history.exists():
        #reset menu
        menu = []
        menu.append(editItem)

        if historyItem:
            menu.append(historyItem)

        label, index = addPrefixToLabel(index, GETTEXT(30163))

        addDir(label, _HISTORYSHOW, thumbnail=SEARCH, isFolder=True, menu=menu, infolabels={'plot':GETTEXT(30201)})

    if SHOWRECOMMEND and len(keyword) > 0:
        #reset menu
        menu = []
        menu.append(editItem)
        if historyItem:
            menu.append(historyItem)
        getMovieMenu(infolabels, menu)

        label, index = addPrefixToLabel(index, GETTEXT(30088))

        if len(imdb) > 0:            
            addDir(label, _RECOMMEND_IMDB, thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword, imdb=imdb, infolabels={'plot':GETTEXT(30202) % (keyword, imdb.replace('/?', ''))})
        elif RECOMMENDAUTO:
            addDir(label, _RECOMMEND_KEY,  thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword, infolabels={'plot':GETTEXT(30215) % keyword})
        else:
            addDir(label, _RECOMMEND_KEY,  thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword, infolabels={'plot':GETTEXT(30205) % keyword})
        
    keyword = urllib.quote_plus(keyword.replace('&', ''))  

    file  = os.path.join(ROOT, 'S', FILENAME)
    faves = favourite.getFavourites(file, superSearch=True)    

    if len(faves) == 0:
        #try shipped search file
        file = os.path.join(HOME, 'resources', 'search', FILENAME)
        faves = favourite.getFavourites(file) 

    if ALPHA_SORT:
         faves = sorted(faves, key=lambda x: cleanForSort(x))

    for fave in faves:
        label = fave[0]
        thumb = fave[1]
        cmd   = fave[2]

        cmd   = cmd.replace('[%SF%]',  keyword)
        cmd   = cmd.replace('[%SF+%]', keyword.replace('+', '%2b'))

        fan = fanart
        if SHOW_FANART:
            fan = favourite.getFanart(cmd)
            if len(fan) == 0:
                fan = fanart

        menu = []

        menu.append((GETTEXT(30103), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s&name=%s&thumb=%s)' % (sys.argv[0], _EDITSEARCH, urllib.quote_plus(file), urllib.quote_plus(cmd), urllib.quote_plus(label), urllib.quote_plus(thumb))))

        menu.append(editItem)

        if historyItem:
            menu.append(historyItem)

        #special fix for GlobalSearch, use local launcher (globalsearch.py) to bypass keyboard
        cmd = cmd.replace('script.globalsearch', os.path.join(HOME, 'globalsearch.py'))

        infolabel = {'plot':GETTEXT(30206) % (label, urllib.unquote_plus(keyword))}

        label, index = addPrefixToLabel(index, label)

        addDir(label, _ACTIVATESEARCH, cmd=cmd, thumbnail=thumb, isFolder=True, menu=menu, fanart=fan, keyword=keyword, infolabels=infolabel)
    
    return True


def playCommand(originalCmd):
    player.playCommand(originalCmd, contentMode)


def cutCopy(file, cmd, cut=True):
    xbmcgui.Window(10000).setProperty('SF_FILE',   file)
    xbmcgui.Window(10000).setProperty('SF_FOLDER', file.rsplit(os.sep, 1)[0])
    xbmcgui.Window(10000).setProperty('SF_CMD',    cmd)
    xbmcgui.Window(10000).setProperty('SF_TYPE',  'cut' if cut else 'copy')

    return True


def cutCopyFolder(folder, cut=True):
    xbmcgui.Window(10000).setProperty(  'SF_FILE',   folder)
    xbmcgui.Window(10000).setProperty(  'SF_FOLDER', folder.rsplit(os.sep, 1)[0])
    xbmcgui.Window(10000).clearProperty('SF_CMD')
    xbmcgui.Window(10000).setProperty(  'SF_TYPE',  'cutfolder' if cut else 'copyfolder')

    return True


def paste(folder):
    if len(folder) < 1:
        return False

    file = xbmcgui.Window(10000).getProperty('SF_FILE')
    cmd  = xbmcgui.Window(10000).getProperty('SF_CMD')
    type = xbmcgui.Window(10000).getProperty('SF_TYPE').lower()

    dst = os.path.join(folder, FILENAME)

    if type == 'cut':
        return pasteCut(file, cmd, folder)
    else:
        return pasteCopy(file, cmd, folder)

    return True


def pasteFolder(dst):
    if len(dst) < 1:
        return False

    src = xbmcgui.Window(10000).getProperty('SF_FILE')
    cut = xbmcgui.Window(10000).getProperty('SF_TYPE').lower() == 'cutfolder'

    root       = src.rsplit(os.sep, 1)[0]
    folderName = src.rsplit(os.sep, 1)[-1]

    same = (root == dst)

    link = True

    if dst == 'special://profile': #i.e. Kodi favourites
        if cut:
            cut   = False
            line1 = GETTEXT(30187) % DISPLAYNAME
            line2 = GETTEXT(30188) % folderName
            line3 = GETTEXT(30189)
            link  = utils.DialogYesNo(line1, line2, line3, noLabel=GETTEXT(30190), yesLabel=GETTEXT(30186))
            if not link:
                return
    else:
        if cut:
            link = False
        else:  
            line1 = GETTEXT(30183) % folderName
            link  = True if same else utils.DialogYesNo(line1, GETTEXT(30184), noLabel=GETTEXT(30185), yesLabel=GETTEXT(30186))

    if link:
        success = pasteFolderLink(src, dst, folderName)
    else:
        success = pasteFolderCopy(src, dst, folderName)

    if not success:
        line1 = GETTEXT(30191) % folderName
        utils.DialogOK(line1)
        return False

    if cut:
        sfile.rmtree(src)

    return success


def pasteFolderLink(src, dst, folderName):
    thumbnail, fanart = getFolderThumb(src)

    folderConfig = os.path.join(src, FOLDERCFG)
    colour       = getParam('COLOUR', folderConfig)

    if colour:
        folderName = '[COLOR %s]%s[/COLOR]' % (colour, folderName)

    path  = utils.convertToHome(src)

    cmd = '%s?label=%s&mode=%d&path=%s' % (sys.argv[0], folderName, _FOLDER, urllib.quote_plus(path))
    cmd = '"%s"' % cmd  
    cmd = cmd.replace('+', '%20')
    cmd = 'ActivateWindow(%d,%s)' % (getCurrentWindowId(), cmd) 
    cmd = favourite.addFanart(cmd, fanart)

    file = os.path.join(dst, FILENAME)

    if favourite.findFave(file, cmd)[0]:
        return True

    faves = favourite.getFavourites(file, validate=False)
    fave  = [folderName, thumbnail, cmd]

    faves.append(fave)

    favourite.writeFavourites(file, faves)

    return True


def pasteFolderCopy(src, _dst, folderName):
    dst = os.path.join(_dst, folderName)

    index = 0
    while sfile.exists(dst):
        index += 1
        dst    = os.path.join(_dst, GETTEXT(30192) % (folderName, index))

    try:
        sfile.copytree(src, dst)
    except Exception, e: 
        utils.log('Error in pasteFolderCopy: %s' % str(e))
        return False

    return True


def pasteCopy(file, cmd, folder):
    copy, index, nFaves = favourite.findFave(file, cmd)
    if not copy:
        return False

    file = os.path.join(folder, FILENAME)

    #xbmc = os.path.join('special://profile', FILENAME)  
    #if xbmc == file:
    #    return addToXBMC(copy[0], copy[1], copy[2], '')

    return favourite.copyFave(file, copy)


def pasteCut(file, cmd, folder):
    if not pasteCopy(file, cmd, folder):
        return False

    return favourite.removeFave(file, cmd)

    

def activateWindowCommand(cmd):
    player.activateWindowCommand(cmd)


def addArtwork(setting, thumbnail, fanart):
    if setting == 0:
        return ''

    if setting == 1:
        return thumbnail

    if setting == 2:
        return fanart

    return ''
    
    
def addDir(label, mode, index=-1, path = '', cmd = '', thumbnail='', isFolder=True, menu=None, fanart=FANART, keyword='', imdb='', infolabels={}, totalItems=0, isPlayable=False):
    global separator

    u  = sys.argv[0]

    u += '?label='

    try:    
        u += urllib.quote_plus(label)
    except:
        label = utils.fix(label)
        u += urllib.quote_plus(label)

    u += '&mode='  + str(mode)

    if index > -1:
        u += '&index=' + str(index)

    if len(path) > 0:
        u += '&path=' + urllib.quote_plus(path)

    if len(cmd) > 0:
        u += '&cmd=' + urllib.quote_plus(cmd)

    if len(keyword) > 0:
        u += '&keyword=' + urllib.quote_plus(keyword)

    if len(imdb) > 0:
        u += '&imdb=' + urllib.quote_plus(imdb)

    if len(thumbnail) > 0:
        u += '&image=' + urllib.quote_plus(thumbnail)
    if len(fanart) > 0:
        u += '&fanart=' + urllib.quote_plus(fanart)

    if CONTENTMODE:
        u += '&contentMode=true'

    if len(thumbnail) == 0:
        thumbnail = BLANK
       
    label = label.replace('&apos;', '\'')

    liz = xbmcgui.ListItem(label, iconImage='Default', thumbnailImage=thumbnail)

    if isPlayable:
        liz.setProperty('IsPlayable', 'true')

    if infolabels and len(infolabels) > 0:
        liz.setInfo(type='Video', infoLabels=infolabels)

    if len(fanart) == 0:
        fanart = FANART

    if fanart != BLANK and SHOW_FANART:
        liz.setProperty('Fanart_Image', fanart)

    if hasattr(liz, 'setArt'):
        art = {}
        art['landscape'] = addArtwork(ART_LANDSCAPE, thumbnail, fanart)
        art['banner']    = addArtwork(ART_BANNER,    thumbnail, fanart)
        art['poster']    = addArtwork(ART_POSTER,    thumbnail, fanart)
        
        if len(art) > 0:
            liz.setArt(art) 

    #this propery can be accessed in a skin via: $INFO[ListItem.Property(Super_Favourites_Folder)]
    #or in Python via: xbmc.getInfoLabel('ListItem.Property(Super_Favourites_Folder)')
    liz.setProperty('Super_Favourites_Folder', theFolder)

    if not menu:
        menu = []   

    #special case
    if mode == _XBMC:
        menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _THUMBFOLDER, urllib.quote_plus(PROFILE))))

    ignoreFave = False
    if mode == _NEWFOLDER:
        ignoreFave = True
    elif (mode == _EDITTERM) or (mode == _ACTIVATESEARCH):
        ignoreFave = len(keyword) == 0

    addGlobalMenuItem(menu, cmd, ignoreFave, label, thumbnail, u, keyword)

    liz.addContextMenuItems(menu, replaceItems=True)

    if separator:
        addSeparatorItem()
        
    global nItem
    nItem += 1

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder, totalItems=totalItems)


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

theFolder = ''
thepath   = ''

try:    mode = int(params['mode'])
except: mode = _MAIN

try:    file = params['file']
except: file = None

try:    cmd = params['cmd']
except: cmd = None

try:    path = params['path']
except: path = None

try:    name = params['name']
except: name = ''

try:    label = params['label']
except: label = ''

try:    folder = params['folder']
except: folder = ''

try:    content = params['content']
except: content = ''

try:    contentMode = params['contentMode'].lower() == 'true'
except: contentMode = False


doRefresh   = False
doEnd       = True
cacheToDisc = False


#which menu was SF launched from
try:    launchMode = params['content_type']
except: launchMode = ''


contentType = CONTENTTYPE
#convert visible (in settings) string to a string that Kodi recognises
if contentType in CONTENTTYPES:
    contentType = CONTENTTYPES[contentType]
else:
    contentType = ''


if len(content) > 0:   
    mode   = _IGNORE
    folder = content
    try:
        path = xbmc.getInfoLabel('Skin.String(%s.Path)' % folder)

        if len(path) > 0:
            folder = ''
            plugin = re.compile('.+?"(.+?)"').search(path).group(1)

            prams = get_params(plugin)

            try:    folder = prams['folder']
            except: pass

            if len(folder) == 0:
                mode = _FOLDER
                path = PROFILE

    except Exception, e:
        pass

    SHOWNEW     = False
    SHOWXBMC    = False
    SHOWSEP     = False
    CONTENTMODE = True


if len(folder) > 0:
    if mode == _MAIN:    
        mode = _FOLDER

    path = os.path.join(PROFILE, folder)


utils.log('------------------ Launch Parameters ------------------')
utils.log(sys.argv[2])
utils.log(sys.argv)
utils.log('mode        = %d' % mode)
utils.log('cmd         = %s' % cmd)
utils.log('folder      = %s' % folder)
utils.log('params      = %s' % params)
utils.log('launchMode  = %s' % launchMode)
utils.log('contentType = %s' % contentType)
utils.log('viewType    = %s' % VIEWTYPE)
utils.log('-------------------------------------------------------')


if mode == _PLAYMEDIA:
    if not contentMode:
        mode = _IGNORE
        playCommand(cmd)

 
elif mode == _ACTIVATEWINDOW:
    if not contentMode:
        doEnd = False
        mode  = _IGNORE
        playCommand(cmd)


elif mode == _ACTIVATEWINDOW_XBMC:
    doEnd = True
    mode  = _IGNORE

    if PLAY_PLAYLISTS and player.isPlaylist(cmd):        
        playCommand(cmd)

        #Container.Update removes current item from history to stop looping
        update = '%s' % (sys.argv[0])
        update = 'Container.Update(%s,replace)' % update
        xbmc.executebuiltin(update)

        xbmc.executebuiltin('Dialog.Close(busydialog)') #Isengard fix
        xbmc.executebuiltin('ActivateWindow(Home)')
    else:
        script = os.path.join(HOME, 'cmdLauncher.py')
        cmd    = 'AlarmClock(%s,RunScript(%s,%s),%d,True)' % ('changelog', script, cmd, 0)
        xbmc.executebuiltin(cmd)


elif mode == _PLAYLIST:
    import playlist
    playlist.play(cmd)


if mode == _ACTIVATESEARCH:
    doEnd = False
    if FRODO or GOTHAM:
        playCommand(cmd)


elif mode == _XBMC:
    showXBMCFolder()
    xbmc.executebuiltin('Container.Update')


elif mode == _FOLDER:
    thepath   = path
    theFolder = label

    if unlock(thepath):
        if mode != _MAIN:
            addNewFolderItem(thepath)
        parseFolder(thepath)
    else:
        pass
        #Reset to main somehow!!!


elif mode == _REMOVEFOLDER:
    doRefresh = removeFolder(path)


elif mode == _RENAMEFOLDER:
    doRefresh = renameFolder(path)
    

elif mode == _EDITFOLDER:
    if unlock(path):
        doRefresh = editFolder(path, name)


elif mode == _EDITFAVE:
    try:    thumb = params['thumb']
    except: thumb = 'null'
    doRefresh = editFave(file, cmd, name, thumb)


elif mode == _EDITSEARCH:
    try:    thumb = params['thumb']
    except: thumb = 'null'
    doRefresh = editSearch(file, cmd, name, thumb)


elif mode == _NEWFOLDER:
    doRefresh = createNewFolder(path)


elif mode == _CUT:
    doRefresh = cutCopy(file, cmd, cut=True)


elif mode == _COPY:
    doRefresh = cutCopy(file, cmd, cut=False)


elif mode == _PASTE:
    try:    folder = params['paste']
    except: folder
    doRefresh = paste(folder)


elif mode == _CUTFOLDER:
    doRefresh = cutCopyFolder(path, cut=True)


elif mode == _COPYFOLDER:
    doRefresh = cutCopyFolder(path, cut=False)


elif mode == _PASTEFOLDER:
    try:    folder = params['paste']
    except: folder
    doRefresh = pasteFolder(folder)


elif mode == _REMOVEFAVE:
    doRefresh = removeFave(file, cmd)


elif mode == _RENAMEFAVE:
    doRefresh = renameFave(file, cmd)


elif mode == _ADDTOXBMC:
    thumb   = params['thumb']
    keyword = params['keyword']
    addToXBMC(name, thumb, cmd, keyword)


elif mode == _THUMBFAVE:
    doRefresh = thumbFave(file, cmd)


elif mode == _THUMBFOLDER:
    doRefresh = thumbFolder(path)


elif mode == _PLAYBACKMODE:
    doRefresh = changePlaybackMode(file, cmd)


elif mode == _SETTINGS:
    try :
        addonID = params['addon']
        utils.openSettings(addonID)
    except:
        utils.openSettings(ADDONID)
        doRefresh = True


elif mode == _SEPARATOR:
    pass


elif mode == _EXTSEARCH:
    externalSearch()


elif mode == _SUPERSEARCH or mode == _SUPERSEARCHDEF:
    try:    keyword = params['keyword']
    except: keyword = ''

    try:    imdb = params['imdb']
    except: imdb = ''

    try:    image = params['image']
    except: image = BLANK

    try:    fanart = params['fanart']
    except: fanart = BLANK

    cacheToDisc = False #len(keyword) > 0 and mode == _SUPERSEARCH
    doEnd       = len(keyword) > 0 and mode == _SUPERSEARCH

    if mode == _SUPERSEARCH:
        superSearch(keyword, image, fanart, imdb)

    xbmc.sleep(250)

    if len(imdb) > 0:
        contentType = 'movies'


elif mode == _EDITTERM:
    try:    keyword = params['keyword']
    except: keyword = ''
    editSearchTerm(keyword)
    cacheToDisc=True
    xbmc.sleep(250)
    doEnd = False


elif mode == _SECURE:
    doRefresh = addLock(path, name)


elif mode == _UNSECURE:
    doRefresh = removeLock(path, name)

elif mode == _IMPORT:
    import importer
    importer.doImport()
    #doRefresh = True


elif mode == _RECOMMEND_KEY or mode == _RECOMMEND_KEY_A:
    try:    keyword = params['keyword']
    except: keyword = ''

    cacheToDisc = True
    doEnd       = True
    contentType = 'movies'

    if mode == _RECOMMEND_KEY:
        recommendKey(keyword, RECOMMENDAUTO)
    else:
        recommendKey(keyword, False)        


elif mode == _RECOMMEND_IMDB:
    try:    imdb = params['imdb']
    except: imdb = ''

    try:    keyword = params['keyword']
    except: keyword = ''

    try:
        if ADDON.getSetting('CACHERECOMMEND') != 'true':
            callback = params['callback']

        cacheToDisc = True
        doEnd       = True
        contentType = 'movies'

        recommendIMDB(imdb, keyword)

    except Exception, e:
        winID = xbmcgui.getCurrentWindowId()
        cmd   = '%s?mode=%d&keyword=%s&imdb=%s&callback=%s' % (sys.argv[0], _RECOMMEND_IMDB, urllib.quote_plus(keyword), urllib.quote_plus(imdb), 'callback')
        xbmc.executebuiltin('Container.Refresh(%s)' % cmd)

        cacheToDisc = False
        doEnd       = False


elif mode == _PLAYTRAILER:
    import yt    
    if not yt.PlayVideo(path):
        utils.DialogOK(GETTEXT(30092))


elif mode == _IPLAY:
    iPlay()


elif mode == _PLAYLISTFILE:
    iPlaylistFile(path)


elif mode == _PLAYLISTITEM:
    try:    image = params['image']
    except: image = BLANK

    iPlaylistItem(path, label, image)


elif mode == _PLAYLISTBROWSE:
    doRefresh = iPlaylistBrowse()


elif mode == _DELETEPLAYLIST:
    doRefresh = iPlaylistDelete(path)


elif mode == _COPY_TO_SF:
    doRefresh = False
    thumb     = params['thumb']
    copyToSF(path, label, thumb, playMedia=False)


elif mode == _COPY_TO_SF_ITEM:
    doRefresh = False
    thumb     = params['thumb']
    copyToSF(path, label, thumb, playMedia=True)


elif mode == _URLPLAYLIST:
    doRefresh = iPlaylistURLBrowse()


elif mode == _HISTORYSHOW:
    doRefresh = iHistoryBrowse()


elif mode == _HISTORYADD:
    try:    keyword = params['keyword']
    except: keyword = ''

    try:    image = params['image']
    except: image = BLANK

    try:    fanart = params['fanart']
    except: fanart = FANART

    image  = image.replace('SF@V', '/')
    fanart = fanart.replace('SF@V', '/')

    doRefresh = iHistoryAdd(keyword, image, fanart)

elif mode == _HISTORYREMOVE:
    doRefresh = iHistoryRemove(name)


elif mode == _MANUAL:
    doRefresh = manualAdd(path)


elif mode == _VIEWTYPE:
    doRefresh = setViewType()

elif mode == _IEXPLORE:
    cacheToDisc = True
    iExplore(path)


elif mode == _PLAY_FILE:
    playFile(path)


elif mode == _PLAY_FOLDER:
    playFolder(path)


elif mode == _PLAY_SUPER_FOLDER_EXT:
    playSuperFolder(path, id=-1)
    #now remove this item from history to prevent looping
    cmd = 'XBMC.Container.Update(%s?mode=%d,replace)' % (sys.argv[0], _MAIN)
    xbmc.executebuiltin(cmd)
    doEnd = True


elif mode == _PLAY_SUPER_FOLDER:
    playSuperFolder(path, id=int(sys.argv[1]))
    
    
elif mode == _MAIN:
    main()


else:
    #do nothing
    nItem = 1


#make sure at least 1 line is showing to allow context menu to be displayed
if nItem < 1:
    if mode == _IPLAY:
        menu = []

        #browse
        cmd  = '%s?mode=%d' % (sys.argv[0], _PLAYLISTBROWSE)
        menu.append((GETTEXT(30148), 'XBMC.Container.Update(%s)' % cmd))

        #browse for URL
        cmd = '%s?mode=%d' % (sys.argv[0], _URLPLAYLIST)
        menu.append((GETTEXT(30153), 'XBMC.Container.Update(%s)' % cmd))

        addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False, menu=menu)
    else:
        addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False)


if doRefresh:
    refresh()

handle = int(sys.argv[1])

if doEnd:
    if len(contentType) > 0:
        xbmcplugin.setContent(handle, contentType)

    if handle > -1:
        xbmcplugin.endOfDirectory(handle, cacheToDisc=cacheToDisc)

    if VIEWTYPE > 0:        
        xbmc.executebuiltin('Container.SetViewMode(%d)' % VIEWTYPE)


if mode == _PLAYMEDIA:
    xbmc.sleep(250)
    playCommand(cmd)


elif mode == _ACTIVATESEARCH:
    if FRODO or GOTHAM:
        pass
    else:
        xbmc.sleep(250)
        doEnd = False
        playCommand(cmd)


elif mode == _ACTIVATEWINDOW:
    xbmc.sleep(250)
    playCommand(cmd)


elif mode == _SUPERSEARCHDEF:
    xbmc.sleep(250)
    import search
    fave = search.getDefaultSearch()
    if fave:
        cmd = fave[2]
        cmd = cmd.replace('[%SF%]', keyword)
        if cmd.startswith('RunScript'):
            #special fix for GlobalSearch, use local launcher (globalsearch.py) to bypass keyboard
            cmd = cmd.replace('script.globalsearch', os.path.join(HOME, 'globalsearch.py'))
            cmd = 'AlarmClock(%s,%s,%d,True)' % ('Default iSearch', cmd, 0)
            xbmc.executebuiltin(cmd) 
        else:
            cmd = re.compile('"(.+?)"').search(cmd).group(1)
            xbmc.executebuiltin('XBMC.Container.Update(%s)' % cmd)