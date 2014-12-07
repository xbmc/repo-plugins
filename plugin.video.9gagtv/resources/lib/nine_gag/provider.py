__author__ = 'bromix'

import datetime
from functools import partial
import json

from resources.lib.kodion.items import DirectoryItem, VideoItem
from resources.lib.kodion.utils import FunctionCache
from resources.lib import kodion
from .client import Client


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._client = None
        pass

    def _get_client(self, context):
        if not self._client:
            access_manager = context.get_access_manager()
            if access_manager.is_access_token_expired():
                access_token, expires = self._client = Client().authenticate()
                access_manager.update_access_token(access_token, expires)
                self._client = Client(access_token)
            else:
                access_token = access_manager.get_access_token()
                self._client = Client(access_token)
                pass
            pass
        return self._client

    @kodion.RegisterProviderPath('^/category/(?P<category_id>.+?)/$')
    def _on_category(self, context, re_match):
        path = context.get_path()
        params = context.get_params()

        def _get_image(thumbnails):
            # qualities = ['thumbnail_840w', 'thumbnail_480w', 'thumbnail_360w', 'thumbnail_240', 'thumbnail_120w']
            qualities = ['thumbnail_480w', 'thumbnail_360w', 'thumbnail_240', 'thumbnail_120w']
            for quality in qualities:
                if quality in thumbnails:
                    return thumbnails[quality]
                pass

            return ''

        context.set_content_type(kodion.constants.content_type.EPISODES)

        result = []

        category_id = re_match.group('category_id')
        next_reference_key = params.get('next_reference_key', '')
        json_data = self._get_client(context).get_posts(category_id, next_reference_key)

        context.log_debug('client.get_posts(%s, %s)' % (category_id, next_reference_key))
        context.log_debug(json.dumps(json_data))

        data = json_data['data'][0]
        posts = data['posts']
        for post in posts:
            title = post['og_title']
            image = _get_image(post.get('thumbnails', {}))

            video = post['video']
            video_type = video['type']
            if video_type == 'youtube':
                video_id = video['external_id']
                video_url = 'plugin://plugin.video.youtube/?action=play_video&videoid=' + video_id
                pass
            else:
                raise kodion.KodimonException("Unknown video type '%s'" % video_item)

            video_item = VideoItem(title,
                                   video_url,
                                   image=image)
            video_item.set_fanart(self.get_fanart(context))

            # plot
            video_item.set_plot(post.get('og_description', ''))

            # date
            created = datetime.datetime.fromtimestamp(int(post['created']))
            video_item.set_aired(created.year, created.month, created.day)

            # duration
            video = post['video']
            duration = int(video['duration'])
            video_item.set_duration_from_seconds(duration)

            result.append(video_item)
            pass

        end_of_list = data.get('end_of_list', True)
        next_reference_key = data.get('next_reference_key', '')
        if not end_of_list and next_reference_key:
            new_params = {}
            new_params.update(params)
            new_params['next_reference_key'] = next_reference_key
            page = int(params.get('page', 1))

            new_context = context.clone(new_params=new_params)
            next_page_item = kodion.items.create_next_page_item(new_context, page)
            next_page_item.set_fanart(self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    def on_root(self, context, re_match):
        result = []

        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, self._get_client(context).get_available)

        context.log_debug('client.get_available()')
        context.log_debug(json.dumps(json_data))

        categories = json_data.get('data', {}).get('lists', [])
        for category in categories:
            title = category['name']
            category_id = category['list_key']
            category_item = DirectoryItem(title,
                                          context.create_uri(['category', category_id]))
            category_item.set_fanart(self.get_fanart(context))
            result.append(category_item)
            pass

        return result

    def get_fanart(self, context):
        """
            This will return a darker and (with blur) fanart
            :return:
            """
        return context.create_resource_path('media', 'fanart.jpg')

    pass
