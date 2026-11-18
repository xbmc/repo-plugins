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


# ----------------------------------------------------------------------------
# Per-show overrides
#
# Two INDEPENDENT per-title dials, both optional and both defaulting to "off":
#
#   consec_overrides : {title_key: {"count": N, "always": bool}}
#       How many of this title play in a row before a switch is forced. A title
#       WITHOUT an entry inherits the channel's max_consecutive / consec_always.
#       This only changes BLOCK LENGTH - it does not make the title picked more.
#
#   weights          : {title_key: N}
#       How OFTEN this title is picked when a new title is chosen. A title WITHOUT
#       an entry weighs 1 (normal). This lives with the channel selector (Mode),
#       not with back-to-back, because "picked more" and "runs longer" are separate
#       ideas. When every title weighs the same, weighted selection is identical to
#       a plain uniform random.choice - so an override-free channel behaves exactly
#       as before.
# ----------------------------------------------------------------------------

def _effective_consec(title_key, default_count, default_always, overrides):
    """Resolve (count, always) for one title: its consec override if present, else
    the channel default."""
    entry = overrides.get(title_key) if overrides else None
    if entry:
        return entry.get('count', default_count), entry.get('always', default_always)
    return default_count, default_always


NOREPEAT_WINDOW_CAP = 100   # hard cap on how many recent episodes we remember per title


def _next_shuffled(decks, key, length):
    """pure_random episode picker with a sliding NO-REPEAT WINDOW: never redraw any of
    the last ~2/3 of a title's episodes, so an episode cannot recur until most of the
    rest have played (this kills the 'same episode again 4-5 plays later' bug) while the
    pick stays genuinely random among the remaining candidates. `decks` (title_key ->
    list of recently-played indices) is mutated in place and persisted with the cursor."""
    if length <= 1:
        return 0
    window = min(length - 1, max(1, length * 2 // 3), NOREPEAT_WINDOW_CAP)
    recent = decks.get(key)
    if not isinstance(recent, list):
        recent = []
    recent_set = set(recent)
    candidates = [i for i in range(length) if i not in recent_set]
    if not candidates:                    # safety net (window is always < length)
        candidates = list(range(length))
    index = random.choice(candidates)
    recent.append(index)
    decks[key] = recent[-window:]         # remember only the last `window` played
    return index


def _weighted_choice(items, weights):
    """Pick one item, biased by the per-title selection weight (a float, default 1.0;
    fractional weights like 1.2 are meaningful and are NOT rounded). With no weights
    (or all-equal weights) this is a plain uniform pick."""
    if weights:
        picks = [max(0.0001, float(weights.get(_key(i), 1.0))) for i in items]
        return random.choices(items, weights=picks, k=1)[0]
    return random.choice(items)


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

def _draw_target(count, always, seq_len):
    """Episodes to play in ONE visit to a title - the back-to-back run length:
      - 'always N' : exactly N (a fixed run).
      - 'up to N'  : a UNIFORM roll in [1, N] - every length 1..N equally likely, so
                     'up to 8' is a single 1-8 dice roll, NOT a per-episode coin flip.
      - 'unlimited': the whole title in one visit.
    Run LENGTH (this) and how OFTEN a title is picked (its weight) are separate axes;
    total screen time is their product."""
    if always:
        return max(1, count)
    if count >= UNLIMITED_CONSEC:
        return max(1, seq_len)
    return random.randint(1, count)


def build_items(items, mode, cursor, count, max_consecutive=1,
                last_key=None, run=0, always=False, cache=None,
                consec_overrides=None, weights=None, target=0):
    """Generate `count` playables one VISIT at a time: weighted-pick a title, roll its
    run length, then emit that many episodes before picking again. `cursor` (title_key
    -> next index) is mutated in place for serial_random so callers can persist the
    lookahead position. `max_consecutive`/`always` are the channel default back-to-back
    count and mode; `consec_overrides`/`weights` are the optional per-show dials (see the
    header). `last_key`/`run`/`target` carry the IN-PROGRESS visit (its title, episodes
    played so far, and its rolled length) so a visit survives across top-ups. Returns
    (picks, positions, last_key, run, target); positions[i] is [title_key, index, file]."""
    if cache is None:
        cache = {}
    if not items:
        return [], [], last_key, run, target

    picks = []
    positions = []
    guard = 0
    limit = count * 8 + 8
    while len(picks) < count and guard < limit:
        guard += 1

        # Still inside the current visit? Keep the same title; otherwise start a new
        # visit with a fresh weighted pick of a DIFFERENT title (each appearance is one
        # bounded visit - a show never immediately follows itself). With a single title
        # there is nothing else to switch to, so it just continues.
        title = None
        if last_key is not None and run < target:
            title = next((i for i in items if _key(i) == last_key), None)
        starting_visit = title is None
        if starting_visit:
            pool = [i for i in items if _key(i) != last_key] or items
            title = _weighted_choice(pool, weights)
            last_key = _key(title)
            run = 0

        sequence = _sequence_for(title, cache)
        if not sequence:
            last_key = None          # dead title - abandon this visit, pick again
            run = 0
            target = 0
            continue

        title_key = _key(title)
        if starting_visit:           # roll the run length now that we know the title
            visit_count, visit_always = _effective_consec(
                title_key, max_consecutive, always, consec_overrides)
            target = _draw_target(visit_count, visit_always, len(sequence))

        if mode == 'pure_random':
            index = _next_shuffled(cursor, title_key, len(sequence))
        else:
            index = cursor.get(title_key, 0) % len(sequence)
            cursor[title_key] = (index + 1) % len(sequence)

        pick = sequence[index]
        picks.append(pick)
        # [title_key, index, file, dbid, mediatype] - the trailing two let the service
        # restore watched-state (None for folder files, which are not in the library).
        positions.append([title_key, index, pick['file'],
                          pick.get('dbid'), pick.get('mediatype')])
        run += 1

    return picks, positions, last_key, run, target


def make_list_item(pick):
    """Build a playable Kodi ListItem for one queue entry."""
    list_item = xbmcgui.ListItem(label=pick['label'])
    tag = list_item.getVideoInfoTag()
    tag.setTitle(pick['label'])
    tag.setPlot(pick.get('plot', ''))
    if pick.get('art'):
        list_item.setArt(pick['art'])
    return list_item
