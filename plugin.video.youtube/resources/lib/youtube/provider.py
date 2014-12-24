__author__ = 'bromix'

from resources.lib.youtube.helper import yt_subscriptions
from resources.lib import kodion
from resources.lib.kodion.utils import FunctionCache
from resources.lib.kodion.items import *
from resources.lib.youtube.client import YouTube
from .helper import v3, ResourceManager, yt_specials, yt_playlist, yt_login, yt_setup_wizard
from .youtube_exceptions import YouTubeException, LoginException


class Provider(kodion.AbstractProvider):
    LOCAL_MAP = {'youtube.channels': 30500,
                 'youtube.playlists': 30501,
                 'youtube.go_to_channel': 30502,
                 'youtube.subscriptions': 30504,
                 'youtube.unsubscribe': 30505,
                 'youtube.subscribe': 30506,
                 'youtube.my_channel': 30507,
                 'youtube.watch_later': 30107,
                 'youtube.liked.videos': 30508,
                 'youtube.history': 30509,
                 'youtube.my_subscriptions': 30510,
                 'youtube.like': 30511,
                 'youtube.remove': 30108,
                 'youtube.browse_channels': 30512,
                 'youtube.what_to_watch': 30513,
                 'youtube.related_videos': 30514,
                 'youtube.setting.auto_remove_watch_later': 30515,
                 'youtube.subscribe_to': 30517,
                 'youtube.sign.in': 30111,
                 'youtube.sign.out': 30112,
                 'youtube.sign.go_to': 30518,
                 'youtube.sign.enter_code': 30519,
                 'youtube.video.add_to_playlist': 30520,
                 'youtube.playlist.select': 30521,
                 'youtube.rename': 30113,
                 'youtube.playlist.create': 30522,
                 'youtube.setup_wizard.select_language': 30524,
                 'youtube.setup_wizard.select_region': 30525,
                 'youtube.setup_wizard.adjust': 30526,
                 'youtube.setup_wizard.adjust.language_and_region': 30527}

    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._client = None
        self._resource_manager = None
        self._is_logged_in = False
        pass

    def on_setup_wizard(self, context):
        super(Provider, self).on_setup_wizard(context)
        yt_setup_wizard.process(self, context)
        pass

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
            language = context.get_settings().get_string('youtube.language', 'en-US')

            # remove the old login.
            if access_manager.has_login_credentials():
                access_manager.remove_login_credentials()
                pass

            if access_manager.has_login_credentials() or access_manager.has_refresh_token():
                username, password = access_manager.get_login_credentials()
                access_token = access_manager.get_access_token()
                refresh_token = access_manager.get_refresh_token()

                # create a new access_token
                """
                if not access_token and username and password:
                    access_token, expires = YouTube(language=language).authenticate(username, password)
                    access_manager.update_access_token(access_token, expires)
                    pass
                """
                if not access_token and refresh_token:
                    access_token, expires = YouTube(language=language).refresh_token(refresh_token)
                    access_manager.update_access_token(access_token, expires)
                    pass

                self._is_logged_in = access_token != ''
                self._client = YouTube(items_per_page=items_per_page, access_token=access_token,
                                       language=language)
            else:
                self._client = YouTube(items_per_page=items_per_page, language=language)
                pass
            pass

        return self._client

    def get_resource_manager(self, context):
        if not self._resource_manager:
            self._resource_manager = ResourceManager(context, self.get_client(context))
            pass
        return self._resource_manager

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    """
    Lists the videos of a playlist.
    path       : '/channel/(?P<channel_id>.*)/playlist/(?P<playlist_id>.*)/'
    channel_id : ['mine'|<CHANNEL_ID>]
    playlist_id: <PLAYLIST_ID>
    """

    @kodion.RegisterProviderPath('^/channel/(?P<channel_id>.*)/playlist/(?P<playlist_id>.*)/$')
    def _on_channel_playlist(self, context, re_match):
        context.get_ui().set_view_mode('videos')
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        result = []

        playlist_id = re_match.group('playlist_id')
        page_token = context.get_param('page_token', '')

        # no caching
        json_data = self.get_client(context).get_playlist_items(playlist_id=playlist_id, page_token=page_token)
        if not v3.handle_error(self, context, json_data):
            return False
        result.extend(v3.response_to_items(self, context, json_data))

        return result

    """
    Lists all playlists of a channel.
    path      : '/channel/(?P<channel_id>.*)/playlists/'
    channel_id: <CHANNEL_ID>
    """

    @kodion.RegisterProviderPath('^/channel/(?P<channel_id>.*)/playlists/$')
    def _on_channel_playlists(self, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        result = []

        channel_id = re_match.group('channel_id')
        page_token = context.get_param('page_token', '')

        # no caching
        json_data = self.get_client(context).get_playlists(channel_id, page_token)
        if not v3.handle_error(self, context, json_data):
            return False
        result.extend(v3.response_to_items(self, context, json_data))

        return result

    """
    Lists a playlist folder and all uploaded videos of a channel.
    path      :'/channel/(?P<channel_id>.*)/'
    channel_id: <CHANNEL_ID>
    """

    @kodion.RegisterProviderPath('^/channel/(?P<channel_id>.*)/$')
    def _on_channel(self, context, re_match):
        context.get_ui().set_view_mode('videos')
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        resource_manager = ResourceManager(context, self.get_client(context))

        result = []

        channel_id = re_match.group('channel_id')
        channel_fanarts = resource_manager.get_fanarts([channel_id])
        page = int(context.get_param('page', 1))
        page_token = context.get_param('page_token', '')

        if page == 1:
            playlists_item = DirectoryItem('[B]' + context.localize(self.LOCAL_MAP['youtube.playlists']) + '[/B]',
                                           context.create_uri(['channel', channel_id, 'playlists']),
                                           image=context.create_resource_path('media', 'playlist.png'))
            playlists_item.set_fanart(channel_fanarts.get(channel_id, self.get_fanart(context)))
            result.append(playlists_item)
            pass

        playlists = resource_manager.get_related_playlists(channel_id)
        upload_playlist = playlists.get('uploads', '')
        if upload_playlist:
            json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 5,
                                                         self.get_client(context).get_playlist_items, upload_playlist,
                                                         page_token=page_token)
            if not v3.handle_error(self, context, json_data):
                return False
            result.extend(v3.response_to_items(self, context, json_data))
            pass

        return result

    """
    Plays a video.
    path for video: '/play/?video_id=XXXXXXX'

    TODO: path for playlist: '/play/?playlist_id=XXXXXXX&mode=[OPTION]'
    OPTION: [normal(default)|reverse|shuffle]
    """

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        vq = context.get_settings().get_video_quality()

        def _compare(item):
            return vq - item['format']['height']

        video_id = context.get_param('video_id')

        try:
            client = self.get_client(context)
            video_streams = client.get_video_streams(context, video_id)
            video_stream = kodion.utils.find_best_fit(video_streams, _compare)
            video_item = VideoItem(video_id, video_stream['url'])

            # Auto-Remove video from 'Watch Later' playlist - this should run asynchronous
            if self.is_logged_in() and context.get_settings().get_bool('youtube.playlist.watchlater.autoremove', True):
                command = 'RunPlugin(%s)' % context.create_uri(['internal', 'auto_remove_watch_later'],
                                                               {'video_id': video_id})
                context.execute(command)
                pass

            return video_item
        except YouTubeException, ex:
            message = ex.get_message()
            message = kodion.utils.strip_html_from_text(message)
            context.get_ui().show_notification(message, time_milliseconds=30000)
            pass

        return False

    @kodion.RegisterProviderPath('^/playlist/(?P<method>.*)/(?P<category>.*)/$')
    def _on_playlist(self, context, re_match):
        method = re_match.group('method')
        category = re_match.group('category')
        return yt_playlist.process(method, category, self, context, re_match)

    @kodion.RegisterProviderPath('^/subscriptions/(?P<method>.*)/$')
    def _on_subscriptions(self, context, re_match):
        method = re_match.group('method')
        return yt_subscriptions.process(method, self, context, re_match)

    @kodion.RegisterProviderPath('^/special/(?P<category>.*)/$')
    def _on_yt_specials(self, context, re_match):
        result = []

        category = re_match.group('category')
        result.extend(yt_specials.process(category, self, context, re_match))
        return result

    """

    """

    @kodion.RegisterProviderPath('^/internal/auto_remove_watch_later/$')
    def _on_auto_remove_watch_later(self, context, re_match):

        video_id = context.get_param('video_id', '')
        if video_id:
            client = self.get_client(context)
            playlist_item_id = client.get_playlist_item_id_of_video_id(playlist_id='WL', video_id=video_id)
            if playlist_item_id:
                json_data = client.remove_video_from_playlist('WL', playlist_item_id)
                if not v3.handle_error(self, context, json_data):
                    return False
                pass
            pass
        return True

    @kodion.RegisterProviderPath('^/sign/(?P<mode>.*)/$')
    def _on_sign(self, context, re_match):
        mode = re_match.group('mode')
        yt_login.process(mode, self, context, re_match)
        return True

    def on_search(self, search_text, context, re_match):
        self.set_content_type(context, kodion.constants.content_type.EPISODES)

        result = []

        page_token = context.get_param('page_token', '')
        search_type = context.get_param('search_type', 'video')
        page = int(context.get_param('page', 1))

        if search_type == 'video':
            context.get_ui().set_view_mode('videos')
            pass

        if page == 1 and search_type == 'video':
            channel_params = {}
            channel_params.update(context.get_params())
            channel_params['search_type'] = 'channel'
            channel_item = DirectoryItem('[B]' + context.localize(self.LOCAL_MAP['youtube.channels']) + '[/B]',
                                         context.create_uri([context.get_path()], channel_params),
                                         image=context.create_resource_path('media', 'channels.png'))
            channel_item.set_fanart(self.get_fanart(context))
            result.append(channel_item)

            playlist_params = {}
            playlist_params.update(context.get_params())
            playlist_params['search_type'] = 'playlist'
            playlist_item = DirectoryItem('[B]' + context.localize(self.LOCAL_MAP['youtube.playlists']) + '[/B]',
                                          context.create_uri([context.get_path()], playlist_params),
                                          image=context.create_resource_path('media', 'playlist.png'))
            playlist_item.set_fanart(self.get_fanart(context))
            result.append(playlist_item)
            pass

        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, self.get_client(context).search,
                                                     q=search_text, search_type=search_type, page_token=page_token)
        if not v3.handle_error(self, context, json_data):
            return False
        result.extend(v3.response_to_items(self, context, json_data))
        return result

    def on_root(self, context, re_match):
        """
        Support old YouTube url call, but also log a deprecation warning.
        plugin://plugin.video.youtube/?action=play_video&videoid=[ID]
        """
        old_action = context.get_param('action', '')
        old_video_id = context.get_param('videoid', '')
        if old_action and old_video_id:
            context.log_warning('DEPRECATED "%s"' % context.get_uri())
            context.log_warning('USE INSTEAD "plugin://%s/play/?video_id=%s"' % (context.get_id(), old_video_id))
            new_params = {'video_id': old_video_id}
            new_path = '/play/'
            new_context = context.clone(new_path=new_path, new_params=new_params)
            return self._on_play(new_context, re_match)

        self.get_client(context)
        resource_manager = self.get_resource_manager(context)

        result = []

        settings = context.get_settings()

        # sign in
        if not self.is_logged_in() and settings.get_bool('youtube.folder.sign.in.show', True):
            sign_in_item = DirectoryItem('[B]%s[/B]' % context.localize(self.LOCAL_MAP['youtube.sign.in']),
                                         context.create_uri(['sign', 'in']),
                                         image=context.create_resource_path('media', 'sign_in.png'))
            sign_in_item.set_fanart(self.get_fanart(context))
            result.append(sign_in_item)
            pass

        if self.is_logged_in() and settings.get_bool('youtube.folder.my_subscriptions.show', True):
            # my subscription
            my_subscriptions_item = DirectoryItem(
                '[B]' + context.localize(self.LOCAL_MAP['youtube.my_subscriptions']) + '[/B]',
                context.create_uri(['special', 'new_uploaded_videos']),
                context.create_resource_path('media', 'new_uploads.png'))
            my_subscriptions_item.set_fanart(self.get_fanart(context))
            result.append(my_subscriptions_item)
            pass

        # what to watch
        if settings.get_bool('youtube.folder.what_to_watch.show', True):
            what_to_watch_item = DirectoryItem(
                '[B]' + context.localize(self.LOCAL_MAP['youtube.what_to_watch']) + '[/B]',
                context.create_uri(['special', 'what_to_watch']),
                context.create_resource_path('media', 'what_to_watch.png'))
            what_to_watch_item.set_fanart(self.get_fanart(context))
            result.append(what_to_watch_item)
            pass

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        # subscriptions
        if self.is_logged_in():
            playlists = resource_manager.get_related_playlists(channel_id='mine')

            # my channel
            if settings.get_bool('youtube.folder.my_channel.show', True):
                my_channel_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.my_channel']),
                                                context.create_uri(['channel', 'mine']),
                                                image=context.create_resource_path('media', 'channel.png'))
                my_channel_item.set_fanart(self.get_fanart(context))
                result.append(my_channel_item)
                pass

            # watch later
            if 'watchLater' in playlists and settings.get_bool('youtube.folder.watch_later.show', True):
                watch_later_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.watch_later']),
                                                 context.create_uri(
                                                     ['channel', 'mine', 'playlist', playlists['watchLater']]),
                                                 context.create_resource_path('media', 'watch_later.png'))
                watch_later_item.set_fanart(self.get_fanart(context))
                result.append(watch_later_item)
                pass

            # liked videos
            if 'likes' in playlists and settings.get_bool('youtube.folder.liked_videos.show', True):
                liked_videos_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.liked.videos']),
                                                  context.create_uri(
                                                      ['channel', 'mine', 'playlist', playlists['likes']]),
                                                  context.create_resource_path('media', 'likes.png'))
                liked_videos_item.set_fanart(self.get_fanart(context))
                result.append(liked_videos_item)
                pass

            # history
            if 'watchHistory' in playlists and settings.get_bool('youtube.folder.history.show', False):
                watch_history_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.history']),
                                                   context.create_uri(
                                                       ['channel', 'mine', 'playlist', playlists['watchHistory']]),
                                                   context.create_resource_path('media', 'history.png'))
                watch_history_item.set_fanart(self.get_fanart(context))
                result.append(watch_history_item)
                pass

            # (my) playlists
            if settings.get_bool('youtube.folder.playlists.show', True):
                playlists_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.playlists']),
                                               context.create_uri(['channel', 'mine', 'playlists']),
                                               context.create_resource_path('media', 'playlist.png'))
                playlists_item.set_fanart(self.get_fanart(context))
                result.append(playlists_item)
                pass

            # subscriptions
            if settings.get_bool('youtube.folder.subscriptions.show', True):
                subscriptions_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.subscriptions']),
                                                   context.create_uri(['subscriptions', 'list']),
                                                   image=context.create_resource_path('media', 'channels.png'))
                subscriptions_item.set_fanart(self.get_fanart(context))
                result.append(subscriptions_item)
                pass
            pass

        if settings.get_bool('youtube.folder.browse_channels.show', True):
            browse_channels_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.browse_channels']),
                                                 context.create_uri(['special', 'browse_channels']),
                                                 image=context.create_resource_path('media', 'browse_channels.png'))
            browse_channels_item.set_fanart(self.get_fanart(context))
            result.append(browse_channels_item)
            pass

        # sign out
        if self.is_logged_in() and settings.get_bool('youtube.folder.sign.out.show', True):
            sign_out_item = DirectoryItem(context.localize(self.LOCAL_MAP['youtube.sign.out']),
                                          context.create_uri(['sign', 'out']),
                                          image=context.create_resource_path('media', 'sign_out.png'))
            sign_out_item.set_fanart(self.get_fanart(context))
            result.append(sign_out_item)
            pass

        return result

    def set_content_type(self, context, content_type):
        if content_type == kodion.constants.content_type.EPISODES:
            context.set_content_type(content_type)
            context.add_sort_method(kodion.constants.sort_method.UNSORTED,
                                    kodion.constants.sort_method.VIDEO_RUNTIME,
                                    kodion.constants.sort_method.VIDEO_TITLE,
                                    kodion.constants.sort_method.VIDEO_YEAR)
            pass
        pass

    def handle_exception(self, context, exception_to_handle):
        if isinstance(exception_to_handle, LoginException):
            context.get_access_manager().update_access_token('')
            context.get_ui().show_notification('Login Failed')
            context.get_ui().open_settings()
            return False

        return True

    pass