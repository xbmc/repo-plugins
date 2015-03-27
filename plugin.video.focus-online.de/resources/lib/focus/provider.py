__author__ = 'bromix'

import datetime
from resources.lib import kodion
from resources.lib.focus.client import Client
from resources.lib.kodion.items import VideoItem, UriItem
from resources.lib.kodion.items.directory_item import DirectoryItem
from resources.lib.kodion.utils import FunctionCache


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)
        self._local_map.update({'focus.related': 30500,
                                'focus.all-videos': 30501})
        self._client = None
        pass

    def get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        def _compare(item):
            vq = context.get_settings().get_video_quality(quality_map_override={0: 480, 1: 720})
            return vq - item['q']

        url = context.get_param('url')

        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 15, client.get_url_data, url)
        video_streams = client.get_video_streams_from_data(json_data)
        video_stream = kodion.utils.find_best_fit(video_streams, _compare)
        return UriItem(video_stream['url'])

    def _do_videos(self, context, json_data):
        result = []
        for json_item in json_data:
            title = json_item.get('overhead', json_item['headline'])
            url = json_item['url']
            video_item = VideoItem(title, context.create_uri(['play'], {'url': url}))
            video_item.set_fanart(self.get_fanart(context))
            video_item.set_image(json_item['image']['url_hdpi'])
            video_item.set_duration_from_seconds(int(json_item['duration']))
            video_item.set_plot(json_item['text'])
            published = datetime.datetime.fromtimestamp(json_item['timestamp'])
            video_item.set_aired(published.year, published.month, published.day)
            video_item.set_date(published.year, published.month, published.day, published.hour, published.minute,
                                published.second)
            video_item.set_year(published.year)
            video_item.set_studio('FOCUS Online')
            video_item.add_artist('FOCUS Online')

            context_menu = [(context.localize(self._local_map['focus.related']),
                             'Container.Update(%s)' % context.create_uri(['related'], {'url': url}))]
            video_item.set_context_menu(context_menu)
            result.append(video_item)
            pass
        return result

    @kodion.RegisterProviderPath('^/related/$')
    def _on_related(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        url = context.get_param('url')
        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 15, client.get_url_data, url)
        json_data = client.get_related_from_data(json_data)
        return self._do_videos(context, json_data)

    @kodion.RegisterProviderPath('^/all-videos/$')
    def _on_all_videos(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, client.get_root_data)
        json_data = client.get_all_videos(json_data)
        return self._do_videos(context=context, json_data=json_data)

    @kodion.RegisterProviderPath('^/category/(?P<category>.+)/$')
    def _on_category(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        category = re_match.group('category')
        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, client.get_root_data)
        json_data = client.get_videos_from_data(json_data, category)
        return self._do_videos(context=context, json_data=json_data)

    def on_root(self, context, re_match):
        result = []

        # all videos
        all_videos_item = DirectoryItem('[B]' + context.localize(self._local_map['focus.all-videos']) + '[/B]',
                                        context.create_uri(['all-videos']))
        all_videos_item.set_image(context.create_resource_path('media', 'category.png'))
        all_videos_item.set_fanart(self.get_fanart(context))
        result.append(all_videos_item)

        # categories
        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, client.get_root_data)
        categories = client.get_categories_from_data(json_data)
        for category in categories:
            category_item = DirectoryItem(category, context.create_uri(['category', category]))
            category_item.set_image(context.create_resource_path('media', 'category.png'))
            category_item.set_fanart(self.get_fanart(context))
            result.append(category_item)
            pass

        return result

    pass