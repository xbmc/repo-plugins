from resources.lib.break_api import Client
from resources.lib.kodion.items import DirectoryItem, VideoItem, ImageItem
from resources.lib.kodion.utils import FunctionCache

__author__ = 'bromix'

from resources.lib import kodion


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._client = Client()
        pass

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def _feed_to_item(self, json_data, context):
        result = []

        data = json_data['data']['data']
        for item in data:
            gallery_item = DirectoryItem(item['title'],
                                         context.create_uri(['show', str(item['id'])]))
            gallery_item.set_fanart(self.get_fanart(context))
            image = item.get('thumbnails', [])
            if len(image) > 0:
                image = image[0].get('url', '')
                gallery_item.set_image(image)
                pass
            result.append(gallery_item)
            pass

        return result

    @kodion.RegisterProviderPath('^/show/(?P<gallery_id>.*)/$')
    def _on_show(self, context, re_match):
        result = []

        gallery_id = re_match.group('gallery_id')
        json_data = context.get_function_cache().get(FunctionCache.ONE_WEEK, self._client.get_gallery, gallery_id)
        collection = json_data['data']['contentCollection']
        for item in collection:
            title = item['contentTitle']
            image_url = item['contentStaticUrl']
            image_item = ImageItem(title,
                                   image_url)
            image_item.set_fanart(self.get_fanart(context))
            result.append(image_item)
            pass

        return result

    def on_root(self, context, re_match):
        params = context.get_params()
        path = context.get_path()

        result = []

        page = int(params.get('page', 1))
        gallery_id = context.get_function_cache().get(FunctionCache.ONE_WEEK, self._client.get_gallery_id)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.get_feed, gallery_id, page)
        result.extend(self._feed_to_item(json_data, context))

        # test next page
        next_page = page + 1
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.get_feed, gallery_id,
                                                  next_page)
        next_page_result = self._feed_to_item(json_data, context)
        if len(next_page_result) > 0:
            next_page_item = kodion.items.NextPageItem(context, page, fanart=self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    pass
