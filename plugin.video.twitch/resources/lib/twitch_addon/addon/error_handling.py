# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from ast import literal_eval
from copy import deepcopy
from functools import wraps

from . import utils
from .common import kodi, log_utils
from .twitch_exceptions import TwitchException, SubRequired, ResourceUnavailableException, NotFound, PlaybackFailed

i18n = utils.i18n

# types
# 0 - nothing (just notify)
# 1 - directory (send end_of_directory)
def error_handler(func=None, route_type=0):
    def _real_dec(func):    
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except ResourceUnavailableException as error:
                message = str(error)
                log_utils.log('Connection failed |{0}|'.format(message), log_utils.LOGERROR)
                kodi.notify(i18n('connection_failed'), message, duration=7000, sound=False)
            except SubRequired as error:
                message = str(error)
                log_utils.log('Requires subscription to |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('subscription_required') % message, duration=5000, sound=False)
            except NotFound as error:
                message = str(error)
                log_utils.log('Not found |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('none_found') % message.lower(), duration=5000, sound=False)
            except PlaybackFailed as error:
                message = str(error)
                log_utils.log('Playback Failed |{0}|'.format(message), log_utils.LOGDEBUG)
                kodi.notify(kodi.get_name(), i18n('playback_failed'), duration=5000, sound=False)
                kodi.set_resolved_url(kodi.ListItem(), succeeded=False)
            except TwitchException as error:
                _error = ''
                _message = literal_eval(str(deepcopy(error)).strip(','))
                try:
                    _error = _message['error']
                    message = '[{0}] {1}'.format(_message['status'], _message['message'])
                except:
                    message = _message
                log_utils.log('Error |{0}| |{1}|'.format(_error, message.strip()), log_utils.LOGERROR)
                kodi.notify(_error if _error else i18n('error'), message.strip(), duration=7000, sound=False)
            if route_type==1:
                kodi.end_of_directory(succeeded=False)
        return wrapper
    
    if func:
        return _real_dec(func)
    return _real_dec


def api_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except:
            raise

    return wrapper
