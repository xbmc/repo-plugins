__author__ = 'bromix'

from resources.lib.kodion import simple_requests as requests


class Client():
    def __init__(self):
        pass

    def get_videos(self):
        data = self._perform_v2_request(url='http://video.golem.de/feeds/golem.de_video.xml')
        return data.text

    def get_video_stream(self, video_id, url, quality='low'):
        download_url = 'http://video.golem.de/download/%s?q=%s&rd=%s&start=0&paused=0&action=init' % (
            video_id, quality, url)

        headers = {'Referer': url}
        data = self._perform_v2_request(download_url,
                                        headers=headers,
                                        allow_redirects=False)
        headers = data.headers
        return headers.get('location', '')

    def _perform_v2_request(self, url, method='GET', headers=None, post_data=None, params=None, allow_redirects=True):
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
        _headers = {'Host': 'video.golem.de',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36',
                    'DNT': '1',
                    'Referer': 'http://www.golem.de/',
                    'Accept-Encoding': 'gzip, deflate',
                    'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
        _headers.update(headers)

        # url
        _url = url

        result = None

        if method == 'GET':
            result = requests.get(_url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            pass
        elif method == 'POST':
            result = requests.post(_url, data=post_data, params=_params, headers=_headers, verify=False,
                                   allow_redirects=allow_redirects)
            pass
        elif method == 'PUT':
            result = requests.put(_url, data=post_data, params=_params, headers=_headers, verify=False,
                                  allow_redirects=allow_redirects)
            pass
        elif method == 'DELETE':
            result = requests.delete(_url, params=_params, headers=_headers, verify=False,
                                     allow_redirects=allow_redirects)
            pass

        if result is None:
            return {}

        return result

    pass