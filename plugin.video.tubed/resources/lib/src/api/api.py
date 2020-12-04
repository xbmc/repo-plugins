# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import time

import tubed_api  # pylint: disable=import-error
import xbmcaddon  # pylint: disable=import-error
from tubed_api import oauth  # pylint: disable=import-error
from tubed_api import usher  # pylint: disable=import-error
from tubed_api import v3  # pylint: disable=import-error

from ..constants import ADDON_ID
from ..constants import CREDENTIALS
from ..constants import ONE_MINUTE
from ..constants import ONE_WEEK
from ..lib import memoizer
from ..storage.users import UserStorage
from .decorators import api_request


def memoizer_ttl():
    return xbmcaddon.Addon(ADDON_ID).getSettingInt('cache.ttl.function')


class API:

    def __init__(self, language='en-US', region='US'):
        self._language = language
        self._region = region
        self._max_results = 50

        self.users = UserStorage()
        self._api = tubed_api

        self._api.CLIENT_ID = str(CREDENTIALS.ID)
        self._api.CLIENT_SECRET = str(CREDENTIALS.SECRET)
        self._api.API_KEY = str(CREDENTIALS.KEY)
        self._api.HTTP_REFERRER = 'https://tubedaddon.panicked.xyz/'

        self._api.ACCESS_TOKEN = self.users.access_token

        self._usher = usher

        self.quality = self._usher.Quality

        self.api = v3
        self.client = oauth.Client()
        self.refresh_token()

    @property
    def logged_in(self):
        self.refresh_token()
        return self.users.access_token and not self.users.token_expired

    @property
    def language(self):
        return self._language.replace('-', '_')

    @language.setter
    def language(self, value):
        self._language = value

    @property
    def region(self):
        return self._region

    @region.setter
    def region(self, value):
        self._region = value

    @property
    def max_results(self):
        return int(self._max_results)

    @max_results.setter
    def max_results(self, value):
        self._max_results = int(value)

    @api_request
    @memoizer.cache_method(limit=ONE_WEEK)
    def languages(self):

        return self.api.i18n_languages.get({
            'part': 'snippet',
            'hl': self.language,
            'fields': 'items(id,snippet(name,hl))'
        })

    @api_request
    @memoizer.cache_method(limit=ONE_WEEK)
    def regions(self):

        return self.api.i18n_regions.get({
            'part': 'snippet',
            'hl': self.language,
            'fields': 'items(id,snippet(name,gl))'
        })

    @api_request
    def remove_playlist(self, playlist_id):
        parameters = {
            'id': playlist_id,
            'mine': 'true'
        }

        return self.api.playlists.delete(parameters=parameters)

    @api_request
    def rename_playlist(self, playlist_id, title, privacy_status='private', fields=None):
        parameters = {
            'part': 'snippet,id,status'
        }
        data = {
            'kind': 'youtube#playlist',
            'id': playlist_id,
            'snippet': {
                'title': title
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }

        if fields:
            parameters['fields'] = fields

        return self.api.playlists.update(parameters=parameters, data=data)

    @api_request
    def create_playlist(self, title, privacy_status='private', fields=None):
        parameters = {
            'part': 'snippet,status'
        }
        data = {
            'kind': 'youtube#playlist',
            'snippet': {
                'title': title
            },
            'status': {
                'privacyStatus': privacy_status
            }
        }

        if fields:
            parameters['fields'] = fields

        return self.api.playlists.insert(parameters=parameters, data=data)

    @api_request
    def add_to_playlist(self, playlist_id, video_id, fields=None):
        parameters = {
            'part': 'snippet',
            'mine': 'true'
        }
        data = {
            'kind': 'youtube#playlistItem',
            'snippet': {
                'playlistId': playlist_id,
                'resourceId': {
                    'kind': 'youtube#video',
                    'videoId': video_id
                }
            }
        }

        if fields:
            parameters['fields'] = fields

        return self.api.playlist_items.insert(parameters=parameters, data=data)

    @api_request
    def remove_from_playlist(self, playlist_item_id):

        return self.api.playlist_items.delete({
            'id': playlist_item_id
        })

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def rating(self, video_id):
        if isinstance(video_id, list):
            video_id = ','.join(video_id)

        return self.api.videos.get_rating({
            'id': video_id
        })

    @api_request
    def rate(self, video_id, rating='like'):
        parameters = {
            'id': video_id,
            'rating': rating
        }

        return self.api.videos.rate(parameters=parameters)

    @api_request
    def subscribe(self, channel_id):
        parameters = {
            'part': 'snippet'
        }
        data = {
            'snippet': {
                'resourceId': {
                    'kind': 'youtube#channel',
                    'channelId': channel_id
                }
            }
        }

        return self.api.subscriptions.insert(parameters=parameters, data=data)

    @api_request
    def unsubscribe(self, subscription_id):

        return self.api.subscriptions.delete({
            'id': subscription_id
        })

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def subscriptions(self, channel_id, order='alphabetical', page_token='', fields=None):
        parameters = {
            'part': 'snippet',
            'maxResults': str(self.max_results),
            'order': order
        }

        if channel_id == 'mine':
            parameters['mine'] = 'true'
        else:
            parameters['channelId'] = channel_id

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.subscriptions.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def video_category(self, category_id, page_token='', fields=None):
        parameters = {
            'part': 'snippet,contentDetails,status',
            'maxResults': str(self.max_results),
            'videoCategoryId': category_id,
            'chart': 'mostPopular',
            'regionCode': self.region,
            'hl': self.language
        }

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.videos.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def video_categories(self, page_token=''):
        parameters = {
            'part': 'snippet',
            'maxResults': str(self.max_results),
            'regionCode': self.region,
            'hl': self.language
        }
        if page_token:
            parameters['pageToken'] = page_token

        return self.api.video_categories.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def channel_sections(self, channel_id):
        parameters = {
            'part': 'snippet,contentDetails',
            'regionCode': self.region,
            'hl': self.language
        }

        if channel_id == 'mine':
            parameters['mine'] = 'true'
        else:
            parameters['channelId'] = channel_id

        return self.api.channel_sections.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def playlists_of_channel(self, channel_id, page_token='', fields=None):
        parameters = {
            'part': 'snippet',
            'maxResults': str(self.max_results)
        }

        if channel_id != 'mine':
            parameters['channelId'] = channel_id
        else:
            parameters['mine'] = 'true'

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.playlists.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def playlist_items(self, playlist_id, page_token='', max_results=None, fields=None):
        parameters = {
            'part': 'snippet',
            'maxResults': max_results or str(self.max_results),
            'playlistId': playlist_id
        }

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.playlist_items.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def channel_by_username(self, username):
        parameters = {
            'part': 'id',
            'fields': 'items(id)'
        }

        if username == 'mine':
            parameters['mine'] = 'true'
        else:
            parameters['forUsername'] = username

        return self.api.channels.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def channels(self, channel_id, fields=None):
        if isinstance(channel_id, list):
            channel_id = ','.join(channel_id)

        parameters = {
            'part': 'snippet,contentDetails,brandingSettings'
        }

        if channel_id != 'mine':
            parameters['id'] = channel_id
        else:
            parameters['mine'] = 'true'

        if fields:
            parameters['fields'] = fields

        return self.api.channels.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def my_rating(self, rating='like', page_token='', fields=None):
        parameters = {
            'part': 'snippet,status',
            'myRating': rating,
            'maxResults': str(self.max_results)
        }

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.videos.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def videos(self, video_id, live_details=False, fields=None):
        if isinstance(video_id, list):
            video_id = ','.join(video_id)

        parts = ['snippet', 'contentDetails', 'status', 'statistics']
        if live_details:
            parts.append('liveStreamingDetails')

        parameters = {
            'part': ','.join(parts),
            'id': video_id
        }

        if fields:
            parameters['fields'] = fields

        return self.api.videos.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def playlists(self, playlist_id, fields=None):
        if isinstance(playlist_id, list):
            playlist_id = ','.join(playlist_id)

        parameters = {
            'part': 'snippet,contentDetails',
            'id': playlist_id
        }

        if fields:
            parameters['fields'] = fields

        return self.api.playlists.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def comment_thread(self, thread_id):
        parameters = {
            'part': 'snippet',
            'id': thread_id,
            'textFormat': 'plainText',
        }

        return self.api.comment_threads.get(parameters=parameters, unauthorized=True)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def comment(self, comment_id):
        parameters = {
            'part': 'snippet',
            'id': comment_id,
            'textFormat': 'plainText',
        }

        return self.api.comments.get(parameters=parameters, unauthorized=True)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def comment_threads(self, video_id, order='relevance', page_token='', max_results=None):
        parameters = {
            'part': 'snippet',
            'videoId': video_id,
            'order': order,
            'textFormat': 'plainText',
            'maxResults': max_results or '100'
        }

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.comment_threads.get(parameters=parameters, unauthorized=True)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def comments(self, parent_id, page_token='', max_results=None):
        parameters = {
            'part': 'snippet',
            'parentId': parent_id,
            'textFormat': 'plainText',
            'maxResults': max_results or '100'
        }

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.comments.get(parameters=parameters, unauthorized=True)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def channel_videos(self, channel_id, page_token='', fields=None):
        parameters = {
            'part': 'snippet',
            'hl': self.language,
            'maxResults': str(self.max_results),
            'type': 'video',
            'safeSearch': 'none',
            'order': 'date'
        }

        if channel_id == 'mine':
            parameters['forMine'] = 'true'
        else:
            parameters['channelId'] = channel_id

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.search.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def live_events(self, event_type='live', order='relevance',
                    page_token='', fields=None, published_after=None):

        parameters = {
            'part': 'snippet',
            'type': 'video',
            'order': order,
            'eventType': event_type,
            'regionCode': self.region,
            'hl': self.language,
            'relevanceLanguage': self.language,
            'maxResults': str(self.max_results)
        }

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if published_after:
            parameters['publishedAfter'] = published_after

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.search.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def related_videos(self, video_id, page_token='', max_results=None, fields=None):
        parameters = {
            'relatedToVideoId': video_id,
            'part': 'snippet',
            'type': 'video',
            'regionCode': self.region,
            'hl': self.language,
            'maxResults': max_results or str(self.max_results)
        }

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.search.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def search(self, query, search_type=None, event_type='', channel_id='',  # pylint: disable=too-many-arguments
               order='relevance', safe_search='moderate', page_token='', fields=None):

        parameters = {
            'q': query,
            'part': 'snippet',
            'regionCode': self.region,
            'hl': self.language,
            'relevanceLanguage': self.language,
            'maxResults': str(self.max_results)
        }

        if search_type is None:
            search_type = ['video', 'channel', 'playlist']

        elif not search_type:
            search_type = ''

        elif isinstance(search_type, list):
            search_type = ','.join(search_type)

        if event_type and event_type in ['live', 'upcoming', 'completed']:
            parameters['eventType'] = event_type

        if search_type:
            parameters['type'] = search_type

        if channel_id:
            parameters['channelId'] = channel_id

        if order:
            parameters['order'] = order

        if safe_search:
            parameters['safeSearch'] = safe_search

        if page_token:
            parameters['pageToken'] = page_token

        video_only = ['eventType', 'videoCaption', 'videoCategoryId', 'videoDefinition',
                      'videoDimension', 'videoDuration', 'videoEmbeddable', 'videoLicense',
                      'videoSyndicated', 'videoType', 'relatedToVideoId', 'forMine']

        for key in video_only:
            if parameters.get(key) is not None:
                parameters['type'] = 'video'
                break

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        return self.api.search.get(parameters=parameters)

    @api_request
    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def most_popular(self, page_token='', region_code='', fields=None):
        parameters = {
            'part': 'snippet,status',
            'maxResults': str(self.max_results),
            'regionCode': region_code or self.region,
            'hl': self.language,
            'chart': 'mostPopular'
        }

        if fields:
            parameters['fields'] = fields + ',nextPageToken'

        if page_token:
            parameters['pageToken'] = page_token

        return self.api.videos.get(parameters=parameters)

    @memoizer.cache_method(limit=ONE_MINUTE * memoizer_ttl())
    def video_id_to_playlist_item_id(self, playlist_id, video_id, page_token=''):
        payload = self.playlist_items(
            playlist_id=playlist_id,
            page_token=page_token,
            max_results=50,
            fields='items(id,snippet(resourceId/videoId)),nextPageToken'
        )

        items = payload.get('items', [])

        for item in items:
            source_video_id = item.get('snippet', {}).get('resourceId', {}).get('videoId', '')
            if source_video_id and source_video_id == video_id:
                return item['id']

        page_token = payload.get('nextPageToken', '')
        if page_token:
            return self.video_id_to_playlist_item_id(playlist_id=playlist_id,
                                                     video_id=video_id,
                                                     page_token=page_token)

        return None

    @memoizer.cache_method(limit=ONE_MINUTE * 7)
    def resolve(self, video_id, quality=None):
        if isinstance(quality, (int, str)):
            quality = self._usher.Quality(quality)

        return self._usher.resolve(video_id, quality=quality,
                                   language=self.language, region=self.region)

    @api_request
    def refresh_token(self):
        if self.users.access_token and self.users.token_expired:
            access_token, expiry = self.client.refresh_token(self.users.refresh_token)
            self.users.access_token = access_token
            self.users.token_expiry = time.time() + int(expiry)
            self.users.save()
            self.refresh_client()

    @api_request
    def revoke_token(self):
        if self.users.refresh_token:
            self.client.revoke_token(self.users.refresh_token)
            self.users.access_token = ''
            self.users.refresh_token = ''
            self.users.token_expiry = -1
            self.users.save()
            self.refresh_client()

    @api_request
    def request_codes(self):
        return self.client.request_codes()

    @api_request
    def request_access_token(self, device_code):
        data = self.client.request_access_token(device_code)

        if 'error' not in data:
            access_token = data.get('access_token', '')
            refresh_token = data.get('refresh_token', '')
            token_expiry = time.time() + int(data.get('expires_in', 3600))

            if not access_token and not refresh_token:
                token_expiry = -1

            self.users.access_token = access_token
            self.users.refresh_token = refresh_token
            self.users.token_expiry = token_expiry
            self.users.save()
            self.refresh_client()
            return True

        if data['error'] == 'authorization_pending':
            return False

        return data

    def refresh_client(self):
        self.users.load()
        self._api.ACCESS_TOKEN = self.users.access_token
        self.client = oauth.Client()
        memoizer.reset_cache()

    def calculate_next_page_token(self, page):
        """
            Copyright (C) 2014-2016 bromix (plugin.video.youtube)
            Copyright (C) 2016-2020 plugin.video.youtube
            SPDX-License-Identifier: GPL-2.0-only
            See LICENSES/GPL-2.0-only for more information.
        """
        low = 'AEIMQUYcgkosw048'
        high = 'ABCDEFGHIJKLMNOP'

        position = (page - 1) * self.max_results

        overflow_token = 'Q'
        if position >= 128:
            overflow_token_iteration = position // 128
            overflow_token = '%sE' % high[overflow_token_iteration]

        low_iteration = position % len(low)

        if position >= 256:
            multiplier = (position // 128) - 1
            position -= 128 * multiplier

        high_iteration = (position // len(low)) % len(high)

        return 'C%sAA' % ''.join([high[high_iteration], low[low_iteration], overflow_token])
