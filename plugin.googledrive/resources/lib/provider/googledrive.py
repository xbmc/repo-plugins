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

from clouddrive.common.remote.provider import Provider


class GoogleDrive(Provider):
    __api_url = 'https://www.googleapis.com/drive/v3'
    _user = None
    
    def __init__(self):
        super(GoogleDrive, self).__init__('googledrive')
        
    def _get_api_url(self):
        return self.__api_url

    def _get_request_headers(self):
        return None
    
    def get_account(self, request_params={}, access_tokens={}):
        me = self.get('/about', parameters={'fields':'user'}, request_params=request_params, access_tokens=access_tokens)
        if not me or not 'user' in me:
            raise Exception('NoAccountInfo')
        self._user = me['user'] 
        return { 'id' : self._user['permissionId'], 'name' : self._user['displayName']}
    
    def get_drives(self, request_params={}, access_tokens={}):
        drives = [{
            'id' : self._user['permissionId'],
            'name' : '',
            'type' : ''
        }]
        return drives
    
    