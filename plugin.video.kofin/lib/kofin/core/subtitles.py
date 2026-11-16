"""Subtitle files as Kodi wants them: the naming and the fetch.

The pure half of the sidecar-subtitle work, shared by the play route
(``plugin/subtitles.localize``) and the late-subtitle chase
(``service/latesubs``): the cache directory every play writes into and
sweeps, the delivery URL with an extension Kodi has a parser for, and the
``<name>.<language>[.forced][.impaired].<ext>`` filename Kodi reads the
label back from. One implementation for both, so a track that arrives late
is labelled exactly as it would have been on time; ``plugin/subtitles.py``
keeps the route-facing surface and re-exports these names.
"""

import os
from typing import Optional

import xbmc
import xbmcvfs

from kofin.core import streams
from kofin.core.http import Http
from kofin.core.log import Logger

LOG = Logger(__name__)

# Everything written here belongs to the playback being resolved right now, and
# is swept before the next one writes its own (see ``localize``).
CACHE_DIR = "special://temp/kofin/subtitles"

# Short, and no retries: a sidecar that does not arrive promptly is not worth
# delaying the picture for. The URL is still attached in its place.
TIMEOUT = (3.05, 8.0)

# Shorter still, for an embedded track: the server either has this one
# extracted already or is about to spend half a minute making it, and no
# budget between those two outcomes buys anything. What does not land here
# is deferred, not lost.
EMBEDDED_TIMEOUT = (3.05, 4.0)

# Extensions Kodi recognises as subtitles. A URL already ending in one of these
# is left alone; anything else is asked for as .srt, which the server converts
# to (the extension in the delivery route selects the output format).
KNOWN_EXTENSIONS = frozenset(
    {"srt", "ass", "ssa", "sub", "smi", "vtt", "txt", "utf", "utf8", "idx", "aqt"}
)
DEFAULT_EXTENSION = "srt"

# Filesystem-hostile characters, plus the dot: Kodi tokenises the filename on
# separators, so a dot inside the name would read as another token.
_UNSAFE = str.maketrans({ch: "_" for ch in '/\\<>:"|?*.\x00'})


def _last_segment(url: str) -> str:
    """The filename part of a URL — no query, no directories.

    Everything here works on this rather than on the whole URL, because a dot
    is common in a host name and rare in a subtitle route: ``http://s.co/Stream``
    has no extension at all, and treating one as if it did rewrote the host.
    """
    return url.split("?", 1)[0].rsplit("/", 1)[-1]


def extension_of(url: str) -> str:
    """The subtitle extension a URL asks the server for, or ''."""
    name = _last_segment(url)
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()


def delivery_url(url: str) -> str:
    """The URL to fetch, with an extension Kodi has a parser for.

    Jellyfin names the file after the *codec*, so a SubRip track arrives as
    ``Stream.subrip`` — which is not in Kodi's subtitle extension list, and is
    not something its parser factory recognises either. Asking the same route
    for ``.srt`` returns the same cues. A URL already asking for a format
    Kodi knows — ``.ass`` keeps its styling, ``.vtt`` its own parser — is
    left alone.
    """
    extension = extension_of(url)
    if extension in KNOWN_EXTENSIONS:
        return url
    path, sep, query = url.partition("?")
    name = _last_segment(url)
    stem = name.rsplit(".", 1)[0] if "." in name else name
    base = path[: len(path) - len(name)]
    return "%s%s.%s%s%s" % (base, stem, DEFAULT_EXTENSION, sep, query)


def display_name(attachment: streams.Attachment) -> str:
    """What Kodi should call the track, as the first part of the filename.

    The server's own ``Title`` when it has one — that is a label a person
    wrote, like "Signs & Songs" — and otherwise the language spelled out, which
    is what the viewer is choosing between. ``convertLanguage`` is Kodi's own
    table, so the wording matches the rest of its UI.
    """
    if attachment.title:
        return attachment.title
    if attachment.language:
        spelled = xbmc.convertLanguage(attachment.language, xbmc.ENGLISH_NAME)
        if spelled:
            return spelled
        return attachment.language
    return "Subtitle"


def filename_for(attachment: streams.Attachment, ordinal: int = 1) -> str:
    """``<name>.<language>[.forced][.impaired][.<n>].<ext>`` — the shape Kodi
    reads back. ``forced`` and ``impaired`` are flags to Kodi; a number past
    the first is neither, so Kodi shows it as part of the name."""
    parts = [display_name(attachment).translate(_UNSAFE).strip() or "Subtitle"]
    if attachment.language:
        parts.append(attachment.language.translate(_UNSAFE))
    if attachment.forced:
        parts.append("forced")
    if attachment.hearing_impaired:
        parts.append("impaired")
    if ordinal > 1:
        parts.append(str(ordinal))
    parts.append(extension_of(delivery_url(attachment.url)) or DEFAULT_EXTENSION)
    return ".".join(parts)


def unique_filename(attachment: streams.Attachment, taken: set[str]) -> str:
    """The first of ``filename_for``'s names not in ``taken``, added to it.

    Two tracks can name themselves alike, as a sidecar and the embedded track
    of one language do, and one path would hold whichever was written last.
    Compared case-blind, as a case-insensitive filesystem would.
    """
    ordinal = 1
    while True:
        name = filename_for(attachment, ordinal)
        if name.lower() not in taken:
            taken.add(name.lower())
            return name
        ordinal += 1


def _cache_dir() -> str:
    return xbmcvfs.translatePath(CACHE_DIR)


def sweep(directory: Optional[str] = None) -> int:
    """Empty the cache. Returns how many files went.

    Called before each play writes its own, which bounds the directory at one
    playback's worth. Best effort throughout: a file the outgoing playback
    still holds open is a failed unlink on some platforms and a stale file
    here, neither of which is worth failing a playback over.
    """
    path = directory or _cache_dir()
    if not os.path.isdir(path):
        return 0
    removed = 0
    for name in os.listdir(path):
        try:
            os.remove(os.path.join(path, name))
            removed += 1
        except OSError as error:
            LOG.debug("could not sweep %s: %s", name, error)
    return removed


def fetch_to(
    http: Http,
    attachment: streams.Attachment,
    directory: Optional[str] = None,
    timeout: Optional[tuple[float, float]] = None,
) -> str:
    """One subtitle to a named local file, or '' — the service's way in.

    The file takes a name no file in the directory has: the play route's
    files for the running playback are there, and this track can name itself
    like one of them."""
    return _fetch(http, attachment, directory or _cache_dir(), timeout)


def _fetch(
    http: Http,
    attachment: streams.Attachment,
    directory: str,
    timeout: Optional[tuple[float, float]] = None,
    name: str = "",
) -> str:
    """One subtitle to a named local file, or '' if anything at all went wrong.

    ``name`` is one the caller reserved (``unique_filename``); without one
    the file takes the first name the directory does not hold."""
    try:
        # exist_ok: concurrent fetches race this check, and a lost race must
        # not read as a failed subtitle.
        os.makedirs(directory, exist_ok=True)
        response = http.request(
            "GET",
            delivery_url(attachment.url),
            timeout=timeout or (TIMEOUT if attachment.sidecar else EMBEDDED_TIMEOUT),
            retries=0,
        )
        if not name:
            held = {entry.lower() for entry in os.listdir(directory)}
            name = unique_filename(attachment, held)
        target = os.path.join(directory, name)
        with open(target, "wb") as handle:
            handle.write(response.content)
        return target
    except Exception as error:
        # Never raises, and deliberately catches everything: a subtitle that
        # did not arrive costs its label and the URL goes on in its place. It
        # must not cost the playback.
        LOG.warning("subtitle %s not fetched (%s)", attachment.stream_index, error)
        return ""
