#-------------------------------------------------------------------------------
# Copyright (C) 2026 Carlos Guzman (cguZZman) carlosguzmang@protonmail.com
#
# This file is part of pCloud for Kodi
#
# pCloud for Kodi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pCloud for Kodi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------

import datetime
import json
from urllib.error import HTTPError

from clouddrive.common.exception import RequestException
from clouddrive.common.remote.provider import Provider
from clouddrive.common.ui.logger import Logger
from clouddrive.common.utils import Utils


class PCloud(Provider):
    """
    pCloud's API (https://docs.pcloud.com). Each account lives in one region, with its own API host: the sign-in
    server hands Kodi the host with the token ('hostname': api.pcloud.com in the US, eapi.pcloud.com in Europe).
    Access tokens don't expire, so there's nothing to refresh. Errors come with HTTP 200 and a nonzero 'result'.
    Items are pCloud's ids: 'd<folderid>' for folders ('d0' is the root) and 'f<fileid>' for files.
    """
    _HOSTS = ('api.pcloud.com', 'eapi.pcloud.com')
    _ROOT = 'd0'
    _SUBTITLE_EXTENSIONS = ('srt', 'idx', 'sub', 'sbv', 'ass', 'ssa', 'smi', 'vtt')
    # Not documented, but pCloud answers it (as in the tomgross/pcloud library). Results are capped.
    _SEARCH_LIMIT = 1000
    # The undocumented search can disappear: then the tree is walked instead, up to this many folders.
    _MAX_WALK_FOLDERS = 200
    # Stands in for "never": pCloud's tokens don't expire, but clouddrive.common renews tokens near their expiry.
    _NEVER_EXPIRES_S = 100 * 365 * 24 * 60 * 60
    # pCloud's result codes that mean the token is no longer good: answered as HTTP 401, so Kodi asks to sign in again.
    # 1000 log in required, 2000 log in failed, 2094 invalid access_token, 2095 access_token expired or revoked.
    _AUTH_ERRORS = (1000, 2000, 2094, 2095)
    # 2002 a component of the parent directory does not exist, 2005 directory does not exist, 2009 file not found.
    _NOT_FOUND_ERRORS = (2002, 2005, 2009)
    # Library exports download these files from the listing's download_info (clouddrive.common's export service):
    # .strm and .nomedia always; .nfo, and artwork pictures named like these or in these folders, with "Download
    # artwork". Only they get a link in listings: each costs a request.
    _EXPORT_DOWNLOADS = ('strm', 'nomedia', 'nfo')
    _ARTWORK_NAMES = ('back', 'banner', 'characterart', 'clearart', 'clearlogo', 'discart', 'fanart', 'keyart', 'landscape', 'poster',
                      'spine', 'thumb', 'folder', 'cover', 'animatedposter', 'animatedfanart')
    _ARTWORK_FOLDERS = ('.actors', 'extrafanart')

    def __init__(self, source_mode=False):
        super(PCloud, self).__init__('pcloud', source_mode)
        # getfilelink answers pre-authenticated links: they must not get the Authorization header.
        self.download_requires_auth = False

    def _get_api_url(self):
        # Every call passes its full URL, with the account's host (_api): this is only the base clouddrive.common
        # builds first. It must not read the account's tokens: while an account is being added, there is none yet.
        return 'https://' + self._HOSTS[0]

    def _get_request_headers(self):
        return None

    def _host(self, access_tokens=None):
        tokens = access_tokens if access_tokens else self.get_access_tokens()
        host = Utils.get_safe_value(tokens, 'hostname')
        return host if host in self._HOSTS else self._HOSTS[0]

    def fetch_tokens_info(self, pin_info, request_params=None):
        # The sign-in server's answer has no refresh token or expiry: pCloud's tokens don't expire.
        tokens_info = super(PCloud, self).fetch_tokens_info(pin_info, request_params)
        if tokens_info:
            tokens_info.setdefault('refresh_token', '')
            tokens_info.setdefault('expires_in', self._NEVER_EXPIRES_S)
        return tokens_info

    def refresh_access_tokens(self, request_params=None):
        # Never reached with the tokens above. If it is, the account has to sign in again.
        raise RequestException('pCloud tokens are not refreshed', HTTPError('pcloud', 401, 'Sign in again', None, None),
                               'Request URL: (none: pCloud tokens are not refreshed)', '{"error": "Sign in again"}')

    def _api(self, method, parameters=None, request_params=None, access_tokens=None):
        """Calls an API method (GET, parameters in the URL) and returns its answer, or raises for a nonzero result."""
        parameters = dict(Utils.default(parameters, {}))
        # Unix timestamps instead of RFC 2822 dates.
        parameters['timeformat'] = 'timestamp'
        url = 'https://%s/%s' % (self._host(access_tokens), method)
        response = self.prepare_request('get', url, parameters, request_params, access_tokens).request_json()
        result = Utils.get_safe_value(response, 'result', 0)
        if result:
            if result in self._AUTH_ERRORS:
                code = 401
            elif result in self._NOT_FOUND_ERRORS:
                code = 404
            elif 4000 <= result < 6000:
                # 4xxx: too many requests; 5xxx: pCloud can't answer now. Both are worth retrying later.
                code = 503
            else:
                code = 400
            message = Utils.get_safe_value(response, 'error', '')
            raise RequestException('pCloud error %s: %s' % (result, message), HTTPError(url, code, message, None, None),
                                   'Request URL: %s' % url, json.dumps({'result': result, 'error': message}))
        return response

    def get_account(self, request_params=None, access_tokens=None):
        me = self._api('userinfo', request_params=request_params, access_tokens=access_tokens)
        user_id = Utils.str(me['userid'])
        return {'id': user_id, 'name': Utils.get_safe_value(me, 'email', user_id)}

    def get_drives(self, request_params=None, access_tokens=None):
        me = self._api('userinfo', request_params=request_params, access_tokens=access_tokens)
        if Utils.get_safe_value(me, 'business'):
            drive_type = 'business'
        elif Utils.get_safe_value(me, 'premium') or Utils.get_safe_value(me, 'premiumlifetime'):
            drive_type = 'premium'
        else:
            drive_type = 'free'
        return [{'id': Utils.str(me['userid']), 'name': '', 'type': drive_type}]

    def get_drive_type_name(self, drive_type):
        return Utils.get_safe_value({'free': 'pCloud Free', 'premium': 'pCloud Premium', 'business': 'pCloud Business'}, drive_type, 'pCloud')

    @staticmethod
    def _real_path(path):
        # A path other than the root, as pCloud takes it: from the root, without a trailing slash. None otherwise.
        path = (path or '').rstrip('/')
        return path if path else None

    @classmethod
    def _folder_id(cls, item_id=None):
        # No id is the root folder ('d0').
        item_id = item_id or cls._ROOT
        if not item_id.startswith('d') or not item_id[1:].isdigit():
            raise ValueError('Not a pCloud folder id: %s' % item_id)
        return item_id[1:]

    @staticmethod
    def _file_id(item_id):
        if not item_id or not item_id.startswith('f') or not item_id[1:].isdigit():
            raise ValueError('Not a pCloud file id: %s' % item_id)
        return item_id[1:]

    def _list(self, item_id=None, recursive=False, path=None):
        # Items are reached by id, except in the source service, which names them by path.
        real_path = None if item_id else self._real_path(path)
        parameters = {'path': real_path} if real_path else {'folderid': self._folder_id(item_id)}
        if recursive:
            parameters['recursive'] = 1
        return self._api('listfolder', parameters)['metadata']

    def get_folder_items(self, item_driveid=None, item_id=None, path=None, on_items_page_completed=None, include_download_info=False, on_before_add_item=None):
        # pCloud answers the whole folder at once. Listed files only get download_info when an export downloads them
        # (_exported_download): each link costs a request, and playback asks for it with get_item.
        folder = self._list(item_id, path=path)
        if self.cancel_operation():
            return
        items = []
        for entry in Utils.get_safe_value(folder, 'contents', []):
            item = self._extract_item(entry, include_download_info and self._exported_download(entry, folder))
            if on_before_add_item:
                on_before_add_item(item)
            items.append(item)
        if on_items_page_completed:
            on_items_page_completed(items)
        return items

    @staticmethod
    def _date(timestamp):
        if not timestamp:
            return None
        return datetime.datetime.fromtimestamp(int(timestamp), datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    def _extract_item(self, entry, include_download_info=False):
        name = Utils.get_safe_value(entry, 'name', '')
        item = {
            'id': entry['id'],
            'name': name,
            'name_extension': Utils.get_extension(name),
            # The root folder has no parent.
            'parent': 'd%s' % entry['parentfolderid'] if entry.get('parentfolderid') is not None else None,
            'last_modified_date': self._date(Utils.get_safe_value(entry, 'modified')),
            'size': Utils.get_safe_value(entry, 'size', 0)
        }
        if Utils.get_safe_value(entry, 'isfolder'):
            item['folder'] = {'child_count': 0}
            return item
        content_type = Utils.get_safe_value(entry, 'contenttype')
        if content_type:
            item['mimetype'] = content_type
        # pCloud's categories: 1 image, 2 video, 3 audio.
        category = Utils.get_safe_value(entry, 'category')
        if category == 1:
            item['image'] = {'size': item['size']}
        elif category == 2:
            video = {}
            for key, field in (('width', 'width'), ('height', 'height'), ('duration', 'duration')):
                value = Utils.get_safe_value(entry, field)
                if value:
                    video[key] = int(float(value))
            item['video'] = video
        elif category == 3:
            audio = {}
            for key, field in (('title', 'title'), ('artist', 'artist'), ('album', 'album'), ('genre', 'genre'), ('tracknumber', 'trackno')):
                value = Utils.get_safe_value(entry, field)
                if value:
                    audio[key] = value
            if audio:
                item['audio'] = audio
        if include_download_info:
            item['download_info'] = {'url': self._file_link(entry['id'])}
        return item

    def _exported_download(self, entry, folder):
        if Utils.get_safe_value(entry, 'isfolder'):
            return False
        name = Utils.get_safe_value(entry, 'name', '').lower()
        extension = Utils.get_extension(name)
        if extension in self._EXPORT_DOWNLOADS:
            return True
        return extension in ('jpg', 'png') and (any(n in name for n in self._ARTWORK_NAMES) or Utils.get_safe_value(folder, 'name') in self._ARTWORK_FOLDERS)

    def _file_link(self, item_id):
        # A pre-authenticated link to the file on one of pCloud's content servers. It expires after a few hours; the
        # download service asks for it again after a few minutes.
        link = self._api('getfilelink', {'fileid': self._file_id(item_id)})
        return 'https://%s%s' % (link['hosts'][0], link['path'])

    def list_subtree(self, item_driveid, item_id):
        # One recursive listing for a whole tree (library exports). pCloud refuses it for the root folder (1101): the
        # root is listed alone and each of its folders recursively.
        item_id = item_id or self._ROOT
        tree = {}

        def add(folder):
            children = Utils.get_safe_value(folder, 'contents', [])
            # Files first, then folders. Only the files an export downloads get download_info (see get_folder_items).
            tree[folder['id']] = [self._extract_item(child, self._exported_download(child, folder)) for child in children if not Utils.get_safe_value(child, 'isfolder')] + \
                [self._extract_item(child) for child in children if Utils.get_safe_value(child, 'isfolder')]
            for child in children:
                if Utils.get_safe_value(child, 'isfolder') and 'contents' in child:
                    add(child)

        if item_id == self._ROOT:
            root = self._list(self._ROOT)
            if self.cancel_operation():
                return None
            folders = [child for child in Utils.get_safe_value(root, 'contents', []) if Utils.get_safe_value(child, 'isfolder')]
            add(dict(root, contents=[child for child in Utils.get_safe_value(root, 'contents', []) if not Utils.get_safe_value(child, 'isfolder')] + folders))
            for folder in folders:
                if self.cancel_operation():
                    return None
                add(self._list(folder['id'], recursive=True))
        else:
            add(self._list(item_id, recursive=True))
        return tree

    def search(self, query, item_driveid=None, item_id=None, on_items_page_completed=None):
        query = Utils.str(query)
        try:
            response = self._api('search', {'query': query, 'limit': self._SEARCH_LIMIT})
        except RequestException as e:
            Logger.notice('pCloud search is not available (%s): looking through the folders instead.' % Utils.str(e))
            return self._walk_search(query, item_id, on_items_page_completed)
        items = [self._extract_item(entry) for entry in Utils.get_safe_value(response, 'items', Utils.get_safe_value(response, 'contents', []))]
        if item_id and item_id != self._ROOT:
            # The search covers the whole account: only what's inside the folder is kept.
            inside = self._folder_ids_under(item_id)
            items = [item for item in items if item['parent'] in inside]
        if on_items_page_completed:
            on_items_page_completed(items)
        return items

    def _folder_ids_under(self, item_id):
        ids = set()

        def add(folder):
            ids.add(folder['id'])
            for child in Utils.get_safe_value(folder, 'contents', []):
                if Utils.get_safe_value(child, 'isfolder'):
                    add(child)

        add(self._list(item_id, recursive=True))
        return ids

    def _walk_search(self, query, item_id=None, on_items_page_completed=None):
        query = query.lower()
        items = []
        folders = [item_id or self._ROOT]
        for _ in range(self._MAX_WALK_FOLDERS):
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
        for item in self.get_folder_items(item_id=parent) or []:
            if 'folder' not in item and item['name'].lower().startswith(prefix) and Utils.default(item['name_extension'], '').lower() in self._SUBTITLE_EXTENSIONS:
                if include_download_info:
                    item['download_info'] = {'url': self._file_link(item['id'])}
                subtitles.append(item)
        return subtitles

    def get_item(self, item_driveid=None, item_id=None, path=None, find_subtitles=False, include_download_info=False):
        real_path = None if item_id else self._real_path(path)
        if real_path:
            # The source service names items by path: stat answers files and folders.
            entry = self._api('stat', {'path': real_path})['metadata']
        else:
            item_id = item_id or self._ROOT
            if item_id.startswith('d'):
                folder = self._list(item_id)
                item = self._extract_item(dict(folder, contents=None))
                if item_id == self._ROOT:
                    item['name'] = ''
                return item
            entry = self._api('stat', {'fileid': self._file_id(item_id)})['metadata']
        item = self._extract_item(entry, include_download_info and not Utils.get_safe_value(entry, 'isfolder'))
        if find_subtitles and 'folder' not in item:
            subtitles = self.get_subtitles(item['parent'], item['name'], item_driveid, include_download_info)
            if subtitles:
                item['subtitles'] = subtitles
        return item
