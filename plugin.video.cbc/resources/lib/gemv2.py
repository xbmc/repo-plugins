"""Module for the V2 Gem API."""
import json

import requests

from resources.lib.cbc import CBC
from resources.lib.utils import loadAuthorization

LAYOUT_MAP = {
    'featured': 'https://services.radio-canada.ca/ott/cbc-api/v2/home',
    'shows': 'https://services.radio-canada.ca/ott/cbc-api/v2/hubs/shows',
    'documentaries': 'https://services.radio-canada.ca/ott/cbc-api/v2/hubs/documentaries',
    'kids': 'https://services.radio-canada.ca/ott/cbc-api/v2/hubs/kids'
}
SHOW_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/shows/{}'
CATEGORY_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/categories/{}'
ASSET_BY_ID = 'https://services.radio-canada.ca/ott/cbc-api/v2/assets/{}'
SEARCH_BY_NAME = 'https://services.radio-canada.ca/ott/cbc-api/v2/search'

class GemV2:
    """V2 Gem API class."""

    @staticmethod
    def get_layout(name):
        """Get a Gem V2 layout by name."""
        url = LAYOUT_MAP[name]
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_show_layout_by_id(show_id):
        """Get a Gem V2 show layout by ID."""
        url = SHOW_BY_ID.format(show_id)
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_asset_by_id(asset_id):
        url = ASSET_BY_ID.format(asset_id)
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_episode(url):
        """Get a Gem V2 episode by URL."""
        auth = loadAuthorization()

        # if we have no authorization, return none to for the UI to authorize
        if auth is None:
            return None

        headers = {}
        if 'token' in auth:
            headers['Authorization'] = 'Bearer {}'.format(auth['token'])

        if 'claims' in auth:
            headers['x-claims-token'] = auth['claims']

        resp = requests.get(url, headers=headers)
        return json.loads(resp.content)

    @staticmethod
    def get_category(category_id):
        """Get a Gem V2 category by ID."""
        url = CATEGORY_BY_ID.format(category_id)
        resp = CBC.get_session().get(url)
        return json.loads(resp.content)

    @staticmethod
    def get_labels(show, episode):
        """Get labels for a show."""
        labels = {
            'studio': 'Canadian Broadcasting Corporation',
            'country': 'Canada',
            'tvshowtitle': show['title'],
            'title': episode['title'],
            'plot': episode['description'],
            'plotoutline': episode['description'],
            'season': episode['season'],
        }
        if 'episode' in episode:
            labels['episode'] = episode['episode']
        return labels

    @staticmethod
    def search_by_term(term):
        params = {'term': term}
        resp = CBC.get_session().get(SEARCH_BY_NAME, params=params)
        return json.loads(resp.content)