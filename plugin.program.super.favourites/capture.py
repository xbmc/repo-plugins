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

import utils
import contextmenu
import favourite


def copyFave(name, thumb, cmd):
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


def doMenu():
    folder = xbmc.getInfoLabel('Container.FolderPath')
    if utils.ADDONID in folder:
        xbmc.executebuiltin('XBMC.Action(ContextMenu)')
        return
        
    choice   = 0
    path     = xbmc.getInfoLabel('ListItem.FolderPath')
    filename = xbmc.getInfoLabel('ListItem.FilenameAndPath')
    name     = xbmc.getInfoLabel('ListItem.Label')
    thumb    = xbmc.getInfoLabel('ListItem.Thumb')
    window   = xbmcgui.getCurrentWindowId()
    playable = xbmc.getInfoLabel('ListItem.Property(IsPlayable)').lower() == 'true'
    isFolder = xbmc.getCondVisibility('ListItem.IsFolder') == 1
    
    if len(path) > 0:
        menu = []
        menu.append((utils.GETTEXT(30047), 1))
        menu.append((utils.GETTEXT(30049), 2))
        menu.append((utils.GETTEXT(30048), 0))

        choice = contextmenu.showMenu(utils.ADDONID, menu)

    if choice == None:
        return

    if choice == 0:
        xbmc.executebuiltin('XBMC.Action(ContextMenu)')
        return

    if choice == 2:
        utils.ADDON.openSettings()
        return

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


doMenu()
