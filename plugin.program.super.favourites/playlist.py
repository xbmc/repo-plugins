#
#       Copyright (C) 2015-
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
import os

import utils
import sfile

#PLAYLIST_EXT = '.m3u|.xsp|.strm'
PLAYLIST_EXT = '.m3u|.m3u8'


def play(cmd):
    import sfile
    if cmd.lower().startswith('activatewindow'):
        playlist = cmd.split(',', 1)
        playlist = playlist[-1][:-1]
        cmd      = 'PlayMedia(%s)' % playlist

    elif sfile.exists(cmd):
        #cmd = 'PlayMedia(%s)' % cmd
        playFile(cmd)
        return

    xbmc.executebuiltin(cmd)


def playFile(path):
    items = parse(sfile.readlines(path))
    utils.playItems(items)


def getPlaylist():
    root     = utils.HOME.split(os.sep, 1)[0] + os.sep    
    playlist = xbmcgui.Dialog().browse(1, utils.GETTEXT(30148), 'files', PLAYLIST_EXT, False, False, root)
    
    if playlist and playlist != root:
        return playlist

    return None


def parseFolder(folder):
    try:    current, dirs, files = sfile.walk(folder)
    except: return []

    items = []

    for file in files:
        try:
            path = os.path.join(current, file)
            file = file.rsplit('.', 1)
            ext  = file[-1]
            file = file[0]            
            if ext in PLAYLIST_EXT:
                items.append([path, file])
        except:
            pass

    return items


def parse(playlist):
    if len(playlist) == 0:
        return []

    items = []
    path  = ''
    title = ''
 
    try:
        for line in playlist:         
            line = line.strip()
            if line.startswith('#EXTINF:'):                
                title  = line.split(':', 1)[-1].split(',', 1)[-1]
                if len(title) == 0:
                    title = "Unnamed" #SJP
            else:
                path = line.replace('rtmp://$OPT:rtmp-raw=', '')
                if len(path) > 0 and len(title) > 0:                    
                    items.append([title, path])
                path  = ''
                title = ''
    except:
        pass
            
    return items


def isPlaylist(cmd):
    cmd = cmd.lower().replace(',return', '')

    if cmd.endswith('.m3u")'):
        return True

    if cmd.endswith('.m3u8")'):
        return True

    return False