__author__ = 'bromix'

from resources.lib.content import Client
from resources.lib import nightcrawler


class Provider(nightcrawler.Provider):
    def __init__(self):
        nightcrawler.Provider.__init__(self)

        self._client = None
        pass

    def get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def on_setup(self, context, mode):
        if mode == 'content-type':
            return ['default', 'episodes']
        pass

    def get_fanart(self, context):
        return context.create_resource_path('media/fanart.jpg')

    @nightcrawler.register_path('/play/')
    @nightcrawler.register_context_value('video_id', unicode, required=True)
    def on_play(self, context, video_id):
        video_streams = self.get_client(context).get_video_streams(video_id)
        return self.select_video_stream(context, video_streams, video_quality_index=[240, 360, 480, 720, 1080])

    @nightcrawler.register_path('/feed/(?P<feed_id>.*)/')
    @nightcrawler.register_path_value('feed_id', int)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_feed(self, context, feed_id, page):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        result = []

        videos = context.cache_function(context.CACHE_ONE_MINUTE, self.get_client(context).get_feed, feed_id, page)
        for video in videos:
            video['uri'] = context.create_uri('play', {'video_id': video['id']})
            video['images'].update({'fanart': self.get_fanart(context)})
            result.append(video)
            pass

        # test next page
        next_page = page + 1
        feed_result = context.cache_function(context.CACHE_ONE_MINUTE, self.get_client(context).get_feed, feed_id,
                                             next_page)
        if len(feed_result) > 0:
            result.append(nightcrawler.items.create_next_page_item(context, fanart=self.get_fanart(context)))
            pass

        return result

    @nightcrawler.register_context_value('page', int, default=1)
    def on_search(self, context, query, page):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        result = []

        video_items = context.cache_function(context.CACHE_ONE_MINUTE, self.get_client(context).search, query=query,
                                             page=page)

        for video_item in video_items['items']:
            video_item['uri'] = context.create_uri('play', {'video_id': video_item['id']})
            video_item['images'].update({'fanart': self.get_fanart(context)})
            result.append(video_item)
            pass

        if video_items.get('continue', False):
            result.append(nightcrawler.items.create_next_page_item(context, fanart=self.get_fanart(context)))
            pass

        return result

    @nightcrawler.register_path('/')
    def on_root(self, context):
        result = []

        categories = context.cache_function(context.CACHE_ONE_DAY, self.get_client(context).get_home)
        for category in categories:
            category['uri'] = context.create_uri('feed/%d' % category['id'])
            category['images'] = {'fanart': self.get_fanart(context)}
            result.append(category)
            pass

        # search
        search_item = nightcrawler.items.create_search_item(context, fanart=self.get_fanart(context))
        result.append(search_item)

        return result

    pass
