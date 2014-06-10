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
import xbmcgui


_STD_SETTINGS = 0
_ADDTOFAVES   = 100
_SF_SETTINGS  = 200
_LAUNCH_SF    = 300
_SEARCH       = 400
_DOWNLOAD     = 500
_PLAYLIST     = 600


def doStandard():
    window   = xbmcgui.getCurrentWindowId()

    if window == 12005: #video playing
        xbmc.executebuiltin('ActivateWindow(videoplaylist)')
        return

    xbmc.executebuiltin('XBMC.Action(ContextMenu)')


def copyFave(name, thumb, cmd):
    import favourite
    import utils

    text = utils.GETTEXT(30019)

    folder = utils.GetFolder(text)
    if not folder:
        return False
  
    file  = os.path.join(folder, utils.FILENAME)
    faves = favourite.getFavourites(file)

    #if it is already in there don't add again
    for fave in faves:
        if fave[2] == cmd:            
            return False

    fave = [name, thumb, cmd] 
  
    faves.append(fave)
    favourite.writeFavourites(file, faves)

    return True


def activateCommand(cmd):
    cmds = cmd.split(',', 1)

    activate = cmds[0]+',return)'
    plugin   = cmds[1][:-1]

    #check if it is a different window and if so activate it
    id = str(xbmcgui.getCurrentWindowId())

    if id not in activate:
        xbmc.executebuiltin(activate)
    
    xbmc.executebuiltin('Container.Update(%s)' % plugin)


def doMenu():
    try:
        import utils
    except:
        doStandard()
        return    

    import contextmenu

    # to prevent master profile setting being used in other profiles
    if utils.ADDON.getSetting('CONTEXT') != 'true':
        doStandard()
        return

    folder = xbmc.getInfoLabel('Container.FolderPath')
    #ignore if in Super Favourites
    if utils.ADDONID in folder:
        doStandard()
        return
        
    choice   = 0
    label    = xbmc.getInfoLabel('ListItem.Label')
    path     = xbmc.getInfoLabel('ListItem.FolderPath')
    filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    name     = xbmc.getInfoLabel('ListItem.Label')
    thumb    = xbmc.getInfoLabel('ListItem.Thumb')
    window   = xbmcgui.getCurrentWindowId()
    playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
    fanart   = xbmc.getInfoLabel('ListItem.Property(Fanart_Image)')
    isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1

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

    #print '**** Context Menu Information ****'
    #print 'Label      : %s' % label
    #print 'Folder     : %s' % folder 
    #print 'Path       : %s' % path    
    #print 'Filename   : %s' % filename
    #print 'Name       : %s' % name    
    #print 'Thumb      : %s' % thumb
    #print 'Fanart     : %s' % fanart   
    #print 'Window     : %d' % window  
    #print 'IsPlayable : %s' % playable
    #print 'IsFolder   : %s' % isFolder
    #print 'File       : %s' % file
    #print 'IsStream   : %s' % isStream

    menu = []

    if (len(menu) == 0) and window == 12005: #video playing
        if isStream:
            menu.append(('Download  %s' % label , _DOWNLOAD))
            menu.append(('Show Playlist',         _PLAYLIST))
        else:
            return doStandard()
        #cancel download feature for now
        return doStandard()
    
    if (len(menu) == 0) and len(path) > 0:    
        utils.verifySuperSearch()
        menu.append((utils.GETTEXT(30047), _ADDTOFAVES))
        menu.append((utils.GETTEXT(30049), _SF_SETTINGS))
        menu.append((utils.GETTEXT(30054), _SEARCH))
        menu.append((utils.GETTEXT(30048), _STD_SETTINGS))

        
    #elif window == 10000: #Home screen
    #    menu.append((utils.GETTEXT(30053), _LAUNCH_SF))
    #    menu.append((utils.GETTEXT(30049), _SF_SETTINGS))


    if len(menu) == 0:
        doStandard()
        return

    xbmcgui.Window(10000).setProperty('SF_MENU_VISIBLE', 'true')
    choice = contextmenu.showMenu(utils.ADDONID, menu)

    if choice == _PLAYLIST:
        xbmc.executebuiltin('ActivateWindow(videoplaylist)')

    if choice == _DOWNLOAD: 
        import download
        download.download(file, 'c:\\temp\\file.mpg', 'Super Favourites')
    
    if choice == _STD_SETTINGS:
        xbmc.executebuiltin('XBMC.Action(ContextMenu)')

    if choice == _SF_SETTINGS:
        utils.ADDON.openSettings()

    if choice == _ADDTOFAVES:
        if isFolder:
            cmd =  'ActivateWindow(%d,"%s")' % (window, path)
        elif path.lower().startswith('script'):
            if path[-1] == '/':
                path = path[:-1]
            cmd = 'RunScript("%s")' % path.replace('script://', '')
        elif path.lower().startswith('videodb') and len(filename) > 0:
            cmd = 'PlayMedia("%s")' % filename
        #elif path.lower().startswith('musicdb') and len(filename) > 0:
        #    cmd = 'PlayMedia("%s")' % filename
        else:
            cmd = 'PlayMedia("%s&sf_win_id=%d_")' % (path, window)

        copyFave(name, thumb, cmd)

    if choice == _LAUNCH_SF:
        xbmc.executebuiltin('ActivateWindow(programs,plugin://%s)' % utils.ADDONID)

    if choice == _SEARCH:
        thumb  = thumb  if len(thumb)  > 0 else 'null'
        fanart = fanart if len(fanart) > 0 else 'null'
        import urllib
        _SUPERSEARCH = 0     #declared as 0 in default.py
        winID        = 10025 #video
        cmd = 'ActivateWindow(%d,"plugin://%s/?mode=%d&keyword=%s&image=%s&fanart=%s")' % (window, utils.ADDONID, _SUPERSEARCH, urllib.quote_plus(name), urllib.quote_plus(thumb), urllib.quote_plus(fanart))
        activateCommand(cmd)


if xbmcgui.Window(10000).getProperty('SF_MENU_VISIBLE') != 'true':
    doMenu()
    xbmcgui.Window(10000).clearProperty('SF_MENU_VISIBLE')