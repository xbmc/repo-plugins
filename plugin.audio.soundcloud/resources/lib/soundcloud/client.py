from resources.lib import kodion

__author__ = 'bromix'

#import requests
from resources.lib.kodion import simple_requests as requests


class ClientException(kodion.KodionException):
    def __init__(self, status_code, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self._status_code = status_code
        pass

    def get_status_code(self):
        return self._status_code

    pass


class Client(object):
    CLIENT_ID = '40ccfee680a844780a41fbe23ea89934'
    CLIENT_SECRET = '26a5240f7ee0ee2d4fa9956ed80616c2'

    def __init__(self, username='', password='', access_token='', client_id='', client_secret='', items_per_page=50):
        self._username = username
        self._password = password
        self._access_token = access_token
        self._items_per_page = items_per_page

        # set client id with fallback
        self._client_id = self.CLIENT_ID
        if client_id:
            self._client_id = client_id
            pass

        # set client secret with fallback
        self._client_secret = self.CLIENT_SECRET
        if client_secret:
            self._client_secret = client_secret
            pass
        pass

    def _create_path_based_on_user_id(self, me_or_user_id, path):
        """
        Creates the API path based on 'me' otherwise for the given user id
        :param me_or_user_id:
        :param path:
        :return:
        """
        user_id = unicode(me_or_user_id)
        if user_id == 'me':
            return 'me/%s' % path.strip('/')
        return 'users/%s/%s' % (user_id, path.strip('/'))

    def resolve_url(self, url):
        params = {'url': url}
        return self._perform_request(path='resolve',
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_trending(self, category='music', page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        path = 'app/mobileapps/suggestions/tracks/popular/%s' % category
        params = {'limit': str(per_page)}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_genre(self, genre, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        path = 'app/mobileapps/suggestions/tracks/categories/%s' % genre
        params = {'limit': str(per_page)}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_categories(self):
        return self._perform_request(path='app/mobileapps/suggestions/tracks/categories',
                                     headers={'Accept': 'application/json'})

    def get_track_url(self, track_id):
        return self._perform_request(path='tracks/%s/stream' % str(track_id),
                                     headers={'Accept': 'application/json'},
                                     allow_redirects=False)

    def search(self, search_text, category='sounds', page=1):
        """

        :param search_text:
        :param category: ['sounds', 'people', 'sets']
        :param page:
        :param per_page:
        :return:
        """
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'q': search_text}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        headers = {'Accept': 'application/json'}
        return self._perform_request(path='search/%s' % category,
                                     headers=headers,
                                     params=params)

    def get_stream(self, page_cursor=None):
        params = {'limit': unicode(self._items_per_page)}
        if page_cursor is not None:
            params['cursor'] = page_cursor

        return self._perform_request(path='me/activities/tracks/affiliated',
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def like_track(self, track_id, like=True):
        method = 'PUT'
        if not like:
            method = 'DELETE'
            pass

        return self._perform_request(method=method,
                                     path='e1/me/track_likes/%s' % unicode(track_id),
                                     headers={'Accept': 'application/json'})

    def like_playlist(self, playlist_id, like=True):
        method = 'PUT'
        if not like:
            method = 'DELETE'
            pass

        return self._perform_request(method=method,
                                     path='e1/me/playlist_likes/%s' % unicode(playlist_id),
                                     headers={'Accept': 'application/json'})

    def get_favorites(self, me_or_user_id, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        path = self._create_path_based_on_user_id(me_or_user_id, 'favorites')
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_likes(self, user_id, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            params['page_size'] = params['offset']
            params['page_number'] = unicode(page)
            pass

        return self._perform_request(path='e1/users/%s/likes' % unicode(user_id),
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def follow_user(self, user_id, follow=True):
        method = 'PUT'
        if not follow:
            method = 'DELETE'
            pass

        return self._perform_request(method=method,
                                     path='me/followings/%s' % unicode(user_id),
                                     headers={'Accept': 'application/json'})

    def get_playlist(self, playlist_id):
        return self._perform_request(path='playlists/%s' % unicode(playlist_id),
                                     headers={'Accept': 'application/json'})

    def get_playlists(self, me_or_user_id, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        path = self._create_path_based_on_user_id(me_or_user_id, 'playlists')
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_follower(self, me_or_user_id, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        path = self._create_path_based_on_user_id(me_or_user_id, 'followers')
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_following(self, me_or_user_id, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        path = self._create_path_based_on_user_id(me_or_user_id, 'followings')
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_recommended_for_track(self, track_id, page=1):
        path = 'tracks/%s/related' % str(track_id)
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_track(self, track_id):
        path = 'tracks/%s' % str(track_id)
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'})

    def get_tracks(self, me_or_user_id, page=1):
        page = int(page)
        per_page = int(self._items_per_page)

        params = {'limit': str(per_page),
                  'linked_partitioning': '1'}
        if page > 1:
            params['offset'] = str((page - 1) * per_page)
            pass

        path = self._create_path_based_on_user_id(me_or_user_id, 'tracks')
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'},
                                     params=params)

    def get_user(self, me_or_user_id):
        self.update_access_token()
        path = self._create_path_based_on_user_id(me_or_user_id, '')
        return self._perform_request(path=path,
                                     headers={'Accept': 'application/json'})

    def get_access_token(self):
        return self._access_token

    def _perform_request(self, method='GET', headers=None, path=None, post_data=None, params=None,
                         allow_redirects=True):
        # params
        if not params:
            params = {}
            pass
        if self._client_id:
            params['client_id'] = self._client_id
            pass

        # basic header
        _headers = {'Accept-Encoding': 'gzip',
                    'Host': 'api.soundcloud.com:443',
                    'Connection': 'Keep-Alive',
                    'User-Agent': 'SoundCloud-Android/14.10.01-27 (Android 4.4.4; samsung GT-I9100'}
        # set access token
        if self._access_token:
            _headers['Authorization'] = 'OAuth %s' % self._access_token
            pass
        if not headers:
            headers = {}
            pass
        _headers.update(headers)

        # url
        _url = 'https://api.soundcloud.com:443/%s' % path

        result = None
        if method == 'GET':
            result = requests.get(_url, params=params, headers=_headers, verify=False, allow_redirects=allow_redirects)
        elif method == 'POST':
            result = requests.post(_url, data=post_data, params=params, headers=_headers, verify=False,
                                   allow_redirects=allow_redirects)
        elif method == 'PUT':
            result = requests.put(_url, data=post_data, params=params, headers=_headers, verify=False,
                                  allow_redirects=allow_redirects)
        elif method == 'DELETE':
            result = requests.delete(_url, data=post_data, params=params, headers=_headers, verify=False,
                                     allow_redirects=allow_redirects)
            pass

        if result is None:
            return {}

        if result.status_code == requests.codes.unauthorized:
            raise ClientException(status_code=result.status_code)

        return result.json()

    def update_access_token(self):
        if not self._access_token and self._username and self._password:
            post_data = {'grant_type': 'password',
                         'client_id': self._client_id,
                         'client_secret': self._client_secret,
                         'username': self._username.encode('utf-8'),
                         'password': self._password.encode('utf-8'),
                         'scope': 'non-expiring'}

            json_data = self._perform_request(method='POST', path='oauth2/token', post_data=post_data)
            self._access_token = json_data.get('access_token', None)
            return self._access_token

        return ''

    pass