#
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
from utils import Key, PluginSettings
from xbmcplugin import addDirectoryItem, endOfDirectory, setResolvedUrl
from xbmcgui import ListItem
from connection_manager import DataHandle


def mms_to_http(url):
    return url.replace('mms', 'http')

def mms_url(data):
    print data
    nurl = ''
    for c in data[18:]:
        if c != '\r':
            nurl += c
        else: break
    nurl = nurl.replace('http', 'mms')
    return nurl
        

        
class Main:

    BASEURL = 'mms://straumv.nrk.no/nrk_tv_direkte_nrk%s_%s'
    CHANNELS = [
            ('NRK',  '1', 'http://fil.nrk.no/nett-tv/data/stillbilder/nrk1_100x57.gif'),
            ('NRK2', '2', 'http://fil.nrk.no/nett-tv/data/stillbilder/nrk2_100x57.gif'),
            ('NRK3', '3', 'http://fil.nrk.no/nett-tv/data/stillbilder/nrk3_100x57.gif')
        ]
  
    
    def __init__(self):

        key = Key( sys.argv[2] )
        self.hndl = int(sys.argv[1])
        self.success = True
        
        if not key.id:
            self.parse_channels()
        else:
            self.get_stream(key.id)
            
    def get_stream(self, id):
        self.get_settings()
        self.dman = DataHandle()
        url = mms_to_http( self.BASEURL % (id, self.settings['connection_speed']) )
        data = self.dman.get_data(url)
        url = mms_url(data)
        listitem = ListItem( self.CHANNELS[int(id) - 1][0], path=url)
        setResolvedUrl(self.hndl, self.success, listitem)
        
    def get_settings(self):
        self.settings = PluginSettings()
        #Connection speed
        options = ( 'l', 'm', 'h', ); index = 11
        self.settings.add('connection_speed', 'values', options, index)
        
    def parse_channels(self):
        for i in self.CHANNELS:
            self.add(i[0], i[1], img=i[2])
        endOfDirectory(self.hndl)

    def add(self, label, id, type='channel', prefix='kanalene', img='', icon='', isdir=False):
        url = Key.build_url(prefix, type=type, id=id)
        li = ListItem(label, iconImage=icon, thumbnailImage=img)
        li.setProperty('IsPlayable', 'true')
        ok = addDirectoryItem(self.hndl, url=url, listitem=li, isFolder=isdir)
        return ok