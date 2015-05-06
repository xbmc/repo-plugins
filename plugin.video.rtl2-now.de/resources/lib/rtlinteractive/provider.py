__author__ = 'bromix'

from resources.lib.kodion.utils import FunctionCache
from resources.lib import kodion
from resources.lib.kodion.items import DirectoryItem, VideoItem, UriItem
from resources.lib.kodion.utils import datetime_parser
from .client import Client, UnsupportedStreamException


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)
        self._client = None

        self._local_map.update({'now.library': 30500,
                                'now.newest': 30501,
                                'now.tips': 30502,
                                'now.top10': 30503,
                                'now.add_to_favs': 30101,
                                'now.watch_later': 30107,
                                'now.exception.drm_not_supported': 30504})
        pass

    def get_wizard_supported_views(self):
        return ['default', 'episodes', 'tvshows']

    def get_client(self, context):
        if not self._client:
            amount = context.get_settings().get_items_per_page()
            self._client = Client(Client.CONFIG_RTL2_NOW, amount=amount)
            pass

        return self._client

    def _list_films(self, context, re_match, json_data, show_format_title=False, sort=True):
        context.get_ui().set_view_mode('videos')

        def _sort_newest(item):
            return item.get_aired()

        context.set_content_type(kodion.constants.content_type.EPISODES)
        context.add_sort_method(kodion.constants.sort_method.UNSORTED,
                                kodion.constants.sort_method.VIDEO_YEAR,
                                kodion.constants.sort_method.VIDEO_RUNTIME)

        result = []

        content = json_data.get('result', {}).get('content', {})
        max_page = int(content.get('maxpage', 1))
        page = int(content.get('page', 1))
        film_list = content.get('filmlist', {})

        result_films = []
        add_next_page_item = True
        keys = sorted(film_list.keys())
        for key in keys:
            film = film_list[key]

            # as soon as we find non-free episodes we don't provide pagination
            # the 'continue' should skip all non-free episodes
            free = str(film.get('free', '0'))
            if free == '0':
                add_next_page_item = False
                continue

            title = film['headlinelong']
            format_title = film['formatlong']
            if show_format_title:
                title = format_title + ' - ' + title
                pass

            film_item = VideoItem(title, context.create_uri(['play'], {'video_id': film['id']}))

            film_item.set_studio(format_title)
            film_item.add_artist(format_title)

            format_id = film['formatid']
            # set image
            image = self.get_client(context).get_config()['images']['format-thumbnail-url'].replace('%FORMAT_ID%',
                                                                                                    format_id)
            pictures = film.get('pictures', [])
            if pictures and isinstance(pictures, dict):
                image = film['pictures']['pic_0']
                image = self.get_client(context).get_config()['images']['episode-thumbnail-url'].replace('%PIC_ID%',
                                                                                                         image)
                pass
            film_item.set_image(image)

            # set fanart
            fanart = self.get_client(context).get_config()['images']['format-fanart-url'].replace('%FORMAT_ID%', format_id)
            film_item.set_fanart(fanart)

            # season and episode
            film_item.set_season(film.get('season', '1'))
            film_item.set_episode(film.get('episode', '1'))

            # aired
            aired = datetime_parser.parse(film['sendestart'])
            film_item.set_aired_from_datetime(aired)
            film_item.set_date_from_datetime(aired)
            film_item.set_year_from_datetime(aired)

            # duration
            duration = datetime_parser.parse(film['duration'])
            film_item.set_duration(duration.hour, duration.minute, duration.second)

            # plot
            film_item.set_plot(film['articlelong'])

            context_menu = [(context.localize(self._local_map['now.watch_later']),
                             'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.WATCH_LATER, 'add'],
                                                                  {'item': kodion.items.to_jsons(film_item)}))]
            film_item.set_context_menu(context_menu)
            result_films.append(film_item)
            pass
        if sort:
            result_films = sorted(result_films, key=_sort_newest, reverse=True)
            pass
        result.extend(result_films)

        if add_next_page_item and page < max_page:
            new_params = {}
            new_params.update(context.get_params())
            new_params['page'] = page + 1
            next_page_item = kodion.items.NextPageItem(context, current_page=page, fanart=self.get_fanart(context))
            result.append(next_page_item)
            pass

        return result

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        video_id = context.get_param('video_id', '')
        if video_id:
            try:
                streams = self.get_client(context).get_film_streams(video_id)
            except UnsupportedStreamException, ex:
                context.get_ui().show_notification(context.localize(self._local_map['now.exception.drm_not_supported']))
                return False

            uri_item = UriItem(streams[0])
            return uri_item

        return False

    @kodion.RegisterProviderPath('^/format/(?P<format_id>\d+)/$')
    def _on_format(self, context, re_match):
        result = []
        format_id = re_match.group('format_id')
        page = int(context.get_param('page', 1))
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR / 2, self.get_client(context).get_films,
                                                     format_id=format_id, page=page)
        result.extend(self._list_films(context, re_match, json_data))
        return result

    @kodion.RegisterProviderPath('^/newest/$')
    def _on_newest(self, context, re_match):
        result = []
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR / 2, self.get_client(context).get_newest)
        result.extend(self._list_films(context, re_match, json_data, show_format_title=True))
        return result

    @kodion.RegisterProviderPath('^/tips/$')
    def _on_tips(self, context, re_match):
        result = []
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR / 2, self.get_client(context).get_tips)
        result.extend(self._list_films(context, re_match, json_data, show_format_title=True, sort=False))
        return result

    @kodion.RegisterProviderPath('^/top10/$')
    def _on_top10(self, context, re_match):
        result = []
        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR / 2, self.get_client(context).get_top_10)
        result.extend(self._list_films(context, re_match, json_data, show_format_title=True, sort=False))
        return result

    @kodion.RegisterProviderPath('^/library/$')
    def _on_library(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.TV_SHOWS)
        context.add_sort_method(kodion.constants.sort_method.LABEL)

        result = []

        json_data = context.get_function_cache().get(FunctionCache.ONE_HOUR, self.get_client(context).get_formats)
        format_list = json_data.get('result', {}).get('content', {}).get('formatlist')
        for key in format_list:
            now_format = format_list[key]
            title = now_format['formatlong']
            format_id = now_format['formatid']
            free_episodes = int(now_format.get('free_episodes', '0'))

            if free_episodes >= 1:
                format_item = DirectoryItem(title,
                                            context.create_uri(['format', format_id]))

                # set image
                image = self.get_client(context).get_config()['images']['format-thumbnail-url'].replace('%FORMAT_ID%',
                                                                                                        format_id)
                format_item.set_image(image)

                # set fanart
                fanart = self.get_client(context).get_config()['images']['format-fanart-url'].replace('%FORMAT_ID%',
                                                                                                         format_id)
                format_item.set_fanart(fanart)

                context_menu = [(context.localize(self._local_map['now.add_to_favs']),
                                 'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.FAVORITES, 'add'],
                                                                      {'item': kodion.items.to_jsons(format_item)}))]
                format_item.set_context_menu(context_menu)
                result.append(format_item)
                pass
            pass

        return result

    def on_search(self, search_text, context, re_match):
        context.get_ui().set_view_mode('videos')
        result = []

        json_data = self.get_client(context).search(search_text)
        list = json_data.get('result', {}).get('content', {}).get('list', {})
        for key in list:
            item = list[key]
            title = item['result']
            format_id = item['formatid']
            search_item = DirectoryItem(title,
                                        context.create_uri(['format', format_id]))
            search_item.set_fanart(self.get_fanart(context))
            result.append(search_item)
            pass

        return result

    def on_root(self, context, re_match):
        result = []

        # favorites
        if len(context.get_favorite_list().list()) > 0:
            fav_item = kodion.items.FavoritesItem(context, fanart=self.get_fanart(context))
            result.append(fav_item)
            pass

        # watch later
        if len(context.get_watch_later_list().list()) > 0:
            watch_later_item = kodion.items.WatchLaterItem(context, fanart=self.get_fanart(context))
            result.append(watch_later_item)
            pass

        client = self.get_client(context)

        # shows (A-Z)
        if 'library' in client.get_config()['supports']:
            library_item = DirectoryItem(context.localize(self._local_map['now.library']),
                                         context.create_uri(['library']),
                                         image=context.create_resource_path('media', 'library.png'))
            library_item.set_fanart(self.get_fanart(context))
            result.append(library_item)
            pass

        # newest
        if 'new' in client.get_config()['supports']:
            newest_item = DirectoryItem(context.localize(self._local_map['now.newest']),
                                        context.create_uri(['newest']),
                                        image=context.create_resource_path('media', 'newest.png'))
            newest_item.set_fanart(self.get_fanart(context))
            result.append(newest_item)
            pass

        # tips
        if 'tips' in client.get_config()['supports']:
            tips_item = DirectoryItem(context.localize(self._local_map['now.tips']),
                                      context.create_uri(['tips']),
                                      image=context.create_resource_path('media', 'tips.png'))
            tips_item.set_fanart(self.get_fanart(context))
            result.append(tips_item)
            pass

        # top 10
        if 'top10' in client.get_config()['supports']:
            top10_item = DirectoryItem(context.localize(self._local_map['now.top10']),
                                       context.create_uri(['top10']),
                                       image=context.create_resource_path('media', 'top10.png'))
            top10_item.set_fanart(self.get_fanart(context))
            result.append(top10_item)
            pass

        # search
        if 'search' in client.get_config()['supports']:
            search_item = kodion.items.SearchItem(context, fanart=self.get_fanart(context))
            result.append(search_item)
            pass

        return result

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    pass