from resources.lib.kodion.exceptions import KodionException

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.kodion.items import DirectoryItem, VideoItem, UriItem
from resources.lib.kodion.utils import datetime_parser
from .client import Client, UnsupportedStreamException


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)
        self._client = None
        self._channel_ids = ['rtl', 'rtl2', 'vox', 'ntv', 'nitro', 'superrtl']

        self._local_map.update({'nowtv.add_to_favs': 30101,
                                'nowtv.exception.drm_not_supported': 30500,
                                'nowtv.buy.title': 30501,
                                'nowtv.buy.text': 30502})
        pass

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def get_client(self, context):
        if not self._client:
            amount = context.get_settings().get_items_per_page()
            self._client = Client(amount=amount)
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

    def _videos_to_items(self, context, videos, channel_config):
        result = []

        show_only_free_videos = context.get_settings().get_bool('nowtv.videos.only_free', False)
        for video in videos:
            if show_only_free_videos and not video['free']:
                continue

            video_params = {'video_path': video['path'],
                            'video_id': str(video['id'])}

            title = video['title']
            if not video['free']:
                title = '[B][%s][/B] - %s' % (video['price'], title)
                video_params['free'] = '0'
                video_params['price'] = video['price']
                pass
            video_item = VideoItem(title, context.create_uri([channel_config['id'], 'play'], video_params))
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
            result.append(video_item)
            pass

        return result

    def _on_channel_format_list(self, context, channel_config, format_list_id):
        context.set_content_type(kodion.content_type.EPISODES)

        result = []

        channel_id = channel_config['id']
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)
        videos = client.get_videos_by_format_list(channel_config, format_list_id).get('items', [])

        return self._videos_to_items(context, videos, channel_config)

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/formatlist/(?P<format_list_id>.+)/$')
    def on_channel_format_list(self, context, re_match):
        channel_id = re_match.group('channel_id')
        format_list_id = re_match.group('format_list_id')
        channel_config = Client.CHANNELS[channel_id]
        return self._on_channel_format_list(context, channel_config, format_list_id)

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/format/(?P<format_id>.+)/$')
    def on_channel_format(self, context, re_match):
        channel_id = re_match.group('channel_id')
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)

        # try to process tabs
        seo_url = context.get_param('seoUrl', '')
        if seo_url:
            format_tabs = client.get_format_tabs(channel_config, seo_url)
            # with only one tab we could display the whole list of videos
            if len(format_tabs) == 1:
                format_tab = format_tabs[0]
                return self._on_channel_format_list(context, channel_config, format_tab['id'])

            # show the tabs/sections
            tabs = []
            for format_tab in format_tabs:
                if format_tab['type'] == 'season' or format_tab['type'] == 'year':
                    tab_item = DirectoryItem(format_tab['title'],
                                             context.create_uri([channel_id, 'formatlist', str(format_tab['id'])]))
                    tab_item.set_image(format_tab['images']['thumb'])
                    tab_item.set_fanart(format_tab['images']['fanart'])
                    tabs.append(tab_item)
                    pass
                elif format_tab['type'] == 'year':
                    tab_item = DirectoryItem(format_tab['title'],
                                             context.create_uri([channel_id, 'yearlist', str(format_tab['id'])]))
                    tab_item.set_image(format_tab['images']['thumb'])
                    tab_item.set_fanart(format_tab['images']['fanart'])
                    tabs.append(tab_item)
                    pass
                else:
                    raise KodionException('Unknown type "%s" for tab' % format_tab['type'])
                pass
            return tabs

        format_id = re_match.group('format_id')

        return []

    def _do_formats(self, context, json_formats):
        result = []
        formats = json_formats.get('items', [])
        for format_data in formats:
            format_title = format_data['title']
            params = {}
            if format_data.get('seoUrl', ''):
                params['seoUrl'] = format_data['seoUrl']
                pass
            format_item = DirectoryItem(format_title,
                                        context.create_uri([format_data['station'], 'format', str(format_data['id'])], params))
            format_item.set_image(format_data['images']['thumb'])
            format_item.set_fanart(format_data['images']['fanart'])
            result.append(format_item)
            context_menu = [(context.localize(self._local_map['nowtv.add_to_favs']),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                  {'item': kodion.items.to_jsons(format_item)}))]
            format_item.set_context_menu(context_menu)
            pass
        return result

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/formats/$')
    def on_channel_formats(self, context, re_match):
        context.add_sort_method(kodion.sort_method.LABEL)

        result = []

        channel_id = re_match.group('channel_id')
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)

        json_formats = client.get_formats(channel_config)
        return self._do_formats(context, json_formats)

    def on_search(self, search_text, context, re_match):
        context.add_sort_method(kodion.sort_method.LABEL)

        client = self.get_client(context)
        json_formats = client.search(search_text)
        return self._do_formats(context, json_formats)

    def on_root(self, context, re_match):
        result = []

        # favorites
        if len(context.get_favorite_list().list()) > 0:
            fav_item = kodion.items.FavoritesItem(context, fanart=self.get_fanart(context))
            fav_item.set_name('[B]%s[/B]' % fav_item.get_name())
            result.append(fav_item)
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