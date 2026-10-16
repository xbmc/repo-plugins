# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

import json
import importlib

import xbmc

from resources.lib.log import log


def get_system_setting(setting_id):
    json_str = ('{{"jsonrpc": "2.0", "method": "Settings.GetSettingValue", "params": ["{}"], "id": 1}}'.
                format(setting_id))
    response = xbmc.executeJSONRPC(json_str)
    data = json.loads(response)
    try:
        return data['result']['value']
    except KeyError:
        msg = data.get('message') or "Failed to get setting"
        log("get_system_setting failed for setting_id '%s': '%s'", setting_id, msg)
        raise ValueError('system setting error: {}'.format(msg))


def local_tz():
    """Return the local time zone from Kodi's settings as a ZoneInfo object.
    Revert to the timezone provided by tzlocal on older Kodi versions, which
    in turn reverts to UTC if the OS provides none.

    """
    ltz = getattr(local_tz, '_ltz_', None)

    if ltz is None:
        from resources.lib.utils import ZoneInfo

        try:
            local_tz._ltz_ = ltz = ZoneInfo(get_system_setting('locale.timezone'))
        except (TypeError, ValueError):
            # To be Matrix compatible
            log("No Kodi timezone setting found, falling back to tzlocal")
            tzlocal = importlib.import_module('tzlocal')
            local_tz._ltz_ = ltz = tzlocal.get_localzone()
    return ltz


def kodi_version():
    vers = getattr(kodi_version, '_vers_', None)
    if vers is None:
        version_code = xbmc.getInfoLabel('System.BuildVersionCode')
        kodi_version._vers_ = vers = tuple(int(v) for v in version_code.split('.'))
    return vers
