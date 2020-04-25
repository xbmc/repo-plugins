import os
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import requests
import zipfile
import resources.lib.utils as utils
from io import BytesIO
try:  # Python 3
    from urllib.parse import urlparse
except ImportError:  # Python 2
    from urlparse import urlparse


class Downloader(object):
    def __init__(self, download_url=None, extract_to=None):
        self.addon = xbmcaddon.Addon()
        self.download_url = download_url
        self.extract_to = xbmc.translatePath(extract_to)
        self.msg_cleardir = self.addon.getLocalizedString(32054)

    def recursive_delete_dir(self, fullpath):
        '''helper to recursively delete a directory'''
        success = True
        if not isinstance(fullpath, unicode):
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
        if not self.is_url(url):
            utils.kodi_log("URL is not of a valid schema: {0}".format(url), 1)
            return False
        try:
            response = requests.head(url, allow_redirects=True, auth=cred)
            if response.status_code < 300:
                utils.kodi_log("URL check passed for {0}: Status code [{1}]".format(url, response.status_code), 1)
                return True
            elif response.status_code < 400:
                utils.kodi_log("URL check redirected from {0} to {1}: Status code [{2}]".format(url, response.headers['Location'], response.status_code), 1)
                return self.check_url(response.headers['Location'])
            elif response.status_code == 401:
                utils.kodi_log("URL requires authentication for {0}: Status code [{1}]".format(url, response.status_code), 1)
                return 'auth'
            else:
                utils.kodi_log("URL check failed for {0}: Status code [{1}]".format(url, response.status_code), 1)
                return False
        except Exception as e:
            utils.kodi_log("URL check error for {0}: [{1}]".format(url, e), 1)
            return False

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
            if count > 2 or not xbmcgui.Dialog().yesno(self.addon.getAddonInfo('name'), self.addon.getLocalizedString(32056), yeslabel=self.addon.getLocalizedString(32057), nolabel=xbmc.getLocalizedString(222)):
                xbmcgui.Dialog().ok(self.addon.getAddonInfo('name'), self.addon.getLocalizedString(32055))
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
                utils.kodi_log(u'Could not delete file {0}: {1}'.format(file_path, str(e)))

    def get_extracted_zip(self):
        if not self.download_url or not self.extract_to:
            return

        with utils.busy_dialog():
            response = self.open_url(self.download_url)
        if not response:
            xbmcgui.Dialog().ok(self.addon.getAddonInfo('name'), self.addon.getLocalizedString(32058))
            return

        if not os.path.exists(self.extract_to):
            os.makedirs(self.extract_to)

        if xbmcgui.Dialog().yesno(self.addon.getAddonInfo('name'), self.msg_cleardir):
            with utils.busy_dialog():
                self.clear_dir(self.extract_to)

        with utils.busy_dialog():
            num_files = 0
            with zipfile.ZipFile(BytesIO(response.content)) as downloaded_zip:
                for item in [x for x in downloaded_zip.namelist() if x.endswith('.json')]:
                    filename = os.path.basename(item)
                    if not filename:
                        continue

                    _file = downloaded_zip.open(item)
                    with open(os.path.join(self.extract_to, filename), 'w') as target:
                        target.write(_file.read())
                        num_files += 1

            try:
                _tempzip = os.path.join(self.extract_to, 'temp.zip')
                os.remove(_tempzip)
            except Exception as e:
                utils.kodi_log(u'Could not delete package {0}: {1}'.format(_tempzip, str(e)))

        if num_files:
            xbmcgui.Dialog().ok(self.addon.getAddonInfo('name'), '{0}\n\n{1} {2}.'.format(self.addon.getLocalizedString(32059), num_files, self.addon.getLocalizedString(32060)))
