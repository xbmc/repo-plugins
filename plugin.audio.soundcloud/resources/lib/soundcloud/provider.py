__author__ = 'bromix'

import re

from resources.lib.kodion.utils import FunctionCache
from resources.lib.kodion.items import DirectoryItem, AudioItem
from resources.lib import kodion
from resources.lib.soundcloud.client import ClientException
from .client import Client


class Provider(kodion.AbstractProvider):
    SETTINGS_USER_ID = 'soundcloud.user.id'

    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._is_logged_in = False
        self._client = None
        self._local_map.update(
            {'soundcloud.explore': 30500,
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
             'soundcloud.people': 30515,
             'soundcloud.user.go_to': 30516,
             'soundcloud.recommended': 30517}
        )
        pass

    def get_wizard_supported_views(self):
        return ['default', 'songs', 'artists', 'albums']

    def get_client(self, context):
        access_manager = context.get_access_manager()
        access_token = access_manager.get_access_token()
        if access_manager.is_new_login_credential() or not access_token:
            access_manager.update_access_token('')  # in case of an old access_token
            self._client = None
            pass

        if not self._client:
            items_per_page = context.get_settings().get_items_per_page()
            if access_manager.has_login_credentials():
                username, password = access_manager.get_login_credentials()
                access_token = access_manager.get_access_token()

                # create a new access_token
                if not access_token:
                    self._client = Client(username=username, password=password, access_token='',
                                          items_per_page=items_per_page)
                    access_token = self._client.update_access_token()
                    access_manager.update_access_token(access_token)
                    pass

                self._is_logged_in = access_token != ''
                self._client = Client(username=username, password=password, access_token=access_token,
                                      items_per_page=items_per_page)
            else:
                self._client = Client(items_per_page=items_per_page)
                pass
            pass

        return self._client

    def handle_exception(self, context, exception_to_handle):
        if isinstance(exception_to_handle, ClientException):
            if exception_to_handle.get_status_code() == 401:
                context.get_access_manager().update_access_token('')
                context.get_ui().show_notification('Login Failed')
                context.get_ui().open_settings()
                return False
            pass

        return True

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        if context.get_settings().get_bool('soundcloud.fanart_dark.show', True):
            return context.create_resource_path('media', 'fanart_dark.jpg')
        return context.create_resource_path('media', 'fanart.jpg')

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        params = context.get_params()
        url = params.get('url', '')
        audio_id = params.get('audio_id', '')

        client = self.get_client(context)
        result = None
        update_playlist = False
        if url and not audio_id:
            json_data = client.resolve_url(url)
            path = context.get_path()
            result = self._do_item(context, json_data, path, process_playlist=True)
            if isinstance(result, AudioItem):
                audio_id = json_data['id']
                update_playlist = True
                pass
            elif isinstance(result, list):
                playlist = context.get_audio_playlist()
                playlist.clear()
                for track in result:
                    playlist.add(track)
                    pass
                return result[0]
            pass
        elif audio_id:
            json_data = client.get_track(audio_id)
            path = context.get_path()
            result = self._do_item(context, json_data, path, process_playlist=True)
            pass
        else:
            raise kodion.KodionException("Audio ID or URL missing")

        json_data = client.get_track_url(audio_id)
        location = json_data.get('location')
        if not location:
            raise kodion.KodionException("Could not get url for track '%s'" % audio_id)

        result.set_uri(location.encode('utf-8'))
        if update_playlist:
            playlist = context.get_audio_playlist()
            playlist.clear()
            playlist.add(result)
            pass

        return result

    def _do_mobile_collection(self, context, json_data, path, params):
        result = []

        # this result is not quite the collection we expected, but with some conversion we can use our
        # main routine for that.
        collection = json_data.get('collection', [])
        for collection_item in collection:
            # move user
            user = collection_item.get('_embedded', {}).get('user', {})
            user_id = user['urn'].split(':')[2]
            collection_item['user'] = {'username': user['username'],
                                       'id': user_id}

            # create track id of urn
            track_id = collection_item['urn'].split(':')[2]
            collection_item['id'] = track_id

            # is always a track
            collection_item['kind'] = 'track'

            track_item = self._do_item(context, collection_item, path)
            if track_item is not None:
                result.append(track_item)
            pass

        page = int(params.get('page', 1))
        next_href = json_data.get('_links', {}).get('next', {}).get('href', '')
        if next_href and len(result) > 0:
            next_page_item = kodion.items.NextPageItem(context, page)
            next_page_item.set_fanart(self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    @kodion.RegisterProviderPath('^\/explore/recommended\/tracks\/(?P<track_id>.+)/$')
    def _on_explore_recommended_tracks(self, context, re_match):
        result = []

        track_id = re_match.group('track_id')
        params = context.get_params()
        page = int(params.get('page', 1))

        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR,
                                                     self.get_client(context).get_recommended_for_track,
                                                     track_id=track_id, page=page)
        path = context.get_path()
        result = self._do_collection(context, json_data, path, params)

        return result

    @kodion.RegisterProviderPath('^\/explore\/trending\/((?P<category>\w+)/)?$')
    def _on_explore_trending(self, context, re_match):
        result = []
        category = re_match.group('category')
        params = context.get_params()
        page = int(params.get('page', 1))
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, self.get_client(context).get_trending,
                                                     category=category, page=page)
        path = context.get_path()
        result = self._do_mobile_collection(context, json_data, path, params)

        if category:
            context.set_content_type(kodion.constants.content_type.SONGS)
            pass

        return result

    @kodion.RegisterProviderPath('^\/explore\/genre\/((?P<category>\w+)\/)((?P<genre>.+)\/)?$')
    def _on_explore_genre(self, context, re_match):
        result = []

        genre = re_match.group('genre')
        if not genre:
            json_data = context.get_function_cache().get(FunctionCache.ONE_DAY, self.get_client(context).get_categories)
            category = re_match.group('category')
            genres = json_data.get(category, [])
            for genre in genres:
                title = genre['title']
                genre_item = DirectoryItem(title,
                                           context.create_uri(['explore', 'genre', category, title]))
                genre_item.set_fanart(self.get_fanart(context))
                result.append(genre_item)
                pass
        else:
            context.set_content_type(kodion.constants.content_type.SONGS)
            params = context.get_params()
            page = int(params.get('page', 1))
            json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, self.get_client(context).get_genre,
                                                         genre=genre,
                                                         page=page)

            path = context.get_path()
            result = self._do_mobile_collection(context, json_data, path, params)
            pass

        return result

    @kodion.RegisterProviderPath('^\/explore\/?$')
    def _on_explore(self, context, re_match):
        result = []

        # trending music
        music_trending_item = DirectoryItem(context.localize(self._local_map['soundcloud.music.trending']),
                                            context.create_uri(['explore', 'trending', 'music']),
                                            image=context.create_resource_path('media', 'music.png'))
        music_trending_item.set_fanart(self.get_fanart(context))
        result.append(music_trending_item)

        # trending audio
        audio_trending_item = DirectoryItem(context.localize(self._local_map['soundcloud.audio.trending']),
                                            context.create_uri(['explore', 'trending', 'audio']),
                                            image=context.create_resource_path('media', 'audio.png'))
        audio_trending_item.set_fanart(self.get_fanart(context))
        result.append(audio_trending_item)

        # genre music
        music_genre_item = DirectoryItem(context.localize(self._local_map['soundcloud.music.genre']),
                                         context.create_uri(['explore', 'genre', 'music']),
                                         image=context.create_resource_path('media', 'music.png'))
        music_genre_item.set_fanart(self.get_fanart(context))
        result.append(music_genre_item)

        # genre audio
        audio_genre_item = DirectoryItem(context.localize(self._local_map['soundcloud.audio.genre']),
                                         context.create_uri(['explore', 'genre', 'audio']),
                                         image=context.create_resource_path('media', 'audio.png'))
        audio_genre_item.set_fanart(self.get_fanart(context))
        result.append(audio_genre_item)

        return result

    @kodion.RegisterProviderPath('^\/stream\/$')
    def _on_stream(self, context, re_match):
        result = []

        params = context.get_params()
        cursor = params.get('cursor', None)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 5, self.get_client(context).get_stream,
                                                     page_cursor=cursor)
        path = context.get_path()
        result = self._do_collection(context, json_data, path, params)
        return result

    @kodion.RegisterProviderPath('^\/user/tracks\/(?P<user_id>.+)/$')
    def _on_tracks(self, context, re_match):
        result = []

        user_id = re_match.group('user_id')
        params = context.get_params()
        page = int(params.get('page', 1))

        json_data = context.get_function_cache().get(FunctionCache.ONE_DAY, self.get_client(context).get_user, user_id)
        user_image = json_data.get('avatar_url', '')
        user_image = self._get_hires_image(user_image)

        if page == 1:
            # playlists
            playlists_item = DirectoryItem(context.localize(self._local_map['soundcloud.playlists']),
                                           context.create_uri(['user/playlists', user_id]),
                                           image=user_image)
            playlists_item.set_fanart(self.get_fanart(context))
            result.append(playlists_item)

            # likes
            likes_item = DirectoryItem(context.localize(self._local_map['soundcloud.likes']),
                                       context.create_uri(['user/favorites', user_id]),
                                       image=user_image)
            likes_item.set_fanart(self.get_fanart(context))
            result.append(likes_item)

            # following
            following_item = DirectoryItem(context.localize(self._local_map['soundcloud.following']),
                                           context.create_uri(['user/following', user_id]),
                                           image=user_image)
            following_item.set_fanart(self.get_fanart(context))
            result.append(following_item)

            # follower
            follower_item = DirectoryItem(context.localize(self._local_map['soundcloud.follower']),
                                          context.create_uri(['user/follower', user_id]),
                                          image=user_image)
            follower_item.set_fanart(self.get_fanart(context))
            result.append(follower_item)
            pass

        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, self.get_client(context).get_tracks,
                                                     user_id,
                                                     page=page)
        path = context.get_path()
        result.extend(self._do_collection(context, json_data, path, params))
        return result

    @kodion.RegisterProviderPath('^\/playlist\/(?P<playlist_id>.+)/$')
    def _on_playlist(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.SONGS)
        result = []

        playlist_id = re_match.group('playlist_id')
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self.get_client(context).get_playlist,
                                                     playlist_id)

        path = context.get_path()
        result.extend(self._do_item(context, json_data, path, process_playlist=True))
        return result

    @kodion.RegisterProviderPath('^\/user/playlists\/(?P<user_id>.+)/$')
    def _on_playlists(self, context, re_match):
        user_id = re_match.group('user_id')
        params = context.get_params()
        page = params.get('page', 1)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self.get_client(context).get_playlists,
                                                     user_id,
                                                     page=page)
        path = context.get_path()
        return self._do_collection(context, json_data, path, params, content_type=kodion.constants.content_type.ALBUMS)

    @kodion.RegisterProviderPath('^\/user/following\/(?P<user_id>.+)/$')
    def _on_following(self, context, re_match):
        user_id = re_match.group('user_id')
        params = context.get_params()
        page = params.get('page', 1)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self.get_client(context).get_following,
                                                     user_id,
                                                     page=page)
        path = context.get_path()
        return self._do_collection(context, json_data, path, params, content_type=kodion.constants.content_type.ARTISTS)

    @kodion.RegisterProviderPath('^\/user/follower\/(?P<user_id>.+)/$')
    def _on_follower(self, context, re_match):
        user_id = re_match.group('user_id')
        params = context.get_params()
        page = params.get('page', 1)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self.get_client(context).get_follower,
                                                     user_id,
                                                     page=page)
        path = context.get_path()
        return self._do_collection(context, json_data, path, params, content_type=kodion.constants.content_type.ARTISTS)

    @kodion.RegisterProviderPath('^\/follow\/(?P<user_id>.+)/$')
    def _on_follow(self, context, re_match):
        user_id = re_match.group('user_id')
        params = context.get_params()
        follow = params.get('follow', '') == '1'
        json_data = self.get_client(context).follow_user(user_id, follow)

        return True

    @kodion.RegisterProviderPath('^\/like\/(?P<category>\w+)\/(?P<content_id>.+)/$')
    def _on_like(self, context, re_match):
        content_id = re_match.group('content_id')
        category = re_match.group('category')
        params = context.get_params()
        like = params.get('like', '') == '1'

        if category == 'track':
            json_data = self.get_client(context).like_track(content_id, like)
        elif category == 'playlist':
            json_data = self.get_client(context).like_playlist(content_id, like)
        else:
            raise kodion.KodionException("Unknown category '%s' in 'on_like'" % category)

        if not like:
            context.get_ui().refresh_container()
            pass

        return True

    @kodion.RegisterProviderPath('^\/user/favorites\/(?P<user_id>.+)/$')
    def _on_favorites(self, context, re_match):
        user_id = re_match.group('user_id')

        # We use an API of th APP, this API only work with an user id. In the case of 'me' we gave to get our own
        # user id to use this function.
        if user_id == 'me':
            json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10,
                                                         self.get_client(context).get_user,
                                                         'me')
            user_id = json_data['id']
            pass

        params = context.get_params()
        page = params.get('page', 1)
        # do not cache: in case of adding or deleting content
        json_data = self.get_client(context).get_likes(user_id, page=page)
        path = context.get_path()
        return self._do_collection(context, json_data, path, params)

    def on_search(self, search_text, context, re_match):
        result = []
        params = context.get_params()
        page = int(params.get('page', 1))
        category = params.get('category', 'sounds')

        path = context.get_path()
        if page == 1 and category == 'sounds':
            people_params = {}
            people_params.update(params)
            people_params['category'] = 'people'
            people_item = DirectoryItem('[B]' + context.localize(self._local_map['soundcloud.people']) + '[/B]',
                                        context.create_uri(path, people_params),
                                        image=context.create_resource_path('media', 'users.png'))
            people_item.set_fanart(self.get_fanart(context))
            result.append(people_item)

            playlist_params = {}
            playlist_params.update(params)
            playlist_params['category'] = 'sets'
            playlist_item = DirectoryItem('[B]' + context.localize(self._local_map['soundcloud.playlists']) + '[/B]',
                                          context.create_uri(path, playlist_params),
                                          image=context.create_resource_path('media', 'playlists.png'))
            playlist_item.set_fanart(self.get_fanart(context))
            result.append(playlist_item)
            pass

        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self.get_client(context).search,
                                                     search_text,
                                                     category=category, page=page)
        result.extend(self._do_collection(context, json_data, path, params))
        return result

    def on_root(self, context, re_match):
        path = context.get_path()
        result = []

        self.get_client(context)

        # is logged in?
        if self._is_logged_in:
            # track
            json_data = self.get_client(context).get_user('me')
            me_item = self._do_item(context, json_data, path)
            result.append(me_item)

            # stream
            stream_item = DirectoryItem(context.localize(self._local_map['soundcloud.stream']),
                                        context.create_uri(['stream']),
                                        image=context.create_resource_path('media', 'stream.png'))
            stream_item.set_fanart(self.get_fanart(context))
            result.append(stream_item)
            pass

        # search
        search_item = DirectoryItem(context.localize(kodion.constants.localize.SEARCH),
                                    context.create_uri([kodion.constants.paths.SEARCH, 'list']),
                                    image=context.create_resource_path('media', 'search.png'))
        search_item.set_fanart(self.get_fanart(context))
        result.append(search_item)

        # explore
        explore_item = DirectoryItem(context.localize(self._local_map['soundcloud.explore']),
                                     context.create_uri('explore'),
                                     image=context.create_resource_path('media', 'explore.png'))
        explore_item.set_fanart(self.get_fanart(context))
        result.append(explore_item)

        return result

    def _do_collection(self, context, json_data, path, params, content_type=kodion.constants.content_type.SONGS):
        context.set_content_type(content_type)

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
            base_item = self._do_item(context, item, path)
            if base_item is not None:
                result.append(base_item)
                pass
            pass

        # test for next page
        next_href = json_data.get('next_href', '')
        if next_href:
            re_match = re.match(r'.*cursor=(?P<cursor>[a-z0-9-]+).*', next_href)
            if re_match:
                params['cursor'] = re_match.group('cursor')
                pass
            pass

        page = int(params.get('page', 1))
        if next_href and len(collection) > 0:
            next_page_item = kodion.items.NextPageItem(context, page)
            next_page_item.set_fanart(self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    def _get_hires_image(self, url):
        return re.sub('(.*)(-large.jpg\.*)(\?.*)?', r'\1-t300x300.jpg', url)

    def _do_item(self, context, json_item, path, process_playlist=False):
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

            return self._get_hires_image(image_url)

        kind = json_item.get('kind', '')
        if kind == 'playlist':
            if process_playlist:
                result = []
                tracks = json_item['tracks']
                track_number = 1
                for track in tracks:
                    path = context.get_path()
                    track_item = self._do_item(context, track, path)

                    # set the name of the playlist for the albumname
                    track_item.set_album_name(json_item['title'])

                    # based on the position in the playlist we add a track number
                    track_item.set_track_number(track_number)
                    result.append(track_item)
                    track_number += 1
                    pass
                return result
            else:
                playlist_item = DirectoryItem(json_item['title'],
                                              context.create_uri(['playlist', unicode(json_item['id'])]),
                                              image=_get_image(json_item))
                playlist_item.set_fanart(self.get_fanart(context))

                if path == '/user/favorites/me/':
                    context_menu = [(context.localize(self._local_map['soundcloud.unlike']),
                                     'RunPlugin(%s)' % context.create_uri(['like/playlist', unicode(json_item['id'])],
                                                                          {'like': '0'}))]
                else:
                    context_menu = [(context.localize(self._local_map['soundcloud.like']),
                                     'RunPlugin(%s)' % context.create_uri(['like/playlist', unicode(json_item['id'])],
                                                                          {'like': '1'}))]

                playlist_item.set_context_menu(context_menu)
                return playlist_item
            pass
        elif kind == 'user':
            username = json_item['username']
            user_id = unicode(json_item['id'])
            if path == '/':
                user_id = 'me'
                username = '[B]' + username + '[/B]'
                pass
            user_item = DirectoryItem(username,
                                      context.create_uri(['user/tracks', user_id]),
                                      image=_get_image(json_item))
            user_item.set_fanart(self.get_fanart(context))

            if path == '/user/following/me/':
                context_menu = [(context.localize(self._local_map['soundcloud.unfollow']),
                                 'RunPlugin(%s)' % context.create_uri(['follow', unicode(json_item['id'])],
                                                                      {'follow': '0'}))]
                pass
            else:
                context_menu = [(context.localize(self._local_map['soundcloud.follow']),
                                 'RunPlugin(%s)' % context.create_uri(['follow', unicode(json_item['id'])],
                                                                      {'follow': '1'}))]
                pass
            user_item.set_context_menu(context_menu)
            return user_item
        elif kind == 'track':
            title = json_item['title']
            track_item = AudioItem(title,
                                   context.create_uri('play', {'audio_id': unicode(json_item['id'])}),
                                   image=_get_image(json_item))
            track_item.set_fanart(self.get_fanart(context))

            # title
            track_item.set_title(title)

            # genre
            track_item.set_genre(json_item.get('genre', ''))

            # duration
            track_item.set_duration_from_milli_seconds(json_item.get('duration', 0))

            # artist
            track_item.set_artist_name(json_item.get('user', {}).get('username', ''))

            # year
            track_item.set_year(_get_track_year(json_item))

            context_menu = []
            # recommended tracks
            context_menu.append((context.localize(self._local_map['soundcloud.recommended']),
                                 'Container.Update(%s)' % context.create_uri(
                                     ['explore', 'recommended', 'tracks', unicode(json_item['id'])])))

            # like/unlike a track
            if path == '/user/favorites/me/':
                context_menu.append((context.localize(self._local_map['soundcloud.unlike']),
                                     'RunPlugin(%s)' % context.create_uri(['like/track', unicode(json_item['id'])],
                                                                          {'like': '0'})))
                pass
            else:
                context_menu.append((context.localize(self._local_map['soundcloud.like']),
                                     'RunPlugin(%s)' % context.create_uri(['like/track', unicode(json_item['id'])],
                                                                          {'like': '1'})))
                pass

            # go to user
            username = json_item['user']['username']
            user_id = str(json_item['user']['id'])
            if path != '/user/tracks/%s/' % user_id:
                context_menu.append((
                    context.localize(self._local_map['soundcloud.user.go_to']) % ('[B]%s[/B]' % username),
                    'Container.Update(%s)' % context.create_uri(['user', 'tracks', user_id])))
                pass

            track_item.set_context_menu(context_menu)

            return track_item
        elif kind == 'like':
            # A like has 'playlist' or 'track' so we find one of them and call this routine again, because the
            # data is same.
            test_playlist = json_item.get('playlist', None)
            if test_playlist is not None:
                return self._do_item(context, test_playlist, path)

            test_track = json_item.get('track', None)
            if test_track is not None:
                return self._do_item(context, test_track, path)
            pass
        elif kind == 'group':
            # at the moment we don't support groups
            """
            group_item = DirectoryItem('Group-Dummy',
                                       '')
            return group_item
            """
            return None

        raise kodion.KodionException("Unknown kind of item '%s'" % kind)

    pass
