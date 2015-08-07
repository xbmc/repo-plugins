__author__ = 'bromix'

from resources.lib.content.client import Client
from resources.lib import nightcrawler


class Provider(nightcrawler.Provider):
    FOCUS_LOCAL_ALL_VIDEOS = 30501
    FOCUS_LOCAL_RELATED_VIDEOS = 30500

    def __init__(self):
        nightcrawler.Provider.__init__(self)
        self._client = None
        pass

    def get_client(self, context):
        if self._client:
            return self._client

        self._client = Client()
        return self._client

    def get_fanart(self, context):
        return context.create_resource_path('media/fanart.jpg')

    def on_setup(self, context, mode):
        if mode == 'content-type':
            return ['default', 'episodes']
        pass

    @nightcrawler.register_path('/play/')
    @nightcrawler.register_context_value('url', str, required=True)
    def on_play(self, context, url):
        video_streams = self.get_client(context).get_video_streams(url)
        return self.select_video_stream(context, video_streams, video_quality_index=[480, 720, 1080])

    def _update_videos(self, context, videos):
        for video in videos:
            video['uri'] = context.create_uri('play', {'url': video['url']})
            video['images'].update({'fanart': self.get_fanart(context)})

            context_menu = [(context.localize(self.FOCUS_LOCAL_RELATED_VIDEOS),
                             'Container.Update(%s)' % context.create_uri('related', {'url': video['url']}))]
            video['context-menu'] = {'items': context_menu}
            pass
        pass

    @nightcrawler.register_path('/related/')
    @nightcrawler.register_context_value('url', str, required=True)
    def on_related(self, context, url):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        client = self.get_client(context)
        videos = context.cache_function(context.CACHE_ONE_HOUR, client.get_related_videos, url)
        self._update_videos(context, videos)
        return videos

    @nightcrawler.register_path('/all-videos/')
    def on_all_videos(self, context):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        client = self.get_client(context)
        videos = context.cache_function(context.CACHE_ONE_HOUR, client.get_all_videos)
        self._update_videos(context, videos)
        return videos

    @nightcrawler.register_path('/category/(?P<category>.+)/')
    @nightcrawler.register_path_value('category', unicode)
    def _on_category(self, context, category):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        client = self.get_client(context)
        videos = context.cache_function(context.CACHE_ONE_HOUR, client.get_videos_by_category, category)
        self._update_videos(context, videos)
        return videos

    @nightcrawler.register_path('/')
    def on_root(self, context):
        result = []

        # all videos
        result.append({'type': 'folder',
                       'title': context.localize(self.FOCUS_LOCAL_ALL_VIDEOS),
                       'uri': context.create_uri('all-videos'),
                       'images': {'thumbnail': context.create_resource_path('media/category.png'),
                                  'fanart': self.get_fanart(context)}})

        # categories
        client = self.get_client(context)
        categories = context.cache_function(context.CACHE_ONE_HOUR/2, client.get_categories)
        for category in categories:
            category.update({'uri': context.create_uri('category/%s' % category['title']),
                             'images': {'thumbnail': context.create_resource_path('media/category.png'),
                                        'fanart': self.get_fanart(context)}})
            result.append(category)
            pass

        return result

    pass