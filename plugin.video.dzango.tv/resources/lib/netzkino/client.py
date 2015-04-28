__author__ = 'bromix'

import urllib
from resources.lib.kodion import simple_requests as requests


class Client(object):
    CONFIG_NETZKINO_DE = {
        'url': 'http://api.netzkino.de.simplecache.net/capi-2.0a/%s',
        'parent': 0,
        'category_image_url': 'http://dyn.netzkino.de/wp-content/themes/netzkino/imgs/categories/%s.png',
        'streaming_url': 'http://netzkino_and-vh.akamaihd.net/i/%s.mp4/master.m3u8',
        'new': {
            'title': 'Neu bei Netzkino',
            'id': 81
        },
        'header': {
            'Origin': 'http://www.netzkino.de',
            'Referer': 'http://www.netzkino.de/'
        }
    }

    CONFIG_DZANGO_DE = {
        'url': 'http://api.amogo.de.simplecache.net/capi-2.0a/%s',
        'parent': 271,
        'category_image_url': 'http://pmd.love-bilder.loveisawonder.com/bilder/dzango-categories/%s.png',
        'streaming_url': 'http://pmd.dzango-seite.dzango.de/%s.mp4',
        'new': {
            'title': 'Neu bei DZANGO',
            'id': 531
        },
        'header': {
            'Origin': 'http://www.dzango.de',
            'Referer': 'http://www.dzango.de/'
        },
        'param': {
            'p': 'dzango'
        }
    }

    CONFIG_DZANGO_TV = {
        'url': 'http://hapi.dzango.tv/capi-2.0a/%s',
        'parent': 271,
        'category_image_url': '',
        'streaming_url': 'http://netzkino_and-vh.akamaihd.net/i/%s.mp4/master.m3u8',
        'new': {
            'title': 'Neu bei DZANGO',
            'id': 311
        },
        'header': {
            'Origin': 'http://www.dzango.tv',
            'Referer': 'http://www.dzango.tv/#!'
        }
    }

    def __init__(self, config):
        self._config = config
        pass

    def get_config(self):
        return self._config

    def _perform_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True):
        # params
        if not params:
            params = {}
            pass
        _params = {
            'd': 'wwww',
            'l': 'de-DE'
        }
        _params.update(self._config.get('param', {}))
        _params.update(params)

        # headers
        if not headers:
            headers = {}
            pass
        _headers = {'Connection': 'keep-alive',
                    'Pragma': 'no-cache',
                    'Cache-Control': 'no-cache',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36',
                    'DNT': '1',
                    'Accept-Encoding': 'gzip',
                    'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
        _headers.update(self._config['header'])
        _headers.update(headers)

        # url
        _url = self._config['url'] % path.strip('/')

        result = None
        if method == 'GET':
            result = requests.get(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            pass

        if result is None:
            return {}

        return result.json()

    def get_home(self):
        """
        Main entry point to get data of netzkino.de
        :return:
        """
        return self._perform_request(path='index.json')

    def get_categories(self):
        """
        Returns directly the 'categories'
        :return:
        """
        json_data = self.get_home()
        categories = json_data.get('categories', [])
        filtered_categories = []
        for category in categories:
            if category['parent'] == self._config['parent']:
                filtered_categories.append(category)
                pass
            pass
        return filtered_categories

    def get_category_content(self, category_id):
        """
        Returns the content of the given category
        :param category_id:
        :return:
        """
        return self._perform_request(path='categories/%s' % str(category_id))

    def search(self, text):
        """
        Search the given text
        :param text:
        :return:
        """
        return self._perform_request(path='search', params={'q': text})

    def get_video_url_by_slug(self, slug):
        result = {}
        json_data = self._perform_request(path='movies/%s.json' % str(slug))
        custom_fields = json_data['custom_fields']
        youtube = custom_fields.get('Youtube', [''])[0]
        if youtube:
            result['youtube'] = 'plugin://plugin.video.youtube/play/?video_id=%s' % youtube
            pass
        streaming = custom_fields.get('Streaming', [''])[0]
        if streaming:
            streamer_url = self._config['streaming_url']
            result['streaming'] = streamer_url % urllib.quote(streaming.encode('utf-8'))
            pass
        return result

    def get_video_url(self, stream_id):
        """
        Returns the url for the given id
        :param stream_id:
        :return:
        """
        content = requests.get('http://www.netzkino.de/adconf/android-new.php')
        json_data = content.json()
        streamer_url = json_data.get('streamer', 'http://netzkino_and-vh.akamaihd.net/i/')
        return streamer_url + urllib.quote(stream_id.encode('utf-8')) + '.mp4/master.m3u8'

    pass
