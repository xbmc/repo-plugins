"""The kind table: what Kodi's public API offers each native kind.

Everything kind-specific that is a *fact about the API* lives here, so the
reconciler can be driven by lookups rather than ``if kind ==`` branches: which
methods list, read, set, refresh and remove a kind, which properties its
readback carries, how a row of it is removed, and which Jellyfin types have a
native row at all.
"""

from typing import Any, NamedTuple, Optional
from collections.abc import Collection, Sequence

from kofin.core import kodirpc

# Independent setters go 25 to a JSON-RPC array; a failed call is cheap to
# retry.
BATCH = 25

# The two music kinds whose patch is their artwork and text, applied once the
# music scans are done and before the version and extra scans
# (native._apply).
MUSIC_FIRST = ("MusicAlbum", "MusicArtist")

# Application order: a season or episode patch needs its show's row first
# and a set needs its movies. Songs go last: each played song is a setter,
# and every album cover would wait behind them.
ORDER = (
    "Series",
    "Season",
    "Episode",
    "Movie",
    "MusicVideo",
    "BoxSet",
    "MusicAlbum",
    "MusicArtist",
    "Audio",
)

# Kinds whose rows carry a resolver URL and a namespaced unique id.
FILED = ("Movie", "Series", "Episode", "MusicVideo")

# Kodi's media type for a playable kind, for playback and userdata lookups.
MEDIA = {
    "movie": "Movie",
    "episode": "Episode",
    "musicvideo": "MusicVideo",
    "song": "Audio",
}

# Kodi's media type for a library row that holds others, for the Jellyfin
# actions menu (identity.mapped_item).
CONTAINERS = {
    "tvshow": "Series",
    "season": "Season",
    "set": "BoxSet",
    "album": "MusicAlbum",
    "artist": "MusicArtist",
}

# Kinds whose rows carry userdata the server and Kodi both edit.
PLAYABLE = ("Movie", "Episode", "MusicVideo", "Audio")

# Playable kinds with a watcher behind Kodi's announcements: their userdata
# writes are recorded as expectations so the echo is not read as a local
# edit. Nothing listens for songs (AudioLibrary.OnUpdate is not watched and
# Kodi has no watched UI for songs), so a song expectation would be a write
# for nothing.
EXPECTED = ("Movie", "Episode", "MusicVideo")

# Kinds the music scanner derives from song tags rather than files: they
# have no directory, no listing of their own and leave when their songs do.
DERIVED = ("MusicAlbum", "MusicArtist")


class Kind(NamedTuple):
    listing: str
    list_key: str
    id_param: str
    getter: str
    result_key: str
    setter: str
    refresh: Optional[str]
    remove: Optional[str]
    # How a tombstone of this kind leaves Kodi (removal.py): "row" by its own
    # remove call, "parent" with its show, "members" with the movies that
    # filed it, "rescan" through the complete listing of its directory.
    removal: str


KINDS: dict[str, Kind] = {
    "Movie": Kind(
        "VideoLibrary.GetMovies",
        "movies",
        "movieid",
        "VideoLibrary.GetMovieDetails",
        "moviedetails",
        "VideoLibrary.SetMovieDetails",
        "VideoLibrary.RefreshMovie",
        "VideoLibrary.RemoveMovie",
        "row",
    ),
    "Series": Kind(
        "VideoLibrary.GetTVShows",
        "tvshows",
        "tvshowid",
        "VideoLibrary.GetTVShowDetails",
        "tvshowdetails",
        "VideoLibrary.SetTVShowDetails",
        "VideoLibrary.RefreshTVShow",
        "VideoLibrary.RemoveTVShow",
        "row",
    ),
    "Season": Kind(
        "VideoLibrary.GetSeasons",
        "seasons",
        "seasonid",
        "VideoLibrary.GetSeasonDetails",
        "seasondetails",
        "VideoLibrary.SetSeasonDetails",
        None,
        None,
        "parent",
    ),
    "Episode": Kind(
        "VideoLibrary.GetEpisodes",
        "episodes",
        "episodeid",
        "VideoLibrary.GetEpisodeDetails",
        "episodedetails",
        "VideoLibrary.SetEpisodeDetails",
        "VideoLibrary.RefreshEpisode",
        "VideoLibrary.RemoveEpisode",
        "row",
    ),
    "MusicVideo": Kind(
        "VideoLibrary.GetMusicVideos",
        "musicvideos",
        "musicvideoid",
        "VideoLibrary.GetMusicVideoDetails",
        "musicvideodetails",
        "VideoLibrary.SetMusicVideoDetails",
        "VideoLibrary.RefreshMusicVideo",
        "VideoLibrary.RemoveMusicVideo",
        "row",
    ),
    "BoxSet": Kind(
        "VideoLibrary.GetMovieSets",
        "sets",
        "setid",
        "VideoLibrary.GetMovieSetDetails",
        "setdetails",
        "VideoLibrary.SetMovieSetDetails",
        None,
        None,
        "members",
    ),
    "Audio": Kind(
        "AudioLibrary.GetSongs",
        "songs",
        "songid",
        "AudioLibrary.GetSongDetails",
        "songdetails",
        "AudioLibrary.SetSongDetails",
        None,
        None,
        "rescan",
    ),
    "MusicAlbum": Kind(
        "AudioLibrary.GetAlbums",
        "albums",
        "albumid",
        "AudioLibrary.GetAlbumDetails",
        "albumdetails",
        "AudioLibrary.SetAlbumDetails",
        None,
        None,
        "rescan",
    ),
    "MusicArtist": Kind(
        "AudioLibrary.GetArtists",
        "artists",
        "artistid",
        "AudioLibrary.GetArtistDetails",
        "artistdetails",
        "AudioLibrary.SetArtistDetails",
        None,
        None,
        "rescan",
    ),
}

# The kinds the pipeline files, in the table's order.
NAMES = tuple(KINDS)

# What a scope readback carries: enough to find a row, own it and see the
# userdata a viewer may have changed, never the whole row. The full row is
# read by id (or as one listing when most of a scope needs it) only for the
# items whose desired state moved.
MINIMAL: dict[str, list[str]] = {
    "Movie": ["file", "uniqueid", "playcount", "lastplayed", "resume"],
    "Series": ["file", "uniqueid"],
    "Season": ["season", "tvshowid"],
    "Episode": ["file", "uniqueid", "playcount", "lastplayed", "resume", "tvshowid"],
    "MusicVideo": ["file", "uniqueid", "playcount", "lastplayed", "resume"],
    "BoxSet": ["title"],
}

# A property or setter field a Kodi has only with a feature
# (requirements.json). A readback that asks for a property Kodi's field enum
# does not name fails whole, and a setter refuses a parameter it does not
# take, so both are shaped by the feature table (capabilities.features):
# on Piers Video.Fields.Season has no plot and Video.Fields.Episode no tag.
FEATURE_FIELDS: dict[str, dict[str, str]] = {
    "Season": {"plot": "season_plot"},
    "Episode": {"tag": "episode_tags"},
}


def properties(
    kind: str, features: Collection[str], minimal: bool = False
) -> list[str]:
    """The readback properties of ``kind`` on a Kodi with ``features``: the
    scope's minimal set with ``minimal``, else the full row."""
    names = MINIMAL.get(kind, PROPERTIES[kind]) if minimal else PROPERTIES[kind]
    gated = FEATURE_FIELDS.get(kind, {})
    return [
        name for name in names if gated.get(name) is None or gated[name] in features
    ]


PROPERTIES: dict[str, list[str]] = {
    "Movie": [
        "file",
        "uniqueid",
        "title",
        "plot",
        "playcount",
        "lastplayed",
        "resume",
        "tag",
        "art",
        "ratings",
        "originaltitle",
        "sorttitle",
        "plotoutline",
        "tagline",
        "year",
        "premiered",
        "mpaa",
        "runtime",
        "genre",
        "studio",
        "country",
        "director",
        "writer",
        "dateadded",
        "trailer",
        "set",
    ],
    "Series": [
        "file",
        "uniqueid",
        "title",
        "originaltitle",
        "sorttitle",
        "plot",
        "premiered",
        "mpaa",
        "genre",
        "studio",
        "tag",
        "art",
        "ratings",
        "dateadded",
        "trailer",
        "status",
        "runtime",
    ],
    "Season": ["season", "title", "plot", "art", "tvshowid"],
    "Episode": [
        "file",
        "uniqueid",
        "title",
        "originaltitle",
        "plot",
        "firstaired",
        "season",
        "episode",
        "runtime",
        "director",
        "writer",
        "tag",
        "art",
        "ratings",
        "dateadded",
        "playcount",
        "lastplayed",
        "resume",
        "tvshowid",
    ],
    "MusicVideo": [
        "file",
        "uniqueid",
        "title",
        "plot",
        "runtime",
        "director",
        "studio",
        "year",
        "premiered",
        "genre",
        "album",
        "artist",
        "track",
        "tag",
        "art",
        "rating",
        "dateadded",
        "playcount",
        "lastplayed",
        "resume",
    ],
    "BoxSet": ["title", "plot", "art"],
    # A song's readback is one call for a whole library, so it carries only
    # what the pass compares -- its userdata -- and what maps its album.
    # Every property that joins another table (artistid, genreid) costs the
    # whole listing dear, as the schema itself warns.
    "Audio": ["file", "albumid", "playcount", "lastplayed"],
    "MusicAlbum": ["art", "description"],
    "MusicArtist": ["art", "description"],
}


def rpc(method: str, params: Optional[dict[str, Any]] = None) -> Any:
    result = kodirpc.call(method, params or {})
    if result is None or result is kodirpc.FAILED:
        raise RuntimeError("Kodi refused " + method)
    return result


def rpc_batch(requests: Sequence[tuple[str, Optional[dict[str, Any]]]]) -> list[Any]:
    """Every reply, as a result or the RuntimeError that ``rpc`` would raise."""
    results = kodirpc.batch(requests)
    return [
        (
            RuntimeError("Kodi refused " + method)
            if result is None or result is kodirpc.FAILED
            else result
        )
        for (method, _), result in zip(requests, results)
    ]
