import re
from functools import partial

from client import Client
from resources.lib import kodimon
from resources.lib.kodimon import constants, contextmenu
from resources.lib.kodimon.helper import FunctionCache


def try_set_season_and_episode(video_item):
    """
    First try to get an episode and after that the season
    """
    re_match = re.search("Staffel (\d+)", video_item.get_name())
    if re_match is not None:
        video_item.set_info(kodimon.VideoItem.INFO_SEASON, re_match.group(1))
        pass
    re_match = re.search("(Episode|Folge) (\d+)", video_item.get_name())
    if re_match is not None:
        video_item.set_info(kodimon.VideoItem.INFO_EPISODE, re_match.group(2))
        pass
    pass


class Provider(kodimon.AbstractProvider):
    CHANNEL_ID_STRING = 'pro7|sat1|kabel1|sixx|sat1gold|prosiebenmaxx'

    def __init__(self, plugin=None):
        kodimon.AbstractProvider.__init__(self, plugin)

        self.set_localization({'7tv.popular_shows': 30500,
                               '7tv.current_entire_episodes': 30501,
                               '7tv.newest_clips': 30502,
                               '7tv.clips': 30503,
                               '7tv.backstage': 30504})

        self._client = Client()

        self._channel_id_list = ['pro7', 'sat1', 'kabel1', 'sixx', 'sat1gold', 'prosiebenmaxx']
        self._channel_data = {'pro7': {'name': u'ProSieben'},
                              'sat1': {'name': u'SAT.1'},
                              'kabel1': {'name': u'kabel eins'},
                              'sixx': {'name': u'sixx'},
                              'sat1gold': {'name': u'SAT.1 Gold'},
                              'prosiebenmaxx': {'name': u'ProSieben MAXX'}}

        pass

    def get_fanart(self):
        return self.create_resource_path('media', 'fanart.jpg')

    def _set_sort_method_for_content_type(self, content_type):
        self.set_content_type(content_type)

        if content_type == constants.CONTENT_TYPE_EPISODES:
            self.add_sort_method(constants.SORT_METHOD_UNSORTED,
                                 constants.SORT_METHOD_LABEL_IGNORE_THE,
                                 constants.SORT_METHOD_VIDEO_RUNTIME,
                                 constants.SORT_METHOD_VIDEO_YEAR)
        elif content_type == constants.CONTENT_TYPE_TVSHOWS:
            self.add_sort_method(constants.SORT_METHOD_LABEL_IGNORE_THE)
            pass
        pass

    def on_watch_later(self, path, params, re_match):
        self._set_sort_method_for_content_type(constants.CONTENT_TYPE_EPISODES)
        pass

    def on_search(self, search_text, path, params, re_match):
        self._set_sort_method_for_content_type(constants.CONTENT_TYPE_EPISODES)

        result = []
        json_data = self.call_function_cached(partial(self._client.search, self._client.API_V2, search_text),
                                              FunctionCache.ONE_MINUTE)
        screen = json_data.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        for screen_object in screen_objects:
            sub_screen_objects = screen_object.get('screen_objects', [])
            for sub_screen_object in sub_screen_objects:
                result.append(self._screen_object_to_item(sub_screen_object))
                pass
            pass

        return result

    @kodimon.RegisterPath('^\/(?P<channelid>' + CHANNEL_ID_STRING + ')\/highlights\/((?P<category>.*)\/)?$')
    def _get_channel_highlights(self, path, params, re_match):
        result = []

        channel_id = re_match.group('channelid')
        channel_image = "media/channels/%s.png" % channel_id
        channel_image = self.create_resource_path(channel_image)

        category = re_match.group('category')
        if category is None:
            # Popular Shows
            item = kodimon.DirectoryItem(self.localize('7tv.popular_shows'),
                                         self.create_uri([channel_id, 'highlights', 'Beliebte Sendungen']),
                                         image=channel_image)
            item.set_fanart(self.get_fanart())
            result.append(item)

            # Current Entire Episodes
            item = kodimon.DirectoryItem(self.localize('7tv.current_entire_episodes'),
                                         self.create_uri([channel_id, 'highlights', 'Aktuelle ganze Folgen']),
                                         image=channel_image)
            item.set_fanart(self.get_fanart())
            result.append(item)

            # Newest Clips
            item = kodimon.DirectoryItem(self.localize('7tv.newest_clips'),
                                         self.create_uri([channel_id, 'highlights', 'Neueste Clips']),
                                         image=channel_image)
            item.set_fanart(self.get_fanart())
            result.append(item)
        else:
            json_data = self.call_function_cached(partial(self._client.get_homepage, self._client.API_V2, channel_id),
                                                  FunctionCache.ONE_MINUTE * 5)
            screen = json_data.get('screen', {})
            screen_objects = screen.get('screen_objects', [])
            for screen_object in screen_objects:
                if screen_object.get('type', '') == 'sushi_bar':
                    if screen_object.get('title', '') == category:
                        sub_screen_objects = screen_object.get('screen_objects', [])
                        for sub_screen_object in sub_screen_objects:
                            result.append(self._screen_object_to_item(sub_screen_object,
                                                                      show_format_title=(category == 'Neueste Clips')))
                            pass
                        break
                    pass
                pass

            if category == 'Beliebte Sendungen':
                self._set_sort_method_for_content_type(constants.CONTENT_TYPE_TVSHOWS)
                result = kodimon.sort_items_by_name(result)
            else:
                self._set_sort_method_for_content_type(constants.CONTENT_TYPE_EPISODES)
                result = kodimon.sort_items_by_info_label(result, info_type=kodimon.VideoItem.INFO_AIRED, reverse=True)
            pass

        return result

    @kodimon.RegisterPath('^/play/$')
    def _play(self, path, params, re_match):
        video_id = params.get('id', '')
        if video_id == '':
            raise kodimon.KodimonException("Missing parameter 'id' to play video")

        json_data = self._client.get_video_url(video_id)
        video_url = json_data.get('VideoURL', '')
        if video_url == '':
            raise kodimon.KodimonException("Could not resolve url for video '%s'" % video_id)

        item = kodimon.VideoItem(video_id, video_url)
        return item

    def _load_format_content(self, channel_id, format_id, return_cached_only=False):
        result = {}

        data = self.call_function_cached(
            partial(self._client.get_format_content, self._client.API_V2, channel_id, format_id),
            FunctionCache.ONE_HOUR, return_cached_only=return_cached_only)
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

    @kodimon.RegisterPath('^/(?P<channelid>' + CHANNEL_ID_STRING + ')/library/(?P<formatid>\d+)/$')
    def _get_format_content(self, path, params, re_match):
        self._set_sort_method_for_content_type(constants.CONTENT_TYPE_EPISODES)

        clip_type = params.get('clip_type', 'full')
        page = int(params.get('page', '1'))

        result = []

        channel_id = re_match.group('channelid')
        channel_image = "media/channels/%s.png" % channel_id
        channel_image = self.get_plugin().create_resource_path(channel_image)
        format_id = re_match.group('formatid')

        data = self._load_format_content(channel_id, format_id)
        fanart = data.get('fanart', self.get_fanart())

        if page == 1 and clip_type == 'full':
            # clips
            if 'Clips' in data:
                clips_item = kodimon.DirectoryItem('[B]' + self.localize('7tv.clips') + '[/B]',
                                                   self.create_uri(path, {'clip_type': 'short'}),
                                                   image=channel_image)
                clips_item.set_fanart(fanart)
                result.append(clips_item)
                pass

            # backstage
            if 'Backstage' in data:
                backstage_item = kodimon.DirectoryItem('[B]' + self.localize('7tv.backstage') + '[/B]',
                                                       self.create_uri(path, {'clip_type': 'webexclusive'}),
                                                       image=channel_image)
                backstage_item.set_fanart(fanart)
                result.append(backstage_item)
                pass
            pass

        # test for a possible next page (cached)
        next_page_test = self.call_function_cached(
            partial(self._client.get_format_videos, self._client.API_V2, channel_id, format_id, clip_type,
                    page=page + 1), seconds=FunctionCache.ONE_HOUR)
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
                video_item = self._screen_object_to_item(episode)
                video_list.append(video_item)
                pass
            video_list = kodimon.sort_items_by_info_label(video_list, kodimon.VideoItem.INFO_AIRED, True)
            result.extend(video_list)

            if next_page:
                next_page_item = self.create_next_page_item(page, path, params)
                result.append(next_page_item)
                pass
        else:
            video_list = []
            episodes = self.call_function_cached(
                partial(self._client.get_format_videos, self._client.API_V2, channel_id, format_id, clip_type,
                        page=page), seconds=FunctionCache.ONE_HOUR)
            episodes = episodes.get('objects', [])
            for episode in episodes:
                video_item = self._screen_object_to_item(episode)
                video_list.append(video_item)
                pass
            video_list = kodimon.sort_items_by_info_label(video_list, kodimon.VideoItem.INFO_AIRED, True)
            result.extend(video_list)

            if next_page:
                next_page_item = self.create_next_page_item(page, path, params)
                result.append(next_page_item)
                pass
            pass

        return result

    @kodimon.RegisterPath('^/(?P<channelid>' + CHANNEL_ID_STRING + ')/library/$')
    def _get_channel_formats(self, path, params, re_match):
        self._set_sort_method_for_content_type(constants.CONTENT_TYPE_TVSHOWS)

        result = []

        # load the formats of the given channel
        channel_id = re_match.group('channelid')
        json_data = self.call_function_cached(partial(self._client.get_formats, self._client.API_V2, channel_id),
                                              seconds=FunctionCache.ONE_DAY)
        screen = json_data.get('screen', {})
        screen_objects = screen.get('screen_objects', {})

        for screen_object in screen_objects:
            format_id = screen_object['id'].split(':')
            channel_id = format_id[0]
            format_id = format_id[1]
            format_item = kodimon.DirectoryItem(screen_object['title'],
                                                self.create_uri([channel_id, 'library', format_id]),
                                                image=screen_object['image_url'])

            fanart = self.get_fanart()
            data = self._load_format_content(channel_id, format_id, return_cached_only=True)
            if data is not None:
                fanart = data.get('fanart', self.get_fanart())
                pass
            format_item.set_fanart(fanart)
            context_menu = [contextmenu.create_add_to_favs(self.get_plugin(),
                                                           self.localize(self.LOCAL_FAVORITES_ADD),
                                                           format_item)]
            format_item.set_context_menu(context_menu)
            result.append(format_item)
            pass

        return kodimon.sort_items_by_name(result)

    @kodimon.RegisterPath('^/(?P<channelid>' + CHANNEL_ID_STRING + ')/$')
    def _get_channel_content(self, path, params, re_match):
        channel_id = re_match.group('channelid')

        result = []

        channel_image = "media/channels/%s.png" % channel_id
        channel_image = self.get_plugin().create_resource_path(channel_image)

        # Highlights
        item = kodimon.DirectoryItem(self.localize(self.LOCAL_HIGHLIGHTS),
                                     self.create_uri([channel_id, 'highlights']),
                                     image=channel_image)
        item.set_fanart(self.get_fanart())
        result.append(item)

        # Library
        item = kodimon.DirectoryItem(self.localize(self.LOCAL_LIBRARY),
                                     self.create_uri([channel_id, 'library']),
                                     image=channel_image)
        item.set_fanart(self.get_fanart())
        result.append(item)

        return result

    @kodimon.RegisterPath('^/favs/latest/$')
    def _latest_video(self, path, params, re_match):
        self._set_sort_method_for_content_type(constants.CONTENT_TYPE_EPISODES)

        result = []

        directory_items = self.get_favorite_list().list()

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

        json_data = self._client.get_new_videos(self._client.API_V2, format_ids)
        """
        json_data = self.call_function_cached(partial(self._client.get_new_videos, self._client.API_V2, format_ids),
                                              FunctionCache.ONE_MINUTE * 5)
                                              """
        screen_objects = json_data.get('screen_objects', [])
        for screen_object in screen_objects:
            result.append(self._screen_object_to_item(screen_object, show_format_title=True))
            pass

        return result

    def on_root(self, path, params, re_match):
        result = []

        # favorites and latest videos
        if len(self.get_favorite_list().list()) > 0:
            fav_item = kodimon.DirectoryItem('[B]' + self.localize(self.LOCAL_FAVORITES) + '[/B]',
                                             self.create_uri([self.PATH_FAVORITES, 'list']),
                                             image=self.create_resource_path('media/highlight.png'))
            fav_item.set_fanart(self.get_fanart())
            result.append(fav_item)

            latest_item = kodimon.DirectoryItem('[B]' + self.localize(self.LOCAL_LATEST_VIDEOS) + '[/B]',
                                                self.create_uri(['favs', 'latest']),
                                                image=self.create_resource_path('media/highlight.png'))
            latest_item.set_fanart(self.get_fanart())
            result.append(latest_item)
            pass

        # watch later
        if len(self.get_watch_later_list().list()) > 0:
            fav_item = kodimon.DirectoryItem('[B]' + self.localize(self.LOCAL_WATCH_LATER) + '[/B]',
                                             self.create_uri([self.PATH_WATCH_LATER, 'list']),
                                             image=self.create_resource_path('media/highlight.png'))
            fav_item.set_fanart(self.get_fanart())
            result.append(fav_item)

        # search
        search_item = kodimon.DirectoryItem('[B]' + self.localize(self.LOCAL_SEARCH) + '[/B]',
                                            self.create_uri([self.PATH_SEARCH, 'list']),
                                            image=self.create_resource_path('media/search.png'))
        search_item.set_fanart(self.get_fanart())
        result.append(search_item)

        # channels
        for channel in self._channel_id_list:
            channel_data = self._channel_data.get(channel, {})
            channel_image = "media/channels/%s.png" % channel
            channel_image = self.create_resource_path(channel_image)
            channel_item = kodimon.DirectoryItem(channel_data.get('name', channel),
                                                 self.create_uri(channel),
                                                 image=channel_image)
            channel_item.set_fanart(self.get_fanart())
            result.append(channel_item)
            pass

        return result, {self.RESULT_CACHE_TO_DISC: False}

    def _screen_object_to_item(self, screen_object, show_format_title=False):
        screen_object_type = screen_object.get('type', '')
        if screen_object_type == '':
            raise kodimon.KodimonException('Missing type for screenObject')

        fanart = self.get_fanart()
        format_id = screen_object.get('format_id', screen_object.get('id', '')).split(':')
        if len(format_id) == 2:
            channel_id = format_id[0]
            format_id = format_id[1]
            if channel_id == 'tvog':
                channel_id = 'pro7'
                pass
            data = self._load_format_content(channel_id, format_id, return_cached_only=True)
            fanart = data.get('fanart', self.get_fanart())
            pass

        if screen_object_type == 'video_item_date_no_label' or screen_object_type == 'video_item_date' \
                or screen_object_type == 'video_item_format_no_label' or screen_object_type == 'video_item_format':
            name = screen_object.get('title', screen_object['video_title'])
            if screen_object_type == 'video_item_format_no_label' or show_format_title:
                name = '%s - %s' % (screen_object['format_title'], name)
                pass
            video_item = kodimon.VideoItem(name,
                                           self.create_uri(['play'], {'id': screen_object['id']}),
                                           image=screen_object.get('image_url', ''))
            video_item.set_fanart(fanart)
            video_item.set_duration_in_seconds(int(screen_object.get('duration', '60')))

            date_time = kodimon.parse_iso_8601(screen_object.get('start', '0000-00-00'))
            video_item.set_aired(date_time['year'], date_time['month'], date_time['day'])
            video_item.set_premiered(date_time['year'], date_time['month'], date_time['day'])
            video_item.set_year(date_time['year'])
            try_set_season_and_episode(video_item)

            context_menu = [contextmenu.create_add_to_watch_later(self._plugin,
                                                                  self.localize(self.LOCAL_WATCH_LATER),
                                                                  video_item)]
            video_item.set_context_menu(context_menu)
            return video_item
        elif screen_object_type == 'format_item_home' or screen_object_type == 'format_item':
            format_item = kodimon.DirectoryItem(screen_object['title'],
                                                self.create_uri([channel_id, 'library', format_id]),
                                                image=screen_object['image_url'])
            format_item.set_fanart(fanart)
            context_menu = [contextmenu.create_add_to_favs(self._plugin,
                                                           self.localize(self.LOCAL_FAVORITES_ADD),
                                                           format_item)]
            format_item.set_context_menu(context_menu)
            return format_item

        raise kodimon.KodimonException("Unknown type '%s' for screen_object" % screen_object_type)