from resources.lib.utils import fix_unique_ids, jsonrpc_request


MOVIE_PROPERTIES = ["title", "year", "uniqueid", "playcount", "lastplayed", "userrating", "dateadded", "file"]
TVSHOW_PROPERTIES = ["title", "uniqueid"]
EPISODE_PROPERTIES = [
    "title", "season", "episode", "tvshowid", "uniqueid",
    "playcount", "lastplayed", "userrating", "dateadded", "file",
]

# Order in which a match is attempted when an item carries more than one
# canonical id -- mirrors the preference already used by find_library_match
# in utils.py for the watchlist browser.
PROVIDER_PRIORITY = ("tmdb", "imdb", "tvdb", "trakt", "mdblist")

# MDBList only ever sends tmdb/tvdb for an episode's own id (nested "ids"
# under /sync/watched's full-pull "episode" object, or flat
# episode_tmdb_id/episode_tvdb_id in /sync/journal rows) -- no imdb/trakt/
# mdblist episode id exists in either API shape.
EPISODE_ID_PROVIDER_PRIORITY = ("tmdb", "tvdb")


def _movies():
    return jsonrpc_request("VideoLibrary.GetMovies", {"properties": MOVIE_PROPERTIES}).get("movies") or []


def _tvshow_ids_by_dbid():
    shows = jsonrpc_request("VideoLibrary.GetTVShows", {"properties": TVSHOW_PROPERTIES}).get("tvshows") or []
    result = {}
    for show in shows:
        ids = fix_unique_ids(show.get("uniqueid", {}), "show")
        if ids:
            result[show.get("tvshowid")] = ids
    return result


def _episodes():
    return jsonrpc_request("VideoLibrary.GetEpisodes", {"properties": EPISODE_PROPERTIES}).get("episodes") or []


def build_snapshot():
    """Full local library snapshot used to match remote sync state against
    Kodi library rows: movies and episodes, each indexed by every canonical
    external id they carry (movies) or their parent show carries (episodes),
    combined with season/episode number.

    TV shows/seasons are intentionally not tracked as their own units here --
    Kodi has no directly writable "show watched"/"show rating" field beyond
    what's derived from its episodes, so watched/ratings/collection sync all
    operate at movie+episode granularity, same as live scrobbling already does.
    """
    snapshot = {"movie": {}, "episode": {}}

    for movie in _movies():
        ids = fix_unique_ids(movie.get("uniqueid", {}), "movie")
        if not ids:
            continue
        record = {
            "dbtype": "movie",
            "dbid": movie.get("movieid"),
            "title": movie.get("title"),
            "ids": ids,
            "playcount": movie.get("playcount") or 0,
            "lastplayed": movie.get("lastplayed") or None,
            "userrating": movie.get("userrating") or 0,
            "dateadded": movie.get("dateadded") or None,
            "file": movie.get("file") or None,
        }
        for provider, value in ids.items():
            snapshot["movie"]["{}:{}".format(provider, value)] = record

    show_ids_by_dbid = _tvshow_ids_by_dbid()

    for episode in _episodes():
        show_ids = show_ids_by_dbid.get(episode.get("tvshowid"))
        if not show_ids:
            continue
        season = episode.get("season")
        episode_number = episode.get("episode")
        # The episode's own id (if any) describes this one specific episode
        # -- tried before falling back to show id + season/episode number,
        # since it's immune to shows that renumber seasons/episodes
        # differently across metadata scrapers (common for anime).
        episode_ids = fix_unique_ids(episode.get("uniqueid", {}), "episode")
        record = {
            "dbtype": "episode",
            "dbid": episode.get("episodeid"),
            "title": episode.get("title"),
            "show_ids": show_ids,
            "episode_ids": episode_ids,
            "season": season,
            "episode": episode_number,
            "playcount": episode.get("playcount") or 0,
            "lastplayed": episode.get("lastplayed") or None,
            "userrating": episode.get("userrating") or 0,
            "dateadded": episode.get("dateadded") or None,
            "file": episode.get("file") or None,
        }
        for provider, value in show_ids.items():
            key = "{}:{}:{}:{}".format(provider, value, season, episode_number)
            snapshot["episode"][key] = record
        for provider in EPISODE_ID_PROVIDER_PRIORITY:
            value = episode_ids.get(provider)
            if value not in (None, ""):
                snapshot["episode"]["episode-id:{}:{}".format(provider, value)] = record

    return snapshot


MOVIE_RATING_PROPERTIES = ["uniqueid", "userrating"]
EPISODE_RATING_PROPERTIES = ["season", "episode", "tvshowid", "userrating"]


def build_ratings_snapshot():
    """Lighter version of build_snapshot() for a frequent local ratings-only
    poll (see sync_orchestrator.check_ratings_local): Kodi's native "Rate" UI
    doesn't reliably announce VideoLibrary.OnUpdate the way marking watched
    does (confirmed -- no notification arrives when rating through the video
    info dialog), so there's no event to react to and this has to poll.
    Skips playcount/lastplayed/dateadded/file entirely since ratings_sync
    doesn't need them, keeping a frequent poll cheap. Same record/bucket
    shape as build_snapshot() so it's a drop-in for ratings_sync.push()."""
    snapshot = {"movie": {}, "episode": {}}

    movies = jsonrpc_request("VideoLibrary.GetMovies", {"properties": MOVIE_RATING_PROPERTIES}).get("movies") or []
    for movie in movies:
        ids = fix_unique_ids(movie.get("uniqueid", {}), "movie")
        if not ids:
            continue
        record = {
            "dbtype": "movie",
            "dbid": movie.get("movieid"),
            "ids": ids,
            "userrating": movie.get("userrating") or 0,
        }
        for provider, value in ids.items():
            snapshot["movie"]["{}:{}".format(provider, value)] = record

    show_ids_by_dbid = _tvshow_ids_by_dbid()

    episodes = jsonrpc_request("VideoLibrary.GetEpisodes", {"properties": EPISODE_RATING_PROPERTIES}).get("episodes") or []
    for episode in episodes:
        show_ids = show_ids_by_dbid.get(episode.get("tvshowid"))
        if not show_ids:
            continue
        season = episode.get("season")
        episode_number = episode.get("episode")
        record = {
            "dbtype": "episode",
            "dbid": episode.get("episodeid"),
            "show_ids": show_ids,
            "season": season,
            "episode": episode_number,
            "userrating": episode.get("userrating") or 0,
        }
        for provider, value in show_ids.items():
            key = "{}:{}:{}:{}".format(provider, value, season, episode_number)
            snapshot["episode"][key] = record

    return snapshot


def journal_episode_ids(entry):
    """Combines a /sync/journal episode row's flat episode_tmdb_id/
    episode_tvdb_id fields into a dict find_episode_match can use -- that
    API shape carries the episode's own id as separate top-level fields
    rather than nested under "ids" (unlike the /sync/watched full-pull
    shape's episode["ids"]), verified against a live call, not documented
    anywhere. Returns None if the row carries neither."""
    tmdb = entry.get("episode_tmdb_id")
    tvdb = entry.get("episode_tvdb_id")
    if tmdb is None and tvdb is None:
        return None
    return {"tmdb": tmdb, "tvdb": tvdb}


def canonical_movie_key(ids):
    for provider in PROVIDER_PRIORITY:
        value = ids.get(provider)
        if value not in (None, ""):
            return "movie:{}:{}".format(provider, value)
    return None


def canonical_episode_key(show_ids, season, episode):
    for provider in PROVIDER_PRIORITY:
        value = show_ids.get(provider)
        if value not in (None, ""):
            return "episode:{}:{}:{}:{}".format(provider, value, season, episode)
    return None


def find_movie_match(snapshot, ids):
    bucket = snapshot.get("movie") or {}
    for provider in PROVIDER_PRIORITY:
        value = ids.get(provider)
        if value in (None, ""):
            continue
        match = bucket.get("{}:{}".format(provider, value))
        if match:
            return match
    return None


def find_episode_match(snapshot, show_ids, season, episode, episode_ids=None):
    """Looks up an episode by its own id first (immune to shows that
    renumber seasons/episodes differently across metadata scrapers),
    falling back to show id + season/episode number."""
    bucket = snapshot.get("episode") or {}

    if episode_ids:
        for provider in EPISODE_ID_PROVIDER_PRIORITY:
            value = episode_ids.get(provider)
            if value in (None, ""):
                continue
            match = bucket.get("episode-id:{}:{}".format(provider, value))
            if match:
                return match

    if season in (None, "") or episode in (None, ""):
        return None
    for provider in PROVIDER_PRIORITY:
        value = show_ids.get(provider)
        if value in (None, ""):
            continue
        match = bucket.get("{}:{}:{}:{}".format(provider, value, season, episode))
        if match:
            return match
    return None


def iter_movies(snapshot):
    seen = set()
    for record in (snapshot.get("movie") or {}).values():
        if record["dbid"] in seen:
            continue
        seen.add(record["dbid"])
        yield record


def iter_episodes(snapshot):
    seen = set()
    for record in (snapshot.get("episode") or {}).values():
        if record["dbid"] in seen:
            continue
        seen.add(record["dbid"])
        yield record
