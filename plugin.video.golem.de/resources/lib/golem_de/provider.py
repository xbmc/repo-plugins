# -*- coding: utf-8 -*-

__author__ = 'bromix'

import re
from resources.lib.kodion import iso8601
from resources.lib.kodion.items import VideoItem, UriItem, DirectoryItem
from resources.lib.kodion.utils import FunctionCache

from resources.lib import kodion
from resources.lib.golem_de.client import Client

from io import BytesIO
import xml.etree.ElementTree as ET


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)
        self._local_map.update({'golem.all-videos': 30500,
                                'golem.watch-later': 30107,
                                'golem.newest-videos': 30513})
        self._client = None
        pass

    def _get_years_from_rss(self, rss):
        result = []

        rss_stream = BytesIO(rss)
        for event, item in ET.iterparse(rss_stream):
            if item.tag == 'item':
                datetime = iso8601.parse(kodion.utils.to_unicode(item.find('pubDate').text))
                if not datetime.year in result:
                    result.append(datetime.year)
                    pass
                item.clear()
                pass
            pass

        return result

    def _get_month_from_rss(self, rss, year):
        result = []

        rss_stream = BytesIO(rss)
        for event, item in ET.iterparse(rss_stream):
            if item.tag == 'item':
                datetime = iso8601.parse(kodion.utils.to_unicode(item.find('pubDate').text))
                if datetime.year == year:
                    if not datetime.month in result:
                        result.append(datetime.month)
                        pass
                    pass
                item.clear()

                if len(result) == 12:
                    break
                pass
            pass

        return result

    def _rss_to_items(self, context, rss, query=None, year=None, month=None, count=None):
        result = []

        video_count = 0

        rss_stream = BytesIO(rss)
        for event, item in ET.iterparse(rss_stream):
            if item.tag == 'item':
                title = kodion.utils.to_unicode(item.find('title').text)
                video_item = VideoItem(title, '')

                description = kodion.utils.to_unicode(item.find('description').text)
                if not description:
                    description = u''
                    pass
                uml_dict = {u'&auml;': u'ä', u'&Auml;': u'Ä',
                            u'&ouml;': u'ö', u'&Ouml;': u'Ö',
                            u'&uuml;': u'ü', u'&Uuml;': u'Ü',
                            u'&szlig;': u'ß'}
                for uml in uml_dict:
                    description = description.replace(uml, uml_dict[uml])
                    pass
                video_item.set_plot(description)

                # validate the search
                if query:
                    if not query.lower() in title.lower() and not query.lower() in description.lower():
                        item.clear()
                        continue
                        pass
                    pass

                enclosure = item.find('enclosure')
                if enclosure is not None:
                    thumb = enclosure.get('url')
                    if thumb:
                        thumb = thumb.replace('thumb-medium-156/', '')
                        video_item.set_image(thumb)
                        pass
                    pass

                guid = kodion.utils.to_unicode(item.find('guid').text)
                uri = context.create_uri(['play'], {'url': guid})
                video_item.set_uri(uri)
                pass

                datetime = iso8601.parse(kodion.utils.to_unicode(item.find('pubDate').text))

                #validate the date
                if year and month:
                    if datetime.year != year or datetime.month != month:
                        item.clear()
                        continue
                    pass

                video_item.set_aired(datetime.year, datetime.month, datetime.day)
                video_item.set_premiered(datetime.year, datetime.month, datetime.day)
                video_item.set_date(datetime.year, datetime.month, datetime.day, datetime.hour, datetime.minute,
                                    datetime.second)

                video_item.set_studio('golem.de')
                video_item.add_artist('golem.de')
                video_item.set_fanart(self.get_fanart(context))

                context_menu = [(context.localize(self._local_map['golem.watch-later']),
                                 'RunPlugin(%s)' % context.create_uri([kodion.constants.paths.WATCH_LATER, 'add'],
                                                                      {'item': kodion.items.to_jsons(video_item)}))]
                video_item.set_context_menu(context_menu)

                result.append(video_item)
                video_count += 1
                if count and count == video_count:
                    break
                item.clear()
                pass
            pass

        return result

    @kodion.RegisterProviderPath('^/play/$')
    def _on_play(self, context, re_match):
        url = context.get_param('url')
        video_id = re.search(r"(?P<video_id>\d+)", url)
        if video_id:
            video_quality = context.get_settings().get_video_quality({0: 360, 1: 720})
            if video_quality == 720:
                video_quality = 'high'
            else:
                video_quality = 'medium'
                pass

            client = self.get_client(context)
            video_url = client.get_video_stream(video_id.group('video_id'), url, quality=video_quality)

            return UriItem(video_url)
        return False

    def get_wizard_supported_views(self):
        return ['default', 'episodes']

    def get_client(self, context):
        if not self._client:
            self._client = Client()
            pass

        return self._client

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    def _get_videos(self, context, query=None, year=None, month=None):
        rss = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, self.get_client(context).get_videos)
        result = self._rss_to_items(context, rss, query=query, year=year, month=month)
        return result

    def _get_videos_newest(self, context, count=50):
        rss = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, self.get_client(context).get_videos)
        result = self._rss_to_items(context, rss, count=50)
        return result

    def _get_years(self, context):
        rss = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, self.get_client(context).get_videos)
        return self._get_years_from_rss(rss)

    def _get_month(self, context, year):
        rss = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 10, self.get_client(context).get_videos)
        return self._get_month_from_rss(rss, year)

    @kodion.RegisterProviderPath('^/browse/(?P<year>\d+)/(?P<month>\d+)/$')
    def _on_browse_year_month(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        year = int(re_match.group('year'))
        month = int(re_match.group('month'))
        return self._get_videos(context, year=year, month=month)

    @kodion.RegisterProviderPath('^/browse/(?P<year>\d+)/$')
    def _on_browse_year(self, context, re_match):
        year = re_match.group('year')
        months = self._get_month(context, int(year))

        result = []
        for month in months:
            month_text = context.localize(30500+month)
            year = kodion.utils.to_unicode(year)
            month_item = DirectoryItem(month_text, context.create_uri(['browse', year, str(month)]))
            month_item.set_fanart(self.get_fanart(context))
            month_item.set_image(context.create_resource_path('media', 'calendar.png'))
            result.append(month_item)
            pass
        return result

    @kodion.RegisterProviderPath('^/browse/newest/$')
    def _on_browse_newest(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        return self._get_videos_newest(context)

    @kodion.RegisterProviderPath('^/browse/all/$')
    def _on_browse_all(self, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        return self._get_videos(context)

    def on_search(self, search_text, context, re_match):
        context.set_content_type(kodion.constants.content_type.EPISODES)
        return self._get_videos(context, query=search_text)

    def on_root(self, context, re_match):
        result = []

        # newest
        newset_videos = DirectoryItem(context.localize(self._local_map['golem.newest-videos']),
                                      context.create_uri(['browse', 'newest']))
        newset_videos.set_fanart(self.get_fanart(context))
        newset_videos.set_image(context.create_resource_path('media', 'videos.png'))
        result.append(newset_videos)

        # watch later
        if len(context.get_watch_later_list().list()) > 0:
            watch_later_item = kodion.items.WatchLaterItem(context, fanart=self.get_fanart(context))
            result.append(watch_later_item)
            pass

        # years
        years = self._get_years(context)
        for year in years:
            year = kodion.utils.to_unicode(str(year))
            year_item = DirectoryItem(year,
                                      context.create_uri(['browse', year]))
            year_item.set_fanart(self.get_fanart(context))
            year_item.set_image(context.create_resource_path('media', 'calendar.png'))
            result.append(year_item)
            pass

        # all videos
        all_videos_items = DirectoryItem(context.localize(self._local_map['golem.all-videos']),
                                         context.create_uri(['browse', 'all']))
        all_videos_items.set_fanart(self.get_fanart(context))
        all_videos_items.set_image(context.create_resource_path('media', 'videos.png'))
        result.append(all_videos_items)

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        return result

    pass