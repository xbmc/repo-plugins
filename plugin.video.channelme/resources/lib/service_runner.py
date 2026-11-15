# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - background service logic (driven by service.py).
#
# Runs continuously while Kodi is open and manages the channel that is currently
# playing (described by the storage 'playback' block written when a channel is
# started). Three jobs:
#
#   1. Record progress: when an item starts, the show's saved resume pointer is
#      set to the episode ACTUALLY playing - so stopping mid-episode resumes that
#      episode (serial_random only).
#   2. Keep it endless: when playback nears the end of the queue, more items are
#      generated and appended to the live playlist.
#   3. Regenerate on manual jump: if the user skips ahead/back in the playlist
#      (position moves by more than +1), the stale future is trimmed and rebuilt
#      so skipped shows resume from where they were actually last watched, while
#      the show jumped to continues from there.
#
# A positions entry is [title_key, index, file]; the file confirms the item now
# playing is really ours before we touch pointers or the playlist.

import json
import time

import xbmc
import xbmcgui

from resources.lib import scheduler
from resources.lib import sleeptimer
from resources.lib import storage

# The standalone "Now Playing" video playlist window. Browsing it while we mutate
# the live playlist by JSON-RPC makes the GUI fight our edits, so we step out of
# it before regenerating.
WINDOW_VIDEO_PLAYLIST = 10028

TOPUP_THRESHOLD = 10   # generate more when this few items remain ahead
TOPUP_BATCH = 20
POLL_SECONDS = 5

# Tracks the last owned position so we can spot manual jumps across item starts.
_LAST = {'session': None, 'pos': None}

# Tracks which sleep deadline we have already shown the warning for (so the once-per-
# deadline countdown is not re-popped every poll).
_SLEEP = {'warned_deadline': None}

# Watched-state preservation ("Don't change watched status"). `current` is the pre-play
# snapshot of the item on screen now; `restores` are items that have finished/stopped and
# whose snapshot we re-assert for a short window to beat Kodi's delayed watched write.
_WATCHED = {'current': None, 'restores': []}
RESTORE_WINDOW = 20   # seconds to keep re-asserting a restore after an item ends


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _log(message):
    xbmc.log('ChannelMe! ' + message, xbmc.LOGINFO)


def _video_playlist():
    return xbmc.PlayList(xbmc.PLAYLIST_VIDEO)


def _owned_position(playback):
    """Current playlist index if the item playing matches our recorded session,
    else None (so we never write progress / append onto unrelated playback)."""
    positions = playback.get('positions') or []
    pos = _video_playlist().getposition()
    if pos < 0 or pos >= len(positions):
        return None
    try:
        playing = xbmc.Player().getPlayingFile()
    except Exception:
        return None
    expected = positions[pos][2] if len(positions[pos]) >= 3 else None
    if expected and playing and expected != playing:
        return None
    return pos


def _playlist_remove(index):
    """Remove one item from the video playlist by position (reliable by index)."""
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Playlist.Remove',
               'params': {'playlistid': xbmc.PLAYLIST_VIDEO, 'position': index}}
    xbmc.executeJSONRPC(json.dumps(request))


def _leave_playlist_window():
    """If the user is sitting in the Now Playing playlist window, step out before we
    rebuild the playlist - editing it underneath the open window conflicts."""
    if xbmcgui.getCurrentWindowId() == WINDOW_VIDEO_PLAYLIST:
        xbmc.executebuiltin('Action(Back)')


# ----------------------------------------------------------------------------
# Watched-state preservation ("Don't change watched status")
#
# When the setting is on, ChannelMe playback must leave the library's play-state exactly
# as it was: watched flag, play count, last-played, AND the resume ("continue") bookmark.
# We snapshot an item the moment it starts (pre-play values) and write those values back
# once it ends OR is stopped mid-episode. Because Kodi commits its own watched/resume
# change slightly after an item ends, each restore is re-asserted for RESTORE_WINDOW
# seconds by the poll loop.
# ----------------------------------------------------------------------------

def _rpc(method, params):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
    return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get('result', {}) or {}


def _video_details(dbid, mediatype):
    """Current playcount / lastplayed / resume for one library item, or None."""
    if mediatype == 'episode':
        return _rpc('VideoLibrary.GetEpisodeDetails',
                    {'episodeid': dbid, 'properties': ['playcount', 'lastplayed', 'resume']}
                    ).get('episodedetails')
    if mediatype == 'movie':
        return _rpc('VideoLibrary.GetMovieDetails',
                    {'movieid': dbid, 'properties': ['playcount', 'lastplayed', 'resume']}
                    ).get('moviedetails')
    return None


def _snapshot(dbid, mediatype):
    """Capture the pre-play watched-state of one library item."""
    details = _video_details(dbid, mediatype)
    if not details:
        return None
    return {'id': dbid, 'type': mediatype,
            'playcount': details.get('playcount', 0),
            'lastplayed': details.get('lastplayed', ''),
            'resume': details.get('resume', {}) or {}}


def _apply_snapshot(snap):
    """Write a snapshot's watched-state back onto its library item."""
    if not snap:
        return
    resume = snap.get('resume') or {}
    params = {'playcount': snap['playcount'], 'lastplayed': snap['lastplayed'],
              'resume': {'position': resume.get('position', 0),
                         'total': resume.get('total', 0)}}
    if snap['type'] == 'episode':
        params['episodeid'] = snap['id']
        _rpc('VideoLibrary.SetEpisodeDetails', params)
    elif snap['type'] == 'movie':
        params['movieid'] = snap['id']
        _rpc('VideoLibrary.SetMovieDetails', params)


def _differs(snap):
    """True if the library item's current state no longer matches the snapshot."""
    current = _video_details(snap['id'], snap['type'])
    if not current:
        return False
    resume = snap.get('resume') or {}
    cur_resume = current.get('resume', {}) or {}
    return (current.get('playcount', 0) != snap['playcount']
            or current.get('lastplayed', '') != snap['lastplayed']
            or int(cur_resume.get('position', 0)) != int(resume.get('position', 0)))


def _queue_restore(snap):
    """Restore a finished/stopped item now and keep re-asserting it for a short window."""
    if not snap:
        return
    _apply_snapshot(snap)
    _WATCHED['restores'].append({'snap': snap, 'until': time.time() + RESTORE_WINDOW})


def preserve_watched_on_start():
    """At each owned item start: restore the item that just finished, then snapshot the
    new one. A no-op (and state reset) unless 'Don't change watched status' is on and we
    own the current playback."""
    if not storage.get_bool_setting('dont_mark_watched'):
        _flush_current()
        return
    data = storage.load()
    playback = data.get('playback')
    pos = _owned_position(playback) if playback else None
    if pos is None:
        _flush_current()
        return

    entry = playback['positions'][pos]
    dbid = entry[3] if len(entry) > 3 else None
    mediatype = entry[4] if len(entry) > 4 else None

    previous = _WATCHED.get('current')
    if previous and (previous['id'] != dbid or previous['type'] != mediatype):
        _queue_restore(previous)           # the item before this one just finished

    if dbid and mediatype in ('episode', 'movie'):
        _WATCHED['current'] = _snapshot(dbid, mediatype)
    else:
        _WATCHED['current'] = None          # folder file - nothing in the library to keep


def preserve_watched_on_stop():
    """On stop / end (including a manual stop mid-episode): restore the item that was
    playing so its watched flag, counts and resume bookmark are left untouched."""
    previous = _WATCHED.get('current')
    if previous:
        _queue_restore(previous)
    _WATCHED['current'] = None


def _flush_current():
    """Move any held snapshot into the restore queue (used when the setting is off, we no
    longer own playback, or the service is shutting down)."""
    previous = _WATCHED.get('current')
    if previous:
        _queue_restore(previous)
    _WATCHED['current'] = None


def reassert_watched():
    """Re-apply pending restores until their window lapses, so Kodi's slightly-delayed
    watched/resume write is reverted. Only writes when the item actually drifted."""
    if not _WATCHED['restores']:
        return
    now = time.time()
    keep = []
    for restore in _WATCHED['restores']:
        if _differs(restore['snap']):
            _apply_snapshot(restore['snap'])
        if now < restore['until']:
            keep.append(restore)
    _WATCHED['restores'] = keep


# ----------------------------------------------------------------------------
# Jobs
# ----------------------------------------------------------------------------

def record_progress():
    data = storage.load()
    playback = data.get('playback')
    if not playback or playback.get('mode') != 'serial_random':
        return

    pos = _owned_position(playback)
    if pos is None:
        return

    entry = playback['positions'][pos]
    title_key, index = entry[0], entry[1]
    channel_id = playback.get('channel_id')
    if not channel_id:
        return

    pointers = data.setdefault('state', {}).setdefault(channel_id, {}).setdefault('pointers', {})
    if pointers.get(title_key) == index:
        return
    pointers[title_key] = index
    storage.save(data)


def regenerate_after_jump(pos):
    """Rebuild the queue after a manual jump so the jumped-to episode becomes the new
    entry #0: BOTH the stale tail after it AND the already-shown backlog before it are
    removed, then a fresh forward run is generated. Skipped shows fall back to their
    last watched episode; the jumped-to show continues from the current one."""
    data = storage.load()
    playback = data.get('playback')
    if not playback or playback.get('mode') != 'serial_random':
        return
    positions = playback.get('positions') or []
    if pos < 0 or pos >= len(positions):
        return

    current = positions[pos]
    current_key, current_index = current[0], current[1]
    channel_id = playback.get('channel_id')

    # Seed the rebuilt tail from the RESUME POINTERS (each show's last actually-watched
    # episode), NOT the generated build state. The episodes between the start and the
    # jump were queued but SKIPPED - never watched - so they must not advance anyone.
    # Every other show therefore resumes from where it was really left (episode 1 on a
    # fresh channel: 1, 2, 3 ...); only the jumped-to show continues forward from here.
    pointers = data.get('state', {}).get(channel_id, {}).get('pointers', {})
    lookahead = dict(pointers)
    lookahead[current_key] = current_index + 1   # the show we jumped into keeps going

    # Step off the playlist window first, then rebuild the live playlist: drop the
    # stale future (top-down after pos), then the played/skipped backlog (the first
    # `pos` items) so the still-playing jumped-to item is left as the new index 0.
    _leave_playlist_window()
    playlist = _video_playlist()
    for index in range(playlist.size() - 1, pos, -1):
        _playlist_remove(index)
    for _ in range(pos):
        _playlist_remove(0)

    # A manual jump ends whatever visit was in progress: the jumped-to episode plays as
    # its own visit, so the generated tail starts a new visit that switches AWAY from it
    # (pass current_key with run/target 0 -> build_items forces a different title next).
    picks, new_positions, last_key, run, target = scheduler.build_items(
        playback['titles'], 'serial_random', lookahead, TOPUP_BATCH,
        playback.get('max_consecutive', 2), current_key, 0,
        always=playback.get('consec_always', False),
        consec_overrides=playback.get('consec_overrides', {}),
        weights=playback.get('weight_overrides', {}))
    for pick in picks:
        playlist.add(pick['file'], scheduler.make_list_item(pick))

    _log('regen @pos {0} ({1}#{2}): rebuilt from scratch, appended {3}; next={4}'.format(
        pos, current_key, current_index, len(picks),
        [p['label'] for p in picks[:4]]))

    playback['positions'] = [current] + new_positions
    playback['lookahead'] = lookahead
    playback['last_key'] = last_key
    playback['run'] = run
    playback['target'] = target
    storage.save(data)
    # The jumped-to item is now index 0; the next item to start is index 1, a normal
    # +1 - so reset the jump tracker, else detect_jump would see a false backwards jump.
    _LAST['pos'] = 0


def topup():
    data = storage.load()
    playback = data.get('playback')
    if not playback:
        return

    playlist = _video_playlist()
    pos = playlist.getposition()
    size = playlist.size()
    if size <= 0 or pos < 0 or (size - pos) > TOPUP_THRESHOLD:
        return
    if _owned_position(playback) is None:
        return

    picks, positions, last_key, run, target = scheduler.build_items(
        playback['titles'], playback['mode'], playback.get('lookahead', {}), TOPUP_BATCH,
        playback.get('max_consecutive', 2), playback.get('last_key'), playback.get('run', 0),
        always=playback.get('consec_always', False),
        consec_overrides=playback.get('consec_overrides', {}),
        weights=playback.get('weight_overrides', {}), target=playback.get('target', 0))
    if not picks:
        return

    for pick in picks:
        playlist.add(pick['file'], scheduler.make_list_item(pick))
    playback['positions'].extend(positions)
    playback['last_key'] = last_key
    playback['run'] = run
    playback['target'] = target
    storage.save(data)


def _stop_for_sleep(playback, data):
    """Stop playback (if it is still ours) because the sleep deadline was reached, then
    clear the deadline and notify."""
    if _owned_position(playback) is not None:
        xbmc.Player().stop()
        _log('sleep timer reached - stopping playback')
    xbmcgui.Dialog().notification(storage.NAME, storage.L(32206), storage.ALERT_ICON, 4000)
    playback['sleep_deadline'] = None
    _SLEEP['warned_deadline'] = None
    storage.save(data)


def check_sleep_timer():
    """Enforce the global sleep timer: pop a live countdown warning (Cancel / Restart)
    `sleep_warn_minutes` before the deadline, and stop playback at the deadline. Only
    ever acts while ChannelMe owns the current playback."""
    data = storage.load()
    playback = data.get('playback')
    if not playback:
        return
    deadline = playback.get('sleep_deadline')
    if not deadline or _owned_position(playback) is None:
        return

    now = time.time()
    if now >= deadline:
        _stop_for_sleep(playback, data)
        return

    warn_seconds = storage.get_int_setting('sleep_warn_minutes', 0) * 60
    if warn_seconds <= 0 or now < deadline - warn_seconds:
        return                              # no warning, or not in the warning window yet
    if _SLEEP['warned_deadline'] == deadline:
        return                              # already warned once for this deadline

    _SLEEP['warned_deadline'] = deadline
    result = sleeptimer.show(int(deadline - now))   # blocks here until decided/expired

    # Time has passed and the user may have chosen - reload before acting.
    data = storage.load()
    playback = data.get('playback')
    if not playback:
        return
    if result == 'cancel':
        playback['sleep_deadline'] = None
        _SLEEP['warned_deadline'] = None
        storage.save(data)
    elif result == 'restart':
        minutes = storage.get_int_setting('sleep_minutes', 0)
        playback['sleep_deadline'] = (time.time() + minutes * 60) if minutes > 0 else None
        _SLEEP['warned_deadline'] = None
        storage.save(data)
    elif result == 'expire':
        _stop_for_sleep(playback, data)
    # 'dismiss': leave the deadline in place - the deadline branch stops it shortly.


def detect_jump():
    """Spot a manual jump (position not advancing by exactly +1) and regenerate."""
    data = storage.load()
    playback = data.get('playback')
    if not playback:
        return

    pos = _owned_position(playback)
    if pos is None:
        return

    session = playback.get('session')
    if _LAST['session'] != session:        # fresh channel start - just anchor
        _LAST['session'] = session
        _LAST['pos'] = pos
        return

    previous = _LAST['pos']
    jumped = previous is not None and pos != previous + 1
    _LAST['pos'] = pos
    if jumped and playback.get('mode') == 'serial_random':
        _log('jump detected: pos {0} -> {1}; regenerating'.format(previous, pos))
        regenerate_after_jump(pos)


# ----------------------------------------------------------------------------
# Player + main loop
# ----------------------------------------------------------------------------

class ChannelPlayer(xbmc.Player):
    def onAVStarted(self):
        preserve_watched_on_start()    # snapshot this item / restore the previous one
        record_progress()
        detect_jump()
        topup()

    def onPlayBackStopped(self):
        preserve_watched_on_stop()     # manual stop (incl. mid-episode) - restore state

    def onPlayBackEnded(self):
        preserve_watched_on_stop()     # queue ran to its end


def main():
    xbmc.log('ChannelMe! service started', xbmc.LOGINFO)
    monitor = xbmc.Monitor()
    player = ChannelPlayer()       # kept alive for the service lifetime
    while not monitor.abortRequested():
        if xbmc.Player().isPlayingVideo():
            topup()
            check_sleep_timer()
        reassert_watched()         # runs even when stopped, to finish pending restores
        if monitor.waitForAbort(POLL_SECONDS):
            break
    # Cleanup on exit (Kodi shutdown / addon disable): make sure the last item's state
    # is put back before we go.
    _flush_current()
    reassert_watched()
    del player
