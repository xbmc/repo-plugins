import re

__author__ = 'bromix'

from resources.lib.kodion import simple_requests as requests


class Client():
    API_URL = 'https://api.redbull.tv/v1/'

    def __init__(self, limit=None):
        self._limit = limit
        pass

    def get_streams(self, video_id, bandwidth=None):
        streams = []

        path = 'videos/%s' % str(video_id)
        json_data = self._perform_v1_request(path=path)
        #uri = json_data.get('videos', {}).get('live', {}).get('uri', '')
        stream = json_data.get('stream', {})
        if stream is None:
            stream = {}
            pass
        if stream.get('status', '') in ['pre-event', 'soon']:
            format = {'width': 0,
                      'height': 0,
                      'bandwidth': 0}
            video_stream = {'url': '',
                            'format': format,
                            'upcoming': True}
            streams.append(video_stream)
            return streams

        videos = json_data.get('videos', {})
        uri = ''
        for key in ['master', 'live']:
            if key in videos:
                uri = videos.get(key, {}).get('uri', '')
                if uri:
                    break
                pass
            pass
        if uri:
            headers = {'Connection': 'keep-alive',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.118 Safari/537.36',
                       'DNT': '1',
                       'Referer': 'https://api.redbull.tv/v1/videos/%s' % str(video_id),
                       'Accept-Encoding': 'gzip',
                       'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
            manifest_result = requests.get(uri, headers=headers, verify=False, allow_redirects=True)
            lines = manifest_result.text.splitlines()
            re_bandwidth = re.compile(r'BANDWIDTH=(?P<bandwidth>\d+)')
            re_resolution = re.compile(r'RESOLUTION=(?P<width>\d+)x(?P<height>\d+)')
            for i in range(len(lines)):
                re_match_bandwidth = re.search(re_bandwidth, lines[i])
                re_match_resolution = re.search(re_resolution, lines[i])
                if re_match_bandwidth and re_match_resolution:
                    line = lines[i + 1]
                    format = {'width': int(re_match_resolution.group('width')),
                              'height': int(re_match_resolution.group('height')),
                              'bandwidth': int(re_match_bandwidth.group('bandwidth'))}
                    video_stream = {'url': line,
                                    'format': format}
                    streams.append(video_stream)
                    pass
                pass
            pass

        def _sort(x):
            return x['format']['height'],x['format']['bandwidth']

        streams = sorted(streams, key=_sort, reverse=True)

        # filter the bandwidth
        if bandwidth is not None:
            bandwidth_dict = {}
            for stream in streams:
                quality = stream['format']['height']
                data = bandwidth_dict.get(quality, [])
                data.append(stream)
                bandwidth_dict[quality] = data
                pass

            streams = []
            for quality in bandwidth_dict:
                quality_list = bandwidth_dict[quality]
                index = bandwidth
                if index > len(quality_list)-1:
                    index = len(quality_list)-1
                    pass

                streams.append(quality_list[index])
                pass
            pass

        streams = sorted(streams, key=_sort, reverse=True)
        return streams

    def url_to_path(self, url):
        url = url.split('?')[0]
        if url.startswith(self.API_URL):
            url = url.replace(self.API_URL, '')
            pass
        if not url.endswith('/'):
            url += '/'
            pass
        return url

    def search(self, query, offset=None, limit=None):
        params = {'search': query}
        if offset or offset is not None:
            params['offset'] = str(offset)
            pass
        if self._limit or self._limit is not None:
            params['limit'] = str(self._limit)
            pass
        if limit or limit is not None:
            params['limit'] = str(limit)
            pass
        return self._perform_v1_request(path='search', params=params)

    def do_raw(self, path, offset=None, limit=None):
        params = {}
        if offset or offset is not None:
            params['offset'] = str(offset)
            pass
        if self._limit or self._limit is not None:
            params['limit'] = str(self._limit)
            pass
        if limit or limit is not None:
            params['limit'] = str(limit)
            pass
        return self._perform_v1_request(path=path, params=params)

    def get_channels(self):
        return self._perform_v1_request(path='channels')

    def _perform_v1_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
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
        _headers = {'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 5.0.1; GT-I9505 Build/LRX22C)',
                    'Host': 'api.redbull.tv',
                    'Connection': 'Keep-Alive',
                    'Accept-Encoding': 'gzip'}
        _headers.update(headers)

        # url
        _url = 'https://api.redbull.tv/v1/%s' % path.strip('/')

        result = None

        if method == 'GET':
            result = requests.get(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            pass
        elif method == 'POST':
            _headers['content-type'] = 'application/json'
            result = requests.post(_url, json=post_data, params=_params, headers=_headers, verify=False,
                                   allow_redirects=allow_redirects)
            pass
        elif method == 'PUT':
            _headers['content-type'] = 'application/json'
            result = requests.put(_url, json=post_data, params=_params, headers=_headers, verify=False,
                                  allow_redirects=allow_redirects)
            pass
        elif method == 'DELETE':
            result = requests.delete(_url, params=_params, headers=_headers, verify=False,
                                     allow_redirects=allow_redirects)
            pass

        if result is None:
            return {}

        if result.headers.get('content-type', '').startswith('application/json'):
            return result.json()
        pass

    pass