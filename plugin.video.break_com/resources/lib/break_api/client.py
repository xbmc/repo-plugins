__author__ = 'bromix'

import json
from resources.lib.kodion import simple_requests as requests


class Client(object):
    def __init__(self):
        self._page_size = 25
        pass

    def get_video_urls(self, video_id):
        def _sort(x):
            return x['height']

        streams = []
        json_data = self.get_video(video_id)
        data = json_data['data']
        hls_uri = data['hlsUri']
        if hls_uri:
            token = data['token']

            media_files = data['mediaFiles']
            for media_file in media_files:
                # someone switched the values
                height = int(media_file['height'])
                bit_rate = str(media_file['bitRate'])

                # url = '%s%s_kbps.mp4.m3u8?%s' % (hls_uri, bit_rate, token)
                streams.append({'height': height,
                                'url': media_file['uri']})
                pass

            streams = sorted(streams, key=_sort, reverse=True)
            return streams

        # try youtube
        youtube_video_id = data['thirdPartyUniqueId']
        return [{'height': 480,
                 'url': 'plugin://plugin.video.youtube/play/?video_id=' + youtube_video_id}]

    def get_video(self, video_id):
        headers = {'Content-Type': 'application/json'}
        params = {'siteName': 'Break',
                  'appName': 'Android Phones',
                  'siteId': '1'}
        json_data = {'id': int(video_id)}
        return self._perform_request(method='POST', path='/content/video/get', params=params, json=json_data,
                                     headers=headers)


    def get_feed(self, feed_id, page=1):
        api_request_json = {
            'requestedProperties': ["title", "description", "contentType", "contentSubType", "thumbnails", "viewCount",
                                    "mediaFiles", "contentPartnerName", "prerollAllowed"],
            'id': feed_id, 'pageSize': self._page_size, 'pageNumber': page}
        params = {'apiRequestJson': json.dumps(api_request_json)}
        return self._perform_request(path='/content/contentfeed/get', params=params)

    def get_home(self):
        api_request_json = {'id': 12}
        params = {'apiRequestJson': json.dumps(api_request_json)}
        return self._perform_request(path='/content/FeedQuery/GetFeedCollection', params=params)

    def search(self, query, page=None):
        if not page:
            page = 1
            pass

        # params
        params = {
            'format': 'xml',
            'safeSearch': 'true',
            'isMobile': 'true',
            'q': query,
            'pageSize': str(self._page_size),
            'page': str(page),
            'youtube': 'true'
        }

        # headers
        headers = {'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.0.1; GT-I9505 Build/LRX22C)',
                   'Connection': 'Keep-Alive',
                   'Accept-Encoding': 'gzip'}

        # url
        _url = 'http://www.break.com/content/find'

        result = requests.get(_url, params=params, headers=headers, verify=False)

        if result is None:
            return ''

        return result.text

    def _perform_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True, json=None):
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

        _headers = {'Host': 'api.breakmedia.com',
                    'Connection': 'Keep-Alive',
                    'Accept-Encoding': 'gzip',
                    'User-Agent': ''}
        _headers.update(headers)

        # url
        _url = 'http://api.breakmedia.com/%s' % path.strip('/')

        result = None
        if method == 'GET':
            result = requests.get(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
        elif method == 'POST':
            if post_data:
                result = requests.post(_url, data=post_data, params=_params, headers=_headers, verify=False,
                                       allow_redirects=allow_redirects)
                pass
            elif json:
                result = requests.post(_url, json=json, params=_params, headers=_headers, verify=False,
                                       allow_redirects=allow_redirects)
                pass

        if result is None:
            return {}

        headers = result.headers
        if 'content-type' in headers:
            content_type = headers['content-type']
            if content_type.lower().startswith('application/json'):
                return result.json()
            pass

        return result.text

    pass