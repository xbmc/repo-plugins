from resources.lib.break_api import Client

from resources.lib.kodion.items import DirectoryItem, VideoItem, UriItem, NextPageItem
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
            title = item['title']
            video_id = str(item['id'])
            video_item = VideoItem(title,
                                   context.create_uri(['play'], {'video_id': video_id}))
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

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        def _compare(item):
            vq = context.get_settings().get_video_quality()
            return vq - item['height']

        video_id = context.get_param('video_id')
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

    def on_search(self, search_text, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)

        result = []

        import xml.etree.ElementTree as ET
        page = int(context.get_param('page', '1'))
        xml = self._client.search(search_text, page=page)
        root = ET.fromstring(xml)
        search_results = root.find('SearchResults')
        if search_results is not None:
            for search_result in search_results:
                title = search_result.find('Title').text
                video_id = search_result.find('ID').text
                video_item = VideoItem(title,
                                       context.create_uri(['play'], {'video_id': video_id}))
                video_item.set_fanart(self.get_fanart(context))

                description = search_result.find('Description')
                if description is not None:
                    video_item.set_plot(description.text)
                    pass

                image = search_result.find('Thumbnail')
                if image is not None:
                    video_item.set_image(image.text)
                    pass
                result.append(video_item)
                pass
            pass

        # next page
        total_pages = root.find('TotalPages')
        if total_pages is not None:
            total_pages = int(total_pages.text)
            if page < total_pages:
                next_page_item = NextPageItem(context, page)
                next_page_item.set_fanart(self.get_fanart(context))
                result.append(next_page_item)
                pass
            pass

        return result

    def on_root(self, context, re_match):
        result = []

        json_data = context.get_function_cache().get(FunctionCache.ONE_DAY, self._client.get_home)
        collection = json_data['data']['data']['collection']
        make_bold = True
        for item in collection:
            title = item['name']
            if title != u'Galleries':
                item_id = str(item['id'])
                if make_bold:
                    title = '[B]%s[/B]' % title
                    make_bold = False
                    pass
                feed_item = DirectoryItem(title,
                                          context.create_uri(['feed', item_id]))
                feed_item.set_fanart(self.get_fanart(context))
                result.append(feed_item)
                pass
            pass

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        search_item.set_name('[B]%s[/B]' % search_item.get_name())
        result.append(search_item)

        return result

    pass
