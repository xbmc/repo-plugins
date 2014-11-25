#/*
# *      Copyright (C) 2013 Joost Kop
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmcplugin
import xbmcgui

import urllib

from resources.lib.utils import *
from resources.lib.dropboxviewer import *
import resources.lib.login as login

class DropboxSearch(DropboxViewer):
        
    def __init__( self, params, account_settings ):
        super(DropboxSearch, self).__init__(params, account_settings)
        self._searchText = params.get('search_text', '')

    def buildList(self):
        #get the list
        searchResult = self._client.search(self._searchText, self._current_path)
        #Build the list
        super(DropboxSearch, self).buildList(searchResult)
        
    def show(self):
        if self._loader:
            super(DropboxSearch, self).show()
        else:
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30021) )
            super(DropboxSearch, self).show(succeeded=False)

    def getUrl(self, path, media_items=0, module=None):
        url = super(DropboxSearch, self).getUrl(path, media_items, module)
        url += '&search_text=' + urllib.quote(self._searchText)
        return url
        
    
def run(params): # This is the entrypoint
    account_name = urllib.unquote( params.get('account', '') )
    account_settings = login.get_account(account_name) 
    if account_settings:
        searchText = params.get('search_text', '')
        #check if a search text is already defined
        if searchText == '':
            #No search text defined, ask for it.
            keyboard = xbmc.Keyboard('', LANGUAGE_STRING(30018))
            keyboard.doModal()
            if keyboard.isConfirmed():
                searchText = keyboard.getText()
                params['search_text'] = searchText
                params['path'] = params.get('path', DROPBOX_SEP)
        if len(searchText) < 3:
            #Search text has to be atleast 3 chars
            dialog = xbmcgui.Dialog()
            dialog.ok(ADDON_NAME, LANGUAGE_STRING(30019) )
            xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)
        else:
            search = DropboxSearch(params, account_settings)
            dialog = xbmcgui.DialogProgress()
            dialog.create(ADDON_NAME, LANGUAGE_STRING(30020), searchText)
            search.buildList()
            dialog.close()
            search.show()
    else:
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False)

