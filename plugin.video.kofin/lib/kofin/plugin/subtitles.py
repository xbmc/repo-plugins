"""Sidecar subtitles as local files, so Kodi's own menu can name them.

Kodi reads a subtitle's language and label out of its **filename**, and
Jellyfin's delivery route fixes it: every attached track arrives as
``Stream.<codec>``. Worse, that stem matches the video stream's own
(``/Videos/<id>/stream.mkv``), so Kodi strips it as a redundant prefix and is
left with nothing at all. So the file has to be local, and this module is the
only thing in kofin that fetches media content on the play path.

**Everything attached**: sidecars, plus at most the one embedded track a
transcode was resolved with (``streams.attached_subtitles``). Kodi opens every
attached subtitle while building the demuxer, and an embedded track is
extracted on demand by the server, so an embedded track that cannot be fetched
here is never given to Kodi by its URL: the URL is what stalls. It is
*deferred* instead — handed back to the caller so the service can chase it
while the picture runs (``service/latesubs.py``). A sidecar still falls back
to its URL, because the server serves a file it already has and Kodi opening
it costs nothing.

A cold extraction takes tens of seconds and is cached after, and abandoning
the request does not abandon the work: the extraction runs to completion
server-side, which is what makes chasing it worthwhile rather than a second
cold start.

Kodi parses ``<name>.<language>[.forced][.impaired].<ext>``: a name, the
language, and the flags that apply. Nothing else, because anything Kodi does
not parse ends up rendered: the number that tells two otherwise alike tracks
apart is rendered on purpose.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import NamedTuple, Optional

from kofin.core import streams
from kofin.core.http import Http
from kofin.core.log import Logger

# The naming and the fetch live in core so the service's late chase
# labels a track exactly as this route would have; re-exported here for
# the play path and the stream menu, which reach them through this module.
from kofin.core.subtitles import (  # noqa: F401 - re-exports
    CACHE_DIR,
    DEFAULT_EXTENSION,
    EMBEDDED_TIMEOUT,
    KNOWN_EXTENSIONS,
    TIMEOUT,
    _cache_dir,
    _fetch,
    delivery_url,
    display_name,
    extension_of,
    fetch_to,
    filename_for,
    sweep,
    unique_filename,
)

LOG = Logger(__name__)

# A stop for a pathological item, not a tuning knob: a handful of sidecar files
# is the normal case, and each one is a round trip the first frame waits on.
MAX_FILES = 8


class Localized(NamedTuple):
    """What the play route got, and what it is still owed.

    ``files`` is the (attachment, path) pairs to hand ``setSubtitles``, in the
    order Kodi will list them — the Jellyfin index of each, in this order, is
    what makes an index translatable to a Kodi subtitle number at all
    (``streams.subtitle_ordinal``).

    ``deferred`` is the embedded tracks the server had not finished extracting.
    They are not failures and not losses: the service fetches them on its own
    clock and adds them to the running playback (``service/latesubs.py``).
    """

    files: list[tuple[streams.Attachment, str]]
    deferred: list[streams.Attachment]


def localize(
    http: Http,
    attached: list[streams.Attachment],
    directory: Optional[str] = None,
) -> Localized:
    """Fetch everything attachable now, and name what has to wait.

    Order is the order in. A sidecar whose fetch failed keeps its URL and its
    place — worse-labelled, never missing. An embedded track whose fetch did
    not land is deferred rather than attached.

    The fetches run concurrently, and the cap bounds fetch *attempts* rather
    than successes. Anything past the cap that is embedded is deferred too,
    for the same reason it would have been if slow.
    """
    if not attached:
        return Localized([], [])
    path = directory or _cache_dir()
    sweep(path)

    to_fetch = attached[:MAX_FILES]
    # Named before any fetch starts, so a name follows the order in and not
    # the order the fetches finish.
    taken: set[str] = set()
    names = [unique_filename(attachment, taken) for attachment in to_fetch]
    local_paths: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=min(4, len(to_fetch))) as pool:
        futures = {
            pool.submit(_fetch, http, attachment, path, name=name): attachment
            for attachment, name in zip(to_fetch, names)
        }
        for future in as_completed(futures):
            local_paths[futures[future].stream_index] = future.result()

    files: list[tuple[streams.Attachment, str]] = []
    deferred: list[streams.Attachment] = []
    fetched = 0
    for attachment in attached:
        local = local_paths.get(attachment.stream_index, "")
        if local:
            fetched += 1
            files.append((attachment, local))
        elif attachment.sidecar:
            files.append((attachment, attachment.url))
        else:
            LOG.debug(
                "subtitle %s deferred: the server is still extracting it",
                attachment.stream_index,
            )
            deferred.append(attachment)
    if fetched:
        LOG.debug("fetched %d subtitle(s) for their labels", fetched)
    return Localized(files, deferred)
