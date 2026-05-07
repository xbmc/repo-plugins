#!/usr/bin/python
# coding: utf-8

########################

import json
import sys
import requests

from resources.lib.helper import *

########################

def get_local_media(force=False):
    local_media = get_cache('local_db')

    if not local_media or force:
        local_media = {}
        local_media['shows'] = query_local_media('tvshow',
                                                get='VideoLibrary.GetTVShows',
                                                properties=['title', 'originaltitle', 'year', 'playcount', 'episode', 'watchedepisodes', 'uniqueid', 'art']
                                                )
        local_media['movies'] = query_local_media('movie',
                                                get='VideoLibrary.GetMovies',
                                                properties=['title', 'originaltitle', 'year', 'uniqueid', 'playcount', 'file', 'art']
                                                )

        if local_media:
            write_cache('local_db', local_media, 24)

    return local_media


def query_local_media(dbtype,get,properties):
    items = json_call(get,properties,sort={'order': 'descending', 'method': 'year'})

    try:
        items = items['result']['%ss' % dbtype]
    except Exception:
        return

    local_items = []
    for item in items:
        local_items.append({'title': item.get('title', ''),
                            'originaltitle': item.get('originaltitle', ''),
                            'imdbnumber': item.get('uniqueid', {}).get('imdb', ''),
                            'tmdbid': item.get('uniqueid', {}).get('tmdb', ''),
                            'tvdbid': item.get('uniqueid', {}).get('tvdb', ''),
                            'year': item.get('year', ''),
                            'dbid': item.get('%sid' % dbtype, ''),
                            'playcount': item.get('playcount', ''),
                            'episodes': item.get('episode', ''),
                            'watchedepisodes': item.get('watchedepisodes', ''),
                            'file': item.get('file', ''),
                            'art': item.get('art', {})}
                            )

    return local_items