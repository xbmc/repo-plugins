__author__ = 'bromix'

import datetime
import json

from resources.lib import nightcrawler
from .client import Client


class Provider(nightcrawler.Provider):
    def __init__(self):
        nightcrawler.Provider.__init__(self)

        self._client = None
        pass

    def on_setup(self, context, mode):
        if mode == 'content-type':
            return ['default', 'episodes']
        pass

    def _get_client(self, context):
        def _access_token():
            return Client().authenticate()

        if not self._client:
            access_data = context.get_access_manager().do_access_token(_access_token)
            self._client = Client(access_data.get('access_token', ''))
            pass

        return self._client

    @nightcrawler.register_path('/category/(?P<category_id>.+?)/')
    @nightcrawler.register_path_value('category_id', unicode)
    @nightcrawler.register_context_value('next_reference_key', unicode, default='')
    def _on_category(self, context, category_id, next_reference_key):
        external_video_urls = {'youtube': 'plugin://plugin.video.youtube/play/?video_id=%s',
                               'vimeo': 'plugin://plugin.video.vimeo/play/?video_id=%s'}

        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        result = []

        video_data = self._get_client(context).get_posts(category_id, next_reference_key)

        for video in video_data['items']:
            video_type = video['type']
            if video_type not in external_video_urls:
                raise nightcrawler.ProviderException("Unknown video type '%s'" % video_type)

            video['type'] = 'video'
            video['uri'] = external_video_urls[video_type] % video['id']
            video['images'].update({'fanart': self.get_fanart(context)})

            result.append(video)
            pass

        next_reference_key = video_data.get('next_reference_key', '')
        if next_reference_key and video_data.get('continue', False):
            new_params = {}
            new_params.update(context.get_params())
            new_params['next_reference_key'] = next_reference_key
            new_context = context.clone(new_params=new_params)

            result.append(nightcrawler.items.create_next_page_item(new_context, fanart=self.get_fanart(new_context)))
            pass

        return result

    @nightcrawler.register_path('/')
    def on_root(self, context):
        result = []

        categories = context.cache_function(context.CACHE_ONE_HOUR, self._get_client(context).get_available)

        make_bold = True
        for category in categories:
            if make_bold:
                category['title'] = '[B]%s[/B]' % category['title']
                make_bold = False
                pass
            category['uri'] = context.create_uri('category/%s' % category['id'])
            category['images'] = {'fanart': self.get_fanart(context)}
            result.append(category)
            pass

        return result

    def get_fanart(self, context):
        return context.create_resource_path('media/fanart.jpg')

    pass
