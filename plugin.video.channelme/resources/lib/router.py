# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - plugin routing.
#
# Reached from default.py on every open/click/context action: reads the action
# out of the plugin URL and dispatches to the channel list, playback, or the
# add/edit/remove flows.
#
# Channel rows are folder items carrying a video infotag:
#   - the infotag plot restores the on-hover info panel (Mode + title list);
#   - being a FOLDER stops Kodi auto-adding Queue / Play next / Mark watched to
#     the context menu (Kodi 19+ ignores the old replaceItems flag);
#   - "entering" the folder is what starts playback.

import random
import sys
import time
import urllib.parse

import xbmc
import xbmcgui
import xbmcplugin

from resources.lib import gui
from resources.lib import library
from resources.lib import scheduler
from resources.lib import storage


# ----------------------------------------------------------------------------
# URL helpers
# ----------------------------------------------------------------------------

BASE_URL = sys.argv[0]
HANDLE = int(sys.argv[1])


def build_url(**kwargs):
    """Build a plugin:// url that points back at this addon with parameters."""
    return BASE_URL + '?' + urllib.parse.urlencode(kwargs)


def channel_episode_total(channel, show_counts, set_counts):
    """Total playables in a channel: show episode counts, movie-set film counts,
    plus 1 per standalone movie."""
    total = 0
    for item in channel.get('items', []):
        if item['type'] == 'tvshow':
            total += show_counts.get(item['dbid'], 0)
        elif item['type'] == 'movieset':
            total += set_counts.get(item['dbid'], 0)
        else:
            total += 1
    return total


def display_name(name):
    """Channel name as shown in the list - append 'Channel' unless already there."""
    if name.strip().lower().endswith('channel'):
        return name
    return storage.L(32071).format(name)


def channel_plot(channel, total_episodes):
    """Multi-line text for the info panel: counts, mode, then the list of titles.
    Labels are bold ([B]); the [TV]/[Set]/[Movie] tags are dropped here (they only
    matter in the selection checklist)."""
    mode_labels = {
        'serial_random': storage.L(32052),
        'pure_random': storage.L(32053),
    }
    consec = channel.get('max_consecutive', 2)
    if consec >= 999:
        consec_label = storage.L(32060)                 # Unlimited
    else:
        # "Up to N" (cap) or "Always N" (fixed run).
        word = storage.L(32066) if channel.get('consec_always') else storage.L(32065)
        consec_label = '{0} {1}'.format(word, consec)
    mode = channel.get('mode', 'pure_random')
    lines = [
        '[B]{0}[/B] {1}'.format(storage.L(32072), total_episodes),
        '[B]{0}[/B] {1}'.format(storage.L(32073), mode_labels.get(mode, mode)),
        '[B]{0}[/B] {1}'.format(storage.L(32074), consec_label),
        '',
        '[B]{0}[/B]'.format(storage.L(32075).format(len(channel.get('items', [])))),
    ]
    for item in channel.get('items', []):
        title = item['title']
        if item['type'] == 'movie' and item.get('year'):
            title = '{0} ({1})'.format(title, item['year'])
        lines.append('- {0}'.format(title))
    return '\n'.join(lines)


# ----------------------------------------------------------------------------
# Artwork
# ----------------------------------------------------------------------------

def _item_key(item):
    return storage.item_key(item)


def channel_art(channel):
    """Pick a source title (pinned, else random) and return its art mapped onto
    Kodi art keys. Re-rolled every render, so a Random channel changes on reload."""
    items = channel.get('items', [])
    if not items:
        return {}

    source = None
    pinned = channel.get('art_source_key')
    if pinned:
        source = next((i for i in items if _item_key(i) == pinned), None)
    if source is None:
        source = random.choice(items)

    art = library.get_art(source)
    chosen = {}
    for name in ('poster', 'fanart', 'banner', 'landscape', 'clearlogo', 'thumb'):
        if art.get(name):
            chosen[name] = art[name]
    if 'thumb' not in chosen and art.get('poster'):
        chosen['thumb'] = art['poster']
    if chosen:
        chosen.setdefault('icon', chosen.get('poster') or chosen.get('thumb'))
    return chosen


# ----------------------------------------------------------------------------
# Views
# ----------------------------------------------------------------------------

def list_channels(update=False):
    """Draw every channel as a folder, then an 'add' row at the bottom."""
    data = storage.load()
    channels = data.get('channels', [])

    xbmcplugin.setPluginCategory(HANDLE, storage.L(32070))
    # 'movies' content unlocks the rich views (List etc.) and a clean context menu.
    # The header breadcrumb's first word ("Movies") is Kodi's section title for that
    # content type - it can't be set to the addon name, and dropping the content
    # type collapses the window to WideList only. So we keep 'movies' for the layout.
    xbmcplugin.setContent(HANDLE, 'movies')
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LABEL)
    # "Last played" uses the per-channel timestamp stamped by play_channel; the
    # native sort method reads the ListItem's lastplayed infotag set below.
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_LASTPLAYED)

    show_counts, set_counts = library.get_count_maps()
    state = data.get('state', {})

    for channel in channels:
        total_episodes = channel_episode_total(channel, show_counts, set_counts)

        list_item = xbmcgui.ListItem(label=display_name(channel['name']))

        tag = list_item.getVideoInfoTag()
        tag.setTitle(display_name(channel['name']))
        tag.setPlot(channel_plot(channel, total_episodes))

        last_played = state.get(channel['id'], {}).get('last_played')
        if last_played:
            tag.setLastPlayed(last_played)

        art = channel_art(channel)
        if art:
            list_item.setArt(art)

        list_item.addContextMenuItems([
            (storage.L(32021), 'RunPlugin({0})'.format(build_url(action='edit', channel=channel['id']))),
            (storage.L(32080), 'RunPlugin({0})'.format(build_url(action='reset', channel=channel['id']))),
            (storage.L(32081), 'RunPlugin({0})'.format(build_url(action='remove', channel=channel['id']))),
            (storage.L(32082), 'RunPlugin({0})'.format(build_url(action='add'))),
        ])

        play_url = build_url(action='play', channel=channel['id'])
        xbmcplugin.addDirectoryItem(HANDLE, play_url, list_item, isFolder=True)

    # 'Add new channel' lives at the BOTTOM, below the channels - SpecialSort pins
    # it there no matter which "Sort by" the user picks.
    add_item = xbmcgui.ListItem(label=storage.L(32076))
    add_item.setProperty('SpecialSort', 'bottom')
    xbmcplugin.addDirectoryItem(HANDLE, build_url(action='add'), add_item, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE, succeeded=True, updateListing=update)


def _end_handle():
    """Close a folder request without leaving the user in an empty directory."""
    if HANDLE >= 0:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)


def play_channel(channel_id):
    """Build the channel's opening queue, hand the service a playback block so it
    can record progress and keep topping up, then start playback."""
    data = storage.load()
    channel = next((c for c in data.get('channels', []) if c['id'] == channel_id), None)

    if channel is None or not channel.get('items'):
        xbmcgui.Dialog().notification(storage.NAME, storage.L(32090),
                                      storage.ALERT_ICON, 3000)
        _end_handle()
        return

    mode = channel.get('mode', 'pure_random')
    max_consecutive = channel.get('max_consecutive', 2)
    consec_always = channel.get('consec_always', False)
    pointers = data.get('state', {}).get(channel_id, {}).get('pointers', {})
    cursor = dict(pointers)   # start generating from the saved resume position
    picks, positions, last_key, run = scheduler.build_items(
        channel['items'], mode, cursor, scheduler.INITIAL_SIZE, max_consecutive,
        always=consec_always)

    if not picks:
        xbmcgui.Dialog().notification(storage.NAME, storage.L(32091),
                                      storage.ALERT_ICON, 4000)
        _end_handle()
        return

    # Hand the service everything it needs to record progress and top up. The
    # session counter lets the service distinguish a fresh start from a jump.
    # Stamp this channel as just-played so the list can offer "last played" sorting.
    data.setdefault('state', {}).setdefault(channel_id, {})['last_played'] = \
        time.strftime('%Y-%m-%d %H:%M:%S')

    session = data.get('playback_seq', 0) + 1
    data['playback_seq'] = session
    data['playback'] = {
        'channel_id': channel_id,
        'mode': mode,
        'titles': channel['items'],
        'positions': positions,
        'lookahead': cursor,
        'max_consecutive': max_consecutive,
        'consec_always': consec_always,
        'last_key': last_key,
        'run': run,
        'session': session,
    }
    storage.save(data)

    _launch_playlist(picks)
    _notify(storage.L(32092).format(channel['name']))


def _notify(message):
    xbmcgui.Dialog().notification(storage.NAME, message, storage.ALERT_ICON, 3000)


def _launch_playlist(picks):
    """Replace the video playlist with `picks` and start playing. The folder handle
    (if any) is closed first so we never leave the user in an empty directory."""
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    for pick in picks:
        playlist.add(pick['file'], scheduler.make_list_item(pick))
    _end_handle()
    xbmc.Player().play(playlist)


# ----------------------------------------------------------------------------
# Play Randomized (ephemeral - library context item, no saved channel)
# ----------------------------------------------------------------------------

def _resolve_random_item(params):
    """Turn the context-item parameters into a single channel item dict."""
    item_type = params.get('type')
    title = params.get('title', '')
    if item_type == 'tvshow':
        return {'type': 'tvshow', 'dbid': int(params['dbid']), 'title': title}
    if item_type == 'movieset':
        return {'type': 'movieset', 'dbid': int(params['dbid']), 'title': title}
    if item_type == 'season':
        return {'type': 'season', 'dbid': int(params['dbid']),
                'season': int(params['season']), 'title': title}
    if item_type == 'folder' and params.get('path'):
        return {'type': 'folder', 'path': params['path'], 'title': title}
    return None


def play_random(params):
    """Play one library item (show / set / season / folder) ephemerally in
    pure_random. No channel is saved; the service tops the queue up endlessly via
    a transient playback block whose channel_id is null."""
    item = _resolve_random_item(params)
    if item is None:
        _notify(storage.L(32111))
        _end_handle()
        return

    items = [item]
    cursor = {}
    # A single title makes the back-to-back cap moot, so leave it unlimited.
    picks, positions, last_key, run = scheduler.build_items(
        items, 'pure_random', cursor, scheduler.INITIAL_SIZE, max_consecutive=999)
    if not picks:
        _notify(storage.L(32111))
        _end_handle()
        return

    data = storage.load()
    session = data.get('playback_seq', 0) + 1
    data['playback_seq'] = session
    data['playback'] = {
        'channel_id': None,        # ephemeral - records no resume pointers
        'mode': 'pure_random',
        'titles': items,
        'positions': positions,
        'lookahead': cursor,
        'max_consecutive': 999,
        'last_key': last_key,
        'run': run,
        'session': session,
    }
    storage.save(data)

    _launch_playlist(picks)
    _notify(storage.L(32092).format(item.get('title') or storage.L(32070)))


# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------

def refresh_after_mutation():
    """Redraw the channel list after add/edit/remove, handling both entry paths:
    a clicked folder item (real HANDLE) vs a context-menu RunPlugin (HANDLE -1)."""
    if HANDLE >= 0:
        list_channels(update=True)
    else:
        xbmc.executebuiltin('Container.Refresh')


def route(query_string):
    params = dict(urllib.parse.parse_qsl(query_string))
    action = params.get('action')
    channel_id = params.get('channel')

    if action == 'play':
        play_channel(channel_id)
    elif action == 'playrandom':
        play_random(params)
    elif action == 'addtochannel':
        # Invoked from the library (never from our own folders), so there is no
        # channel list on screen to refresh - the notification is the feedback.
        gui.add_to_channel(params)
    elif action == 'add':
        gui.add_channel()
        refresh_after_mutation()
    elif action == 'edit':
        gui.edit_channel(channel_id)
        refresh_after_mutation()
    elif action == 'reset':
        gui.reset_progress(channel_id)
        refresh_after_mutation()
    elif action == 'remove':
        gui.remove_channel(channel_id)
        refresh_after_mutation()
    else:
        list_channels()


def main():
    # sys.argv[2] is like "?action=play&channel=ch_0001"; drop the leading "?".
    route(sys.argv[2][1:])
