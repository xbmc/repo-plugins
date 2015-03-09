__author__ = 'bromix'

from resources.lib.kodion import simple_requests as requests

class Client():
    def __init__(self):
        pass

    def get_root_data(self):
        return self._perform_request()

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
        content = json_data.get('content', [{}])[0]

        result = [{'q': 480, 'url': content['videoSDUrl']},
                  {'q': 720, 'url': content['mp4Url']}]
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
