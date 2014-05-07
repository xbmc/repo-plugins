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
PROFILE  = utils.PROFILE
VERSION  = utils.VERSION
ICON     = utils.ICON

FANART   = utils.FANART
BLANK    = utils.BLANK
GETTEXT  = utils.GETTEXT
TITLE    = utils.TITLE
FRODO    = utils.FRODO
GOTHAM   = utils.GOTHAM

FILENAME  = utils.FILENAME
FOLDERCFG = utils.FOLDERCFG


_SEPARATOR    = 0
_SETTINGS     = 100
_ADDTOXBMC    = 200
_XBMC         = 300
_FOLDER       = 400
_NEWFOLDER    = 500
_COMMAND      = 600
_REMOVEFOLDER = 700
_REMOVEFAVE   = 800
_RENAMEFOLDER = 900
_RENAMEFAVE   = 1000
_MOVE         = 1100
_COPY         = 1200
_UP           = 1300
_DOWN         = 1400
_THUMBFAVE    = 1500
_THUMBFOLDER  = 1600
_PLAYBACKMODE = 1700


SHOWNEW  = ADDON.getSetting('SHOWNEW')  == 'true'
SHOWXBMC = ADDON.getSetting('SHOWXBMC') == 'true'
SHOWSEP  = ADDON.getSetting('SHOWSEP')  == 'true'


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

    profile = xbmc.translatePath(PROFILE)

    addNewFolderItem(profile)

    parseFolder(profile)


def addNewFolderItem(path):
    if SHOWNEW:
        addDir(GETTEXT(30004), _NEWFOLDER, path=path, thumbnail=ICON, isFolder=False) 
        addSeparatorItem()


def addSeparatorItem():
    if SHOWSEP:  
        addDir('', _SEPARATOR, thumbnail=BLANK, isFolder=False)


def addGlobalMenuItem(menu):
    #check if we are in the XBMC favourites folder
    if mode != _XBMC:
        cmd = '%s?mode=%d' % (sys.argv[0], _XBMC)
        menu.append((GETTEXT(30040), 'XBMC.Container.Update(%s)' % cmd))

        path = thepath
        if path == '':
            path = PROFILE
        menu.append((GETTEXT(30004), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _NEWFOLDER, urllib.quote_plus(path))))

    menu.append((GETTEXT(30005), 'XBMC.RunPlugin(%s?mode=%d)' % (sys.argv[0], _SETTINGS)))


def addFavouriteMenuItem(menu, name, thumb, cmd):
    if cmd.endswith('&mode=0'):
        return

    menu.append((GETTEXT(30006), 'XBMC.RunPlugin(%s?mode=%d&name=%s&thumb=%s&cmd=%s)' % (sys.argv[0], _ADDTOXBMC, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(cmd))))


def addToXBMC(name, thumb, cmd):
    cmd = '"%s"' % cmd

    folder = '&mode=%d&' % _FOLDER

    if folder in cmd:
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


def showXBMCFolder():
    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)
    parseFile(file, isXBMC=True)


def parseFile(file, reqSep=False, isXBMC=False):
    faves = favourite.getFavourites(file)

    if reqSep and len(faves) > 0:
        addSeparatorItem()
        

    for fave in faves:
        label = fave[0]
        thumb = fave[1]
        cmd   = fave[2]

        menu  = []

        include = True #originally set to (not isXBMC) to prevent altering XBMC favourites themselves

        if include:
            menu.append((GETTEXT(30041), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _UP,   urllib.quote_plus(file), urllib.quote_plus(cmd))))
            menu.append((GETTEXT(30042), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _DOWN, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        menu.append((GETTEXT(30007), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _COPY,       urllib.quote_plus(file), urllib.quote_plus(cmd))))

        if include:
            menu.append((GETTEXT(30008), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _MOVE,         urllib.quote_plus(file), urllib.quote_plus(cmd))))
            menu.append((GETTEXT(30009), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _REMOVEFAVE,   urllib.quote_plus(file), urllib.quote_plus(cmd))))
            menu.append((GETTEXT(30010), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _RENAMEFAVE,   urllib.quote_plus(file), urllib.quote_plus(cmd))))
            menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _THUMBFAVE,    urllib.quote_plus(file), urllib.quote_plus(cmd))))

            if 'sf_win_id=' in cmd:
                menu.append((GETTEXT(30052), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _PLAYBACKMODE, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        addDir(label, _COMMAND, cmd=cmd, thumbnail=thumb, isFolder=False, menu=menu)

    return len(faves) > 0


def parseFolder(folder):
    if SHOWXBMC:        
        addDir(GETTEXT(30040), _XBMC, thumbnail='DefaultFolder.png', isFolder=True)

    try:    current, dirs, files = os.walk(folder).next()
    except: return

    nmrDirs = len(dirs)
    reqSep  = nmrDirs > 0

    if SHOWXBMC:
        if reqSep:
            addSeparatorItem()
        else:
            reqSep = True

    for dir in dirs:
        path = os.path.join(current, dir)
        menu = []
        menu.append((GETTEXT(30011), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _REMOVEFOLDER, urllib.quote_plus(path))))
        menu.append((GETTEXT(30012), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _RENAMEFOLDER, urllib.quote_plus(path))))
        menu.append((GETTEXT(30043), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _THUMBFOLDER,  urllib.quote_plus(path))))

        folderConfig = os.path.join(path, FOLDERCFG)
        thumbnail = getParam('ICON', folderConfig)
        if not thumbnail:
            thumbnail = ICON

        addDir(dir,  _FOLDER, path=path, thumbnail=thumbnail, isFolder=True, menu=menu)

    file     = os.path.join(folder, FILENAME)
    nmrFaves = parseFile(file, reqSep=reqSep)

    if nmrDirs == 0 and nmrFaves == 0 and not SHOWNEW:
        if not (SHOWXBMC and mode == -1):
            addSeparatorItem() 


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

    copy.append(param + value)

    f = open(file, 'w')

    for line in copy:
        f.write(line)
        f.write('\n')
    f.close()


def getText(title, text=''):
    kb = xbmc.Keyboard(text, title)
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

    image = xbmcgui.Dialog().browse(2,GETTEXT(30044), 'files')
    if image and len(image) > 0:
        return image

    return ''


def thumbFolder(path, cmd):
    image = getImage()

    if not image:
        return False

    #special case
    if image == 'Super Favourite.png':
        image = ''

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


def playCommand(cmd):
    try:
        cmd = cmd.replace('&quot;', '')
        cmd = cmd.replace('&amp;', '&')

        #if a 'Super Favourite' favourite just do it
        #if ADDONID in cmd:
        #    return xbmc.executebuiltin(cmd)

        if 'ActivateWindow' in cmd:
            return activateWindowCommand(cmd)

        #workaround bug in Frodo that can cause lock-up
        #when running a script favourite
        #if FRODO and 'RunScript' in cmd:
        #    xbmc.executebuiltin('ActivateWindow(Home)')

        xbmc.executebuiltin(cmd)
    except:
        pass


def activateWindowCommand(cmd):
    cmds = cmd.split(',', 1)

    activate = cmds[0]+',return)'
    plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())
    if id not in activate:
        xbmc.executebuiltin(activate)
    
    xbmc.executebuiltin('Container.Update(%s)' % plugin)

    
def addDir(label, mode, index=-1, path = '', cmd = '', thumbnail='', isFolder=True, menu=None):
    u  = sys.argv[0]

    u += '?label=' + urllib.quote_plus(label)
    u += '&mode='  + str(mode)

    if index > -1:
        u += '&index=' + str(index)

    if len(path) > 0:
        u += '&path=' + urllib.quote_plus(path)

    if len(cmd) > 0:
        u += '&cmd=' + urllib.quote_plus(cmd)

    label = label.replace('&apos;', '\'')

    liz = xbmcgui.ListItem(urllib.unquote_plus(label), iconImage=thumbnail, thumbnailImage=thumbnail)

    if not menu:
        menu = []

    if mode != _XBMC:
        addFavouriteMenuItem(menu, label, thumbnail, u)

    addGlobalMenuItem(menu)
    liz.addContextMenuItems(menu, replaceItems=True)

    #infoLabels = {'container.folderName' : 'FANART'}
    #liz.setInfo(type='default-view', infoLabels=infoLabels)

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

try:    cmd    = urllib.unquote_plus(params['cmd'])
except: cmd = None

try:    path = urllib.unquote_plus(params['path'])
except: path = None

doRefresh = False

if mode == _XBMC:
    showXBMCFolder()
    xbmc.executebuiltin('Container.Update')


elif mode == _COMMAND:
    playCommand(cmd)


elif mode == _FOLDER:
    thepath = urllib.unquote_plus(params['path'])
    addNewFolderItem(thepath)
    parseFolder(thepath)


elif mode == _REMOVEFOLDER:
    doRefresh = removeFolder(path)


elif mode == _RENAMEFOLDER:
    doRefresh = renameFolder(path)


elif mode == _NEWFOLDER:
    doRefresh = createNewFolder(path)


elif mode == _MOVE:
    doRefresh = moveFave(file, cmd)


elif mode == _COPY:
    if copyFave(file, cmd):
        refresh()

elif mode == _UP:
    doRefresh = shiftFave(file, cmd, up=True)


elif mode == _DOWN:
    doRefresh = shiftFave(file, cmd, up=False)


elif mode == _REMOVEFAVE:
    doRefresh = removeFave(file, cmd)


elif mode == _RENAMEFAVE:
    doRefresh = renameFave(file, cmd)


elif mode == _ADDTOXBMC:
    name  = urllib.unquote_plus(params['name'])
    thumb = urllib.unquote_plus(params['thumb'])
    addToXBMC(name, thumb, cmd)


elif mode == _THUMBFAVE:
    doRefresh = thumbFave(file, cmd)


elif mode == _THUMBFOLDER:
    doRefresh = thumbFolder(path, cmd)


elif mode == _PLAYBACKMODE:
    doRefresh = changePlaybackMode(file, cmd)

    
elif mode == _SETTINGS:
    ADDON.openSettings()
    refresh()

elif mode == _SEPARATOR:
    pass

else:
    main()

if doRefresh:
    refresh()
    
xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)