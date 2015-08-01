__author__ = 'bromix'

import json
from resources.lib import nightcrawler


class Client(nightcrawler.HttpClient):
    def __init__(self):
        nightcrawler.HttpClient.__init__(self)
        self._page_size = 25
        self._default_header = {'Host': 'api.breakmedia.com',
                                'Connection': 'Keep-Alive',
                                'Accept-Encoding': 'gzip',
                                'User-Agent': ''}
        pass

    def _feed_to_item(self, json_data):
        result = []

        data = json_data.get('data', {}).get('data', [])
        for item in data:
            video_item = {'title': item['title'],
                          'type': 'video',
                          'id': int(item['id']),
                          'format': 'Break'}

            image = item.get('thumbnails', [])
            if len(image) > 0:
                image = image[0].get('url', '')
                if image:
                    video_item['images'] = {'thumbnail': image}
                    pass
                pass

            result.append(video_item)
            pass

        return result

    def get_feed(self, feed_id, page=1):
        api_request_json = {
            'requestedProperties': ["title", "description", "contentType", "contentSubType", "thumbnails", "viewCount",
                                    "mediaFiles", "contentPartnerName", "prerollAllowed"],
            'id': feed_id, 'pageSize': self._page_size, 'pageNumber': page}
        params = {'apiRequestJson': json.dumps(api_request_json)}
        json_data = self._request('/content/contentfeed/get', params=params)
        return self._feed_to_item(json_data)

    def get_home(self):
        api_request_json = {'id': 12}
        params = {'apiRequestJson': json.dumps(api_request_json)}
        json_data = self._request('/content/FeedQuery/GetFeedCollection', params=params)

        result = []
        collection = json_data.get('data', {}).get('data', {}).get('collection', [])
        make_bold = True
        for item in collection:
            title = item['name']
            if title == u'Galleries':
                continue

            item_id = int(item['id'])
            if make_bold:
                title = '[B]%s[/B]' % title
                make_bold = False
                pass

            result.append({'title': title,
                           'type': 'folder',
                           'id': item_id})
            pass
        return result

    def get_video_streams(self, video_id):
        headers = {'Content-Type': 'application/json'}
        params = {'siteName': 'Break',
                  'appName': 'Android Phones',
                  'siteId': '1'}
        json_data = json.dumps({'id': int(video_id)})
        video_data = self._request('/content/video/get', method='POST', params=params, post_data=json_data, headers=headers)

        data = video_data['data']
        hls_uri = data.get('hlsUri', '')
        if hls_uri:
            video_streams = []

            token = data['token']
            media_files = data['mediaFiles']
            for media_file in media_files:
                height = int(media_file['height'])
                bit_rate = int(media_file['bitRate'])

                # someone switched the values
                video_streams.append({'title': '%d @ %d' % (height, bit_rate),
                                      'sort': [height, bit_rate],
                                      'uri': media_file['uri'],
                                      'video': {'height': height}})
                pass

            return video_streams

        # try youtube
        youtube_video_id = data['thirdPartyUniqueId']
        return [{'title': 'YouTube',
                 'sort': [1],
                 'uri': 'plugin://plugin.video.youtube/play/?video_id=' + youtube_video_id,
                 'video': {'height': 1}}]

    def _request(self, url, method='GET', headers=None, post_data=None, params=None, allow_redirects=True):
        if not params:
            params = {}
            pass

        url = 'http://api.breakmedia.com/%s' % url.strip('/')

        response = super(Client, self)._request(url, method, headers, post_data, params, allow_redirects)
        if response.headers.get('content-type', '').startswith('application/json'):
            return response.json()

        return response.text

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
        url = 'http://www.break.com/content/find'

        result = nightcrawler.http.get(url, params=params, headers=headers, verify=False)

        import xml.etree.ElementTree as ET
        root = ET.fromstring(result.text)
        search_results = root.find('SearchResults')
        if search_results is not None:
            result = {'items': [],
                      'continue': False}

            for search_result in search_results:
                video_item = {'type': 'video',
                              'title': search_result.find('Title').text,
                              'id': search_result.find('ID').text,
                              'format': 'Break'}
                description = search_result.find('Description')
                if description is not None:
                    video_item['plot'] = description.text
                    pass

                image = search_result.find('Thumbnail')
                if image is not None:
                    video_item['images'] = {'thumbnail': image.text}
                    pass

                result['items'].append(video_item)
                pass
            pass

        # next page
        total_pages = root.find('TotalPages')
        if total_pages is not None:
            total_pages = int(total_pages.text)
            if page < total_pages:
                result['continue'] = True
                pass
            pass

        return result

    pass
