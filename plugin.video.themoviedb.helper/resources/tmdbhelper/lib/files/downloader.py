import os
import xbmcvfs
import gzip
from xbmcgui import Dialog, ALPHANUM_HIDE_INPUT
from io import BytesIO
from urllib.parse import urlparse
from tmdbhelper.lib.addon.plugin import get_localized, ADDONNAME
from tmdbhelper.lib.addon.dialog import BusyDialog
from tmdbhelper.lib.addon.logger import kodi_log

""" Lazyimports
import zipfile
import requests
"""


class Downloader(object):
    def __init__(self, download_url=None, extract_to=None):
        self.download_url = download_url
        self.extract_to = xbmcvfs.translatePath(extract_to)
        self.msg_cleardir = get_localized(32054)

    def recursive_delete_dir(self, fullpath):
        '''helper to recursively delete a directory'''
        success = True
        if not isinstance(fullpath, str):
            fullpath = fullpath.decode("utf-8")
        dirs, files = xbmcvfs.listdir(fullpath)
        for file in files:
            file = file.decode("utf-8")
            success = xbmcvfs.delete(os.path.join(fullpath, file))
        for directory in dirs:
            directory = directory.decode("utf-8")
            success = self.recursive_delete_dir(os.path.join(fullpath, directory))
        success = xbmcvfs.rmdir(fullpath)
        return success

    def is_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def check_url(self, url, cred):
        import requests
        if not self.is_url(url):
            kodi_log(f'URL is not of a valid schema: {url}', 1)
            return False
        try:
            response = requests.head(url, allow_redirects=True, auth=cred)
            if response.status_code < 300:
                kodi_log(f'URL check passed for {url}: Status code [{response.status_code}]', 1)
                return True
            elif response.status_code < 400:
                kodi_log(f'URL check redirected from {url} to {response.headers["Location"]}: Status code [{response.status_code}]', 1)
                return self.check_url(response.headers['Location'])
            elif response.status_code == 401:
                kodi_log(f'URL requires authentication for {url}: Status code [{response.status_code}]', 1)
                return 'auth'
            else:
                kodi_log(f'URL check failed for {url}: Status code [{response.status_code}]', 1)
                return False
        except Exception as e:
            kodi_log(f'URL check error for {url}: [{e}]', 1)
            return False

    def open_url(self, url, stream=False, check=False, cred=None, count=0):
        import requests
        if not url:
            return False

        valid = self.check_url(url, cred)

        if not valid:
            return False
        if check:
            return True
        if valid == 'auth' and not cred:
            cred = (Dialog().input(heading=get_localized(1014)) or '', Dialog().input(heading=get_localized(733), option=ALPHANUM_HIDE_INPUT) or '')

        response = requests.get(url, timeout=10.000, stream=stream, auth=cred)
        if response.status_code == 401:
            if count > 2 or not Dialog().yesno(ADDONNAME, get_localized(32056), yeslabel=get_localized(32057), nolabel=get_localized(222)):
                Dialog().ok(ADDONNAME, get_localized(32055))
                return False
            count += 1
            cred = (Dialog().input(heading=get_localized(1014)) or '', Dialog().input(heading=get_localized(733), option=ALPHANUM_HIDE_INPUT) or '')
            response = self.open_url(url, stream, check, cred, count)
        return response

    def clear_dir(self, folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    self.recursive_delete_dir(file_path)
            except Exception as exc:
                kodi_log(f'Could not delete file {file_path}: {exc}')

    def get_gzip_text(self):
        if not self.download_url:
            return

        with BusyDialog():
            response = self.open_url(self.download_url)
        if not response:
            Dialog().ok(ADDONNAME, get_localized(32058))
            return

        with gzip.GzipFile(fileobj=BytesIO(response.content)) as downloaded_gzip:
            content = downloaded_gzip.read()
        return content

    def get_extracted_zip(self):
        import zipfile
        if not self.download_url or not self.extract_to:
            return

        with BusyDialog():
            response = self.open_url(self.download_url)
        if not response:
            Dialog().ok(ADDONNAME, get_localized(32058))
            return

        if not os.path.exists(self.extract_to):
            os.makedirs(self.extract_to)

        if Dialog().yesno(ADDONNAME, self.msg_cleardir):
            with BusyDialog():
                self.clear_dir(self.extract_to)

        with BusyDialog():
            num_files = 0
            with zipfile.ZipFile(BytesIO(response.content)) as downloaded_zip:
                for item in [x for x in downloaded_zip.namelist() if x.endswith('.json')]:
                    filename = os.path.basename(item)
                    if not filename:
                        continue

                    _file = downloaded_zip.open(item)
                    with open(os.path.join(self.extract_to, filename), 'wb') as target:
                        target.write(_file.read())
                        num_files += 1

            try:
                _tempzip = os.path.join(self.extract_to, 'temp.zip')
                os.remove(_tempzip)
            except Exception as exc:
                kodi_log(f'Could not delete package {_tempzip}: {exc}')

        if num_files:
            Dialog().ok(ADDONNAME, f'{get_localized(32059)}\n\n{num_files} {get_localized(32060)}.')
