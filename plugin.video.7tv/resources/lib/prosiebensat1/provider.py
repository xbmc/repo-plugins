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


def convert_to_aired(date_string):
    _data = date_string.split('T')
    return _data[0]


class Provider(kodimon.AbstractProvider):
    __CHANNEL_ID_STRING__ = 'pro7|sat1|kabel1|sixx|sat1gold|prosiebenmaxx'

    def __init__(self, plugin=None):
        kodimon.AbstractProvider.__init__(self, plugin)

        self.set_localization({'7tv.popular_shows': 30500,
                               '7tv.current_entire_episodes': 30501,
                               '7tv.newest_clips': 30502,
                               '7tv.clips': 30503})

        self._client = Client()

        self._channel_id_list = ['pro7', 'sat1', 'kabel1', 'sixx', 'sat1gold', 'prosiebenmaxx']
        self._channel_data = {'pro7': {'name': u'ProSieben'},
                              'sat1': {'name': u'SAT.1'},
                              'kabel1': {'name': u'kabel eins'},
                              'sixx': {'name': u'sixx'},
                              'sat1gold': {'name': u'SAT.1 Gold'},
                              'prosiebenmaxx': {'name': u'ProSieben MAXX'}}

        pass

    def on_watch_later(self, path, params, re_match):
        self.set_content_type(constants.CONTENT_TYPE_EPISODES)
        self.add_sort_method(constants.SORT_METHOD_UNSORTED, constants.SORT_METHOD_DATE)
        pass

    def on_search(self, search_text, path, params, re_match):
        self.set_content_type(constants.CONTENT_TYPE_EPISODES)
        self.add_sort_method(constants.SORT_METHOD_UNSORTED,
                             constants.SORT_METHOD_VIDEO_RUNTIME,
                             constants.SORT_METHOD_VIDEO_YEAR)

        result = []
        """
        Cache the search result at least for a minute
        """
        json_data = self.call_function_cached(partial(self._client.search, search_text), FunctionCache.ONE_MINUTE)
        screen = json_data.get('screen', {})
        screen_objects = screen.get('screen_objects', [])
        for screen_object in screen_objects:
            sub_screen_objects = screen_object.get('screen_objects', [])
            for sub_screen_object in sub_screen_objects:
                title = screen_object.get('title', '')
                if title == 'Sendungen':
                    channel_reference = sub_screen_object.get('channel_reference', [])
                    channel_id = channel_reference[0]
                    format_path = "/%s/library/" % channel_id
                    result.append(self._screen_object_to_item(format_path, sub_screen_object))
                    pass
                elif title == 'Ganze Folgen':
                    channel_reference = sub_screen_object.get('channel_reference', [])
                    channel_id = channel_reference[0]
                    result.append(self._screen_object_to_item('/play/', sub_screen_object))
                    pass
                elif title == 'Highlights':
                    channel_reference = sub_screen_object.get('channel_reference', [])
                    channel_id = channel_reference[0]
                    result.append(self._screen_object_to_item('/play/', sub_screen_object))
                    pass
                pass
            pass

        return result

    @kodimon.RegisterPath('^/(?P<channelid>' + __CHANNEL_ID_STRING__ + ')/highlights/?$')
    def _get_channel_highlights(self, path, params, re_match):
        channel_id = re_match.group('channelid')

        result = []

        channel_image = "media/channels/%s.png" % channel_id
        channel_image = self.get_plugin().create_resource_path(channel_image)

        category = params.get('category', None)
        if category is None:
            """
            Popular Shows
            """
            item = kodimon.DirectoryItem(name=self.localize('7tv.popular_shows'),
                                         path=kodimon.create_content_path([channel_id, 'highlights']),
                                         params={'category': 'Beliebte Sendungen'},
                                         image=channel_image)
            item.set_fanart(self.get_plugin().get_fanart())
            result.append(item)

            """
            Current Entire Episodes
            """
            item = kodimon.DirectoryItem(name=self.localize('7tv.current_entire_episodes'),
                                         path=kodimon.create_content_path([channel_id, 'highlights']),
                                         params={'category': 'Aktuelle ganze Folgen'},
                                         image=channel_image)
            item.set_fanart(self.get_plugin().get_fanart())
            result.append(item)

            """
            Newest Clips
            """
            item = kodimon.DirectoryItem(name=self.localize('7tv.newest_clips'),
                                         path=kodimon.create_content_path([channel_id, 'highlights']),
                                         params={'category': 'Neueste Clips'},
                                         image=channel_image)
            item.set_fanart(self.get_plugin().get_fanart())
            result.append(item)
        else:
            json_data = self._client.get_homepage(channel_id)
            screen = json_data.get('screen', {})
            screen_objects = screen.get('screen_objects', [])
            for screen_object in screen_objects:
                if screen_object.get('type', '') == 'sushi_bar':
                    if screen_object.get('title', '') == category:
                        sub_screen_objects = screen_object.get('screen_objects', [])
                        for sub_screen_object in sub_screen_objects:
                            format_path = kodimon.create_content_path([channel_id, 'library'])
                            result.append(self._screen_object_to_item(format_path, sub_screen_object))
                            pass
                        break
                    pass
                pass

            if category == 'Beliebte Sendungen':
                result = kodimon.sort_items_by_name(result)
                pass
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

        item = kodimon.VideoItem(name=video_id,
                                 path='/')
        item.set_url(video_url)

        return item

    @kodimon.RegisterPath('^/(?P<channelid>' + __CHANNEL_ID_STRING__ + ')/library/(?P<formatid>\d+)/$')
    def _get_format_content(self, path, params, re_match):
        self.set_content_type(constants.CONTENT_TYPE_EPISODES)
        self.add_sort_method(constants.SORT_METHOD_UNSORTED,
                             constants.SORT_METHOD_VIDEO_YEAR,
                             constants.SORT_METHOD_VIDEO_RUNTIME)

        clip_type = params.get('clip_type', 'full')
        page = int(params.get('page', '1'))

        result = []

        channel_id = unicode(re_match.group('channelid'))
        channel_image = "media/channels/%s.png" % channel_id
        channel_image = self.get_plugin().create_resource_path(channel_image)

        format_id = unicode(re_match.group('formatid'))
        if page == 1 and clip_type == 'full':
            clips_item = kodimon.DirectoryItem(name='[B]' + self.localize('7tv.clips') + '[/B]',
                                               path=kodimon.create_content_path(path),
                                               params={'clip_type': 'short'},
                                               image=channel_image)
            clips_item.set_fanart(self.call_function_cached(
                partial(self._client.get_format_background, channel_id=channel_id, format_id=format_id),
                FunctionCache.ONE_DAY))
            if not clips_item.get_fanart():
                clips_item.set_fanart(self._plugin.get_fanart())
            result.append(clips_item)
            pass

        """
        Cache the video (full and clips) for at least 1 hour.
        """
        per_page = self._plugin.get_settings().get_int(constants.SETTING_ITEMS_PER_PAGE, 50, lambda x: (x+1)*5)
        json_data = self.call_function_cached(
            partial(self._client.get_format_videos, channel_id, format_id, clip_type=clip_type, page=page, per_page=per_page),
            FunctionCache.ONE_HOUR)
        videos = json_data.get('objects', [])
        video_list = []
        for video in videos:
            video_list.append(self._screen_object_to_item(path, video))
            pass

        video_list = kodimon.sort_items_by_info_label(video_list, kodimon.VideoItem.INFO_AIRED, True)
        result.extend(video_list)

        if self._client.has_more_videos(channel_id, format_id, clip_type=clip_type, current_page=page, per_page=per_page):
            new_params = {}
            new_params.update(params)
            new_params['page'] = str(page + 1)
            name = self.localize(self.LOCAL_NEXT_PAGE)
            if name.find('%d') != -1:
                name %= page + 1
                pass
            next_page_item = kodimon.DirectoryItem(name=name,
                                                   path=path,
                                                   params=new_params)
            result.append(next_page_item)
            pass

        return result

    """
    Content of one category of one channel
    
    <Channel> = pro7|sat1|...
    <Category> = highlights|library|archive
    
    <Channel>/<Category>/*
    """

    @kodimon.RegisterPath('^/(?P<channelid>' + __CHANNEL_ID_STRING__ + ')/library/$')
    def _get_channel_content_by_category(self, path, params, re_match):
        self.set_content_type(constants.CONTENT_TYPE_TVSHOWS)
        self.add_sort_method(constants.SORT_METHOD_LABEL_IGNORE_THE)

        channel_id = re_match.group('channelid')
        category = params.get('category', 'Aktuell')

        result = []

        """
        Cache the formats (Galileo...) for at least a day.
        """
        json_data = self.call_function_cached(partial(self._client.get_format, channel_id),
                                              seconds=FunctionCache.ONE_DAY)
        screen = json_data.get('screen', {})
        screen_objects = screen.get('screen_objects', {})

        if len(screen_objects) > 0:
            screen_objects = screen_objects[0]
            screen_objects = screen_objects.get('screen_objects', {})

            for screen_object in screen_objects:
                if screen_object.get('type', '') == 'grid_page' and screen_object.get('title', '') == category:

                    sub_screen_objects = screen_object.get('screen_objects', [])
                    for sub_screen_object in sub_screen_objects:
                        result.append(self._screen_object_to_item(path, sub_screen_object))
                        pass
                    pass
                pass
            pass

        return kodimon.sort_items_by_name(result)

    """
    Content of one channel
    
    <Channel> = pro7|sat1|...
    
    <Channel>/Highlights
    <Channel>/Library
    <Channel>/Archive
    """

    @kodimon.RegisterPath('^/(?P<channelid>' + __CHANNEL_ID_STRING__ + ')/$')
    def _get_channel_content(self, path, params, re_match):
        channel_id = re_match.group('channelid')

        result = []

        channel_image = "media/channels/%s.png" % channel_id
        channel_image = self.get_plugin().create_resource_path(channel_image)

        """
        highlights
        """
        item = kodimon.DirectoryItem(name=self.localize(self.LOCAL_HIGHLIGHTS),
                                     path=kodimon.create_content_path([channel_id, 'highlights']),
                                     image=channel_image)
        item.set_fanart(self.get_plugin().get_fanart())
        result.append(item)

        """
        Library
        """
        item = kodimon.DirectoryItem(name=self.localize(self.LOCAL_LIBRARY),
                                     path=kodimon.create_content_path([channel_id, 'library']),
                                     params={'category': 'Aktuell'},
                                     image=channel_image)
        item.set_fanart(self.get_plugin().get_fanart())
        result.append(item)

        """
        Archive
        """
        item = kodimon.DirectoryItem(name=self.localize(self.LOCAL_ARCHIVE),
                                     path=kodimon.create_content_path([channel_id, 'library']),
                                     params={'category': 'Archiv'},
                                     image=channel_image)
        item.set_fanart(self.get_plugin().get_fanart())
        result.append(item)

        return result

    @kodimon.RegisterPath('^/favs/latest/$')
    def _latest_video(self, path, params, re_match):
        self.set_content_type(constants.CONTENT_TYPE_EPISODES)
        self.add_sort_method(constants.SORT_METHOD_LABEL_IGNORE_THE, constants.SORT_METHOD_DATE)

        result = []

        directory_items = self.get_favorite_list().list()

        format_ids = []
        for directory_item in directory_items:
            path = directory_item.get_path()
            re_match = re.match('/(' + self.__CHANNEL_ID_STRING__ + ')/(library)/(\d+)/', path)
            if re_match is not None:
                channel_id = re_match.group(1)
                format_id = re_match.group(3)
                format_ids.append("%s:%s" % (channel_id, format_id))
                pass
            pass

        json_data = self._client.get_new_videos(format_ids)
        screen_objects = json_data.get('screen_objects', [])
        for screen_object in screen_objects:
            result.append(self._screen_object_to_item(path, screen_object))
            pass

        return result

    def on_root(self, path, params, re_match):
        result = []

        # favorites and latest videos
        if len(self.get_favorite_list().list()) > 0:
            fav_item = kodimon.DirectoryItem(name='[B]' + self.localize(self.LOCAL_FAVORITES) + '[/B]',
                                             path=kodimon.create_content_path(self.PATH_FAVORITES, 'list'),
                                             image=self.get_plugin().create_resource_path('media/highlight.png'))
            fav_item.set_fanart(self.get_plugin().get_fanart())
            result.append(fav_item)

            latest_item = kodimon.DirectoryItem(name='[B]' + self.localize(self.LOCAL_LATEST_VIDEOS) + '[/B]',
                                                path=kodimon.create_content_path('favs', 'latest'),
                                                image=self.get_plugin().create_resource_path('media/highlight.png'))
            latest_item.set_fanart(self.get_plugin().get_fanart())
            result.append(latest_item)
            pass

        # watch later
        if len(self.get_watch_later_list().list()) > 0:
            fav_item = kodimon.DirectoryItem(name='[B]' + self.localize(self.LOCAL_WATCH_LATER) + '[/B]',
                                             path=kodimon.create_content_path(self.PATH_WATCH_LATER, 'list'),
                                             image=self.get_plugin().create_resource_path('media/highlight.png'))
            fav_item.set_fanart(self.get_plugin().get_fanart())
            result.append(fav_item)

        # search
        search_item = kodimon.DirectoryItem('[B]' + self.localize(self.LOCAL_SEARCH) + '[/B]',
                                            kodimon.create_content_path(self.PATH_SEARCH, 'list'),
                                            image=self.get_plugin().create_resource_path('media/search.png'))
        search_item.set_fanart(self.get_plugin().get_fanart())
        result.append(search_item)

        # channels
        for channel in self._channel_id_list:
            channel_data = self._channel_data.get(channel, {})
            channel_image = "media/channels/%s.png" % channel
            channel_image = self.get_plugin().create_resource_path(channel_image)
            channel_item = kodimon.DirectoryItem(name=channel_data.get('name', channel),
                                                 path=kodimon.create_content_path(channel),
                                                 image=channel_image)
            channel_item.set_fanart(self.get_plugin().get_fanart())
            result.append(channel_item)
            pass

        return result, {self.RESULT_CACHE_TO_DISC: False}

    def _screen_object_to_item(self, path, screen_object):
        screen_object_type = screen_object.get('type', '')
        if screen_object_type == '':
            raise kodimon.KodimonException('Missing type for screenObject')

        if screen_object_type == 'format_item' or screen_object_type == 'format_item_home':
            format_id = screen_object['id']
            format_id = format_id.split(':')
            channel_id = format_id[0]
            format_id = format_id[1]

            format_item = kodimon.DirectoryItem(name=unicode(screen_object['title']),
                                                path=kodimon.create_content_path([path, format_id]),
                                                image=screen_object.get('image_url', u''))

            fanart = self.call_function_cached(
                partial(self._client.get_format_background, channel_id=channel_id, format_id=format_id),
                FunctionCache.ONE_MINUTE, True)
            format_item.set_fanart(fanart)
            if not format_item.get_fanart():
                format_item.set_fanart(self.get_plugin().get_fanart())

            try:
                context_menu = [contextmenu.create_add_to_favs(self._plugin,
                                                               self.localize(self.LOCAL_FAVORITES_ADD),
                                                               format_item)]

                format_item.set_context_menu(context_menu)
            except UnicodeEncodeError, ex:
                kodimon.log(format_item.get_name())
                pass
            return format_item
        elif screen_object_type == 'video_item_date' or screen_object_type == 'video_item_format_no_label' \
                or screen_object_type == 'video_item_format':
            name = screen_object.get('title', None)
            if name is None:
                name = screen_object.get('video_title', '')
                pass

            """
            prepend the format name to the episode
            """
            format_name = None
            if screen_object_type == 'video_item_format_no_label' or screen_object_type == 'video_item_format' \
                    or screen_object.get('video_item_type', None) is None:
                format_name = screen_object.get('format_title', None)
                if format_name:
                    name = format_name + ' - ' + name
                    pass
                pass

            video_item = kodimon.VideoItem(name=name,
                                           path=kodimon.create_content_path('play'),
                                           params={'id': screen_object['id']},
                                           image=screen_object.get('image_url', u''))
            video_item.set_duration_in_seconds(int(screen_object.get('duration', '60')))

            date_time = kodimon.parse_iso_8601(screen_object.get('start', '0000-00-00'))
            video_item.set_aired(date_time['year'], date_time['month'], date_time['day'])
            video_item.set_premiered(date_time['year'], date_time['month'], date_time['day'])
            video_item.set_year(date_time['year'])
            if format_name:
                video_item.set_info(kodimon.VideoItem.INFO_TVSHOWTITLE, format_name)

            format_id = screen_object.get('format_id', '')
            format_id = format_id.split(':')
            channel_id = format_id[0]
            format_id = format_id[1]
            fanart = self.call_function_cached(
                partial(self._client.get_format_background, channel_id=channel_id, format_id=format_id),
                seconds=FunctionCache.ONE_DAY)
            video_item.set_fanart(fanart)
            if not video_item.get_fanart():
                video_item.set_fanart(self.get_plugin().get_fanart())

            try_set_season_and_episode(video_item)
            context_menu = [contextmenu.create_add_to_watch_later(self._plugin,
                                                                  self.localize(self.LOCAL_WATCH_LATER),
                                                                  video_item)]

            video_item.set_context_menu(context_menu)
            return video_item

        raise kodimon.KodimonException("Unknown type '%s' for screen_object" % screen_object_type)