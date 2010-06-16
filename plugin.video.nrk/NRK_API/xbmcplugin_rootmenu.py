#
#   NRK plugin for XBMC Media center
#
# Copyright (C) 2009 Victor Vikene  contact: z0py3r@hotmail.com
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
#

import sys, os
import api_nrk as nrk
import xbmc
from utils import Key, Plugin
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory, getSetting

xbmc.log( "PLUGIN::LOADED -> '%s'" % __name__, xbmc.LOGNOTICE )
lang = sys.modules[ "__main__" ].__language__

FAV_PATH = os.path.join(
                xbmc.translatePath("special://profile/"), 
                "addon_data",  
                os.path.basename(Plugin.cwd), 
                "shows.xml"
            )

class Main:
    
    # Default path for images
    rpath = os.path.join(os.getcwd(), 'resources', 'images')
    
    
    # Function for adding main menu entries that is to displayed to the user
    def add(self, label, prefix, type, id=None, img='', icon='', isdir=True, commands=None):
    
        # Make full path for where to look for specified image
        if img != '':
            img = os.path.join(self.rpath, img)
            
        url = Key.build_url(prefix, type=type, id=id)
        li  = ListItem(label, iconImage=icon, thumbnailImage=img)
        if commands:
            li.addContextMenuItems( commands, True )
        ok  = addDirectoryItem(self.hndl, url=url, listitem=li, isFolder=isdir)
        
        return ok
        
        
    # This initialization function builds the main menu. 
    # Order, text and icons for main menu entries are given here.
    def __init__(self):
    
        self.hndl = int(sys.argv[1])
     
     
        self.add(lang(30250),  nrk.PROGRAM,  nrk.PROGRAM,  img='program-icon.png')
        self.add(lang(30251),  nrk.PROGRAM,  nrk.LIVE,     img='live-icon.png')
        self.add(lang(30252),  nrk.CHANNELS, nrk.CHANNELS, img='channels-icon.png')
            
        self.add(lang(30253),   nrk.PROGRAM,  nrk.PLAYLIST, 'sport',    'sports-icon.png')
        self.add(lang(30254),  nrk.PROGRAM,  nrk.PLAYLIST, 'nyheter',  'news-icon.png')
        self.add(lang(30255),  nrk.PROGRAM,  nrk.PLAYLIST, 'distrikt', 'regions-icon.png')
        #self.add('Barn',       nrk.PROGRAM,     nrk.PLAYLIST, 'super',    'children-icon.png')
        self.add(lang(30256),  nrk.PROGRAM,  nrk.PLAYLIST, 'natur',    'nature-icon.png')
      
        self.add(lang(30257),  'nrkbeta',    'feed',     img='nrkbeta.png')
        self.add(lang(30258),  'webradio',   'webradio', img='speaker-icon.png')
        self.add(lang(30260),  'podcast',    'video',    img='video-podcast.png')
        self.add(lang(30259),  'podcast',    'sound',    img='audio-podcast.png')
        
        commands = []
        commands.append(( lang(30800), 
                        'XBMC.RunPlugin(%s)' % ( Key.build_url('teletext', page=101)), 
                        ))
        commands.append(( lang(30801), 
                        'XBMC.RunPlugin(%s)' % ( Key.build_url('teletext', page=131)), 
                        ))
        commands.append(( lang(30802), 
                        'XBMC.RunPlugin(%s)' % ( Key.build_url('teletext', page=200)), 
                        ))
        commands.append(( lang(30803), 
                        'XBMC.RunPlugin(%s)' % ( Key.build_url('teletext', page=300)), 
                        ))
        commands.append(( lang(30804), 
                        'XBMC.RunPlugin(%s)' % ( Key.build_url('teletext', page=590)), 
                        ))
        self.add( lang(30261),      'teletext', 'teletext', img='ttv-icon.png', isdir=False, commands=commands)
        
        # Only add the entry for Favourites if the xml file containing favourites exists already.
        if os.path.isfile(FAV_PATH):
          self.add(lang(30262), 'favorites', 'favorites', img='favorites.png')
          
        endOfDirectory(self.hndl)
