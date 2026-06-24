# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - persistent storage
#
# Channel definitions and playback state live in a single JSON file inside the
# addon's private profile folder, e.g. on Windows:
#   %APPDATA%\Kodi\userdata\addon_data\plugin.video.channelme\channels.json
#
# Schema:
#   {
#     "channels": [
#       {
#         "id": "ch_0001",
#         "name": "Saturday Mornings",
#         "mode": "serial_random" | "pure_random",
#         "items": [ {"type": "tvshow"|"movie", "dbid": 12, "title": "..."} ]
#       }
#     ],
#     "state": { "ch_0001": { ... per-channel playback position ... } }
#   }

import json
import os

import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
NAME = ADDON.getAddonInfo('name')
DATA_FILE = os.path.join(PROFILE, 'channels.json')


def L(string_id):
    """A localized UI string from resources/language/.../strings.po."""
    return ADDON.getLocalizedString(string_id)

# Custom icon shown on notification ("alert") pop-ups.
ALERT_ICON = os.path.join(ADDON_PATH, 'resources', 'AlertIcon.png')

# A seed channel so a fresh install has something to look at and click.
DEFAULT_DATA = {
    'channels': [
        {
            'id': 'ch_0001',
            'name': 'Sample Channel (edit me)',
            'mode': 'serial_random',
            'items': [],
        }
    ],
    'state': {},
}


# ----------------------------------------------------------------------------
# Internal
# ----------------------------------------------------------------------------

def _ensure_profile():
    if not xbmcvfs.exists(PROFILE):
        xbmcvfs.mkdirs(PROFILE)


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------

def load():
    """Return the stored data, creating it from the default seed if absent."""
    _ensure_profile()
    if not os.path.exists(DATA_FILE):
        save(DEFAULT_DATA)
        return json.loads(json.dumps(DEFAULT_DATA))  # return a fresh copy
    with open(DATA_FILE, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def save(data):
    """Write the full data structure back to disk."""
    _ensure_profile()
    with open(DATA_FILE, 'w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2)


def item_key(item):
    """Stable identity for a channel/playback item, used everywhere a dict needs a
    string handle. Folders key on their path and seasons on tvshow+season (neither
    has a Kodi dbid); everything else keys on '<type>:<dbid>'."""
    item_type = item['type']
    if item_type == 'folder':
        return 'folder:{0}'.format(item.get('path', ''))
    if item_type == 'season':
        return 'season:{0}:{1}'.format(item.get('dbid'), item.get('season'))
    return '{0}:{1}'.format(item_type, item.get('dbid'))


def next_channel_id(data):
    """Return the next free 'ch_NNNN' id given the current data."""
    highest = 0
    for channel in data.get('channels', []):
        cid = channel.get('id', '')
        if cid.startswith('ch_'):
            try:
                highest = max(highest, int(cid[3:]))
            except ValueError:
                pass
    return 'ch_{0:04d}'.format(highest + 1)
