import datetime
import time

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.kodion.items import DirectoryItem, VideoItem, UriItem
from resources.lib.kodion.utils import datetime_parser
from resources.lib.kodion.exceptions import KodionException
from .client import Client, UnsupportedStreamException


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)
        self._client = None
        self._is_logged_in = False
        self._channel_ids = ['rtl', 'rtl2', 'vox', 'ntv', 'nitro', 'superrtl']

        self._local_map.update({'nowtv.add_to_favs': 30101,
                                'nowtv.add_to_watch_later': 30107,
                                'nowtv.remove_from_favs': 30108,
                                'nowtv.remove_from_watch_later': 30108,
                                'nowtv.exception.drm_not_supported': 30500,
                                'nowtv.buy.title': 30501,
                                'nowtv.buy.text': 30502})
        pass

    def is_logged_in(self):
        return self._is_logged_in

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def get_client(self, context):
        # set the items per page (later)
        items_per_page = context.get_settings().get_items_per_page()

        # reset all login relevant data if the credentials have changed
        access_manager = context.get_access_manager()
        access_token = access_manager.get_access_token()
        if access_manager.is_new_login_credential() or access_manager.is_access_token_expired():
            # reset access_token
            access_manager.update_access_token('')
            # we clear the cache, so none cached data of an old account will be displayed.
            context.get_function_cache().clear()
            # reset the client
            self._client = None
            pass

        if not self._client and access_manager.has_login_credentials():
            username, password = access_manager.get_login_credentials()
            access_token = access_manager.get_access_token()
            user_id = context.get_settings().get_string('nowtv.user.id', '')

            # create a new access_token
            if (not access_token or not user_id) and username and password:
                data = Client().login(username, password)
                access_token = data.get('token', '')
                user_id = str(data.get('id', ''))
                if not access_token and not user_id:
                    # context.get_ui().show_notification()
                    context.get_ui().open_settings()
                    return None

                context.get_settings().set_string('nowtv.user.id', user_id)
                expires_in = time.time() + 60 * 60  # 1 hour
                access_manager.update_access_token(access_token=access_token, unix_timestamp=expires_in)
                pass

            # create new client with access token
            if access_token and user_id:
                self._client = Client(token=access_token, user_id=user_id)
                pass

            self._is_logged_in = access_token != ''
            pass

        # fallback client with no login
        if not self._client:
            self._client = Client(amount=items_per_page)
            pass

        return self._client

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/play/$')
    def on_play(self, context, re_match):
        channel_id = re_match.group('channel_id')
        channel_config = Client.CHANNELS[channel_id]
        video_id = context.get_param('video_id', '')
        video_path = context.get_param('video_path', '')

        if context.get_param('free', '1') == '0':
            price = context.get_param('price', '')
            title = context.localize(self._local_map['nowtv.buy.title']) % price
            context.get_ui().on_ok(title, context.localize(self._local_map['nowtv.buy.text']))
            return False

        if video_id and video_path:
            try:
                video_streams = self.get_client(context).get_video_streams(channel_config, video_path)
                video_stream = kodion.utils.select_stream(context, video_streams)
                return UriItem(video_stream['url'])
            except UnsupportedStreamException, ex:
                context.get_ui().show_notification(context.localize(self._local_map['now.exception.drm_not_supported']))
                return False

        return False

    def _videos_to_items(self, context, videos, prepend_format_title=False):
        result = []

        # show only free videos if not logged in or or the setting is enabled
        show_only_free_videos = not self.is_logged_in() or context.get_settings().get_bool('nowtv.videos.only_free',
                                                                                           False)
        for video in videos:
            if show_only_free_videos and not video['free'] and not video['payed']:
                continue

            video_params = {'video_path': video['path'],
                            'video_id': str(video['id'])}

            title = video['title']
            if prepend_format_title:
                title = '%s - %s' % (video['format'], title)
                pass
            if not video['free'] and not video['payed']:
                title = '[B][%s][/B] - %s' % (video['price'], title)
                video_params['free'] = '0'
                video_params['price'] = video['price']
                pass
            video_item = VideoItem(title, context.create_uri([video['channel'], 'play'], video_params))
            duration = datetime_parser.parse(video['duration'])
            video_item.set_duration(duration.hour, duration.minute, duration.second)

            published = datetime_parser.parse(video['published'])
            video_item.set_aired_from_datetime(published)
            video_item.set_date_from_datetime(published)
            video_item.set_year_from_datetime(published)

            video_item.set_studio(video['format'])
            video_item.add_artist(video['format'])
            video_item.set_episode(video['episode'])
            video_item.set_season(video['season'])
            video_item.set_plot(video['plot'])
            video_item.set_image(video['images']['thumb'])
            video_item.set_fanart(video['images']['fanart'])

            context_menu = []
            if self.is_logged_in():
                if context.get_path() == '/nowtv/watch_later/list/':
                    context_menu = [(context.localize(self._local_map['nowtv.remove_from_watch_later']),
                                     'RunPlugin(%s)' % context.create_uri(['nowtv', 'watch_later', 'delete'],
                                                                          {'video_id': video['id']}))]
                    pass
                else:
                    context_menu = [(context.localize(self._local_map['nowtv.add_to_watch_later']),
                                     'RunPlugin(%s)' % context.create_uri(['nowtv', 'watch_later', 'add'],
                                                                          {'video_id': video['id']}))]
                    pass
            else:
                context_menu = [(context.localize(self._local_map['nowtv.add_to_watch_later']),
                                 'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.WATCH_LATER, 'add'],
                                                                      {'item': kodion.items.to_jsons(video_item)}))]
                pass

            if context_menu:
                video_item.set_context_menu(context_menu)
                pass

            result.append(video_item)
            pass

        return result

    def _on_channel_format_list(self, context, channel_config, format_list_id):
        context.set_content_type(kodion.content_type.EPISODES)

        channel_id = channel_config['id']
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)
        videos = client.get_videos_by_format_list(channel_config, format_list_id).get('items', [])

        return self._videos_to_items(context, videos)

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/format/(?P<format_id>\d+)/list/(?P<format_list_id>.+)/$')
    def on_channel_format_per_list(self, context, re_match):
        channel_id = re_match.group('channel_id')
        format_list_id = re_match.group('format_list_id')
        channel_config = Client.CHANNELS[channel_id]
        return self._on_channel_format_list(context, channel_config, format_list_id)

    @kodion.RegisterProviderPath(
        '^/(?P<channel_id>[a-z0-9]+)/format/(?P<format_id>\d+)/year/(?P<year>\d+)/month/(?P<month>\d+)/$')
    def on_channel_format_per_year_and_month(self, context, re_match):
        context.set_content_type(kodion.content_type.EPISODES)

        def _get_days_of_month(_year, _month):
            _days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            _days = _days_per_month[_month - 1]

            if _month == 2 and (_year % 4 == 0 and _year % 100 != 0 or _year % 400 == 0):
                return 29

            return _days

        channel_id = re_match.group('channel_id')
        format_id = re_match.group('format_id')
        year = int(re_match.group('year'))
        month = int(re_match.group('month'))

        start_date_param = context.get_param('start')
        start_date = datetime.datetime(*time.strptime(start_date_param, '%Y-%m-%d %H:%M:%S')[:6])

        end_date_param = context.get_param('end')
        end_date = datetime.datetime(*time.strptime(end_date_param, '%Y-%m-%d %H:%M:%S')[:6])

        day = _get_days_of_month(year, month)
        if year == end_date.year and month == end_date.month:
            day = min(day, end_date.day)
            pass

        start_date_query = '%d-%02d-01 00:00:00' % (year, month)
        end_date_query = '%d-%02d-%02d 23:59:59' % (year, month, day)

        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)
        videos = client.get_videos_by_date_filter(channel_config, format_id, start_date_query, end_date_query).get(
            'items', [])

        return self._videos_to_items(context, videos)

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/format/(?P<format_id>\d+)/year/(?P<year>\d+)/$')
    def on_channel_format_per_year(self, context, re_match):
        result = []

        channel_id = re_match.group('channel_id')
        format_id = re_match.group('format_id')
        year = re_match.group('year')

        start_date_param = context.get_param('start')
        start_date = datetime.datetime(*time.strptime(start_date_param, '%Y-%m-%d %H:%M:%S')[:6])

        end_date_param = context.get_param('end')
        end_date = datetime.datetime(*time.strptime(end_date_param, '%Y-%m-%d %H:%M:%S')[:6])

        image = context.get_param('image', '')
        fanart = context.get_param('fanart', self.get_fanart(context))

        for month in range(start_date.month, end_date.month + 1):
            month_text = context.localize(30510 + month - 1)
            month_item = DirectoryItem(month_text,
                                       # /[CHANNEL_ID]/format/[FORMAT_ID]/year/[year]/month/[month]/
                                       context.create_uri(
                                           [channel_id, 'format', format_id, 'year', year, 'month', str(month)],
                                           {'start': start_date_param,
                                            'end': end_date_param}),
                                       image=image,
                                       fanart=fanart)
            result.append(month_item)
            pass

        # reverse order of the month
        result = result[::-1]

        return result

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/format/(?P<format_id>\d+)/$')
    def on_channel_format(self, context, re_match):
        channel_id = re_match.group('channel_id')
        format_id = re_match.group('format_id')
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)

        # try to process tabs
        seo_url = context.get_param('seoUrl', '')
        if not seo_url:
            raise KodionException('seoUrl missing')

        format_tabs = client.get_format_tabs(channel_config, seo_url)

        # only on season tab -> show the content directly
        if len(format_tabs) == 1 and format_tabs[0]['type'] == 'tab':
            format_tab = format_tabs[0]
            return self._on_channel_format_list(context, channel_config, format_tab['id'])

        # show the tabs/sections
        tabs = []
        for format_tab in format_tabs:
            if format_tab['type'] == 'tab':
                tab_item = DirectoryItem(format_tab['title'],
                                         # /[CHANNEL_ID]/format/[FORMAT_ID]/list/[FORMAT_LIST_ID]/
                                         context.create_uri(
                                             [channel_id, 'format', format_id, 'list', str(format_tab['id'])]))
                tab_item.set_image(format_tab['images']['thumb'])
                tab_item.set_fanart(format_tab['images']['fanart'])
                tabs.append(tab_item)
                pass
            elif format_tab['type'] == 'date-span':
                tab_title = format_tab['title']
                image = format_tab['images']['thumb']
                fanart = format_tab['images']['fanart']
                tab_item = DirectoryItem(tab_title,
                                         # /[CHANNEL_ID]/format/[FORMAT_ID]/year/[YEAR]/
                                         context.create_uri([channel_id, 'format', format_id, 'year', tab_title],
                                                            {'start': format_tab['start'],
                                                             'end': format_tab['end'],
                                                             'image': image,
                                                             'fanart': fanart}))
                tab_item.set_image(image)
                tab_item.set_fanart(fanart)
                tabs.append(tab_item)
                pass
            else:
                raise KodionException('Unknown type "%s" for tab' % format_tab['type'])
            pass

        return tabs

    # converts the list of formats into list items
    def _do_formats(self, context, json_formats):
        result = []
        formats = json_formats.get('items', [])

        # show only free videos if not logged in or or the setting is enabled
        show_only_free_videos = not self.is_logged_in() or context.get_settings().get_bool('nowtv.videos.only_free',
                                                                                           False)

        for format_data in formats:
            if show_only_free_videos and not format_data['free']:
                continue

            format_title = format_data['title']
            params = {}
            if format_data.get('seoUrl', ''):
                params['seoUrl'] = format_data['seoUrl']
                pass
            format_item = DirectoryItem(format_title,
                                        # /rtl/format/2/
                                        context.create_uri([format_data['station'], 'format', str(format_data['id'])],
                                                           params))
            format_item.set_image(format_data['images']['thumb'])
            format_item.set_fanart(format_data['images']['fanart'])
            result.append(format_item)

            if self.is_logged_in():
                if context.get_path() == '/nowtv/favorites/list/':
                    context_menu = [(context.localize(self._local_map['nowtv.remove_from_favs']),
                                     'RunPlugin(%s)' % context.create_uri(['nowtv', 'favorites', 'delete'],
                                                                          {'format_id': format_data['id']}))]
                    pass
                else:
                    context_menu = [(context.localize(self._local_map['nowtv.add_to_favs']),
                                     'RunPlugin(%s)' % context.create_uri(['nowtv', 'favorites', 'add'],
                                                                          {'format_id': format_data['id']}))]
                    pass
            else:
                context_menu = [(context.localize(self._local_map['nowtv.add_to_favs']),
                                 'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                      {'item': kodion.items.to_jsons(format_item)}))]
                pass
            format_item.set_context_menu(context_menu)
            pass
        return result

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/formats/$')
    def on_channel_formats(self, context, re_match):
        context.add_sort_method(kodion.sort_method.LABEL)

        channel_id = re_match.group('channel_id')
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)

        json_formats = client.get_formats(channel_config)
        return self._do_formats(context, json_formats)

    """
    method = [list|delete|add]
    params = format_id = [FORMAT_ID]
    """
    @kodion.RegisterProviderPath('^/nowtv/favorites/(?P<method>.*)/$')
    def on_favorites(self, context, re_match):
        method = re_match.group('method')
        if not method in ['list', 'delete', 'add']:
            raise KodionException('Unknown method "%s" for favorites')

        client = self.get_client(context)
        format_id = context.get_param('format_id', '')

        if method == 'list':
            context.add_sort_method(kodion.sort_method.LABEL)
            json_formats = client.get_favorites()
            return self._do_formats(context, json_formats)
        elif method == 'delete':
            client.remove_favorite_format(format_id=format_id)
            context.get_ui().refresh_container()
            pass
        elif method == 'add':
            client.add_favorite_format(format_id=format_id)
            pass

        return True

    """
    method = [list|delete|add]
    params = video_id = [VIDEO_ID]
    """
    @kodion.RegisterProviderPath('^/nowtv/watch_later/(?P<method>.*)/$')
    def _on_watch_later(self, context, re_match):
        method = re_match.group('method')
        if not method in ['list', 'delete', 'add']:
            raise KodionException('Unknown method "%s" for watch later')

        client = self.get_client(context)
        video_id = context.get_param('video_id', '')

        if method == 'list':
            context.set_content_type(kodion.content_type.EPISODES)
            json_videos = client.get_watch_later().get('items', [])
            return self._videos_to_items(context, json_videos, prepend_format_title=True)
        elif method == 'delete':
            client.remove_watch_later_video(video_id=video_id)
            context.get_ui().refresh_container()
            pass
        elif method == 'add':
            client.add_watch_later_video(video_id=video_id)
            pass

        return True

    def on_search(self, search_text, context, re_match):
        context.add_sort_method(kodion.sort_method.LABEL)

        client = self.get_client(context)
        json_formats = client.search(search_text)
        return self._do_formats(context, json_formats)

    def on_root(self, context, re_match):
        result = []

        client = self.get_client(context)
        if self.is_logged_in():
            # online favorites
            fav_item = DirectoryItem('[B]%s[/B]' % context.localize(kodion.constants.localize.FAVORITES),
                                     context.create_uri(['nowtv', 'favorites', 'list']),
                                     image=context.create_resource_path('media/favorites.png'),
                                     fanart=self.get_fanart(context))
            result.append(fav_item)

            # online watch later
            wl_item = DirectoryItem('[B]%s[/B]' % context.localize(kodion.constants.localize.WATCH_LATER),
                                    context.create_uri(['nowtv', 'watch_later', 'list']),
                                    image=context.create_resource_path('media/watch_later.png'),
                                    fanart=self.get_fanart(context))
            result.append(wl_item)
            pass
        else:
            # offline favorites
            if len(context.get_favorite_list().list()) > 0:
                fav_item = kodion.items.FavoritesItem(context, fanart=self.get_fanart(context))
                fav_item.set_name('[B]%s[/B]' % fav_item.get_name())
                result.append(fav_item)
                pass

            # offline watch later
            if len(context.get_watch_later_list().list()) > 0:
                wl_item = kodion.items.WatchLaterItem(context, fanart=self.get_fanart(context))
                wl_item.set_name('[B]%s[/B]' % wl_item.get_name())
                result.append(wl_item)
                pass
            pass

        # watch later
        if len(context.get_watch_later_list().list()) > 0:
            watch_later_item = kodion.items.WatchLaterItem(context, fanart=self.get_fanart(context))
            result.append(watch_later_item)
            pass

        # list channels
        for channel_id in self._channel_ids:
            channel_config = Client.CHANNELS[channel_id]
            channel_id = channel_config['id']
            channel_title = channel_config['title']
            channel_item = DirectoryItem(channel_title, context.create_uri([channel_id, 'formats']))
            channel_item.set_fanart(context.create_resource_path('media', channel_id, 'background.jpg'))
            channel_item.set_image(context.create_resource_path('media', channel_id, 'logo.png'))
            result.append(channel_item)
            pass

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        return result

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    pass