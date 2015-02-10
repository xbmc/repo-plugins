#
#       Copyright (C) 2014
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
import re
import urllib
import glob
import shutil
import re
import json


import favourite
import quicknet
import utils

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

FILENAME      = utils.FILENAME
FOLDERCFG     = utils.FOLDERCFG


# -----Addon Modes ----- #
_IGNORE           = -10
_MAIN             = -2
_SUPERSEARCH      = 0
_SUPERSEARCHDEF   = 10
_EXTSEARCH        = 25 #used to trigger new Super Search from outside of addon
_SEPARATOR        = 50
_SETTINGS         = 100
_ADDTOXBMC        = 200
_XBMC             = 300
_FOLDER           = 400
_NEWFOLDER        = 500
_PLAYMEDIA        = 600
_ACTIVATEWINDOW   = 650
_ACTIVATESEARCH   = 675
_REMOVEFOLDER     = 700
_REMOVEFAVE       = 800
_RENAMEFOLDER     = 900
_RENAMEFAVE       = 1000
_MOVE             = 1100
_COPY             = 1200
_UP               = 1300
_DOWN             = 1400
_THUMBFAVE        = 1500
_THUMBFOLDER      = 1600
_PLAYBACKMODE     = 1700
_EDITTERM         = 1900
_EDITFOLDER       = 2000
_EDITFAVE         = 2100
_SECURE           = 2200
_UNSECURE         = 2300
_PLAYLIST         = 2400
_COLOURFOLDER     = 2500
_COLOURFAVE       = 2600
_RECOMMEND_KEY    = 2700
_RECOMMEND_IMDB   = 2800
_PLAYTRAILER      = 2900
_EDITSEARCH       = 3000
_IMPORT           = 3100


# --------------------- Addon Settings --------------------- #
SHOWNEW        = ADDON.getSetting('SHOWNEW')           == 'true'
SHOWXBMC       = ADDON.getSetting('SHOWXBMC')          == 'true'
SHOWXBMCROOT   = ADDON.getSetting('SHOWXBMCROOT')      == 'true'
SHOWIMPORT     = ADDON.getSetting('SHOWIMPORT')        == 'true'
SHOWIMPORTROOT = ADDON.getSetting('SHOWIMPORTROOT')    == 'true'
SHOWSEP        = ADDON.getSetting('SHOWSEP')           == 'true'
SHOWSS         = ADDON.getSetting('SHOWSS')            == 'true'
SHOW_FANART    = ADDON.getSetting('SHOW_FANART')       == 'true'
SHOWRECOMMEND  = ADDON.getSetting('SHOWRECOMMEND')     == 'true'
PLAY_PLAYLISTS = ADDON.getSetting('PLAY_PLAYLISTS')    == 'true'
METARECOMMEND  = ADDON.getSetting('METARECOMMEND')     == 'true'
INHERIT        = ADDON.getSetting('INHERIT')           == 'true'
REMOTE         = ADDON.getSetting('REMOTE')            == 'true'
DEFAULT_FANART = ADDON.getSetting('DEFAULT_FANART')

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
# ---------------------------------------------------------- #


utils.CheckVersion()


global nItem
nItem = 0

global separator
separator = False


def clean(text):
    if not text:
        return None

    text = re.sub('[:\\\\/*?\<>|"]+', '', text)
    text = text.strip()
    if len(text) < 1:
        return  None

    return text


def main():
    addSuperSearch()

    profile = xbmc.translatePath(PROFILE)

    addNewFolderItem(profile)

    parseFolder(profile)


def addSuperSearch():
    global separator

    if not SHOWSS:
        return

    separator = False        
    addDir(GETTEXT(30054), _SUPERSEARCH, thumbnail=SEARCH, isFolder=True)
    separator = True


def addNewFolderItem(path):
    global separator
    if SHOWNEW:
        separator = False
        addDir(GETTEXT(30004), _NEWFOLDER, path=path, thumbnail=ICON, isFolder=False)
        separator = True


def addSeparatorItem(menu=None):
    global separator
    separator = False        
    if SHOWSEP:
        addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False, menu=menu)


def addGlobalMenuItem(menu, item):
    #check if we are in the XBMC favourites folder
    if mode != _XBMC:
        cmd = '%s?mode=%d' % (sys.argv[0], _XBMC)
        menu.append((GETTEXT(30040), 'XBMC.Container.Update(%s)' % cmd))

        if mode != _SUPERSEARCH:
            path = thepath
            if path == '':
                path = PROFILE
            menu.append((GETTEXT(30004), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _NEWFOLDER, urllib.quote_plus(path))))

    menu.append((GETTEXT(30005), 'XBMC.RunPlugin(%s?mode=%d)' % (sys.argv[0], _SETTINGS)))

    try:
        addon = re.compile('"(.+?)"').search(item).group(1)
        addon = addon.replace('plugin://', '')
        addon = addon.replace('/', '')
        addon = addon.split('?', 1)[0]

        if addon == utils.ADDONID:
            return
        
        if xbmc.getCondVisibility('System.HasAddon(%s)' % addon) == 0:
            return
        
        menu.append((GETTEXT(30094) % xbmcaddon.Addon(addon).getAddonInfo('name'), 'XBMC.RunPlugin(%s?mode=%d&addon=%s)' % (sys.argv[0], _SETTINGS, urllib.quote_plus(addon))))
    except:
        pass


def addFavouriteMenuItem(menu, name, thumb, cmd):
    if cmd.endswith('&mode=0'):
        return

    if len(name) < 1:
        return

    if mode == _XBMC:
        return

    menu.append((GETTEXT(30006), 'XBMC.RunPlugin(%s?mode=%d&name=%s&thumb=%s&cmd=%s)' % (sys.argv[0], _ADDTOXBMC, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(cmd))))


def getCurrentWindowId():
    winID = xbmcgui.getCurrentWindowId()
    tries = 10

    while winID == 10000 and tries > 0:
        xbmc.sleep(100)
        tries -= 1
        winID = xbmcgui.getCurrentWindowId()

    return winID if winID != 10000 else 10025


def addToXBMC(name, thumb, cmd):
    p = get_params(cmd.replace('?', '&'))
    try: 
        mode = int(p['mode'])
        if mode == _FOLDER:
            label = urllib.unquote_plus(p['label'])
            path  = urllib.unquote_plus(p['path'])
            path  = favourite.convertToHome(path)
            cmd   = '%s?label=%s&mode=%d&path=%s' % (sys.argv[0], label, _FOLDER, urllib.quote_plus(path))
    except:
        pass

    cmd = '"%s"' % cmd   
    
    folder   = '&mode=%d' % _FOLDER
    search   = '&mode=%d' % _SUPERSEARCH
    edit     = '&mode=%d' % _EDITTERM

    if (folder in cmd) or (search in cmd) or (edit in cmd):
        cmd = cmd.replace('+', '%20')
        cmd = 'ActivateWindow(%d,%s,return)' % (getCurrentWindowId(), cmd)
    else:
        cmd = 'PlayMedia(%s)' % cmd

    if (search in cmd) and ('keyword' not in cmd):
        replace = '%s&keyword=%s' % (search, ISEARCH_EMPTY)
        cmd = cmd.replace(search, replace)
        if not cmd.lower().endswith(',return)'):
            cmd = cmd[:-1] + ',return)'
   
    fave = [name, thumb, cmd]

    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)

    #if it is already in there don't add again
    if favourite.findFave(file, cmd)[0]:
        return False    

    faves = favourite.getFavourites(file, validate=False)

    faves.append(fave)

    favourite.writeFavourites(file, faves)

    return True


def refresh():
    xbmc.executebuiltin('Container.Refresh')


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


def unlocked(path):
    folderConfig = os.path.join(path, FOLDERCFG)
    lock = getParam('LOCK', folderConfig)
    if not lock:
        return True

    import cache
    if cache.exists(path):
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
    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)
    parseFile(file)


def parseFile(file):
    global separator
    faves = favourite.getFavourites(file)

    text = GETTEXT(30099) if mode == _XBMC else GETTEXT(30068)

    for fave in faves:
        label  = fave[0]
        thumb  = fave[1]
        cmd    = fave[2]
        fanart = favourite.getFanart(cmd)
      
        menu  = []
        menu.append((text, 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s&name=%s&thumb=%s)' % (sys.argv[0], _EDITFAVE, urllib.quote_plus(file), urllib.quote_plus(cmd), urllib.quote_plus(label), urllib.quote_plus(thumb))))

        if isPlaylist(cmd) and (not PLAY_PLAYLISTS):
            menu.append((GETTEXT(30084), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _PLAYLIST, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        if 'playmedia(' in cmd.lower():
            addDir(label, _PLAYMEDIA, cmd=cmd, thumbnail=thumb, isFolder=False, menu=menu, fanart=fanart)
        else:
            addDir(label, _ACTIVATEWINDOW, cmd=cmd, thumbnail=thumb, isFolder=True, menu=menu, fanart=fanart)

    separator = len(faves) > 0


def getFolderThumb(path, isXBMC=False):
    cfg    = os.path.join(path, FOLDERCFG)
    thumb  = getParam('ICON', cfg)
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


def parseFolder(folder):
    global separator

    show = SHOWXBMC
    if (mode != _MAIN and SHOWXBMCROOT):
        show = False

    if show:
        separator = False

        thumbnail, fanart = getFolderThumb(xbmc.translatePath(PROFILE), True)

        addDir(GETTEXT(30040), _XBMC, thumbnail=thumbnail, isFolder=True, fanart=fanart)
        separator = True


    show = SHOWIMPORT and LOCATION
    if (mode != _MAIN and SHOWIMPORTROOT):
        show = False

    if show:
        separator = False

        thumbnail = 'DefaultFile.png'
        fanart    = ''

        addDir(GETTEXT(30125), _IMPORT, thumbnail=thumbnail, isFolder=False, fanart=fanart)
        separator = True

    try:    current, dirs, files = os.walk(folder).next()
    except: return
   
    dirs = sorted(dirs, key=str.lower)

    for dir in dirs:
        path = os.path.join(current, dir)

        folderConfig = os.path.join(path, FOLDERCFG)
        lock   = getParam('LOCK',   folderConfig)
        colour = getParam('COLOUR', folderConfig)

        menu = []
        menu.append((GETTEXT(30067), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _EDITFOLDER, urllib.quote_plus(path), urllib.quote_plus(dir))))

        if lock:
            menu.append((GETTEXT(30077), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _UNSECURE, urllib.quote_plus(path), urllib.quote_plus(dir))))
        else:
            menu.append((GETTEXT(30076), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _SECURE,   urllib.quote_plus(path), urllib.quote_plus(dir))))

        thumbnail, fanart = getFolderThumb(path)

        if colour:
            dir = '[COLOR %s]%s[/COLOR]' % (colour, dir)

        addDir(dir, _FOLDER, path=path, thumbnail=thumbnail, isFolder=True, menu=menu, fanart=fanart)

    if len(dirs) > 0:
        separator = True

    file = os.path.join(folder, FILENAME)
    parseFile(file)


def getParam(param, file):
    try:
        config = []
        param  = param.upper() + '='
        f      = open(file, 'r')
        config = f.readlines()
        f.close()
    except:
        return None

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
        f      = open(file, 'r')
        config = f.readlines()
        f.close()
    except:
        pass
        
    copy = []
    for line in config:
        line = line.strip()
        if (len(line) > 0) and (not line.startswith(param)):
            copy.append(line)

    if len(value) > 0:
        copy.append(param + value)

    f = open(file, 'w')

    for line in copy:
        f.write(line)
        f.write('\n')
    f.close()


def getColour():
    filename = os.path.join(HOME, 'resources', 'colours', 'Color.xml')

    if not os.path.exists(filename):
        return None

    menu = [[GETTEXT(30087), 'SF_RESET']]

    f = open(filename, 'r')
    for line in f:
        if 'name' in line:
            name = line.split('"')[1]            
            menu.append(['[COLOR %s]%s[/COLOR]' % (name, name), name])

    if len(menu) < 2:
        return None

    import menus
    option = menus.selectMenu(GETTEXT(30086), menu)
                 
    if option < 0:
        return None

    return option


def getText(title, text='', hidden=False):
    kb = xbmc.Keyboard(text.strip(), title)
    kb.setHiddenInput(hidden)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    text = kb.getText().strip()

    if len(text) < 1:
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

    if os.path.exists(icon):
        f = open(icon, 'r')
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


def fanartFolder(path):
    image = getImage()

    if not image:
        return False

    image = favourite.convertToHome(image)

    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('FANART', image, folderConfig)
    return True


def thumbFolder(path):
    image = getImage()

    if not image:
        return False

    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('ICON', image, folderConfig)
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

    fave[2] = favourite.removeFanart(cmd)

    favourite.updateFave(file, fave)
    return True


def fanartFave(file, cmd):
    image = getImage()

    if not image:
        return False

    fave, index, nFaves = favourite.findFave(file, cmd)

    fave[2] = favourite.addFanart(fave[2], image)

    return favourite.updateFave(file, fave)


def thumbFave(file, cmd):
    image = getImage()

    if not image:
        return False

    fave, index, nFaves = favourite.findFave(file, cmd)
    fave[1] = image

    return favourite.updateFave(file, fave)


def getFolder(title):
    return utils.GetFolder(title)


def createNewFolder(current):
    text = clean(getText(GETTEXT(30013)))
    if not text:
        return False

    folder = os.path.join(current, text)
    if os.path.exists(folder):
        utils.DialogOK('', GETTEXT(30014) % text)
        return False

    os.makedirs(xbmc.translatePath(folder))
    return True


def changePlaybackMode(file, cmd):
    copy = []
    faves = favourite.getFavourites(file)
    for fave in faves:
        if favourite.equals(fave[2], cmd):
            if cmd.startswith('PlayMedia'):
                try:    winID = re.compile('sf_win_id=(.+?)_').search(cmd).group(1)
                except: winID = '10025'
                cmd = cmd.replace('PlayMedia(', 'ActivateWindow(%s,' % winID)
            elif cmd.startswith('ActivateWindow'):
                cmd = 'PlayMedia(' + cmd.split(',', 1)[-1]
            fave[2] = cmd
        copy.append(fave)

    favourite.writeFavourites(file, copy)
    return True


def editFolder(path, name):
    cfg       = os.path.join(path, FOLDERCFG)
    thumb     = getParam('ICON',   cfg)
    fanart    = getParam('FANART', cfg)
    hasThumb  = thumb  and len(thumb)  > 0
    hasFanart = fanart and len(fanart) > 0

    REMOVE       = 0
    RENAME       = 1
    CHOOSETHUMB  = 2
    CHOOSEFANART = 3
    REMOVETHUMB  = 4
    REMOVEFANART = 5
    COLOUR       = 6

    options = []
    options.append([GETTEXT(30011), REMOVE])
    options.append([GETTEXT(30012), RENAME])
    options.append([GETTEXT(30043), CHOOSETHUMB])
    options.append([GETTEXT(30107), CHOOSEFANART])

    if hasThumb:
        options.append([GETTEXT(30097), REMOVETHUMB])

    if hasFanart:
        options.append([GETTEXT(30108), REMOVEFANART])

    options.append([GETTEXT(30085), COLOUR])

    import menus
    option = menus.selectMenu(name, options)

    if option == REMOVE:
        return removeFolder(path)

    if option == RENAME:
        return renameFolder(path)

    if option == CHOOSETHUMB:
        return thumbFolder(path)

    if option == CHOOSEFANART:
        return fanartFolder(path)

    if option == REMOVETHUMB:
        return removeThumbFolder(path)

    if option == REMOVEFANART:
        return removeFanartFolder(path)

    if option == COLOUR:
        return colourFolder(path)

    return False
    


def editFave(file, cmd, name, thumb):
    fanart    = favourite.getFanart(cmd)
    hasThumb  = len(thumb)  > 0
    hasFanart = len(fanart) > 0
    hasMode   = 'sf_win_id=' in cmd

    UP           = 0
    DOWN         = 1
    COPY         = 2
    MOVE         = 3
    REMOVE       = 4
    RENAME       = 5
    CHOOSETHUMB  = 6
    CHOOSEFANART = 7
    REMOVETHUMB  = 8
    REMOVEFANART = 9
    COLOUR       = 10
    PLAYBACKMODE = 11

    options = []
    options.append([GETTEXT(30041), UP])
    options.append([GETTEXT(30042), DOWN])
    options.append([GETTEXT(30007), COPY])
    options.append([GETTEXT(30008), MOVE])
    options.append([GETTEXT(30009), REMOVE])
    options.append([GETTEXT(30010), RENAME])
    options.append([GETTEXT(30043), CHOOSETHUMB])
    options.append([GETTEXT(30107), CHOOSEFANART])

    if hasThumb:
        options.append([GETTEXT(30097), REMOVETHUMB])

    if hasFanart:
        options.append([GETTEXT(30108), REMOVEFANART])

    options.append([GETTEXT(30085), COLOUR])

    if hasMode:
        options.append([GETTEXT(30052), PLAYBACKMODE])

    import menus
    option = menus.selectMenu(name, options)

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

    if option == CHOOSETHUMB:
        return thumbFave(file, cmd)

    if option == CHOOSEFANART:
        return fanartFave(file, cmd)

    if option == REMOVETHUMB:
        return removeThumbFave(file, cmd)

    if option == REMOVEFANART:
        return removeFanartFave(file, cmd)

    if option == COLOUR:
        return colourFave(file, cmd)

    if option == PLAYBACKMODE:
        return changePlaybackMode(file, cmd)

    return False


def editSearch(file, cmd, name, thumb):
    fanart    = favourite.getFanart(cmd)
    hasThumb  = len(thumb) > 0
    hasFanart = len(fanart) > 0

    UP           = 0
    DOWN         = 1
    RENAME       = 2
    CHOOSETHUMB  = 3
    CHOOSEFANART = 4
    REMOVETHUMB  = 5
    REMOVEFANART = 6
    COLOUR       = 7

    options = []
    options.append([GETTEXT(30041), UP])
    options.append([GETTEXT(30042), DOWN])
    options.append([GETTEXT(30010), RENAME])
    options.append([GETTEXT(30043), CHOOSETHUMB])
    options.append([GETTEXT(30107), CHOOSEFANART])

    if hasThumb:
        options.append([GETTEXT(30097), REMOVETHUMB])

    if hasFanart:
        options.append([GETTEXT(30108), REMOVEFANART])

    options.append([GETTEXT(30085), COLOUR])

    import menus
    option = menus.selectMenu(name, options)

    if option == UP:
        return favourite.shiftFave(file, cmd, up=True)

    if option == DOWN:
        return favourite.shiftFave(file, cmd, up=False)

    if option == RENAME:
        return renameFave(file, cmd)

    if option == CHOOSETHUMB:
        return thumbFave(file, cmd)

    if option == CHOOSEFANART:
        return fanartFave(file, cmd)

    if option == REMOVETHUMB:
        return removeThumbFave(file, cmd)

    if option == REMOVEFANART:
        return removeFanartFave(file, cmd)

    if option == COLOUR:
        return colourFave(file, cmd)

    return False


def renameFolder(path):
    label = path.rsplit(os.sep, 1)[-1]

    text = clean(getText(GETTEXT(30015) % label, label))

    if not text:
        return False

    root = path.rsplit(os.sep, 1)[0]
    newName = os.path.join(root, text)
    os.rename(path, newName)
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
    if not utils.DialogYesNo(GETTEXT(30016) % label, GETTEXT(30017), GETTEXT(30018)):
        return False

    try:    shutil.rmtree(path)
    except: pass
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

    newName = getText(GETTEXT(30021), text=fave[0])

    if not newName:
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

    if 'trailer_url' in infolabels and len(infolabels['trailer_url']) > 0:   
        menu.append((GETTEXT(30091), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _PLAYTRAILER,  urllib.quote_plus(infolabels['trailer_url']))))          

    return menu


def recommendIMDB(imdb, keyword):
    from metahandler import metahandlers
    grabber = metahandlers.MetaData()

    url  = 'http://imdb.com/title/%s' % imdb
    html = quicknet.getURL(url, maxSec=86400, agent='Firefox')

    items = re.compile('<div class="rec-title">.+?<a href="/title/(.+?)/?ref_=tt_rec_tt" ><b>(.+?)</b>').findall(html)

    if len(items) == 0:
        return recommendKey(keyword)

    infolabels = {}

    for item in items:
        imdb      = item[0]
        name      = item[1]

        thumbnail = BLANK
        fanart    = FANART

        if METARECOMMEND:
            #thumbnail,  fanart = getTVDB(imdb)
            infolabels = getMeta(grabber, '', 'movie', year=None, imdb=imdb)
            thumbnail  = infolabels['cover_url']
            fanart     = infolabels['fanart']  

        addDir(name, _SUPERSEARCH, thumbnail=thumbnail, isFolder=True, menu=getMovieMenu(infolabels), fanart=fanart, keyword=name, imdb=imdb, infolabels=infolabels, totalItems=len(items))

    
def recommendKey(keyword):
    from metahandler import metahandlers
    grabber = metahandlers.MetaData()

    url  = 'http://m.imdb.com/find?q=%s' % keyword.replace(' ', '+') #use mobile site as less data
    html = quicknet.getURL(url, maxSec=86400, agent='Apple-iPhone/')

    items = re.compile('<div class="title">.+?<a href="/title/(.+?)/">(.+?)</a>(.+?)</div>').findall(html)

    infolabels = {}

    for item in items:
        imdb  = item[0]
        name  = item[1]
        if 'video game' in item[2].lower():
            continue

        label = name + ' ' + item[2].strip()

        thumbnail = BLANK
        fanart    = FANART

        if METARECOMMEND:
            #thumbnail,  fanart = getTVDB(imdb)
            infolabels = getMeta(grabber, name, 'movie', year=None, imdb=imdb)
            thumbnail  = infolabels['cover_url']
            fanart     = infolabels['fanart']  

        addDir(label, _SUPERSEARCH, thumbnail=thumbnail, isFolder=True, menu=getMovieMenu(infolabels), fanart=fanart, keyword=name, imdb=imdb, infolabels=infolabels, totalItems=len(items))
    

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

    
def superSearch(keyword='', image=BLANK, fanart=FANART, imdb=''):
    if len(keyword) < 1:
        kb = xbmc.Keyboard(keyword, GETTEXT(30054))
        kb.doModal()
        if kb.isConfirmed():
            keyword = kb.getText()

            if len(keyword) > 0:
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

    menu = []
    menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITTERM, keyword)))

    infolabels = {}


    if METARECOMMEND and len(imdb) > 0:
        from metahandler import metahandlers
        grabber = metahandlers.MetaData()
        infolabels = getMeta(grabber, '', 'movie', year=None, imdb=imdb)
        getMovieMenu(infolabels, menu)

    addDir(GETTEXT(30066) % keyword.strip(), _EDITTERM, thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword, infolabels=infolabels)

    #reset menu, since adddir call will have added to it
    menu = []
    menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITTERM, keyword)))
    addSeparatorItem(menu)

    if SHOWRECOMMEND:
        menu = []
        menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITTERM, keyword)))
        getMovieMenu(infolabels, menu)

        if len(imdb) > 0:
            addDir(GETTEXT(30088), _RECOMMEND_IMDB, thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword, imdb=imdb, infolabels=infolabels)
        else:
            addDir(GETTEXT(30088), _RECOMMEND_KEY,  thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword)
        
    keyword = urllib.quote_plus(keyword.replace('&', ''))  

    file  = os.path.join(xbmc.translatePath(ROOT), 'Search', FILENAME)
    faves = favourite.getFavourites(file, superSearch=True)    

    if len(faves) == 0:
        #try shipped search file
        file = os.path.join(xbmc.translatePath(HOME), 'resources', 'Search', FILENAME)
        faves = favourite.getFavourites(file) 

    for fave in faves:
        label = fave[0]
        thumb = fave[1]
        cmd   = fave[2].replace('[%SF%]', keyword)

        fan = fanart
        if SHOW_FANART:
            fan = favourite.getFanart(cmd)
            if len(fan) == 0:
                fan = fanart

        menu = []
        menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITTERM, keyword)))
        menu.append((GETTEXT(30103), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s&name=%s&thumb=%s)' % (sys.argv[0], _EDITSEARCH, urllib.quote_plus(file), urllib.quote_plus(cmd), urllib.quote_plus(label), urllib.quote_plus(thumb))))

        #special fix for GlobalSearch, use local launcher (globalsearch.py) to bypass keyboard
        cmd = cmd.replace('script.globalsearch', os.path.join(HOME, 'globalsearch.py'))

        addDir(label, _ACTIVATESEARCH, cmd=cmd, thumbnail=thumb, isFolder=True, menu=menu, fanart=fan)
    
    return True


def playCommand(cmd):
    try:
        cmd = favourite.tidy(cmd)  
        
        #if a 'Super Favourite' favourite just do it
        if ADDONID in cmd:
             return xbmc.executebuiltin(cmd)

        #if in contentMode just do it
        if contentMode:
            xbmc.executebuiltin('ActivateWindow(Home)') #some items don't play nicely if launched from wrong window
            if cmd.lower().startswith('activatewindow'):
                cmd = cmd.replace('")', '",return)') #just in case return is missing                
            return xbmc.executebuiltin(cmd)

        if cmd.startswith('RunScript'):    
            #workaround bug in Frodo that can cause lock-up
            #when running a script favourite
            if FRODO:
                xbmc.executebuiltin('ActivateWindow(Home)')
    
        if isPlaylist(cmd):
            if PLAY_PLAYLISTS:
                return playPlaylist(cmd)      

        if 'ActivateWindow' in cmd:
            return activateWindowCommand(cmd)        

        xbmc.executebuiltin(cmd)


    except Exception, e:
        utils.log('Error in playCommand')
        utils.log('Command: %s' % cmd)
        utils.log('Error:   %s' % str(e))        


def isPlaylist(cmd):
    return cmd.lower().endswith('.m3u")')


def playPlaylist(cmd):
    if cmd.lower().startswith('activatewindow'):
        playlist = cmd.split(',', 1)
        playlist = playlist[-1][:-1]
        cmd      = 'PlayMedia(%s)' % playlist

    xbmc.executebuiltin(cmd)


def activateWindowCommandReturn(cmd):
    if not cmd.lower().endswith(',return)'):
        cmd = cmd[:-1] + ',return)'
    xbmc.executebuiltin(cmd)


def activateWindowCommand(cmd):
    cmds = cmd.split(',', 1)

    plugin   = None
    activate = None

    if len(cmds) == 1:
        activate = cmds[0]
    else:
        activate = cmds[0]+',return)'
        plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())

    if id not in activate:
        xbmc.executebuiltin(activate)

    if plugin:    
        xbmc.executebuiltin('Container.Update(%s)' % plugin)

    
def addDir(label, mode, index=-1, path = '', cmd = '', thumbnail='', isFolder=True, menu=None, fanart=FANART, keyword='', imdb='', infolabels={}, totalItems=0):
    global separator

    u  = sys.argv[0]

    u += '?label=' + urllib.quote_plus(label)
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

    if mode == _SUPERSEARCH:
        if len(thumbnail) > 0:
            u += '&image=' + urllib.quote_plus(thumbnail)
        if len(fanart) > 0:
            u += '&fanart=' + urllib.quote_plus(fanart)

    if CONTENTMODE:
        u += '&contentMode=true'

    if len(thumbnail) == 0:
        thumbnail = BLANK
       
    label = label.replace('&apos;', '\'')

    liz = xbmcgui.ListItem(urllib.unquote_plus(label), iconImage=thumbnail, thumbnailImage=thumbnail)

    if len(infolabels) > 0:
        liz.setInfo(type='Video', infoLabels=infolabels)

    if len(fanart) == 0:
        fanart = FANART

    if fanart != BLANK and SHOW_FANART:
        liz.setProperty('Fanart_Image', fanart)     

    #this propery can be accessed in a skin via: $INFO[ListItem.Property(Super_Favourites_Folder)]
    #or in Python via: xbmc.getInfoLabel('ListItem.Property(Super_Favourites_Folder)')
    liz.setProperty('Super_Favourites_Folder', theFolder)

    if not menu:
        menu = []   

    #special case
    if mode == _XBMC:
        profile = xbmc.translatePath(PROFILE)
        menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _THUMBFOLDER,  urllib.quote_plus(profile))))

    addFavouriteMenuItem(menu, label, thumbnail, u)

    addGlobalMenuItem(menu, cmd)

    liz.addContextMenuItems(menu, replaceItems=True)

    if separator:
        addSeparatorItem()
        
    global nItem
    nItem += 1

    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=isFolder, totalItems=totalItems)

   
def get_params(p):
    param=[]
    paramstring=p
    if len(paramstring)>=2:
        params=p
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


params = get_params(sys.argv[2])

theFolder = ''
thepath   = ''

try:    mode = int(params['mode'])
except: mode = _MAIN

try:    file = urllib.unquote_plus(params['file'])
except: file = None

try:    cmd = urllib.unquote_plus(params['cmd'])
except: cmd = None

try:    path = urllib.unquote_plus(params['path'])
except: path = None

try:    name = urllib.unquote_plus(params['name'])
except: name = ''

try:    label = urllib.unquote_plus(params['label'])
except: label = ''

try:    folder = urllib.unquote_plus(params['folder'])
except: folder = ''

try:    content = urllib.unquote_plus(params['content'])
except: content = ''

try:    contentMode = params['contentMode'].lower() == 'true'
except: contentMode = False



doRefresh   = False
doEnd       = True
cacheToDisc = False
contentType = ''


if len(content) > 0:   
    mode   = _IGNORE
    folder = content
    try:
        path = xbmc.getInfoLabel('Skin.String(%s.Path)' % folder)

        if len(path) > 0:
            folder = ''
            import re
            plugin = re.compile('.+?"(.+?)"').search(path).group(1)

            prams = get_params(plugin)

            try:    folder = urllib.unquote_plus(prams['folder'])
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
    mode = _FOLDER
    path = os.path.join(PROFILE, folder)


utils.log(sys.argv[2])
utils.log(sys.argv)
utils.log('Mode = %d' % mode)
utils.log('cmd  = %s' % cmd)



if mode == _PLAYMEDIA:
    if not contentMode:
        mode = _IGNORE
        playCommand(cmd)
 
elif mode == _ACTIVATEWINDOW:
    if not contentMode:
        doEnd = False
        mode  = _IGNORE
        playCommand(cmd)


elif mode == _PLAYLIST:
    playPlaylist(cmd)


elif mode == _ACTIVATESEARCH:
    doEnd = False
    playCommand(cmd)


elif mode == _XBMC:
    showXBMCFolder()
    xbmc.executebuiltin('Container.Update')


elif mode == _FOLDER:
    thepath   = xbmc.translatePath(path)
    theFolder = label

    if unlocked(thepath):
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
    if unlocked(path):
        doRefresh = editFolder(path, name)


elif mode == _EDITFAVE:
    try:    thumb = urllib.unquote_plus(params['thumb'])
    except: thumb = 'null'
    doRefresh = editFave(file, cmd, name, thumb)


elif mode == _EDITSEARCH:
    try:    thumb = urllib.unquote_plus(params['thumb'])
    except: thumb = 'null'
    doRefresh = editSearch(file, cmd, name, thumb)


elif mode == _NEWFOLDER:
    doRefresh = createNewFolder(path)


elif mode == _MOVE:
    doRefresh = favourite.moveFave(file, cmd)


elif mode == _COPY:
    doRefresh = copyFave(file, cmd)


elif mode == _UP:
    doRefresh = favourite.shiftFave(file, cmd, up=True)


elif mode == _DOWN:
    doRefresh = favourite.shiftFave(file, cmd, up=False)


elif mode == _REMOVEFAVE:
    doRefresh = removeFave(file, cmd)


elif mode == _RENAMEFAVE:
    doRefresh = renameFave(file, cmd)


elif mode == _ADDTOXBMC:
    thumb = urllib.unquote_plus(params['thumb'])
    addToXBMC(name, thumb, cmd)


elif mode == _THUMBFAVE:
    doRefresh = thumbFave(file, cmd)


elif mode == _THUMBFOLDER:
    doRefresh = thumbFolder(path)


elif mode == _PLAYBACKMODE:
    doRefresh = changePlaybackMode(file, cmd)

    
elif mode == _SETTINGS:
    try :
        addon = urllib.unquote_plus(params['addon'])
        xbmcaddon.Addon(addon).openSettings()
    except:
        ADDON.openSettings()
        refresh()


elif mode == _SEPARATOR:
    pass


elif mode == _EXTSEARCH:
    externalSearch()


elif mode == _SUPERSEARCH or mode == _SUPERSEARCHDEF:
    try:    keyword = urllib.unquote_plus(params['keyword'])
    except: keyword = ''

    try:    imdb = urllib.unquote_plus(params['imdb'])
    except: imdb = ''

    try:    image = urllib.unquote_plus(params['image'])
    except: image = BLANK

    try:    fanart = urllib.unquote_plus(params['fanart'])
    except: fanart = BLANK

    cacheToDisc = len(keyword) > 0 and mode == _SUPERSEARCH
    doEnd       = len(keyword) > 0 and mode == _SUPERSEARCH

    if mode == _SUPERSEARCH:
        superSearch(keyword, image, fanart, imdb)

    xbmc.sleep(250)

    if len(imdb) > 0:
        contentType = 'movies'

elif mode == _EDITTERM:
    try:    keyword = urllib.unquote_plus(params['keyword'])
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


elif mode == _RECOMMEND_KEY:
    try:    keyword = urllib.unquote_plus(params['keyword'])
    except: keyword = ''

    cacheToDisc = True
    doEnd       = True
    contentType = 'movies'

    recommendKey(keyword)


elif mode == _RECOMMEND_IMDB:
    try:    imdb = urllib.unquote_plus(params['imdb'])
    except: imdb = ''

    try:    keyword = urllib.unquote_plus(params['keyword'])
    except: keyword = ''

    try:
        if ADDON.getSetting('CACHERECOMMEND') != 'true':
            callback = urllib.unquote_plus(params['callback'])

        cacheToDisc = True
        doEnd       = True
        contentType = 'movies'

        recommendIMDB(imdb, keyword)

    except:
        winID = xbmcgui.getCurrentWindowId()
        cmd   = '%s?mode=%d&keyword=%s&imdb=%s&callback=%s' % (sys.argv[0], _RECOMMEND_IMDB, urllib.quote_plus(keyword), urllib.quote_plus(imdb), 'callback')
        xbmc.executebuiltin('Container.Refresh(%s)' % cmd)

        cacheToDisc = False
        doEnd       = False


elif mode == _PLAYTRAILER:
    import yt    
    if not yt.PlayVideo(path):
        utils.DialogOK(GETTEXT(30092))
        
elif mode == _MAIN:
    main()

else:
    #do nothing
    nItem = 1


#make sure at least 1 line is showing to allow context menu to be displayed
if nItem < 1:
    addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False)


if doRefresh:
    refresh()


if doEnd:
    if len(contentType) > 0:
        xbmcplugin.setContent(int(sys.argv[1]), contentType)
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cacheToDisc)


xbmc.sleep(250)


if mode == _PLAYMEDIA:
    playCommand(cmd)

elif mode == _ACTIVATEWINDOW:
    playCommand(cmd)

elif mode == _SUPERSEARCHDEF:
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


#xbmc.executebuiltin('RunScript(script.tlbb.systemsettings,type=setlangauge)')