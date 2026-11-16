"""Build Kodi ListItems from Jellyfin item DTOs via InfoTagVideo/InfoTagMusic.

Pure helpers (paths, art, resume, type mapping) are separated from the
tag-setter glue so they can be unit tested; the setters are validated by the
Kodistubs type check and exercised live.
"""

import time
from typing import Any, Optional

import xbmc
import xbmcgui

from kofin.core import settings
from kofin.core.log import Logger
from kofin.core.urls import plugin_url

LOG = Logger(__name__)

JsonDict = dict[str, Any]


FOLDER_TYPES = frozenset(
    {
        "CollectionFolder",
        "UserView",
        "Folder",
        "Series",
        "Season",
        "BoxSet",
        "MusicArtist",
        "MusicAlbum",
        "Playlist",
        "PhotoAlbum",
        "Genre",
        "MusicGenre",
    }
)

# Jellyfin's AudioBook is an Audio item.
AUDIO_TYPES = frozenset({"Audio", "AudioBook"})

PLAYABLE_TYPES = (
    frozenset({"Movie", "Episode", "MusicVideo", "Video", "Trailer", "Recording"})
    | AUDIO_TYPES
)

MUSIC_TYPES = AUDIO_TYPES | {"MusicAlbum", "MusicArtist", "MusicGenre"}

# Kodi's media type for each Jellyfin item type a tag can carry.
MEDIATYPE = {
    "Movie": "movie",
    "Series": "tvshow",
    "Season": "season",
    "Episode": "episode",
    "MusicVideo": "musicvideo",
    "BoxSet": "set",
    "Video": "video",
    "Trailer": "video",
    "Recording": "video",
    "Audio": "song",
    "MusicAlbum": "album",
    "MusicArtist": "artist",
}


def is_folder(item: JsonDict) -> bool:
    if item.get("Type") in PLAYABLE_TYPES:
        return False
    return bool(item.get("IsFolder")) or item.get("Type") in FOLDER_TYPES


def play_path(item_id: str) -> str:
    """The playback URL of an item — one spelling, because Kodi keys what it
    remembers about a plugin row (its resume bookmark, its play count) on this
    exact string, and the reset that clears the bookmark has to name it
    identically (actions.reset_resume)."""
    return plugin_url({"mode": "play", "id": item_id})


def path_for(item: JsonDict) -> str:
    """The navigation/playback URL for an item."""
    item_type = item.get("Type", "")
    item_id = item.get("Id", "")
    if item_type in PLAYABLE_TYPES:
        return play_path(item_id)
    return plugin_url({"mode": "browse", "folder": item_id, "type": item_type.lower()})


def resume_of(item: JsonDict, offset: Optional[float] = None) -> tuple[float, float]:
    """(resume seconds, total seconds) from UserData/RunTimeTicks.

    The position carries the Advanced-tab resume offset, so the time Kodi's
    resume prompt names is the time playback will actually start at.

    ``offset`` is a precomputed ``settings.resume_offset()`` — listings pass
    it so a thousand rows cost one settings read, not a thousand (each read
    constructs a fresh Addon; see ``settings.adjusted_resume``).
    """
    userdata = item.get("UserData") or {}
    position = float(userdata.get("PlaybackPositionTicks") or 0) / 10_000_000
    total = float(item.get("RunTimeTicks") or 0) / 10_000_000
    return settings.adjusted_resume(position, offset), total


def playcount_of(item: JsonDict) -> int:
    """Kodi playcount for a DTO -- 0 unless the server calls the item played.

    ``Played`` is the watch state and ``PlayCount`` only sizes it: Jellyfin
    *keeps* the count when an item is marked unwatched.
    """
    userdata = item.get("UserData") or {}
    if not userdata.get("Played"):
        return 0
    return int(userdata.get("PlayCount") or 0) or 1


def hdr_type(stream: JsonDict) -> str:
    """Kodi's ``hdrtype`` for a Jellyfin video MediaStream; '' for SDR.

    DvProfile is tested first because it is the signal that survives the
    variants -- a Dolby Vision stream can report any of DOVI, DOVIWithHDR10,
    DOVIWithHDR10Plus or DOVIInvalid as its VideoRangeType, and all of them
    carry the profile.
    """
    if "DvProfile" in stream:
        return "dolbyvision"
    range_type = stream.get("VideoRangeType") or ""
    if range_type in ("HDR10", "HDR10Plus"):
        return "hdr10"
    if "HLG" in range_type:
        return "hlg"
    return ""


def person_thumb(server: str, person: JsonDict) -> str:
    """A person's portrait URL, '' when the server has none.

    A URL, not a cached file: Kodi fetches it when the info dialog draws the
    cast, and only then. Capped and encoded (``person_query``), because the
    video scanner caches a row's actor thumbs at import
    (``videolibrary.actorthumbs``, on by default).
    """
    tag = person.get("PrimaryImageTag")
    person_id = person.get("Id")
    if not tag or not person_id:
        return ""
    return "%s/Items/%s/Images/Primary?tag=%s%s" % (
        server,
        person_id,
        tag,
        person_query(),
    )


# The art query, memoised for a moment. Module state on purpose: a settings
# read constructs a fresh Addon each time (settings.get_addon), and art_for
# runs once per item. Two seconds of memory survives any restart (it is time,
# not a handle) and a settings change shows within them.
_ART_QUERY: tuple[float, str, str] = (0.0, "", "")
ART_QUERY_TTL = 2.0
# The longest side of a person's portrait, which is drawn as a thumb beside a
# name, never across a screen.
PERSON_MAX = 400


def art_query() -> str:
    """The size cap and encoding the server applies to listed artwork.

    Kodi decodes and re-encodes every image it caches and caps the result at
    its own fanart and thumb heights, so anything the server sends above the
    cap is work for nothing. ``maxArtResolution`` asks the server for the
    capped height (its own resize, cached server-side) and ``compressArt`` for
    JPEG at quality 90, which only changes bytes once a resize happens.
    """
    return _queries()[0]


def person_query() -> str:
    """The cap and encoding for a person's portrait: ``PERSON_MAX`` on its
    longest side, or the artwork cap where that is the smaller."""
    return _queries()[1]


def _queries() -> tuple[str, str]:
    global _ART_QUERY
    now = time.monotonic()
    stamp, art, person = _ART_QUERY
    if now - stamp < ART_QUERY_TTL:
        return art, person
    maxheight = settings.get_int("maxArtResolution")
    quality = "&Quality=90" if settings.get_bool("compressArt") else ""
    art = "&MaxHeight=%d%s" % (maxheight, quality) if maxheight else ""
    side = min(maxheight, PERSON_MAX) if maxheight else PERSON_MAX
    person = "&MaxHeight=%d&MaxWidth=%d%s" % (side, side, quality)
    _ART_QUERY = (now, art, person)
    return art, person


def forget_art_query() -> None:
    """Drop the memo (tests, and anything that changes the settings itself)."""
    global _ART_QUERY
    _ART_QUERY = (0.0, "", "")


def art_for(item: JsonDict, server: str) -> dict[str, str]:
    """Art dict with parent fallbacks (series poster on episodes, etc.)."""
    query = art_query()

    def image(
        item_id: str, image_type: str, tag: str, index: Optional[int] = None
    ) -> str:
        path = "%s/Items/%s/Images/%s" % (server, item_id, image_type)
        if index is not None:
            path += "/%d" % index
        return path + "?tag=%s" % tag + query

    art: dict[str, str] = {}
    item_id = item.get("Id", "")
    tags = item.get("ImageTags") or {}

    if tags.get("Primary"):
        primary = image(item_id, "Primary", tags["Primary"])
        art["thumb"] = primary
        art["poster"] = primary
    if tags.get("Logo"):
        art["clearlogo"] = image(item_id, "Logo", tags["Logo"])
    if tags.get("Thumb"):
        art["landscape"] = image(item_id, "Thumb", tags["Thumb"])
    if tags.get("Banner"):
        art["banner"] = image(item_id, "Banner", tags["Banner"])

    backdrops = item.get("BackdropImageTags") or []
    if backdrops:
        art["fanart"] = image(item_id, "Backdrop", backdrops[0], index=0)
    else:
        parent_backdrops = item.get("ParentBackdropImageTags") or []
        parent_id = item.get("ParentBackdropItemId")
        if parent_backdrops and parent_id:
            art["fanart"] = image(parent_id, "Backdrop", parent_backdrops[0], index=0)

    series_id = item.get("SeriesId")
    series_tag = item.get("SeriesPrimaryImageTag")
    if series_id and series_tag:
        series_primary = image(series_id, "Primary", series_tag)
        art["tvshow.poster"] = series_primary
        if item.get("Type") == "Episode":
            art["poster"] = series_primary
        if "thumb" not in art:
            art["thumb"] = series_primary

    album_id = item.get("AlbumId")
    album_tag = item.get("AlbumPrimaryImageTag")
    if album_id and album_tag and "thumb" not in art:
        art["thumb"] = image(album_id, "Primary", album_tag)

    return art


def build(
    item: JsonDict,
    server: str,
    resume_seconds: Optional[float] = None,
    resume_offset: Optional[float] = None,
) -> xbmcgui.ListItem:
    """A fully populated ListItem for a Jellyfin DTO.

    ``resume_seconds`` replaces the resume point derived from the item's
    UserData, and 0 means no resume point at all. The play route passes the
    position this playback was resolved to start at (see ``plugin.play``).

    ``resume_offset`` is a precomputed ``settings.resume_offset()`` for
    listings that build many rows (see :func:`resume_of`).
    """
    li = xbmcgui.ListItem(item.get("Name", ""), offscreen=True)
    li.setArt(art_for(item, server))
    li.setProperty("kofin.id", item.get("Id", ""))

    if item.get("Type") in MUSIC_TYPES:
        _fill_music(li, item)
    elif item.get("Type") not in ("Photo", "PhotoAlbum", "Genre"):
        _fill_video(li, item, server, resume_seconds, resume_offset)

    # Exactly the rows path_for sends to the play route.
    if item.get("Type") in PLAYABLE_TYPES:
        li.setProperty("IsPlayable", "true")
    return li


# Library containers (addon root views, etc.) are folders, not media: their
# tag takes a title and a plot.
_CONTAINER_TYPES = frozenset({"CollectionFolder", "UserView"})


def _fill_video(
    li: xbmcgui.ListItem,
    item: JsonDict,
    server: str,
    resume_seconds: Optional[float] = None,
    resume_offset: Optional[float] = None,
) -> None:
    tag = li.getVideoInfoTag()
    item_type = item.get("Type", "")
    tag.setTitle(item.get("Name", ""))

    if item_type in _CONTAINER_TYPES:
        if item.get("Overview"):
            tag.setPlot(item["Overview"])
        return

    # A DBTYPE of video is playable video to addon.xml's "Play with
    # transcoding", so a type MEDIATYPE does not name takes none.
    media_type = MEDIATYPE.get(item_type)
    if media_type:
        tag.setMediaType(media_type)

    if item.get("OriginalTitle"):
        tag.setOriginalTitle(item["OriginalTitle"])
    if item.get("SortName"):
        tag.setSortTitle(item["SortName"])
    if item.get("Overview"):
        tag.setPlot(item["Overview"])
    if item.get("Taglines"):
        tag.setTagLine(item["Taglines"][0])
    if item.get("ProductionYear"):
        tag.setYear(int(item["ProductionYear"]))
    if item.get("PremiereDate"):
        premiered = str(item["PremiereDate"])[:10]
        tag.setPremiered(premiered)
        if item_type == "Episode":
            tag.setFirstAired(premiered)
    if item.get("DateCreated"):
        tag.setDateAdded(str(item["DateCreated"])[:19].replace("T", " "))
    if item.get("OfficialRating"):
        tag.setMpaa(item["OfficialRating"])
    if item.get("RunTimeTicks"):
        tag.setDuration(int(item["RunTimeTicks"] // 10_000_000))
    if item.get("Genres"):
        tag.setGenres(list(item["Genres"]))
    if item.get("Studios"):
        tag.setStudios([studio.get("Name", "") for studio in item["Studios"]])
    if item.get("CommunityRating") is not None:
        tag.setRating(float(item["CommunityRating"]), isdefault=True)

    provider_ids = item.get("ProviderIds") or {}
    if provider_ids:
        unique_ids = {
            key.lower(): value for key, value in provider_ids.items() if value
        }
        if unique_ids:
            tag.setUniqueIDs(unique_ids)

    if item_type == "Episode":
        if item.get("IndexNumber") is not None:
            tag.setEpisode(int(item["IndexNumber"]))
        if item.get("ParentIndexNumber") is not None:
            tag.setSeason(int(item["ParentIndexNumber"]))
        if item.get("SeriesName"):
            tag.setTvShowTitle(item["SeriesName"])
    elif item_type == "Season":
        if item.get("IndexNumber") is not None:
            tag.setSeason(int(item["IndexNumber"]))
        if item.get("SeriesName"):
            tag.setTvShowTitle(item["SeriesName"])

    tag.setPlaycount(playcount_of(item))
    position, total = resume_of(item, resume_offset)
    if resume_seconds is not None:
        # The resolved item: 0 means the setter is never called (plugin.play).
        if resume_seconds > 0 and total > 0:
            tag.setResumePoint(resume_seconds, total)
    elif total > 0:
        # A listing row: stamped either way. Kodi reads a zero point with a
        # total as "set, and nothing to resume", which is not resumable and —
        # the reason it is stamped — keeps Kodi from consulting the bookmark it
        # saved for this plugin path the last time the item was stopped
        # (VideoUtils.cpp GetNonFolderItemResumeInformation falls back to
        # MyVideos only for an unset point).
        tag.setResumePoint(position, total)

    people = item.get("People") or []
    if people:
        actors = [
            xbmc.Actor(
                person.get("Name", ""),
                person.get("Role", ""),
                index,
                person_thumb(server, person),
            )
            for index, person in enumerate(people)
            if person.get("Type") in ("Actor", "GuestStar")
        ]
        if actors:
            tag.setCast(actors)
        directors = [p.get("Name", "") for p in people if p.get("Type") == "Director"]
        if directors:
            tag.setDirectors(directors)
        writers = [p.get("Name", "") for p in people if p.get("Type") == "Writer"]
        if writers:
            tag.setWriters(writers)

    for stream in item.get("MediaStreams") or []:
        stream_type = stream.get("Type")
        if stream_type == "Video":
            tag.addVideoStream(
                xbmc.VideoStreamDetail(
                    width=int(stream.get("Width") or 0),
                    height=int(stream.get("Height") or 0),
                    codec=stream.get("Codec") or "",
                    duration=int(item.get("RunTimeTicks") or 0) // 10_000_000,
                    hdrtype=hdr_type(stream),
                )
            )
        elif stream_type == "Audio":
            tag.addAudioStream(
                xbmc.AudioStreamDetail(
                    channels=int(stream.get("Channels") or 2),
                    codec=stream.get("Codec") or "",
                    language=stream.get("Language") or "",
                )
            )
        elif stream_type == "Subtitle":
            tag.addSubtitleStream(
                xbmc.SubtitleStreamDetail(language=stream.get("Language") or "")
            )


def _fill_music(li: xbmcgui.ListItem, item: JsonDict) -> None:
    tag = li.getMusicInfoTag()
    item_type = item.get("Type", "")
    tag.setMediaType(
        {"Audio": "song", "MusicAlbum": "album", "MusicArtist": "artist"}.get(
            item_type, "song"
        )
    )
    tag.setTitle(item.get("Name", ""))
    if item.get("Artists"):
        tag.setArtist(" / ".join(item["Artists"]))
    if item.get("AlbumArtist"):
        tag.setAlbumArtist(item["AlbumArtist"])
    if item.get("Album"):
        tag.setAlbum(item["Album"])
    if item.get("ProductionYear"):
        tag.setYear(int(item["ProductionYear"]))
    if item.get("RunTimeTicks"):
        tag.setDuration(int(item["RunTimeTicks"] // 10_000_000))
    if item.get("IndexNumber") is not None:
        tag.setTrack(int(item["IndexNumber"]))
    if item.get("ParentIndexNumber") is not None:
        tag.setDisc(int(item["ParentIndexNumber"]))
    if item.get("Genres"):
        tag.setGenres(list(item["Genres"]))
