# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import json
import time
from binascii import hexlify
from copy import deepcopy

import xbmc  # pylint: disable=import-error
import xbmcgui  # pylint: disable=import-error

from ..constants import ADDON_ID
from .logger import Log

LOG = Log('lib', __file__)


def event_notification(method, data):
    data = json.dumps(deepcopy(data)).encode('utf-8')
    data = hexlify(data).decode('utf-8')
    jsonrpc_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "JSONRPC.NotifyAll",
        "params": {
            "sender": "%s.SIGNAL" % ADDON_ID,
            "message": method,
            "data": [data],
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


def addon_enabled(addon_id):
    rpc_request = json.dumps({
        "jsonrpc": "2.0",
        "method": "Addons.GetAddonDetails",
        "id": 1,
        "params": {
            "addonid": "%s" % addon_id,
            "properties": ["enabled"]
        }
    })
    response = json.loads(xbmc.executeJSONRPC(rpc_request))
    try:
        return response['result']['addon']['enabled'] is True
    except KeyError:
        message = response['error']['message']
        code = response['error']['code']
        error = 'Requested {request} and received error {error} and code: {code}' \
            .format(request=rpc_request, error=message, code=code)
        LOG.error(error)
        return False


def set_addon_enabled(addon_id, enabled=True):
    rpc_request = json.dumps({
        "jsonrpc": "2.0",
        "method": "Addons.SetAddonEnabled",
        "id": 1,
        "params": {
            "addonid": "%s" % addon_id,
            "enabled": enabled
        }
    })
    response = json.loads(xbmc.executeJSONRPC(rpc_request))
    try:
        return response['result'] == 'OK'
    except KeyError:
        message = response['error']['message']
        code = response['error']['code']
        error = 'Requested {request} and received error {error} and code: {code}' \
            .format(request=rpc_request, error=message, code=code)
        LOG.error(error)
        return False


def prompt_to_enable_inputstream_adaptive(context):
    enabled = addon_enabled('inputstream.adaptive')

    if not enabled:
        if xbmcgui.Dialog().yesno(context.addon.getAddonInfo('name'),
                                  context.i18n('InputStream Adaptive is required '
                                               'and appears to be disabled. Would '
                                               'you like to enable InputStream '
                                               'Adaptive now?')):
            enabled = set_addon_enabled('inputstream.adaptive')

    return enabled
