# -*- coding: utf-8 -*-
"""

    Copyright (C) 2016 Twitch-on-Kodi

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from functools import wraps
import utils
from common import kodi, log_utils
from twitch_exceptions import TwitchException, SubRequired, ResourceUnavailableException, NotFound, PlaybackFailed

i18n = utils.i18n


def error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except ResourceUnavailableException as error:
            log_utils.log('Connection failed |{0}|'.format(error.message), log_utils.LOGERROR)
            kodi.notify(i18n('connection_failed'), error.message, duration=7000, sound=False)
        except SubRequired as error:
            log_utils.log('Requires subscription to |{0}|'.format(error.message), log_utils.LOGDEBUG)
            kodi.notify(kodi.get_name(), i18n('subscription_required') % error.message, duration=5000, sound=False)
        except NotFound as error:
            log_utils.log('Not found |{0}|'.format(error.message), log_utils.LOGDEBUG)
            kodi.notify(kodi.get_name(), i18n('none_found') % error.message.lower(), duration=5000, sound=False)
        except PlaybackFailed as error:
            log_utils.log('Playback Failed |{0}|'.format(error.message), log_utils.LOGDEBUG)
            kodi.notify(kodi.get_name(), i18n('playback_failed'), duration=5000, sound=False)
        except TwitchException as error:
            _error = ''
            try:
                _message = error.message
                _error = _message['error']
                message = '[{0}] {1}'.format(_message['status'], _message['message'])
            except:
                message = error.message
            log_utils.log('Error |{0}| |{1}|'.format(_error, message.strip()), log_utils.LOGERROR)
            kodi.notify(_error if _error else i18n('error'), message.strip(), duration=7000, sound=False)

    return wrapper


def api_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return result
        except:
            raise

    return wrapper
