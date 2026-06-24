# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - Kodi video library access (via JSON-RPC)
#
# We never touch files directly. We ask Kodi's own library for the user's TV
# shows and movies through executeJSONRPC, so we inherit correct titles, ids,
# episode ordering and metadata. Each entry is normalised to:
#   {"type": "tvshow"|"movie", "dbid": <int>, "title": <str>, "year": <int?>}
# where dbid is Kodi's tvshowid / movieid.

import json
import os
import re

import xbmc
import xbmcvfs


# ----------------------------------------------------------------------------
# Internal
# ----------------------------------------------------------------------------

def _rpc(method, params):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
    raw = xbmc.executeJSONRPC(json.dumps(request))
    return json.loads(raw).get('result', {}) or {}


def _episode_playable(episode):
    """Normalise one GetEpisodes record into a queue playable."""
    return {
        'file': episode['file'],
        'label': '{0} - S{1:02d}E{2:02d} - {3}'.format(
            episode.get('showtitle', ''), episode.get('season', 0),
            episode.get('episode', 0), episode.get('title', '')),
        'art': episode.get('art', {}) or {},
        'plot': episode.get('plot', ''),
    }


def _natural_key(text):
    """Sort key that orders embedded numbers numerically ('ep2' before 'ep10')."""
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r'(\d+)', text)]


def _join_path(base, name):
    """Append a child name to a Kodi vfs/file path, tolerating either separator."""
    if base.endswith('/') or base.endswith('\\'):
        return base + name
    return base + '/' + name


def _walk_videos(path, extensions, out):
    """Recursively collect video file paths under `path` into `out`."""
    directories, files = xbmcvfs.listdir(path)
    for name in files:
        if os.path.splitext(name)[1].lower() in extensions:
            out.append(_join_path(path, name))
    for directory in directories:
        _walk_videos(_join_path(path, directory), extensions, out)


# ----------------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------------

def get_tvshows():
    """All TV shows in the library, sorted by title."""
    result = _rpc('VideoLibrary.GetTVShows', {
        'properties': ['title'],
        'sort': {'method': 'title', 'order': 'ascending'},
    })
    return [
        {'type': 'tvshow', 'dbid': show['tvshowid'], 'title': show['title']}
        for show in result.get('tvshows', [])
    ]


def get_movies():
    """All movies in the library, sorted by title."""
    result = _rpc('VideoLibrary.GetMovies', {
        'properties': ['title', 'year'],
        'sort': {'method': 'title', 'order': 'ascending'},
    })
    return [
        {'type': 'movie', 'dbid': movie['movieid'],
         'title': movie['title'], 'year': movie.get('year')}
        for movie in result.get('movies', [])
    ]


def get_moviesets():
    """All movie sets (collections like 'The Lord of the Rings'), sorted by title."""
    result = _rpc('VideoLibrary.GetMovieSets', {
        'properties': ['title'],
        'sort': {'method': 'title', 'order': 'ascending'},
    })
    return [
        {'type': 'movieset', 'dbid': s['setid'], 'title': s['title']}
        for s in result.get('sets', [])
    ]


def get_catalog():
    """TV shows, then movie sets, then movies - the pool for building a channel."""
    return get_tvshows() + get_moviesets() + get_movies()


def get_episode_playables(tvshowid):
    """Ordered (season, episode) list of playable episode dicts for one show."""
    result = _rpc('VideoLibrary.GetEpisodes', {
        'tvshowid': tvshowid,
        'properties': ['title', 'season', 'episode', 'file', 'showtitle', 'art', 'plot'],
    })
    # Season 0 is specials - it does not define show order, so skip it.
    episodes = [e for e in result.get('episodes', [])
                if e.get('file') and e.get('season', 0) >= 1]
    episodes.sort(key=lambda e: (e.get('season', 0), e.get('episode', 0)))
    return [_episode_playable(episode) for episode in episodes]


def get_season_playables(tvshowid, season):
    """Ordered playable episodes for a single season of one show."""
    result = _rpc('VideoLibrary.GetEpisodes', {
        'tvshowid': int(tvshowid),
        'season': int(season),
        'properties': ['title', 'season', 'episode', 'file', 'showtitle', 'art', 'plot'],
    })
    episodes = [e for e in result.get('episodes', []) if e.get('file')]
    episodes.sort(key=lambda e: e.get('episode', 0))
    return [_episode_playable(episode) for episode in episodes]


def get_folder_playables(path):
    """Every video file under `path` (recursively), natural-sorted by full path.
    Labels come from the filename (no library metadata for raw folders)."""
    extensions = {ext for ext in xbmc.getSupportedMedia('video').lower().split('|') if ext}
    files = []
    _walk_videos(path, extensions, files)
    files.sort(key=_natural_key)
    return [
        {
            'file': file_path,
            'label': os.path.splitext(os.path.basename(file_path.rstrip('/\\')))[0],
            'art': {},
            'plot': '',
        }
        for file_path in files
    ]


def get_movie_playables(movieid):
    """Single-element playable list for one movie (or empty if it has no file)."""
    result = _rpc('VideoLibrary.GetMovieDetails', {
        'movieid': movieid, 'properties': ['title', 'file', 'art', 'plot', 'year']})
    movie = result.get('moviedetails', {})
    if not movie.get('file'):
        return []
    label = movie.get('title', '')
    if movie.get('year'):
        label = '{0} ({1})'.format(label, movie['year'])
    return [{
        'file': movie['file'],
        'label': label,
        'art': movie.get('art', {}) or {},
        'plot': movie.get('plot', ''),
    }]


def get_movieset_playables(setid):
    """Films in a movie set as playables, ordered by release year (series order)."""
    result = _rpc('VideoLibrary.GetMovieSetDetails', {
        'setid': setid,
        'movies': {'properties': ['title', 'file', 'art', 'plot', 'year'],
                   'sort': {'method': 'year', 'order': 'ascending'}},
    })
    movies = (result.get('setdetails', {}) or {}).get('movies', [])
    playables = []
    for movie in movies:
        if not movie.get('file'):
            continue
        label = movie.get('title', '')
        if movie.get('year'):
            label = '{0} ({1})'.format(label, movie['year'])
        playables.append({'file': movie['file'], 'label': label,
                          'art': movie.get('art', {}) or {}, 'plot': movie.get('plot', '')})
    return playables


def get_count_maps():
    """(tvshow_id -> episode count, movieset_id -> film count) in two RPC calls.
    TV counts include Season 0 specials, which playback skips."""
    shows = _rpc('VideoLibrary.GetTVShows', {'properties': ['episode']}).get('tvshows', [])
    show_counts = {s['tvshowid']: s.get('episode', 0) for s in shows}

    movies = _rpc('VideoLibrary.GetMovies', {'properties': ['setid']}).get('movies', [])
    set_counts = {}
    for movie in movies:
        setid = movie.get('setid') or 0
        if setid:
            set_counts[setid] = set_counts.get(setid, 0) + 1

    return show_counts, set_counts


def get_art(item):
    """Artwork dict (poster/fanart/...) for one channel item, or {} if none.
    Folders and seasons have no library art (and no dbid), so they return {}."""
    if item['type'] == 'tvshow':
        result = _rpc('VideoLibrary.GetTVShowDetails',
                      {'tvshowid': item['dbid'], 'properties': ['art']})
        details = result.get('tvshowdetails', {})
    elif item['type'] == 'movieset':
        result = _rpc('VideoLibrary.GetMovieSetDetails',
                      {'setid': item['dbid'], 'properties': ['art']})
        details = result.get('setdetails', {})
    elif item['type'] == 'movie':
        result = _rpc('VideoLibrary.GetMovieDetails',
                      {'movieid': item['dbid'], 'properties': ['art']})
        details = result.get('moviedetails', {})
    else:
        return {}
    return details.get('art', {}) or {}
