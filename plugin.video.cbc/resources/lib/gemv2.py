"""Module for the V2 Gem API."""
import json
from datetime import datetime

import requests

from resources.lib.cbc import CBC
from resources.lib.utils import loadAuthorization, log


# api CONFIG IS AT https://services.radio-canada.ca/ott/catalog/v1/gem/settings?device=web
BROWSE_URI = 'https://services.radio-canada.ca/ott/catalog/v2/gem/browse?device=web'
FORMAT_BY_ID = 'https://services.radio-canada.ca/ott/catalog/v2/gem/{}?device=web'
SEARCH_BY_NAME = 'https://services.radio-canada.ca/ott/catalog/v1/gem/search'
SHOW_BY_ID = 'https://services.radio-canada.ca/ott/catalog/v2/gem/show/{}?device=web'


class GemV2:
    """V2 Gem API class."""

    @staticmethod
    def iso8601_to_local(dttm):
        """Convert an ISO 8601 timestamp (UTC or offset-aware) to local time string."""
        try:
            local_dt = datetime.fromisoformat(dttm.replace('Z', '+00:00')).astimezone()
            return local_dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError, AttributeError):
            return dttm

    @staticmethod
    def scrape_json(uri, headers=None, params=None):
        if headers is None:
            headers = {}
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
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
        # categories are "category/shows" and have a basic list result, sections, like "section/sports" contain a list of lists.
        # since we can't nest menus programatically in kodi, we end up having to refetch the with with the selected key. So, we
        # may have a path like "section/sports/2415872347", which indicates that we want the list in "section/sports" with key "2415872347".
        key = None
        fmt = FORMAT_BY_ID
        part = path.rpartition('/')

        # determine which format to use for fetching the data based on the path
        if path.startswith('category/') or path.startswith('section/') or path.startswith('show/'):
            fmt = FORMAT_BY_ID
        else:
            fmt = SHOW_BY_ID
            key = part[2] if not (part[2] == '' or part[2] == path) else None

        if '/' in part[0]:
            # if there is a first part and it has a slash, we may be dealing with a section, eg: section/sports/2415872347
            path = part[0]
            key = part[2]
        elif part[0] == '':
            # if there is a first part and it's not category or section, its a season, eg: 'curling-canada-vs-sweden-mixed-doubles-round-robin-29364/1'
            path = part[2]

        # if there is no first part we may be dealing with a show, eg: snowboard-pgs-mens-womens-final-31718
        url = fmt.format(path)
        jsObj = GemV2.scrape_json(url)
        if jsObj is None:
            log(f'Unable to get format for path {path} (got no response from {url})')
            return None
        if 'lineups' in jsObj:
            if 'results' not in jsObj['lineups']:
                log(f'Unable to find key lineups/results in response from {url}')
                return None
            results = jsObj['lineups']['results']
            if key is not None:
                # as described above, we have to search through the lineups to find the one with the right key, then return its items
                for r in results:
                    if 'key' in r and r['key'] == key:
                        if 'items' in r:
                            return r['items']
                        if 'callToActions' in r:
                            return [r['callToActions']['primary']]
                        log(f'Unable to find items or callToAction/primary/url for lineup with key {key} in response from {url}')
                log(f'Unable to find key {key} in lineups/results from {url}')

            return results
        elif 'content' in jsObj:
            content = jsObj['content'][0]
        else:
            log(f'Unable to find key content in response from {url}')
            return None
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
            # are we looking for a sepcifci key (eg: season number)
            if key is not None:
                for c in content['lineups']:
                    if 'seasonNumber' in c and str(c['seasonNumber']) == key:
                        return c['items']
            # if there is just one lineup item, use it rather than returning a list with one item
            if len(content['lineups']) == 1 and 'items' in content['lineups'][0] and len(content['lineups'][0]['items']) == 1:
                return content['lineups'][0]['items']

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
        title = item['label'] if 'label' in item else item['title']
        retval = {
            'label': title,
            'playable': 'idMedia' in item,
            'info_labels': {
                'tvshowtitle': title,
                'title': title,
            }
        }
        if 'description' in item:
            retval['info_labels']['plot'] = item['description']
            retval['info_labels']['plotoutline'] = item['description']
        if images:
            retval['art'] = {
                'thumb': images['background']['url'] if 'background' in images else None,
                'poster': images['card']['url'] if 'card' in images else None,
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
            if 'live' in meta and 'startDate' in meta['live']:
                dttm = GemV2.iso8601_to_local(meta['live']['startDate'])
                retval['label'] += f' [Live: {dttm}]'

        if 'idMedia' in item:
            # logic in https://services.radio-canada.ca/ott/catalog/v1/gem/settings?device=web
            if 'type' in item:
                match item['type'].lower():
                    case 'media':
                        retval['app_code'] = 'gem'
                    case 'quickturn':
                        retval['app_code'] = 'medianet'
                    case 'liveevent' | 'replay':
                        retval['app_code'] = 'medianetlive'
                    case _:
                        log(f'Unknown type {item["type"]} for item with idMedia {item["idMedia"]}, defaulting to app_code "gem"')
                        retval['app_code'] = 'gem'

                
        return retval

    @staticmethod
    def has_playable(items):
        for item in items:
            if 'idMedia' in item:
                return True
        return False

    @staticmethod
    def normalized_format_path(item, parent_path=None):
        if 'idMedia' in item:
            return item['idMedia']
        if 'type' in item:
            if item['type'].lower() == 'show':
                return f'{item["type"]}/{item["url"]}'.lower()
            if item['type'].lower() == 'live':
                return item['url']
        if 'callToAction' in item:
            # line-up
            return item['callToAction']['primary']['url']
        if 'lineupType' in item:
            return f'{parent_path}/{item["key"]}'
        if 'action' in item and item['action'].lower() == 'openurl':
            return item['url']
        if 'seasonNumber' in item:
            # its a season, we just refetch with 
            return f'{parent_path}/{item["seasonNumber"]}'
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