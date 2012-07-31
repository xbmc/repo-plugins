# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Benjamin Bertrand
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
# http://www.gnu.org/copyleft/gpl.html

import os
from xbmcswift import Plugin, xbmc, xbmcplugin

# Global variables
PLUGIN_NAME = 'Arrêt Sur Images'
PLUGIN_ID = 'plugin.video.arretsurimages'


class Plugin_mod(Plugin):
    """Plugin class modified to pass updateListing to xbmcplugin.endOfDirectory"""

    def add_items(self, iterable, view_mode=None, update_listing=False):
        items = []  # Keeps track of the list of tuples (url, list_item, is_folder) to pass to xbmcplugin.addDirectoryItems
        urls = []  # Keeps track of the XBMC urls for all of the list items
        for i, li_info in enumerate(iterable):
            items.append(self._make_listitem(**li_info))
            if self._mode in ['crawl', 'interactive', 'test']:
                #print '[%d] %s%s%s (%s)' % (i + 1, C.blue, li_info.get('label'), C.end, li_info.get('url'))
                print '[%d] %s%s%s (%s)' % (i + 1, '', li_info.get('label'), '', li_info.get('url'))
                urls.append(li_info.get('url'))

        if self._mode is 'xbmc':
            if not xbmcplugin.addDirectoryItems(self.handle, items, len(items)):
                raise Exception, 'problem?'
            if view_mode:
                xbmc.executebuiltin('Container.SetViewMode(%s)' % view_mode)
            xbmcplugin.endOfDirectory(self.handle, updateListing=update_listing)

        return urls

plugin = Plugin_mod(PLUGIN_NAME, PLUGIN_ID, __file__)
profile_path = xbmc.translatePath(plugin._plugin.getAddonInfo('profile'))
cookie_file = os.path.join(profile_path, 'asi_cookie.pkl')
