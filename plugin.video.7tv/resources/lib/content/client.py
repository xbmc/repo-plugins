import hashlib
import json
import re
from resources.lib import nightcrawler


class Client(nightcrawler.HttpClient):
    CHANNEL_ID_LIST = ['pro7', 'sat1', 'kabel1', 'sixx', 'sat1gold', 'prosiebenmaxx']
    CHANNEL_IDS_STRING = '|'.join(CHANNEL_ID_LIST)
    CHANNEL_DATA = {'pro7': {'name': u'ProSieben'},
                    'sat1': {'name': u'SAT.1'},
                    'kabel1': {'name': u'kabel eins'},
                    'sixx': {'name': u'sixx'},
                    'sat1gold': {'name': u'SAT.1 Gold'},
                    'prosiebenmaxx': {'name': u'ProSieben MAXX'}}

    REGEX_VIDEO = re.compile(
        r'/mega-app/v2/(?P<channel_id>%s)/(tablet|phone)/(?P<type>video)/(?P<video_id>\d+)' % CHANNEL_IDS_STRING)
    REGEX_FORMAT = re.compile(
        r'/mega-app/v2/(?P<channel_id>(%s))/(tablet|phone)/format/show/(%s):(?P<format_id>\d+)' % (
            CHANNEL_IDS_STRING, CHANNEL_IDS_STRING))

    def __init__(self):
        nightcrawler.HttpClient.__init__(self, default_header={'User-Agent': '7TV-App-Android-v1.7.0.8-fb8e88f',
                                                               'Accept-Language': 'en_US',
                                                               'Accept-Encoding': 'gzip'})

        self._device = 'tablet'  # 'phone'
        pass

    def _request(self, url, method='GET', headers=None, post_data=None, params=None, allow_redirects=True):
        if not params:
            params = {}
            pass

        if not headers:
            headers = {}
            pass

        response = super(Client, self)._request(url, method, self._default_header, post_data, params, allow_redirects)

        if method != 'HEAD':
            return json.loads(response.text)

        return response

    def _screen_objects_to_result(self, json_data, result):
        for json_item in json_data:
            title = nightcrawler.utils.strings.to_unicode(json_item.get('title', json_item.get('video_title', '')))
            screen_objects = json_item.get('screen_objects', [])

            if title and screen_objects and len(screen_objects) > 0:
                result[title] = {}
                self._screen_objects_to_result(screen_objects, result[title])

                # remove empty lists
                if len(result[title]['items']) == 0:
                    del result[title]
                    pass
                pass
            elif screen_objects:
                self._screen_objects_to_result(json_item.get('screen_objects', []), result)
                pass
            elif title:
                if 'items' not in result:
                    result['items'] = []
                    pass

                item = {'title': title}

                format_title = nightcrawler.utils.strings.to_unicode(json_item.get('format_title', ''))
                if format_title is None:
                    format_title = ''
                    pass

                subtitle = nightcrawler.utils.strings.to_unicode(json_item.get('subtitle', ''))
                if subtitle is None:
                    subtitle = ''
                    pass

                # test for video
                video_match = self.REGEX_VIDEO.match(json_item.get('link', ''))
                if video_match:
                    item.update({'type': 'video',
                                 'channel': video_match.group('channel_id'),
                                 'id': json_item['id'],
                                 'images': {'thumbnail': json_item.get('image_url', '')}})

                    # duration
                    duration = int(json_item.get('duration', 0))
                    if duration > 0:
                        item['duration'] = duration
                        pass

                    # published
                    published = json_item.get('start', '')
                    if published:
                        published = nightcrawler.utils.datetime.parse(published)
                        item['published'] = str(published)
                        pass

                    # format based on subtitle or format_title
                    if subtitle:
                        item['format'] = item['title']
                        item['title'] = subtitle
                        pass
                    elif format_title:
                        item['format'] = format_title
                        pass

                    # try to match season and episode
                    season_match = re.search(r'Staffel (?P<season>\d+)', item['title'])
                    if season_match:
                        item['season'] = int(season_match.group('season'))
                        pass
                    episode_match = re.search(r'(Episode|Folge) (?P<episode>\d+)', item['title'])
                    if episode_match:
                        item['episode'] = int(episode_match.group('episode'))
                        pass

                    result['items'].append(item)
                    continue
                    pass

                # test for format
                format_match = self.REGEX_FORMAT.match(json_item.get('link', ''))
                if format_match:
                    item.update({'type': 'format',
                                 'channel': format_match.group('channel_id'),
                                 'id': json_item['id'],
                                 'images': {'thumbnail': json_item.get('image_url', '')}})
                    result['items'].append(item)
                    continue
                    pass
                pass
            pass
        pass

    def _objects_to_result(self, json_data):
        objects = json_data.get('objects', [])
        result = {}
        self._screen_objects_to_result(objects, result)
        return result

    def _screen_to_result(self, json_data, result):
        screen = json_data.get('screen', {})
        self._screen_objects_to_result(screen.get('screen_objects', []), result)
        return result

    def get_homepage(self, channel_id):
        url = "http://contentapi.sim-technik.de/mega-app/v2/%s/%s/homepage" % (channel_id, self._device)
        json_data = self._request(url)

        result = {}
        return self._screen_to_result(json_data, result)

    def get_formats(self, channel_id):
        url = 'http://contentapi.sim-technik.de/mega-app/v2/%s/%s/format' % (channel_id, self._device)
        json_data = self._request(url)
        result = {}
        return self._screen_to_result(json_data, result)

    def get_format_content(self, channel_id, format_id):
        result = {}

        # http://contentapi.sim-technik.de/mega-app/v2/pro7/phone/format/show/pro7:789
        url = 'http://contentapi.sim-technik.de/mega-app/v2/%s/%s/format/show/%s' % (
            channel_id,
            self._device,
            format_id)

        json_data = self._request(url)
        result = {}
        return self._screen_to_result(json_data, result)

    def get_format_videos(self, channel_id, format_id, clip_type='full', page=1, per_page=50):
        def _load_videos(_page):
            # http://contentapi.sim-technik.de/mega-app/v2/tablet/videos/format/pro7:505?clip_type=full&page=1&per_page=50
            url = 'http://contentapi.sim-technik.de/mega-app/v2/%s/videos/format/%s' % (self._device, format_id)
            params = {'clip_type': clip_type,
                      'page': str(_page),
                      'per_page': str(per_page)}
            return self._request(url, params=params)

        current_page_result = _load_videos(page)
        result = self._objects_to_result(current_page_result)

        # test next page
        next_page_result = _load_videos(page + 1)
        next_page_result = self._objects_to_result(next_page_result)
        if len(next_page_result.get('items', [])) > 0:
            result['continue'] = True
            pass

        return result

    def search(self, query):
        result = {}

        # http://contentapi.sim-technik.de/mega-app/v2/phone/search?query=halligalli
        url = 'http://contentapi.sim-technik.de/mega-app/v2/tablet/search'
        json_data = self._request(url, params={'query': query})
        result = {}
        return self._screen_to_result(json_data, result)

    def get_new_videos(self, format_ids=None):
        if not format_ids:
            format_ids = []
            pass

        result = {}

        format_id_string = ','.join(format_ids)
        format_id_string = '[' + format_id_string + ']'
        url = 'http://contentapi.sim-technik.de/mega-app/v2/tablet/videos/favourites'
        json_data = self._request(url, params={'ids': format_id_string})

        # wrap the result into a 'screen' object so we can use common routines
        json_data = {'screen': json_data}
        result = {}
        return self._screen_to_result(json_data, result)

    def get_video_url(self, video_id):
        # first request the web url of the video
        url = 'http://contentapi.sim-technik.de/mega-app/v2/pro7/phone/video/%s' % str(video_id)
        data = self._request(url)
        video_link = nightcrawler.utils.strings.to_utf8(
            data.get('screen', {}).get('screen_objects', [{'video_link': ''}])[0].get('video_link', ''))

        url = 'https://vas.sim-technik.de/vas/live/v2/videos'
        params = {'access_token': 'seventv-app',
                  'client_location': video_link,
                  'client_name': '7tv-app',
                  'ids': str(video_id)}
        data = self._request(url, params=params)
        is_protected = False
        if len(data) > 0:
            is_protected = data[0].get('is_protected', False)
            pass

        url = 'http://vas.sim-technik.de/video/video.json'
        params = {'clipid': video_id,
                  'app': 'megapp',
                  'method': '6'}
        data = self._request(url, params=params)
        video_url = data['VideoURL']

        video_format_list = [{'id': 12, 'title': '1280x720@2.7mbps', 'height': 720, 'bitrate': 2700},
                             {'id': 11, 'title': '1280x720@2mbps', 'height': 720, 'bitrate': 2000},
                             {'id': 10, 'title': '960x540@1.7mbps', 'height': 540, 'bitrate': 1700},
                             {'id': 9, 'title': '960x540@1.4mbps', 'height': 540, 'bitrate': 1400},
                             {'id': 8, 'title': '768x432@1.8mbps', 'height': 432, 'bitrate': 1800},
                             {'id': 7, 'title': '768x432@1.5mbps', 'height': 432, 'bitrate': 1500},
                             {'id': 6, 'title': '640x360@1.1mbps', 'height': 360, 'bitrate': 1100},
                             {'id': 5, 'title': '640x360@0.6mbps', 'height': 360, 'bitrate': 600},
                             {'id': 4, 'title': '480x270@0.4mbps', 'height': 270, 'bitrate': 400},
                             {'id': 3, 'title': '416x258@0.2mbps', 'height': 258, 'bitrate': 200}]

        result = []
        last_video_format = {}
        for video_format in video_format_list:
            # optimization - skip the lower bit rates of the same resolution group
            if last_video_format and last_video_format['height'] == video_format['height']:
                continue
                pass

            url = re.sub(r'(.+?)(tp\d+.mp4)(.+)', r'\1tp%02d.mp4\3' % video_format['id'], video_url)
            response = self._request(url, method='HEAD')
            if response.status_code == 200:
                video_stream = {'title': video_format['title'],
                                'sort': [video_format['height'], video_format['bitrate']],
                                'video': {'height': video_format['height']},
                                'uri': url}

                # mark the stream protected
                if is_protected:
                    video_stream['is_protected'] = True
                    pass

                result.append(video_stream)

                # skip all other streans if the video is protected
                if is_protected:
                    break
                    pass

                last_video_format = video_format
                pass
            pass

        return result
