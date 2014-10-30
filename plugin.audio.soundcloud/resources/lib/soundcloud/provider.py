from functools import partial
import re

from resources.lib.kodimon.helper import FunctionCache

from resources.lib.kodimon import DirectoryItem, AudioItem, constants, KodimonException, contextmenu
from resources.lib import kodimon
from resources.lib.soundcloud.client import ClientException


__author__ = 'bromix'


class Provider(kodimon.AbstractProvider):
    SETTINGS_USER_ID = 'soundcloud.user.id'

    def __init__(self, plugin=None):
        kodimon.AbstractProvider.__init__(self, plugin)

        self._is_logged_in = False
        self._client = None
        self.set_localization({'soundcloud.explore': 30500,
                               'soundcloud.music.trending': 30501,
                               'soundcloud.audio.trending': 30502,
                               'soundcloud.music.genre': 30503,
                               'soundcloud.audio.genre': 30504,
                               'soundcloud.stream': 30505,
                               'soundcloud.playlists': 30506,
                               'soundcloud.following': 30507,
                               'soundcloud.follow': 30508,
                               'soundcloud.follower': 30509,
                               'soundcloud.likes': 30510,
                               'soundcloud.like': 30511,
                               'soundcloud.tracks': 30512,
                               'soundcloud.unfollow': 30513,
                               'soundcloud.unlike': 30514,
                               'soundcloud.people': 30515, })
        pass

    def get_client(self):
        if self._client is not None:
            return self._client

        from resources.lib import soundcloud
        access_manager = self.get_access_manager()
        if access_manager.has_login_credentials():
            username, password = access_manager.get_login_credentials()
            access_token = access_manager.get_access_token()

            # new credentials of no access_token
            if access_manager.is_new_login_credential() or not access_token:
                access_manager.update_access_token('')  # in case of an old access_token

                # create a new access_token
                self._client = soundcloud.Client(username=username, password=password, access_token='')
                access_token = self._client.update_access_token()
                access_manager.update_access_token(access_token)
                pass

            self._is_logged_in = access_token != ''
            self._client = soundcloud.Client(username=username, password=password, access_token=access_token)
        else:
            self._client = soundcloud.Client()

        return self._client

    def handle_exception(self, exception_to_handle):
        if isinstance(exception_to_handle, ClientException):
            if exception_to_handle.get_status_code() == 401:
                self.get_access_manager().update_access_token('')
                self.show_notification('Login Failed')
                self.get_settings().open_settings()
                return False
            pass

        return True

    def get_fanart(self):
        """
            This will return a darker and (with blur) fanart
            :return:
            """
        return self.create_resource_path('media', 'fanart.jpg')

    @kodimon.RegisterPath('^/play/$')
    def _play(self, path, params, re_match):
        track_id = params.get('id', '')
        if not track_id:
            raise kodimon.KodimonException('Missing if for audio file')

        json_data = self.get_client().get_track_url(track_id)
        location = json_data.get('location')
        if not location:
            raise kodimon.KodimonException("Could not get url for trask '%s'" % track_id)

        item = kodimon.AudioItem(track_id, location)
        return item

    def _do_mobile_collection(self, json_data, path, params):
        result = []

        # this result is not quite the collection we expected, but with some conversion we can use our
        # main routine for that.
        collection = json_data.get('collection', [])
        for collection_item in collection:
            # move user
            user = collection_item.get('_embedded', {}).get('user', {})
            collection_item['user'] = user

            # create track id of urn
            track_id = collection_item['urn'].split(':')[2]
            collection_item['id'] = track_id

            # is always a track
            collection_item['kind'] = 'track'

            track_item = self._do_item(collection_item, path)
            if track_item is not None:
                result.append(track_item)
            pass

        # test for next page
        page = int(params.get('page', 1))
        next_href = json_data.get('_links', {}).get('next', {}).get('href', '')
        if next_href and len(result) > 0:
            next_page_item = self.create_next_page_item(page,
                                                        path,
                                                        params)
            result.append(next_page_item)
            pass

        return result

    @kodimon.RegisterPath('^\/explore\/trending\/((?P<category>\w+)/)?$')
    def _on_explore_trending(self, path, params, re_match):
        result = []
        category = re_match.group('category')
        page = int(params.get('page', 1))
        json_data = self.call_function_cached(partial(self.get_client().get_trending, category=category, page=page),
                                              seconds=FunctionCache.ONE_HOUR)
        result = self._do_mobile_collection(json_data, path, params)

        return result

    @kodimon.RegisterPath('^\/explore\/genre\/((?P<category>\w+)\/)((?P<genre>.+)\/)?$')
    def _on_explore_genre(self, path, params, re_match):
        result = []

        genre = re_match.group('genre')
        if not genre:
            json_data = self.call_function_cached(partial(self.get_client().get_categories), seconds=FunctionCache.ONE_DAY)
            category = re_match.group('category')
            genres = json_data.get(category, [])
            for genre in genres:
                title = genre['title']
                genre_item = DirectoryItem(title,
                                           self.create_uri(['explore', 'genre', category, title]))
                genre_item.set_fanart(self.get_fanart())
                result.append(genre_item)
                pass
        else:
            page = int(params.get('page', 1))
            json_data = self.call_function_cached(partial(self.get_client().get_genre, genre=genre, page=page),
                                                  seconds=FunctionCache.ONE_HOUR)
            result = self._do_mobile_collection(json_data, path, params)
            pass

        return result

    @kodimon.RegisterPath('^\/explore\/?$')
    def _on_explore(self, path, params, re_match):
        result = []

        # trending music
        music_trending_item = DirectoryItem(self.localize('soundcloud.music.trending'),
                                            self.create_uri(['explore', 'trending', 'music']),
                                            image=self.create_resource_path('media', 'music.png'))
        music_trending_item.set_fanart(self.get_fanart())
        result.append(music_trending_item)

        # trending audio
        audio_trending_item = DirectoryItem(self.localize('soundcloud.audio.trending'),
                                            self.create_uri(['explore', 'trending', 'audio']),
                                            image=self.create_resource_path('media', 'audio.png'))
        audio_trending_item.set_fanart(self.get_fanart())
        result.append(audio_trending_item)

        # genre music
        music_genre_item = DirectoryItem(self.localize('soundcloud.music.genre'),
                                         self.create_uri(['explore', 'genre', 'music']),
                                         image=self.create_resource_path('media', 'music.png'))
        music_genre_item.set_fanart(self.get_fanart())
        result.append(music_genre_item)

        # genre audio
        audio_genre_item = DirectoryItem(self.localize('soundcloud.audio.genre'),
                                         self.create_uri(['explore', 'genre', 'audio']),
                                         image=self.create_resource_path('media', 'audio.png'))
        audio_genre_item.set_fanart(self.get_fanart())
        result.append(audio_genre_item)

        return result

    @kodimon.RegisterPath('^\/stream\/$')
    def _on_stream(self, path, params, re_match):
        result = []

        cursor = params.get('cursor', None)
        json_data = self.get_client().get_stream(page_cursor=cursor)
        result = self._do_collection(json_data, path, params)
        return result

    @kodimon.RegisterPath('^\/user/tracks\/(?P<user_id>.+)/$')
    def _on_tracks(self, path, params, re_match):
        result = []

        user_id = re_match.group('user_id')
        page = int(params.get('page', 1))

        json_data = self.call_function_cached(partial(self.get_client().get_user, user_id), seconds=FunctionCache.ONE_DAY)
        user_image = json_data.get('avatar_url', '')
        user_image = self._get_hires_image(user_image)

        if page == 1:
            # playlists
            playlists_item = DirectoryItem(self.localize('soundcloud.playlists'),
                                           self.create_uri(['user/playlists', user_id]),
                                           image=user_image)
            playlists_item.set_fanart(self.get_fanart())
            result.append(playlists_item)

            # likes
            likes_item = DirectoryItem(self.localize('soundcloud.likes'),
                                       self.create_uri(['user/favorites', user_id]),
                                       image=user_image)
            likes_item.set_fanart(self.get_fanart())
            result.append(likes_item)

            # following
            following_item = DirectoryItem(self.localize('soundcloud.following'),
                                           self.create_uri(['user/following', user_id]),
                                           image=user_image)
            following_item.set_fanart(self.get_fanart())
            result.append(following_item)

            # follower
            follower_item = DirectoryItem(self.localize('soundcloud.follower'),
                                          self.create_uri(['user/follower', user_id]),
                                          image=user_image)
            follower_item.set_fanart(self.get_fanart())
            result.append(follower_item)
            pass

        json_data = self.call_function_cached(partial(self.get_client().get_tracks, user_id, page=page),
                                              seconds=FunctionCache.ONE_MINUTE * 10)

        result.extend(self._do_collection(json_data, path, params))
        return result

    @kodimon.RegisterPath('^\/playlist\/(?P<playlist_id>.+)/$')
    def _on_playlist(self, path, params, re_match):
        result = []

        playlist_id = re_match.group('playlist_id')
        json_data = self.call_function_cached(partial(self.get_client().get_playlist, playlist_id),
                                              seconds=FunctionCache.ONE_MINUTE)
        tracks = json_data['tracks']
        track_number = 1
        for track in tracks:
            track_item = self._do_item(track, path)

            # set the name of the playlist for the albumname
            track_item.set_album_name(json_data['title'])

            # based on the position in the playlist we add a track number
            track_item.set_track_number(track_number)
            result.append(track_item)
            track_number += 1
            pass

        return result

    @kodimon.RegisterPath('^\/user/playlists\/(?P<user_id>.+)/$')
    def _on_playlists(self, path, params, re_match):
        user_id = re_match.group('user_id')
        page = params.get('page', 1)
        json_data = self.call_function_cached(partial(self.get_client().get_playlists, user_id, page=page),
                                              seconds=FunctionCache.ONE_MINUTE)
        return self._do_collection(json_data, path, params)

    @kodimon.RegisterPath('^\/user/following\/(?P<user_id>.+)/$')
    def _on_following(self, path, params, re_match):
        user_id = re_match.group('user_id')
        page = params.get('page', 1)
        json_data = self.call_function_cached(partial(self.get_client().get_following, user_id, page=page),
                                              seconds=FunctionCache.ONE_MINUTE)
        return self._do_collection(json_data, path, params)

    @kodimon.RegisterPath('^\/user/follower\/(?P<user_id>.+)/$')
    def _on_follower(self, path, params, re_match):
        user_id = re_match.group('user_id')
        page = params.get('page', 1)
        json_data = self.call_function_cached(partial(self.get_client().get_follower, user_id, page=page),
                                              seconds=FunctionCache.ONE_MINUTE)
        return self._do_collection(json_data, path, params)

    @kodimon.RegisterPath('^\/follow\/(?P<user_id>.+)/$')
    def _on_follow(self, path, params, re_match):
        user_id = re_match.group('user_id')
        follow = params.get('follow', '') == '1'
        json_data = self.get_client().follow_user(user_id, follow)

        return True

    @kodimon.RegisterPath('^\/like\/(?P<category>\w+)\/(?P<content_id>.+)/$')
    def _on_like(self, path, params, re_match):
        content_id = re_match.group('content_id')
        category = re_match.group('category')
        like = params.get('like', '') == '1'

        if category == 'track':
            json_data = self.get_client().like_track(content_id, like)
        elif category == 'playlist':
            json_data = self.get_client().like_playlist(content_id, like)
        else:
            raise KodimonException("Unknown category '%s' in 'on_like'" % category)

        if not like:
            self.refresh_container()
            pass

        return True

    @kodimon.RegisterPath('^\/user/favorites\/(?P<user_id>.+)/$')
    def _on_favorites(self, path, params, re_match):
        user_id = re_match.group('user_id')

        # We use an API of th APP, this API only work with an user id. In the case of 'me' we gave to get our own
        # user id to use this function.
        if user_id == 'me':
            json_data = self.call_function_cached(partial(self.get_client().get_user, 'me'),
                                                  seconds=FunctionCache.ONE_MINUTE * 10)
            user_id = json_data['id']
            pass

        page = params.get('page', 1)
        # do not cache: in case of adding or deleting content
        json_data = self.get_client().get_likes(user_id, page=page)
        return self._do_collection(json_data, path, params)

    def on_search(self, search_text, path, params, re_match):
        result = []
        page = int(params.get('page', 1))
        category = params.get('category', 'sounds')

        if page == 1 and category == 'sounds':
            people_params = {}
            people_params.update(params)
            people_params['category'] = 'people'
            people_item = DirectoryItem(self.localize('soundcloud.people'),
                                        self.create_uri(path, people_params),
                                        image=self.create_resource_path('media', 'users.png'))
            people_item.set_fanart(self.get_fanart())
            result.append(people_item)

            playlist_params = {}
            playlist_params.update(params)
            playlist_params['category'] = 'sets'
            playlist_item = DirectoryItem(self.localize('soundcloud.playlists'),
                                        self.create_uri(path, playlist_params),
                                        image=self.create_resource_path('media', 'playlists.png'))
            playlist_item.set_fanart(self.get_fanart())
            result.append(playlist_item)
            pass

        json_data = self.call_function_cached(partial(self.get_client().search, search_text, category=category, page=page),
                                              seconds=FunctionCache.ONE_MINUTE)
        result.extend(self._do_collection(json_data, path, params))
        return result

    def on_root(self, path, params, re_match):
        result = []

        self.get_client()

        # is logged in?
        if self._is_logged_in:
            # track
            json_data = self.get_client().get_user('me')
            me_item = self._do_item(json_data, path)
            result.append(me_item)

            # stream
            stream_item = DirectoryItem(self.localize('soundcloud.stream'),
                                        self.create_uri(['stream']),
                                        image=self.create_resource_path('media', 'stream.png'))
            stream_item.set_fanart(self.get_fanart())
            result.append(stream_item)
            pass

        # search
        search_item = DirectoryItem(self.localize(self.LOCAL_SEARCH),
                                    self.create_uri([self.PATH_SEARCH, 'list']),
                                    image=self.create_resource_path('media', 'search.png'))
        search_item.set_fanart(self.get_fanart())
        result.append(search_item)

        # explore
        explore_item = DirectoryItem(self.localize('soundcloud.explore'),
                                     self.create_uri('explore'),
                                     image=self.create_resource_path('media', 'explore.png'))
        explore_item.set_fanart(self.get_fanart())
        result.append(explore_item)

        return result

    def _do_collection(self, json_data, path, params):
        self.set_content_type(constants.CONTENT_TYPE_SONGS)

        """
            Helper function to display the items of a collection
            :param json_data:
            :param path:
            :param params:
            :return:
            """
        result = []

        collection = json_data.get('collection', [])
        for collection_item in collection:
            # test if we have an 'origin' tag. If so we are in the activities
            item = collection_item.get('origin', collection_item)
            base_item = self._do_item(item, path)
            if base_item is not None:
                result.append(base_item)
                pass
            pass

        # test for next page
        next_href = json_data.get('next_href', '')
        re_match = re.match('.*cursor\=(?P<cursor>[a-z0-9-]+).*', next_href)
        if re_match:
            params['cursor'] = re_match.group('cursor')
            pass

        page = int(params.get('page', 1))
        if next_href and len(collection) > 0:
            next_page_item = self.create_next_page_item(page,
                                                        path,
                                                        params)
            result.append(next_page_item)
            pass

        return result

    def _get_hires_image(self, url):
        return re.sub('(.*)(-large.jpg\.*)(\?.*)?', r'\1-t500x500.jpg', url)

    def _do_item(self, json_item, path):
        def _get_track_year(collection_item_json):
            # this would be the default info, but is mostly not set :(
            year = collection_item_json.get('release_year', '')
            if year:
                return year

            # we use a fallback.
            # created_at=2013/03/24 00:32:01 +0000
            re_match = re.match('(?P<year>\d{4})(.*)', collection_item_json.get('created_at', ''))
            if re_match:
                year = re_match.group('year')
                if year:
                    return year
                pass

            return ''

        def _get_image(json_data):
            image_url = json_data.get('artwork_url', '')

            # test avatar image
            if not image_url:
                image_url = json_data.get('avatar_url', '')

            # test tracks (used for playlists)
            if not image_url:
                tracks = json_data.get('tracks', [])
                if len(tracks) > 0:
                    return _get_image(tracks[0])

                # fall back is the user avatar (at least)
                image_url = json_data.get('user', {}).get('avatar_url', '')
                pass

            # try to convert the image to 500x500 pixel
            return self._get_hires_image(image_url)

        kind = json_item.get('kind', '')
        if kind == 'playlist':
            playlist_item = DirectoryItem(json_item['title'],
                                          self.create_uri(['playlist', unicode(json_item['id'])]),
                                          image=_get_image(json_item))
            playlist_item.set_fanart(self.get_fanart())

            if path == '/user/favorites/me/':
                context_menu = [contextmenu.create_run_plugin(self.get_plugin(),
                                                              self.localize('soundcloud.unlike'),
                                                              ['like/playlist', unicode(json_item['id'])], {'like': '0'})]
            else:
                context_menu = [contextmenu.create_run_plugin(self.get_plugin(),
                                                              self.localize('soundcloud.like'),
                                                              ['like/playlist', unicode(json_item['id'])], {'like': '1'})]

            playlist_item.set_context_menu(context_menu)
            return playlist_item
        elif kind == 'user':
            username = json_item['username']
            user_id = unicode(json_item['id'])
            if path == '/':
                user_id = 'me'
                username = '[B]' + username + '[/B]'
                pass
            user_item = DirectoryItem(username,
                                      self.create_uri(['user/tracks', user_id]),
                                      image=_get_image(json_item))
            user_item.set_fanart(self.get_fanart())

            if path == '/user/following/me/':
                context_menu = [contextmenu.create_run_plugin(self.get_plugin(),
                                                              self.localize('soundcloud.unfollow'),
                                                              ['follow', unicode(json_item['id'])], {'follow': '0'})]
            else:
                context_menu = [contextmenu.create_run_plugin(self.get_plugin(),
                                                              self.localize('soundcloud.follow'),
                                                              ['follow', unicode(json_item['id'])], {'follow': '1'})]
                pass
            user_item.set_context_menu(context_menu)
            return user_item
        elif kind == 'track':
            title = json_item['title']
            track_item = AudioItem(title,
                                   self.create_uri('play', {'id': unicode(json_item['id'])}),
                                   image=_get_image(json_item))
            track_item.set_fanart(self.get_fanart())

            # title
            track_item.set_title(title)

            # genre
            track_item.set_genre(json_item.get('genre', ''))

            # duration
            track_item.set_duration_in_milli_seconds(json_item.get('duration', 0))

            # artist
            track_item.set_artist_name(json_item.get('user', {}).get('username', ''))

            # year
            track_item.set_year(_get_track_year(json_item))

            if path == '/user/favorites/me/':
                context_menu = [contextmenu.create_run_plugin(self.get_plugin(),
                                                              self.localize('soundcloud.unlike'),
                                                              ['like/track', unicode(json_item['id'])], {'like': '0'})]
            else:
                context_menu = [contextmenu.create_run_plugin(self.get_plugin(),
                                                              self.localize('soundcloud.like'),
                                                              ['like/track', unicode(json_item['id'])], {'like': '1'})]
            track_item.set_context_menu(context_menu)

            return track_item
        elif kind == 'like':
            # A like has 'playlist' or 'track' so we find one of them and call this routine again, because the
            # data is same.
            test_playlist = json_item.get('playlist', None)
            if test_playlist is not None:
                return self._do_item(test_playlist, path)

            test_track = json_item.get('track', None)
            if test_track is not None:
                return self._do_item(test_track, path)
            pass
        elif kind == 'group':
            # at the moment we don't support groups
            """
            group_item = DirectoryItem('Group-Dummy',
                                       '')
            return group_item
            """
            return None

        raise KodimonException("Unknown kind of item '%s'" % kind)

    pass
