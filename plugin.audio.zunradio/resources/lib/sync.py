# SPDX-License-Identifier: GPL-2.0-or-later
"""Keeps the now playing information of the running stream in step with the audio.

track_for_web.json changes as soon as a track starts in the studio, but the
listener hears it a few seconds later. Kodi itself reads the ICY StreamTitle
("Artist - Title") from the stream exactly when the audio reaches that point
and replaces the artist and title it shows. This module waits for that moment
before it shows a new track with its cover, so the picture changes together
with the music. When the stream does not announce the new track within
DEFER_MAX seconds (no ICY data, a jingle), the new track is shown anyway.

Pure Python without Kodi modules, so the logic can be tested outside Kodi.
"""

import time
from collections import namedtuple

POLL_INTERVAL = 20  # seconds between downloads of the track information
RETRY_INTERVAL = 3  # seconds between downloads while waiting for the JSON to catch up
DEFER_MAX = 25  # seconds to wait for the stream and the JSON to agree

# What Kodi shows for the playing item
Shown = namedtuple('Shown', 'title artist album')


def _norm(text):
    return ' '.join(str(text or '').split()).casefold()


def same_shown(first, second):
    """True when two Shown values display the same texts."""
    if first is None or second is None:
        return first is second
    return all(_norm(a) == _norm(b) for a, b in zip(first, second))


def shows_track(shown, now_playing):
    """True when the title shown by Kodi belongs to the given track.

    Kodi splits the StreamTitle "Artist - Title" into artist and title; when the
    StreamTitle has more than one " - ", the whole text stays in the title.
    """
    if shown is None or now_playing is None or not now_playing.title:
        return False
    title = _norm(shown.title)
    return title in (_norm(now_playing.title),
                     _norm('{} - {}'.format(now_playing.artist, now_playing.title)))


def same_track(first, second):
    """True when two NowPlaying values describe the same track."""
    if first is None or second is None:
        return False
    return _norm(first.artist) == _norm(second.artist) and _norm(first.title) == _norm(second.title)


class Synchronizer:
    """Decides when to show which track. Call tick() about once a second.

    fetch() returns the NowPlaying on air (or None), read_shown() returns the
    Shown of the playing item and apply(now_playing) updates the playing item
    and returns the Shown that Kodi displays afterwards.
    """

    def __init__(self, fetch, read_shown, apply, clock=time.monotonic, log=None):
        self._fetch = fetch
        self._read_shown = read_shown
        self._apply = apply
        self._clock = clock
        self._log = log or (lambda message: None)
        self._failing = False
        self.reset()

    def reset(self):
        """Forget everything, for a new playback."""
        self.applied = None  # NowPlaying shown now
        self.shown = None  # Shown read back after our last update
        self.pending = None  # newer NowPlaying waiting for the audio to reach it
        self.pending_since = 0.0
        self.mismatch_since = None  # the stream announced a track the JSON does not have yet
        self.next_fetch = 0.0

    def tick(self):
        now = self._clock()
        if self.applied is None:
            if now >= self.next_fetch:
                now_playing = self._get(now, POLL_INTERVAL)
                if now_playing:
                    self._show(now_playing)
            return

        current = self._read_shown()
        if not same_shown(current, self.shown):
            self._stream_changed(now, current)
            return

        if self.pending and now - self.pending_since >= DEFER_MAX:
            self._log('No track change from the stream, showing the new track anyway')
            self._show(self.pending)
            return

        if now >= self.next_fetch:
            now_playing = self._get(now, POLL_INTERVAL)
            if now_playing:
                self._consider(now, now_playing)

    def _stream_changed(self, now, current):
        """Kodi replaced the texts of the playing item (ICY StreamTitle)."""
        if shows_track(current, self.applied):
            # Same track, Kodi only reset the other fields: restore them
            self._show(self.applied)
            return
        if shows_track(current, self.pending):
            self._show(self.pending)
            return
        if self.mismatch_since is None:
            # A new track reached the listener: find out its details right away
            self.mismatch_since = now
            self.next_fetch = now
        if now < self.next_fetch:
            return
        now_playing = self._get(now, RETRY_INTERVAL)
        if now_playing is None:
            return
        if shows_track(current, now_playing) or now - self.mismatch_since >= DEFER_MAX:
            self._show(now_playing)

    def _consider(self, now, now_playing):
        """A regular download: decide what to do with the result."""
        if now_playing == self.applied:
            self.pending = None
            return
        if same_track(now_playing, self.applied):
            # The show or the cover changed, not the track
            self._show(now_playing)
            return
        if not same_track(now_playing, self.pending):
            self.pending_since = now
        self.pending = now_playing

    def _show(self, now_playing):
        self.shown = self._apply(now_playing)
        self.applied = now_playing
        self.pending = None
        self.mismatch_since = None
        self._log('Showing {} / {} / {}'.format(now_playing.artist, now_playing.title,
                                                now_playing.show))

    def _get(self, now, next_interval):
        self.next_fetch = now + next_interval
        try:
            now_playing = self._fetch()
        except (OSError, ValueError) as error:
            if not self._failing:
                self._log('Track information unavailable: {}'.format(error))
            self._failing = True
            return None
        self._failing = False
        return now_playing
