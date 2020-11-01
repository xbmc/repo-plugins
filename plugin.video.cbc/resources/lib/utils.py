import os, pickle
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict

def getCookieFile():
    """
    Get the cookies file
    """
    try:
        import xbmc, xbmcaddon
        base = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    except:
        base = os.getcwd()

    return os.path.join(base, 'cookies')


def saveCookies(session_cookies):
    """
    Write cookies to the cookie file
    @param session_cookies the session.cookies object to save
    """
    with open(getCookieFile(), 'wb') as f:
        cookies = dict_from_cookiejar(session_cookies)
        pickle.dump(cookies, f)


def loadCookies():
    """
    Load cookies from the cookie file into a session.cookies object
    @return a session.cookies object
    """
    try:
        with open(getCookieFile(), 'rb') as f:
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
