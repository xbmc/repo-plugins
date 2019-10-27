from resources.lib.fake_useragent import UserAgent
import xbmc
import xbmcaddon
import sys, os

__addon__ = xbmcaddon.Addon()

FILE_NAME = "UA.txt"

def set_UA():
    UA = (UserAgent()).chrome
    _save_UA_to_file(FILE_NAME, UA)

def get_UA():
    return _get_UA_from_file(FILE_NAME)

def _save_UA_to_file(file_name, data):
    path = _get_profile_path()

    if not os.path.exists(path):
        os.mkdir(path, 0o775)

    os.chdir(path)

    with open(file_name, 'w') as file:
        return file.write(data)

def _get_UA_from_file(file_name):
    path = _get_profile_path()

    if not os.path.exists(path):
        os.mkdir(path, 0o775)

    os.chdir(path)


    with open(file_name, 'r') as file:
        return file.read()

def _get_profile_path():
    global profile
    if sys.version_info[0] == 3:
        profile = xbmc.translatePath(__addon__.getAddonInfo('profile'))
    else:
        profile = xbmc.translatePath(__addon__.getAddonInfo('profile')).decode("utf-8")

    return profile
