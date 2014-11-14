from resources.lib.kodimon import DirectoryItem, VideoItem

__author__ = 'bromix'

from resources.lib import kodimon
from resources.lib.kodimon.helper import FunctionCache
from resources.lib.kodimon import constants, contextmenu


class Provider(kodimon.AbstractProvider):
    def __init__(self, plugin=None):
        kodimon.AbstractProvider.__init__(self, plugin)

        from . import Client

        self._client = Client()
        pass

    def _create_video_item_from_post(self, post):
        def _read_custom_fields(_post, field_name):
            custom_fields = post.get('custom_fields', {})
            field = custom_fields.get(field_name, [])
            if len(field) >= 1:
                return field[0]
            return u''

        stream_id = _read_custom_fields(post, 'Streaming')
        movie_item = VideoItem(post['title'],
                               self.create_uri('play', {'stream_id': stream_id}),
                               image=post['thumbnail'])

        # stars
        stars = _read_custom_fields(post, 'Stars')
        if stars:
            stars = stars.split(',')
            for star in stars:
                movie_item.add_cast(star.strip())
                pass
            pass

        # director
        director = _read_custom_fields(post, 'Regisseur')
        if director:
            movie_item.set_director(director.strip())
            pass

        # imdb
        imdb = _read_custom_fields(post, 'IMDb-Link')
        if imdb:
            movie_item.set_imdb_id(imdb)
            pass

        # rating
        rating = _read_custom_fields(post, 'IMDb-Bewertung')
        if rating:
            rating = rating.replace(',', '.')
            movie_item.set_rating(rating)
            pass

        # year
        year = _read_custom_fields(post, 'Jahr')
        if year:
            # There was one case with '2006/2012' as a result. Therefore we split every year.
            year = year.split('/')[0]
            movie_item.set_year(year)
            pass

        # fanart
        movie_item.set_fanart(_read_custom_fields(post, 'featured_img_all'))

        # plot
        plot = kodimon.strip_html_from_text(post['content'])
        movie_item.set_plot(plot)

        # date added - in this case date modified (why?!?!)
        date = kodimon.iso8601.parse(post['modified'])
        movie_item.set_date(date.year, date.month, date.day)

        # context menu
        ctx_menu = [contextmenu.create_add_to_watch_later(self._plugin,
                                                          self.localize(self.LOCAL_WATCH_LATER_ADD),
                                                          movie_item)]
        movie_item.set_context_menu(ctx_menu)
        return movie_item

    def _set_content_and_sort(self):
        self.set_content_type(constants.CONTENT_TYPE_MOVIES)
        self.add_sort_method(constants.SORT_METHOD_LABEL_IGNORE_THE,
                             constants.SORT_METHOD_VIDEO_YEAR,
                             constants.SORT_METHOD_VIDEO_RATING,
                             constants.SORT_METHOD_DATE)
        pass

    def on_search(self, search_text, path, params, re_match):
        self._set_content_and_sort()

        result = []

        json_data = self.get_function_cache().get(FunctionCache.ONE_MINUTE, self._client.search, search_text)
        posts = json_data['posts']
        for post in posts:
            result.append(self._create_video_item_from_post(post))
            pass

        return result, {self.RESULT_CACHE_TO_DISC: False}

    def on_watch_later(self, path, params, re_match):
        self._set_content_and_sort()
        pass

    @kodimon.RegisterPath('^/play/?$')
    def _on_play(self, path, params, re_match):
        stream_id = params['stream_id']

        stream_url = self._client.get_video_url(stream_id)
        movie_item = VideoItem(stream_id,
                               stream_url)
        return movie_item

    @kodimon.RegisterPath('^/category/(?P<categoryid>\d+)/?$')
    def _on_category(self, path, params, re_match):
        self._set_content_and_sort()

        result = []
        category_id = re_match.group('categoryid')

        json_data = self.get_function_cache().get(FunctionCache.ONE_DAY, self._client.get_category_content, category_id)
        posts = json_data['posts']
        for post in posts:
            result.append(self._create_video_item_from_post(post))
            pass

        return result

    def on_root(self, path, params, re_match):
        result = []

        # watch later
        if len(self._watch_later.list()) > 0:
            watch_later_item = DirectoryItem('[B]' + self.localize(self.LOCAL_WATCH_LATER) + '[/B]',
                                             self.create_uri([self.PATH_WATCH_LATER, 'list']),
                                             image=self.create_resource_path('media', 'watch_later.png'))
            watch_later_item.set_fanart(self.get_fanart())
            result.append(watch_later_item)
            pass

        # search
        search_item = DirectoryItem('[B]' + self.localize(self.LOCAL_SEARCH) + '[/B]',
                                    self.create_uri([self.PATH_SEARCH, 'list']),
                                    image=self.create_resource_path('media', 'search.png')
        )
        search_item.set_fanart(self.get_fanart())
        result.append(search_item)

        # "Neu bei Netzkino"
        category_id = '81'
        image = 'http://dyn.netzkino.de/wp-content/themes/netzkino/imgs/categories/%s.png' % category_id
        category_item = DirectoryItem(u'[B]Neu bei Netzkino[/B]',
                                      self.create_uri(['category', category_id]),
                                      image=image)
        category_item.set_fanart(self.get_fanart())
        result.append(category_item)

        # categories
        categories = self.get_function_cache().get(FunctionCache.ONE_DAY, self._client.get_categories)
        for category in categories:
            category_id = str(category['id'])
            image = 'http://dyn.netzkino.de/wp-content/themes/netzkino/imgs/categories/%s.png' % category_id
            category_item = DirectoryItem(category['title'],
                                          self.create_uri(['category', category_id]),
                                          image=image)
            category_item.set_fanart(self.get_fanart())
            result.append(category_item)
            pass

        return result, {self.RESULT_CACHE_TO_DISC: False}

    def get_fanart(self):
        return self.create_resource_path('media', 'fanart.jpg')

    pass