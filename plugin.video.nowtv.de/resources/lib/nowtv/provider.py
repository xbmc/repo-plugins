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
                                'nowtv.exception.drm_not_supported': 30500})
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
        if video_id and video_path:
            try:
                video_streams = self.get_client(context).get_video_streams(channel_config, video_path)
                video_stream = kodion.utils.select_stream(context, video_streams)
                return UriItem(video_stream['url'])
            except UnsupportedStreamException, ex:
                context.get_ui().show_notification(context.localize(self._local_map['now.exception.drm_not_supported']))
                return False

        return False

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/format/(?P<format_id>.+)/$')
    def on_channel_format(self, context, re_match):
        context.set_content_type(kodion.content_type.EPISODES)
        result = []

        channel_id = re_match.group('channel_id')
        format_id = re_match.group('format_id')
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)

        videos = client.get_videos(channel_config, format_id).get('items', [])
        for video in videos:
            video_item = VideoItem(video['title'], context.create_uri([channel_id, 'play'],
                                                                      {'video_path': video['path'],
                                                                       'video_id': str(video['id'])}))
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

    @kodion.RegisterProviderPath('^/(?P<channel_id>[a-z0-9]+)/formats/$')
    def on_channel_formats(self, context, re_match):
        context.add_sort_method(kodion.sort_method.LABEL)

        result = []

        channel_id = re_match.group('channel_id')
        channel_config = Client.CHANNELS[channel_id]
        client = self.get_client(context)

        formats = client.get_formats(channel_config).get('items', [])
        for format_data in formats:
            format_title = format_data['title']
            format_item = DirectoryItem(format_title,
                                        context.create_uri([channel_id, 'format', str(format_data['id'])]))
            format_item.set_image(format_data['images']['thumb'])
            format_item.set_fanart(format_data['images']['fanart'])
            result.append(format_item)
            context_menu = [(context.localize(self._local_map['nowtv.add_to_favs']),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                  {'item': kodion.items.to_jsons(format_item)}))]
            format_item.set_context_menu(context_menu)
            pass

        return result

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

        return result

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    pass