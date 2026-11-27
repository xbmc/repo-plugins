"""Embedded subtitles that arrive after the picture does.

A transcoded stream carries no subtitles, so a text track reaches Kodi as a
file the play route fetches from Jellyfin's delivery URL. The first request
for a track makes the server extract it with ffmpeg, which can take minutes,
so the play route waits only long enough to catch an already-extracted track
and hands anything slower here (``plugin/subtitles.localize``).

When the file lands, ``Player.setSubtitles`` puts it on the running playback.
The *Player* method takes a single path and adds it to the playback in flight;
the ListItem method of the same name takes a list and applies only before the
stream is opened. There is no ``addSubtitle`` on Player, whatever
``Player.AddSubtitle`` over JSON-RPC suggests.

Each attempt uses the play route's own short read budget and the loop sleeps
on the cancel event between them, so a service teardown or a stopped playback
is answered within one attempt. The whole chase ends at ``DEADLINE_SECONDS``,
and the stream menu still offers the track.
"""

import threading
from typing import Any, Optional

from kofin.core import streams
from kofin.core.http import Http
from kofin.core.log import Logger
from kofin.core import subtitles

LOG = Logger(__name__)

JsonDict = dict[str, Any]

# How long to keep asking: twice the slowest extraction seen. Past this the
# server is not going to produce the track.
DEADLINE_SECONDS = 300.0

# Between attempts.
POLL_SECONDS = 8.0


def fetchable_of(item: JsonDict) -> dict[int, streams.Attachment]:
    """Every text track this playback can be handed as a file, by index.

    Only on a transcode, and not by omission. On a direct play the container
    already holds every embedded track, so there is nothing to fetch — and a
    late ``setSubtitles`` there would land *after* the demuxed tracks, which
    is the one arrangement ``streams.subtitle_ordinal`` cannot describe (it
    puts every attached track before every demuxed one, because Kodi registers
    a ListItem's subtitle files in ``OpenInputStream`` and the container's own
    only arrive with ``OpenDemuxStream``).
    """
    if streams.is_direct(str(item.get("PlayMethod") or "")):
        return {}
    payload = item.get("Streams") or {}
    rebuilt: dict[int, streams.Attachment] = {}
    for raw in payload.get("Fetchable") or []:
        try:
            attachment = streams.Attachment(**raw)
        except TypeError:  # pragma: no cover - a payload from another version
            LOG.debug("undecodable fetchable subtitle: %s", raw)
            continue
        rebuilt[attachment.stream_index] = attachment
    return rebuilt


def deferred_of(item: JsonDict) -> list[streams.Attachment]:
    """The tracks to chase without being asked: the one this play resolved
    with and did not get inside the play route's budget, unless a chase has
    attached it since (a claim a stopped generation handed over)."""
    fetchable = fetchable_of(item)
    payload = item.get("Streams") or {}
    attached = set(payload.get("Attached") or [])
    wanted = [int(index) for index in payload.get("Deferred") or []]
    return [
        fetchable[index]
        for index in wanted
        if index in fetchable and index not in attached
    ]


class LateSubtitles:
    """One playback's outstanding subtitle fetches.

    Built per claim by the Player: ``start()`` chases on a worker thread,
    ``stop()`` abandons the chase at the next step. Nothing here raises into a
    player callback.

    ``requested`` says where the chase came from, and it decides only one
    thing: what happens once the file lands. An automatic chase reproduces
    what the play route would have done — ``apply_default_tracks``, the single
    rule for whether a track is merely available or actually shown. A chase
    the viewer asked for through the stream menu shows the track they picked,
    because that rule would answer with the *resolved* index instead and
    switch them straight back off it.
    """

    def __init__(
        self,
        http: Http,
        player: Any,
        item: JsonDict,
        deferred: list[streams.Attachment],
        requested: bool = False,
    ) -> None:
        self._http = http
        self._player = player
        self._item = item
        self._deferred = deferred
        self._requested = requested
        self._cancel = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="kofin-late-subtitles")
        self._thread.daemon = True
        self._thread.start()

    def stop(self) -> None:
        self._cancel.set()

    # -- the chase -------------------------------------------------------------

    def _run(self) -> None:
        try:
            for attachment in self._deferred:
                if self._cancel.is_set():
                    return
                self._chase(attachment)
        except Exception:  # pragma: no cover - defensive
            LOG.exception("late subtitle fetch failed")

    def _chase(self, attachment: streams.Attachment) -> None:
        waited = 0.0
        while not self._cancel.is_set() and waited < DEADLINE_SECONDS:
            path = subtitles.fetch_to(self._http, attachment)
            if path:
                self._attach(attachment, path)
                return
            if self._cancel.wait(POLL_SECONDS):
                return
            waited += POLL_SECONDS
        if not self._cancel.is_set():
            LOG.debug(
                "subtitle %s gave up after %.0fs; the server never produced it",
                attachment.stream_index,
                DEADLINE_SECONDS,
            )

    def _attach(self, attachment: streams.Attachment, path: str) -> None:
        """Hand the file to the running playback, if it is still that one.

        The session check is what keeps a slow fetch from landing on whatever
        is playing by the time it finishes — the stream menu's restart makes
        exactly that race, replacing the playback while this thread waits.
        """
        if self._cancel.is_set():
            return
        live = self._player.current_item()
        if live is None or live.get("PlaySessionId") != self._item.get("PlaySessionId"):
            LOG.debug(
                "subtitle %s arrived after its playback ended", attachment.stream_index
            )
            return

        self._player.setSubtitles(path)
        # Kodi appends it to the subtitle list, and on a transcode that list is
        # exactly the attached one — nothing is demuxed — so recording it in
        # the same order keeps streams.subtitle_ordinal able to answer.
        payload = live.setdefault("Streams", {})
        attached = payload.setdefault("Attached", [])
        if attachment.stream_index not in attached:
            attached.append(attachment.stream_index)
        LOG.debug(
            "subtitle %s attached late (kodi %s)",
            attachment.stream_index,
            len(attached) - 1,
        )
        # Republished before anything is selected, so the stream menu marks
        # and switches the right row against the list this just extended.
        self._player.republish_streams(live)
        if not self._requested:
            # Landed the way it would have landed on time.
            self._player.apply_default_tracks()
            return
        # The viewer picked this one, so it goes on screen whatever the
        # resolved index was. setSubtitles already selected it — Kodi appends
        # and selects in one step — but saying so is what makes the state
        # right when subtitles were switched off at the time of the pick.
        ordinal = len(payload.get("Attached") or []) - 1
        self._player.setSubtitleStream(ordinal)
        self._player.showSubtitles(True)
