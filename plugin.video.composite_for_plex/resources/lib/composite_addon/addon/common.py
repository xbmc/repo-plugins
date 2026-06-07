# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import socket
import sys

from kodi_six import xbmc  # pylint: disable=import-error
from six.moves import xrange
from six.moves.urllib_parse import unquote
from six.moves.urllib_parse import urlencode

from .constants import COMMANDS
from .constants import CONFIG
from .logger import Logger

LOG = Logger()


def get_argv():
    return sys.argv


def get_handle():
    try:
        return int(get_argv()[1])
    except (ValueError, IndexError):
        return -1


def get_params():
    try:
        param_string = get_argv()[2]
    except IndexError:
        param_string = ''

    params = {}
    if len(param_string) >= 2:
        _params = param_string

        pairs_of_params = _params.lstrip('?').split('&')
        number_of_pairs = len(pairs_of_params)
        for idx in xrange(number_of_pairs):
            split_params = pairs_of_params[idx].split('=')

            if (len(split_params)) == 2:
                params[split_params[0]] = split_params[1]
            elif (len(split_params)) == 3:
                params[split_params[0]] = split_params[1] + '=' + split_params[2]

    url = params.get('url')
    if url:
        if url.startswith('http') or url.startswith('file'):
            url = unquote(url)

    params['url'] = url
    params['command'] = _get_command_parameter(url)
    params['path_mode'] = get_plugin_url_path()

    LOG.debug('Parameters |%s| -> |%s|' % (param_string, str(params)))
    return params


def _get_command_parameter(url):
    command = None
    if url and url.startswith('cmd'):
        command = url.split(':')[1]

    if command is None:
        try:
            command = get_argv()[1]
        except:  # pylint: disable=bare-except
            pass

    try:
        _ = int(command)
        command = COMMANDS.UNSET
    except (ValueError, TypeError):
        pass

    return command


def is_resuming_video():
    try:
        _resume_arg = get_argv()[3].split(':')
        if _resume_arg[0] == 'resume' and _resume_arg[1] == 'true':
            return True
        return False
    except:  # pylint: disable=bare-except
        return False


def get_plugin_url_path():
    plugin_url = get_argv()[0]
    path = plugin_url.replace('plugin://%s/' % CONFIG['id'], '').rstrip('/')
    if not path or (path and path.endswith('.py')):
        return None
    return path


def get_plugin_url(params):
    return 'plugin://%s/?%s' % (CONFIG['id'], urlencode(params))


def is_ip(address):
    """from http://www.seanelavelle.com/2012/04/16/checking-for-a-valid-ip-in-python/"""
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False


def get_platform_ip():
    return xbmc.getIPAddress()


def get_platform():
    platform = 'Unknown'

    if xbmc.getCondVisibility('system.platform.osx'):
        platform = 'MacOSX'
    if xbmc.getCondVisibility('system.platform.atv2'):
        platform = 'AppleTV2'
    if xbmc.getCondVisibility('system.platform.tvos'):
        platform = 'tvOS'
    if xbmc.getCondVisibility('system.platform.ios'):
        platform = 'iOS'
    if xbmc.getCondVisibility('system.platform.windows'):
        platform = 'Windows'
    if xbmc.getCondVisibility('system.platform.raspberrypi'):
        platform = 'RaspberryPi'
    if xbmc.getCondVisibility('system.platform.linux'):
        platform = 'Linux'
    if xbmc.getCondVisibility('system.platform.android'):
        platform = 'Android'

    return platform
