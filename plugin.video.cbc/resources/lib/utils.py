"""Utilities module."""
import os
import pickle
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict

def get_cookie_file():
    """Get the cookies file."""
    try:
        from xbmcvfs import translatePath
        base = translatePath('special://userdata/addon_data/plugin.video.cbc')
    except ModuleNotFoundError:
        base = os.getcwd()
    return os.path.join(base, 'cookies')


def get_iptv_channels_file():
    """Get the filename for the IPTV channels filter."""
    try:
        from xbmcvfs import translatePath
        base = translatePath('special://userdata/addon_data/plugin.video.cbc')
    except ModuleNotFoundError:
        base = os.getcwd()
    return os.path.join(base, 'iptvchannels')

def save_cookies(session_cookies):
    """
    Write cookies to the cookie file
    @param session_cookies the session.cookies object to save
    """
    with open(get_cookie_file(), 'wb') as f:
        cookies = dict_from_cookiejar(session_cookies)
        pickle.dump(cookies, f)


def loadCookies():
    """
    Load cookies from the cookie file into a session.cookies object
    @return a session.cookies object
    """
    try:
        with open(get_cookie_file(), 'rb') as f:
            cookies = pickle.load(f)
            return cookiejar_from_dict(cookies)
    except IOError as err:
        log('Unable to load cookies: {}'.format(err), True)
        return None

    return None


def getAuthorizationFile():
    """
    Get the authorization file
    """
    try:
        import xbmc, xbmcaddon
        base = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    except:
        base = os.getcwd()

    return os.path.join(base, 'authorization')


def saveAuthorization(authorization):
    with open(getAuthorizationFile(), 'wb') as f:
        pickle.dump(authorization, f)


def loadAuthorization():
    """
    Load authorization from the authorization file into an object
    @return an object
    """
    try:
        with open(getAuthorizationFile(), 'rb') as f:
            authorization = pickle.load(f)
            return authorization
    except IOError as err:
        log('Unable to load authorization: {}'.format(err), True)
        return None

    return None


def log(msg, error = False):
    """
    Log an error
    @param msg The error to log
    @param error error severity indicator
    """
    try:
        import xbmc
        full_msg = "plugin.video.cbc: {}".format(msg)
        xbmc.log(full_msg, level=xbmc.LOGERROR if error else xbmc.LOGINFO)
    except:
        print(msg)
