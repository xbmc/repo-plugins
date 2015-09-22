__author__ = 'bromix'

import re

from resources.lib import nightcrawler
from .client import Client


class Provider(nightcrawler.Provider):
    LOCAL_7TV_DRM_NOT_SUPPORTED = 30500

    def __init__(self):
        nightcrawler.Provider.__init__(self)
        self._client = None
        pass

    def on_setup(self, context, mode):
        if mode == 'content-type':
            return ['default', 'episodes', 'tvshows']
        pass

    def _get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def get_fanart(self, context):
        return context.create_resource_path('media/fanart.jpg')

    @nightcrawler.register_path('/watch_later/list/')
    def on_watch_later(self, context):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        context.add_sort_method(context.SORT_METHOD_DATE_ADDED,
                                context.SORT_METHOD_DURATION)
        return super(Provider, self).on_watch_later(context)

    @nightcrawler.register_path('/')
    def on_root(self, context):
        result = []

        # favorites and latest videos
        if len(context.get_favorite_list().list()) > 0:
            result.append({'type': 'folder',
                           'title': '[B]%s[/B]' % context.localize(self.LOCAL_FAVORITES),
                           'uri': context.create_uri(self.PATH_FAVORITES_LIST),
                           'images': {'thumbnail': context.create_resource_path('media/highlight.png'),
                                      'fanart': self.get_fanart(context)}})

            result.append({'type': 'folder',
                           'title': '[B]%s[/B]' % context.localize(self.LOCAL_LATEST_VIDEOS),
                           'uri': context.create_uri('favs/latest'),
                           'images': {'thumbnail': context.create_resource_path('media/highlight.png'),
                                      'fanart': self.get_fanart(context)}})
            pass

        # watch later
        if len(context.get_watch_later_list().list()) > 0:
            result.append({'type': 'folder',
                           'title': '[B]%s[/B]' % context.localize(self.LOCAL_WATCH_LATER),
                           'uri': context.create_uri(self.PATH_WATCH_LATER_LIST),
                           'images': {'thumbnail': context.create_resource_path('media/highlight.png'),
                                      'fanart': self.get_fanart(context)}})
            pass

        # search
        result.append(nightcrawler.items.create_search_item(context, fanart=self.get_fanart(context)))

        # channels
        for channel_id in Client.CHANNEL_ID_LIST:
            channel_data = Client.CHANNEL_DATA[channel_id]
            result.append({'type': 'folder',
                           'title': channel_data['name'],
                           'uri': context.create_uri(channel_id),
                           'images': {'thumbnail': context.create_resource_path('media/channels/%s.png' % channel_id),
                                      'fanart': self.get_fanart(context)}})
            pass

        return result

    def _do_json_result(self, context, json_data, prepend_format=True):
        path = context.get_path()

        result = []
        for title, json_item in json_data.iteritems():
            if title in ['items', 'continue']:
                continue
                pass

            result.append({'type': 'folder',
                           'title': title,
                           'uri': context.create_uri('%s/%s' % (path, title)),
                           'images': {'fanart': self.get_fanart(context)}})
            pass

        items = json_data.get('items', [])
        if len(items) > 0:
            if items[0]['type'] == 'video':
                result.extend(self._do_video_items(context, items, next_page=json_data.get('continue', False),
                                                   prepend_format=prepend_format))
                pass
            elif items[0]['type'] == 'format':
                result.extend(self._do_format_items(context, items))
            pass
        return result

    def _do_video_items(self, context, items, next_page, prepend_format=True):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        result = []
        for item in items:
            # prepend the title
            if prepend_format:
                item['title'] = '%s - %s' % (item['format'], item['title'])
                pass

            item['images']['fanart'] = self.get_fanart(context)
            item['uri'] = context.create_uri('play', {'video_id': item['id']})

            item['context-menu'] = {'items': [(context.localize(self.LOCAL_WATCH_LATER),
                                               'RunPlugin(%s)' % context.create_uri(self.PATH_WATCH_LATER_ADD,
                                                                                    {'item': item}))]}
            result.append(item)
            pass

        if next_page:
            result.append(nightcrawler.items.create_next_page_item(context, fanart=self.get_fanart(context)))
            pass

        return result

    def _do_format_items(self, context, items):
        context.set_content_type(context.CONTENT_TYPE_TV_SHOWS)

        result = []
        for item in items:
            item['type'] = 'folder'
            item['images']['fanart'] = self.get_fanart(context)
            item['uri'] = context.create_uri('%s/library/%s' % (item['channel'], item['id']))

            item['context-menu'] = {'items': [(context.localize(self.LOCAL_FAVORITES_ADD),
                                               'RunPlugin(%s)' % context.create_uri(self.PATH_FAVORITES_ADD,
                                                                                    {'item': item}))]}
            result.append(item)
            pass
        return result

    @nightcrawler.register_path('/(?P<channel_id>%s)/' % Client.CHANNEL_IDS_STRING)
    @nightcrawler.register_path_value('channel_id', unicode)
    def on_channel(self, context, channel_id):
        # add 'Mediathek' (library)
        result = [{'type': 'folder',
                   'title': '[B]%s[/B]' % context.localize(self.LOCAL_LIBRARY),
                   'uri': context.create_uri('%s/library' % channel_id),
                   'images': {'fanart': self.get_fanart(context)}}]

        # add channel based content
        client = self._get_client(context)
        json_data = client.get_homepage(channel_id)

        result.extend(self._do_json_result(context, json_data))
        return result

    @nightcrawler.register_path('/(?P<channel_id>%s)/(?P<category>[a-zA-Z0-9 ]+)/' % Client.CHANNEL_IDS_STRING)
    @nightcrawler.register_path_value('channel_id', unicode)
    @nightcrawler.register_path_value('category', unicode)
    def on_channel_category(self, context, channel_id, category):
        # 'Mediathek'
        if category == 'library':
            json_data = self._get_client(context).get_formats(channel_id)
            pass
        else:
            json_data = self._get_client(context).get_homepage(channel_id)
            json_data = json_data.get(category, {})
            pass

        return self._do_json_result(context, json_data)

    @nightcrawler.register_path('/(?P<channel_id>%s)/library/(?P<format_id>[^\/]+)/' % Client.CHANNEL_IDS_STRING)
    @nightcrawler.register_path_value('channel_id', unicode)
    @nightcrawler.register_path_value('format_id', unicode)
    def on_format_content(self, context, channel_id, format_id):
        client = self._get_client(context)
        json_data = client.get_format_content(channel_id, format_id)
        return self._do_json_result(context, json_data, prepend_format=False)

    @nightcrawler.register_path(
        '/(?P<channel_id>%s)/library/(?P<format_id>[^\/]+)/(?P<category>[^\/]+)/' % Client.CHANNEL_IDS_STRING)
    @nightcrawler.register_path_value('channel_id', unicode)
    @nightcrawler.register_path_value('format_id', unicode)
    @nightcrawler.register_path_value('category', unicode)
    @nightcrawler.register_context_value('page', int, default=1)
    def on_format_content_category(self, context, channel_id, format_id, category, page):
        client = self._get_client(context)
        clip_type = {'Ganze Folgen': 'full',
                     'Clips': 'short',
                     'Backstage': 'webexclusive'}[category]
        json_data = client.get_format_videos(channel_id, format_id, clip_type, page)
        return self._do_json_result(context, json_data, prepend_format=False)

    def on_search(self, context, query):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        client = self._get_client(context)
        json_data = client.search(query)
        result = []

        # we sort the result: show first the formats, full episodes and clips
        for category in ['Sendungen', 'Ganze Folgen', 'Clips']:
            category_data = json_data.get(category, {})
            if category_data:
                result.extend(self._do_json_result(context, category_data))
                pass
            pass

        return result

    @nightcrawler.register_path('/favs/latest/')
    def on_latest_video(self, context):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        items = context.get_favorite_list().list()
        format_ids = []
        for item in items:
            format_ids.append(item['id'])
            pass

        json_data = self._get_client(context).get_new_videos(format_ids)
        return self._do_json_result(context, json_data)

    @nightcrawler.register_path('/play/')
    @nightcrawler.register_context_value('video_id', unicode, required=True)
    def play(self, context, video_id):
        video_streams = self._get_client(context).get_video_url(video_id)

        # check for DRM protection
        if len(video_streams) > 0 and video_streams[0].get('is_protected', False):
            context.get_ui().show_notification(context.localize(self.LOCAL_7TV_DRM_NOT_SUPPORTED))
            return False

        return self.select_video_stream(context, video_streams, video_quality_index=[240, 360, 480, 720])