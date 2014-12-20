# import json
import json
import urllib
import urllib2

import requests
# Verify is disabled and to avoid warnings we disable the warnings. Behind a proxy request isn't working correctly all
# the time and if so can't validate the hosts correctly resulting in a exception and the addon won't work properly.
try:
    from requests.packages import urllib3

    urllib3.disable_warnings()
except:
    # do nothing
    pass

__author__ = 'bromix'


class Client(object):
    def __init__(self):
        pass

    def _perform_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True):
        # params
        if not params:
            params = {}
            pass
        if path != 'search':
            _params = {'d': 'android-tablet', 'l': 'de-DE', 'g': 'DE'}
            pass
        else:
            _params = {'d': 'android-phone'}
            pass
        _params.update(params)

        # headers
        if not headers:
            headers = {}
            pass
        _headers = {'Host': 'api.netzkino.de.simplecache.net',
                    'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.4; GT-I9100 Build/KTU84Q)',
                    'Connection': 'Keep-Alive',
                    'Accept-Encoding': 'gzip'}
        _headers.update(headers)

        # url
        _url = 'http://api.netzkino.de.simplecache.net/capi-2.0a/%s' % path.strip('/')

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
        return json_data.get('categories', {})

    def get_category_content(self, category_id):
        """
        Returns the content of the given category
        :param category_id:
        :return:
        """
        return self._perform_request(path='categories/%s' % str(category_id))
        pass

    def search(self, text):
        """
        Search the given text
        :param text:
        :return:
        """
        return self._perform_request(path='search', params={'q': text})

    def get_video_url(self, stream_id):
        """
        Returns the url for the given id
        :param stream_id:
        :return:
        """
        content = urllib2.urlopen('http://www.netzkino.de/adconf/android-new.php')
        json_data = json.load(content)
        streamer_url = json_data.get('streamer', 'http://netzkino_and-vh.akamaihd.net/i/')
        return streamer_url + urllib.quote(stream_id.encode('utf-8')) + '.mp4/master.m3u8'


    pass
