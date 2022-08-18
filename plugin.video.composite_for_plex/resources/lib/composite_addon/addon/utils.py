# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import json
import os
import time

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from six import PY3
from six.moves import cPickle as pickle
from six.moves import xrange

from ..addon.constants import CONFIG
from ..addon.logger import Logger
from ..addon.strings import i18n

LOG = Logger()


def get_xml(context, url, tree=None):
    if tree is None:
        tree = context.plex_network.get_processed_xml(url)

    if tree.get('message'):
        xbmcgui.Dialog().ok(tree.get('header', i18n('Message')), tree.get('message', ''))
        return None

    return tree


def get_master_server(context, all_servers=False):
    possible_servers = []
    append_server = possible_servers.append
    current_master = context.settings.master_server()
    for server_data in context.plex_network.get_server_list():
        LOG.debug(str(server_data))
        if server_data.get_master() == 1:
            append_server(server_data)
    LOG.debug('Possible master servers are: %s' % possible_servers)

    if all_servers:
        return possible_servers

    if len(possible_servers) > 1:
        preferred = 'local'
        for server_data in possible_servers:
            if server_data.get_name == current_master:
                LOG.debug('Returning current master')
                return server_data
            if preferred == 'any':
                LOG.debug('Returning \'any\'')
                return server_data
            if server_data.get_discovery() == preferred:
                LOG.debug('Returning local')
                return server_data

    if len(possible_servers) == 0:
        return None

    return possible_servers[0]


def get_transcode_profile(context):
    profile_count = 3
    profile_labels = []
    append_label = profile_labels.append

    for idx in xrange(profile_count):
        profile = context.settings.transcode_profile(idx)
        if profile.get('enabled'):
            resolution, bitrate = profile.get('quality').split(',')
            sub_size = profile.get('subtitle_size')
            audio_boost = profile.get('audio_boost')
            append_label('[%s] %s@%s (%s/%s)' %
                         (str(idx + 1), resolution, bitrate.strip(),
                          sub_size, audio_boost))

    if len(profile_labels) == 1:
        return 0

    dialog = xbmcgui.Dialog()
    result = dialog.select(i18n('Transcode Profiles'), profile_labels)

    if result == -1:
        return 0

    return result


def write_pickled(filename, data):
    try:
        os.makedirs(CONFIG['temp_path'])
    except:  # pylint: disable=bare-except
        pass
    filename = os.path.join(CONFIG['temp_path'], filename)
    pickled_data = pickle.dumps(data, protocol=2)
    with open(filename, 'wb') as open_file:
        open_file.write(pickled_data)


def read_pickled(filename, delete_after=True):
    filename = os.path.join(CONFIG['temp_path'], filename)
    if not os.path.exists(filename):
        return None
    with open(filename, 'rb') as open_file:
        pickled_data = open_file.read()
    if delete_after:
        try:
            os.remove(filename)
        except:  # pylint: disable=bare-except
            pass
    return pickle.loads(pickled_data)


def notify_all(encoding, method, data):
    next_data = json.dumps(data)
    if not isinstance(next_data, bytes):
        next_data = next_data.encode('utf-8')

    if encoding == 'base64':
        from base64 import b64encode  # pylint: disable=import-outside-toplevel
        data = b64encode(next_data)
        if PY3:
            data = data.decode('ascii')
    elif encoding == 'hex':
        from binascii import hexlify  # pylint: disable=import-outside-toplevel
        if PY3:
            if not isinstance(next_data, bytes):
                next_data = next_data.encode('utf-8')
            data = hexlify(next_data).decode('utf-8')
        else:
            data = hexlify(next_data)

    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "JSONRPC.NotifyAll",
        "params": {
            "sender": "%s.SIGNAL" % CONFIG['id'],
            "message": method,
            "data": [data],
        }
    }

    xbmc.executeJSONRPC(json.dumps(jsonrpc_request))


def jsonrpc_play(url):
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "player.open",
        "params": {
            "item": {
                "file": url
            }
        }
    }

    xbmc.executeJSONRPC(json.dumps(jsonrpc_request))


def wait_for_busy_dialog():
    """
    Wait for busy dialogs to close, starting playback while the busy dialog is active
    could crash Kodi 18 / 19 (pre-alpha)

    Github issues:
        https://github.com/xbmc/xbmc/issues/16756
        https://github.com/xbmc/xbmc/pull/16450  # possible solution

    TODO: remove this function when the above issue is resolved
    """
    monitor = xbmc.Monitor()
    start_time = time.time()
    xbmc.sleep(500)

    def _abort():
        return monitor.abortRequested()

    def _busy():
        return xbmcgui.getCurrentWindowDialogId() in [10138, 10160]

    def _wait():
        LOG.debug('Waiting for busy dialogs to close ...')
        while not _abort() and _busy():
            if monitor.waitForAbort(1):
                break

    while not _abort():
        if _busy():
            _wait()

        if monitor.waitForAbort(1):
            break

        if not _busy():
            break

    LOG.debug('Waited %.2f for busy dialogs to close.' % (time.time() - start_time))
    return not _abort() and not _busy()


def get_file_type(filename):
    if filename[0:2] == '\\\\':
        LOG.debug('Detected UNC source file')
        return 'UNC'
    if filename[0:1] in ['/', '\\']:
        LOG.debug('Detected unix source file')
        return 'NIX'
    if filename[1:3] == ':\\' or filename[1:2] == ':/':
        LOG.debug('Detected windows source file')
        return 'WIN'

    LOG.debug('Unknown file type source: %s' % filename)
    return None
