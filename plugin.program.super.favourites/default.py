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

import favourite
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
_SUPERSEARCH    = 0
_EXTSEARCH      = 25 #used to trigger new Super Search from outside of addon
_SEPARATOR      = 50
_SETTINGS       = 100
_ADDTOXBMC      = 200
_XBMC           = 300
_FOLDER         = 400
_NEWFOLDER      = 500
_PLAYMEDIA      = 600
_ACTIVATEWINDOW = 650
_ACTIVATESEARCH = 675
_REMOVEFOLDER   = 700
_REMOVEFAVE     = 800
_RENAMEFOLDER   = 900
_RENAMEFAVE     = 1000
_MOVE           = 1100
_COPY           = 1200
_UP             = 1300
_DOWN           = 1400
_THUMBFAVE      = 1500
_THUMBFOLDER    = 1600
_PLAYBACKMODE   = 1700
_EDITSEARCH     = 1900
_EDITFOLDER     = 2000
_EDITFAVE       = 2100
_SECURE         = 2200
_UNSECURE       = 2300
_PLAYLIST       = 2400


# ----- Addon Settings ----- #
SHOWNEW        = ADDON.getSetting('SHOWNEW')        == 'true'
SHOWXBMC       = ADDON.getSetting('SHOWXBMC')       == 'true'
SHOWSEP        = ADDON.getSetting('SHOWSEP')        == 'true'
SHOWSS         = ADDON.getSetting('SHOWSS')         == 'true'
SHOWSS_FANART  = ADDON.getSetting('SHOWSS_FANART')  == 'true'
SHOWRECOMMEND  = ADDON.getSetting('SHOWRECOMMEND')  == 'true'
SHOWXBMCROOT   = ADDON.getSetting('SHOWXBMCROOT')   == 'true'
PLAY_PLAYLISTS = ADDON.getSetting('PLAY_PLAYLISTS') == 'true'



global nItem
nItem = 0

global separator
separator = False


def log(text):
    print('%s V%s : %s' % (TITLE, VERSION, text))
    xbmc.log('%s V%s : %s' % (TITLE, VERSION, text), xbmc.LOGDEBUG)


def clean(text):
    if not text:
        return None

    text = re.sub('[:\\\\/*?\<>|"]+', '', text)
    text = text.strip()
    if len(text) < 1:
        return  None

    return text


def main():
    utils.CheckVersion()

    addSuperSearch()

    profile = xbmc.translatePath(PROFILE)

    addNewFolderItem(profile)

    parseFolder(profile)


def addSuperSearch():
    global separator

    if not SHOWSS:
        return

    utils.verifySuperSearch()

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


def addGlobalMenuItem(menu):
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


def addFavouriteMenuItem(menu, name, thumb, cmd):
    if cmd.endswith('&mode=0'):
        return

    if len(name) < 1:
        return

    if mode == _XBMC:
        return

    menu.append((GETTEXT(30006), 'XBMC.RunPlugin(%s?mode=%d&name=%s&thumb=%s&cmd=%s)' % (sys.argv[0], _ADDTOXBMC, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(cmd))))


def addToXBMC(name, thumb, cmd):
    cmd = '"%s"' % cmd

    folder = '&mode=%d' % _FOLDER
    search = '&mode=%d' % _SUPERSEARCH
    edit   = '&mode=%d' % _EDITSEARCH

    if (folder in cmd) or (search in cmd) or (edit in cmd):
        cmd = cmd.replace('+', '%20')
        cmd = 'ActivateWindow(%d,%s)' % (xbmcgui.getCurrentWindowId(), cmd)
    else:
        cmd = 'PlayMedia(%s)' % cmd

    fave = [name, thumb, cmd]

    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)

    #if it is already in there don't add again
    if findFave(file, cmd)[0]:
        return False

    faves = favourite.getFavourites(file)
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
    md5    = utils.generateMD5(unlock)
    match  = md5 == lock

    if not match:
        return ''

    return md5


def showXBMCFolder():
    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)
    parseFile(file)


def parseFile(file):
    global separator
    faves = favourite.getFavourites(file)        

    for fave in faves:
        label = fave[0]
        thumb = fave[1]
        cmd   = fave[2]

        menu  = []
        menu.append((GETTEXT(30068), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s&name=%s)' % (sys.argv[0], _EDITFAVE, urllib.quote_plus(file), urllib.quote_plus(cmd), urllib.quote_plus(label))))

        if isPlaylist(cmd) and (not PLAY_PLAYLISTS):
            menu.append((GETTEXT(30084), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _PLAYLIST, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        #menu.append((GETTEXT(30041), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _UP,   urllib.quote_plus(file), urllib.quote_plus(cmd))))
        #menu.append((GETTEXT(30042), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _DOWN, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        #menu.append((GETTEXT(30007), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _COPY, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        #menu.append((GETTEXT(30008), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _MOVE,         urllib.quote_plus(file), urllib.quote_plus(cmd))))
        #menu.append((GETTEXT(30009), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _REMOVEFAVE,   urllib.quote_plus(file), urllib.quote_plus(cmd))))
        #menu.append((GETTEXT(30010), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _RENAMEFAVE,   urllib.quote_plus(file), urllib.quote_plus(cmd))))
        #menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _THUMBFAVE,    urllib.quote_plus(file), urllib.quote_plus(cmd))))

        #if 'sf_win_id=' in cmd:
        #    menu.append((GETTEXT(30052), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _PLAYBACKMODE, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        if 'playmedia(' in cmd.lower():
            addDir(label, _PLAYMEDIA, cmd=cmd, thumbnail=thumb, isFolder=False, menu=menu)
        else:
            addDir(label, _ACTIVATEWINDOW, cmd=cmd, thumbnail=thumb, isFolder=True, menu=menu)

    separator = len(faves) > 0


def parseFolder(folder):
    global separator

    show = SHOWXBMC
    if (mode != -2 and SHOWXBMCROOT):
        show = False

    if show:
        separator = False

        profile      = xbmc.translatePath(PROFILE)
        folderConfig = os.path.join(profile, FOLDERCFG)
        thumbnail    = getParam('ICON', folderConfig)
        if not thumbnail:
            thumbnail = 'DefaultFolder.png'

        addDir(GETTEXT(30040), _XBMC, thumbnail=thumbnail, isFolder=True)
        separator = True

    try:    current, dirs, files = os.walk(folder).next()
    except: return

    for dir in dirs:
        path = os.path.join(current, dir)

        folderConfig = os.path.join(path, FOLDERCFG)
        lock = getParam('LOCK', folderConfig)

        menu = []
        menu.append((GETTEXT(30067), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _EDITFOLDER, urllib.quote_plus(path), urllib.quote_plus(dir))))

        if lock:
            menu.append((GETTEXT(30077), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _UNSECURE, urllib.quote_plus(path), urllib.quote_plus(dir))))
        else:
            menu.append((GETTEXT(30076), 'XBMC.RunPlugin(%s?mode=%d&path=%s&name=%s)' % (sys.argv[0], _SECURE,   urllib.quote_plus(path), urllib.quote_plus(dir))))

        #menu.append((GETTEXT(30011), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _REMOVEFOLDER, urllib.quote_plus(path))))
        #menu.append((GETTEXT(30012), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _RENAMEFOLDER, urllib.quote_plus(path))))
        #menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _THUMBFOLDER,  urllib.quote_plus(path))))

        folderConfig = os.path.join(path, FOLDERCFG)
        thumbnail = getParam('ICON', folderConfig)
        if not thumbnail:
            thumbnail = ICON

        addDir(dir, _FOLDER, path=path, thumbnail=thumbnail, isFolder=True, menu=menu)

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


def getText(title, text='', hidden=False):
    kb = xbmc.Keyboard(text, title)
    kb.setHiddenInput(hidden)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    text = kb.getText().strip()

    if len(text) < 1:
        return None

    return text


def getImage():
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

    image = xbmcgui.Dialog().browse(2,GETTEXT(30044), 'files', '', False, False, os.sep)
    if image and len(image) > 0:
        return image

    return ''


def thumbFolder(path):
    image = getImage()

    if not image:
        return False

    #special case
    if image == 'Super Favourite.png':
        image = os.path.join(HOME, 'icon.png')

    folderConfig = os.path.join(path, FOLDERCFG)
    setParam('ICON', image, folderConfig)
    return True


def thumbFave(file, cmd):
    image = getImage()

    if not image:
        return False

    fave, index, nFaves = findFave(file, cmd)
    fave[1] = image

    updateFave(file, fave)
    return True


def updateFave(file, update):
    cmd = update[2]
    fave, index, nFaves = findFave(file, cmd)

    removeFave(file, cmd)

    return insertFave(file, update, index)


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

    os.mkdir(xbmc.translatePath(folder))
    return True


def changePlaybackMode(file, cmd):
    copy = []
    faves = favourite.getFavourites(file)
    for fave in faves:
        if fave[2] == cmd:
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
    options = []
    options.append(GETTEXT(30011)) #remove
    options.append(GETTEXT(30012)) #rename
    options.append(GETTEXT(30043)) #thumb

    option = xbmcgui.Dialog().select(name, options)
    if option < 0:
        return False

    if option == 0:
        return removeFolder(path)

    if option == 1:
        return renameFolder(path)

    if option == 2:
        return thumbFolder(path)

    return False


def editFave(file, cmd, name):
    options = []
    options.append(GETTEXT(30041)) #up
    options.append(GETTEXT(30042)) #down
    options.append(GETTEXT(30007)) #copy
    options.append(GETTEXT(30008)) #move
    options.append(GETTEXT(30009)) #remove
    options.append(GETTEXT(30010)) #rename
    options.append(GETTEXT(30043)) #thumb
    if 'sf_win_id=' in cmd:
        options.append(GETTEXT(30052)) #playback mode

    option = xbmcgui.Dialog().select(name, options)
    if option < 0:
        return False

    if option == 0:
        return shiftFave(file, cmd, up=True)

    if option == 1:
        return shiftFave(file, cmd, up=False)

    if option == 2:
        return copyFave(file, cmd)

    if option == 3:
        return moveFave(file, cmd)

    if option == 4:
        return removeFave(file, cmd)

    if option == 5:
        return renameFave(file, cmd)

    if option == 6:
        return thumbFave(file, cmd)

    if option == 7:
        return changePlaybackMode(file, cmd)

    return False


def renameFolder(path):
    label = path.rsplit(os.sep, 1)[-1]
    text  = clean(getText(GETTEXT(30015) % label, label))
    if not text:
        return False

    root = path.rsplit(os.sep, 1)[0]
    newName = os.path.join(root, text)
    os.rename(path, newName)
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

    return removeFave(file, cmd)


def findFave(file, cmd):
    faves = favourite.getFavourites(file)
    index = -1
    for fave in faves:
        index += 1
        if fave[2] == cmd:
            return fave, index, len(faves)
    return None, -1, 0


def shiftFave(file, cmd, up):
    fave, index, nFaves = findFave(file, cmd)
    max = nFaves - 1
    if up:
        index -= 1
        if index < 0:
            index = max
    else: #down
        index += 1
        if index > max:
            index = 0

    removeFave(file, cmd)
    return insertFave(file, fave, index)


def insertFave(file, newFave, index):
    copy = []
    faves = favourite.getFavourites(file)
    for fave in faves:
        if len(copy) == index:
            copy.append(newFave)
        copy.append(fave)

    if index >= len(copy):
        copy.append(newFave)

    favourite.writeFavourites(file, copy)

    return True


def copyFave(file, cmd, move=False):
    copy, index, nFaves = findFave(file, cmd)
    if not copy:
        return

    text = GETTEXT(30020) if move else GETTEXT(30019)

    folder = getFolder(text)
    if not folder:
        return False
  
    file  = os.path.join(folder, FILENAME)
    faves = favourite.getFavourites(file)

    #if it is already in there don't add again
    for fave in faves:
        if fave[2] == cmd:
            return False

    faves.append(copy)
    favourite.writeFavourites(file, faves)

    return True

def removeFave(file, cmd):
    copy = []
    faves = favourite.getFavourites(file)
    for fave in faves:
        if fave[2] != cmd:
            copy.append(fave)

    if len(copy) == len(faves):
        return False

    favourite.writeFavourites(file, copy)

    return True


def renameFave(file, cmd):
    copy = []
    faves = favourite.getFavourites(file)
    for fave in faves:
        if fave[2] == cmd:
            text = getText(GETTEXT(30021), text=fave[0])
            if not text:
                return
            fave[0] = text
        copy.append(fave)

    favourite.writeFavourites(file, copy)

    return True



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

    
def superSearch(keyword='', image=BLANK, fanart=BLANK):
    #if len(keyword) < 1:
    #    keyword = xbmcgui.Window(10000).getProperty('SF_KEYWORD')

    if len(keyword) < 1:
        kb = xbmc.Keyboard(keyword, GETTEXT(30054))
        kb.doModal()
        if kb.isConfirmed():
            keyword = kb.getText()
            #xbmcgui.Window(10000).setProperty('SF_KEYWORD', keyword)

            if len(keyword) > 0:
                cmd = '%s?mode=%d&keyword=%s&image=%s&fanart=%s' % (sys.argv[0], _SUPERSEARCH, keyword, image, fanart)
                xbmc.executebuiltin('XBMC.Container.Update(%s)' % cmd)
                return

    if len(keyword) < 1:
        return

    if not SHOWSS_FANART:
        fanart = BLANK
        
    file  = os.path.join(xbmc.translatePath(ROOT), 'Search', FILENAME)

    faves = favourite.getFavourites(file)

    menu = []
    menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITSEARCH, keyword)))

    addDir(GETTEXT(30066) % keyword, _EDITSEARCH, thumbnail=image, isFolder=True, menu=menu, fanart=fanart, keyword=keyword)

    #reset menu, since adddir call will have added to it
    menu = []
    menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITSEARCH, keyword)))
    addSeparatorItem(menu)

    keyword = urllib.quote_plus(keyword.replace('&', ''))

    for fave in faves:
        label = fave[0]
        thumb = fave[1]
        cmd   = fave[2].replace('[%SF%]', keyword)

        if 'plugin' in cmd:
            addPluginSearch(label, thumb, cmd, keyword, fanart)

        if 'RunScript' in cmd:
            addScriptSearch(label, thumb, cmd, keyword, fanart)


def addPluginSearch(label, thumb, cmd, keyword, fanart):
    try:
        plugin = re.compile('plugin://(.+?)/').search(cmd).group(1)
        #simple check to ensure it is available, will throw if not installed
        xbmcaddon.Addon(plugin)

        menu = []
        menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITSEARCH, keyword)))

        addDir(label, _ACTIVATESEARCH, cmd=cmd, thumbnail=thumb, isFolder=True, menu=menu, fanart=fanart)

    except:
       pass


def addScriptSearch(label, thumb, cmd, keyword, fanart):
    try:
        script = cmd.split('(', 1)[1].split(',', 1)[0].replace(')', '').replace('"', '')
        #simple check to ensure it is available, will throw if not installed
        xbmcaddon.Addon(script)

        #special fix for GlobalSearch, use local launcher (globalsearch.py) to bypass keyboard
        cmd = cmd.replace('script.globalsearch', os.path.join(HOME, 'globalsearch.py'))

        menu = []
        menu.append((GETTEXT(30057), 'XBMC.Container.Update(%s?mode=%d&keyword=%s)' % (sys.argv[0], _EDITSEARCH, keyword)))

        addDir(label, _ACTIVATESEARCH, cmd=cmd, thumbnail=thumb, isFolder=True, menu=menu, fanart=fanart)

    except:
       pass


def playCommand(cmd):
    try:
        cmd = cmd.replace('&quot;', '')
        cmd = cmd.replace('&amp;', '&')

        #if a 'Super Favourite' favourite just do it
        if ADDONID in cmd:
            return xbmc.executebuiltin(cmd)

        if isPlaylist(cmd):
            if PLAY_PLAYLISTS:
                return playPlaylist(cmd)

        if 'ActivateWindow' in cmd:
            return activateWindowCommand(cmd)

        xbmc.executebuiltin(cmd)
    except:
        pass


def isPlaylist(cmd):
    return cmd.lower().endswith('.m3u")')


def playPlaylist(cmd):
    if cmd.lower().startswith('activatewindow'):
        playlist = cmd.split(',', 1)
        playlist = playlist[-1][:-1]
        cmd      = 'PlayMedia(%s)' % playlist

    xbmc.executebuiltin(cmd)


def activateWindowCommand(cmd):
    cmds = cmd.split(',', 1)

    activate = cmds[0]+',return)'
    plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())

    if id not in activate:
        xbmc.executebuiltin(activate)
    
    xbmc.executebuiltin('Container.Update(%s)' % plugin)

    
def addDir(label, mode, index=-1, path = '', cmd = '', thumbnail='', isFolder=True, menu=None, fanart=None, keyword=''):
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

    label = label.replace('&apos;', '\'')

    liz = xbmcgui.ListItem(urllib.unquote_plus(label), iconImage=thumbnail, thumbnailImage=thumbnail)

    if fanart:
        liz.setProperty('Fanart_Image', fanart)

    if not menu:
        menu = []

    #special case
    if mode == _XBMC:
        profile = xbmc.translatePath(PROFILE)
        menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _THUMBFOLDER,  urllib.quote_plus(profile))))

    addFavouriteMenuItem(menu, label, thumbnail, u)

    addGlobalMenuItem(menu)
    liz.addContextMenuItems(menu, replaceItems=True)

    if separator:
        addSeparatorItem()
        
    global nItem
    nItem += 1
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
thepath  = ''

try:    mode = int(params['mode'])
except: mode = -2

try:    file = urllib.unquote_plus(params['file'])
except: file = None

try:    cmd = urllib.unquote_plus(params['cmd'])
except: cmd = None

try:    path = urllib.unquote_plus(params['path'])
except: path = None

try:    name = urllib.unquote_plus(params['name'])
except: name = ''


doRefresh   = False
doEnd       = True
cacheToDisc = False


log('Started')
log(sys.argv[2])
log(sys.argv)


if mode == _PLAYMEDIA:
    playCommand(cmd)


elif mode == _ACTIVATEWINDOW:
    doEnd = False
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
    thepath = urllib.unquote_plus(params['path'])
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
    doRefresh = editFolder(path, name)


elif mode == _EDITFAVE:
    doRefresh = editFave(file, cmd, name)


elif mode == _NEWFOLDER:
    doRefresh = createNewFolder(path)


elif mode == _MOVE:
    doRefresh = moveFave(file, cmd)


elif mode == _COPY:
    doRefresh = copyFave(file, cmd)


elif mode == _UP:
    doRefresh = shiftFave(file, cmd, up=True)


elif mode == _DOWN:
    doRefresh = shiftFave(file, cmd, up=False)


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
    ADDON.openSettings()
    refresh()


elif mode == _SEPARATOR:
    pass


elif mode == _EXTSEARCH:
    externalSearch()


elif mode == _SUPERSEARCH:
    try:    keyword = urllib.unquote_plus(params['keyword'])
    except: keyword = ''

    cacheToDisc = len(keyword) > 0
    doEnd       = len(keyword) > 0

    try:    image = urllib.unquote_plus(params['image'])
    except: image = BLANK

    try:    fanart = urllib.unquote_plus(params['fanart'])
    except: fanart = BLANK

    superSearch(keyword, image, fanart)


elif mode == _EDITSEARCH:
    keyword = urllib.unquote_plus(params['keyword'])
    editSearchTerm(keyword)
    cacheToDisc=True
    xbmc.sleep(100)
    doEnd = False


elif mode == _SECURE:
    doRefresh = addLock(path, name)


elif mode == _UNSECURE:
    doRefresh = removeLock(path, name)

    
else:
    #xbmcgui.Window(10000).clearProperty('SF_KEYWORD')
    main()


#make sure at least 1 line is showing to allow context menu to be displayed
if nItem < 1:
    addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False)


if doRefresh:
    refresh()
    

if doEnd:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=cacheToDisc)