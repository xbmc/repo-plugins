#-------------------------------------------------------------------------------
# Copyright (C) 2017 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
# 
# This file is part of OneDrive for Kodi
# 
# OneDrive for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Cloud Drive Common Module for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import urllib

from clouddrive.common.ui.addon import CloudDriveAddon
from clouddrive.common.utils import Utils
from resources.lib.provider.onedrive import OneDrive

class OneDriveAddon(CloudDriveAddon):
    _provider = OneDrive()
    _action = None
    
    def __init__(self):
        super(OneDriveAddon, self).__init__()
        
    def get_provider(self):
        return self._provider
    
    def get_custom_drive_folders(self, driveid):
        drive = self._account_manager.get_by_driveid('drive', driveid)
        drive_folders = []
        if drive['type'] == 'personal':
            if self._content_type == 'image':
                path = 'special/photos'
                params = {'action': '_slideshow', 'content_type': self._content_type, 'driveid': driveid, 'path': path}
                context_options = [(self._common_addon.getLocalizedString(32032), 'RunPlugin('+self._addon_url + '?' + urllib.urlencode(params)+')')]
                drive_folders.append({'name' : self._addon.getLocalizedString(32007), 'path' : path, 'context_options': context_options})
                
                path = 'special/cameraroll'
                params['path'] = path
                context_options = [(self._common_addon.getLocalizedString(32032), 'RunPlugin('+self._addon_url + '?' + urllib.urlencode(params)+')')]
                drive_folders.append({'name' : self._addon.getLocalizedString(32008), 'path' : path, 'context_options': context_options})
            elif self._content_type == 'audio':
                drive_folders.append({'name' : self._addon.getLocalizedString(32009), 'path' : 'special/music'})
        drive_folders.append({'name' : self._common_addon.getLocalizedString(32053), 'path' : 'recent'})
        if drive['type'] != 'documentLibrary':
            drive_folders.append({'name' : self._common_addon.getLocalizedString(32058), 'path' : 'sharedWithMe'})
        return drive_folders

    def _rename_action(self):
        if self._action == 'open_drive_folder':
            self._addon_params['path'] = Utils.get_safe_value(self._addon_params, 'folder')
        self._action = Utils.get_safe_value({
            'open_folder': '_list_folder',
            'open_drive': '_list_drive',
            'open_drive_folder': '_list_folder'
        }, self._action, self._action)

if __name__ == '__main__':
    OneDriveAddon().route()

