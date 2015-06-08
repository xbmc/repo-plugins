from resources.lib.kodion.items import DirectoryItem, UriItem
from resources.lib.vimeo.client import Client
from resources.lib.vimeo.helper import do_xml_error

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.vimeo import helper


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._local_map.update({'vimeo.my-feed': 30500,
                                'vimeo.watch-later': 30107,
                                'vimeo.likes': 30501,
                                'vimeo.like': 30518,
                                'vimeo.unlike': 30519,
                                'vimeo.following': 30502,
                                'vimeo.watch-later.add': 30516,
                                'vimeo.watch-later.remove': 30517,
                                'vimeo.sign-in': 30111,
                                'vimeo.channels': 30503,
                                'vimeo.groups': 30504,
                                'vimeo.group.join': 30514,
                                'vimeo.group.leave': 30515,
                                'vimeo.channel.follow': 30512,
                                'vimeo.channel.unfollow': 30513,
                                'vimeo.albums': 30505,
                                'vimeo.videos': 30506,
                                'vimeo.user.go-to': 30511,
                                'vimeo.video.add-to': 30510,
                                'vimeo.select': 30509,
                                'vimeo.adding.no-group': 30507,
                                'vimeo.adding.no-channel': 30521,
                                'vimeo.adding.no-album': 30508,
                                'vimeo.removing.no-group': 30523,
                                'vimeo.removing.no-channel': 30524,
                                'vimeo.removing.no-album': 30525,
                                'vimeo.remove': 30108,
                                'vimeo.featured': 30526,
                                'vimeo.video.remove-from': 30522})

        self._client = None
        self._is_logged_in = False
        pass

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def is_logged_in(self):
        return self._is_logged_in

    def reset_client(self):
        self._client = None
        pass

    def get_client(self, context):
        # set the items per page (later)
        items_per_page = context.get_settings().get_items_per_page()

        access_manager = context.get_access_manager()
        access_token = access_manager.get_access_token()
        if access_manager.is_new_login_credential() or not access_token or access_manager.is_access_token_expired():
            # reset access_token
            access_manager.update_access_token('')
            # we clear the cache, so none cached data of an old account will be displayed.
            context.get_function_cache().clear()
            # reset the client
            self._client = None
            pass

        if not self._client:
            if access_manager.has_login_credentials() or access_manager.has_refresh_token():
                username, password = access_manager.get_login_credentials()
                access_token = access_manager.get_access_token()
                refresh_token = access_manager.get_refresh_token()

                # create a new access_token
                if not access_token and username and password:
                    data = Client().login(username, password)
                    access_manager.update_access_token(access_token=data.get('oauth_token'),
                                                       refresh_token=data.get('oauth_token_secret'))
                    pass

                access_token = access_manager.get_access_token()
                refresh_token = access_manager.get_refresh_token()

                if access_token and refresh_token:
                    self._client = Client(oauth_token=access_token, oauth_token_secret=refresh_token)
                else:
                    self._client = Client()
                    pass

                self._is_logged_in = access_token != ''
            else:
                self._client = Client()
                pass
            pass

        return self._client

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    @kodion.RegisterProviderPath('^/search/$')
    def endpoint_search(self, context, re_match):
        query = context.get_param('q', '')
        if not query:
            return []

        return self.on_search(query, context, re_match)

    def on_search(self, search_text, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        result = []

        client = self.get_client(context)
        page = int(context.get_param('page', '1'))
        xml = client.search(query=search_text, page=page)
        result.extend(helper.do_xml_videos_response(context, self, xml))

        return result

    # LIST: VIDEO OF A CHANNEL
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/channel\/(?P<channel_id>\d+)/$')
    def _on_user_channel(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        channel_id = re_match.group('channel_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_channel_videos(channel_id=channel_id, page=page))

    # LIST: VIDEO OF A CHANNEL
    @kodion.RegisterProviderPath('^\/channel\/(?P<channel_id>.+)/$')
    def _on_channel(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        channel_id = re_match.group('channel_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_channel_videos(channel_id=channel_id, page=page))

    # LIST: VIDEO OF A GROUP
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/group\/(?P<group_id>\d+)/$')
    def _on_user_group(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        group_id = re_match.group('group_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_group_videos(group_id=group_id, page=page))

    # LIST: MY FEEDs
    @kodion.RegisterProviderPath('^/user/me/feed/$')
    def _on_my_feed(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        client = self.get_client(context)
        xml = client.get_my_feed(page=page)
        return helper.do_xml_videos_response(context, self, xml)

    # LIST: WATCH LATER
    @kodion.RegisterProviderPath('^/user/me/watch-later/$')
    def _on_me_watch_later(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_watch_later(page=page))

    @kodion.RegisterProviderPath('^/user/(?P<user_id>me|\d+)/$')
    def _on_user(self, context, re_match):
        user_id = re_match.group('user_id')
        page = int(context.get_param('page', '1'))

        return self._create_user_items(user_id=user_id, context=context)

    # LIST: VIDEOS
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/videos\/$')
    def _on_user_videos(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_videos_of_user(user_id=user_id, page=page))

    # LIST: FOLLOWING
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/following\/$')
    def _on_user_following(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        if user_id == 'me':
            user_id = None
            pass

        client = self.get_client(context)
        return helper.do_xml_user_response(context, self, client.get_contacts(user_id=user_id, page=page))

    # LIST: VIDEO OF ALBUM
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/album\/(?P<album_id>\d+)/$')
    def _on_user_albums_videos(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        album_id = re_match.group('album_id')
        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_album_videos(album_id=album_id, page=page))

    # LIST: ALBUMS
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/albums\/$')
    def _on_user_albums(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        client = self.get_client(context)
        return helper.do_xml_albums_response(user_id, context, self, client.get_albums(user_id=user_id, page=page))

    # LIST: GROUPS
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/groups\/$')
    def _on_user_groups(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        client = self.get_client(context)
        return helper.do_xml_groups_response(user_id, context, self, client.get_groups(user_id=user_id, page=page))

    # LIST: CHANNELS
    @kodion.RegisterProviderPath('^\/user\/(?P<user_id>me|\d+)\/channels\/$')
    def _on_user_channels(self, context, re_match):
        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        client = self.get_client(context)
        return helper.do_xml_channels_response(user_id, context, self, client.get_channels_all(user_id=user_id, page=page))

    # LIST: LIKES
    @kodion.RegisterProviderPath('^/user/(?P<user_id>me|\d+)/likes/$')
    def _on_user_likes(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)

        page = int(context.get_param('page', '1'))
        user_id = re_match.group('user_id')
        if user_id == 'me':
            user_id = None
            pass

        client = self.get_client(context)
        return helper.do_xml_videos_response(context, self, client.get_video_likes(user_id=user_id, page=page))

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        def _compare(item):
            vq = context.get_settings().get_video_quality()
            return vq - item['resolution']

        video_id = context.get_param('video_id')
        client = self.get_client(context)
        video_item = helper.do_xml_video_response(context, self, client.get_video_info(video_id))
        xml = self.get_client(context).get_video_streams(video_id=video_id)

        if not do_xml_error(context, self, xml):
            return False

        video_streams = helper.do_xml_to_video_stream(context, self, xml)
        video_stream = kodion.utils.select_stream(context, video_streams)

        video_item.set_uri(video_stream['url'])
        return video_item

    # /video/like|unlike/?video_id=XX
    @kodion.RegisterProviderPath('^/video/(?P<method>like|unlike)/$')
    def _on_video_like(self, context, re_match):
        video_id = context.get_param('video_id')
        like = re_match.group('method') == 'like'

        client = self.get_client(context)
        helper.do_xml_error(context, self, client.like_video(video_id=video_id, like=like))

        context.get_ui().refresh_container()
        return True

    # /group/(join|leave)/?group_id=XX
    @kodion.RegisterProviderPath('^/group/(?P<method>join|leave)/$')
    def _on_group_join(self, context, re_match):
        group_id = context.get_param('group_id')

        client = self.get_client(context)
        if re_match.group('method') == 'join':
            helper.do_xml_error(context, self, client.join_group(group_id=group_id))
        else:
            helper.do_xml_error(context, self, client.leave_group(group_id=group_id))
            pass

        context.get_ui().refresh_container()
        return True

    # /channel/(subscribe|unsubscribe)/?channel_id=XX
    @kodion.RegisterProviderPath('^/channel/(?P<method>subscribe|unsubscribe)/$')
    def _on_channel_subscribe(self, context, re_match):
        channel_id = context.get_param('channel_id')

        client = self.get_client(context)
        if re_match.group('method') == 'subscribe':
            helper.do_xml_error(context, self, client.subscribe_channel(channel_id=channel_id))
        else:
            helper.do_xml_error(context, self, client.unsubscribe_channel(channel_id=channel_id))
            pass

        context.get_ui().refresh_container()
        return True

    @kodion.RegisterProviderPath('^/video/add-to/$')
    def _on_video_add_to(self, context, re_match):
        items = [
            (context.localize(self._local_map['vimeo.groups']), 'group'),
            (context.localize(self._local_map['vimeo.channels']), 'channel'),
            (context.localize(self._local_map['vimeo.albums']), 'album')]
        result = context.get_ui().on_select(context.localize(self._local_map['vimeo.video.add-to']), items)
        if result != -1:
            video_id = context.get_param('video_id')
            helper.do_manage_video_for_x(video_id=video_id, category=result, provider=self, context=context, add=True)
            pass
        pass

    @kodion.RegisterProviderPath('^/video/remove-from/$')
    def _on_video_remove_from(self, context, re_match):
        items = [
            (context.localize(self._local_map['vimeo.groups']), 'group'),
            (context.localize(self._local_map['vimeo.channels']), 'channel'),
            (context.localize(self._local_map['vimeo.albums']), 'album')]
        result = context.get_ui().on_select(context.localize(self._local_map['vimeo.video.remove-from']), items)
        if result != -1:
            video_id = context.get_param('video_id')
            helper.do_manage_video_for_x(video_id=video_id, category=result, provider=self, context=context, add=False)
            pass
        pass

    @kodion.RegisterProviderPath('^/video/watch-later/(?P<method>add|remove)/$')
    def _on_video_watch_later(self, context, re_match):
        video_id = context.get_param('video_id')
        method = re_match.group('method')

        client = self.get_client(context)
        if method == 'add':
            helper.do_xml_error(context, self, client.add_video_to_watch_later(video_id=video_id))
        elif method=='remove':
            helper.do_xml_error(context, self, client.remove_video_from_watch_later(video_id=video_id))
            pass

        context.get_ui().refresh_container()
        return True

    @kodion.RegisterProviderPath('^/sign/in/$')
    def _on_sign_in(self, context, re_match):
        context.get_ui().open_settings()
        return True

    def _create_user_items(self, user_id, context):
        result = []

        # Videos
        videos_item = DirectoryItem(context.localize(self._local_map['vimeo.videos']),
                                    context.create_uri(['user', user_id, 'videos']),
                                    image=context.create_resource_path('media', 'videos.png'))
        videos_item.set_fanart(self.get_fanart(context))
        result.append(videos_item)

        if user_id == 'me' and self.is_logged_in():
            # Watch Later
            watch_later_item = DirectoryItem(context.localize(self._local_map['vimeo.watch-later']),
                                             context.create_uri(['user', 'me', 'watch-later']),
                                             image=context.create_resource_path('media', 'watch_later.png'))
            watch_later_item.set_fanart(self.get_fanart(context))
            result.append(watch_later_item)
            pass

        # Likes
        likes_item = DirectoryItem(context.localize(self._local_map['vimeo.likes']),
                                   context.create_uri(['user', user_id, 'likes']),
                                   image=context.create_resource_path('media', 'likes.png'))
        likes_item.set_fanart(self.get_fanart(context))
        result.append(likes_item)

        # Following
        following_item = DirectoryItem(context.localize(self._local_map['vimeo.following']),
                                       context.create_uri(['user', user_id, 'following']),
                                       image=context.create_resource_path('media', 'channel.png'))
        following_item.set_fanart(self.get_fanart(context))
        result.append(following_item)

        # Groups
        groups_item = DirectoryItem(context.localize(self._local_map['vimeo.groups']),
                                    context.create_uri(['user', user_id, 'groups']),
                                    image=context.create_resource_path('media', 'groups.png'))
        groups_item.set_fanart(self.get_fanart(context))
        result.append(groups_item)

        # Channels
        channels_item = DirectoryItem(context.localize(self._local_map['vimeo.channels']),
                                      context.create_uri(['user', user_id, 'channels']),
                                      image=context.create_resource_path('media', 'channels.png'))
        channels_item.set_fanart(self.get_fanart(context))
        result.append(channels_item)

        # Albums
        albums_item = DirectoryItem(context.localize(self._local_map['vimeo.albums']),
                                    context.create_uri(['user', user_id, 'albums']),
                                    image=context.create_resource_path('media', 'albums.png'))
        albums_item.set_fanart(self.get_fanart(context))
        result.append(albums_item)

        return result

    @kodion.RegisterProviderPath('^/featured/$')
    def _on_featured(self, context, re_match):
        return helper.do_xml_featured_response(context, self, self.get_client(context).get_featured())


    def on_root(self, context, re_match):
        result = []

        client = self.get_client(context)

        # featured
        featured_item = DirectoryItem(context.localize(self._local_map['vimeo.featured']),
                                      context.create_uri(['featured']),
                                      image=context.create_resource_path('media', 'featured.png'))
        featured_item.set_fanart(self.get_fanart(context))
        result.append(featured_item)

        if self._is_logged_in:
            # my feed
            feed_item = DirectoryItem(context.localize(self._local_map['vimeo.my-feed']),
                                      context.create_uri(['user', 'me', 'feed']),
                                      image=context.create_resource_path('media', 'new_uploads.png'))
            feed_item.set_fanart(self.get_fanart(context))
            result.append(feed_item)

            result.extend(self._create_user_items(user_id='me', context=context))
            pass

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        # sign in
        if not self._is_logged_in:
            sign_in_item = DirectoryItem(context.localize(self._local_map['vimeo.sign-in']),
                                         context.create_uri(['sign', 'in']),
                                         image=context.create_resource_path('media', 'sign_in.png'))
            sign_in_item.set_fanart(self.get_fanart(context))
            result.append(sign_in_item)
            pass

        return result

    def set_content_type(self, context, content_type):
        context.set_content_type(content_type)
        if content_type == kodion.constants.content_type.EPISODES:
            context.add_sort_method(kodion.constants.sort_method.UNSORTED,
                                    kodion.constants.sort_method.VIDEO_RUNTIME,
                                    kodion.constants.sort_method.VIDEO_TITLE,
                                    kodion.constants.sort_method.VIDEO_YEAR)
            pass
        pass

    pass