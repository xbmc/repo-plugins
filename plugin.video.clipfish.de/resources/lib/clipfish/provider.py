from resources.lib.kodion.utils import FunctionCache, datetime_parser

__author__ = 'bromix'

from resources.lib.clipfish.client import Client
from resources.lib.kodion.items import DirectoryItem, VideoItem, UriItem
from resources.lib import kodion


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)

        self._client = None
        self._local_map.update({'clipfish.categories': 30500,
                                'clipfish.highestrated': 30501,
                                'clipfish.mostviewed': 30502,
                                'clipfish.highlights': 30503,
                                'clipfish.all-videos': 30504,
                                'clipfish.mostrecent': 30505})
        pass

    def get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def get_wizard_supported_views(self):
        return ['default', 'episodes', 'tvshows', 'movies']

    def _do_videos(self, context, json_data, content_type='episodes'):
        result = []

        videos = json_data.get('videos', [])
        for video in videos:
            #video_item = VideoItem(video['title'], video['video_url_wifi_quality'])
            video_item = VideoItem(video['title'], context.create_uri(['play'], {'video_id': video['video_id']}))
            image = video.get('media_content_thumbnail_large', '')
            if content_type == 'movies':
                image = video.get('poster', '')
                pass
            video_item.set_image(image)
            video_item.set_fanart(self.get_fanart(context))
            video_item.set_plot(video['description'])
            video_item.set_duration_from_seconds(int(video['media_length']))
            date = datetime_parser.parse(video['pubDate'])
            video_item.set_year_from_datetime(date)
            video_item.set_aired_from_datetime(date)
            video_item.set_date_from_datetime(date)
            video_item.set_studio('clipfish.de')
            video_item.add_artist('clipfish.de')
            result.append(video_item)
            pass

        list_page_limit = int(json_data.get('list_page_limit', '16'))
        total_num_videos = int(json_data.get('total_num_videos', '0'))
        page = int(context.get_param('page', '1'))
        if page * list_page_limit < total_num_videos:
            next_page_item = kodion.items.NextPageItem(context, page)
            next_page_item.set_fanart(self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    def _do_shows(self, context, json_data, content_type='episodes'):
        result = []

        for show in json_data:
            show_item = DirectoryItem(show['title'],
                                      context.create_uri(['show', str(show['id'])], {'type': content_type}),
                                      image=show['img_topbanner_ipad'])
            show_item.set_fanart(self.get_fanart(context))

            context_menu = [(context.localize(kodion.constants.localize.FAVORITES_ADD),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                  {'item': kodion.items.to_jsons(show_item)}))]
            show_item.set_context_menu(context_menu)

            result.append(show_item)
            pass

        return result

    @kodion.RegisterProviderPath('^/show/(?P<show_id>\d+)/$')
    def _on_show(self, context, re_match):
        content_type = context.get_param('type', 'episodes')
        if content_type == 'movies':
            context.set_content_type(kodion.constants.content_type.MOVIES)
            pass
        else:
            context.set_content_type(kodion.constants.content_type.EPISODES)
            pass

        result = []

        show_id = re_match.group('show_id')
        category = context.get_param('category', 'mostrecent')
        page = int(context.get_param('page', '1'))

        # root of show
        if page == 1 and category == 'mostrecent':
            # highestrated
            new_params = {}
            new_params.update(context.get_params())
            new_params['category'] = 'highestrated'
            highestrated_item = DirectoryItem(
                '[B]' + context.localize(self._local_map['clipfish.highestrated']) + '[/B]',
                context.create_uri(context.get_path(), new_params))
            highestrated_item.set_image(context.create_resource_path('media', 'clipfish.png'))
            highestrated_item.set_fanart(self.get_fanart(context))
            result.append(highestrated_item)

            # mostviewed
            new_params = {}
            new_params.update(context.get_params())
            new_params['category'] = 'mostviewed'
            mostviewed_item = DirectoryItem('[B]' + context.localize(self._local_map['clipfish.mostviewed']) + '[/B]',
                                            context.create_uri(context.get_path(), new_params))
            mostviewed_item.set_image(context.create_resource_path('media', 'clipfish.png'))
            mostviewed_item.set_fanart(self.get_fanart(context))
            result.append(mostviewed_item)
            pass

        client = self.get_client(context)
        json_data = client.get_videos_of_show(show_id=show_id, category=category, page=page)
        result.extend(self._do_videos(context, json_data, content_type))

        return result

    @kodion.RegisterProviderPath('^/category/(?P<category_id>\d+)/$')
    def _on_category(self, context, re_match):
        category_id = re_match.group('category_id')

        # we skip movies with the content type
        if category_id != '19':
            context.set_content_type(kodion.constants.content_type.TV_SHOWS)
            pass
        context.add_sort_method(kodion.constants.sort_method.LABEL)

        result = []

        category_id = re_match.group('category_id')
        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, client.get_categories)
        for category in json_data:
            if category['id'] == category_id:
                specials = category['specials']
                content_type = 'episodes'
                if category_id == '19':
                    content_type = 'movies'
                    pass
                result.extend(self._do_shows(context, specials, content_type))
                break
            pass

        return result

    @kodion.RegisterProviderPath('^/categories/$')
    def _on_categories(self, context, re_match):
        result = []

        client = self.get_client(context)
        json_data = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, client.get_categories)
        for category in json_data:
            title = category['title']
            category_item = DirectoryItem(title, context.create_uri(['category', category['id']]),
                                          image=context.create_resource_path('media', 'categories.png'))
            category_item.set_fanart(self.get_fanart(context))
            result.append(category_item)
            pass

        return result

    @kodion.RegisterProviderPath('^/highlights/$')
    def _on_highlights(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.TV_SHOWS)

        client = self.get_client(context)
        return self._do_shows(context, client.get_highlights())

    @kodion.RegisterProviderPath('^/all-videos/$')
    def _on_all_videos(self, context, re_match):
        result = []

        category = context.get_param('category', '')
        if not category:
            # mostrecent
            mostrecent_item = DirectoryItem(context.localize(self._local_map['clipfish.mostrecent']),
                                            context.create_uri(['all-videos'],
                                                               {'category': 'mostrecent'}),
                                            image=context.create_resource_path('media', 'clipfish.png'))
            mostrecent_item.set_fanart(self.get_fanart(context))
            result.append(mostrecent_item)

            # highestrated
            highestrated_item = DirectoryItem(context.localize(self._local_map['clipfish.highestrated']),
                                              context.create_uri(['all-videos'],
                                                                 {'category': 'highestrated'}),
                                              image=context.create_resource_path('media', 'clipfish.png'))
            highestrated_item.set_fanart(self.get_fanart(context))
            result.append(highestrated_item)

            # mostviewed
            mostviewed_item = DirectoryItem(context.localize(self._local_map['clipfish.mostviewed']),
                                            context.create_uri(['all-videos'],
                                                               {'category': 'mostviewed'}),
                                            image=context.create_resource_path('media', 'clipfish.png'))
            mostviewed_item.set_fanart(self.get_fanart(context))
            result.append(mostviewed_item)
            pass
        else:
            context.set_content_type(kodion.constants.content_type.EPISODES)
            client = self.get_client(context)
            page = int(context.get_param('page', '1'))
            return self._do_videos(context, client.get_all_videos(category=category, page=page))

        return result

    def on_search(self, search_text, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)

        result = []

        category = context.get_param('category', 'mostrecent')
        page = int(context.get_param('page', '1'))

        # root of show
        if page == 1 and category == 'mostrecent':
            # highestrated
            new_params = {}
            new_params.update(context.get_params())
            new_params['category'] = 'highestrated'
            highestrated_item = DirectoryItem(
                '[B]' + context.localize(self._local_map['clipfish.highestrated']) + '[/B]',
                context.create_uri(context.get_path(), new_params))
            highestrated_item.set_image(context.create_resource_path('media', 'clipfish.png'))
            highestrated_item.set_fanart(self.get_fanart(context))
            result.append(highestrated_item)

            # mostviewed
            new_params = {}
            new_params.update(context.get_params())
            new_params['category'] = 'mostviewed'
            mostviewed_item = DirectoryItem('[B]' + context.localize(self._local_map['clipfish.mostviewed']) + '[/B]',
                                            context.create_uri(context.get_path(), new_params))
            mostviewed_item.set_image(context.create_resource_path('media', 'clipfish.png'))
            mostviewed_item.set_fanart(self.get_fanart(context))
            result.append(mostviewed_item)
            pass

        client = self.get_client(context)
        json_data = client.search(search_text, category=category, page=page)
        result.extend(self._do_videos(context, json_data))

        return result

    def _internal_favorite(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.TV_SHOWS)
        return kodion.AbstractProvider._internal_favorite(self, context, re_match)

    @kodion.RegisterProviderPath('^/play/$')
    def on_play(self, context, re_match):
        video_id = context.get_param('video_id', '')
        video_url = self.get_client(context).get_video_url(video_id)
        if video_url:
            uri_item = UriItem(video_url)
            return uri_item
            pass

        return False

    def on_root(self, context, re_match):
        result = []

        # favorites and latest videos
        if len(context.get_favorite_list().list()) > 0:
            fav_item = DirectoryItem('[B]' + context.localize(kodion.constants.localize.FAVORITES) + '[/B]',
                                     context.create_uri([kodion.constants.paths.FAVORITES, 'list']),
                                     image=context.create_resource_path('media', 'favorites.png'))
            fav_item.set_fanart(self.get_fanart(context))
            result.append(fav_item)
            pass

        # categories
        categories_item = DirectoryItem(context.localize(self._local_map['clipfish.categories']),
                                        context.create_uri(['categories']),
                                        image=context.create_resource_path('media', 'categories.png'))
        categories_item.set_fanart(self.get_fanart(context))
        result.append(categories_item)

        # highlights
        highlights_item = DirectoryItem(context.localize(self._local_map['clipfish.highlights']),
                                        context.create_uri(['highlights']),
                                        image=context.create_resource_path('media', 'highlights.png'))
        highlights_item.set_fanart(self.get_fanart(context))
        result.append(highlights_item)

        # all videos
        all_videos_item = DirectoryItem(context.localize(self._local_map['clipfish.all-videos']),
                                        context.create_uri(['all-videos']),
                                        image=context.create_resource_path('media', 'all_videos.png'))
        all_videos_item.set_fanart(self.get_fanart(context))
        result.append(all_videos_item)

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        return result

    pass