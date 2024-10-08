# -*- coding: utf-8 -*-
import os
import json
import logging
import binascii
import webbrowser
from urllib.parse import urlencode
from datetime import datetime

import xbmc
import xbmcvfs

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

KB = 1024
MB = 1024 * KB

# Read and write operations are limited to this chunk size.
# This can make a big difference when dealing with large files.
CHUNK_SIZE = 256 * KB

BASE_URL = 'https://api.put.io/v2'
ACCESS_TOKEN_URL = 'https://api.put.io/v2/oauth2/access_token'
AUTHENTICATION_URL = 'https://api.put.io/v2/oauth2/authenticate'

SPECIAL_TEMPORARY_DIRECTORY_PATH = 'special://temp/plugin.video.putio'

logger = logging.getLogger(__name__)


class AuthHelper(object):

    def __init__(self, client_id, client_secret, redirect_uri, type='code'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.callback_url = redirect_uri
        self.type = type

    @property
    def authentication_url(self):
        """Redirect your users to here to authenticate them."""
        params = {
            'client_id': self.client_id,
            'response_type': self.type,
            'redirect_uri': self.callback_url
        }
        return AUTHENTICATION_URL + "?" + urlencode(params)

    def open_authentication_url(self):
        webbrowser.open(self.authentication_url)

    def get_access_token(self, code):
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'authorization_code',
            'redirect_uri': self.callback_url,
            'code': code
        }
        response = requests.get(ACCESS_TOKEN_URL, params=params)
        logger.debug(response)
        assert response.status_code == 200
        return response.json()['access_token']


class Client(object):

    def __init__(self, access_token, use_retry=False):
        self.access_token = access_token
        self.session = requests.session()

        if use_retry:
            # Retry maximum 10 times, backoff on each retry
            # Sleeps 1s, 2s, 4s, 8s, etc to a maximum of 120s between retries
            # Retries on HTTP status codes 500, 502, 503, 504
            retries = Retry(total=10,
                            backoff_factor=1,
                            status_forcelist=[500, 502, 503, 504])

            # Use the retry strategy for all HTTPS requests
            self.session.mount('https://', HTTPAdapter(max_retries=retries))

        # Keep resource classes as attributes of client.
        # Pass client to resource classes so resource object
        # can use the client.
        attributes = {'client': self}
        self.File = type('File', (_File,), attributes)
        self.Transfer = type('Transfer', (_Transfer,), attributes)
        self.Account = type('Account', (_Account,), attributes)

    def request(self, path, method='GET', params=None, data=None, files=None,
                headers=None, raw=False, stream=False):
        """
        Wrapper around requests.request()

        Prepends BASE_URL to path.
        Inserts oauth_token to query params.
        Parses response as JSON and returns it.

        """
        if not params:
            params = {}

        if not headers:
            headers = {}

        # All requests must include oauth_token
        params['oauth_token'] = self.access_token

        headers['Accept'] = 'application/json'

        url = BASE_URL + path
        logger.debug('url: %s', url)

        response = self.session.request(
            method, url, params=params, data=data, files=files,
            headers=headers, allow_redirects=True, stream=stream)
        logger.debug('response: %s', response)
        if raw:
            return response

        logger.debug('content: %s', response.content)
        try:
            response = json.loads(response.content)
        except ValueError:
            raise Exception('Server didn\'t send valid JSON:\n%s\n%s' % (
                response, response.content))

        if response['status'] == 'ERROR':
            raise Exception(response['error_type'])

        return response


class _BaseResource(object):

    client = None

    def __init__(self, resource_dict):
        """Constructs the object from a dict."""
        # All resources must have id and name attributes
        self.id = None
        self.name = None
        self.__dict__.update(resource_dict)
        try:
            self.created_at = strptime(self.created_at)
        except Exception:
            self.created_at = None

    def __str__(self):
        return self.name.encode('utf-8')

    def __repr__(self):
        # shorten name for display
        name = self.name[:17] + '...' if len(self.name) > 20 else self.name
        return '<%s id=%r, name="%r">' % (
            self.__class__.__name__, self.id, name)


class _File(_BaseResource):

    @classmethod
    def get(cls, id):
        d = cls.client.request('/files/%i?video_metadata=1' % id, method='GET')
        t = d['file']
        return cls(t)

    @classmethod
    def list(cls, parent_id=0):
        d = cls.client.request('/files/list?video_metadata=1', params={'parent_id': parent_id})
        files = d['files']
        return [cls(f) for f in files]

    # FIXME: temporarily added.
    def stream_url(self):
        return BASE_URL + '/files/%s/stream?oauth_token=%s' % (self.id, self.client.access_token)

    # FIXME: temporarily added.
    def subtitles(self):
        """
        Returns an array of all subtitles for the video.
        
        Subtitles are listed by the api, and downloaded to a temporary directory.
        """
        subtitles_list_url = '/files/%s/subtitles' % self.id
        subtitles_list_response = self.client.request(subtitles_list_url)
        assert subtitles_list_response.status_code == 200
        # NOTE: The subtitle key (used below) is a bunch of base64 encoded bits. They are not
        # deterministic, and may change even if the video id and each subtitle file contents
        # stays the same. Deleting any previous temporary subtitle files (for all videos) to
        # not amass files, neither from duplicates of subtitles, every previously watched video,
        # nor videos already deleted from put.io.
        subtitles_directory_path = '%s/subtitles' % SPECIAL_TEMPORARY_DIRECTORY_PATH
        ensure_local_special_path_rmdir_recursive(subtitles_directory_path)
        video_directory_path = '%s/%s' % (subtitles_directory_path, self.id)
        subtitle_file_paths = []
        for subtitle in subtitles_list_response['subtitles']:
            # NOTE: There are subtitle filename collisions, even per video. Using the
            # subtitle key for subtitle uniqueness to not overwrite files during download,
            # but the raw key string is too long.
            truncated_subtitle_key = subtitle['key'][:5]
            subtitle_directory_path = '%s/%s' % (video_directory_path, truncated_subtitle_key)
            xbmcvfs.mkdirs(subtitle_directory_path)

            subtitle_name = subtitle['name']
            subtitle_language = subtitle['language_code'] or ''
            if len(subtitle_language) == 3:  # sometimes this returns wrong
                subtitle_name = subtitle_name + ' - ' + subtitle_language

            subtitle_path = '%s/%s' % (subtitle_directory_path, subtitle_name)
            # FIXME: Parallelize downloads.
            subtitle_url = '%s/%s' % (subtitles_list_url, subtitle['key'])
            self._download_subtitle(subtitle_url, subtitle_path)
            subtitle_file_paths.append(subtitle_path)
        return subtitle_file_paths

    def _download_subtitle(self, url, special_path):
        special_path_translated = xbmcvfs.translatePath(special_path)
        response = self.client.request(url, raw=True)
        with open(special_path_translated, 'wb') as f:
            for data in response.iter_content():
                f.write(data)

    # FIXME: temporarily added.
    @property
    def is_video(self):
        return self.file_type == 'VIDEO'

    # FIXME: temporarily added.
    @property
    def is_audio(self):
        return self.file_type == 'AUDIO'

    # FIXME: temporarily added.
    @property
    def is_folder(self):
        return self.file_type == 'FOLDER'

    @classmethod
    def upload(cls, path, name=None, parent_id=0):
        with open(path) as f:
            if name:
                files = {'file': (name, f)}
            else:
                files = {'file': f}
            d = cls.client.request('/files/upload', method='POST',
                                   data={'parent_id': parent_id}, files=files)

        f = d['file']
        return cls(f)

    def dir(self):
        """List the files under directory."""
        return self.list(parent_id=self.id)

    def download(self, dest='.', delete_after_download=False, chunk_size=CHUNK_SIZE):
        if self.content_type == 'application/x-directory':
            self._download_directory(dest, delete_after_download, chunk_size)
        else:
            self._download_file(dest, delete_after_download, chunk_size)

    def _download_directory(self, dest, delete_after_download, chunk_size):
        name = self.name
        if isinstance(name, unicode):
            name = name.encode('utf-8', 'replace')

        dest = os.path.join(dest, name)
        if not os.path.exists(dest):
            os.mkdir(dest)

        for sub_file in self.dir():
            sub_file.download(dest, delete_after_download, chunk_size)

        if delete_after_download:
            self.delete()

    def _verify_file(self, filepath):
        logger.info('verifying crc32...')
        filesize = os.path.getsize(filepath)
        if self.size != filesize:
            logging.error('file %s is %d bytes, should be %s bytes' % (filepath, filesize, self.size))
            return False

        crcbin = 0
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                crcbin = binascii.crc32(chunk, crcbin) & 0xffffffff

        crc32 = '%08x' % crcbin

        if crc32 != self.crc32:
            logging.error('file %s CRC32 is %s, should be %s' % (filepath, crc32, self.crc32))
            return False

        return True

    def _download_file(self, dest, delete_after_download, chunk_size):
        name = self.name
        if isinstance(name, unicode):
            name = name.encode('utf-8', 'replace')

        filepath = os.path.join(dest, name)
        if os.path.exists(filepath):
            first_byte = os.path.getsize(filepath)

            if first_byte == self.size:
                logger.warning('file %s exists and is the correct size %d' % (filepath, self.size))
        else:
            first_byte = 0

        logger.debug('file %s is currently %d, should be %d' % (filepath, first_byte, self.size))

        if self.size == 0:
            # Create an empty file
            open(filepath, 'w').close()
            logger.debug('created empty file %s' % filepath)
        else:
            if first_byte < self.size:
                with open(filepath, 'ab') as f:
                    headers = {'Range': 'bytes=%d-' % first_byte}

                    logger.debug('request range: bytes=%d-' % first_byte)
                    response = self.client.request('/files/%s/download' % self.id,
                                                headers=headers,
                                                raw=True,
                                                stream=True)

                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)

        if self._verify_file(filepath):
            if delete_after_download:
                self.delete()

    def delete(self):
        return self.client.request('/files/delete', method='POST',
                                   data={'file_id': str(self.id)})

    @classmethod
    def delete_multi(cls, ids):
        return cls.client.request('/files/delete', method='POST',
                                  data={'file_ids': ','.join(map(str, ids))})

    def move(self, parent_id):
        return self.client.request('/files/move', method='POST',
                                   data={'file_ids': str(self.id), 'parent_id': str(parent_id)})

    def rename(self, name):
        return self.client.request('/files/rename', method='POST',
                                   data={'file_id': str(self.id), 'name': str(name)})


class _Transfer(_BaseResource):

    @classmethod
    def list(cls):
        d = cls.client.request('/transfers/list')
        transfers = d['transfers']
        return [cls(t) for t in transfers]

    @classmethod
    def get(cls, id):
        d = cls.client.request('/transfers/%i' % id, method='GET')
        t = d['transfer']
        return cls(t)

    @classmethod
    def add_url(cls, url, parent_id=0, extract=False, callback_url=None):
        d = cls.client.request('/transfers/add', method='POST', data=dict(
            url=url, save_parent_id=parent_id, extract=extract,
            callback_url=callback_url))
        t = d['transfer']
        return cls(t)

    @classmethod
    def add_torrent(cls, path, parent_id=0, extract=False, callback_url=None):
        with open(path, 'rb') as f:
            files = {'file': f}
            d = cls.client.request('/files/upload', method='POST', files=files,
                                   data=dict(save_parent_id=parent_id,
                                             extract=extract,
                                             callback_url=callback_url))
        t = d['transfer']
        return cls(t)

    @classmethod
    def clean(cls):
        return cls.client.request('/transfers/clean', method='POST')

    def cancel(self):
        return self.client.request('/transfers/cancel',
                                   method='POST',
                                   data={'transfer_ids': self.id})

    @classmethod
    def cancel_multi(cls, ids):
        return cls.client.request('/transfers/cancel',
                                  method='POST',
                                  data={'transfer_ids': ','.join(map(str, ids))})


class _Account(_BaseResource):

    @classmethod
    def info(cls):
        return cls.client.request('/account/info', method='GET')

    @classmethod
    def settings(cls):
        return cls.client.request('/account/settings', method='GET')


# Due to a nasty bug in datetime module, datetime.strptime calls
# are not thread-safe and can throw a TypeError. Details: https://bugs.python.org/issue7980
# Here we are implementing simple RFC3339 parser which is used in Put.io APIv2.
def strptime(date):
    """Returns datetime object from the given date, which is in a specific format: YYYY-MM-ddTHH:mm:ss"""
    d = {
            'year': date[0:4],
            'month': date[5:7],
            'day': date[8:10],
            'hour': date[11:13],
            'minute': date[14:16],
            'second': date[17:],
            }

    d = dict((k, int(v)) for k, v in list(d.items()))
    return datetime(**d)

# FIXME: Import from some library, or move to utilities.
def local_rmdir_recursive(dirpath):
    """
    Recursive directory removal utility, as non-empty directories cannot be deleted.
    """
    dirs, files = xbmcvfs.listdir(dirpath)
    for f in files:
        xbmcvfs.delete(os.path.join(dirpath, f))
    for d in dirs:
        local_rmdir_recursive(os.path.join(dirpath, d))
    return xbmcvfs.rmdir(dirpath)

# FIXME: Import from some library, or move to utilities.
def local_special_directory_exists(special_dir_path):
    """
    Checks if a directory, specified by a special:// path, exists.
    """
    # NOTE: Checking if directory exists requires a trailing slash.
    # NOTE: Assuming special:// paths, which use forward slashes only.
    special_separator = '/'
    special_dir_path_with_slash = (special_dir_path + special_separator
        if special_dir_path[:-1] != special_separator else special_dir_path)
    return xbmcvfs.exists(special_dir_path_with_slash)

# FIXME: Import from some library, or move to utilities.
def ensure_local_special_path_rmdir_recursive(special_dir_path):
    """
    Ensures that a directory, specified by a special:// path, exists, does not exist.
    """
    if local_special_directory_exists(special_dir_path):
        return local_rmdir_recursive(special_dir_path)
    return True
