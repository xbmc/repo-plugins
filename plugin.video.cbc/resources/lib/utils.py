"""Utilities module."""
import os
import pickle
from datetime import datetime, timezone
from requests.utils import dict_from_cookiejar
from requests.cookies import cookiejar_from_dict


def get_iptv_channels_file():
    """Get the filename for the IPTV channels filter."""
    try:
        from xbmcvfs import translatePath
        base = translatePath('special://userdata/addon_data/plugin.video.cbc')
    except ModuleNotFoundError:
        base = os.getcwd()
    return os.path.join(base, 'iptvchannels')


def getAuthorizationFile():
    """
    Get the authorization file
    """
    try:
        from xbmcvfs import translatePath
        base = translatePath('special://userdata/addon_data/plugin.video.cbc')
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


def iso8601_to_local(dttm):
    """Convert an ISO 8601 timestamp (UTC or offset-aware) to local datetime."""
    try:
        return datetime.fromisoformat(dttm.replace('Z', '+00:00')).astimezone()
    except (ValueError, TypeError, AttributeError):
        return None


def is_pending(timestamp, item=None):
    """Return true when the supplied datetime is in the future.

    If item is supplied and has a string title, append a live marker when pending.
    """
    try:
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        pending = timestamp.astimezone(timezone.utc) > datetime.now(timezone.utc)
        
        if pending and item is not None and 'title' in item:
            title = item['title']
            if isinstance(title, bytes):
                title = title.decode('utf-8', errors='replace')
            elif title is None:
                title = ''
            elif not isinstance(title, str):
                title = str(title)
            item['title'] = f'{title} [Live at {timestamp.strftime("%Y-%m-%d %H:%M:%S")}]'
        return pending
    except (ValueError, TypeError, AttributeError) as err:
        log(f'is_pending failed: {err}', True)
        return False
