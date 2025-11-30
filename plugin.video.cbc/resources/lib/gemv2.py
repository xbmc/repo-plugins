"""Module for the V2 Gem API."""
import json

import requests

from resources.lib.cbc import CBC
from resources.lib.utils import loadAuthorization, log


# api CONFIG IS AT https://services.radio-canada.ca/ott/catalog/v1/gem/settings?device=web
BROWSE_URI = 'https://services.radio-canada.ca/ott/catalog/v2/gem/browse?device=web'
FORMAT_BY_ID = 'https://services.radio-canada.ca/ott/catalog/v2/gem/{}?device=web'
SEARCH_BY_NAME = 'https://services.radio-canada.ca/ott/catalog/v1/gem/search'


class GemV2:
    """V2 Gem API class."""

    @staticmethod
    def scrape_json(uri, headers=None, params=None):
        resp = CBC.get_session().get(uri, headers=headers, params=params)

        if resp.status_code != 200:
            log(f'HTTP {resp.status_code} from {uri}', True)
            return None
        
        try:
            jsObj = json.loads(resp.content)
        except:
            log(f'Unable to parse JSON from {uri} (status {resp.status_code})', True)
            return None
        return jsObj


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

        return GemV2.scrape_json(url, headers)


    @staticmethod
    def get_browse(type='formats'):
        """Get a Gem V2 API V2 browse format"""
        jsObj = GemV2.scrape_json(BROWSE_URI)
        if jsObj is not None and type in jsObj:
            return jsObj[type]
        log(f'Unable to find key "{type}" in response from {BROWSE_URI}')
        return None
    
    @staticmethod
    def get_format(path):
        """Get a Gem V2 API V2 browse format"""
        url = FORMAT_BY_ID.format(path)
        jsObj = GemV2.scrape_json(url)
        if jsObj is None or 'content' not in jsObj:
            log(f'Unable to find key content in response from {url}')
            return None
        content = jsObj['content'][0]
        if 'items' in content and 'results' in content['items']:
            return content['items']['results']
        
        if 'requestedType' in jsObj and jsObj['requestedType'].lower() == 'season':
            # Search for the right season:
            # - lineup url will be something like 'rosemary-barton-live/s02'
            # - path will be something like 'show/rosemary-barton-live/s02'
            for lineup in content['lineups']:
                if 'url' in lineup and lineup['url'] in path:
                    return lineup['items']
            return content['lineups'][0]['items']
        if 'lineups' in content:
            return content['lineups']

        log(f'Unable to find key content/[0]/items/results in response from {url}')
        return None
    
    @staticmethod
    def get_stream(id, app_code):
        url = f'https://services.radio-canada.ca/media/meta/v1/index.ashx?appCode={app_code}&idMedia={id}&output=jsonObject'
        jsObj = GemV2.scrape_json(url)
        if jsObj['errorMessage'] is not None:
            log(f'Error fetching {url}: {jsObj["errorMessage"]}')
            return None
        
        drm = None
        for at in jsObj['availableTechs']:
            if at['name'] == 'dash':
                drm = at
            elif at['name'] == 'hls' and drm == None:
                # only use HLS if dash isn't available -- the new HLS cannot be played
                drm = at
        log(drm)
        tech = drm['name']
        manifest_versions = drm['manifestVersions']
        mv = manifest_versions[-1] if manifest_versions is not None else 1
        url = f'https://services.radio-canada.ca/media/validation/v2/?appCode={app_code}&connectionType=hd&deviceType=multiams&idMedia={id}&multibitrate=true&output=json&tech={tech}&manifestType=desktop&manifestVersion={mv}'
        retval = GemV2.get_episode(url)
        if retval is not None:
            retval['type'] = drm['name']
        return retval
    
    @staticmethod
    def get_stream_drm(stream):
        wv_url = None
        wv_tok = None
        for x in stream['params']:
            if x['name'] == 'widevineLicenseUrl':
                wv_url = x['value']
            if x['name'] == 'widevineAuthToken':
                wv_tok = x['value']
        return (wv_url, wv_tok)
    
    @staticmethod
    def normalized_format_item(item):
        """
        Given an object in the list returned by get_format, turn its useful
        bits into stuff we can display
        """
        images = item['images'] if 'images' in item else None
        retval = {
            'label': item['title'],
            'playable': 'idMedia' in item,
            'info_labels': {
                'tvshowtitle': item['title'],
                'title': item['title'],
            }
        }
        if 'description' in item:
            retval['info_labels']['plot'] = item['description']
            retval['info_labels']['plotoutline'] = item['description']
        if images:
            retval['art'] = {
                'thumb': images['background']['url'] if 'background' in images else None,
                'poster': images['card']['url'],
                'clearlogo': images['logo']['url'] if 'logo' in images else None,
            }
        if 'metadata' in item:
            meta = item['metadata']
            if 'country' in meta:
                retval['info_labels']['country'] = meta['country']
            if 'duration' in meta:
                retval['info_labels']['duration'] = meta['duration']
            if 'airDate' in meta:
                retval['info_labels']['aired'] = meta['airDate']
            if 'credits' in meta:
                retval['info_labels']['cast'] = meta['credits'][0]['peoples'].split(',')
        if 'idMedia' in item:
            retval['app_code'] = 'medianet' if item['mediaType'] == 'LiveToVod' else 'gem'
            None
        return retval

    @staticmethod
    def normalized_format_path(item):
        if 'idMedia' in item:
            return item['idMedia']
        if 'type' in item and item['type'].lower() == 'show':
            return f'{item["type"]}/{item["url"]}'
        return f'show/{item["url"]}'


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
        if 'duration' in episode:
            labels['duration'] = episode['duration']
        return labels


    @staticmethod
    def search_by_term(term):
        params = {
            'term': term,
            'device': 'web',
        }
        jsObj = GemV2.scrape_json(SEARCH_BY_NAME, params=params)
        if jsObj is None or 'result' not in jsObj:
            log(f'Search by term yields no result: {term}')
            return None
        return jsObj['result']