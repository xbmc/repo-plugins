import urllib
import urlparse

__author__ = 'bromix'

import time
import hmac
from hashlib import sha1

from resources.lib.kodion import simple_requests as requests

"""
video_sort_kind: 'newest', 'oldest', 'most_played', 'most_commented', 'most_liked'
"""


class Client():
    CONSUMER_KEY = 'ae4ac83f9facda375a72fed704a3643a'
    CONSUMER_SECRET = 'b6072a4aba1eaaed'

    def __init__(self, oauth_token='', oauth_token_secret=''):
        self._oauth_token = oauth_token
        self._oauth_token_secret = oauth_token_secret
        pass

    def login(self, username, password):
        headers = {'Content-Type': 'application/x-www-form-urlencoded',
                   'Host': 'secure.vimeo.com'}
        post_data = {'x_auth_password': password,
                     'x_auth_username': username,
                     'x_auth_mode': 'client_auth',
                     'x_auth_permission': 'delete'}

        data = self._perform_v2_request(url='https://secure.vimeo.com/oauth/access_token',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

        data = dict(urlparse.parse_qsl(data))
        return data

    def get_collections(self, video_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.videos.getCollections',
                     'video_id': video_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def search(self, query, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.videos.search',
                     'sort': 'relevant',
                     'page': str(page),
                     'full_response': '1',
                     'query': query}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_channel_videos(self, channel_id, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.getVideos',
                     'sort': 'newest',  # 'oldest', 'most_played', 'most_commented', 'most_liked'
                     'page': str(page),
                     'channel_id': channel_id,
                     'full_response': '1'}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def remove_video_from_group(self, video_id, group_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.groups.removeVideo',
                     'video_id': video_id,
                     'group_id': group_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def add_video_to_group(self, video_id, group_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.groups.addVideo',
                     'video_id': video_id,
                     'group_id': group_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_groups(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.groups.getAddable',
                     'sort': 'newest',  # 'oldest', 'most_played', 'most_commented', 'most_liked'
                     'page': str(page)}
        if user_id and user_id != 'me':
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_group_videos(self, group_id, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.groups.getVideos',
                     'sort': 'newest',  # 'oldest', 'most_played', 'most_commented', 'most_liked'
                     'group_id': group_id,
                     'page': str(page),
                     'full_response': '1'}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_my_feed(self, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.videos.getSubscriptions',
                     'sort': 'newest',
                     'page': str(page),
                     'full_response': '1'}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_video_likes(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        # video_sort_kind: 'newest', 'oldest', 'most_played', 'most_commented', 'most_liked'
        post_data = {'method': 'vimeo.videos.getLikes',
                     'sort': 'newest',
                     'page': str(page),
                     'full_response': '1'}
        if user_id:
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_video_info(self, video_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.videos.getInfo',
                     'video_id': video_id}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_watch_later(self, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.albums.getWatchLater',
                     'page': str(page),
                     'full_response': '1'}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_channels_all(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.getAll',
                     'page': str(page),
                     'sort': 'alphabetical'}  # 'newest', 'oldest', 'alphabetical', 'most_videos', 'most_subscribed', 'most_recently_updated'
        if user_id and user_id != 'me':
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_channels_moderated(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.getModerated',
                     'page': str(page),
                     'sort': 'alphabetical'}  # 'newest', 'oldest', 'alphabetical', 'most_videos', 'most_subscribed', 'most_recently_updated'
        if user_id and user_id != 'me':
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def remove_video_from_channel(self, video_id, channel_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.removeVideo',
                     'video_id': video_id,
                     'channel_id': channel_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def add_video_to_channel(self, video_id, channel_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.addVideo',
                     'video_id': video_id,
                     'channel_id': channel_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_videos_of_user(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.videos.getAll',
                     'page': str(page),
                     'full_response': '1',
                     'sort': 'newest'}  # 'oldest', 'most_played', 'most_commented', 'most_liked'

        if user_id and user_id != 'me':
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def like_video(self, video_id, like=True):
        if like:
            like = '1'
        else:
            like = '0'
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.videos.setLike',
                     'video_id': video_id,
                     'like': like}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def add_video_to_watch_later(self, video_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'video_id': video_id,
                     'method': 'vimeo.albums.addToWatchLater'}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def remove_video_from_watch_later(self, video_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'video_id': video_id,
                     'method': 'vimeo.albums.removeFromWatchLater'}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def join_group(self, group_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.groups.join',
                     'group_id': group_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def leave_group(self, group_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.groups.leave',
                     'group_id': group_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def subscribe_channel(self, channel_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.subscribe',
                     'channel_id': channel_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def unsubscribe_channel(self, channel_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.channels.unsubscribe',
                     'channel_id': channel_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_albums(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.albums.getAll',
                     'page': str(page),
                     'sort': 'alphabetical'}
        if user_id and user_id != 'me':
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def remove_video_from_album(self, video_id, album_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.albums.removeVideo',
                     'video_id': video_id,
                     'album_id': album_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def add_video_to_album(self, video_id, album_id):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.albums.addVideo',
                     'video_id': video_id,
                     'album_id': album_id}
        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_album_videos(self, album_id, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.albums.getVideos',
                     'page': str(page),
                     'full_response': '1',
                     'album_id': album_id,
                     'sort': 'newest'}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_contacts(self, user_id=None, page=1):
        if not page:
            page = 1
            pass

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        post_data = {'method': 'vimeo.contacts.getAll',
                     'page': str(page),
                     'sort': 'alphabetical'}
        if user_id:
            post_data['user_id'] = user_id
            pass

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)

    def get_video_streams(self, video_id, password=None):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        if not password:
            password = ''
            pass

        post_data = {'method': 'vimeo.videos.getSourceFileUrls',
                     'password': password,
                     'video_id': video_id}

        return self._perform_v2_request(url='http://vimeo.com/api/rest/v2',
                                        method='POST',
                                        headers=headers,
                                        post_data=post_data)


    def get_featured(self):
        return self._perform_v2_request(url='http://vimeo.com/api/v2/featured.xml',
                                        method='GET')

    def _create_authorization(self, url, method, params=None):
        def _percent_encode(s):
            if isinstance(s, unicode):
                s = s.encode('utf-8')
                pass

            result = urllib.quote_plus(s).replace('+', '%20').replace('*', '%2A').replace('%7E', '~')
            # the implementation of the app has a bug. someone double escaped the '@' so we have to correct this
            # on our end.
            result = result.replace('%40', '%2540')
            return result

        def _compute_signature(s):
            key = _percent_encode(self.CONSUMER_SECRET) + '&' + _percent_encode(self._oauth_token_secret)
            a = hmac.new(key, s, sha1)
            return a.digest().encode("base64").rstrip('\n')

        def _normalize_parameters(_params):
            sorted_keys = sorted(_params.keys())
            list_of_params = []
            for key in sorted_keys:
                value = _params[key]
                # who wrote the android app should burn in hell! No clue of correct encoding - make up your mind
                if url == 'https://secure.vimeo.com/oauth/access_token' and key != 'x_auth_password':
                    list_of_params.append('%s=%s' % (key, value))
                    pass
                else:
                    list_of_params.append('%s=%s' % (key, _percent_encode(value)))
                    pass
                pass
            return '&'.join(list_of_params)

        if not params:
            params = {}
            pass

        all_params = {'oauth_consumer_key': self.CONSUMER_KEY,
                      'oauth_signature_method': 'HMAC-SHA1',
                      'oauth_timestamp': str(time.time()),
                      'oauth_nonce': str(time.time()),
                      'oauth_version': '1.0'}
        if self._oauth_token:
            all_params['oauth_token'] = self._oauth_token
            pass
        all_params.update(params)

        base_string = _percent_encode(method.upper())
        base_string += '&'
        base_string += _percent_encode(url)
        base_string += '&'
        base_string += _percent_encode(_normalize_parameters(all_params))

        all_params['oauth_signature'] = _compute_signature(base_string)

        authorization = []
        for key in all_params:
            if key.startswith('oauth_'):
                authorization.append('%s="%s"' % (key, _percent_encode(all_params[key])))
                pass
            pass
        return {'Authorization': 'OAuth %s' % (', '.join(authorization))}

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
        _headers = {
            'User-Agent': 'VimeoAndroid/1.1.42 (Android ver=4.4.2 sdk=19; Model samsung GT-I9505; Linux 3.4.0-3423977 armv7l)',
            'Host': 'vimeo.com',
            'Accept-Encoding': 'gzip, deflate'}
        _headers.update(headers)
        oauth_parms = post_data or params
        _headers.update(self._create_authorization(url, method, oauth_parms))

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

        return result.text

    pass