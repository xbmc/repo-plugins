import os
import xbmc
import xbmcvfs
import xbmcgui
import zipfile
import gzip
from resources.lib.addon.plugin import ADDON, kodi_log
from resources.lib.addon.decorators import busy_dialog
from io import BytesIO
from urllib.parse import urlparse

requests = None  # Requests module is slow to import so lazy import via decorator instead


def lazyimport_requests(func):
    def wrapper(*args, **kwargs):
        global requests
        if requests is None:
            import requests
        return func(*args, **kwargs)
    return wrapper


class Downloader(object):
    def __init__(self, download_url=None, extract_to=None):
        self.download_url = download_url
        self.extract_to = xbmcvfs.translatePath(extract_to)
        self.msg_cleardir = ADDON.getLocalizedString(32054)

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

    @lazyimport_requests
    def check_url(self, url, cred):
        if not self.is_url(url):
            kodi_log(u"URL is not of a valid schema: {0}".format(url), 1)
            return False
        try:
            response = requests.head(url, allow_redirects=True, auth=cred)
            if response.status_code < 300:
                kodi_log(u"URL check passed for {0}: Status code [{1}]".format(url, response.status_code), 1)
                return True
            elif response.status_code < 400:
                kodi_log(u"URL check redirected from {0} to {1}: Status code [{2}]".format(url, response.headers['Location'], response.status_code), 1)
                return self.check_url(response.headers['Location'])
            elif response.status_code == 401:
                kodi_log(u"URL requires authentication for {0}: Status code [{1}]".format(url, response.status_code), 1)
                return 'auth'
            else:
                kodi_log(u"URL check failed for {0}: Status code [{1}]".format(url, response.status_code), 1)
                return False
        except Exception as e:
            kodi_log(u"URL check error for {0}: [{1}]".format(url, e), 1)
            return False

    @lazyimport_requests
    def open_url(self, url, stream=False, check=False, cred=None, count=0):
        if not url:
            return False

        valid = self.check_url(url, cred)

        if not valid:
            return False
        if check:
            return True
        if valid == 'auth' and not cred:
            cred = (xbmcgui.Dialog().input(heading=xbmc.getLocalizedString(1014)) or '', xbmcgui.Dialog().input(heading=xbmc.getLocalizedString(733), option=xbmcgui.ALPHANUM_HIDE_INPUT) or '')

        response = requests.get(url, timeout=10.000, stream=stream, auth=cred)
        if response.status_code == 401:
            if count > 2 or not xbmcgui.Dialog().yesno(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(32056), yeslabel=ADDON.getLocalizedString(32057), nolabel=xbmc.getLocalizedString(222)):
                xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(32055))
                return False
            count += 1
            cred = (xbmcgui.Dialog().input(heading=xbmc.getLocalizedString(1014)) or '', xbmcgui.Dialog().input(heading=xbmc.getLocalizedString(733), option=xbmcgui.ALPHANUM_HIDE_INPUT) or '')
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
            except Exception as e:
                kodi_log(u'Could not delete file {0}: {1}'.format(file_path, str(e)))

    def get_gzip_text(self):
        if not self.download_url:
            return

        with busy_dialog():
            response = self.open_url(self.download_url)
        if not response:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(32058))
            return

        with gzip.GzipFile(fileobj=BytesIO(response.content)) as downloaded_gzip:
            content = downloaded_gzip.read()
        return content

    def get_extracted_zip(self):
        if not self.download_url or not self.extract_to:
            return

        with busy_dialog():
            response = self.open_url(self.download_url)
        if not response:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), ADDON.getLocalizedString(32058))
            return

        if not os.path.exists(self.extract_to):
            os.makedirs(self.extract_to)

        if xbmcgui.Dialog().yesno(ADDON.getAddonInfo('name'), self.msg_cleardir):
            with busy_dialog():
                self.clear_dir(self.extract_to)

        with busy_dialog():
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
            except Exception as e:
                kodi_log(u'Could not delete package {0}: {1}'.format(_tempzip, str(e)))

        if num_files:
            xbmcgui.Dialog().ok(ADDON.getAddonInfo('name'), u'{0}\n\n{1} {2}.'.format(ADDON.getLocalizedString(32059), num_files, ADDON.getLocalizedString(32060)))
