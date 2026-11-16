"""What a sync cycle's additions are announced as: one message per content
type, naming the item when there is one of it and counting when there are
several.

* A watched item is never announced.
* Songs are not announced: an album says it arrived. ``BoxSet`` and
  ``Season`` are silent too.
"""

from typing import Any, NamedTuple, Optional
from collections.abc import Iterable

from kofin.core import settings

MOVIE = "Movie"
SERIES = "Series"
EPISODE = "Episode"
MUSICVIDEO = "MusicVideo"
ARTIST = "MusicArtist"
ALBUM = "MusicAlbum"

# Jellyfin types that produce a message; Audio entries exist only for
# download subscriptions.
ANNOUNCED = (MOVIE, SERIES, EPISODE, MUSICVIDEO, ARTIST, ALBUM)

# Message strings, singular then plural. The singular takes the item's name,
# the plural a count; the two episode lines take a count *and* a show name
# (arity checked in tests/unit/test_new_content.py).
MOVIE_ONE = 30624
MOVIE_MANY = 30625
SERIES_ONE = 30626
SERIES_MANY = 30627
EPISODE_ONE = 30628
EPISODE_MANY = 30629
EPISODES_MIXED = 30630
MUSICVIDEO_ONE = 30631
MUSICVIDEO_MANY = 30632
ARTIST_ONE = 30633
ARTIST_MANY = 30634
ALBUM_ONE = 30635
ALBUM_MANY = 30636


class Entry(NamedTuple):
    """One announceable addition.

    ``series``/``series_id`` are the episode's show (empty for every other
    type): the name is what a message says, the id is what groups episodes and
    matches them against a show announced in the same batch.
    """

    type: str
    item_id: str
    name: str
    series: str = ""
    series_id: str = ""


def entry_for(item: dict[str, Any]) -> Optional[Entry]:
    """The announceable entry for an item, or None when it is not.

    None covers every reason to stay quiet: a type with no message, a watched
    item, and payloads too thin to name (no ``Id``, no ``Name``, an episode
    with no show).
    """
    item_type = item.get("Type") or ""

    if item_type not in ANNOUNCED and item_type != "Audio":
        return None

    if item_type != "Audio" and (item.get("UserData") or {}).get("Played"):
        return None

    item_id = item.get("Id") or ""
    name = (item.get("Name") or "").strip()

    if not item_id or not name:
        return None

    if item_type != EPISODE:
        return Entry(item_type, item_id, name)

    series = (item.get("SeriesName") or "").strip()
    series_id = item.get("SeriesId") or ""

    if not series or not series_id:
        return None

    return Entry(item_type, item_id, name, series, series_id)


def summarize(entries: Iterable[Entry]) -> list[str]:
    """The messages for one cycle's entries, in display order.

    Ids are deduplicated first.
    """
    unique: dict[str, Entry] = {}

    for entry in entries:
        unique.setdefault("%s/%s" % (entry.type, entry.item_id), entry)

    by_type: dict[str, list[Entry]] = {}

    for entry in unique.values():
        by_type.setdefault(entry.type, []).append(entry)

    messages: list[str] = []

    _count_line(messages, by_type.get(MOVIE, []), MOVIE_ONE, MOVIE_MANY)
    _count_line(messages, by_type.get(SERIES, []), SERIES_ONE, SERIES_MANY)
    _episode_line(messages, by_type.get(EPISODE, []), by_type.get(SERIES, []))
    _count_line(messages, by_type.get(MUSICVIDEO, []), MUSICVIDEO_ONE, MUSICVIDEO_MANY)
    _count_line(messages, by_type.get(ARTIST, []), ARTIST_ONE, ARTIST_MANY)
    _count_line(messages, by_type.get(ALBUM, []), ALBUM_ONE, ALBUM_MANY)

    return messages


def _count_line(
    messages: list[str], entries: list[Entry], one_id: int, many_id: int
) -> None:
    """Name it when there is one of it, count it when there are more."""
    if not entries:
        return

    if len(entries) == 1:
        messages.append(settings.localized(one_id) % entries[0].name)
    else:
        messages.append(settings.localized(many_id) % len(entries))


def _episode_line(
    messages: list[str], episodes: list[Entry], series: list[Entry]
) -> None:
    """The episode line, which is three lines depending on the spread.

    Episodes of a show announced in the same batch are dropped: "Severance
    show added to library" followed by "8 episodes of Severance added to
    library" is the same news twice, and the show line is the one that says
    it is new. When that was all of them, no episode line is raised at all.
    """
    announced = {entry.item_id for entry in series}
    remaining = [entry for entry in episodes if entry.series_id not in announced]

    if not remaining:
        return

    shows = {entry.series_id for entry in remaining}

    if len(shows) > 1:
        messages.append(settings.localized(EPISODES_MIXED) % len(remaining))
        return

    template = EPISODE_ONE if len(remaining) == 1 else EPISODE_MANY
    messages.append(
        settings.localized(template) % (len(remaining), remaining[0].series)
    )
