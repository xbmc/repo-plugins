import xbmc
import xbmcaddon
import sys, os

__addon__ = xbmcaddon.Addon()

FILE_NAME = "UA.txt"
UA = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 " \
     "(KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36"

def set_UA():
    if not _UA_exists():
        _save_UA_to_file(FILE_NAME, UA)

def get_UA():
    return _get_UA_from_file(FILE_NAME)


def _UA_exists():
    path = _get_profile_path()

    if not os.path.exists(path):
        return False

    os.chdir(path)

    return os.path.isfile('UA.txt')


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
