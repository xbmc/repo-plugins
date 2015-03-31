import re

__author__ = 'bromix'

from resources.lib.kodion import simple_requests as requests


class Client():
    def __init__(self):
        pass

    def get_root_data(self):
        return self._perform_request()

    def get_all_videos(self, json_data):
        def _sort(x):
            return x.get('timestamp', 0)

        videos = []
        categories = self.get_categories_from_data(json_data)
        for category in categories:
            videos.extend(self.get_videos_from_data(json_data, category))
            pass

        videos = sorted(videos, key=_sort, reverse=True)
        return videos

    def get_categories_from_data(self, json_data):
        items = json_data.get('items', [])
        result = []
        for item in items:
            category = item.get('ressortTitle', '')
            if category:
                result.append(category)
                pass
            pass
        return result

    def get_videos_from_data(self, json_data, category):
        items = json_data.get('items', [])
        result = []
        for item in items:
            if item.get('ressortTitle', '') == category:
                return item.get('items', [])
            pass
        pass

    def get_related_from_data(self, json_data):
        return json_data.get('related', [])

    def get_url_data(self, url):
        headers = {'Host': 'www.focus.de'}
        return self._perform_request(url=url, headers=headers)

    def get_video_streams_from_data(self, json_data):
        def _sort(x):
            return x['q']

        content = json_data.get('content', [{}])[0]

        regex_list = [re.compile(r'\d+x(?P<resolution>\d+)'),
                      re.compile(r'MP4(1920|1280|768)(?P<resolution>1080|720|432)')]

        result = []
        url_fields = ['videoHDUrl', 'mp4Url', 'videoSDUrl', 'flvUrl']
        for url_field in url_fields:
            url = content.get(url_field, '')
            if url:
                resolution = 480
                for regex in regex_list:
                    re_match = regex.search(url)
                    if re_match:
                        resolution = int(re_match.group('resolution'))
                        break
                    pass

                result.append({'q': resolution, 'url': url})
                pass
            pass

        result = sorted(result, key=_sort, reverse=True)
        return result

    def _perform_request(self, url='http://json.focus.de/videos', headers=None):
        _headers = {'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.2; GT-I9505 Build/KOT49H)',
                    'Host': 'json.focus.de',
                    'Accept-Encoding': 'gzip'}
        if headers:
            _headers.update(headers)
            pass

        # url
        _url = url

        _params = {'cst': '8'}

        result = requests.get(_url, params=_params, headers=_headers, verify=False)
        return result.json()

    pass
