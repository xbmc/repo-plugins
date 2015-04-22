from resources.lib.break_api import Client

from resources.lib.kodion.items import DirectoryItem, VideoItem, UriItem
from resources.lib.kodion.utils import FunctionCache
from resources.lib.kodion import constants

__author__ = 'bromix'

from resources.lib import kodion


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._client = Client()
        pass

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def _feed_to_item(self, json_data, context):
        result = []

        data = json_data['data']['data']
        for item in data:
            video_item = VideoItem(item['title'],
                                   context.create_uri(['play', str(item['id'])]))
            video_item.set_fanart(self.get_fanart(context))
            video_item.set_plot(item['description'])
            image = item.get('thumbnails', [])
            if len(image) > 0:
                image = image[0].get('url', '')
                video_item.set_image(image)
                pass
            result.append(video_item)
            pass

        return result

    @kodion.RegisterProviderPath('^/play/(?P<video_id>.*)/$')
    def _on_play(self, context, re_match):
        def _compare(item):
            vq = context.get_settings().get_video_quality()
            return vq - item['height']

        video_id = re_match.group('video_id')
        video_urls = self._client.get_video_urls(video_id)
        video_url = kodion.utils.find_best_fit(video_urls, _compare)
        uri_item = UriItem(video_url['url'])
        return uri_item

    @kodion.RegisterProviderPath('^/feed/(?P<feed_id>.*)/$')
    def _on_feed(self, context, re_match):
        params = context.get_params()
        path = context.get_path()

        context.set_content_type(kodion.constants.content_type.EPISODES)
        result = []

        feed_id = int(re_match.group('feed_id'))
        page = int(params.get('page', 1))

        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.get_feed, feed_id, page)
        result.extend(self._feed_to_item(json_data, context))

        # test next page
        next_page = page + 1
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.get_feed, feed_id, next_page)
        next_page_result = self._feed_to_item(json_data, context)
        if len(next_page_result) > 0:
            next_page_item = kodion.items.NextPageItem(context, page, fanart=self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    def on_root(self, context, re_match):
        result = []

        json_data = context.get_function_cache().get(FunctionCache.ONE_DAY, self._client.get_home)
        collection = json_data['data']['data']['collection']
        for item in collection:
            title = item['name']
            if title != u'Galleries':
                item_id = str(item['id'])
                feed_item = DirectoryItem(title,
                                          context.create_uri(['feed', item_id]))
                feed_item.set_fanart(self.get_fanart(context))
                result.append(feed_item)
                pass
            pass

        return result

    pass
