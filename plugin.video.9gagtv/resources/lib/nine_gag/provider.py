import datetime
from functools import partial
import json
from resources.lib.kodimon import DirectoryItem, VideoItem, KodimonException
from resources.lib.kodimon.helper import FunctionCache

__author__ = 'bromix'

from resources.lib import kodimon


class Provider(kodimon.AbstractProvider):
    def __init__(self, plugin=None):
        kodimon.AbstractProvider.__init__(self, plugin)

        from . import Client
        access_manager = self.get_access_manager()

        if access_manager.is_access_token_expired():
            access_token, expires = self._client = Client().authenticate()
            access_manager.update_access_token(access_token, expires)
            self._client = Client(access_token)
        else:
            access_token = access_manager.get_access_token()
            self._client = Client(access_token)
            pass

        pass

    @kodimon.RegisterPath('^/category/(?P<category_id>.+?)/$')
    def _on_category(self, path, params, re_match):
        def _get_image(thumbnails):
            # qualities = ['thumbnail_840w', 'thumbnail_480w', 'thumbnail_360w', 'thumbnail_240', 'thumbnail_120w']
            qualities = ['thumbnail_480w', 'thumbnail_360w', 'thumbnail_240', 'thumbnail_120w']
            for quality in qualities:
                if quality in thumbnails:
                    return thumbnails[quality]
                pass

            return ''

        self.set_content_type(kodimon.constants.CONTENT_TYPE_EPISODES)

        result = []

        category_id = re_match.group('category_id')
        next_reference_key = params.get('next_reference_key', '')
        json_data = self._client.get_posts(category_id, next_reference_key)

        self.log('client.get_posts(%s, %s)' % (category_id, next_reference_key), kodimon.constants.LOG_DEBUG)
        self.log(json.dumps(json_data), kodimon.constants.LOG_DEBUG)

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
                raise KodimonException("Unknown video type '%s'" % video_item)

            video_item = VideoItem(title,
                                   video_url,
                                   image=image)
            video_item.set_fanart(self.get_fanart())

            # plot
            video_item.set_plot(post.get('og_description', ''))

            # date
            created = datetime.datetime.fromtimestamp(int(post['created']))
            video_item.set_aired(created.year, created.month, created.day)

            # duration
            video = post['video']
            duration = int(video['duration'])
            video_item.set_duration_in_seconds(duration)

            result.append(video_item)
            pass

        end_of_list = data.get('end_of_list', True)
        next_reference_key = data.get('next_reference_key', '')
        if not end_of_list and next_reference_key:
            new_params = {}
            new_params.update(params)
            new_params['next_reference_key'] = next_reference_key
            page = int(params.get('page', 1))
            next_page_item = self.create_next_page_item(page,
                                                        path,
                                                        new_params)
            result.append(next_page_item)
            pass

        return result

    def on_root(self, path, params, re_match):
        result = []

        json_data = self.call_function_cached(partial(self._client.get_available), seconds=FunctionCache.ONE_HOUR)

        self.log('client.get_available()', kodimon.constants.LOG_DEBUG)
        self.log(json.dumps(json_data), kodimon.constants.LOG_DEBUG)

        categories = json_data.get('data', {}).get('lists', [])
        for category in categories:
            title = category['name']
            category_id = category['list_key']
            category_item = DirectoryItem(title,
                                          self.create_uri(['category', category_id]))
            category_item.set_fanart(self.get_fanart())
            result.append(category_item)
            pass

        return result

    def get_fanart(self):
        """
            This will return a darker and (with blur) fanart
            :return:
            """
        return self.create_resource_path('media', 'fanart.jpg')

    pass
