# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import xbmc
import fsutils
import logging
from collections import namedtuple


Source = namedtuple('Source', ['name', 'path'])


def jsonrpc(query):
    return json.loads(xbmc.executeJSONRPC(json.dumps(query, encoding='utf-8')))


def _unstack(paths):
    for path in paths:
        if path.startswith("stack://"):
            for part in path.split("stack://", 1)[1].split(" , "):
                yield part
        else:
            yield path


def get_movies():
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetMovies",
        "params": {"properties": ["file", "trailer"]},
        "id": 1
    }
    items = jsonrpc(query)['result'].get('movies', [])
    return list(_unstack((item['file'].encode('utf-8') for item in items)))


def get_tvshows():
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetTVShows",
        "params": {"properties": ["file"]},
        "id": 1
    }
    items = jsonrpc(query)['result'].get('tvshows', [])
    return [item['file'].encode('utf-8').rstrip('\\/') for item in items]


def get_episodes():
    query = {
        "jsonrpc": "2.0",
        "method": "VideoLibrary.GetEpisodes",
        "params": {"properties": ["file"]},
        "id": 1
    }
    items = jsonrpc(query)['result'].get('episodes', [])
    return list(_unstack((item['file'].encode('utf-8') for item in items)))


def get_sources():
    query = {
        "jsonrpc": "2.0",
        "method": "Files.GetSources",
        "params": {"media": "video"},
        "id": 1
    }
    response = jsonrpc(query)
    return [Source(item['label'].encode('utf-8'), item['file'].encode('utf-8').rstrip('\\/'))
            for item in response['result'].get('sources', [])]


def _identify_source_content():
    movie_content = get_movies()
    tv_content = get_tvshows() + get_episodes()

    movie_sources = []
    tv_sources = []

    for source in get_sources():
        sep = fsutils.separator(source.path)
        if any((path.startswith(source.path + sep) for path in movie_content)):
            movie_sources.append(source)
            logging.debug("source '%s' identified as movie source" % source.path)
        elif any((path.startswith(source.path + sep) for path in tv_content)):
            tv_sources.append(source)
            logging.debug("source '%s' identified as tv source" % source.path)
        else:
            logging.debug("source '%s' does not contain any known content. "
                          "assuming content not set." % source.path)

    return movie_sources, tv_sources


def get_movie_sources():
    return _identify_source_content()[0]


def get_tv_sources():
    return _identify_source_content()[1]
