import hashlib
import time

__author__ = 'bromix'


import requests


class Client(object):
    PACKAGE_ID = 'com.ninegag.android.tv'
    DEVICE_ID = '0170c4d7-6653-46e9-9d89-4b6d0ade20c1'
    DEVICE_TYPE = 'Android'

    def __init__(self, access_token=''):
        self._access_token = access_token
        self._items_per_page = 20
        pass

    def get_posts(self, list_key, next_reference_key=''):
        _key = '%s:%d' % (list_key, self._items_per_page)
        if next_reference_key:
            _key += ':%s' % next_reference_key
            pass
        params = {'ref_keys': _key}
        return self._perform_request(path='list/posts', params=params)

    def get_available(self):
        return self._perform_request(path='list/available')

    def authenticate(self):
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        post_data = 'method=guest&package_id=%s' % self.PACKAGE_ID
        json_data = self._perform_request(method='POST', headers=headers, post_data=post_data, path='account/authenticate')
        token = json_data['data']['token']
        access_token = token['access_token']
        expires = int(token['expiry_ts'])
        return access_token, expires

    def calculate_request_signature(self, time_stamp=None):
        if time_stamp is None:
            time_stamp = int(time.time()*1000)
            pass

        request_signature_string = 'SIGNATURE_'+str(time_stamp)+'_'+self.PACKAGE_ID+'_'+self.DEVICE_ID
        return hashlib.sha1(request_signature_string).hexdigest()

    def _perform_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True):
        # params
        if not params:
            params = {}
            pass
        _params = {}
        _params.update(params)

        # headers
        if not headers:
            headers = {}
            pass

        time_stamp = int(time.time()*1000)
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

        _headers.update(headers)

        # url
        _url = 'http://api.9gag.tv/v1/%s' % path.strip('/')

        result = None
        if method == 'GET':
            result = requests.get(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
        elif method == 'POST':
            result = requests.post(_url, data=post_data, params=_params, headers=_headers, verify=False,
                                   allow_redirects=allow_redirects)

        if result is None:
            return {}

        return result.json()

    pass
