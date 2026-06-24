# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - channel add / edit / remove operations.
#
# The add/edit experience is a skinned editor window (resources/lib/editor.py):
# a sidebar of categories on the left, a content panel on the right, and
# Save/Cancel buttons. This module owns only the persistence around it: build a
# working copy, run the editor, and commit the result to channels.json.

import xbmcgui

from resources.lib import editor
from resources.lib import storage


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _key(item):
    """Stable identity for a channel item (delegates to storage.item_key)."""
    return storage.item_key(item)


def _find(data, channel_id):
    return next((c for c in data.get('channels', []) if c['id'] == channel_id), None)


def _notify(message):
    xbmcgui.Dialog().notification(storage.NAME, message, storage.ALERT_ICON, 3000)


def _apply_start_points(data, channel_id, items, start_points):
    """Write chosen starting episodes into the channel's resume pointers."""
    item_keys = {_key(item) for item in items}
    pointers = data.setdefault('state', {}).setdefault(channel_id, {}).setdefault('pointers', {})
    for key, index in start_points.items():
        if key in item_keys:
            pointers[key] = index


# ----------------------------------------------------------------------------
# Channel operations (called by the router)
# ----------------------------------------------------------------------------

def add_channel(seed_items=None):
    """Open the editor on a new channel. `seed_items`, when given (e.g. from
    'Add to Channel' -> new channel), pre-populates the title list and, for a
    single seed, the channel name."""
    seed_items = seed_items or []
    name = seed_items[0].get('title', '') if len(seed_items) == 1 else ''
    working = {'name': name, 'mode': 'pure_random', 'items': list(seed_items),
               'art_source_key': None, 'max_consecutive': 2, 'consec_always': False,
               'start_points': {}}
    if not editor.run(storage.ADDON_PATH, working, is_new=True):
        return False

    data = storage.load()
    channel_id = storage.next_channel_id(data)
    start_points = working.pop('start_points', {})   # belongs in state, not the record
    working['id'] = channel_id
    data['channels'].append(working)
    _apply_start_points(data, channel_id, working['items'], start_points)
    storage.save(data)
    _notify(storage.L(32100).format(working['name']))
    return True


def edit_channel(channel_id):
    data = storage.load()
    channel = _find(data, channel_id)
    if channel is None:
        return False

    existing_pointers = data.get('state', {}).get(channel_id, {}).get('pointers', {})
    working = {
        'name': channel['name'],
        'mode': channel.get('mode', 'pure_random'),
        'items': list(channel.get('items', [])),
        'art_source_key': channel.get('art_source_key'),
        'max_consecutive': channel.get('max_consecutive', 2),
        'consec_always': channel.get('consec_always', False),
        'start_points': dict(existing_pointers),   # seed from current positions
    }
    if not editor.run(storage.ADDON_PATH, working, is_new=False):
        return False

    channel['name'] = working['name']
    channel['mode'] = working['mode']
    channel['items'] = working['items']
    channel['art_source_key'] = working['art_source_key']
    channel['max_consecutive'] = working['max_consecutive']
    channel['consec_always'] = working['consec_always']
    _apply_start_points(data, channel_id, channel['items'], working['start_points'])
    storage.save(data)
    _notify(storage.L(32101).format(working['name']))
    return True


def _item_from_params(params):
    """A persistable channel item from context-item params. Seasons are excluded -
    channels are built from whole shows / sets / folders."""
    item_type = params.get('type')
    title = params.get('title', '')
    if item_type == 'tvshow':
        return {'type': 'tvshow', 'dbid': int(params['dbid']), 'title': title}
    if item_type == 'movieset':
        return {'type': 'movieset', 'dbid': int(params['dbid']), 'title': title}
    if item_type == 'folder' and params.get('path'):
        return {'type': 'folder', 'path': params['path'], 'title': title}
    return None


def add_to_channel(params):
    """Append a library show / set / folder to a chosen channel (or a new one),
    deduping by item key. Notify only - path management happens later in the editor
    File filter."""
    item = _item_from_params(params)
    if item is None:
        _notify(storage.L(32117))
        return False

    data = storage.load()
    channels = data.get('channels', [])
    labels = [channel['name'] for channel in channels] + [storage.L(32114)]
    choice = xbmcgui.Dialog().select(storage.L(32113), labels)
    if choice < 0:
        return False
    if choice == len(channels):           # last row == "[ New channel ]"
        return add_channel([item])

    channel = channels[choice]
    key = _key(item)
    if any(_key(existing) == key for existing in channel.get('items', [])):
        _notify(storage.L(32116).format(item['title'], channel['name']))
        return False
    channel.setdefault('items', []).append(item)
    storage.save(data)
    _notify(storage.L(32115).format(item['title'], channel['name']))
    return True


def reset_progress(channel_id):
    """Clear the per-title resume pointers so the channel starts fresh."""
    data = storage.load()
    channel_state = data.get('state', {}).get(channel_id)
    if channel_state and channel_state.get('pointers'):
        channel_state['pointers'] = {}
        storage.save(data)
    _notify(storage.L(32102))
    return True


def remove_channel(channel_id):
    data = storage.load()
    channel = _find(data, channel_id)
    if channel is None:
        return False

    if not xbmcgui.Dialog().yesno(storage.NAME, storage.L(32104).format(channel['name'])):
        return False

    data['channels'] = [c for c in data['channels'] if c['id'] != channel_id]
    data.get('state', {}).pop(channel_id, None)
    storage.save(data)
    _notify(storage.L(32103).format(channel['name']))
    return True
