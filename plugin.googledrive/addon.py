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
import urlparse

from clouddrive.common.remote.request import Request
from clouddrive.common.ui.addon import CloudDriveAddon
from clouddrive.common.ui.utils import KodiUtils
from clouddrive.common.utils import Utils
from resources.lib.provider.googledrive import GoogleDrive
from clouddrive.common.ui.logger import Logger


class GoogleDriveAddon(CloudDriveAddon):
    _provider = GoogleDrive()
    _change_token = None
    
    def __init__(self):
        self._child_count_supported = False
        super(GoogleDriveAddon, self).__init__()
        
    def get_provider(self):
        return self._provider
    
    def get_my_files_menu_name(self):
        return self._addon.getLocalizedString(32013)
    
    def get_custom_drive_folders(self, driveid):
        self._account_manager.load()
        drive_folders = []
        drive_folders.append({'name' : self._common_addon.getLocalizedString(32058), 'path' : 'sharedWithMe'})
        if self._content_type == 'image':
            drive_folders.append({'name' : self._addon.getLocalizedString(32007), 'path' : 'photos'})
        drive_folders.append({'name' : self._addon.getLocalizedString(32014), 'path' : 'starred'})
        return drive_folders

    def new_change_token_slideshow(self, change_token, driveid, item_driveid=None, item_id=None, path=None):
        self._provider.configure(self._account_manager, driveid)
        if not change_token:
            response = self._provider.get('/changes/startPageToken', parameters = self._provider._parameters)
            self._change_token = Utils.get_safe_value(response, 'startPageToken')
            change_token = 1
        else:
            page_token = self._change_token
            while page_token:
                self._provider._parameters['pageToken'] = page_token
                self._provider._parameters['fields'] = 'nextPageToken,newStartPageToken,changes(file(id,name,parents))'
                response = self._provider.get('/changes', parameters = self._provider._parameters)
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
    
    def _get_item_play_url(self, file_name, driveid, item_driveid=None, item_id=None):
        url = None
        if KodiUtils.get_addon_setting('ask_stream_format') == 'true':
            url = self._select_stream_format(driveid, item_driveid, item_id)
        if not url:
            url = super(GoogleDriveAddon, self)._get_item_play_url(file_name, driveid, item_driveid, item_id)
        return url
    
    def _select_stream_format(self, driveid, item_driveid=None, item_id=None):
        url = None
        self._progress_dialog.update(0, self._addon.getLocalizedString(32009))
        self._provider.configure(self._account_manager, driveid)
        self._provider.get_item(item_driveid, item_id)
        request = Request('https://drive.google.com/get_video_info', urllib.urlencode({'docid' : item_id}), {'authorization': 'Bearer %s' % self._provider.get_access_tokens()['access_token']})
        response_text = request.request()
        response_params = dict(urlparse.parse_qsl(response_text))
        self._progress_dialog.close()
        if Utils.get_safe_value(response_params, 'status', '') == 'ok':
            fmt_list = Utils.get_safe_value(response_params, 'fmt_list', '').split(',')
            stream_formats = []
            for fmt in fmt_list:
                data = fmt.split('/')
                stream_formats.append(data[1])
            stream_formats.append(self._addon.getLocalizedString(32015))
            Logger.debug('Stream formats: %s' % Utils.str(stream_formats))
            select = self._dialog.select(self._addon.getLocalizedString(32016), stream_formats, 8000, 0)
            Logger.debug('Selected: %s' % Utils.str(select))
            if select == -1:
                self._cancel_operation = True
            elif select != len(stream_formats) - 1:
                data = fmt_list[select].split('/')
                fmt_stream_map = Utils.get_safe_value(response_params, 'fmt_stream_map', '').split(',')
                
                for fmt in fmt_stream_map:
                    stream_data = fmt.split('|')
                    if stream_data[0] == data[0]:
                        url = stream_data[1]
                        break
                if url:
                    cookie_header = ''
                    for cookie in request.response_cookies:
                        if cookie_header: cookie_header += ';'
                        cookie_header += cookie.name + '=' + cookie.value;
                    url += '|cookie=' + urllib.quote(cookie_header)
        return url;
    
if __name__ == '__main__':
    GoogleDriveAddon().route()

