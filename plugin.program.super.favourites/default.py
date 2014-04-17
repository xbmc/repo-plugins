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
GOTHAM   = utils.GOTHAM

FILENAME = 'favourites.xml'

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

SHOWNEW  = ADDON.getSetting('SHOWNEW')  == 'true'
SHOWXBMC = ADDON.getSetting('SHOWXBMC') == 'true'


def clean(text):
    text = re.sub('[:\\/*?\<>|"]+', '', text)
    return text.strip()


def main():
    utils.CheckVersion()

    profile = xbmc.translatePath(PROFILE)

    addNewFolderItem(profile)

    if SHOWXBMC:        
        addDir(GETTEXT(30040), _XBMC, thumbnail='DefaultFolder.png', isFolder=True)
        addSeparatorItem()

    parseFolder(profile)


def addNewFolderItem(path):
    if SHOWNEW:
        addDir(GETTEXT(30004), _NEWFOLDER, path=path, thumbnail=ICON, isFolder=False) 
        addSeparatorItem()


def addSeparatorItem():
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
    menu.append((GETTEXT(30006), 'XBMC.RunPlugin(%s?mode=%d&name=%s&thumb=%s&cmd=%s)' % (sys.argv[0], _ADDTOXBMC, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(cmd))))


def addToXBMC(name, thumb, cmd):
    cmd = cmd.replace('&', '&amp;')
    cmd = cmd.replace('+', '%20')
    cmd = '&quot;%s&quot;' % cmd

    cmd = 'ActivateWindow(10001,%s)' % cmd

    fave = [name, thumb, cmd]

    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)

    #if it is already in there don't add again
    if findFave(file, cmd):
        return False

    faves = favourite.getFavourites(file)
    faves.append(fave)

    favourite.writeFavourites(file, faves)

    return True


def refresh():
    xbmc.executebuiltin('Container.Refresh')


def showXBMCFolder():
    file = os.path.join(xbmc.translatePath('special://profile'), FILENAME)
    parseFile(file, True)


def parseFile(file, isXBMC=False):
    faves = favourite.getFavourites(file)
    for fave in faves:
        label = fave[0]
        thumb = fave[1]
        cmd   = fave[2]

        menu  = []

        include = True #originally set to (not isXBMC)

        menu.append((GETTEXT(30007), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _COPY, urllib.quote_plus(file), urllib.quote_plus(cmd))))
        if include:
            menu.append((GETTEXT(30008), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _MOVE,       urllib.quote_plus(file), urllib.quote_plus(cmd))))
            menu.append((GETTEXT(30009), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _REMOVEFAVE, urllib.quote_plus(file), urllib.quote_plus(cmd))))
            menu.append((GETTEXT(30010), 'XBMC.RunPlugin(%s?mode=%d&file=%s&cmd=%s)' % (sys.argv[0], _RENAMEFAVE, urllib.quote_plus(file), urllib.quote_plus(cmd))))

        addDir(label, _COMMAND, cmd=cmd, thumbnail=thumb, isFolder=False, menu=menu)

    return len(faves) > 0


def parseFolder(folder):
    try:    current, dirs, files = os.walk(folder).next()
    except: return

    for dir in dirs:
        path = os.path.join(current, dir)
        menu = []
        menu.append((GETTEXT(30011), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _REMOVEFOLDER, urllib.quote_plus(path))))
        menu.append((GETTEXT(30012), 'XBMC.RunPlugin(%s?mode=%d&path=%s)' % (sys.argv[0], _RENAMEFOLDER, urllib.quote_plus(path))))

        addDir(dir,  _FOLDER, path=path, thumbnail=ICON, isFolder=True, menu=menu)

    file  = os.path.join(folder, FILENAME)

    nmrDirs = len(dirs)

    if nmrDirs > 0:
        addSeparatorItem()

    nmrFaves = parseFile(file)

    if nmrDirs == 0 and nmrFaves == 0 and not SHOWNEW:
        if not (SHOWXBMC and mode == -1):
            addSeparatorItem() 


def getText(title, text=''):
    kb = xbmc.Keyboard(text, title)
    kb.doModal()
    if not kb.isConfirmed():
        return None

    text = clean(kb.getText())
    if len(text) < 1:
        return None

    return text


def getFolder(title):
    default = ADDON.getAddonInfo('profile')
    folder  = xbmc.translatePath(PROFILE)

    if not os.path.isdir(folder):
        os.makedirs(folder) 

    folder = xbmcgui.Dialog().browse(3, title, 'files', '', False, False, default)
    if folder == default:
        return None

    return xbmc.translatePath(folder)


def createNewFolder(current):
    text = getText(GETTEXT(30013))
    if not text:
        return

    folder = os.path.join(current, text)
    if os.path.exists(folder):
        utils.DialogOK('', GETTEXT(30014) % text)
        return

    os.mkdir(folder)
    refresh()


def renameFolder(path):
    label = path.rsplit(os.sep, 1)[-1]
    text  = getText(GETTEXT(30015) % label, label)
    if not text:
        return

    root = path.rsplit(os.sep, 1)[0]
    newName = os.path.join(root, text)
    os.rename(path, newName)
    refresh()


def removeFolder(path):
    label = path.rsplit(os.sep, 1)[-1]
    if utils.DialogYesNo(GETTEXT(30016) % label, GETTEXT(30017), GETTEXT(30018)):
        try:    shutil.rmtree(path)
        except: pass
        refresh()


def moveFave(file, cmd):
    if not copyFave(file, cmd, move=True):
        return False

    return removeFave(file, cmd)


def findFave(file, cmd):
    faves = favourite.getFavourites(file)
    for fave in faves:
        if fave[2] == cmd:
            return fave
    return None


def copyFave(file, cmd, move=False):
    copy = findFave(file, cmd)
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

        #if 'ActivateWindow' in cmd:
        #    return activateWindowCommand(cmd)

        #workaraound bug in Frodo that can cause lock-up
        #when running a script favourite
        #if not GOTHAM and 'RunScript' in cmd:
        #    xbmc.executebuiltin('ActivateWindow(Home)')

        xbmc.executebuiltin(cmd)
    except:
        pass


def activateWindowCommand(cmd):
    cmds = cmd.split(',', 1)

    activate = cmds[0]+')'
    plugin   = cmds[1][:-1]

    xbmc.executebuiltin(activate)
    xbmc.executebuiltin('XBMC.Container.Update(%s)' % plugin)

    
def addDir(label, mode, index=-1, path = '', cmd = '', thumbnail='', isFolder=True, menu=None):
    u  = sys.argv[0]
    u += '?label='    + urllib.quote_plus(label)
    u += '&mode='     + str(mode)

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

    if isFolder and mode != _XBMC:
        addFavouriteMenuItem(menu, label, thumbnail, u)

    addGlobalMenuItem(menu)
    liz.addContextMenuItems(menu, replaceItems=True)

    infoLabels = {'container.folderName' : 'FANART'}
    liz.setInfo(type='default-view', infoLabels=infoLabels)

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
mode     = -1
thepath  = ''

try:    mode = int(params['mode'])
except: pass

if mode == _XBMC:
    showXBMCFolder()
    xbmc.executebuiltin('Container.Update')


elif mode == _COMMAND:
    cmd = urllib.unquote_plus(params['cmd'])
    playCommand(cmd)


elif mode == _FOLDER:
    thepath = urllib.unquote_plus(params['path'])
    addNewFolderItem(thepath)
    parseFolder(thepath)


elif mode == _REMOVEFOLDER:
    path = urllib.unquote_plus(params['path'])
    removeFolder(path)


elif mode == _RENAMEFOLDER:
    path = urllib.unquote_plus(params['path'])
    renameFolder(path)


elif mode == _NEWFOLDER:
    path = urllib.unquote_plus(params['path'])
    createNewFolder(path)


elif mode == _MOVE:
    file = urllib.unquote_plus(params['file'])
    cmd  = urllib.unquote_plus(params['cmd'])
    if moveFave(file, cmd):
        refresh()


elif mode == _COPY:
    file = urllib.unquote_plus(params['file'])
    cmd  = urllib.unquote_plus(params['cmd'])
    if copyFave(file, cmd):
        refresh()


elif mode == _REMOVEFAVE:
    file = urllib.unquote_plus(params['file'])
    cmd  = urllib.unquote_plus(params['cmd'])
    if removeFave(file, cmd):
        refresh()


elif mode == _RENAMEFAVE:
    file = urllib.unquote_plus(params['file'])
    cmd  = urllib.unquote_plus(params['cmd'])
    if renameFave(file, cmd):
        refresh()

elif mode == _ADDTOXBMC:
    name  = urllib.unquote_plus(params['name'])
    thumb = urllib.unquote_plus(params['thumb'])
    cmd   = urllib.unquote_plus(params['cmd'])
    addToXBMC(name, thumb, cmd)

    
elif mode == _SETTINGS:
    ADDON.openSettings()
    refresh()

elif mode == _SEPARATOR:
    pass

else:
    main()
    
xbmcplugin.endOfDirectory(int(sys.argv[1]))