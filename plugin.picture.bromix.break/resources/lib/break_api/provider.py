from resources.lib.break_api import Client
from resources.lib.kodimon import DirectoryItem, VideoItem, ImageItem
from resources.lib.kodimon.helper import FunctionCache

__author__ = 'bromix'

from resources.lib import kodimon


class Provider(kodimon.AbstractProvider):
    def __init__(self):
        kodimon.AbstractProvider.__init__(self)

        self._client = Client()
        pass

    def get_fanart(self):
        return self.create_resource_path('media', 'fanart.jpg')

    def _feed_to_item(self, json_data):
        result = []

        data = json_data['data']['data']
        for item in data:
            gallery_item = DirectoryItem(item['title'],
                                         self.create_uri(['show', str(item['id'])]))
            gallery_item.set_fanart(self.get_fanart())
            image = item.get('thumbnails', [])
            if len(image) > 0:
                image = image[0].get('url', '')
                gallery_item.set_image(image)
                pass
            result.append(gallery_item)
            pass

        return result

    @kodimon.RegisterPath('^/show/(?P<gallery_id>.*)/$')
    def _on_show(self, path, params, re_match):
        result = []

        gallery_id = re_match.group('gallery_id')
        json_data = self.get_function_cache().get(FunctionCache.ONE_WEEK, self._client.get_gallery, gallery_id)
        collection = json_data['data']['contentCollection']
        for item in collection:
            title = item['contentTitle']
            image_url = item['contentStaticUrl']
            image_item = ImageItem(title,
                                   image_url)
            image_item.set_fanart(self.get_fanart())
            result.append(image_item)
            pass

        return result

    def on_root(self, path, params, re_match):
        result = []

        page = int(params.get('page', 1))
        gallery_id = self.get_function_cache().get(FunctionCache.ONE_WEEK, self._client.get_gallery_id)
        json_data = self.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.get_feed, gallery_id, page)
        result.extend(self._feed_to_item(json_data))

        # test next page
        next_page = page + 1
        json_data = self.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.get_feed, gallery_id,
                                                  next_page)
        next_page_result = self._feed_to_item(json_data)
        if len(next_page_result) > 0:
            next_page_item = self.create_next_page_item(page, path, params)
            result.append(next_page_item)
            pass

        return result

    pass
