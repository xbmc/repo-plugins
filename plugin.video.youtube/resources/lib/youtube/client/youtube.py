__author__ = 'bromix'

import json

from resources.lib import kodion
from resources.lib.kodion import simple_requests as requests
from .login_client import LoginClient
from ..helper.video_info import VideoInfo


class YouTube(LoginClient):
    def __init__(self, key='', language='en-US', items_per_page=50, access_token=''):
        LoginClient.__init__(self, key=key, language=language, access_token=access_token)

        self._max_results = items_per_page
        pass

    def get_max_results(self):
        return self._max_results

    def get_language(self):
        return self._language

    def get_country(self):
        return self._country

    def update_watch_history(self, video_id):
        headers = {'Host': 'www.youtube.com',
                   'Connection': 'keep-alive',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36',
                   'Accept': 'image/webp,*/*;q=0.8',
                   'DNT': '1',
                   'Referer': 'https://www.youtube.com/tv',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'en-US,en;q=0.8,de;q=0.6'}
        params = {'noflv': '1',
                  'html5': '1',
                  'video_id': video_id,
                  'referrer': '',
                  'eurl': 'https://www.youtube.com/tv#/watch?v=%s' % video_id,
                  'skl': 'false',
                  'ns': 'yt',
                  'el': 'leanback',
                  'ps': 'leanback'}
        if self._access_token:
            params['access_token'] = self._access_token
            pass

        url = 'https://www.youtube.com/user_watch'

        result = requests.get(url, params=params, headers=headers, verify=False, allow_redirects=True)
        pass

    def get_video_streams(self, context, video_id):
        def _sort(x):
            index = {'mp4': 0,
                     'ts': 0,
                     'webm': -1,
                     'flv': -10,
                     '3gb': -20}
            container = x.get('format', {}).get('container', '')
            return index.get(container, -100)

        video_info = VideoInfo(context, access_token=self._access_token, language=self._language)

        video_streams = video_info.load_stream_infos(video_id)
        video_streams = sorted(video_streams, key=_sort, reverse=True)
        return video_streams

    def get_uploaded_videos_of_subscriptions(self, start_index=0):
        params = {'max-results': str(self._max_results),
                  'alt': 'json'}
        if start_index > 0:
            params['start-index'] = str(start_index)
            pass
        return self._perform_v2_request(method='GET', path='feeds/api/users/default/newsubscriptionvideos',
                                        params=params)

    def remove_playlist(self, playlist_id):
        params = {'id': playlist_id,
                  'mine': 'true'}
        return self._perform_v3_request(method='DELETE', path='playlists', params=params)

    def get_supported_languages(self, language=None):
        _language = language
        if not _language:
            _language = self._language
            pass
        _language = _language.replace('-', '_')
        params = {'part': 'snippet',
                  'hl': _language.split('_')[0]}
        return self._perform_v3_request(method='GET', path='i18nLanguages', params=params)

    def get_supported_regions(self, language=None):
        _language = language
        if not _language:
            _language = self._language
            pass
        _language = _language.replace('-', '_')
        params = {'part': 'snippet',
                  'hl': _language}
        return self._perform_v3_request(method='GET', path='i18nRegions', params=params)

    def rename_playlist(self, playlist_id, new_title, privacy_status='private'):
        params = {'part': 'snippet,id,status'}
        post_data = {'kind': 'youtube#playlist',
                     'id': playlist_id,
                     'snippet': {'title': new_title},
                     'status': {'privacyStatus': privacy_status}}
        return self._perform_v3_request(method='PUT', path='playlists', params=params, post_data=post_data)

    def create_playlist(self, title, privacy_status='private'):
        params = {'part': 'snippet,status'}
        post_data = {'kind': 'youtube#playlist',
                     'snippet': {'title': title},
                     'status': {'privacyStatus': privacy_status}}
        return self._perform_v3_request(method='POST', path='playlists', params=params, post_data=post_data)

    def get_video_rating(self, video_id):
        if isinstance(video_id, list):
            video_id = ','.join(video_id)
            pass

        params = {'id': video_id}
        return self._perform_v3_request(method='GET', path='videos/getRating', params=params)

    def rate_video(self, video_id, rating='like'):
        """
        Rate a video
        :param video_id: if of the video
        :param rating: [like|dislike|none]
        :return:
        """
        params = {'id': video_id,
                  'rating': rating}
        return self._perform_v3_request(method='POST', path='videos/rate', params=params)

    def add_video_to_playlist(self, playlist_id, video_id):
        params = {'part': 'snippet',
                  'mine': 'true'}
        post_data = {'kind': 'youtube#playlistItem',
                     'snippet': {'playlistId': playlist_id,
                                 'resourceId': {'kind': 'youtube#video',
                                                'videoId': video_id}}}
        return self._perform_v3_request(method='POST', path='playlistItems', params=params, post_data=post_data)

    def remove_video_from_playlist(self, playlist_id, playlist_item_id):
        params = {'id': playlist_item_id}
        return self._perform_v3_request(method='DELETE', path='playlistItems', params=params)

    def unsubscribe(self, subscription_id):
        params = {'id': subscription_id}
        return self._perform_v3_request(method='DELETE', path='subscriptions', params=params)

    def subscribe(self, channel_id):
        params = {'part': 'snippet'}
        post_data = {'kind': 'youtube#subscription',
                     'snippet': {'resourceId': {'kind': 'youtube#channel',
                                                'channelId': channel_id}}}
        return self._perform_v3_request(method='POST', path='subscriptions', params=params, post_data=post_data)

    def get_subscription(self, channel_id, order='alphabetical', page_token=''):
        """

        :param channel_id: [channel-id|'mine']
        :param order: ['alphabetical'|'relevance'|'unread']
        :param page_token:
        :return:
        """
        params = {'part': 'snippet,contentDetails',
                  'maxResults': str(self._max_results),
                  'order': order}
        if channel_id == 'mine':
            params['mine'] = 'true'
            pass
        else:
            params['channelId'] = channel_id
            pass
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='subscriptions', params=params)

    def get_guide_category(self, guide_category_id, page_token=''):
        params = {'part': 'snippet,contentDetails,brandingSettings',
                  'maxResults': str(self._max_results),
                  'categoryId': guide_category_id,
                  'regionCode': self._country,
                  'hl': self._language}
        if page_token:
            params['pageToken'] = page_token
            pass
        return self._perform_v3_request(method='GET', path='channels', params=params)

    def get_guide_categories(self, page_token=''):
        params = {'part': 'snippet',
                  'maxResults': str(self._max_results),
                  'regionCode': self._country,
                  'hl': self._language}
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='guideCategories', params=params)

    def get_popular_videos(self, page_token=''):
        params = {'part': 'snippet,contentDetails',
                  'maxResults': str(self._max_results),
                  'regionCode': self._country,
                  'hl': self._language,
                  'chart': 'mostPopular'}
        if page_token:
            params['pageToken'] = page_token
            pass
        return self._perform_v3_request(method='GET', path='videos', params=params)

    def get_video_category(self, video_category_id, page_token=''):
        params = {'part': 'snippet,contentDetails',
                  'maxResults': str(self._max_results),
                  'videoCategoryId': video_category_id,
                  'chart': 'mostPopular',
                  'regionCode': self._country,
                  'hl': self._language}
        if page_token:
            params['pageToken'] = page_token
            pass
        return self._perform_v3_request(method='GET', path='videos', params=params)

    def get_video_categories(self, page_token=''):
        params = {'part': 'snippet',
                  'maxResults': str(self._max_results),
                  'regionCode': self._country,
                  'hl': self._language}
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='videoCategories', params=params)

    def get_activities(self, channel_id, page_token=''):
        params = {'part': 'snippet,contentDetails',
                  'maxResults': str(self._max_results),
                  'regionCode': self._country,
                  'hl': self._language}
        if channel_id == 'home':
            params['home'] = 'true'
            pass
        elif channel_id == 'mine':
            params['mine'] = 'true'
            pass
        else:
            params['channelId'] = channel_id
            pass
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='activities', params=params)

    def get_channel_sections(self, channel_id):
        params = {'part': 'snippet,contentDetails',
                  'regionCode': self._country,
                  'hl': self._language}
        if channel_id == 'mine':
            params['mine'] = 'true'
            pass
        else:
            params['channelId'] = channel_id
            pass
        return self._perform_v3_request(method='GET', path='channelSections', params=params)

    def get_playlists(self, channel_id, page_token=''):
        params = {'part': 'snippet,contentDetails',
                  'maxResults': str(self._max_results)}
        if channel_id != 'mine':
            params['channelId'] = channel_id
            pass
        else:
            params['mine'] = 'true'
            pass
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='playlists', params=params)

    def get_playlist_item_id_of_video_id(self, playlist_id, video_id, page_token=''):
        old_max_results = self._max_results
        self._max_results = 50
        json_data = self.get_playlist_items(playlist_id=playlist_id, page_token=page_token)
        self._max_results = old_max_results

        items = json_data.get('items', [])
        for item in items:
            playlist_item_id = item['id']
            playlist_video_id = item.get('snippet', {}).get('resourceId', {}).get('videoId', '')
            if playlist_video_id and playlist_video_id == video_id:
                return playlist_item_id
            pass

        next_page_token = json_data.get('nextPageToken', '')
        if next_page_token:
            return self.get_playlist_item_id_of_video_id(playlist_id=playlist_id, video_id=video_id,
                                                         page_token=next_page_token)

        return None

    def get_playlist_items(self, playlist_id, page_token=''):
        # prepare params
        params = {'part': 'snippet',
                  'maxResults': str(self._max_results),
                  'playlistId': playlist_id}
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='playlistItems', params=params)

    def get_channel_by_username(self, username):
        """
        Returns a collection of zero or more channel resources that match the request criteria.
        :param channel_id: list or comma-separated list of the YouTube channel ID(s)
        :return:
        """
        params = {'part': 'id',
                  'forUsername': username}

        return self._perform_v3_request(method='GET', path='channels', params=params)

    def get_channels(self, channel_id):
        """
        Returns a collection of zero or more channel resources that match the request criteria.
        :param channel_id: list or comma-separated list of the YouTube channel ID(s)
        :return:
        """
        if isinstance(channel_id, list):
            channel_id = ','.join(channel_id)
            pass

        params = {'part': 'snippet,contentDetails,brandingSettings'}
        if channel_id != 'mine':
            params['id'] = channel_id
            pass
        else:
            params['mine'] = 'true'
            pass
        return self._perform_v3_request(method='GET', path='channels', params=params)

    def get_disliked_videos(self, page_token=''):
        # prepare page token
        if not page_token:
            page_token = ''
            pass

        # prepare params
        params = {'part': 'snippet,contentDetails',
                  'myRating': 'dislike',
                  'maxResults': str(self._max_results)}
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='videos', params=params)

    def get_videos(self, video_id):
        """
        Returns a list of videos that match the API request parameters
        :param video_id: list of video ids
        :return:
        """
        if isinstance(video_id, list):
            video_id = ','.join(video_id)
            pass

        params = {'part': 'snippet,contentDetails',
                  'id': video_id}
        return self._perform_v3_request(method='GET', path='videos', params=params)

    def get_live_events(self, event_type='live', order='relevance', page_token=''):
        """

        :param event_type: one of: 'live', 'completed', 'upcoming'
        :param order: one of: 'date', 'rating', 'relevance', 'title', 'videoCount', 'viewCount'
        :param page_token:
        :return:
        """
        # prepare page token
        if not page_token:
            page_token = ''
            pass

        # prepare params
        params = {'part': 'snippet',
                  'type': 'video',
                  'order': order,
                  'eventType': event_type,
                  'regionCode': self._country,
                  'hl': self._language,
                  'maxResults': str(self._max_results)}
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='search', params=params)

    def get_related_videos(self, video_id, page_token=''):
        # prepare page token
        if not page_token:
            page_token = ''
            pass

        # prepare params
        params = {'relatedToVideoId': video_id,
                  'part': 'snippet',
                  'type': 'video',
                  'regionCode': self._country,
                  'hl': self._language,
                  'maxResults': str(self._max_results)}
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='search', params=params)

    def search(self, q, search_type=['video', 'channel', 'playlist'], event_type='', page_token=''):
        """
        Returns a collection of search results that match the query parameters specified in the API request. By default,
        a search result set identifies matching video, channel, and playlist resources, but you can also configure
        queries to only retrieve a specific type of resource.
        :param q:
        :param search_type: acceptable values are: 'video' | 'channel' | 'playlist'
        :param event_type: 'live', 'completed', 'upcoming'
        :param page_token: can be ''
        :return:
        """

        # prepare search type
        if not search_type:
            search_type = ''
            pass
        if isinstance(search_type, list):
            search_type = ','.join(search_type)
            pass

        # prepare page token
        if not page_token:
            page_token = ''
            pass

        # prepare params
        params = {'q': q,
                  'part': 'snippet',
                  'regionCode': self._country,
                  'hl': self._language,
                  'maxResults': str(self._max_results)}
        if event_type and event_type in ['live', 'upcoming', 'completed']:
            params['eventType'] = event_type
            pass
        if search_type:
            params['type'] = search_type
            pass
        if page_token:
            params['pageToken'] = page_token
            pass

        return self._perform_v3_request(method='GET', path='search', params=params)

    def _perform_v3_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                            allow_redirects=True):
        # params
        if not params:
            params = {}
            pass
        _params = {'key': self._key}
        _params.update(params)

        # headers
        if not headers:
            headers = {}
            pass
        _headers = {'Host': 'www.googleapis.com',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36',
                    'Accept-Encoding': 'gzip, deflate',
                    'X-JavaScript-User-Agent': 'Google APIs Explorer'}
        if self._access_token:
            _headers['Authorization'] = 'Bearer %s' % self._access_token
            pass
        _headers.update(headers)

        # url
        _url = 'https://www.googleapis.com/youtube/v3/%s' % path.strip('/')

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

    def _perform_v2_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                            allow_redirects=True):
        # params
        if not params:
            params = {}
            pass
        _params = {'key': self._key}
        _params.update(params)

        # headers
        if not headers:
            headers = {}
            pass
        _headers = {'Host': 'gdata.youtube.com',
                    'X-GData-Key': 'key=%s' % self._key,
                    'GData-Version': '2.1',
                    'Accept-Encoding': 'gzip, deflate',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.36 Safari/537.36'}
        if self._access_token:
            _headers['Authorization'] = 'Bearer %s' % self._access_token
            pass
        _headers.update(headers)

        # url
        url = 'https://gdata.youtube.com/%s/' % path.strip('/')

        result = None
        if method == 'GET':
            result = requests.get(url, params=_params, headers=_headers, verify=False, allow_redirects=allow_redirects)
            pass

        if result is None:
            return {}

        if method != 'DELETE' and result.text:
            return result.json()
        pass

    pass