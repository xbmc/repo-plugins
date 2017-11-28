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

import datetime
import urllib

from clouddrive.common.cache.simplecache import SimpleCache
from clouddrive.common.ui.addon import CloudDriveAddon
from clouddrive.common.utils import Utils
from resources.lib.provider.onedrive import OneDrive
from clouddrive.common.ui.utils import KodiUtils
from resources.lib.migration import MigrateAccounts


class OneDriveAddon(CloudDriveAddon):
    _provider = OneDrive()
    _extra_parameters = {'expand': 'thumbnails'}
    _cache = None
    
    def __init__(self):
        self._cache = SimpleCache()
        super(OneDriveAddon, self).__init__()
        
    def get_provider(self):
        return self._provider
    
    def get_custom_drive_folders(self, driveid):
        self._account_manager.load()
        drive = self._account_manager.get_drive_by_driveid(driveid)
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

    def get_folder_items(self, driveid, item_driveid=None, item_id=None, path=None, on_items_page_completed=None):
        self._provider.configure(self._account_manager, driveid)
        item_driveid = Utils.default(item_driveid, driveid)
        if item_id:
            files = self._provider.get('/drives/'+item_driveid+'/items/' + item_id + '/children', parameters = self._extra_parameters)
        elif path == 'sharedWithMe' or path == 'recent':
            files = self._provider.get('/drives/'+driveid+'/' + path)
        else:
            if path == '/':
                path = 'root'
            else:
                parts = path.split('/')
                if len(parts) > 1 and not parts[0]:
                    path = 'root:'+path+':'
            files = self._provider.get('/drives/'+driveid+'/' + path + '/children', parameters = self._extra_parameters)
        if self.cancel_operation():
            return
        return self.process_files(driveid, files, on_items_page_completed)
    
    def search(self, query, driveid, item_driveid=None, item_id=None, on_items_page_completed=None):
        self._provider.configure(self._account_manager, driveid)
        item_driveid = Utils.default(item_driveid, driveid)
        url = '/drives/'
        if item_id:
            url += item_driveid+'/items/' + item_id
        else:
            url += driveid
        url += '/search(q=\''+urllib.quote(query)+'\')'
        self._extra_parameters['filter'] = 'file ne null'
        files = self._provider.get(url, parameters = self._extra_parameters)
        if self.cancel_operation():
            return
        return self.process_files(driveid, files, on_items_page_completed)
    
    def process_files(self, driveid, files, on_items_page_completed=None):
        items = []
        for f in files['value']:
            f = Utils.get_safe_value(f, 'remoteItem', f)
            item = self._extract_item(f)
            cache_key = self._addonid+'-drive-'+driveid+'-item_driveid-'+item['drive_id']+'-item_id-'+item['id']+'-path-None'
            self._cache.set(cache_key, f, expiration=datetime.timedelta(minutes=1))
            items.append(item)
        if on_items_page_completed:
            on_items_page_completed(items)
        if '@odata.nextLink' in files:
            next_files = self._provider.get(files['@odata.nextLink'])
            if self.cancel_operation():
                return
            items.extend(self.process_files(driveid, next_files, on_items_page_completed))
        return items
    
    def _extract_item(self, f, include_download_info=False):
        item = {
            'id': f['id'],
            'name': f['name'],
            'name_extension' : Utils.get_extension(f['name']),
            'drive_id' : Utils.get_safe_value(Utils.get_safe_value(f, 'parentReference', {}), 'driveId'),
            'mimetype' : Utils.get_safe_value(Utils.get_safe_value(f, 'file', {}), 'mimeType'),
            'last_modified_date' : Utils.get_safe_value(f,'lastModifiedDateTime'),
            'size': Utils.get_safe_value(f, 'size', 0),
            'description': Utils.get_safe_value(f, 'description', '')
        }
        if 'folder' in f:
            item['folder'] = {
                'child_count' : Utils.get_safe_value(f['folder'],'childCount',0)
            }
        if 'video' in f:
            video = f['video']
            item['video'] = {
                'width' : Utils.get_safe_value(video,'width', 0),
                'height' : Utils.get_safe_value(video, 'height', 0),
                'duration' : Utils.get_safe_value(video, 'duration', 0) /1000
            }
        if 'audio' in f:
            audio = f['audio']
            item['audio'] = {
                'tracknumber' : Utils.get_safe_value(audio, 'track'),
                'discnumber' : Utils.get_safe_value(audio, 'disc'),
                'duration' : int(Utils.get_safe_value(audio, 'duration') or '0') / 1000,
                'year' : Utils.get_safe_value(audio, 'year'),
                'genre' : Utils.get_safe_value(audio, 'genre'),
                'album': Utils.get_safe_value(audio, 'album'),
                'artist': Utils.get_safe_value(audio, 'artist'),
                'title': Utils.get_safe_value(audio, 'title')
            }
        if 'image' in f or 'photo' in f:
            item['image'] = {
                'size' : Utils.get_safe_value(f, 'size', 0)
            }
        if 'thumbnails' in f and type(f['thumbnails']) == list and len(f['thumbnails']) > 0:
            thumbnails = f['thumbnails'][0]
            item['thumbnail'] = Utils.get_safe_value(Utils.get_safe_value(thumbnails, 'large', {}), 'url', '')
        if include_download_info:
            item['download_info'] =  {
                'url' : Utils.get_safe_value(f,'@microsoft.graph.downloadUrl')
            }
        return item
    
    def get_item(self, driveid, item_driveid=None, item_id=None, path=None, find_subtitles=False, include_download_info=False):
        self._provider.configure(self._account_manager, driveid)
        item_driveid = Utils.default(item_driveid, driveid)
        cache_key = self._addonid+'-drive-'+driveid+'-item_driveid-'+Utils.str(item_driveid)+'-item_id-'+Utils.str(item_id)+'-path-'+Utils.str(path)
        f = self._cache.get(cache_key)
        if not f :
            if item_id:
                f = self._provider.get('/drives/'+item_driveid+'/items/' + item_id, parameters = self._extra_parameters)
            elif path == 'sharedWithMe' or path == 'recent':
                return
            else:
                if path == '/':
                    path = 'root'
                else:
                    parts = path.split('/')
                    if len(parts) > 1 and not parts[0]:
                        path = 'root:'+path+':'
                f = self._provider.get('/drives/'+driveid+'/' + path, parameters = self._extra_parameters)
            self._cache.set(cache_key, f, expiration=datetime.timedelta(seconds=59))
        item = self._extract_item(f, include_download_info)
        if find_subtitles:
            subtitles = []
            parent_id = Utils.get_safe_value(Utils.get_safe_value(f, 'parentReference', {}), 'id')
            search_url = '/drives/'+item_driveid+'/items/' + parent_id + '/search(q=\'{'+urllib.quote(Utils.remove_extension(item['name']))+'}\')'
            files = self._provider.get(search_url)
            for f in files['value']:
                subtitle = self._extract_item(f, include_download_info)
                if subtitle['name_extension'] == 'srt' or subtitle['name_extension'] == 'sub' or subtitle['name_extension'] == 'sbv':
                    subtitles.append(subtitle)
            if subtitles:
                item['subtitles'] = subtitles
        return item
    
    def _rename_action(self):
        self._action = Utils.get_safe_value({
            'open_folder': '_list_folder',
            'open_drive': '_list_drive',
        }, self._action, self._action)

if __name__ == '__main__':
    onedrive_addon = OneDriveAddon()
    if not KodiUtils.get_addon_setting('migrated'):
        try:
            MigrateAccounts()
        except Exception as e:
            onedrive_addon._handle_exception(e, False)
    onedrive_addon.route()

