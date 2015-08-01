# -*- coding: utf-8 -*-
__author__ = 'bromix'

import json

from resources.lib.content.client import Client
from resources.lib import nightcrawler


def filter_video_items(provider, context, video_items, query=None, year=None, month=None, count=None):
    result = []
    videos = video_items['items']
    for video in videos:
        # validate the search
        if query:
            if not query.lower() in video['title'].lower() and not query.lower() in video['plot'].lower():
                continue
                pass
            pass

        # validate the date
        if year and month:
            datetime = nightcrawler.utils.datetime.parse(video['published'])
            if datetime.year != year or datetime.month != month:
                continue
                pass
            pass

        video['uri'] = context.create_uri('/play/', {'url': video['uri']})
        video['type'] = 'video'
        video['images'].update({'fanart': provider.get_fanart(context)})

        context_menu = [(context.localize(provider.LOCAL_WATCH_LATER),
                         'RunPlugin(%s)' % context.create_uri(provider.PATH_WATCH_LATER_ADD,
                                                              {'item': json.dumps(video)}))]
        video['context-menu'] = {'items': context_menu}

        result.append(video)

        if count and len(result) == count:
            break
        pass

    return result


def get_years_from_video_items(video_items):
    result = []

    videos = video_items['items']
    for video in videos:
        datetime = nightcrawler.utils.datetime.parse(video['published'])
        if not datetime.year in result:
            result.append(datetime.year)
            pass
        pass

    return result


def get_month_from_video_items(video_items, year):
    result = []

    videos = video_items['items']
    for video in videos:
        datetime = nightcrawler.utils.datetime.parse(video['published'])
        if datetime.year == year:
            if not datetime.month in result:
                result.append(datetime.month)
                if len(result) == 12:
                    break
                pass
            pass
        pass

    return result


class Provider(nightcrawler.Provider):
    LOCAL_GOLEM_ALL_VIDEOS = 30500
    LOCAL_GOLEM_NEWEST_VIDEOS = 30513
    LOCAL_GOLEM_STREAM_NOT_FOUND = 30514
    LOCAL_GOLEM_TRAILER = 30515
    LOCAL_GOLEM_MANUFACTURE_VIDEOS = 30517
    LOCAL_GOLEM_WEEK_IN_REVIEW = 30516

    def __init__(self):
        nightcrawler.Provider.__init__(self)
        self._client = None
        pass

    def on_setup(self, context, mode):
        if mode == 'content-type':
            return ['default', 'episodes']

        return None

    def get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def get_fanart(self, context):
        return context.create_resource_path('media/fanart.jpg')

    def _get_videos(self, context, query=None, year=None, month=None, count=None):
        video_items = context.cache_function(context.CACHE_ONE_MINUTE * 30, self.get_client(context).get_videos)
        return filter_video_items(self, context, video_items, query, year, month, count)

    def _get_years(self, context):
        video_items = context.cache_function(context.CACHE_ONE_MINUTE * 30, self.get_client(context).get_videos)
        result = context.cache_function(context.CACHE_ONE_HOUR, get_years_from_video_items, video_items)
        return result

    def _get_months(self, context, year):
        video_items = context.cache_function(context.CACHE_ONE_MINUTE * 30, self.get_client(context).get_videos)
        result = context.cache_function(context.CACHE_ONE_HOUR, get_month_from_video_items, video_items, year)
        return result

    @nightcrawler.register_context_value('limit', int)
    def on_search(self, context, query, limit):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        return self._get_videos(context, query=query, count=limit)

    @nightcrawler.register_path('/play/')
    @nightcrawler.register_context_value('url', unicode, required=True)
    def on_play(self, context, url):
        video_streams = self.get_client(context).get_video_streams(url)
        return self.select_video_stream(context, video_streams, video_quality_index=[360, 720])

    @nightcrawler.register_path('/browse/all/')
    def on_browse_all(self, context, ):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        return self._get_videos(context)

    @nightcrawler.register_path('/browse/date/(?P<year>\d+)/(?P<month>\d+)/')
    @nightcrawler.register_path_value('year', int)
    @nightcrawler.register_path_value('month', int)
    def on_browse_year_month(self, context, year, month):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        return self._get_videos(context, year=year, month=month)

    @nightcrawler.register_path('/browse/date/(?P<year>\d+)/')
    @nightcrawler.register_path_value('year', int)
    def on_browse_year(self, context, year):
        months = self._get_months(context, year)
        result = []
        for month in months:
            month_text = context.localize(30500 + month)
            year = nightcrawler.utils.strings.to_unicode(year)
            result.append({'type': 'folder',
                           'title': month_text,
                           'uri': context.create_uri('browse/date/%s/%s/' % (year, str(month))),
                           'images': {'thumbnail': context.create_resource_path('media/calendar.png'),
                                      'fanart': self.get_fanart(context)}})
            pass

        return result

    @nightcrawler.register_path('/browse/query/(?P<year>\d+)/(?P<month>\d+)/')
    @nightcrawler.register_path_value('year', int)
    @nightcrawler.register_path_value('month', int)
    @nightcrawler.register_context_value('q', unicode, alias='query', required=True)
    def on_filter_by_query_show_result(self, context, year, month, query):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        return self._get_videos(context, query=query, year=year, month=month)

    @nightcrawler.register_path('/browse/query/(?P<year>\d+)/')
    @nightcrawler.register_path_value('year', int)
    @nightcrawler.register_context_value('q', unicode, alias='query', required=True)
    def on_browse_by_query_year(self, context, query, year):
        video_items = context.cache_function(context.CACHE_ONE_MINUTE * 30, self.get_client(context).get_videos)
        months = get_month_from_video_items(video_items, year)
        result = []
        for month in months:
            month_text = context.localize(30500 + month)
            year = nightcrawler.utils.strings.to_unicode(year)
            result.append({'type': 'folder',
                           'title': month_text,
                           'uri': context.create_uri('browse/query/%s/%s' % (year, str(month)), {'q': query}),
                           'images': {'thumbail': context.create_resource_path('media/calendar.png'),
                                      'fanart': self.get_fanart(context)}})
            pass

        return result

    @nightcrawler.register_path('/browse/query/')
    @nightcrawler.register_context_value('q', unicode, alias='query', required=True)
    def on_browse_by_query(self, context, query):
        result = []

        years = self._get_years(context)
        for year in years:
            year = nightcrawler.utils.strings.to_unicode(str(year))
            result.append({'type': 'folder',
                           'title': year,
                           'uri': context.create_uri('browse/query/%s' % year, {'q': query}),
                           'images': {'thumbnail': context.create_resource_path('media/calendar.png'),
                                      'fanart': self.get_fanart(context)}})
            pass

        return result

    @nightcrawler.register_path('/browse/newest/')
    def on_browse_newest(self, context):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)

        video_items = context.cache_function(context.CACHE_ONE_MINUTE * 30, self.get_client(context).get_videos)
        return filter_video_items(self, context, video_items, count=50)

    @nightcrawler.register_path('/watch_later/list/')
    def on_watch_later(self, context):
        context.set_content_type(context.CONTENT_TYPE_EPISODES)
        context.add_sort_method(context.SORT_METHOD_DATE_ADDED)
        return super(Provider, self).on_watch_later(context)

    @nightcrawler.register_path('/')
    def on_root(self, context):
        result = []

        # Neuste
        result.append({'type': 'folder',
                       'title': context.localize(self.LOCAL_GOLEM_NEWEST_VIDEOS),
                       'uri': context.create_uri('browse/newest'),
                       'images': {'thumbnail': context.create_resource_path('media/videos.png'),
                                  'fanart': self.get_fanart(context)}})

        # Wochenrueckblick
        result.append({'type': 'folder',
                       'title': context.localize(self.LOCAL_GOLEM_WEEK_IN_REVIEW),
                       'uri': context.create_uri(self.PATH_SEARCH_QUERY, {'q': 'wochenrueckblick'}),
                       'images': {'thumbnail': context.create_resource_path('media/calendar.png'),
                                  'fanart': self.get_fanart(context)}})

        # Herstellervideos
        result.append({'type': 'folder',
                       'title': context.localize(self.LOCAL_GOLEM_MANUFACTURE_VIDEOS),
                       'uri': context.create_uri('browse/query', {'q': 'herstellervideo'}),
                       'images': {'thumbnail': context.create_resource_path('media/videos.png'),
                                  'fanart': self.get_fanart(context)}})

        # Trailer
        result.append({'type': 'folder',
                       'title': context.localize(self.LOCAL_GOLEM_TRAILER),
                       'uri': context.create_uri('browse/query', {'q': 'trailer'}),
                       'images': {'thumbnail': context.create_resource_path('media/videos.png'),
                                  'fanart': self.get_fanart(context)}})

        # watch later
        if len(context.get_watch_later_list().list()) > 0:
            result.append(nightcrawler.items.create_watch_later_item(context, fanart=self.get_fanart(context)))
            pass

        # years
        years = self._get_years(context)
        for year in years:
            year = nightcrawler.utils.strings.to_unicode(str(year))
            result.append({'type': 'folder',
                           'title': year,
                           'uri': context.create_uri('browse/date/%s' % year),
                           'images': {'thumbnail': context.create_resource_path('media/calendar.png'),
                                      'fanart': self.get_fanart(context)}})
            pass

        # all videos
        result.append({'type': 'folder',
                       'title': context.localize(self.LOCAL_GOLEM_ALL_VIDEOS),
                       'uri': context.create_uri('browse/all'),
                       'images': {'thumbnail': context.create_resource_path('media/videos.png'),
                                  'fanart': self.get_fanart(context)}})

        # search
        result.append(nightcrawler.items.create_search_item(context, fanart=self.get_fanart(context)))
        return result

    pass