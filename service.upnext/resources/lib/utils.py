# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
import sys
import json
from xbmc import executeJSONRPC, getRegion, log as xlog, LOGDEBUG, LOGNOTICE
from xbmcaddon import Addon
from xbmcgui import Window
from statichelper import from_unicode, to_unicode

ADDON = Addon()


def get_addon_info(key):
    """Return add-on information"""
    return to_unicode(ADDON.getAddonInfo(key))


def addon_id():
    """Return add-on ID"""
    return get_addon_info('id')


def addon_path():
    """Return add-on path"""
    return get_addon_info('path')


def get_property(key, window_id=10000):
    """Get a Window property"""
    return to_unicode(Window(window_id).getProperty(key))


def set_property(key, value, window_id=10000):
    """Set a Window property"""
    return Window(window_id).setProperty(key, from_unicode(str(value)))


def clear_property(key, window_id=10000):
    """Clear a Window property"""
    return Window(window_id).clearProperty(key)


def get_setting(key, default=None):
    """Get an add-on setting as string"""
    # We use Addon() here to ensure changes in settings are reflected instantly
    try:
        value = to_unicode(Addon().getSetting(key))
    except RuntimeError:  # Occurs when the add-on is disabled
        return default
    if value == '' and default is not None:
        return default
    return value


def get_setting_bool(key, default=None):
    """Get an add-on setting as boolean"""
    try:
        return Addon().getSettingBool(key)
    except (AttributeError, TypeError):  # On Krypton or older, or when not a boolean
        value = get_setting(key, default)
        if value not in ('false', 'true'):
            return default
        return bool(value == 'true')
    except RuntimeError:  # Occurs when the add-on is disabled
        return default


def get_setting_int(key, default=None):
    """Get an add-on setting as integer"""
    try:
        return Addon().getSettingInt(key)
    except (AttributeError, TypeError):  # On Krypton or older, or when not an integer
        value = get_setting(key, default)
        try:
            return int(value)
        except ValueError:
            return default
    except RuntimeError:  # Occurs when the add-on is disabled
        return default


def encode_data(data, encoding='base64'):
    """Encode data for a notification event"""
    json_data = json.dumps(data).encode()
    if encoding == 'base64':
        from base64 import b64encode
        encoded_data = b64encode(json_data)
    elif encoding == 'hex':
        from binascii import hexlify
        encoded_data = hexlify(json_data)
    else:
        log("Unknown payload encoding type '%s'" % encoding, level=0)
        return None
    if sys.version_info[0] > 2:
        encoded_data = encoded_data.decode('ascii')
    return encoded_data


def decode_data(encoded):
    """Decode data coming from a notification event"""
    encoding = 'base64'
    from binascii import Error, unhexlify
    try:
        json_data = unhexlify(encoded)
    except (TypeError, Error):
        from base64 import b64decode
        json_data = b64decode(encoded)
    else:
        encoding = 'hex'
    # NOTE: With Python 3.5 and older json.loads() does not support bytes or bytearray, so we convert to unicode
    return json.loads(to_unicode(json_data)), encoding


def decode_json(data):
    encoded = json.loads(data)
    if not encoded:
        return None, None
    return decode_data(encoded[0])


def event(message, data=None, sender=None, encoding='base64'):
    """Send internal notification event"""
    data = data or {}
    sender = sender or addon_id()

    encoded = encode_data(data, encoding=encoding)
    if not encoded:
        return

    jsonrpc(method='JSONRPC.NotifyAll', params=dict(
        sender='%s.SIGNAL' % sender,
        message=message,
        data=[encoded],
    ))


def log(msg, name=None, level=1):
    """Log information to the Kodi log"""
    log_level = get_setting_int('logLevel', level)
    debug_logging = get_global_setting('debug.showloginfo')
    set_property('logLevel', log_level)
    if not debug_logging and log_level < level:
        return
    level = LOGDEBUG if debug_logging else LOGNOTICE
    xlog('[%s] %s -> %s' % (addon_id(), name, from_unicode(msg)), level=level)


def calculate_progress_steps(period):
    """Calculate a progress step"""
    if int(period) == 0:  # Avoid division by zero
        return 10.0
    return (100.0 / int(period)) / 10


def jsonrpc(**kwargs):
    """Perform JSONRPC calls"""
    if kwargs.get('id') is None:
        kwargs.update(id=0)
    if kwargs.get('jsonrpc') is None:
        kwargs.update(jsonrpc='2.0')
    return json.loads(executeJSONRPC(json.dumps(kwargs)))


def get_global_setting(setting):
    """Get a Kodi setting"""
    result = jsonrpc(method='Settings.GetSettingValue', params=dict(setting=setting))
    return result.get('result', {}).get('value')


def localize(string_id):
    """Return the translated string from the .po language files"""

    return ADDON.getLocalizedString(string_id)


def localize_time(time):
    """Localize time format"""
    time_format = getRegion('time')

    # Fix a bug in Kodi v18.5 and older causing double hours
    # https://github.com/xbmc/xbmc/pull/17380
    time_format = time_format.replace('%H%H:', '%H:')

    # Strip off seconds
    time_format = time_format.replace(':%S', '')

    return time.strftime(time_format)
