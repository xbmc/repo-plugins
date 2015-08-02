__author__ = 'bromix'

from resources.lib import nightcrawler
from resources.lib.nightcrawler.exception import ProviderException
from .client import Client


class Provider(nightcrawler.Provider):
    SOUNDCLOUD_LOCAL_STREAM = 30505
    SOUNDCLOUD_LOCAL_EXPLORE = 30500
    SOUNDCLOUD_LOCAL_TRACKS = 30512
    SOUNDCLOUD_LOCAL_RECOMMENDED = 30517
    SOUNDCLOUD_LOCAL_GO_TO_USER = 30516
    SOUNDCLOUD_LOCAL_PLAYLISTS = 30506
    SOUNDCLOUD_LOCAL_PEOPLE = 30515
    SOUNDCLOUD_LOCAL_LIKES = 30510
    SOUNDCLOUD_LOCAL_FOLLOWING = 30507
    SOUNDCLOUD_LOCAL_FOLLOWER = 30509
    SOUNDCLOUD_LOCAL_LIKE = 30511
    SOUNDCLOUD_LOCAL_UNLIKE = 30514
    SOUNDCLOUD_LOCAL_FOLLOW = 30508
    SOUNDCLOUD_LOCAL_UNFOLLOW = 30513

    SOUNDCLOUD_LOCAL_MUSIC_TRENDING = 30501
    SOUNDCLOUD_LOCAL_AUDIO_TRENDING = 30502
    SOUNDCLOUD_LOCAL_MUSIC_GENRE = 30503
    SOUNDCLOUD_LOCAL_AUDIO_GENRE = 30504

    SOUNDCLOUD_LOCAL_SETUP_LOGIN = 30519

    def __init__(self):
        nightcrawler.Provider.__init__(self)
        self._client = None
        pass

    def on_setup(self, context, mode):
        if mode == 'content-type':
            return ['default', 'songs', 'artists', 'albums']

        if mode == 'setup':
            if not context.get_ui().on_yes_no_input(context.get_name(),
                                                    context.localize(self.SOUNDCLOUD_LOCAL_SETUP_LOGIN)):
                return

            context.get_ui().open_settings();
            pass

        return None

    def handle_exception(self, context, exception_to_handle):
        if isinstance(exception_to_handle, nightcrawler.CredentialsException):
            context.get_function_cache().clear()
            context.get_access_manager().remove_login_credentials()
            context.get_ui().show_notification(exception_to_handle.get_message(),
                                               header=context.localize(self.LOCAL_LOGIN_FAILED))
            context.get_ui().open_settings()
            return False

        return True

    def get_fanart(self, context):
        if context.get_settings().get_bool('soundcloud.fanart_dark.show', True):
            return context.create_resource_path('media/fanart_dark.jpg')
        return context.create_resource_path('media/fanart.jpg')

    def get_client(self, context):
        def _login(username, password):
            return Client().login(username, password)

        if self._client:
            return self._client

        access_data = context.get_access_manager().do_login(_login)
        items_per_page = context.get_settings().get_items_per_page()
        self._client = Client(access_token=access_data.get('access_token', ''), items_per_page=items_per_page)
        return self._client

    def process_result(self, context, result):
        client = self.get_client(context)

        items = []
        path = context.get_path()
        for item in result['items']:
            context_menu = []
            item_type = item['type']

            if item_type == 'audio':
                # playback uri
                item['uri'] = context.create_uri('play', {'audio_id': unicode(item['id'])})

                # recommended tracks
                context_menu.append((context.localize(self.SOUNDCLOUD_LOCAL_RECOMMENDED),
                                     'Container.Update(%s)' % context.create_uri(
                                         '/explore/recommended/tracks/%s' % unicode(item['id']))))

                # like/unlike a track
                if client.get_access_token():
                    if path == '/user/favorites/me/':
                        context_menu.append((context.localize(self.SOUNDCLOUD_LOCAL_UNLIKE),
                                             'RunPlugin(%s)' % context.create_uri('like/track/%s' % unicode(item['id']),
                                                                                  {'like': '0'})))
                        pass
                    else:
                        context_menu.append((context.localize(self.SOUNDCLOUD_LOCAL_LIKE),
                                             'RunPlugin(%s)' % context.create_uri('like/track/%s' % unicode(item['id']),
                                                                                  {'like': '1'})))
                        pass
                    pass

                # go to user
                username = nightcrawler.utils.strings.to_unicode(item['user']['username'])
                user_id = nightcrawler.utils.strings.to_unicode(item['user']['id'])
                if path != '/user/tracks/%s/' % user_id:
                    context_menu.append((
                        context.localize(self.SOUNDCLOUD_LOCAL_GO_TO_USER) % ('[B]%s[/B]' % username),
                        'Container.Update(%s)' % context.create_uri('/user/tracks/%s/' % user_id)))
                    pass
                pass
            elif item_type == 'playlist':
                item['type'] = 'folder'
                item['uri'] = context.create_uri('/playlist/%s/' % item['id'])

                if client.get_access_token():
                    if path == '/user/favorites/me/':
                        context_menu = [(context.localize(self.SOUNDCLOUD_LOCAL_UNLIKE),
                                         'RunPlugin(%s)' % context.create_uri('like/playlist/%s' % unicode(item['id']),
                                                                              {'like': '0'}))]
                    else:
                        context_menu = [(context.localize(self.SOUNDCLOUD_LOCAL_LIKE),
                                         'RunPlugin(%s)' % context.create_uri('like/playlist/%s' % unicode(item['id']),
                                                                              {'like': '1'}))]
                        pass
                    pass
                pass
            elif item_type == 'artist':
                item['type'] = 'folder'
                item['uri'] = context.create_uri('/user/tracks/%s/' % item['id'])

                if client.get_access_token():
                    if path == '/user/following/me/':
                        context_menu = [(context.localize(self.SOUNDCLOUD_LOCAL_UNFOLLOW),
                                         'RunPlugin(%s)' % context.create_uri('follow/%s' % unicode(item['id']),
                                                                              {'follow': '0'}))]
                        pass
                    else:
                        context_menu = [(context.localize(self.SOUNDCLOUD_LOCAL_FOLLOW),
                                         'RunPlugin(%s)' % context.create_uri('follow/%s' % unicode(item['id']),
                                                                              {'follow': '1'}))]
                        pass
                    pass
                pass
            else:
                raise ProviderException('Unknown item type "%s"' % item_type)

            if context_menu:
                item['context-menu'] = {'items': context_menu}
                pass

            item['images']['fanart'] = self.get_fanart(context)
            items.append(item)
            pass

        # create next page item
        if result.get('continue', False):
            new_params = {}
            new_params.update(context.get_params())
            if 'cursor' in result:
                new_params['cursor'] = result['cursor']
                pass
            new_context = context.clone(new_params=new_params)
            items.append(nightcrawler.items.create_next_page_item(new_context, fanart=self.get_fanart(context)))
            pass
        return items

    @nightcrawler.register_path('/like/(?P<category>track|playlist)/(?P<content_id>.+)/')
    @nightcrawler.register_path_value('category', unicode)
    @nightcrawler.register_path_value('content_id', int)
    @nightcrawler.register_context_value('like', bool, required=True)
    def on_like(self, context, category, content_id, like):

        if category == 'track':
            json_data = self.get_client(context).like_track(content_id, like)
            pass
        elif category == 'playlist':
            json_data = self.get_client(context).like_playlist(content_id, like)
            pass
        else:
            raise ProviderException('Unknown category "%s" in "on_like"' % category)

        if not like:
            context.get_ui().refresh_container()
            pass

        return True

    @nightcrawler.register_path('/follow/(?P<user_id>.+)/')
    @nightcrawler.register_path_value('user_id', int)
    @nightcrawler.register_context_value('follow', bool, required=True)
    def _on_follow(self, context, user_id, follow):
        self.get_client(context).follow_user(user_id, follow)
        if not follow:
            context.get_ui().refresh_container()
            pass

        return True

    @nightcrawler.register_path('/play/')
    @nightcrawler.register_context_value('audio_id', int, alias='track_id', default=None)
    @nightcrawler.register_context_value('playlist_id', int, default=None)
    @nightcrawler.register_context_value('url', str, default='')
    def on_play(self, context, track_id, playlist_id, url):
        client = self.get_client(context)

        if track_id:
            track_item = client.get_track(track_id)
            url = client.get_track_url(track_id)
            track_item['uri'] = url
            return track_item

        if url:
            item = client.resolve_url(url)
            item_type = item['type']
            if item_type in ['audio', 'music']:
                return {'type': 'uri',
                        'uri': context.create_uri('/play/', {'audio_id': item['id']})}

            if item_type == 'playlist':
                return {'type': 'uri',
                        'uri': context.create_uri('/play/', {'playlist_id': item['id']})}

            raise ProviderException('Unknown item kind "%s"' % item_type)

        if playlist_id:
            tracks = client.get_playlist(playlist_id).get('items', [])
            if tracks:
                playlist = context.get_audio_playlist()
                playlist.clear()
                for track in tracks:
                    track['uri'] = context.create_uri('/play/', {'audio_id': track['id']})
                    playlist.add(track)
                    pass

                return tracks[0]

            raise ProviderException('No tracks found in playlist')

        return False

    @nightcrawler.register_context_value('category', unicode, default='sounds')
    @nightcrawler.register_context_value('page', int, default=1)
    def on_search(self, context, search_text, category, page):
        result = []

        # set the correct content type
        if category == 'sounds':
            context.set_content_type(context.CONTENT_TYPE_SONGS)
            pass
        elif category == 'sets':
            context.set_content_type(context.CONTENT_TYPE_ALBUMS)
            pass
        elif category == 'people':
            context.set_content_type(context.CONTENT_TYPE_ARTISTS)
            pass

        # first page of search
        if page == 1 and category == 'sounds':
            people_params = {}
            people_params.update(context.get_params())
            people_params['category'] = 'people'
            result.append({'type': 'folder',
                           'title': '[B]%s[/B]' % context.localize(self.SOUNDCLOUD_LOCAL_PEOPLE),
                           'uri': context.create_uri(context.get_path(), people_params),
                           'images': {'thumbnail': context.create_resource_path('media/users.png'),
                                      'fanart': self.get_fanart(context)}})

            playlist_params = {}
            playlist_params.update(context.get_params())
            playlist_params['category'] = 'sets'
            result.append({'type': 'folder',
                           'title': '[B]%s[/B]' % context.localize(self.SOUNDCLOUD_LOCAL_PLAYLISTS),
                           'uri': context.create_uri(context.get_path(), playlist_params),
                           'images': {'thumbnail': context.create_resource_path('media/playlists.png'),
                                      'fanart': self.get_fanart(context)}})

            pass

        search_result = context.cache_function(context.CACHE_ONE_MINUTE * 10, self.get_client(context).search,
                                               search_text, category, page=page)
        result.extend(self.process_result(context, search_result))
        return result

    @nightcrawler.register_path('/playlist/(?P<playlist_id>.+)/')
    @nightcrawler.register_path_value('playlist_id', int)
    def on_playlist(self, context, playlist_id):
        context.set_content_type(context.CONTENT_TYPE_SONGS)
        result = context.cache_function(context.CACHE_ONE_MINUTE * 5, self.get_client(context).get_playlist,
                                        playlist_id)
        return self.process_result(context, result)

    @nightcrawler.register_path('/user/playlists/(?P<user_id>.+)/')
    @nightcrawler.register_path_value('user_id', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_user_playlists(self, context, user_id, page):
        context.set_content_type(context.CONTENT_TYPE_ALBUMS)
        result = context.cache_function(context.CACHE_ONE_MINUTE * 5, self.get_client(context).get_playlists, user_id,
                                        page=page)
        return self.process_result(context, result)

    @nightcrawler.register_path('/user/following/(?P<user_id>.+)/')
    @nightcrawler.register_path_value('user_id', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_user_following(self, context, user_id, page):
        context.set_content_type(context.CONTENT_TYPE_ARTISTS)
        result = context.cache_function(context.CACHE_ONE_MINUTE * 5, self.get_client(context).get_following, user_id,
                                        page=page)
        return self.process_result(context, result)

    @nightcrawler.register_path('/user/follower/(?P<user_id>.+)/')
    @nightcrawler.register_path_value('user_id', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_user_follower(self, context, user_id, page):
        context.set_content_type(context.CONTENT_TYPE_ARTISTS)
        result = context.cache_function(context.CACHE_ONE_MINUTE * 5, self.get_client(context).get_follower, user_id,
                                        page=page)
        return self.process_result(context, result)

    @nightcrawler.register_path('^/user/favorites/(?P<user_id>.+)/')
    @nightcrawler.register_path_value('user_id', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_user_favorites(self, context, user_id, page):
        context.set_content_type(context.CONTENT_TYPE_SONGS)

        # We use an API of the APP, this API only work with an user id. In the case of 'me' we gave to get our own
        # user id to use this function.
        if user_id == 'me':
            json_data = context.cache_function(context.CACHE_ONE_MINUTE * 10, self.get_client(context).get_user, 'me')
            user_id = json_data['id']
            pass

        # do not cache: in case of adding or deleting content
        return self.process_result(context, self.get_client(context).get_likes(user_id, page=page))

    @nightcrawler.register_path('/user/tracks/(?P<user_id>.+)/')
    @nightcrawler.register_path_value('user_id', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_user_tracks(self, context, user_id, page):
        def _make_bold(_user_id, title):
            if _user_id != 'me':
                return '[B]%s[/B]' % title
            return title

        context.set_content_type(context.CONTENT_TYPE_SONGS)
        result = []

        # on the first page add some extra stuff to navigate to
        if page == 1:
            user_item = context.cache_function(context.CACHE_ONE_MINUTE * 10, self.get_client(context).get_user,
                                               user_id)
            user_image = user_item.get('images', {}).get('thumbnail')

            # playlists
            result.append({'type': 'folder',
                           'title': _make_bold(user_id, context.localize(self.SOUNDCLOUD_LOCAL_PLAYLISTS)),
                           'uri': context.create_uri('/user/playlists/%s' % user_id),
                           'images': {'thumbnail': user_image,
                                      'fanart': self.get_fanart(context)}})

            # likes
            result.append({'type': 'folder',
                           'title': _make_bold(user_id, context.localize(self.SOUNDCLOUD_LOCAL_LIKES)),
                           'uri': context.create_uri('/user/favorites/%s' % user_id),
                           'images': {'thumbnail': user_image,
                                      'fanart': self.get_fanart(context)}})

            # following
            result.append({'type': 'folder',
                           'title': _make_bold(user_id, context.localize(self.SOUNDCLOUD_LOCAL_FOLLOWING)),
                           'uri': context.create_uri('/user/following/%s' % user_id),
                           'images': {'thumbnail': user_image,
                                      'fanart': self.get_fanart(context)}})

            # follower
            result.append({'type': 'folder',
                           'title': _make_bold(user_id, context.localize(self.SOUNDCLOUD_LOCAL_FOLLOWER)),
                           'uri': context.create_uri('/user/follower/%s' % user_id),
                           'images': {'thumbnail': user_image,
                                      'fanart': self.get_fanart(context)}})
            pass

        tracks_result = context.cache_function(context.CACHE_ONE_MINUTE * 10, self.get_client(context).get_tracks,
                                               user_id, page=page)
        result.extend(self.process_result(context, tracks_result))
        return result

    @nightcrawler.register_path('/explore/recommended/tracks\/(?P<track_id>.+)/')
    @nightcrawler.register_path_value('track_id', int)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_explore_recommended_tracks(self, context, track_id, page):
        context.set_content_type(context.CONTENT_TYPE_SONGS)

        result = context.cache_function(context.CACHE_ONE_HOUR, self.get_client(context).get_recommended_for_track,
                                        track_id, page=page)
        return self.process_result(context, result)

    @nightcrawler.register_path('/explore/genre/(?P<category>music|audio)/(?P<genre>.*)/')
    @nightcrawler.register_path_value('category', unicode)
    @nightcrawler.register_path_value('genre', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_explore_genre_sub(self, context, category, genre, page):
        context.set_content_type(context.CONTENT_TYPE_SONGS)

        result = context.cache_function(context.CACHE_ONE_HOUR, self.get_client(context).get_genre, genre=genre,
                                        page=page)
        return self.process_result(context, result)

    @nightcrawler.register_path('/explore/genre/(?P<category>music|audio)/')
    @nightcrawler.register_path_value('category', unicode)
    def on_explore_genre(self, context, category):
        categories = context.cache_function(context.CACHE_ONE_HOUR, self.get_client(context).get_categories)
        items = categories.get(category, [])
        result = []
        for item in items:
            item.update({'uri': context.create_uri('/explore/genre/%s/%s/' % (category, item['title'])),
                         'images': {'fanart': self.get_fanart(context),
                                    'thumbnail': context.create_resource_path('media/%s.png' % category)}})
            result.append(item)
            pass

        return result

    @nightcrawler.register_path('/explore/trending/(?P<category>music|audio)/')
    @nightcrawler.register_path_value('category', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_explore_trending(self, context, category, page):
        context.set_content_type(context.CONTENT_TYPE_SONGS)

        result = context.cache_function(context.CACHE_ONE_HOUR, self.get_client(context).get_trending,
                                        category=category, page=page)
        return self.process_result(context, result)

    @nightcrawler.register_path('/explore/')
    def on_explore(self, context):
        result = []

        # trending music
        result.append({'type': 'folder',
                       'title': context.localize(self.SOUNDCLOUD_LOCAL_MUSIC_TRENDING),
                       'uri': context.create_uri('explore/trending/music'),
                       'images': {'thumbnail': context.create_resource_path('media/music.png'),
                                  'fanart': self.get_fanart(context)}})

        # trending audio
        result.append({'type': 'folder',
                       'title': context.localize(self.SOUNDCLOUD_LOCAL_AUDIO_TRENDING),
                       'uri': context.create_uri('explore/trending/audio'),
                       'images': {'thumbnail': context.create_resource_path('media/audio.png'),
                                  'fanart': self.get_fanart(context)}})

        # genre music
        result.append({'type': 'folder',
                       'title': context.localize(self.SOUNDCLOUD_LOCAL_MUSIC_GENRE),
                       'uri': context.create_uri('explore/genre/music'),
                       'images': {'thumbnail': context.create_resource_path('media/music.png'),
                                  'fanart': self.get_fanart(context)}})

        # genre audio
        result.append({'type': 'folder',
                       'title': context.localize(self.SOUNDCLOUD_LOCAL_AUDIO_GENRE),
                       'uri': context.create_uri('explore/genre/audio'),
                       'images': {'thumbnail': context.create_resource_path('media/audio.png'),
                                  'fanart': self.get_fanart(context)}})
        return result

    @nightcrawler.register_path('/stream/')
    @nightcrawler.register_context_value('cursor', unicode)
    @nightcrawler.register_context_value('page', int)
    def on_stream(self, context, cursor, page):
        context.set_content_type(context.CONTENT_TYPE_SONGS)

        result = context.cache_function(context.CACHE_ONE_MINUTE * 10, self.get_client(context).get_stream,
                                        page_cursor=cursor)
        return self.process_result(context, result)

    @nightcrawler.register_path('/')
    def on_root(self, context):
        result = []

        client = self.get_client(context)

        # if logged in provide some extra items
        if client.get_access_token():
            # track
            json_data = context.cache_function(context.CACHE_ONE_MINUTE * 10, self.get_client(context).get_user, 'me')
            json_data['id'] = 'me'
            result.extend(self.process_result(context, {'items': [json_data]}))

            # stream
            result.append({'type': 'folder',
                           'title': context.localize(self.SOUNDCLOUD_LOCAL_STREAM),
                           'uri': context.create_uri('stream'),
                           'images': {'thumbnail': context.create_resource_path('media/stream.png')}})
            pass

        # search
        result.append(nightcrawler.items.create_search_item(context, fanart=self.get_fanart(context)))

        # explore
        result.append({'type': 'folder',
                       'title': context.localize(self.SOUNDCLOUD_LOCAL_EXPLORE),
                       'uri': context.create_uri('explore'),
                       'images': {'thumbnail': context.create_resource_path('media/explore.png'),
                                  'fanart': self.get_fanart(context)}})
        return result

    pass
