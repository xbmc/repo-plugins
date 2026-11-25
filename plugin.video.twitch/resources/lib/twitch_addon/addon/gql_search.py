# -*- coding: utf-8 -*-
"""
    Website-grade search via Twitch's GQL backend (gql.twitch.tv) — the same
    Elasticsearch-backed search the Twitch website uses. Gives proper fuzzy
    matching + relevance ranking (and live ordering) that the Helix
    search/channels endpoint does not. Public/anonymous (web client id, no OAuth).

    Results are adapted to the same shape the Helix search returns
    ({'data': [...]} with the addon's Keys) so the existing converters and
    routes keep working unchanged. Returns None on any failure so the caller
    can fall back to the Helix search.

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""
import requests

from .constants import Keys
from .common import log_utils

GQL_URL = 'https://gql.twitch.tv/gql'
WEB_CLIENT_ID = 'kimne78kx3ncx6brgo4mv6wki5h1ko'  # Twitch public web client (same as the website)
TIMEOUT = 15

_CHANNEL_QUERY = (
    'query Search($q: String!) {'
    '  searchFor(userQuery: $q, platform: "web", target: {index: CHANNEL}) {'
    '    channels { edges { item { ... on User {'
    '      id login displayName'
    '      broadcastSettings { language title }'
    '      profileImageURL(width: 300)'
    '      stream { id viewersCount previewImageURL game { id name displayName } }'
    '    } } } }'
    '  }'
    '}'
)

_GAME_QUERY = (
    'query Search($q: String!) {'
    '  searchFor(userQuery: $q, platform: "web", target: {index: GAME}) {'
    '    games { edges { item { ... on Game { id name displayName boxArtURL(width: 285, height: 380) } } } }'
    '  }'
    '}'
)


def _post(query, search_query):
    body = [{'operationName': 'Search', 'query': query, 'variables': {'q': search_query}}]
    r = requests.post(GQL_URL, json=body, headers={'Client-ID': WEB_CLIENT_ID}, timeout=TIMEOUT)
    data = r.json()
    if isinstance(data, list):
        data = data[0] if data else {}
    if data.get('errors'):
        log_utils.log('gql_search: GQL errors |%s|' % data['errors'], log_utils.LOGWARNING)
        return None
    return (data.get('data') or {}).get('searchFor') or {}


def _channel_item(item):
    stream = item.get('stream') or {}
    game = stream.get('game') or {}
    profile = item.get('profileImageURL', '')
    return {
        Keys.ID: item.get('id'),
        Keys.BROADCASTER_LOGIN: item.get('login'),
        Keys.DISPLAY_NAME: item.get('displayName'),
        Keys.BROADCASTER_LANGUAGE: (item.get('broadcastSettings') or {}).get('language', ''),
        Keys.TITLE: (item.get('broadcastSettings') or {}).get('title', ''),
        Keys.OFFLINE_IMAGE_URL: profile,
        Keys.THUMBNAIL_URL: stream.get('previewImageURL') or profile,
        Keys.VIEWER_COUNT: stream.get('viewersCount', 0) if item.get('stream') else 0,
        Keys.GAME_NAME: game.get('name', ''),
        Keys.GAME_ID: game.get('id', ''),
    }


def search(search_query, kind):
    """kind: 'streams' (live only) | 'channels' (all) | 'games'.
    Returns {'data': [...]} (Helix-shaped) on success, or None on failure (-> caller falls back to Helix)."""
    try:
        if kind == 'games':
            sf = _post(_GAME_QUERY, search_query)
            if sf is None:
                return None
            edges = ((sf.get('games') or {}).get('edges')) or []
            items = [{Keys.ID: e['item'].get('id'),
                      Keys.NAME: e['item'].get('name') or e['item'].get('displayName'),
                      Keys.BOX_ART_URL: e['item'].get('boxArtURL', '')}
                     for e in edges if e.get('item')]
            return {Keys.DATA: items}

        sf = _post(_CHANNEL_QUERY, search_query)
        if sf is None:
            return None
        edges = ((sf.get('channels') or {}).get('edges')) or []
        items = []
        for e in edges:
            item = e.get('item')
            if not item:
                continue
            if kind == 'streams' and not item.get('stream'):
                continue  # streams branch == live channels only
            items.append(_channel_item(item))
        return {Keys.DATA: items}
    except Exception as e:
        log_utils.log('gql_search.search error |%s|' % e, log_utils.LOGWARNING)
        return None
