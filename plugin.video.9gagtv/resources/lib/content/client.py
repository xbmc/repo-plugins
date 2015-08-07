import datetime

__author__ = 'bromix'

import hashlib
import time
from resources.lib import nightcrawler


class Client(nightcrawler.HttpClient):
    PACKAGE_ID = 'com.ninegag.android.tv'
    DEVICE_ID = '0170c4d7-6653-46e9-9d89-4b6d0ade20c1'
    DEVICE_TYPE = 'Android'

    def __init__(self, access_token=''):
        nightcrawler.HttpClient.__init__(self)
        self._access_token = access_token
        self._items_per_page = 20
        pass

    def get_posts(self, list_key, next_reference_key=''):
        def _get_image(thumbnails):
            # qualities = ['thumbnail_840w', 'thumbnail_480w', 'thumbnail_360w', 'thumbnail_240', 'thumbnail_120w']
            qualities = ['thumbnail_480w', 'thumbnail_360w', 'thumbnail_240', 'thumbnail_120w']
            for quality in qualities:
                if quality in thumbnails:
                    return thumbnails[quality]
                pass

            return ''

        _key = '%s:%d' % (list_key, self._items_per_page)
        if next_reference_key:
            _key += ':%s' % next_reference_key
            pass
        params = {'ref_keys': _key}
        json_data = self._request('list/posts', params=params)
        json_data = json_data.get('data', [{}])[0]

        result = {'items': []}
        for item in json_data.get('posts', []):
            video_item = {'type': item['video']['type'],
                          'id': item['video']['external_id'],
                          'format': '9gag.tv',
                          'title': item['og_title'],
                          'plot': item.get('og_description', ''),
                          'published': str(datetime.datetime.fromtimestamp(int(item['created']))),
                          'duration': int(item['video']['duration']),
                          'images': {'thumbnail': _get_image(item.get('thumbnails', {}))}}

            result['items'].append(video_item)
            pass

        end_of_list = json_data.get('end_of_list', True)
        next_reference_key = json_data.get('next_reference_key', '')
        if not end_of_list and next_reference_key:
            result['continue'] = True
            result['next_reference_key'] = next_reference_key
            pass

        return result

    def get_available(self):
        json_data = self._request('list/available')

        result = []
        items = json_data.get('data', {}).get('lists', [])
        for item in items:
            result.append({'type': 'folder',
                           'title': item['name'],
                           'id': item['list_key']})
            pass
        return result

    def authenticate(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        post_data = 'method=guest&package_id=%s' % self.PACKAGE_ID
        json_data = self._request('account/authenticate', method='POST', headers=headers, post_data=post_data)
        token = json_data['data']['token']
        return {'access_token': token['access_token'],
                'expires_in': int(token['expiry_ts'])}

    def calculate_request_signature(self, time_stamp=None):
        if time_stamp is None:
            time_stamp = int(time.time() * 1000)
            pass

        request_signature_string = 'SIGNATURE_' + str(time_stamp) + '_' + self.PACKAGE_ID + '_' + self.DEVICE_ID
        return hashlib.sha1(request_signature_string).hexdigest()

    def _request(self, url, method='GET', headers=None, post_data=None, params=None, allow_redirects=True):
        if not params:
            params = {}
            pass

        if not headers:
            headers = {}
            pass

        time_stamp = int(time.time() * 1000)
        _headers = {'X-TIMESTAMP': str(time_stamp),
                    'X-PACKAGE-ID': self.PACKAGE_ID,
                    'X-DEVICE-UUID': self.DEVICE_ID,
                    'X-DEVICE-TYPE': self.DEVICE_TYPE,
                    'X-REQUEST-SIGNATURE': self.calculate_request_signature(time_stamp),
                    'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.4; GT-I9100 Build/KTU84Q)',
                    'Host': 'api.9gag.tv',
                    'Connection': 'Keep-Alive',
                    'Accept-Encoding': 'gzip'}
        if self._access_token:
            _headers['X-REQUEST-TOKEN'] = self._access_token
            pass

        _headers.update(headers)

        url = 'http://api.9gag.tv/v1/%s' % url.strip('/')

        response = super(Client, self)._request(url, method, _headers, post_data, params, allow_redirects)
        if response.headers.get('content-type', '').startswith('application/json'):
            return response.json()

        return response.text

    pass
