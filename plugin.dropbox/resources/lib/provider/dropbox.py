#-------------------------------------------------------------------------------
# Copyright (C) 2017 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
#
# This file is part of Dropbox for Kodi
#
# Dropbox for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dropbox for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import json
import posixpath
import urllib

from clouddrive.common.remote.provider import Provider
from clouddrive.common.ui.logger import Logger
from clouddrive.common.utils import Utils


class Dropbox(Provider):
    _CONTENT_URL = 'https://content.dropboxapi.com/2'
    _SUBTITLE_EXTENSIONS = ('srt', 'idx', 'sub', 'sbv', 'ass', 'ssa', 'smi', 'vtt')
    # Search results are paged; stop after this many pages.
    _MAX_SEARCH_PAGES = 5

    def __init__(self, source_mode=False):
        super(Dropbox, self).__init__('dropbox', source_mode)
        # Files are downloaded from the API with the Authorization header, never through pre-authenticated links.
        self.download_requires_auth = True

    def _get_api_url(self):
        return 'https://api.dropboxapi.com/2'

    def _get_request_headers(self):
        # No default Content-Type: the download endpoint rejects a JSON one. The API calls set it in _rpc.
        return None

    revoke_supported = True
    signin_company = 'Dropbox'
    # Revoking ends only this device's sign-in: other devices have their own refresh tokens.
    revoke_ends_all_sign_ins = False

    def revoke_access(self):
        # Disables the access token, the refresh token it came from, and every access token issued with it.
        request = self.prepare_request('post', '/auth/token/revoke', {}, None, None, {'content-type': 'application/json'})
        request.data = b'null'
        request.request()

    def _rpc(self, path, args=None, request_params=None, access_tokens=None):
        # Dropbox's API calls are POSTs with a JSON body; calls without arguments take "null".
        request = self.prepare_request('post', path, Utils.default(args, {}), request_params, access_tokens, {'content-type': 'application/json'})
        if args is None:
            request.data = b'null'
        return request.request_json()

    @staticmethod
    def _api_path(item_id=None, path=None):
        # Items are addressed by id ("id:...") or by path. The root folder is the empty path.
        if item_id:
            return item_id
        if not path or path == '/':
            return ''
        return path if path.startswith('/') or path.startswith('id:') else '/' + path

    def get_account(self, request_params=None, access_tokens=None):
        me = self._rpc('/users/get_current_account', request_params=request_params, access_tokens=access_tokens)
        if not me:
            raise Exception('NoAccountInfo')
        name = Utils.get_safe_value(Utils.get_safe_value(me, 'name', {}), 'display_name')
        return {'id': me['account_id'], 'name': Utils.default(name, Utils.get_safe_value(me, 'email', me['account_id']))}

    def get_drives(self, request_params=None, access_tokens=None):
        me = self._rpc('/users/get_current_account', request_params=request_params, access_tokens=access_tokens)
        return [{
            'id': me['account_id'],
            'name': '',
            'type': Utils.get_safe_value(Utils.get_safe_value(me, 'account_type', {}), '.tag', 'basic')
        }]

    def get_drive_type_name(self, drive_type):
        # "pro" covers the paid personal plans (Plus, Essentials, Professional).
        return Utils.get_safe_value({'basic': 'Dropbox Basic', 'pro': 'Dropbox', 'business': 'Dropbox Business'}, drive_type, drive_type)

    def get_folder_items(self, item_driveid=None, item_id=None, path=None, on_items_page_completed=None, include_download_info=False, on_before_add_item=None):
        # When the folder is known by id, its children get it as parent: library exports link items by parent id.
        return self._list_folder(self._api_path(item_id, path), item_id, on_items_page_completed, include_download_info, on_before_add_item)

    def _list_folder(self, api_path, parent=None, on_items_page_completed=None, include_download_info=False, on_before_add_item=None):
        items = []
        response = self._rpc('/files/list_folder', {'path': api_path, 'limit': 2000})
        while response:
            page = []
            for entry in Utils.get_safe_value(response, 'entries', []):
                if Utils.get_safe_value(entry, '.tag') not in ('file', 'folder'):
                    continue
                item = self._extract_item(entry, include_download_info, parent)
                if on_before_add_item:
                    on_before_add_item(item)
                page.append(item)
            if self.cancel_operation():
                return
            if on_items_page_completed:
                on_items_page_completed(page)
            items.extend(page)
            response = self._rpc('/files/list_folder/continue', {'cursor': response['cursor']}) if Utils.get_safe_value(response, 'has_more') else None
        return items

    def _extract_item(self, entry, include_download_info=False, parent=None):
        name = Utils.get_safe_value(entry, 'name', '')
        path = Utils.get_safe_value(entry, 'path_lower')
        item = {
            'id': entry['id'],
            'name': name,
            'name_extension': Utils.get_extension(name),
            'path': path,
            # The parent folder's id when known, otherwise its path: both work as a Dropbox path.
            'parent': parent if parent else (posixpath.dirname(path) if path else None),
            'last_modified_date': Utils.get_safe_value(entry, 'server_modified'),
            'size': Utils.get_safe_value(entry, 'size', 0)
        }
        if entry['.tag'] == 'folder':
            item['folder'] = {'child_count': 0}
        elif include_download_info:
            item['download_info'] = {
                'url': self._CONTENT_URL + '/files/download?' + urllib.parse.urlencode({'arg': json.dumps({'path': entry['id']}, separators=(',', ':'))})
            }
        return item

    def list_subtree(self, item_driveid, item_id):
        # One recursive, paged listing for a whole tree (library exports), mapped back to folder ids by path.
        api_path = self._api_path(item_id)
        entries = []
        response = self._rpc('/files/list_folder', {'path': api_path, 'recursive': True, 'limit': 2000})
        while response:
            if self.cancel_operation():
                return None
            entries.extend(e for e in Utils.get_safe_value(response, 'entries', []) if Utils.get_safe_value(e, '.tag') in ('file', 'folder'))
            response = self._rpc('/files/list_folder/continue', {'cursor': response['cursor']}) if Utils.get_safe_value(response, 'has_more') else None
        # The listing includes the folder itself; the root of the Dropbox has the empty path.
        root_path = next((e['path_lower'] for e in entries if e['id'] == item_id), None)
        if root_path is None:
            root_path = Utils.get_safe_value(self._rpc('/files/get_metadata', {'path': api_path}), 'path_lower', '') if api_path else ''
        folder_ids = {root_path: item_id}
        for e in entries:
            if e['.tag'] == 'folder':
                folder_ids.setdefault(e['path_lower'], e['id'])
        tree = {folder_id: [] for folder_id in folder_ids.values()}
        for e in entries:
            if e['path_lower'] == root_path:
                continue
            parent_path = posixpath.dirname(e['path_lower'])
            parent = folder_ids.get('' if parent_path == '/' else parent_path)
            if parent is not None:
                tree[parent].append(self._extract_item(e, True, parent))
        return tree

    def search(self, query, item_driveid=None, item_id=None, on_items_page_completed=None):
        options = {'file_status': 'active', 'max_results': 1000}
        if item_id:
            options['path'] = item_id
        items = []
        response = self._rpc('/files/search_v2', {'query': Utils.str(query), 'options': options})
        pages = 0
        while response:
            page = []
            for match in Utils.get_safe_value(response, 'matches', []):
                metadata = Utils.get_safe_value(match, 'metadata', {})
                entry = Utils.get_safe_value(metadata, 'metadata', {})
                if Utils.get_safe_value(metadata, '.tag') == 'metadata' and Utils.get_safe_value(entry, '.tag') in ('file', 'folder'):
                    page.append(self._extract_item(entry))
            if self.cancel_operation():
                return
            if on_items_page_completed:
                on_items_page_completed(page)
            items.extend(page)
            pages += 1
            more = Utils.get_safe_value(response, 'has_more')
            if more and pages >= self._MAX_SEARCH_PAGES:
                Logger.notice('Search for "%s" stopped after %d results; Dropbox has more matches.' % (Utils.str(query), len(items)))
                more = False
            response = self._rpc('/files/search/continue_v2', {'cursor': response['cursor']}) if more else None
        return items

    def get_subtitles(self, parent, name, item_driveid=None, include_download_info=False):
        # Subtitle files in the same folder named after the video, e.g. "movie.srt" or "movie.en.srt" (not "movie2.srt").
        if parent is None:
            return []
        prefix = Utils.remove_extension(name).lower() + '.'
        subtitles = []
        # None when the operation was cancelled.
        items = self._list_folder(self._api_path(None, parent), None, include_download_info=include_download_info) or []
        for item in items:
            if 'folder' not in item and item['name'].lower().startswith(prefix) and Utils.default(item['name_extension'], '').lower() in self._SUBTITLE_EXTENSIONS:
                subtitles.append(item)
        return subtitles

    def get_item(self, item_driveid=None, item_id=None, path=None, find_subtitles=False, include_download_info=False):
        api_path = self._api_path(item_id, path)
        if not api_path:
            # The root folder has no metadata.
            return {'id': '', 'name': '', 'name_extension': '', 'path': '', 'parent': None, 'size': 0, 'folder': {'child_count': 0}}
        entry = self._rpc('/files/get_metadata', {'path': api_path})
        item = self._extract_item(entry, include_download_info)
        if find_subtitles and 'folder' not in item:
            subtitles = self.get_subtitles(item['parent'], item['name'], item_driveid, include_download_info)
            if subtitles:
                item['subtitles'] = subtitles
        return item
