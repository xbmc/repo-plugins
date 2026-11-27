"""The only cross-process live state: a few window properties on window 10000.

Anything else someone wants to share between the plugin and service processes
must argue its way into this module. Several are read outside kofin's Python —
by addon.xml, settings.xml, skins and other add-ons — which can read a window
property and none of kofin's other state.
"""

import json
import os
import time
import uuid
from typing import Any, Callable, Optional, TypeVar

import xbmcgui
import xbmcvfs

from kofin.core.urls import BASE_URL

PROP_ONLINE = "kofin.online"
PROP_PLAYING_ID = "kofin.playing.id"
# Earns its place here because addon.xml's <visible> can only test window
# properties: there is no infolabel that reads an addon setting, so hiding
# "Play with transcoding" when no bitrates are configured needs the setting
# mirrored into one.
PROP_CONTEXT_BITRATES = "kofin.context.bitrates"

# The playing item's selectable streams, and the one-word summary addon.xml
# tests to choose the stream context item's label.
#
# PROP_PLAYING_STREAMS is here because no other surface reaches: the streams
# are resolved in the *plugin* process, the service claims the playback and
# empties the play queue, and the thing that needs them is a *third*
# process — the context item, run minutes later.
#
# PROP_PLAYING_MENU earns its place the same way PROP_CONTEXT_BITRATES does: a
# context item's <label> is a fixed string id, so an entry whose wording
# depends on what the item offers has to be three declared entries whose
# <visible> conditions are mutually exclusive — and a boolean expression can
# read a window property and nothing else. The service publishes one of
# streams.OFFER_* when it claims; "" hides all three.
PROP_PLAYING_STREAMS = "kofin.playing.streams"
PROP_PLAYING_MENU = "kofin.playing.menu"

# The additional users on this device's session, as the root listing's
# "Who's watching?" entry names them. Earns its place because the owner and
# the reader are different processes: the *service* is where the set changes
# (the picker worker, the connect-time restore) and it knows the names the
# moment it changes them, while the *plugin* renders the label on every root
# listing.
PROP_WHO_NAMES = "kofin.who.names"

# Whether the addon-root "Who's watching?" / SyncPlay entries are on offer.
# Earns its place the same way PROP_CONTEXT_BITRATES does: a skin <visible>
# can only test a window property, and these two entries come and go with
# addon settings the skin cannot read (the shortlist's nobody sentinel, and
# syncPlayEnabled). Contuary's home-widget buttons hide on the same
# conditions as the root listing.
PROP_MENU_WHO = "kofin.menu.who"
PROP_MENU_SYNCPLAY = "kofin.menu.syncplay"
# A SyncPlay pulse's rate left in force (syncplay/tempo.py): written when a
# pulse asks Kodi for a rate, dropped when Kodi takes 1.0 back. Kodi keeps a
# tempo across a pause and refuses a new one while paused, so a pulse cut while
# paused leaves its rate behind until the resume; and a service generation that
# ends mid-pulse would leave the item playing fast or slow to its end. Kodi's
# tempo lasts as long as its process, and so does this property, which is what
# lets the next resume, or the next generation, put 1.0 back. Not cleared by
# clear_all for exactly that reason.
PROP_SYNCPLAY_PULSE = "kofin.syncplay.pulse"
# The SyncPlay group a service generation was in when it was restarted in
# place (a settings change): written by the manager's stop when it keeps the
# membership instead of leaving, read once by the next generation, which
# rejoins. The group is the server's and outlives the generation, so the id
# must too; a Kodi quit leaves the group and clears it. Not cleared by
# clear_all for the same reason as the pulse.
PROP_SYNCPLAY_GROUP = "kofin.syncplay.group"
# Whether this Kodi has the tempo feature (capabilities, "tempo"). Earns its
# place because settings.xml greys the fine-sync settings on a Kodi without
# it, and a setting's dependency can read another setting or an InfoBool,
# which reads a window property; the service publishes it from each start's
# probe. A Kodi's features last as long as its process, so clear_all leaves
# it, and a bounce does not grey the settings while the next generation
# starts.
PROP_FEATURE_TEMPO = "kofin.feature.tempo"
# The public sync-session mirror: what a provider add-on or a skin needs to
# offer "watch together" affordances — in-group, group name, member names,
# phase, the current item's provider:key. Cross-process shared live state
# read by add-ons that are not kofin, which is exactly this module's charter;
# deliberately NOT kofin-prefixed, because the name is part of the published
# provider contract (docs/syncplay-provider-contract.md).
PROP_SYNCSESSION = "syncsession.state"

# The native music pass's hold on Kodi's music scanner. Every song or album
# written through the public API is announced, and Estuary's music home
# widgets re-query the whole library on each announcement -- unless the
# announcement is marked a transaction, which Kodi does while its music
# scanner is busy. So the pass asks the scanner to list a hold directory and
# the *plugin* process, which serves that listing inside Kodi's scanner
# thread, keeps it open until the service lets go. Earns its place because
# the holder and the releaser are different processes and a window property
# is the one channel both share live; the value is a nonce so a listing that
# outlived its pass never waits on the next one.
PROP_NATIVE_HOLD = "kofin.native.hold"

# The item the pass is having Kodi refresh (patch.Applier.refresh). Kodi asks
# the scanner callback for a refreshed item the same way whoever pressed
# Refresh, with kodi_action=refresh_info and nothing else, and a viewer's is
# a request to ask the server again (ipc.REFRESH_ITEMS) where the pass's is
# the catalogue being filed. Earns its place because the one that knows is
# the service and the one that is asked is the *plugin* process, inside
# Kodi's refresh job. Told apart in the service instead, every refresh of a
# pass that files a library again would be a NotifyAll to every add-on's
# Monitor. One value: the pass waits for each refresh before the next.
PROP_NATIVE_REFRESH = "kofin.native.refresh"

# The listings being built, per plugin URL: at most two builds of one URL at
# a time, so a skin's home widgets asked for again at every visit to Home
# cannot pile up until Kodi has no thread left to create. Named here, as
# every property kofin shares is; read and written in plugin/gate.py alone,
# because the request it turns away must not have imported this module or
# anything else of kofin's. Earns its place because the requests are
# separate interpreters with nothing in common but this window.
PROP_LISTING_FLIGHT = "kofin.listing.flight"

# Which Play all owns the music playlist (plugin/playall.py, ipc.START_QUEUE).
# A second Play all while the first is still adding its tracks takes the
# playlist over: the first stops adding, and the service starts only the
# newest request's queue. A token rather than a counter, so two interpreters
# never race on a read and an increment.
PROP_QUEUE_OWNER = "kofin.queue.owner"

# The version Play Next has the next episode play (service/segments.py,
# plugin/versions.py). Earns its place because Play Next plays the
# episode's library path, which Kodi matches its row by and which carries no
# parameter of kofin's: the service that starts the play and the plugin
# process that resolves it share nothing else. A hint older than
# NEXT_VERSION_TTL_SECONDS is a Play Next that never reached the play route,
# and a person starting that episode later is asked.
PROP_NEXT_VERSION = "kofin.next.version"
NEXT_VERSION_TTL_SECONDS = 60

# The lyrics channel. These earn their place for the same reason as
# PROP_CONTEXT_BITRATES: a skin or a script can only read window properties,
# and lyrics cannot reach one any other way -- Kodi's music database has no
# lyrics column, and an addon window cannot draw a passive overlay (it becomes
# the active window and swallows the OSD).
#
# kofin publishes and stops. It fetches the lyrics at playback start, when it
# alone knows the song's Jellyfin id, and hands them over here; rendering
# them and following the clock belong to script.kofin.lyrics. PROP_LYRIC_JSON
# carries the timed lines; PROP_LYRIC_HAS is what a renderer shows and hides
# on; PROP_LYRIC_PATH is the address of the plugin directory that serves the
# lines as list items, and it carries the song id so that it *changes* per
# song -- a list bound to it re-reads the directory on the change, which
# Container.Refresh cannot do for a window that is not a media window.
PROP_LYRIC_HAS = "kofin.lyric.has"
PROP_LYRIC_JSON = "kofin.lyric.json"
PROP_LYRIC_PATH = "kofin.lyric.path"

# The song id is a cache-buster as much as an argument: the path has to differ
# between songs for the skin's list to notice.
LYRICS_DIRECTORY = BASE_URL + "?mode=lyrics&id=%s"

_HOME_WINDOW = 10000


def _window() -> xbmcgui.Window:
    return xbmcgui.Window(_HOME_WINDOW)


def _set_flag(prop: str, on: bool) -> None:
    """A property that is "true" or absent."""
    if on:
        _window().setProperty(prop, "true")
    else:
        _window().clearProperty(prop)


def _publish_json(prop: str, payload: Any) -> None:
    _window().setProperty(prop, json.dumps(payload))


_T = TypeVar("_T", dict, list)


def _json(prop: str, kind: type[_T]) -> _T:
    """The property's JSON payload as a ``kind``, or an empty one when the
    property is absent, malformed or of another shape."""
    raw = _window().getProperty(prop)
    if not raw:
        return kind()
    try:
        payload = json.loads(raw)
    except ValueError:
        return kind()
    return payload if isinstance(payload, kind) else kind()


def take_queue() -> str:
    """Make this Play all the music playlist's owner; returns its token."""
    token = uuid.uuid4().hex
    _window().setProperty(PROP_QUEUE_OWNER, token)
    return token


def owns_queue(token: str) -> bool:
    return _window().getProperty(PROP_QUEUE_OWNER) == token


def set_online(online: bool) -> None:
    """Publish the connection state. Three-valued on purpose: "true",
    "false", and *absent* — the last meaning "nobody has said yet", which is
    every moment between Kodi starting and the service's first probe.

    Writing "false" rather than clearing is what lets a caller tell a known
    outage from an unanswered question: refusing a playback during the
    startup window because the flag had not been raised yet would be a
    false negative on the most ordinary action there is.
    """
    _window().setProperty(PROP_ONLINE, "true" if online else "false")


def is_online() -> bool:
    """Whether the server is known reachable. Absent reads as not-online,
    which is what the sync-side guards want: they only run after a connect,
    so for them absence means the service went away."""
    return _window().getProperty(PROP_ONLINE) == "true"


def is_offline() -> bool:
    """Whether the server is known *un*reachable — a stated outage, not an
    unanswered question. This is the one to gate user-facing refusals on."""
    return _window().getProperty(PROP_ONLINE) == "false"


# The play queue is a directory of one file per resolved play, not a window
# property holding a list. Both processes write it — the plugin's play route
# pushes, the service's player claims — and a window property can only be
# read-modify-written, which across processes is a race with no lock
# available.
#
# One file per entry removes the shared structure: nobody rewrites anybody
# else's data, and ``os.remove`` is the claim — the filesystem guarantees
# exactly one caller succeeds. Names are time-ordered so "oldest" is a sort,
# not a timestamp field to trust.
PLAY_QUEUE_DIR = "special://profile/addon_data/plugin.video.kofin/playqueue"

# How long an unclaimed entry survives. A play that resolved but never reached
# the player (a failed stream, a Kodi that never started it) would otherwise
# sit there forever.
PLAY_QUEUE_TTL_SECONDS = 600

# An entry that names a live stream holds the server's stream, and the tuner
# behind it, until a session report names it or something closes it. Kodi
# claims a live play within seconds of its resolve, so such an entry left this
# long unclaimed is closed and dropped (close_stale_live_streams); nothing else
# drops it.
PLAY_QUEUE_LIVE_TTL_SECONDS = 60


def _queue_dir() -> str:
    return xbmcvfs.translatePath(PLAY_QUEUE_DIR)


def _queue_files() -> list[str]:
    """Queued entry paths, oldest first (names carry a nanosecond stamp)."""
    directory = _queue_dir()
    try:
        return sorted(
            os.path.join(directory, name)
            for name in os.listdir(directory)
            if name.endswith(".json")
        )
    except OSError:
        return []


def _read_entry(path: str) -> Optional[dict[str, Any]]:
    try:
        with open(path) as handle:
            item = json.load(handle)
    except (OSError, ValueError):
        return None
    return item if isinstance(item, dict) else None


def _write_private(temporary: str, target: str, payload: Any) -> None:
    """``payload`` as JSON at ``target``, written to ``temporary`` and renamed
    so a reader never sees half of it. A claim's Path is its stream URL, and
    a transcoding URL carries api_key=: the same owner-only mode as the IPC
    nonce, so a copied addon_data tree does not leak the token."""
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        json.dump(payload, handle)
    os.chmod(temporary, 0o600)
    os.replace(temporary, target)


def push_play_item(item: dict[str, Any]) -> None:
    """Queue a resolved play's state for the service-side player to claim."""
    directory = _queue_dir()
    try:
        os.makedirs(directory, exist_ok=True)
        _expire_play_items()
        # The stamp orders the queue; the suffix keeps two plays resolved in
        # the same nanosecond apart. Written to a temp name and renamed so a
        # reader never sees a half-written entry.
        name = "%019d-%s.json" % (time.time_ns(), uuid.uuid4().hex[:8])
        target = os.path.join(directory, name)
        temporary = target + ".tmp"
        _write_private(temporary, target, item)
    except OSError:
        # A queue that cannot be written costs this playback its reporting,
        # never the play.
        pass


def _file_of(path: str) -> str:
    """A playing path without the protocol options after ``|``, which a
    resolved URL can carry and Kodi may or may not report back with it."""
    return path.split("|", 1)[0]


def claim_play_item(path: str) -> Optional[dict[str, Any]]:
    """Take only a queued entry for the file Kodi actually started.

    The removal is the claim: whoever unlinks the file owns that entry, and
    a loser simply moves on to the next candidate. An unrelated queued play
    must not be reported as this one if its stream never started.
    """
    files = _queue_files()
    if not files:
        return None

    matching = []
    for entry_path in files:
        item = _read_entry(entry_path)
        if item is None:
            continue
        if _file_of(str(item.get("Path") or "")) == _file_of(path):
            matching.append((entry_path, item))

    for entry_path, item in matching:
        try:
            os.remove(entry_path)
        except OSError:
            continue  # someone else claimed it first
        return item
    return None


def claim_play_item_of(item_id: str) -> Optional[dict[str, Any]]:
    """Take the newest queued entry for an item, whatever it resolved to,
    and drop any older one for it.

    For a track Kodi queued ahead. PAPlayer asks for the next track a few
    seconds before the current one ends; the play route resolves it and
    queues its entry under the stream it resolved to; and when the track
    starts Kodi names it by the plugin URL it was listed under, not by that
    stream.
    """
    newest = None
    for entry_path in reversed(_queue_files()):
        item = _read_entry(entry_path)
        if item is None or item.get("Id") != item_id:
            continue
        if newest is not None and item.get("LiveStreamId"):
            continue  # its stream is closed by close_stale_live_streams
        try:
            os.remove(entry_path)
        except OSError:
            continue  # someone else claimed it first
        if newest is None:
            newest = item
    return newest


def _expire_play_items() -> None:
    """Drop entries older than the TTL (see PLAY_QUEUE_TTL_SECONDS), except one
    that names a live stream, which only close_stale_live_streams drops."""
    cutoff = time.time_ns() - PLAY_QUEUE_TTL_SECONDS * 1_000_000_000
    for entry in _queue_files():
        stamp = os.path.basename(entry).split("-", 1)[0]
        if not stamp.isdigit() or int(stamp) >= cutoff:
            continue
        if (_read_entry(entry) or {}).get("LiveStreamId"):
            continue
        try:
            os.remove(entry)
        except OSError:
            pass


def close_stale_live_streams(close: Callable[[str], None]) -> list[str]:
    """Close and drop every entry that names a live stream and has waited
    PLAY_QUEUE_LIVE_TTL_SECONDS unclaimed; returns the ids it closed.

    Renaming the entry out of the queue is the claim, so a play that starts
    meanwhile and this sweep never both take it. A close that raises puts the
    entry back for the next sweep, until PLAY_QUEUE_TTL_SECONDS have passed.
    """
    now = time.time_ns()
    closed = []
    for entry in _queue_files():
        stamp = os.path.basename(entry).split("-", 1)[0]
        if not stamp.isdigit():
            continue
        age = now - int(stamp)
        if age < PLAY_QUEUE_LIVE_TTL_SECONDS * 1_000_000_000:
            continue
        live_stream_id = (_read_entry(entry) or {}).get("LiveStreamId")
        if not live_stream_id:
            continue
        taken = entry + ".closing"
        try:
            os.rename(entry, taken)
        except OSError:
            continue  # claimed meanwhile
        try:
            close(live_stream_id)
        except Exception:
            if age < PLAY_QUEUE_TTL_SECONDS * 1_000_000_000:
                try:
                    os.rename(taken, entry)
                except OSError:
                    pass
                continue
        else:
            closed.append(live_stream_id)
        try:
            os.remove(taken)
        except OSError:
            pass
    return closed


def clear_play_queue() -> None:
    """Drop the queue, except an entry that names a live stream, which
    close_stale_live_streams closes first."""
    for entry in _queue_files():
        if (_read_entry(entry) or {}).get("LiveStreamId"):
            continue
        try:
            os.remove(entry)
        except OSError:
            pass


def same_file(path: str, other: str) -> bool:
    """Whether two playing paths name one file, protocol options aside."""
    return _file_of(path) == _file_of(other)


def _handover_path() -> str:
    """Where a stopped generation leaves the claim of a play it no longer
    reports (Player.stop_threads), for the next one to report on or drop
    (Player.adopt): beside the play queue, out of its housekeeping, which
    reads only ``.json`` entries, and of clear_all, which an in-process
    restart runs before its successor exists."""
    return os.path.join(_queue_dir(), "handover.claim")


def hand_over_play(payload: dict[str, Any]) -> None:
    """Leave a playing claim to the next generation."""
    target = _handover_path()
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        _write_private(target + ".tmp", target, payload)
    except OSError:
        # Costs the next generation this play's reporting, never the play.
        pass


def take_handed_over_play() -> dict[str, Any]:
    """What a stopped generation handed over, or {}; gone either way."""
    path = _handover_path()
    payload = _read_entry(path) or {}
    try:
        os.remove(path)
    except OSError:
        pass
    return payload


def set_playing_id(item_id: str) -> None:
    _window().setProperty(PROP_PLAYING_ID, item_id)


def get_playing_id() -> str:
    return _window().getProperty(PROP_PLAYING_ID)


def clear_playing_id() -> None:
    _window().clearProperty(PROP_PLAYING_ID)


def follow_version(item_id: str, name: str) -> None:
    """Have the next play of ``item_id`` take its version called ``name``
    without asking, or the server's default when it has none by that name."""
    _publish_json(PROP_NEXT_VERSION, {"Id": item_id, "Name": name, "At": time.time()})


def followed_version(item_id: str) -> Optional[str]:
    """The version name Play Next left for the play of ``item_id``, taken
    once; None when that play is not one Play Next started."""
    hint = _json(PROP_NEXT_VERSION, dict)
    if not item_id or hint.get("Id") != item_id:
        return None
    _window().clearProperty(PROP_NEXT_VERSION)
    try:
        age = time.time() - float(hint.get("At") or 0)
    except (TypeError, ValueError):
        return None
    if not 0 <= age <= NEXT_VERSION_TTL_SECONDS:
        return None
    return str(hint.get("Name") or "")


def set_native_hold(scanner: str) -> str:
    """Start a hold on the named scanner; returns the token to release it by."""
    token = scanner + ":" + uuid.uuid4().hex
    _window().setProperty(PROP_NATIVE_HOLD + "." + scanner, token)
    return token


def native_hold(scanner: str) -> str:
    """The current hold token for the scanner, '' when none is held."""
    return _window().getProperty(PROP_NATIVE_HOLD + "." + scanner)


def clear_native_hold(scanner: str) -> None:
    _window().clearProperty(PROP_NATIVE_HOLD + "." + scanner)


def set_native_refresh(item_id: str) -> None:
    """Name the item the pass is about to have Kodi refresh."""
    _window().setProperty(PROP_NATIVE_REFRESH, item_id)


def native_refresh() -> str:
    """The item the pass is refreshing, '' between its refreshes."""
    return _window().getProperty(PROP_NATIVE_REFRESH)


def clear_native_refresh() -> None:
    _window().clearProperty(PROP_NATIVE_REFRESH)


def set_context_bitrates(bitrates: str) -> None:
    """Mirror the configured context bitrates so addon.xml can hide the
    "Play with transcoding" item when the user has selected none."""
    if bitrates:
        _window().setProperty(PROP_CONTEXT_BITRATES, bitrates)
    else:
        _window().clearProperty(PROP_CONTEXT_BITRATES)


def publish_playing_streams(payload: dict[str, Any], offer: str) -> None:
    """Publish the playing item's streams and what the menu should offer.

    Written when the service claims a playback, cleared when it ends, so the
    properties' lifetime is exactly the playback's and a stale menu can never
    act on an item that stopped.
    """
    window = _window()
    _publish_json(PROP_PLAYING_STREAMS, payload)
    if offer:
        window.setProperty(PROP_PLAYING_MENU, offer)
    else:
        window.clearProperty(PROP_PLAYING_MENU)


def playing_streams() -> dict[str, Any]:
    """The published streams payload, or {} when nothing kofin owns is on."""
    return _json(PROP_PLAYING_STREAMS, dict)


def clear_playing_streams() -> None:
    window = _window()
    window.clearProperty(PROP_PLAYING_STREAMS)
    window.clearProperty(PROP_PLAYING_MENU)


def set_watching_names(names: list[str]) -> None:
    """Publish the additional-user names on this device's session.

    An empty list clears the property, which reads back as "nobody extra" —
    the base label. The service calls this wherever the set changes or is
    re-learned: the picker, the connect-time restore.
    """
    window = _window()
    if names:
        _publish_json(PROP_WHO_NAMES, names)
    else:
        window.clearProperty(PROP_WHO_NAMES)


def watching_names() -> list[str]:
    """The published additional-user names, or [] when there are none."""
    return [str(name) for name in _json(PROP_WHO_NAMES, list) if name]


def set_menu_who(offered: bool) -> None:
    """Whether the Who's watching? root entry is on offer."""
    _set_flag(PROP_MENU_WHO, offered)


def publish_syncplay_pulse(payload: dict[str, Any]) -> None:
    _publish_json(PROP_SYNCPLAY_PULSE, payload)


def syncplay_pulse() -> dict[str, Any]:
    """The rate a pulse left in force (``{"player": id}``), or {}."""
    return _json(PROP_SYNCPLAY_PULSE, dict)


def clear_syncplay_pulse() -> None:
    _window().clearProperty(PROP_SYNCPLAY_PULSE)


def publish_syncplay_group(group_id: str) -> None:
    """The group the stopping generation stays in, for the next one."""
    _window().setProperty(PROP_SYNCPLAY_GROUP, group_id)


def syncplay_group() -> str:
    return _window().getProperty(PROP_SYNCPLAY_GROUP)


def clear_syncplay_group() -> None:
    _window().clearProperty(PROP_SYNCPLAY_GROUP)


def set_feature_tempo(on: bool) -> None:
    """Whether the fine-sync settings are offered (PROP_FEATURE_TEMPO)."""
    _set_flag(PROP_FEATURE_TEMPO, on)


def publish_syncsession(payload: dict[str, Any]) -> None:
    """The public sync-session state, JSON on PROP_SYNCSESSION."""
    _publish_json(PROP_SYNCSESSION, payload)


def syncsession() -> dict[str, Any]:
    return _json(PROP_SYNCSESSION, dict)


def clear_syncsession() -> None:
    _window().clearProperty(PROP_SYNCSESSION)


def set_menu_syncplay(offered: bool) -> None:
    """Whether the SyncPlay root entry is on offer."""
    _set_flag(PROP_MENU_SYNCPLAY, offered)


def publish_lyrics(lines: list[Any], item_id: str) -> None:
    """Publish the song's lyrics for whatever is going to render them.

    ``lines`` is ``[[start_seconds_or_null, text], ...]``. The timings ride
    along because the renderer decides which line is current -- kofin's job
    ends at fetching them.
    """
    window = _window()
    _publish_json(PROP_LYRIC_JSON, lines)
    window.setProperty(PROP_LYRIC_PATH, LYRICS_DIRECTORY % item_id)
    window.setProperty(PROP_LYRIC_HAS, "true")


def lyric_lines() -> list[Any]:
    """The published ``[start, text]`` pairs, or [] when there are none."""
    return _json(PROP_LYRIC_JSON, list)


def lyric_texts() -> list[str]:
    """Just the text of each line, for serving the list's directory."""
    return [str(line[1]) for line in lyric_lines() if isinstance(line, list) and line]


def clear_lyrics() -> None:
    """Drop the overlay. The skin hides on PROP_LYRIC_HAS, so this is what
    stops lyrics outliving the song that owned them."""
    window = _window()
    window.clearProperty(PROP_LYRIC_HAS)
    window.clearProperty(PROP_LYRIC_JSON)
    window.clearProperty(PROP_LYRIC_PATH)


def clear_all() -> None:
    """Drop the live state."""
    window = _window()
    props = [
        PROP_ONLINE,
        PROP_PLAYING_ID,
        PROP_CONTEXT_BITRATES,
        PROP_PLAYING_STREAMS,
        PROP_PLAYING_MENU,
        PROP_WHO_NAMES,
        PROP_MENU_WHO,
        PROP_MENU_SYNCPLAY,
        PROP_SYNCSESSION,
        PROP_NEXT_VERSION,
    ]
    for prop in props:
        window.clearProperty(prop)
    clear_lyrics()
    clear_play_queue()
