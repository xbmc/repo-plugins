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

import datetime
import urllib

from clouddrive.common.cache.simplecache import SimpleCache
from clouddrive.common.ui.addon import CloudDriveAddon
from clouddrive.common.utils import Utils
from resources.lib.provider.googledrive import GoogleDrive
from urllib2 import HTTPError


class GoogleDriveAddon(CloudDriveAddon):
    _provider = GoogleDrive()
    _parameters = {'spaces': 'drive', 'prettyPrint': 'false'}
    _file_fileds = 'id,name,mimeType,description,hasThumbnail,thumbnailLink,modifiedTime,owners(permissionId),parents,size,imageMediaMetadata(width),videoMediaMetadata'
    _cache = None
    _child_count_supported = False
    _change_token = None
    _extension_map = {
        'html' : 'text/html',
        'htm' : 'text/html',
        'txt' : 'text/plain',
        'rtf' : 'application/rtf',
        'odf' : 'application/vnd.oasis.opendocument.text',
        'pdf' : 'application/pdf',
        'doc' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'docx' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'epub' : 'application/epub+zip',
        'xls' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'sxc' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'csv' : 'text/csv',
        'ppt' : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'pptx' : 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'sxi' : 'application/vnd.oasis.opendocument.presentation',
        'json' : 'application/vnd.google-apps.script+json'
    }    
    def __init__(self):
        self._cache = SimpleCache()
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
            response = self._provider.get('/changes/startPageToken', parameters = self._parameters)
            self._change_token = Utils.get_safe_value(response, 'startPageToken')
            change_token = 1
        else:
            page_token = self._change_token
            while page_token:
                self._parameters['pageToken'] = page_token
                self._parameters['fields'] = 'nextPageToken,newStartPageToken,changes(file(id,name,parents))'
                response = self._provider.get('/changes', parameters = self._parameters)
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
    
    def get_folder_items(self, driveid, item_driveid=None, item_id=None, path=None, on_items_page_completed=None):
        self._provider.configure(self._account_manager, driveid)
        item_driveid = Utils.default(item_driveid, driveid)
        self._parameters['fields'] = 'files(%s),nextPageToken' % self._file_fileds
        if item_id:
            self._parameters['q'] = '\'%s\' in parents' % item_id
        elif path == 'sharedWithMe' or path == 'starred':
            self._parameters['q'] = path
        elif path == 'photos':
            self._parameters['spaces'] = path
        else:
            if path == '/':
                self._parameters['q'] = '\'root\' in parents'
            else:
                item = self.get_item_by_path(path)
                self._parameters['q'] = '\'%s\' in parents' % item['id']
        files = self._provider.get('/files', parameters = self._parameters)
        if self.cancel_operation():
            return
        return self.process_files(driveid, files, on_items_page_completed)
    
    def search(self, query, driveid, item_driveid=None, item_id=None, on_items_page_completed=None):
        self._provider.configure(self._account_manager, driveid)
        item_driveid = Utils.default(item_driveid, driveid)
        self._parameters['fields'] = 'files(%s)' % self._file_fileds
        query = 'fullText contains \'%s\'' % query
        if item_id:
            query += ' and \'%s\' in parents' % item_id
        self._parameters['q'] = query
        files = self._provider.get('/files', parameters = self._parameters)
        if self.cancel_operation():
            return
        return self.process_files(driveid, files, on_items_page_completed)
    
    def process_files(self, driveid, files, on_items_page_completed=None):
        items = []
        for f in files['files']:
            item = self._extract_item(f)
            cache_key = self._addonid+'-drive-'+driveid+'-item_driveid-'+item['drive_id']+'-item_id-'+item['id']+'-path-None'
            self._cache.set(cache_key, f, expiration=datetime.timedelta(minutes=1))
            items.append(item)
        if on_items_page_completed:
            on_items_page_completed(items)
        if 'nextPageToken' in files:
            self._parameters['pageToken'] = files['nextPageToken']
            next_files = self._provider.get('/files', parameters = self._parameters)
            if self.cancel_operation():
                return
            items.extend(self.process_files(driveid, next_files, on_items_page_completed))
        return items
    
    def _extract_item(self, f, include_download_info=False):
        size = long('%s' % Utils.get_safe_value(f, 'size', 0))
        item = {
            'id': f['id'],
            'name': f['name'],
            'name_extension' : Utils.get_extension(f['name']),
            'drive_id' : Utils.get_safe_value(Utils.get_safe_value(f, 'owners', [{}])[0], 'permissionId'),
            'mimetype' : Utils.get_safe_value(f, 'mimeType', ''),
            'last_modified_date' : Utils.get_safe_value(f,'modifiedTime'),
            'size': size,
            'description': Utils.get_safe_value(f, 'description', '')
        }
        if item['mimetype'] == 'application/vnd.google-apps.folder':
            item['folder'] = {
                'child_count' : 0
            }
        if 'videoMediaMetadata' in f:
            video = f['videoMediaMetadata']
            item['video'] = {
                'width' : Utils.get_safe_value(video, 'width'),
                'height' : Utils.get_safe_value(video, 'height'),
                'duration' : long('%s' % Utils.get_safe_value(video, 'durationMillis', 0)) / 1000
            }
        if 'imageMediaMetadata' in f:
            item['image'] = {
                'size' : size
            }
        if 'hasThumbnail' in f and f['hasThumbnail']:
            item['thumbnail'] = Utils.get_safe_value(f, 'thumbnailLink')
        if include_download_info:
            parameters = {
                'alt': 'media',
                'access_token': self._provider.get_access_tokens()['access_token']
            }
            url = self._provider._get_api_url() + '/files/%s' % item['id']
            if 'size' not in f and item['mimetype'] == 'application/vnd.google-apps.document':
                url += '/export'
                parameters['mimeType'] = self.get_mimetype_by_extension(item['name_extension'])
            item['download_info'] =  {
                'url' : url + '?%s' % urllib.urlencode(parameters)
            }
        return item
    
    def get_mimetype_by_extension(self, extension):
        if extension and extension in self._extension_map:
            return self._extension_map[extension]
        return self._extension_map['pdf']
    
    def get_item_by_path(self, path, include_download_info=False):
        if path[:1] == '/':
            path = path[1:]
        if path[-1:] == '/':
            path = path[:-1]
        parts = path.split('/')
        parent = 'root'
        current_path = ''
        item = None
        self._parameters['fields'] = 'files(%s)' % self._file_fileds
        for part in parts:
            part = urllib.unquote(part)
            current_path += '/%s' % part
            self._parameters['q'] = '\'%s\' in parents and name = \'%s\'' % (parent, part)
            files = self._provider.get('/files', parameters = self._parameters)
            if (len(files['files']) > 0):
                for f in files['files']:
                    item = self._extract_item(f, include_download_info)
                    parent = item['id']
                    cache_key = self._addonid+'-drive-None-item_driveid-None-item_id-None-path-'+current_path
                    self._cache.set(cache_key, f, expiration=datetime.timedelta(minutes=1))
                    break
            else:
                item = None
                break
        if not item:
            raise HTTPError(path, 404, 'Not found', None, None)
        return item
    
    def get_item(self, driveid, item_driveid=None, item_id=None, path=None, find_subtitles=False, include_download_info=False):
        self._provider.configure(self._account_manager, driveid)
        item_driveid = Utils.default(item_driveid, driveid)
        cache_key = self._addonid+'-drive-'+driveid+'-item_driveid-'+Utils.str(item_driveid)+'-item_id-'+Utils.str(item_id)+'-path-'+Utils.str(path)
        f = self._cache.get(cache_key)
        if f:
            item = self._extract_item(f, include_download_info)
        else:
            cache_key = self._addonid+'-drive-None-item_driveid-None-item_id-None-path-'+path
            f = self._cache.get(cache_key)
            if f:
                item = self._extract_item(f, include_download_info)
            else:
                self._parameters['fields'] = self._file_fileds
                if not item_id and path == '/':
                    item_id = 'root'
                if item_id:
                    f = self._provider.get('/files/%s' % item_id, parameters = self._parameters)
                    self._cache.set(cache_key, f, expiration=datetime.timedelta(seconds=59))
                    item = self._extract_item(f, include_download_info)
                else:
                    item = self.get_item_by_path(path, include_download_info)
        
        if find_subtitles:
            subtitles = []
            self._parameters['q'] = 'name contains \'%s\'' % urllib.quote(Utils.remove_extension(item['name']))
            files = self._provider.get('/files', parameters = self._parameters)
            for f in files['files']:
                subtitle = self._extract_item(f, include_download_info)
                if subtitle['name_extension'] == 'srt' or subtitle['name_extension'] == 'sub' or subtitle['name_extension'] == 'sbv':
                    subtitles.append(subtitle)
            if subtitles:
                item['subtitles'] = subtitles
        return item
    
if __name__ == '__main__':
    GoogleDriveAddon().route()

