# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import json
from functools import wraps
from uuid import uuid4

import xbmcgui  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..lib.context import Context
from ..lib.logger import Log
from ..lib.txt_fmt import strip_html

LOG = Log('api', __file__)


def api_request(func):
    context = Context()

    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) > 0 and not func.__name__.endswith('refresh_token'):
            try:
                args[0].refresh_token()
            except AttributeError:
                pass

        uuid = ''

        if context.settings.log_api_requests:
            uuid = str(uuid4().hex)[:8]
            try:
                LOG.debug('API Request [%s]: \n  Func: %s\n  Args: %s\n  Kwargs: %s' %
                          (uuid, func, args[1:], kwargs))

            except:  # pylint: disable=bare-except
                LOG.debug('API Request [%s]: Failed to log request')

        payload = func(*args, **kwargs)

        if context.settings.log_api_requests:
            try:
                LOG.debug('API Response [%s]: \n  Payload: \n%s' %
                          (uuid, json.dumps(payload, indent=4)))

            except:  # pylint: disable=bare-except
                LOG.debug('API Request [%s]: Failed to log response')

        return __api_error_check(payload)

    return wrapper


def __api_error_check(payload):
    context = Context()

    if isinstance(payload, dict) and 'error' in payload:
        if not ('error' in payload and 'code' in payload['error'] and
                200 <= int(payload['error']['code']) < 300):

            heading = context.i18n('Error')
            message = ''

            if 'message' in payload['error']:
                message = strip_html(payload['error']['message'])

            if 'errors' in payload['error']:
                error = payload['error']['errors'][0]

                if 'reason' in error:
                    heading += ': ' + error['reason']

                if 'message' in error:
                    message = strip_html(payload['error']['message'])

            if 'code' in payload['error']:
                message = '[%s] %s' % (payload['error']['code'], message)

            xbmcgui.Dialog().notification(
                heading,
                message,
                LOGO_SMALL,
                sound=False
            )
            LOG.error('API request failed:\n  %s' % payload)

    return payload
