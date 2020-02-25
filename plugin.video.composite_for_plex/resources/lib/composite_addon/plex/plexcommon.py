# -*- coding: utf-8 -*-
"""

    Copyright (C) 2019-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import platform
import sys
import uuid
from contextlib import closing

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcvfs  # pylint: disable=import-error

from ..addon.common import get_platform
from ..addon.constants import CONFIG


def get_device_name(settings, device_name):
    if device_name is None:
        device_name = settings.device_name()
    return device_name


def get_client_identifier(settings, client_id):
    if client_id is None:
        client_id = settings.client_id()

        if not client_id:
            client_id = str(uuid.uuid4())
            settings.set_client_id(client_id)

    return client_id


def create_plex_identification(settings, device_name=None, client_id=None, user=None, token=None):
    headers = {
        'X-Plex-Device': get_device(),
        'X-Plex-Client-Platform': 'Kodi',
        'X-Plex-Device-Name': get_device_name(settings, device_name),
        'X-Plex-Language': CONFIG['language'],
        'X-Plex-Platform': get_platform(),
        'X-Plex-Client-Identifier': get_client_identifier(settings, client_id),
        'X-Plex-Product': CONFIG['name'],
        'X-Plex-Platform-Version': platform.uname()[2],
        'X-Plex-Version': CONFIG['version'],
        'X-Plex-Provides': 'player,controller'
    }

    if token is not None:
        headers['X-Plex-Token'] = token

    if user is not None:
        headers['X-Plex-User'] = user

    return headers


def get_device():
    device = None
    if xbmc.getCondVisibility('system.platform.windows'):
        device = 'Windows'
    if xbmc.getCondVisibility('system.platform.linux') \
            and not xbmc.getCondVisibility('system.platform.android'):
        device = 'Linux'
    if xbmc.getCondVisibility('system.platform.osx'):
        device = 'Darwin'
    if xbmc.getCondVisibility('system.platform.android'):
        device = 'Android'

    if xbmcvfs.exists('/proc/device-tree/model'):
        with closing(xbmcvfs.File('/proc/device-tree/model')) as open_file:
            if 'Raspberry Pi' in open_file.read():
                device = 'Raspberry Pi'

    if xbmcvfs.exists('/etc/os-release'):
        with closing(xbmcvfs.File('/etc/os-release')) as open_file:
            contents = open_file.read()
            if 'libreelec' in contents:
                device = 'LibreELEC'
            if 'osmc' in contents:
                device = 'OSMC'

    if device is None:
        try:
            device = platform.system()
        except:  # pylint: disable=bare-except
            try:
                device = platform.platform(terse=True)
            except:  # pylint: disable=bare-except
                device = sys.platform

    return device
