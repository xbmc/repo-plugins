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
import xbmcgui
import os


_STD_SETTINGS = 0
_ADDTOFAVES   = 100
_SF_SETTINGS  = 200
_LAUNCH_SF    = 300
_SEARCH       = 400
_SEARCHDEF    = 450
_DOWNLOAD     = 500
_PLAYLIST     = 600
_PLAYTUBE     = 700


def getDefaultSearch():
    import search

    fave = search.getDefaultSearch()
    if fave:
        return fave[0]

    return ''


def doStandard(useScript=True):
    window = xbmcgui.getCurrentWindowId()

    if window == 12005: #video playing
        xbmc.executebuiltin('Dialog.Close(all, true)')
        xbmc.executebuiltin('ActivateWindow(videoplaylist)')
        return

    if useScript:
        #open menu via script to prevent animation locking up (due to bug in XBMC)
        import utils    
        path   = utils.HOME
        script = os.path.join(path, 'standardMenu.py')
        cmd    = 'AlarmClock(%s,RunScript(%s),%d,True)' % ('menu', script, 0)
        xbmc.executebuiltin(cmd)  
    else:
        xbmc.executebuiltin('Action(ContextMenu)')
    

def copyFave(name, thumb, cmd):
    import favourite
    import utils

    text = utils.GETTEXT(30019)

    folder = utils.GetFolder(text)
    if not folder:
        return False
  
    file  = os.path.join(folder, utils.FILENAME)    

    fave = [name, thumb, cmd] 
  
    return favourite.copyFave(file, fave)


def activateCommand(cmd):
    cmds = cmd.split(',', 1)

    activate = cmds[0]+',return)'
    plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())

    if id not in activate:
        xbmc.executebuiltin(activate)
    
    xbmc.executebuiltin('Container.Update(%s)' % plugin)


def getDescription():
    labels = []
    labels.append('ListItem.Plot')
    labels.append('ListItem.Property(Addon.Description)')
    labels.append('ListItem.Property(Addon.Summary)')
    labels.append('ListItem.Property(Artist_Description)')
    labels.append('ListItem.Property(Album_Description)')
    labels.append('ListItem.Artist')
    labels.append('ListItem.Comment')

    for label in labels:
        desc = xbmc.getInfoLabel(label)
        if len(desc) > 0:
            return desc

    return ''


def doMenu():
    try:
        import utils
    except:
        doStandard(useScript=False)
        return  

    DEBUG = utils.ADDON.getSetting('DEBUG') == 'true'
    if DEBUG:
        window = xbmcgui.getCurrentWindowId()
        utils.DialogOK('Current Window ID %d' % window)  

    active = [0, 1, 2, 25, 40, 500, 501, 502, 601]
    window = xbmcgui.getCurrentWindowId()
    utils.log('Window     : %d' % window)  
    if window-10000 not in active:
        doStandard(useScript=False)
        return

    import menus

    # to prevent master profile setting being used in other profiles
    if utils.ADDON.getSetting('CONTEXT') != 'true':
        doStandard(useScript=False)
        return

    folder = xbmc.getInfoLabel('Container.FolderPath')
    path  = xbmc.getInfoLabel('ListItem.FolderPath')

    #ignore if in Super Favourites
    if (utils.ADDONID in folder) or (utils.ADDONID in path):
        doStandard(useScript=False)
        return
        
    choice   = 0
    label    = xbmc.getInfoLabel('ListItem.Label')
    filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    name     = xbmc.getInfoLabel('ListItem.Label')
    thumb    = xbmc.getInfoLabel('ListItem.Thumb')    
    thumb    = xbmc.getInfoLabel('ListItem.Art(thumb)')
    playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
    fanart   = xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
    fanart   = xbmc.getInfoLabel('ListItem.Art(fanart)')
    isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1
    desc     = getDescription()

    try:    file = xbmc.Player().getPlayingFile()
    except: file = None

    isStream = False
    if file:
        isStream = file.startswith('http://')

    #GOTHAM only 
    #if hasattr(xbmc.Player(), 'isInternetStream'):
    #    isStream = xbmc.Player().isInternetStream()
    #elif file:
    #    isStream = file.startswith('http://')

    if isFolder:
        path     = path.replace('\\', '\\\\')
        filename = filename.replace('\\', '\\\\')

    utils.log('**** Context Menu Information ****')
    utils.log('Label      : %s' % label)
    utils.log('Folder     : %s' % folder) 
    utils.log('Path       : %s' % path) 
    utils.log('Filename   : %s' % filename)
    utils.log('Name       : %s' % name)    
    utils.log('Thumb      : %s' % thumb)
    utils.log('Fanart     : %s' % fanart)   
    utils.log('Window     : %d' % window)  
    utils.log('IsPlayable : %s' % playable)
    utils.log('IsFolder   : %s' % isFolder)
    utils.log('File       : %s' % file)
    utils.log('IsStream   : %s' % isStream)

    menu = []

    #if (len(menu) == 0) and window == 12005: #video playing
        #if isStream:
        #    menu.append(('Download  %s' % label, _DOWNLOAD))
        #    menu.append(('Show Playlist',        _PLAYLIST))
        #else:
        #    return doStandard()
        #cancel download feature for now
        #return doStandard()
    
    if (len(menu) == 0) and len(path) > 0:
        menu.append((utils.GETTEXT(30047), _ADDTOFAVES))
        menu.append((utils.GETTEXT(30049), _SF_SETTINGS))

        if utils.ADDON.getSetting('SHOWSS') == 'true':
            menu.append((utils.GETTEXT(30054), _SEARCH))

            default = getDefaultSearch()
            if len(default) > 0:
                menu.append((utils.GETTEXT(30098) % default, _SEARCHDEF))

        menu.append((utils.GETTEXT(30048), _STD_SETTINGS))

    elif window == 10000: #Home screen
        #menu.append((utils.GETTEXT(30053), _LAUNCH_SF))
        #menu.append((utils.GETTEXT(30049), _SF_SETTINGS))
        pass


    if len(menu) == 0:
        doStandard()
        return

    xbmcgui.Window(10000).setProperty('SF_MENU_VISIBLE', 'true')

    dialog = utils.ADDON.getSetting('CONTEXT_STYLE') == '1'

    if dialog:
        choice = menus.selectMenu(utils.TITLE, menu)
    else:
        choice = menus.showMenu(utils.ADDONID, menu, utils.HELIX)


    if choice == _STD_SETTINGS:
        doStandard()
        return

    xbmc.executebuiltin('Dialog.Close(all, true)')

    if choice == _PLAYLIST:
        xbmc.executebuiltin('ActivateWindow(videoplaylist)')

    #if choice == _DOWNLOAD: 
    #    import download
    #    download.download(file, 'c:\\temp\\file.mpg', 'Super Favourites')

    
    if choice == _STD_SETTINGS:
        doStandard()

    if choice == _SF_SETTINGS:
        utils.ADDON.openSettings()

    if choice == _ADDTOFAVES:
        import favourite
        if isFolder:
            cmd =  'ActivateWindow(%d,"%s' % (window, path)
        elif path.lower().startswith('script'):
            #if path[-1] == '/':
            #    path = path[:-1]
            cmd = 'RunScript("%s' % path.replace('script://', '')
        elif path.lower().startswith('videodb') and len(filename) > 0:
            cmd = 'PlayMedia("%s' % filename
        #elif path.lower().startswith('musicdb') and len(filename) > 0:
        #    cmd = 'PlayMedia("%s")' % filename
        elif path.lower().startswith('androidapp'):
            cmd = 'StartAndroidActivity("%s")' % path.replace('androidapp://sources/apps/', '', 1)
        else:            
            cmd = 'PlayMedia("%s")' % path
            cmd = favourite.updateSFOption(cmd, 'winID', window)

        cmd = favourite.addFanart(cmd, fanart)
        cmd = favourite.updateSFOption(cmd, 'desc', desc)

        if isFolder:
            cmd = cmd.replace('")', '",return)')
       
        copyFave(name, thumb, cmd)

    if choice == _LAUNCH_SF:
        utils.LaunchSF()

    if choice == _SEARCH or choice == _SEARCHDEF:
        if utils.ADDON.getSetting('STRIPNUMBERS') == 'true':
            name = utils.Clean(name)

        thumb  = thumb  if len(thumb)  > 0 else 'null'
        fanart = fanart if len(fanart) > 0 else 'null'

        _SUPERSEARCH    =  0     #declared as  0 in default.py
        _SUPERSEARCHDEF = 10     #declared as 10 in default.py

        mode    = _SUPERSEARCH if (choice == _SEARCH) else _SUPERSEARCHDEF
        videoID = 10025 #video

        if window == 10000: #don't activate on home screen, push to video
            window = videoID

        import urllib        

        cmd = 'ActivateWindow(%d,"plugin://%s/?mode=%d&keyword=%s&image=%s&fanart=%s")' % (window, utils.ADDONID, mode, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(fanart))
        activateCommand(cmd)


def main():
    if xbmcgui.Window(10000).getProperty('SF_MENU_VISIBLE') == 'true':
        return

    doMenu()    


try:        
    main()
except Exception, e:
    import utils
    utils.log('Exception in capture.py %s' % str(e))

xbmc.sleep(1000)
xbmcgui.Window(10000).clearProperty('SF_MENU_VISIBLE')