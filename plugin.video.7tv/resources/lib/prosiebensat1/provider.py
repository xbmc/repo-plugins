import re

from client import Client
from resources.lib import kodion
from resources.lib.kodion.items import VideoItem, DirectoryItem, UriItem
from resources.lib.kodion.utils import FunctionCache, datetime_parser


def try_set_season_and_episode(video_item):
    """
    First try to get an episode and after that the season
    """
    re_match = re.search("Staffel (\d+)", video_item.get_name())
    if re_match is not None:
        video_item.set_season(int(re_match.group(1)))
        pass
    re_match = re.search("(Episode|Folge) (\d+)", video_item.get_name())
    if re_match is not None:
        video_item.set_episode(int(re_match.group(2)))
        pass
    pass


class Provider(kodion.AbstractProvider):
    CHANNEL_ID_STRING = 'pro7|sat1|kabel1|sixx|sat1gold|prosiebenmaxx'

    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._local_map.update({'7tv.popular_shows': 30500,
                                '7tv.current_entire_episodes': 30501,
                                '7tv.newest_clips': 30502,
                                '7tv.clips': 30503,
                                '7tv.backstage': 30504,
                                '7tv.exception.drm_not_supported': 30505})

        self._client = None

        self._channel_id_list = ['pro7', 'sat1', 'kabel1', 'sixx', 'sat1gold', 'prosiebenmaxx']
        self._channel_data = {'pro7': {'name': u'ProSieben'},
                              'sat1': {'name': u'SAT.1'},
                              'kabel1': {'name': u'kabel eins'},
                              'sixx': {'name': u'sixx'},
                              'sat1gold': {'name': u'SAT.1 Gold'},
                              'prosiebenmaxx': {'name': u'ProSieben MAXX'}}

        pass

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def _get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def _set_sort_method_for_content_type(self, context, content_type):
        context.set_content_type(content_type)

        if content_type == kodion.constants.content_type.EPISODES:
            context.add_sort_method(kodion.constants.sort_method.UNSORTED,
                                    kodion.constants.sort_method.LABEL_IGNORE_THE,
                                    kodion.constants.sort_method.VIDEO_RUNTIME,
                                    kodion.constants.sort_method.VIDEO_YEAR)
        elif content_type == kodion.constants.content_type.TV_SHOWS:
            context.add_sort_method(kodion.constants.sort_method.LABEL_IGNORE_THE)
            pass
        pass

    def on_watch_later(self, context, re_match):
        self._set_sort_method_for_content_type(context, kodion.constants.content_type.EPISODES)
        pass

    def on_search(self, search_text, context, re_match):
        context.get_ui().set_view_mode('videos')
        self._set_sort_method_for_content_type(context, kodion.constants.content_type.EPISODES)

        result = []
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self._get_client(context).search,
                                                     self._get_client(context).API_V2,
                                                     search_text)
        screen = json_data.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        for screen_object in screen_objects:
            sub_screen_objects = screen_object.get('screen_objects', [])
            for sub_screen_object in sub_screen_objects:
                result.append(self._screen_object_to_item(context, sub_screen_object))
                pass
            pass

        return result

    @kodion.RegisterProviderPath('^\/(?P<channelid>' + CHANNEL_ID_STRING + ')\/highlights\/((?P<category>.*)\/)?$')
    def _get_channel_highlights(self, context, re_match):
        result = []

        channel_id = re_match.group('channelid')
        channel_image = context.create_resource_path('media', 'channels' '%s.png' % channel_id)

        category = re_match.group('category')
        if category is None:
            # Popular Shows
            item = DirectoryItem(context.localize(self._local_map['7tv.popular_shows']),
                                 context.create_uri([channel_id, 'highlights', 'Beliebte Sendungen']),
                                 image=channel_image)
            item.set_fanart(self.get_fanart(context))
            result.append(item)

            # Current Entire Episodes
            item = DirectoryItem(context.localize(self._local_map['7tv.current_entire_episodes']),
                                 context.create_uri([channel_id, 'highlights', 'Aktuelle ganze Folgen']),
                                 image=channel_image)
            item.set_fanart(self.get_fanart(context))
            result.append(item)

            # Newest Clips
            item = DirectoryItem(context.localize(self._local_map['7tv.newest_clips']),
                                 context.create_uri([channel_id, 'highlights', 'Neueste Clips']),
                                 image=channel_image)
            item.set_fanart(self.get_fanart(context))
            result.append(item)
        else:
            json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 5,
                                                         self._get_client(context).get_homepage,
                                                         self._get_client(context).API_V2, channel_id)
            screen = json_data.get('screen', {})
            screen_objects = screen.get('screen_objects', [])
            for screen_object in screen_objects:
                if screen_object.get('type', '') == 'sushi_bar':
                    if screen_object.get('title', '') == category:
                        sub_screen_objects = screen_object.get('screen_objects', [])
                        for sub_screen_object in sub_screen_objects:
                            result.append(self._screen_object_to_item(context,
                                                                      sub_screen_object,
                                                                      show_format_title=(category == 'Neueste Clips')))
                            pass
                        break
                    pass
                pass

            if category == 'Beliebte Sendungen':
                self._set_sort_method_for_content_type(context, kodion.constants.content_type.TV_SHOWS)
                result = self._sort_result_by_name(result)
            else:
                self._set_sort_method_for_content_type(context, kodion.constants.content_type.EPISODES)
                result = self._sort_result_by_aired(result)
            pass

        return result

    def _sort_result_by_name(self, items, reverse=False):
        def _sort(item):
            return item.get_name()

        return sorted(items, key=_sort, reverse=reverse)

    def _sort_result_by_aired(self, items, reverse=False):
        def _sort(item):
            return item.get_aired()

        return sorted(items, key=_sort, reverse=reverse)

    @kodion.RegisterProviderPath('^/play/$')
    def _play(self, context, re_match):
        params = context.get_params()
        video_id = params.get('id', '')
        if video_id == '':
            raise kodion.KodimonException("Missing parameter 'id' to play video")

        json_data = self._get_client(context).get_video_url(video_id)
        video_url = json_data.get('VideoURL', '')
        if not video_url:
            raise kodion.KodimonException("Could not resolve url for video '%s'" % video_id)

        re_drm_match = re.search(r'no_flash_de|drm_update_app_de', video_url)
        if re_drm_match:
            context.get_ui().show_notification(context.localize(self._local_map['7tv.exception.drm_not_supported']))
            return False

        return UriItem(video_url)

    def _load_format_content(self, context, channel_id, format_id, return_cached_only=False):
        result = {}

        data = None
        if return_cached_only:
            data = context.get_function_cache().get_cached_only(self._get_client(context).get_format_content,
                                                                self._get_client(context).API_V2, channel_id, format_id)
        else:
            data = context.get_function_cache().get(FunctionCache.ONE_HOUR,
                                                    self._get_client(context).get_format_content,
                                                    self._get_client(context).API_V2, channel_id, format_id)

        if data is None:
            return {}

        screen = data.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        for screen_object in screen_objects:
            if screen_object.get('type', '') == 'format_teaser_header_item':
                result['fanart'] = screen_object.get('image_url', '')
            elif screen_object.get('type', '') == 'sushi_bar':
                name = screen_object['title']
                sub_screen_objects = screen_object.get('screen_objects', [])
                if len(sub_screen_objects) > 0:
                    result[name] = screen_object.get('screen_objects', [])
                    pass
                pass
            pass

        return result

    @kodion.RegisterProviderPath('^/(?P<channelid>' + CHANNEL_ID_STRING + ')/library/(?P<formatid>\d+)/$')
    def _get_format_content(self, context, re_match):
        path = context.get_path()
        context.get_ui().set_view_mode('videos')
        self._set_sort_method_for_content_type(context, kodion.constants.content_type.EPISODES)

        params = context.get_params()
        clip_type = params.get('clip_type', 'full')
        page = int(params.get('page', '1'))

        result = []

        channel_id = re_match.group('channelid')
        channel_image = context.create_resource_path('media', 'channels', '%s.png' % channel_id)
        format_id = re_match.group('formatid')

        data = self._load_format_content(context, channel_id, format_id)
        fanart = data.get('fanart', self.get_fanart(context))

        if page == 1 and clip_type == 'full':
            # clips
            if 'Clips' in data:
                clips_item = DirectoryItem('[B]' + context.localize(self._local_map['7tv.clips']) + '[/B]',
                                           context.create_uri(path, {'clip_type': 'short'}),
                                           image=channel_image)
                clips_item.set_fanart(fanart)
                result.append(clips_item)
                pass

            # backstage
            if 'Backstage' in data:
                backstage_item = DirectoryItem('[B]' + context.localize(self._local_map['7tv.backstage']) + '[/B]',
                                               context.create_uri(path, {'clip_type': 'webexclusive'}),
                                               image=channel_image)
                backstage_item.set_fanart(fanart)
                result.append(backstage_item)
                pass
            pass

        # test for a possible next page (cached)
        next_page_test = context.get_function_cache().get(FunctionCache.ONE_HOUR,
                                                          self._get_client(context).get_format_videos,
                                                          self._get_client(context).API_V2, channel_id, format_id,
                                                          clip_type,
                                                          page=page + 1)
        next_page_test = next_page_test.get('objects', [])
        next_page = len(next_page_test) > 0

        if page == 1:
            # the first page will work like this
            clip_type_map = {'full': 'Ganze Folgen',
                             'short': 'Clips',
                             'webexclusive': 'Backstage'}
            episodes = data.get(clip_type_map[clip_type], [])
            video_list = []
            for episode in episodes:
                video_item = self._screen_object_to_item(context, episode)
                video_list.append(video_item)
                pass

            video_list = self._sort_result_by_aired(video_list, reverse=True)
            result.extend(video_list)

            if next_page:
                next_page_item = kodion.items.NextPageItem(context, page, fanart=fanart)
                result.append(next_page_item)
                pass
        else:
            video_list = []
            episodes = context.get_function_cache().get(FunctionCache.ONE_HOUR,
                                                        self._get_client(context).get_format_videos,
                                                        self._get_client(context).API_V2, channel_id, format_id,
                                                        clip_type,
                                                        page=page)
            episodes = episodes.get('objects', [])
            for episode in episodes:
                video_item = self._screen_object_to_item(context, episode)
                video_list.append(video_item)
                pass

            video_list = self._sort_result_by_aired(video_list, reverse=True)
            result.extend(video_list)

            if next_page:
                next_page_item = kodion.items.NextPageItem(context, page, fanart=fanart)
                result.append(next_page_item)
                pass
            pass

        return result

    @kodion.RegisterProviderPath('^/(?P<channelid>' + CHANNEL_ID_STRING + ')/library/$')
    def _get_channel_formats(self, context, re_match):
        self._set_sort_method_for_content_type(context, kodion.constants.content_type.TV_SHOWS)

        result = []

        # load the formats of the given channel
        channel_id = re_match.group('channelid')
        json_data = context.get_function_cache().get(FunctionCache.ONE_DAY, self._get_client(context).get_formats,
                                                     self._get_client(context).
                                                     API_V2, channel_id)
        screen = json_data.get('screen', {})
        screen_objects = screen.get('screen_objects', {})

        for screen_object in screen_objects:
            format_id = screen_object['id'].split(':')
            channel_id = format_id[0]
            format_id = format_id[1]
            format_item = DirectoryItem(screen_object['title'],
                                        context.create_uri([channel_id, 'library', format_id]),
                                        image=screen_object['image_url'])

            fanart = self.get_fanart(context)
            data = self._load_format_content(context, channel_id, format_id, return_cached_only=True)
            if data is not None:
                fanart = data.get('fanart', self.get_fanart(context))
                pass
            format_item.set_fanart(fanart)
            context_menu = [(context.localize(kodion.constants.localize.FAVORITES_ADD),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                  {'item': kodion.items.to_jsons(format_item)}))]
            format_item.set_context_menu(context_menu)
            result.append(format_item)
            pass

        return self._sort_result_by_name(result)

    @kodion.RegisterProviderPath('^/(?P<channelid>' + CHANNEL_ID_STRING + ')/$')
    def _get_channel_content(self, context, re_match):
        channel_id = re_match.group('channelid')

        result = []

        channel_image = context.create_resource_path('media', 'channels', '%s.png' % channel_id)

        # Highlights
        item = DirectoryItem(context.localize(kodion.constants.localize.HIGHLIGHTS),
                             context.create_uri([channel_id, 'highlights']),
                             image=channel_image)
        item.set_fanart(self.get_fanart(context))
        result.append(item)

        # Library
        item = DirectoryItem(context.localize(kodion.constants.localize.LIBRARY),
                             context.create_uri([channel_id, 'library']),
                             image=channel_image)
        item.set_fanart(self.get_fanart(context))
        result.append(item)

        return result

    @kodion.RegisterProviderPath('^/favs/latest/$')
    def _latest_video(self, context, re_match):
        context.get_ui().set_view_mode('videos')
        self._set_sort_method_for_content_type(context, kodion.constants.content_type.EPISODES)

        result = []

        directory_items = context.get_favorite_list().list()

        format_ids = []
        for directory_item in directory_items:
            item_uri = directory_item.get_uri()
            re_match = re.match('.*\/(?P<channelid>' + self.CHANNEL_ID_STRING + ')\/(library)\/(?P<formatid>\d+)\/',
                                item_uri)
            if re_match is not None:
                channel_id = re_match.group('channelid')
                format_id = re_match.group('formatid')
                format_ids.append("%s:%s" % (channel_id, format_id))
                pass
            pass

        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 5,
                                                     self._get_client(context).get_new_videos,
                                                     self._get_client(context).API_V2, format_ids)
        screen_objects = json_data.get('screen_objects', [])
        for screen_object in screen_objects:
            result.append(self._screen_object_to_item(context, screen_object, show_format_title=True))
            pass

        return result

    def on_root(self, context, re_match):
        result = []

        # favorites and latest videos
        if len(context.get_favorite_list().list()) > 0:
            fav_item = DirectoryItem('[B]' + context.localize(kodion.constants.localize.FAVORITES) + '[/B]',
                                     context.create_uri([kodion.constants.paths.FAVORITES, 'list']),
                                     image=context.create_resource_path('media', 'highlight.png'))
            fav_item.set_fanart(self.get_fanart(context))
            result.append(fav_item)

            latest_item = DirectoryItem('[B]' + context.localize(kodion.constants.localize.LATEST_VIDEOS) + '[/B]',
                                        context.create_uri(['favs', 'latest']),
                                        image=context.create_resource_path('media', 'highlight.png'))
            latest_item.set_fanart(self.get_fanart(context))
            result.append(latest_item)
            pass

        # watch later
        if len(context.get_watch_later_list().list()) > 0:
            fav_item = DirectoryItem('[B]' + context.localize(kodion.constants.localize.WATCH_LATER) + '[/B]',
                                     context.create_uri([kodion.constants.paths.WATCH_LATER, 'list']),
                                     image=context.create_resource_path('media', 'highlight.png'))
            fav_item.set_fanart(self.get_fanart(context))
            result.append(fav_item)

        # search
        search_item = DirectoryItem('[B]' + context.localize(kodion.constants.localize.SEARCH) + '[/B]',
                                    context.create_uri([kodion.constants.paths.SEARCH, 'list']),
                                    image=context.create_resource_path('media', 'search.png'))
        search_item.set_fanart(self.get_fanart(context))
        result.append(search_item)

        # channels
        for channel in self._channel_id_list:
            channel_data = self._channel_data.get(channel, {})
            channel_image = context.create_resource_path('media', 'channels', '%s.png' % channel)
            channel_item = DirectoryItem(channel_data.get('name', channel),
                                         context.create_uri(channel),
                                         image=channel_image)
            channel_item.set_fanart(self.get_fanart(context))
            result.append(channel_item)
            pass

        return result, {self.RESULT_CACHE_TO_DISC: False}

    def _screen_object_to_item(self, context, screen_object, show_format_title=False):
        screen_object_type = screen_object.get('type', '')
        if screen_object_type == '':
            raise kodion.KodimonException('Missing type for screenObject')

        fanart = self.get_fanart(context)
        format_id = screen_object.get('format_id', screen_object.get('id', '')).split(':')
        if len(format_id) == 2:
            channel_id = format_id[0]
            format_id = format_id[1]
            if channel_id == 'tvog':
                channel_id = 'pro7'
                pass
            data = self._load_format_content(context, channel_id, format_id, return_cached_only=True)
            fanart = data.get('fanart', self.get_fanart(context))
            pass

        if screen_object_type == 'video_item_date_no_label' or screen_object_type == 'video_item_date' \
                or screen_object_type == 'video_item_format_no_label' or screen_object_type == 'video_item_format':
            name = screen_object.get('title', screen_object['video_title'])
            if screen_object_type == 'video_item_format_no_label' or show_format_title:
                name = '%s - %s' % (screen_object['format_title'], name)
                pass
            video_item = VideoItem(name,
                                   context.create_uri(['play'], {'id': screen_object['id']}),
                                   image=screen_object.get('image_url', ''))
            video_item.set_fanart(fanart)
            video_item.set_duration_from_seconds(int(screen_object.get('duration', '60')))

            date_time = datetime_parser.parse(screen_object.get('start', '0000-00-00'))
            video_item.set_aired_from_datetime(date_time)
            video_item.set_premiered_from_datetime(date_time)
            video_item.set_year_from_datetime(date_time)
            try_set_season_and_episode(video_item)

            context_menu = [(context.localize(kodion.constants.localize.WATCH_LATER),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.WATCH_LATER, 'add'],
                                                                  {'item': kodion.items.to_jsons(video_item)}))]
            video_item.set_context_menu(context_menu)
            return video_item
        elif screen_object_type == 'format_item_home' or screen_object_type == 'format_item':
            format_item = DirectoryItem(screen_object['title'],
                                        context.create_uri([channel_id, 'library', format_id]),
                                        image=screen_object['image_url'])
            format_item.set_fanart(fanart)
            context_menu = [(context.localize(kodion.constants.localize.FAVORITES_ADD),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                  {'item': kodion.items.to_jsons(format_item)}))]
            format_item.set_context_menu(context_menu)
            return format_item

        raise kodion.KodimonException("Unknown type '%s' for screen_object" % screen_object_type)