__author__ = 'bromix'

import datetime
import re

# nightcrawler
from resources.lib import nightcrawler


class Client(nightcrawler.HttpClient):
    def __init__(self):
        nightcrawler.HttpClient.__init__(self)
        self._default_header = {'User-Agent': 'Dalvik/1.6.0 (Linux; U; Android 4.4.2; GT-I9505 Build/KOT49H)',
                                'Host': 'json.focus.de',
                                'Accept-Encoding': 'gzip'}
        pass

    def _request(self, url, method='GET', headers=None, post_data=None, params=None, allow_redirects=True):
        if not params:
            params = {}
            pass
        params['cst'] = '8'
        return super(Client, self)._request(url, method, headers, post_data, params, allow_redirects)

    def get_root_data(self):
        response = self._request('http://json.focus.de/videos')
        return response.json()

    def get_categories(self):
        json_data = self.get_root_data()
        items = json_data.get('items', [])
        result = []
        for item in items:
            category = item.get('ressortTitle', '')
            if category:
                result.append({'type': 'folder',
                               'title': nightcrawler.utils.strings.to_unicode(category)})
                pass
            pass
        return result

    def _make_video_item(self, json_data):
        item = {'type': 'video',
                'title': nightcrawler.utils.strings.to_unicode(json_data.get('overhead', json_data['headline'])),
                'url': json_data['url'],
                'duration': int(json_data['duration']),
                'images': {'thumbnail': json_data['image']['url_hdpi']},
                'plot': nightcrawler.utils.strings.to_unicode(json_data['text']),
                'published': str(datetime.datetime.fromtimestamp(json_data['timestamp']))}
        credit = json_data['credit'].replace('FOCUS Online', '').strip('/')
        credit = 'FOCUS Online/%s' % credit
        item['format'] = credit.strip('/')
        return item

    def _make_video_items(self, json_data):
        result = []
        items = json_data.get('items', [])
        for item in items:
            result.append(self._make_video_item(item))
            pass
        return result

    def get_videos_by_category(self, category):
        json_data = self.get_root_data()
        items = json_data.get('items', [])
        for item in items:
            if item.get('ressortTitle', '') == category:
                return self._make_video_items(item)
            pass
        return []

    def get_all_videos(self):
        def _sort(x):
            return x.get('published', 0)

        json_data = self.get_root_data()
        category_items = json_data.get('items', [])

        result = []
        for category_item in category_items:
            result.extend(self._make_video_items(category_item))
            pass

        result = sorted(result, key=_sort, reverse=True)
        return result

    def get_related_videos(self, url):
        json_data = self.get_url_data(url)
        fake_data = {'items': json_data.get('related', [])}
        return self._make_video_items(fake_data)

    def get_url_data(self, url):
        headers = {'Host': 'www.focus.de'}
        response = self._request(url, headers=headers)
        return response.json()

    def get_video_streams(self, url):
        collected_urls = []
        json_data = self.get_url_data(url)
        content = json_data.get('content', [{}])[0]

        regex_list = [re.compile(r'\d+x(?P<resolution>\d+)'),
                      re.compile(r'MP4(1920|1280|768)(?P<resolution>1080|720|432)')]

        result = []
        url_fields = ['videoHDUrl', 'mp4Url', 'videoSDUrl', 'flvUrl']
        for url_field in url_fields:
            url = content.get(url_field, '')
            if not url:
                continue

            if url in collected_urls:
                continue

            collected_urls.append(url)

            resolution = 480
            for regex in regex_list:
                re_match = regex.search(url)
                if re_match:
                    resolution = int(re_match.group('resolution'))
                    break
                pass

            if resolution < 480:
                resolution = 480
                pass

            result.append({'title': '%dp' % resolution,
                           'sort': [resolution],
                           'video': {'height': resolution},
                           'uri': url})
            pass
        return result

    pass
