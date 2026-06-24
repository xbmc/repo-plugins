# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - playback scheduler
#
# Turns a channel definition into playable items.
#
#   serial_random : pick a random title, then play ITS NEXT episode in order,
#                   advancing a per-title cursor (wraps after the finale).
#   pure_random   : pick a random title, then a random episode/movie from it.
#
# Two cursors are kept deliberately separate:
#   - the LOOKAHEAD cursor (passed in here) advances as items are GENERATED, so
#     successive queue entries for one show step through its episodes;
#   - the saved RESUME pointer (in storage state) advances only as items are
#     actually PLAYED (the service records that). Keeping them apart is what
#     fixes "queueing 30 ahead jumps my position 30 forward".
#
# Movies are a one-item sequence. Each positions entry is [title_key, index,
# file] so the service can both record progress and verify it owns the playback.

import random

import xbmcgui

from resources.lib import library
from resources.lib import storage

INITIAL_SIZE = 30
UNLIMITED_CONSEC = 999   # the "Unlimited" back-to-back count (matches the editor)


# ----------------------------------------------------------------------------
# Internal
# ----------------------------------------------------------------------------

def _key(item):
    return storage.item_key(item)


def _sequence_for(item, cache):
    """Ordered playables for one title, memoised within a single build pass."""
    key = _key(item)
    if key not in cache:
        if item['type'] == 'movie':
            cache[key] = library.get_movie_playables(item['dbid'])
        elif item['type'] == 'movieset':
            cache[key] = library.get_movieset_playables(item['dbid'])
        elif item['type'] == 'season':
            cache[key] = library.get_season_playables(item['dbid'], item['season'])
        elif item['type'] == 'folder':
            cache[key] = library.get_folder_playables(item['path'])
        else:
            cache[key] = library.get_episode_playables(item['dbid'])
    return cache[key]


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------

def _choose_title(items, last_key, run, max_consecutive, always=False):
    """Pick the next title given the back-to-back rule.
      - 'up to' (always=False): random each time, but never repeat the previous
        title once it has played `max_consecutive` times in a row.
      - 'always' (always=True): stick with the previous title until it has played
        EXACTLY `max_consecutive` in a row, then switch to a different one.
    A run only forces a switch when there is another title to switch to."""
    if last_key is not None and len(items) > 1:
        # 'always': keep the current title going until it reaches the count.
        if always and run < max_consecutive and max_consecutive < UNLIMITED_CONSEC:
            current = next((i for i in items if _key(i) == last_key), None)
            if current is not None:
                return current
        # Both modes: once the count is reached, force a different title.
        if run >= max_consecutive:
            alternatives = [i for i in items if _key(i) != last_key]
            if alternatives:
                return random.choice(alternatives)
    return random.choice(items)


def build_items(items, mode, cursor, count, max_consecutive=1,
                last_key=None, run=0, always=False, cache=None):
    """Generate `count` playables. `cursor` (title_key -> next index) is mutated
    in place for serial_random so callers can persist the lookahead position.
    `max_consecutive` is the back-to-back count; `always` switches it from a cap
    ("up to N") to a fixed run ("always N"). `last_key`/`run` carry the current
    run length in so it holds across top-ups. Returns (picks, positions, last_key,
    run) where positions[i] is [title_key, index, file]."""
    if cache is None:
        cache = {}
    if not items:
        return [], [], last_key, run

    picks = []
    positions = []
    guard = 0
    limit = count * 8 + 8
    while len(picks) < count and guard < limit:
        guard += 1
        title = _choose_title(items, last_key, run, max_consecutive, always)
        sequence = _sequence_for(title, cache)
        if not sequence:
            continue

        title_key = _key(title)
        if mode == 'pure_random':
            index = random.randrange(len(sequence))
        else:
            index = cursor.get(title_key, 0) % len(sequence)
            cursor[title_key] = (index + 1) % len(sequence)

        pick = sequence[index]
        picks.append(pick)
        positions.append([title_key, index, pick['file']])

        if title_key == last_key:
            run += 1
        else:
            last_key = title_key
            run = 1

    return picks, positions, last_key, run


def make_list_item(pick):
    """Build a playable Kodi ListItem for one queue entry."""
    list_item = xbmcgui.ListItem(label=pick['label'])
    tag = list_item.getVideoInfoTag()
    tag.setTitle(pick['label'])
    tag.setPlot(pick.get('plot', ''))
    if pick.get('art'):
        list_item.setArt(pick['art'])
    return list_item
