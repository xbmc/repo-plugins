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

import base64
import json
import posixpath
import urllib

from clouddrive.common.remote.provider import Provider
from clouddrive.common.ui.logger import Logger
from clouddrive.common.utils import Utils


class Dropbox(Provider):
    folder_paging_supported = True
    _CONTENT_URL = 'https://content.dropboxapi.com/2'
    _SUBTITLE_EXTENSIONS = ('srt', 'idx', 'sub', 'sbv', 'ass', 'ssa', 'smi', 'vtt')
    # Search results are paged; stop after this many pages.
    _MAX_SEARCH_PAGES = 5
    _MAX_LINK_SEARCH_FOLDERS = 100
    SHARED_WITH_ME = 'sharedWithMe'
    # What's shared with the user and not in their Dropbox is reached through its shared link: these items' ids are
    # the link and the path inside it. Ids go in download URL paths, so they are encoded without '/'.
    _LINK_ID = 'link:'

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

    @staticmethod
    def _link_id(url, path=''):
        return Dropbox._LINK_ID + base64.urlsafe_b64encode(json.dumps([url, path]).encode('utf-8')).decode('ascii')

    @staticmethod
    def _parse_link_id(item_id):
        # (url, path inside the link), or None for any other id.
        if not item_id or not item_id.startswith(Dropbox._LINK_ID):
            return None
        url, path = json.loads(base64.urlsafe_b64decode(item_id[len(Dropbox._LINK_ID):].encode('ascii')).decode('utf-8'))
        return url, path

    def _list_args(self, item_id=None, path=None):
        link = self._parse_link_id(item_id)
        if link:
            return {'path': link[1], 'shared_link': {'url': link[0]}}
        return {'path': self._api_path(item_id, path)}

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
        if path == self.SHARED_WITH_ME:
            return self._shared_with_me(on_items_page_completed, include_download_info, on_before_add_item)
        # When the folder is known by id, its children get it as parent: library exports link items by parent id.
        return self._list_folder(self._list_args(item_id, path), item_id, on_items_page_completed, include_download_info, on_before_add_item)

    def _list_folder(self, args, parent=None, on_items_page_completed=None, include_download_info=False, on_before_add_item=None):
        items = []
        response = self._rpc('/files/list_folder', dict(args, limit=2000))
        while response:
            page = self._page_items(response, parent, include_download_info, on_before_add_item, args)
            if self.cancel_operation():
                return
            if on_items_page_completed:
                on_items_page_completed(page)
            items.extend(page)
            response = self._rpc('/files/list_folder/continue', {'cursor': response['cursor']}) if Utils.get_safe_value(response, 'has_more') else None
        return items

    def _page_items(self, response, parent=None, include_download_info=False, on_before_add_item=None, args=None):
        page = []
        link = Utils.get_safe_value(args or {}, 'shared_link')
        for entry in Utils.get_safe_value(response, 'entries', []):
            if Utils.get_safe_value(entry, '.tag') not in ('file', 'folder'):
                continue
            if link:
                entry = dict(entry, id=self._link_id(link['url'], args['path'] + '/' + Utils.get_safe_value(entry, 'name', '')))
            item = self._extract_item(entry, include_download_info, parent)
            if on_before_add_item:
                on_before_add_item(item)
            page.append(item)
        return page

    def get_folder_page(self, item_driveid=None, item_id=None, path=None, page_size=500, page_token=None, on_items_page_completed=None):
        # Dropbox can't sort a listing: pages come in its order, each one sorted by Kodi.
        if path == self.SHARED_WITH_ME:
            # Not paged: what's shared is listed whole.
            items = self._shared_with_me(on_items_page_completed)
            return None if items is None else (items, None)
        args = self._list_args(item_id, path)
        if page_token:
            response = self._rpc('/files/list_folder/continue', {'cursor': page_token})
        else:
            response = self._rpc('/files/list_folder', dict(args, limit=page_size))
        # A link's cursor goes on listing that link: its items are named the same way.
        page = self._page_items(response, item_id, args=args)
        if self.cancel_operation():
            return
        if on_items_page_completed:
            on_items_page_completed(page)
        return page, response['cursor'] if Utils.get_safe_value(response, 'has_more') else None

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
            link = self._parse_link_id(entry['id'])
            if link:
                route, arg = '/sharing/get_shared_link_file', {'url': link[0], 'path': link[1]} if link[1] else {'url': link[0]}
            else:
                route, arg = '/files/download', {'path': entry['id']}
            item['download_info'] = {
                'url': self._CONTENT_URL + route + '?' + urllib.parse.urlencode({'arg': json.dumps(arg, separators=(',', ':'))})
            }
        return item

    def _shared_with_me(self, on_items_page_completed=None, include_download_info=False, on_before_add_item=None):
        # The folders and files others share with the user. Those added to the user's Dropbox are reached by their
        # path or id, the rest through their shared link.
        items = []
        for route, arg in (('/sharing/list_folders', {'limit': 1000}), ('/sharing/list_received_files', {'limit': 300})):
            response = self._rpc(route, arg)
            while response:
                page = []
                for entry in Utils.get_safe_value(response, 'entries', []):
                    folder = route == '/sharing/list_folders'
                    if folder and Utils.get_safe_value(entry, 'access_type', {}).get('.tag') == 'owner':
                        # Shared by the user.
                        continue
                    path = Utils.get_safe_value(entry, 'path_lower')
                    if path:
                        item_id = path if folder else entry['id']
                    else:
                        item_id = self._link_id(entry['preview_url'])
                    item = self._extract_item({'.tag': 'folder' if folder else 'file', 'id': item_id, 'name': entry['name'], 'path_lower': path,
                                               'server_modified': Utils.get_safe_value(entry, 'time_invited')}, include_download_info)
                    if on_before_add_item:
                        on_before_add_item(item)
                    page.append(item)
                if self.cancel_operation():
                    return
                if on_items_page_completed:
                    on_items_page_completed(page)
                items.extend(page)
                cursor = Utils.get_safe_value(response, 'cursor')
                response = self._rpc(route + '/continue', {'cursor': cursor}) if cursor else None
        return items

    def list_subtree(self, item_driveid, item_id):
        # One recursive, paged listing for a whole tree (library exports), mapped back to folder ids by path.
        if self._parse_link_id(item_id):
            # Dropbox lists shared links one folder at a time.
            return None
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
        if self._parse_link_id(item_id):
            return self._search_link(query, item_id, on_items_page_completed)
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

    def _search_link(self, query, item_id, on_items_page_completed=None):
        # Dropbox doesn't search shared links: their folders are walked, up to _MAX_LINK_SEARCH_FOLDERS.
        query = Utils.str(query).lower()
        items = []
        folders = [item_id]
        for _ in range(self._MAX_LINK_SEARCH_FOLDERS):
            if not folders:
                break
            children = self.get_folder_items(item_id=folders.pop(0))
            if children is None:
                return
            page = [child for child in children if query in child['name'].lower()]
            folders.extend(child['id'] for child in children if 'folder' in child)
            if on_items_page_completed:
                on_items_page_completed(page)
            items.extend(page)
        return items

    def get_subtitles(self, parent, name, item_driveid=None, include_download_info=False):
        # Subtitle files in the same folder named after the video, e.g. "movie.srt" or "movie.en.srt" (not "movie2.srt").
        if parent is None:
            return []
        prefix = Utils.remove_extension(name).lower() + '.'
        subtitles = []
        # None when the operation was cancelled.
        items = self._list_folder(self._list_args(parent, None) if self._parse_link_id(parent) else {'path': self._api_path(None, parent)}, None,
                                  include_download_info=include_download_info) or []
        for item in items:
            if 'folder' not in item and item['name'].lower().startswith(prefix) and Utils.default(item['name_extension'], '').lower() in self._SUBTITLE_EXTENSIONS:
                subtitles.append(item)
        return subtitles

    def get_item(self, item_driveid=None, item_id=None, path=None, find_subtitles=False, include_download_info=False):
        link = self._parse_link_id(item_id)
        if link:
            entry = self._rpc('/sharing/get_shared_link_metadata', {'url': link[0], 'path': link[1]} if link[1] else {'url': link[0]})
            item = self._extract_item(dict(entry, id=item_id), include_download_info)
            if link[1]:
                item['parent'] = self._link_id(link[0], posixpath.dirname(link[1]).rstrip('/'))
            if find_subtitles and 'folder' not in item and link[1]:
                subtitles = self.get_subtitles(item['parent'], item['name'], item_driveid, include_download_info)
                if subtitles:
                    item['subtitles'] = subtitles
            return item
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
