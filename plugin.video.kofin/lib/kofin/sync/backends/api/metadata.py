"""One normalized policy for scanner ListItems and public detail patches.

``details`` is the desired native state of an item as the JSON-RPC setter of
its kind takes it, and ``listitem`` is the same facts expressed through the
InfoTag the scanner reads, so a row the scanner just created already matches
most of what the patch would send. Kodi persists its own representation --
trimmed strings, arrays through the configured separator, the year from a
full premiere date -- and ``details`` speaks that representation.
"""

import hashlib
import re
import time
from datetime import datetime, timezone
from typing import Any, NamedTuple, Optional, Union
from collections.abc import Collection, Iterable, Sequence

import xbmc
import xbmcgui

from kofin.core.log import Logger
from kofin.plugin import listitems
from kofin.sync.model import ratings as shared_ratings, streams_and_runtime
from . import paths
from .paths import ASCII_SPACE
from .store import encode, payload_hash

LOG = Logger(__name__)

# An episode as a show's listing names it: its payload, or the row
# ``episode_row`` reduces it to.
EpisodeRef = Union[dict[str, Any], tuple[str, int, int]]

_DATE_RE = re.compile(
    r"^(\d{1,4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?"
)


def convert_to_local(date: Union[str, datetime]) -> str:
    """A Jellyfin UTC timestamp in local time (``YYYY-MM-DDTHH:MM:SS``).
    Handles 7-digit tick fractions and the year-1 "no date" sentinel."""
    try:
        if isinstance(date, datetime):
            parsed = date
        else:
            match = _DATE_RE.match(str(date))
            if not match:
                raise ValueError("unrecognized date: %r" % date)
            year, month, day, hour, minute, second = (
                int(part) for part in match.groups()[:6]
            )
            parsed = datetime(year, month, day, hour, minute, second)
        parsed = parsed.replace(tzinfo=timezone.utc)
        # Bad metadata defaults to date 1-1-1. astimezone() on it can
        # underflow, and it only means "no date" anyway.
        if parsed.year < 1900:
            return (
                f"{parsed.year:04d}-{parsed.month:02d}-{parsed.day:02d}"
                f"T{parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
            )
        return parsed.astimezone().strftime("%Y-%m-%dT%H:%M:%S")
    except Exception as error:
        LOG.exception("Item date: %s --- %s", str(date), error)
        return str(date)


MUSIC = ("Audio", "MusicAlbum", "MusicArtist")
# Jellyfin's "no date" for music: year 1, 0001-01-01.
NO_YEAR = 1
FAVORITE_TAG = {
    "Movie": "Favorite movies",
    "Series": "Favorite tvshows",
    # An episode keeps its tags only with the episode_tags feature (details,
    # kinds.FEATURE_FIELDS).
    "Episode": "Favorite episodes",
    "MusicVideo": "Favorite musicvideos",
}
# Kodi's sort position for a special that airs after a whole season.
AFTER_SEASON_EPISODE = 4096

# Payload keys no serializer reads. A Jellyfin DTO carries them on every
# item and every cast member.
_DROP = ("ImageBlurHashes", "Chapters", "Trickplay", "MediaAttachments")


def compact(item: dict[str, Any]) -> dict[str, Any]:
    """The DTO minus what nothing reads; applied before hashing or storing.

    A song keeps its sources (the file size is the scanner's hash input)
    and drops its streams: no music setter reads them.
    """
    result = {k: v for k, v in item.items() if k not in _DROP}
    if not result.get("SpecialFeatureCount"):
        # Every movie is sent the count; only one with extras keeps it.
        result.pop("SpecialFeatureCount", None)
    sources = item.get("MediaSources")
    if item.get("Type") == "Audio":
        result.pop("MediaStreams", None)
    if isinstance(sources, list):
        if not result.get("MediaStreams") and item.get("Type") != "Audio":
            for source in sources:
                if isinstance(source, dict) and source.get("MediaStreams"):
                    result["MediaStreams"] = source["MediaStreams"]
                    break
        # A movie with several sources lists a file per source, each with
        # the source's own streams; a single source's are the item's.
        strip = (
            _DROP
            if len(sources) > 1 and item.get("Type") == "Movie"
            else _DROP + ("MediaStreams",)
        )
        result["MediaSources"] = [
            (
                {k: v for k, v in s.items() if k not in strip}
                if isinstance(s, dict)
                else s
            )
            for s in sources
        ]
    people = item.get("People")
    if isinstance(people, list):
        result["People"] = [
            (
                {k: v for k, v in p.items() if k != "ImageBlurHashes"}
                if isinstance(p, dict)
                else p
            )
            for p in people
        ]
    return result


# What a special feature's payload keeps: its row, its file name and the
# streams Kodi reads off the listing.
_EXTRA_KEYS = (
    "Id",
    "Name",
    "Overview",
    "Container",
    "RunTimeTicks",
    "ImageTags",
    "BackdropImageTags",
    "ExtraType",
    "DateCreated",
    "MediaStreams",
)


# A tag earlier builds put on every row; patch.merge takes it off.
LIBRARY_TAG_PREFIX = "kofin.library."


def compact_extra(feature: dict[str, Any]) -> dict[str, Any]:
    """A movie's special feature as its payload carries it."""
    result = {k: feature[k] for k in _EXTRA_KEYS if k in feature}
    sources = feature.get("MediaSources")
    if not result.get("MediaStreams") and isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict) and source.get("MediaStreams"):
                result["MediaStreams"] = source["MediaStreams"]
                break
    return result


def version_sources(item: dict[str, Any]) -> list[dict[str, Any]]:
    """The media sources a movie is listed by, a file each, when it has
    more than one; Jellyfin's first is the one the movie's plain URL plays."""
    sources = [
        s
        for s in (item.get("MediaSources") or [])
        if isinstance(s, dict) and s.get("Id")
    ]
    return sources if len(sources) > 1 else []


def version_label(source: dict[str, Any]) -> str:
    """A media source's name as a video asset title, or empty when it is no
    label: Jellyfin's ``GetMediaSourceName`` returns the file name without
    its extension unless local alternate versions exist, so a name equal to
    the source file's stem says nothing about the version. Kodi files an
    untitled asset as the Standard Edition."""
    name = str(source.get("Name") or "").strip(ASCII_SPACE)
    if not name or name.lower() == "standard edition":
        return ""
    path = str(source.get("Path") or "").replace("\\", "/").rsplit("/", 1)[-1]
    stem = path.rsplit(".", 1)[0] if "." in path else path
    if stem and name.lower() == stem.lower():
        return ""
    return name


def special_features(item: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        f
        for f in (item.get("SpecialFeatures") or [])
        if isinstance(f, dict) and f.get("Id") and f.get("Name")
    ]


def assets_token(item: dict[str, Any], features: Collection[str] = frozenset()) -> str:
    """What a movie's folder lists beyond the movie's own file: its version
    files and its extras, as the listing names them on a Kodi with
    ``features`` (version files only with ``video_versions``). Empty for a
    movie with neither. The pass scans the folder by name when the token
    moves, since the root walk lists the movie's file alone."""
    sources = version_sources(item) if "video_versions" in features else []
    extras = special_features(item)
    if not sources and not extras:
        return ""
    return _token(
        {
            "versions": [[s["Id"], s.get("Name") or ""] for s in sources],
            "extras": [
                [f["Id"], stem, paths.video_container_of(f)]
                for stem, f in paths.extra_stems(extras)
            ],
        }
    )


def asset_files(
    item: dict[str, Any],
    key: str,
    library: str,
    features: Collection[str] = frozenset(),
) -> Optional[dict[str, Any]]:
    """The files a movie's folder lists beyond its own, by URL: its version
    files with the source's name (only with ``video_versions``), its
    extras. None for a movie with neither. Acknowledged beside the assets
    token, so what a movie's folder listed is known without a payload being
    loaded for it: which movies have an extras folder to bind
    (``Native.bind_movie_folders``)."""
    sources = version_sources(item) if "video_versions" in features else []
    extras = special_features(item)
    if not sources and not extras:
        return None
    item_id = str(item.get("Id") or "")
    # The label, not the raw name: this is the name the version is filed
    # under, and a name equal to the file's stem is no label
    # (version_label). The token above keeps the raw name, so a rename
    # still moves it.
    return {
        "versions": [
            [paths.version_url(key, library, item_id, s["Id"]), version_label(s)]
            for s in sources[1:]
        ],
        "extras": [
            paths.extra_url(key, library, item_id, stem, f)
            for stem, f in paths.extra_stems(extras)
        ],
    }


# A movie that lost every version and extra keeps an empty entry, so that
# its last acknowledgement does not still list them.
NO_ASSET_FILES: dict[str, Any] = {"versions": [], "extras": []}


def item_separator() -> str:
    """Read Kodi's configured video-array separator through its public tag API.

    The ListItem must outlive the tag: ``getVideoInfoTag`` hands out a
    pointer into the item (``InfoTagVideo(tag, offscreen)``, owned=false),
    and the item's destructor deletes it. Taken from a temporary, the tag
    dangles and the first setter writes freed memory.
    """
    probe = xbmcgui.ListItem(offscreen=True)
    tag = probe.getVideoInfoTag()
    tag.setGenres(["kofin_left", "kofin_right"])
    joined = tag.getGenre()
    del tag
    del probe
    return joined[len("kofin_left") : -len("kofin_right")] if joined else " / "


def _token(value: Any) -> str:
    return hashlib.sha256(encode(value).encode()).hexdigest()[:24]


def refresh_fields(
    item: dict[str, Any], seasons: Iterable[dict[str, Any]] = ()
) -> dict[str, Any]:
    """Fields with no complete public setter: a change here means a refresh.

    An episode's sort numbering has no setter, so it joins the token. A
    show's seasons join it by number alone: a season's name and plot are its
    own row's to patch.
    """
    kind = item.get("Type")
    keys: tuple[str, ...] = ("People",)
    if kind in ("Movie", "Episode", "MusicVideo"):
        keys += ("MediaStreams", "MediaSources", "Video3DFormat", "AspectRatio")
    if kind == "Episode":
        keys += (
            "AirsBeforeSeasonNumber",
            "AirsAfterSeasonNumber",
            "AirsBeforeEpisodeNumber",
            "IndexNumberEnd",
        )
    value: dict[str, Any] = {key: item.get(key) for key in keys}
    if kind == "Movie" and isinstance(value.get("MediaSources"), list):
        # The movie's own source alone, without its name or streams: its
        # further sources are version files its folder's scan files,
        # Jellyfin's first-source name and the source's streams change with
        # the number of versions, and a refresh files the movie again under
        # a new id.
        value["MediaSources"] = [
            (
                {k: v for k, v in source.items() if k not in ("Name", "MediaStreams")}
                if isinstance(source, dict)
                else source
            )
            for source in value["MediaSources"][:1]
        ]
    if kind == "Series":
        value["Seasons"] = sorted(
            int(s.get("IndexNumber") or 0)
            for s in seasons
            if s.get("IndexNumber") is not None
        )
    return value


def refresh_token(item: dict[str, Any], seasons: Iterable[dict[str, Any]] = ()) -> str:
    return _token(refresh_fields(item, seasons))


# The token's fields by what a viewer would call them, for the line a
# refresh is logged with.
REFRESH_PARTS = {
    "People": "cast",
    "MediaStreams": "streams",
    "MediaSources": "streams",
    "Video3DFormat": "streams",
    "AspectRatio": "streams",
    "AirsBeforeSeasonNumber": "numbering",
    "AirsAfterSeasonNumber": "numbering",
    "AirsBeforeEpisodeNumber": "numbering",
    "IndexNumberEnd": "numbering",
    "Seasons": "seasons",
}


def refresh_parts(
    item: dict[str, Any], seasons: Iterable[dict[str, Any]] = ()
) -> dict[str, str]:
    """The token's own fields, a short hash per part: kept beside a row's
    acknowledgement so that the refresh of it can say which part moved. The
    token alone says only that something did. Built from the one dict the
    token hashes, so a field cannot join the token and be missing here; one
    that has no word yet is reported under its own name."""
    grouped: dict[str, dict[str, Any]] = {}
    for key, value in refresh_fields(item, seasons).items():
        grouped.setdefault(REFRESH_PARTS.get(key, key.lower()), {})[key] = value
    return {part: _token(value)[:8] for part, value in sorted(grouped.items())}


def userdata(item: dict[str, Any]) -> dict[str, Any]:
    """The userdata Kodi keeps for a playable row. A song has no resume point
    in Kodi's music library, so a song's is its playcount and last played."""
    data = item.get("UserData") or {}
    result: dict[str, Any] = {"playcount": listitems.playcount_of(item)}
    if item.get("Type") != "Audio":
        result["resume"] = {
            "position": float(data.get("PlaybackPositionTicks") or 0) / 10000000,
            "total": float(item.get("RunTimeTicks") or 0) / 10000000,
        }
    # Kodi's watched setter generates a timestamp when none is supplied.
    # Preserve that supported behavior for old server records without a date;
    # explicit server dates and unwatched clears still round-trip exactly.
    if data.get("LastPlayedDate"):
        result["lastplayed"] = _timestamp(data["LastPlayedDate"])
    elif not result["playcount"]:
        if item.get("Type") != "Audio":
            result["lastplayed"] = ""
        # An unplayed song has no opinion on its stamp. Kodi's song setter
        # cannot clear one: it loads the row, an empty date leaves the old
        # one standing (CDateTime::SetFromDBDateTime), and UpdateSong writes
        # it back, so a desired empty date fails every readback.
    elif item.get("Type") == "Audio":
        # Played, but the server never recorded when. Kodi's UpdateSong
        # stamps the current time on a played song with no date
        # (MusicDatabase.cpp). The date the server first saw the song is the
        # latest moment certainly no later than the play, and it never reads
        # as recent. The video setters leave a missing date alone.
        result["lastplayed"] = _timestamp(item.get("DateCreated"))
    return result


def unique_ids(
    item: dict[str, Any], key: str, seasons: Iterable[dict[str, Any]] = ()
) -> dict[str, str]:
    result = {
        k.lower(): str(v) for k, v in (item.get("ProviderIds") or {}).items() if v
    }
    result.update(
        kofin=paths.identity(key, item["Id"]),
        kofinrefresh=refresh_token(item, seasons),
    )
    return result


def tags(item: dict[str, Any], kind: str = "Movie") -> list[str]:
    if kind not in FAVORITE_TAG:
        return []
    values = [value.strip(ASCII_SPACE) for value in item.get("Tags") or []]
    if (item.get("UserData") or {}).get("IsFavorite"):
        values.append(FAVORITE_TAG[kind])
    return sorted(set(value for value in values if value))


def ratings(item: dict[str, Any]) -> dict[str, Any]:
    result = {}
    source = shared_ratings(
        dict(
            Rating=item.get("CommunityRating"),
            Votes=item.get("VoteCount"),
            CriticRating=item.get("CriticRating"),
        )
    )
    for name, (rating, votes) in source.items():
        if rating is not None:
            result[name] = {
                "rating": float(rating),
                "votes": int(votes or 0),
                "default": name == "default",
            }
    return result


def episode_numbers(item: dict[str, Any]) -> Optional[dict[str, int]]:
    """Kodi's numbering for an episode, or None when Kodi cannot file it.

    The scanner keeps an episode whose tag says season >= 0 and episode > 0,
    or -- for a plugin -- season > 0 and episode >= 0. An unnumbered special
    (season 0, no number) matches neither and would be dropped with a log
    line, so it stays dynamic-only and is counted, not imported.
    """
    season = item.get("ParentIndexNumber")
    episode = item.get("IndexNumber")
    if season is None:
        if item.get("AbsoluteEpisodeNumber"):
            season, episode = 1, item["AbsoluteEpisodeNumber"]
        else:
            season = 0
    season = int(season)
    episode = int(episode) if episode is not None else 0
    if not ((season >= 0 and episode > 0) or (season > 0 and episode >= 0)):
        return None
    result = {"season": season, "episode": episode}
    after = item.get("AirsAfterSeasonNumber")
    before = item.get("AirsBeforeSeasonNumber")
    if after is not None:
        result["sortseason"] = int(after)
        result["sortepisode"] = AFTER_SEASON_EPISODE
    elif before is not None:
        result["sortseason"] = int(before)
        result["sortepisode"] = int(item.get("AirsBeforeEpisodeNumber") or 0)
    return result


def season_title(season: dict[str, Any]) -> str:
    """A season's custom name; '' when Jellyfin's default label is in use.

    Kodi labels an unnamed season itself, localized, so the server's English
    "Season 3" must not be written over it.
    """
    name = (season.get("Name") or "").strip(ASCII_SPACE)
    number = season.get("IndexNumber")
    if number is None:
        return name
    defaults = {"Season %d" % int(number), "Season %02d" % int(number)}
    if int(number) == 0:
        defaults |= {"Specials", "Special"}
    return "" if name in defaults else str(name)


def _clean_strings(data: dict[str, Any], fields: Iterable[str]) -> None:
    for field in fields:
        data[field] = (data.get(field) or "").strip(ASCII_SPACE)


def _clean_arrays(data: dict[str, Any], fields: Iterable[str], separator: str) -> None:
    # InfoTag setters trim ASCII whitespace. String-array fields round-trip
    # through Kodi's configured separator; tags use separate native links.
    for field in fields:
        data[field] = list(
            dict.fromkeys(
                part.strip(ASCII_SPACE)
                for value in data.get(field) or []
                for part in (value.split(separator) if separator else [value])
                if part.strip(ASCII_SPACE)
            )
        )


def _people(item: dict[str, Any], role: str) -> list[str]:
    return [p["Name"] for p in item.get("People") or [] if p.get("Type") == role]


def _date(value: Any, length: int = 10) -> str:
    return str(value or "")[:length].replace("T", " ")


def _int(value: Any) -> int:
    """A number the server sent, or 0 when absent or unparsable."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _timestamp(value: Any) -> str:
    """A server UTC instant as the local-time text Kodi stores and shows.

    Kodi writes its own lastplayed and dateadded in local time, so a UTC
    string would read an hour or more off in the UI and differ from every
    value Kodi sets itself. Dates (premiered, first aired) stay as given:
    shifting a calendar date by the zone would move it a day.
    """
    if not value:
        return ""
    return convert_to_local(value)[:19].replace("T", " ")


# Kodi's own spelling of a last-played stamp, local time: what _timestamp writes.
STAMP = "%Y-%m-%d %H:%M:%S"
# How much later than the server's stamp Kodi's own may be and still be
# the same play: the server stamps a play when it starts and Kodi when it
# ends, so the two differ by the length of what was played, pauses included.
SAME_PLAY = 6 * 3600
# How much earlier than the server's a stamp of Kodi's own may be and still
# be the same play. Kodi stamps a song when it ends, the server when kofin
# reports the stop a moment later.
STOP_REPORT = 10


def same_play(actual: str, wanted: str) -> bool:
    """Whether Kodi's last-played stamp needs no write to agree with the
    server's: equal, later by up to SAME_PLAY or earlier by up to
    STOP_REPORT, it is the same play."""
    if actual == wanted:
        return True
    if not actual or not wanted:
        return False
    try:
        # On Python 3.11 datetime.strptime fails in every interpreter after
        # the first that called it, which keeps its _strptime module;
        # time.strptime imports the module on each call.
        ahead = (
            datetime(*time.strptime(actual, STAMP)[:6])
            - datetime(*time.strptime(wanted, STAMP)[:6])
        ).total_seconds()
    except ValueError:
        return False
    return -STOP_REPORT <= ahead <= SAME_PLAY


def own_art(item: dict[str, Any], server: str) -> dict[str, str]:
    """The art a row carries in its own right: no dotted key (``tvshow.*``,
    ``season.*``), which Kodi reads off the show and season rows.

    An episode has no poster, and a thumb only for its own picture: the
    listing mapping fills both from the show, which is right for a plugin
    listing and wrong for a library row.
    """
    art = {
        key: value
        for key, value in listitems.art_for(item, server).items()
        if "." not in key
    }
    if item.get("Type") == "Episode":
        art.pop("poster", None)
        if not (item.get("ImageTags") or {}).get("Primary"):
            art.pop("thumb", None)
    return art


def details(
    item: dict[str, Any],
    server: str,
    key: str,
    library: str,
    separator: str = " / ",
    seasons: Sequence[dict[str, Any]] = (),
    set_name: Optional[str] = None,
    features: Collection[str] = frozenset(),
) -> dict[str, Any]:
    """The desired native state, keyed as the kind's JSON-RPC setter takes it.

    Explicit empty values clear metadata the server removed. ``features`` is
    what this Kodi offers (``capabilities.features``): a field its setter
    does not take is left out, so it is neither sent nor compared -- a
    season's plot and an episode's tags are Kodi 23's (``kinds.FEATURE_FIELDS``).
    """
    kind = item.get("Type", "Movie")
    if kind in MUSIC:
        return music_details(item, server)
    data: dict[str, Any] = {
        "title": item.get("Name", ""),
        "plot": item.get("Overview") or "",
        "art": own_art(item, server),
        "dateadded": _timestamp(item.get("DateCreated")),
    }
    if kind == "BoxSet":
        _clean_strings(data, ("title", "plot"))
        data.pop("dateadded")
        return data
    data["uniqueid"] = unique_ids(item, key, seasons)
    if kind != "Season":
        data["runtime"] = int(item.get("RunTimeTicks") or 0) // 10000000
    if kind in FAVORITE_TAG and (kind != "Episode" or "episode_tags" in features):
        data["tag"] = tags(item, kind)
    if kind in ("Movie", "Series", "Episode"):
        data["originaltitle"] = item.get("OriginalTitle") or ""
        data["ratings"] = ratings(item)
    if kind in ("Movie", "Series"):
        data.update(
            sorttitle=item.get("SortName") or "",
            premiered=_date(item.get("PremiereDate")),
            mpaa=item.get("OfficialRating") or "",
            genre=item.get("Genres") or [],
            studio=[s["Name"] for s in item.get("Studios") or []],
            trailer=next(
                (t["Url"] for t in item.get("RemoteTrailers") or [] if t.get("Url")),
                "",
            ),
        )
    if kind == "Movie":
        data.update(
            plotoutline=item.get("ShortOverview") or "",
            tagline=next(iter(item.get("Taglines") or []), ""),
            year=int(item.get("ProductionYear") or 0),
            country=item.get("ProductionLocations") or [],
            director=_people(item, "Director"),
            writer=_people(item, "Writer"),
        )
        if set_name is not None:
            data["set"] = set_name.strip(ASCII_SPACE)
    elif kind == "Series":
        data["status"] = item.get("Status") or ""
        # A show's date added is derived: tvshowcounts takes the newest of
        # its episode files, and SetTVShowDetails cannot move it.
        data.pop("dateadded")
    elif kind == "Episode":
        numbers = episode_numbers(item) or {}
        data.update(
            firstaired=_date(item.get("PremiereDate")),
            season=numbers.get("season", 0),
            episode=numbers.get("episode", 0),
            director=_people(item, "Director"),
            writer=_people(item, "Writer"),
        )
    elif kind == "MusicVideo":
        data.update(
            year=int(item.get("ProductionYear") or 0),
            premiered=_date(item.get("PremiereDate")),
            genre=item.get("Genres") or [],
            studio=[s["Name"] for s in item.get("Studios") or []],
            director=_people(item, "Director"),
            artist=list(item.get("Artists") or []),
            album=item.get("Album") or "",
            track=int(item.get("IndexNumber") or 0),
        )
        if item.get("CommunityRating") is not None:
            data["rating"] = float(item["CommunityRating"])
    elif kind == "Season":
        data = {
            "title": season_title(item),
            "art": data["art"],
            "uniqueid": data["uniqueid"],
        }
        # No opinion on an empty plot: Kodi's season setter leaves the
        # stored one in place (SetDetailsForSeason writes no empty plot), so
        # an empty desired plot would differ from the row on every pass. No
        # plot at all without the season_plot feature: the setter has no
        # such parameter and the season readback no such property.
        plot = (item.get("Overview") or "").strip(ASCII_SPACE)
        if plot and "season_plot" in features:
            data["plot"] = plot
        return data
    _clean_strings(
        data,
        [
            f
            for f in (
                "title",
                "originaltitle",
                "sorttitle",
                "plot",
                "plotoutline",
                "tagline",
                "mpaa",
                "trailer",
                "status",
                "album",
            )
            if f in data
        ],
    )
    _clean_arrays(
        data,
        [
            f
            for f in ("genre", "studio", "country", "director", "writer", "artist")
            if f in data
        ],
        separator,
    )
    # Kodi stores one release date. Its public year is derived from a
    # full premiere date, even when Jellyfin's ProductionYear differs.
    if data.get("premiered") and "year" in data:
        data["year"] = int(data["premiered"][:4])
    if kind in ("Movie", "Episode", "MusicVideo"):
        data.update(userdata(item))
    # No opinion on a date the server does not have. Kodi fills a missing
    # premiere or aired date itself and its setters ignore an empty one, so
    # an empty desired value never matches the row.
    for key in ("dateadded", "premiered", "firstaired"):
        if key in data and not data.get(key):
            data.pop(key)
    return data


# -- music ---------------------------------------------------------------------


def music_art(item: dict[str, Any], server: str) -> dict[str, str]:
    """The two art types Kodi's music library shows for albums and artists."""
    art = listitems.art_for(item, server)
    return {key: art[key] for key in ("thumb", "fanart") if art.get(key)}


def music_details(item: dict[str, Any], server: str) -> dict[str, Any]:
    """The desired native state of a music kind.

    A song's tags are the scanner's to write: the only public setter a song
    needs after import is for the userdata the scanner discards (``CSong``
    zeroes the play count of every new row). An album or artist
    is derived from its songs, and what it cannot derive -- its art and its
    description -- is the whole of its desired state.
    """
    kind = item.get("Type")
    if kind == "Audio":
        return userdata(item)
    return {
        "art": music_art(item, server),
        "description": (item.get("Overview") or "").strip(ASCII_SPACE),
    }


def names(credits: Optional[Iterable[Any]]) -> list[str]:
    result = []
    for credit in credits or []:
        name = credit.get("Name", "") if isinstance(credit, dict) else str(credit)
        name = name.strip(ASCII_SPACE)
        if name and name not in result:
            result.append(name)
    return result


def song_year(item: dict[str, Any]) -> int:
    year = _int(item.get("ProductionYear"))
    return year if year > NO_YEAR else 0


def song_tags(
    item: dict[str, Any], album: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Every tag the song's ListItem sets, as plain values: the scanner's
    input, and the hash a metadata change moves the directory by.

    The album's MusicBrainz ids come from the album's own record so every
    song in the directory carries the same ones; a Jellyfin id is never
    dressed as an MBID. Userdata is deliberately absent: a play on the
    server must not re-import the album. Every number goes through ``_int``:
    the function is total, so one malformed song cannot stall its library.
    """
    album = album or {}
    sources = item.get("MediaSources") or []
    size = 0
    if sources and isinstance(sources[0], dict):
        size = _int(sources[0].get("Size"))
    providers = item.get("ProviderIds") or {}
    album_providers = album.get("ProviderIds") or {}
    year = song_year(item)
    release = _date(item.get("PremiereDate")) if year else ""
    return {
        "title": (item.get("Name") or "").strip(ASCII_SPACE),
        "album": (item.get("Album") or album.get("Name") or "").strip(ASCII_SPACE),
        "albumartist": names(item.get("AlbumArtists") or album.get("AlbumArtists")),
        "artist": names(item.get("ArtistItems")) or names(item.get("Artists")),
        "genre": [g.strip(ASCII_SPACE) for g in item.get("Genres") or [] if g],
        "track": _int(item.get("IndexNumber")),
        "disc": _int(item.get("ParentIndexNumber")),
        "duration": _int(item.get("RunTimeTicks")) // 10000000,
        "year": year,
        "releasedate": release,
        "musicbrainztrackid": str(providers.get("MusicBrainzTrack") or ""),
        "musicbrainzalbumid": str(album_providers.get("MusicBrainzAlbum") or ""),
        "musicbrainzreleasegroupid": str(
            album_providers.get("MusicBrainzReleaseGroup") or ""
        ),
        "size": size,
    }


def tag_hash(item: dict[str, Any], album: Optional[dict[str, Any]] = None) -> str:
    return _token(song_tags(item, album))


def hash_time(digest: str) -> str:
    """A timestamp derived from a hash, for the directory's own hash.

    The music scanner hashes a directory by each item's path, size and
    full date, and skips a directory whose hash it already holds; a song
    whose tags changed therefore has to present a different date, or the
    rescan never happens. Twenty-five years of seconds is the range.
    """
    import datetime

    seconds = int(digest[:12], 16) % (25 * 365 * 86400)
    moment = datetime.datetime(2000, 1, 1) + datetime.timedelta(seconds=seconds)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def mark_loaded(li: xbmcgui.ListItem, size: int) -> None:
    """Tell the scanner the tag is complete so it reads no file.

    ``InfoTagMusic`` has no ``setLoaded``; the legacy ``setInfo`` sets the
    flag, and its ``size`` key is the one that does so without the
    per-row deprecation warning. The real file size is the scanner's hash
    input, never an invented one. An upstream ``setLoaded`` replaces this
    here and nowhere else.
    """
    li.setInfo("music", {"size": str(size)})
    tag = li.getMusicInfoTag()
    if hasattr(tag, "setLoaded"):
        tag.setLoaded(True)


def song_listitem(
    item: dict[str, Any],
    album: Optional[dict[str, Any]] = None,
    salt: int = 0,
    features: Collection[str] = frozenset(),
) -> xbmcgui.ListItem:
    """A scanner row for a song: its tags, its size, and a date that moves
    with its tags so a change re-imports the directory."""
    tags = song_tags(item, album)
    li = xbmcgui.ListItem(tags["title"] or item.get("Name", ""), offscreen=True)
    tag = li.getMusicInfoTag()
    tag.setMediaType("song")
    tag.setTitle(tags["title"])
    if tags["album"]:
        tag.setAlbum(tags["album"])
    if tags["albumartist"]:
        tag.setAlbumArtist(" / ".join(tags["albumartist"]))
    if tags["artist"]:
        tag.setArtist(" / ".join(tags["artist"]))
    if tags["genre"]:
        tag.setGenres(tags["genre"])
    if tags["track"]:
        tag.setTrack(tags["track"])
    if tags["disc"]:
        tag.setDisc(tags["disc"])
    if tags["duration"]:
        tag.setDuration(tags["duration"])
    if tags["year"]:
        tag.setYear(tags["year"])
    if tags["releasedate"]:
        tag.setReleaseDate(tags["releasedate"])
    if tags["musicbrainztrackid"]:
        tag.setMusicBrainzTrackID(tags["musicbrainztrackid"])
    if tags["musicbrainzalbumid"]:
        tag.setMusicBrainzAlbumID(tags["musicbrainzalbumid"])
    if tags["musicbrainzreleasegroupid"]:
        tag.setMusicBrainzReleaseGroupID(tags["musicbrainzreleasegroupid"])
    # When the server first saw the song (song_date_added). Not one of the
    # tags: a date the server corrects moves no directory's hash, and an
    # existing library takes the date as its directories are listed again.
    created = _timestamp(item.get("DateCreated"))
    if created and "song_date_added" in features:
        tag.setDateAdded(created)
    # The date is what the scanner hashes a listing by; a salt moves it
    # without touching a tag (store.bump_salt).
    li.setDateTime(hash_time(_token([tags, salt]) if salt else _token(tags)))
    mark_loaded(li, tags["size"])
    return li


def fallback_song_listitem(item: dict[str, Any]) -> xbmcgui.ListItem:
    """The least a song row needs to survive a serializer fault: a title,
    its size and a loaded tag. Better one plain row than a deleted song."""
    sources = item.get("MediaSources") or []
    size = sources[0].get("Size") if sources and isinstance(sources[0], dict) else 0
    li = xbmcgui.ListItem(str(item.get("Name") or item.get("Id") or ""), offscreen=True)
    tag = li.getMusicInfoTag()
    tag.setMediaType("song")
    tag.setTitle(str(item.get("Name") or item.get("Id") or ""))
    if item.get("Album"):
        tag.setAlbum(str(item["Album"]))
    mark_loaded(li, int(size or 0))
    return li


def folder_label(album: Optional[dict[str, Any]], folder: str, salt: int = 0) -> str:
    """The root listing's label for an album directory: Kodi walks a
    directory's folders in label order and numbers albums as it adds
    them, so oldest-first on the server's creation date puts the
    server's newest album at the top of Kodi's recently added. A salted
    directory carries its salt so a root walk sees it changed too."""
    created = str((album or {}).get("DateCreated") or "0000-00-00T00:00:00")[:19]
    return created + " " + folder + (" %d" % salt if salt else "")


def collections_of(boxsets: Iterable[dict[str, Any]]) -> dict[str, str]:
    """Movie id -> the one set Kodi can hold, chosen stably by name then id."""
    result: dict[str, tuple[str, str, str]] = {}
    for boxset in boxsets:
        name = (boxset.get("Name") or "").strip(ASCII_SPACE)
        if not name:
            continue
        rank = (name.lower(), boxset.get("Id", ""), name)
        for member in boxset.get("KofinMembers") or []:
            if member not in result or rank < result[member]:
                result[member] = rank
    return {member: rank[2] for member, rank in result.items()}


# -- scanner ListItems -------------------------------------------------------


def _cast(tag: xbmc.InfoTagVideo, item: dict[str, Any], server: str) -> None:
    actors = [
        xbmc.Actor(
            person.get("Name", ""),
            person.get("Role", ""),
            index,
            listitems.person_thumb(server, person),
        )
        for index, person in enumerate(item.get("People") or [])
        if person.get("Type") in ("Actor", "GuestStar")
    ]
    if actors:
        tag.setCast(actors)


# What a scanner row carries that no setter can put there afterwards, as a
# number, raised when the listing gains something the rows already filed
# lack: 3 with the streams' default, forced and hearing-impaired flags, 2
# without them (``scanner_format`` gives what a Kodi reaches). A library
# filed under a lower number is rebuilt only on Repair (library.Library
# .rebuild_stale).
SCANNER_FORMAT = 3


def scanner_format(features: Collection[str]) -> int:
    """The scanner format a listing carries on a Kodi with ``features``."""
    return SCANNER_FORMAT if "stream_flags" in features else SCANNER_FORMAT - 1


# A Jellyfin stream's flags by the names an NFO's <flag> takes, which is
# what the stream details' setFlags reads.
STREAM_FLAGS = (
    ("IsDefault", "default"),
    ("IsForced", "forced"),
    ("IsHearingImpaired", "hearingimpaired"),
)


def _flags(raw: Iterable[Any], kind: str) -> list[list[str]]:
    """The flag names of each stream of ``kind`` ("Audio", "Subtitle"), in
    the order ``streams_and_runtime`` lists them."""
    return [
        [name for field, name in STREAM_FLAGS if stream.get(field)]
        for stream in raw
        if isinstance(stream, dict) and stream.get("Type") == kind
    ]


def _stream_source(item: dict[str, Any]) -> dict[str, Any]:
    """The item as ``streams_and_runtime`` reads it. ``compact`` keeps a
    single source's streams on the item alone, and the shared reader looks
    in the first source, so they are copied there."""
    sources = item.get("MediaSources") or []
    streams = item.get("MediaStreams")
    if (
        not streams
        or not sources
        or not isinstance(sources[0], dict)
        or sources[0].get("MediaStreams")
    ):
        return item
    first = dict(sources[0], MediaStreams=streams)
    return dict(item, MediaSources=[first] + list(sources[1:]))


def _streams(
    tag: xbmc.InfoTagVideo,
    item: dict[str, Any],
    features: Collection[str] = frozenset(),
) -> None:
    """The item's streams on the tag; their flags only where the stream
    detail classes take them (the stream_flags feature)."""
    flagged = "stream_flags" in features
    source = _stream_source(item)
    streams, runtime = streams_and_runtime(source)
    # The raw list streams_and_runtime reads, for the flags it drops.
    sources = source.get("MediaSources") or []
    raw = (
        (sources[0].get("MediaStreams") if sources else None)
        or source.get("MediaStreams")
        or []
    )
    audio_flags = _flags(raw, "Audio")
    subtitle_flags = _flags(raw, "Subtitle")
    for stream in streams["video"]:
        stereo = {
            "HalfSideBySide": "left_right",
            "FullSideBySide": "left_right",
            "HalfTopAndBottom": "top_bottom",
            "FullTopAndBottom": "top_bottom",
        }.get(stream.get("3d"), "")
        tag.addVideoStream(
            xbmc.VideoStreamDetail(
                width=int(stream.get("width") or 0),
                height=int(stream.get("height") or 0),
                aspect=float(stream.get("aspect") or 0),
                duration=int(runtime),
                codec=stream.get("codec") or "",
                stereomode=stereo,
                hdrtype=stream.get("hdrtype") or "",
            )
        )
    for index, stream in enumerate(streams["audio"]):
        audio = xbmc.AudioStreamDetail(
            channels=int(stream.get("channels") or 0),
            codec=stream.get("codec") or "",
            language=stream.get("language") or "",
        )
        if flagged and index < len(audio_flags) and audio_flags[index]:
            audio.setFlags(audio_flags[index])  # type: ignore[attr-defined]
        tag.addAudioStream(audio)
    for index, language in enumerate(streams["subtitle"]):
        subtitle = xbmc.SubtitleStreamDetail(language=language or "")
        if flagged and index < len(subtitle_flags) and subtitle_flags[index]:
            subtitle.setFlags(subtitle_flags[index])  # type: ignore[attr-defined]
        tag.addSubtitleStream(subtitle)


# What ``details`` makes of a payload, as a number: raised when the same
# payload and inputs come to a different desired state, so that an
# acknowledgement made under the old one is compared again and not taken
# on trust (inputs_token). A pass that finds a number other than the one
# the last pass stamped compares every row (Native.reconcile).
SERIALIZER = 6


def inputs_token(
    server: str,
    key: str,
    library: str,
    separator: str,
    seasons: Iterable[dict[str, Any]] = (),
    set_name: Optional[str] = None,
    downloaded: str = "",
    features: Collection[str] = (),
) -> str:
    """Everything ``details`` reads besides the payload, as one token.

    A mapping that carries the payload hash and this token was acknowledged
    for exactly the desired state the same inputs would produce again, so a
    pass can skip building and comparing it (``patch.Applier.plan``). The
    token is that contract: an input missing from it freezes the state the
    next change of that input should have moved. Besides the caller's
    arguments ``details`` reads the artwork cap and encoding
    (``listitems.art_query``) and renders its timestamps in the local zone
    (``convert_to_local``); both are here, and anything new that
    ``details`` reads joins them.
    """
    return _token(
        [
            SERIALIZER,
            server or "",
            key,
            library or "",
            separator,
            set_name or "",
            sorted(payload_hash(season) for season in seasons),
            listitems.art_query(),
            # The zone, not the current offset: the names list both halves
            # of a zone with daylight saving, so a token does not flip twice
            # a year for a change that convert_to_local already renders
            # correctly per instant.
            [time.timezone, list(time.tzname)],
            # A download's badge and tag are part of the row (downloaded.py).
            downloaded,
            # What this Kodi offers shapes the state (the feature table): a
            # Kodi upgrade compares again, and a Kodi that lacks a feature is
            # never told its rows are stale for it.
            sorted(features),
        ]
    )


# What ``episode_row`` makes of a payload, as a number. The store keeps each
# episode's row beside it (Store.episode_rows), and a row kept under another
# number is reduced again: raised when ``episode_row`` or ``episode_numbers``
# reads a payload differently.
EPISODE_ROW_FORMAT = 1


def episode_row(item: dict[str, Any]) -> Optional[tuple[str, int, int]]:
    """All the show hash takes from an episode: its id and numbering, or
    None for one Kodi cannot file."""
    numbers = episode_numbers(item)
    if numbers is None:
        return None
    return (str(item["Id"]), numbers["season"], numbers["episode"])


def show_hash(episodes: Iterable[EpisodeRef]) -> str:
    """What the scanner may skip a show for: its importable episode set.

    Kodi compares the folder's ``hash`` property with the one it stored after
    the last import and skips the listing when they match, so the hash must
    move when an episode arrives, leaves or is renumbered -- and must not move
    for a plot edit, which the detail patch carries. Takes payloads or the
    rows ``episode_row`` reduces them to.
    """
    rows = []
    for episode in episodes:
        row = episode if isinstance(episode, tuple) else episode_row(episode)
        if row is not None:
            rows.append(row)
    return _token(sorted(rows))


def hash_date(value: str) -> str:
    """A calendar day derived from a hash, for the root listing's own hash.

    The scanner hashes a plugin folder by path, size and *date* (day
    precision), so a show whose contents changed has to show a different
    day or a root-level update skips every show at once.
    """
    days = int(value[:8], 16) % 20000
    import datetime

    day = datetime.date(1971, 1, 1) + datetime.timedelta(days=days)
    return day.strftime("%Y-%m-%dT00:00:00Z")


class Version(NamedTuple):
    """A file of a movie with several media sources, as its scanner row
    says so: the source's label, whether it is the movie's own file, and
    the movie's unique ids (not the source's, whose streams move the
    refresh token). A plugin item's tag takes the NFO branch of
    RetrieveInfoForMovie, which groups a file under the movie its unique ids
    name only when the tag says it has versions. A further version's ids
    leave out ``kofinrefresh`` (``Version.of``): Kodi groups a file under a
    movie only while no unique id type of the two differs
    (``HasConflictingUniqueID``), and the token the movie's row was filed
    under need not be the one a version listed later carries."""

    label: str
    default: bool
    ids: dict[str, str]

    @classmethod
    def of(cls, label: str, default: bool, ids: dict[str, str]) -> "Version":
        if not default:
            ids = {k: v for k, v in ids.items() if k != "kofinrefresh"}
        return cls(label, default, ids)


def listitem(
    item: dict[str, Any],
    server: str,
    key: str,
    library: str,
    separator: str = " / ",
    seasons: Sequence[dict[str, Any]] = (),
    episodes: Optional[Iterable[EpisodeRef]] = None,
    set_name: Optional[str] = None,
    version: Optional[Version] = None,
    features: Collection[str] = frozenset(),
) -> xbmcgui.ListItem:
    """A scanner row: everything ``details`` wants, through the InfoTag.

    No zero resume point is ever stamped: the scanner persists any *set*
    point as a bookmark, and the in-progress rule for movies and episodes
    alike is that row's existence.

    A ``version`` row says it is one of the movie's versions (see
    ``Version``).
    """
    kind = item.get("Type", "Movie")
    if kind == "Audio":
        return song_listitem(item)
    data = details(
        item, server, key, library, separator, seasons, set_name, features=features
    )
    li = xbmcgui.ListItem(data.get("title", item.get("Name", "")), offscreen=True)
    li.setArt(data["art"])
    tag = li.getVideoInfoTag()
    tag.setMediaType(listitems.MEDIATYPE[kind])
    tag.setTitle(data["title"])
    tag.setPlot(data.get("plot", ""))
    if data.get("originaltitle"):
        tag.setOriginalTitle(data["originaltitle"])
    if data.get("sorttitle"):
        tag.setSortTitle(data["sorttitle"])
    if data.get("plotoutline"):
        tag.setPlotOutline(data["plotoutline"])
    if data.get("tagline"):
        tag.setTagLine(data["tagline"])
    if data.get("year"):
        tag.setYear(data["year"])
    if data.get("premiered"):
        tag.setPremiered(data["premiered"])
    if data.get("firstaired"):
        tag.setFirstAired(data["firstaired"])
    if data.get("dateadded"):
        tag.setDateAdded(data["dateadded"])
    if data.get("mpaa"):
        tag.setMpaa(data["mpaa"])
    if data.get("runtime"):
        tag.setDuration(data["runtime"])
    if data.get("genre"):
        tag.setGenres(data["genre"])
    if data.get("studio"):
        tag.setStudios(data["studio"])
    if data.get("country"):
        tag.setCountries(data["country"])
    if data.get("director"):
        tag.setDirectors(data["director"])
    if data.get("writer"):
        tag.setWriters(data["writer"])
    if data.get("tag"):
        tag.setTags(data["tag"])
    if data.get("trailer"):
        tag.setTrailer(data["trailer"])
    if data.get("status"):
        tag.setTvShowStatus(data["status"])
    if data.get("set"):
        # The scanner files the set at import; no patch per member later.
        tag.setSet(data["set"])
    tag.setUniqueIDs(version.ids if version else data["uniqueid"], "kofin")
    if version is not None:
        tag.setHasVideoVersions(True)
        tag.setIsDefaultVideoVersion(version.default)
        if version.label:
            tag.setVideoAssetTitle(version.label)
    if data.get("ratings"):
        tag.setRatings(
            {name: (r["rating"], r["votes"]) for name, r in data["ratings"].items()},
            "default" if "default" in data["ratings"] else "",
        )
    elif data.get("rating") is not None:
        tag.setRating(float(data["rating"]), isdefault=True)
    if kind == "Episode":
        numbers = episode_numbers(item) or {}
        tag.setSeason(numbers.get("season", 0))
        tag.setEpisode(numbers.get("episode", 0))
        if "sortseason" in numbers:
            tag.setSortSeason(numbers["sortseason"])
            tag.setSortEpisode(numbers["sortepisode"])
        if item.get("SeriesName"):
            tag.setTvShowTitle(item["SeriesName"])
    if kind == "MusicVideo":
        if data.get("artist"):
            tag.setArtists(data["artist"])
        if data.get("album"):
            tag.setAlbum(data["album"])
        if data.get("track"):
            tag.setTrackNumber(data["track"])
    if kind == "Series":
        for season in sorted(
            (s for s in seasons if s.get("IndexNumber") is not None),
            key=lambda s: int(s["IndexNumber"]),
        ):
            number = int(season["IndexNumber"])
            tag.addSeason(
                number,
                season_title(season),
                (season.get("Overview") or "").strip(ASCII_SPACE),
            )
            # The season's art rides with the show. The scanner files what a
            # show's tag offers under a season number with the show's own
            # row (GetSeasonThumbs, SetDetailsForTvShow), so a first import
            # finds the season row as desired and sends it nothing. A row
            # Kodi filed otherwise (an artwork level that takes fewer types)
            # differs and is patched.
            for art_type, url in sorted(own_art(season, server).items()):
                tag.addAvailableArtwork(url, art_type, season=number)
        if episodes is not None:
            digest = show_hash(episodes)
            li.setProperty("hash", digest)
            li.setDateTime(hash_date(digest))
    if kind in ("Movie", "Episode", "MusicVideo"):
        if "playcount" in data:
            tag.setPlaycount(data["playcount"])
        if data.get("lastplayed"):
            tag.setLastPlayed(data["lastplayed"])
        resume = data.get("resume") or {}
        if resume.get("position", 0) > 0 and resume.get("total", 0) > 0:
            tag.setResumePoint(resume["position"], resume["total"])
        _cast(tag, item, server)
        _streams(tag, item, features)
    elif kind == "Series":
        _cast(tag, item, server)
    return li


def extra_listitem(
    item: dict[str, Any], server: str, features: Collection[str] = frozenset()
) -> xbmcgui.ListItem:
    """A scanner row for a movie extra. Kodi files the extra by its URL under
    the movie it found beside it (CVideoInfoScanner::AddVideoExtras) and keeps
    the row's dates, streams and art; the name it shows is the file's stem,
    not this tag's title."""
    title = str(item.get("Name") or "")
    li = xbmcgui.ListItem(title, offscreen=True)
    li.setArt(listitems.art_for(item, server))
    tag = li.getVideoInfoTag()
    tag.setMediaType("video")
    tag.setTitle(title)
    plot = (item.get("Overview") or "").strip(ASCII_SPACE)
    if plot:
        tag.setPlot(plot)
    runtime = int((item.get("RunTimeTicks") or 0) // 10_000_000)
    if runtime:
        tag.setDuration(runtime)
    _streams(tag, item, features)
    return li


def owned(data: dict[str, Any]) -> dict[str, list[str]]:
    """The map keys and tags this write puts its name to; a later write may
    clear exactly these and nothing a user or another add-on added."""
    result: dict[str, list[str]] = {}
    for field in ("art", "ratings", "uniqueid"):
        if isinstance(data.get(field), dict):
            result[field] = sorted(data[field])
    if isinstance(data.get("tag"), list):
        result["tag"] = sorted(data["tag"])
    if data.get("set"):
        result["set"] = [data["set"]]
    if "runtime" not in data and data.get("title"):
        # A season's custom name. Withdrawn, it is cleared once -- the pass
        # that still finds it owned -- and then left to Kodi's own label.
        result["title"] = [data["title"]]
    return result
