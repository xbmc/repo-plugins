#-------------------------------------------------------------------------------
# Copyright (C) 2017 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
# 
# This file is part of Google Drive for Kodi
# 
# Google Drive for Kodi is free software: you can redistribute it and/or modify
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
from resources.lib.provider.googledrive import GoogleDrive


class GoogleDriveAddon(CloudDriveAddon):
    _plugin_actions = ('check_download_quota',)
    _change_token = None
    
    def __init__(self):
        self._provider = GoogleDrive()
        self._child_count_supported = False
        super(GoogleDriveAddon, self).__init__()
        
    def get_provider(self):
        return self._provider
    
    def get_my_files_menu_name(self):
        return self._addon.getLocalizedString(32013)
    
    def get_custom_drive_folders(self, driveid):
        drive_folders = []
        self._provider.configure(self._account_manager, driveid)
        if not self._provider._is_shared_drive:
            drive_folders.append({'name' : self._common_addon.getLocalizedString(32058), 'path' : 'sharedWithMe'})
        drive_folders.append({'name' : self._addon.getLocalizedString(32014), 'path' : 'starred'})
        return drive_folders

    def new_change_token_slideshow(self, change_token, driveid, item_driveid=None, item_id=None, path=None):
        self._provider.configure(self._account_manager, driveid)
        if not change_token:
            response = self._provider.get('/changes/startPageToken', parameters = self._provider.prepare_parameters())
            self._change_token = Utils.get_safe_value(response, 'startPageToken')
            change_token = 1
        else:
            page_token = self._change_token
            while page_token:
                parameters = self._provider.prepare_parameters()
                parameters['pageToken'] = page_token
                parameters['fields'] = 'nextPageToken,newStartPageToken,changes(file(id,name,parents))'
                response = self._provider.get('/changes', parameters = parameters)
                if self.cancel_operation():
                    return
                self._change_token = Utils.get_safe_value(response, 'newStartPageToken', self._change_token)
                changes = Utils.get_safe_value(response, 'changes', [])
                for change in changes:
                    f = Utils.get_safe_value(change, 'file', {})
                    parents = Utils.get_safe_value(f, 'parents', [])
                    parents.append(f['id'])
                    if item_id in parents:
                        return change_token + 1
                page_token = Utils.get_safe_value(response, 'nextPageToken')
        return change_token
    
    def get_context_options(self, list_item, params, is_folder):
        context_options = []
        if Utils.get_safe_value(params, 'action', '') == 'play':
            p = params.copy()
            p['action'] = 'check_download_quota'
            context_options.append((self._addon.getLocalizedString(32071), 'RunPlugin('+self._addon_url + '?' + urllib.parse.urlencode(p)+')'))
        return context_options
    
    def check_download_quota(self, driveid, item_driveid=None, item_id=None):
        # Google refuses downloads (403 or 429) when a file's download quota is exceeded.
        self._provider.configure(self._account_manager, driveid)
        self._progress_dialog.update(0, '')
        item = self._provider.get_item(item_driveid=item_driveid, item_id=item_id, include_download_info = True)
        url = item['download_info']['url']
        request_params = {
            'read_content' : False,
            'on_complete': lambda request: self.display_download_quota_result(request),
        }
        self._provider.prepare_request('get', url, request_params = request_params).request()

    def display_download_quota_result(self, request):
        self._progress_dialog.close()
        color = 'lime'
        exceeded = self._common_addon.getLocalizedString(32013)
        if request.response_code == 403 or request.response_code == 429:
            color = 'red'
            exceeded = self._common_addon.getLocalizedString(32033)
        msg = self._addon.getLocalizedString(32072) % '[B][COLOR %s]%s[/COLOR][/B]' % (color, exceeded,)
        msg += '\n' + self._addon.getLocalizedString(32073) % '[B]%s[/B]' % Utils.str(request.response_code)
        msg += '\n' + request.response_text
        self._dialog.ok(self._addon_name, msg)
