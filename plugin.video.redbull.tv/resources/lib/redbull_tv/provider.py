# -*- coding: utf-8 -*-
import datetime
import urlparse
from xml.dom.minidom import _append_child
from resources.lib.kodion.exceptions import KodionException
from resources.lib.kodion.items import DirectoryItem, VideoItem, NextPageItem, UriItem
from resources.lib.kodion.utils import FunctionCache

__author__ = 'bromix'

from resources.lib import kodion
from resources.lib.redbull_tv.client import Client


class Provider(kodion.AbstractProvider):
    def __init__(self):
        kodion.AbstractProvider.__init__(self)
        self._local_map.update({'redbull.shows': 30500,
                                'redbull.films': 30501,
                                'redbull.videos': 30502,
                                'redbull.clips': 30503,
                                'redbull.featured': 30504,
                                'redbull.featured_shows': 30505,
                                'redbull.event.upcoming': 30506})
        self._client = None
        pass

    def get_client(self, context):
        if not self._client:
            items_per_page = context.get_settings().get_items_per_page()
            self._client = Client(limit=items_per_page)
            pass

        return self._client

    def get_wizard_supported_views(self):
        return ['default', 'episodes', 'tvshows']

    def get_alternative_fanart(self, context):
        return self.get_fanart(context)

    def get_fanart(self, context):
        return context.create_resource_path('media', 'fanart.jpg')

    @kodion.RegisterProviderPath('^/redbull/(?P<path>.+)/$')
    def _on_path(self, context, re_match):
        path = re_match.group('path')
        offset = context.get_param('offset', None)
        limit = context.get_param('limit', None)

        client = self.get_client(context)
        response = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 5, client.do_raw, path=path,
                                                    offset=offset, limit=limit)
        return self._response_to_items(context, response)

    def _get_path_from_url(self, context, item, name):
        url = item.get('meta', {}).get('links', {}).get(name, '')
        path = self.get_client(context).url_to_path(url)
        if not path or path == '/':
            return ''

        path = 'redbull/%s' % path
        return path.replace('//', '/')

    def _get_image(self, item, name, width=None, height=None, fallback=''):
        image = item.get('images', {}).get(name, {}).get('uri', '')
        if image:
            if width and height:
                image = '%s/width=%d,height=%d' % (image, width, height)
                pass
            elif width:
                image = '%s/width=%d' % (image, width)
                pass
            elif height:
                image = '%s/height=%d' % (image, height)
                pass
            pass
        elif fallback:
            return fallback

        return image

    def _do_channel_item(self, context, item):
        title = item['title']

        # change main => 'Red Bull TV'
        channel_id = item['id']
        if channel_id == 'main':
            title = u'Red Bull TV'
            pass
        image = self._get_image(item, 'portrait', width=440)
        fanart = self._get_image(item, 'background', width=1280, height=720, fallback=self.get_fanart(context))

        path = self._get_path_from_url(context, item, 'self')
        channel_item = DirectoryItem(title, uri=context.create_uri([path]),
                                     image=image, fanart=fanart)
        return channel_item

    def _do_channel_content(self, context, item):
        result = []

        # Map for sub menus of each channel
        # main is an exception: will always be empty and filled up manually
        sub_categories = ['shows', 'films', 'videos', 'clips']

        # for 'main' (Red Bull TV) we create our own content
        if context.get_path() == '/redbull/channels/main/':
            sub_categories = []
            pass

        # for 'sports' we tweak the result
        show_all_sports = context.get_param('all', '0') == '1'
        if context.get_path() == '/redbull/channels/sports/' and not show_all_sports:
            sub_categories = []
            pass

        # for 'live' we only use the 'featured' categorie
        if context.get_path() == '/redbull/channels/live/':
            sub_categories = ['featured']
            pass

        for sub_category in sub_categories:
            sub_category_path = self._get_path_from_url(context, item, sub_category)
            if sub_category_path:
                title = context.localize(self._local_map['redbull.%s' % sub_category]);
                sub_category_item = DirectoryItem(title, uri=context.create_uri([sub_category_path]))
                sub_category_item.set_fanart(self.get_fanart(context))
                result.append(sub_category_item)
                pass
            pass

        # Red Bull TV needs some different sub menus
        if context.get_path() == '/redbull/channels/main/':
            # Featured
            featured_shows_item = DirectoryItem('Featured', context.create_uri(['redbull', 'featured']))
            featured_shows_item.set_fanart(self.get_fanart(context))
            result.append(featured_shows_item)

            # Upcoming Live Events
            upcoming_live_events_item = DirectoryItem('Upcoming Live Events',
                                                      context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                         {'limit': '100',
                                                                          'event_type': 'upcoming',
                                                                          'next_page_allowed': '0'}))
            upcoming_live_events_item.set_fanart(self.get_fanart(context))
            result.append(upcoming_live_events_item)

            # Featured Shows
            featured_shows_item = DirectoryItem('Featured Shows', context.create_uri(['redbull', 'shows']))
            featured_shows_item.set_fanart(self.get_fanart(context))
            result.append(featured_shows_item)

            # Latest Films
            latest_films_item = DirectoryItem('Latest Films',
                                              context.create_uri(['redbull', 'channels', 'sports', 'films']))
            latest_films_item.set_fanart(self.get_fanart(context))
            result.append(latest_films_item)

            # Recently Added
            recently_added_item = DirectoryItem('Recently Added', context.create_uri(['redbull', 'videos']))
            recently_added_item.set_fanart(self.get_fanart(context))
            result.append(recently_added_item)

            # Past Live Events
            past_live_events_item = DirectoryItem('Past Live Events',
                                                  context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                     {'limit': '100',
                                                                      'event_type': 'replay',
                                                                      'next_page_allowed': '0'}))
            past_live_events_item.set_fanart(self.get_fanart(context))
            result.append(past_live_events_item)
            pass

        # Live
        if context.get_path() == '/redbull/channels/live/':
            # Upcoming
            upcoming_item = DirectoryItem('Upcoming', context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                         {'limit': '100',
                                                                          'event_type': 'upcoming',
                                                                          'next_page_allowed': '0'}))
            upcoming_item.set_fanart(self.get_fanart(context))
            result.append(upcoming_item)

            # Replays
            replays_item = DirectoryItem('Replays', context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                       {'limit': '100',
                                                                        'event_type': 'replay',
                                                                        'next_page_allowed': '0'}))
            replays_item.set_fanart(self.get_fanart(context))
            result.append(replays_item)

            # try to find a live stream
            new_params = {}
            new_params.update(context.get_params())
            new_params['event_type'] = 'live'
            new_params['next_page_allowed'] = '0'
            new_path = 'redbull/channels/live/'
            new_context = context.clone(new_path=new_path, new_params=new_params)
            client = self.get_client(context)
            response = context.get_function_cache().get(FunctionCache.ONE_MINUTE * 5, client.do_raw,
                                                        path='channels/live/featured', limit=100)
            live_result = self._response_to_items(new_context, response)
            if len(live_result) > 0:
                for item in live_result:
                    result.append(item)
                    pass
                pass
            pass

        # add 'All Sports'
        if context.get_path() == '/redbull/channels/sports/' and not show_all_sports:
            new_params = {}
            new_params.update(context.get_params())
            new_params['all'] = '1'
            new_context = context.clone(new_params=new_params)
            all_sports_items = DirectoryItem('All Sports', uri=new_context.get_uri())
            all_sports_items.set_fanart(self.get_fanart(context))
            result.append(all_sports_items)

            sub_channels = item.get('sub_channels', [])
            for sub_channel in sub_channels:
                channel_item = self._do_channel_item(context, sub_channel)
                result.append(channel_item)
                pass
            pass
        return result

    def _do_show_item(self, context, item, make_bold=False):
        title = item['title']
        if make_bold:
            title = '[B]%s[/B]' % title
            pass
        image = self._get_image(item, 'portrait', width=440)
        fanart = self._get_image(item, 'background', width=1280, height=720,
                                 fallback=self.get_fanart(context))

        path = self._get_path_from_url(context, item, 'episodes')
        # in the case of the main channel, we sometime get no correct uri for the episodes of the show
        # we try to compensate the problem here
        if not path or path == '/':
            show_id = item['id']
            path = 'redbull/shows/%s/episodes' % show_id
            pass
        show_item = DirectoryItem(title, uri=context.create_uri([path]), image=image, fanart=fanart)
        return show_item

    def _do_video_item(self, context, item):
        title = item['title']
        subtitle = item.get('subtitle', '')
        if subtitle:
            title = '%s - %s' % (title, subtitle)
            pass
        image = self._get_image(item, 'landscape', width=440)

        # we try to get a nice background based on the show
        show = item.get('show', {})
        if not show or show is None:
            show = {}
            pass
        fanart = self._get_image(show, 'background', width=1280, height=720,
                                 fallback=self.get_fanart(context))

        path = self._get_path_from_url(context, item, 'self')
        video_id = item['id']
        video_item = VideoItem(title, uri=context.create_uri(['play'], {'video_id': video_id}), image=image,
                               fanart=fanart)

        _plot = item.get('long_description', item.get('short_description', ''))
        video_item.set_plot(_plot)

        duration = item.get('duration', '')
        if duration:
            try:
                duration = kodion.utils.datetime_parser.parse(duration)
                seconds = duration.second
                seconds += duration.minute * 60
                seconds += duration.hour * 60 * 60
                video_item.set_duration_from_seconds(seconds)
            except:
                duration = ''
                pass
            pass

        # update events based on their status
        stream = item.get('stream', {})
        if stream is None:
            stream = {}
            pass
        status = stream.get('status', '')
        if status in ['replay', 'complete']:
            # video_item.set_title('[B][Replay][/B] %s' % video_item.get_title())
            # do nothing
            pass
        elif status in ['live']:
            video_item.set_title('[B][Live][/B] %s' % video_item.get_title())
            pass
        elif status in ['pre-event', 'soon']:
            try:
                starts_at = stream.get('starts_at', '')
                start_time = published = kodion.utils.datetime_parser.parse(starts_at)
                date_str = context.format_date_short(start_time)
                time_str = context.format_time(start_time)
                video_item.set_title('[B]%s %s (GMT)[/B] %s' % (date_str, time_str, video_item.get_title()))
            except:
                video_item.set_title('[B][Upcoming][/B] %s' % video_item.get_title())
                pass
            pass

        # Fallback: we try to calculate a duration based on the event
        if not duration:
            try:
                starts_at = stream.get('starts_at', '')
                ends_at = stream.get('ends_at', '')
                if starts_at and ends_at:
                    start_time = published = kodion.utils.datetime_parser.parse(starts_at)
                    end_time = published = kodion.utils.datetime_parser.parse(ends_at)
                    duration = end_time - start_time
                    video_item.set_duration_from_seconds(duration.seconds)
                    pass
            except:
                # do nothing
                pass
            pass

        published = item.get('published_on', '')
        if published:
            published = kodion.utils.datetime_parser.parse(published)
            if isinstance(published, datetime.date):
                published = datetime.datetime(published.year, published.month, published.day, 0, 0, 0, 0)
                pass
            video_item.set_aired_from_datetime(published)
            video_item.set_date_from_datetime(published)
            video_item.set_year(published.year)
            video_item.set_premiered_from_datetime(published)
            pass

        season = item.get('season_number', 1)
        if season and season is not None:
            video_item.set_season(int(season))
            pass

        episode = item.get('episode_number', 1)
        if episode and episode is not None:
            video_item.set_episode(int(episode))
            pass
        return video_item

    def _response_to_items(self, context, response):
        result = []

        response_type = response.get('type', '')
        # channel
        if response_type:
            if response_type == 'channel':
                result.extend(self._do_channel_content(context, response))
                pass
            else:
                raise KodionException('Unknown response type "%s"' % response_type)
            return result

        # channels
        channels = []
        response_channels = response.get('channels', [])
        for response_channel in response_channels:
            channel_item = self._do_channel_item(context, response_channel)
            channels.append(channel_item)
            pass
        result.extend(channels)

        # shows
        shows = []
        response_shows = response.get('shows', [])
        for response_show in response_shows:
            show_item = self._do_show_item(context, response_show)
            shows.append(show_item)
            pass

        # videos
        videos = []
        response_videos = response.get('videos', [])
        event_type = context.get_param('event_type', '')
        for response_video in response_videos:
            # try to filter the video on an event type
            stream = response_video.get('stream', {})
            if stream is None:
                stream = {}
                pass
            status = stream.get('status', '')
            if not event_type or (event_type == 'replay' and status in ['replay', 'complete']) or (
                            event_type == 'upcoming' and status in ['pre-event', 'soon']) or (
                            event_type == 'live' and status in ['live']):
                video_item = self._do_video_item(context, response_video)
                videos.append(video_item)
                pass
            pass

        # in case of upcoming videos we reverse the order
        if event_type == 'upcoming':
            videos = videos[::-1]
            pass

        featured_items = response.get('featured_items', [])
        for featured_item in featured_items:
            feature_type = featured_item.get('type', '')
            if feature_type == 'clip' or feature_type == 'episode' or feature_type == 'film' or feature_type == 'event_stream':
                # try to filter the video on an event type
                stream = featured_item.get('stream', {})
                if stream is None:
                    stream = {}
                    pass
                status = stream.get('status', '')
                if not event_type or (event_type == 'replay' and status in ['replay', 'complete']) or (
                                event_type == 'upcoming' and status in ['pre-event', 'soon']) or (
                                event_type == 'live' and status in ['live']):
                    video_item = self._do_video_item(context, featured_item)
                    videos.append(video_item)
                    pass
                pass
            elif feature_type == 'series':
                show_item = self._do_show_item(context, featured_item)
                shows.append(show_item)
                pass
            else:
                raise kodion.KodionException('Unknown feature type "%s"' % feature_type)
            pass

        search_results = response.get('search_results', [])
        for search_result in search_results:
            search_result_type = search_result.get('type', '')
            if search_result_type == 'clip' or search_result_type == 'episode' or search_result_type == 'film':
                video_item = self._do_video_item(context, search_result)
                videos.append(video_item)
                pass
            elif search_result_type == 'series':
                show_item = self._do_show_item(context, search_result, make_bold=True)
                shows.append(show_item)
                pass
            else:
                raise kodion.KodionException('Unknown search result type "%s"' % search_result_type)
            pass

        # we combine both results because of a possible search. A search will return shows and videos.
        result.extend(shows)
        result.extend(videos)

        # let content type EPISODES win
        if len(shows) > 0:
            context.set_content_type(kodion.constants.content_type.TV_SHOWS)
            pass
        if len(videos) > 0:
            context.set_content_type(kodion.constants.content_type.EPISODES)
            pass

        # meta (next page)
        next_page_allowed = context.get_param('next_page_allowed', '1') == '1'
        next_page = self._get_path_from_url(context, response, 'next_page')
        if next_page_allowed and next_page:
            next_page_url = response.get('meta', {}).get('links', {}).get('next_page', '')
            next_page_url = next_page_url.split('?')
            if len(next_page_url) > 1:
                params = dict(urlparse.parse_qsl(next_page_url[1]))

                new_params = {}
                new_params.update(context.get_params())
                new_params.update(params)
                new_context = context.clone(new_params=new_params)
                current_page = int(context.get_param('page', '1'))
                next_page_item = NextPageItem(new_context, current_page, fanart=self.get_fanart(new_context))
                result.append(next_page_item)
                pass
            pass

        return result

    @kodion.RegisterProviderPath('^/play/$')
    def on_play(self, context, re_match):
        video_id = context.get_param('video_id', '')
        if not video_id:
            return False

        client = self.get_client(context)
        streams = client.get_streams(video_id)

        if len(streams) > 0 and streams[0].get('upcoming', False):
            context.get_ui().show_notification(context.localize(self._local_map['redbull.event.upcoming']),
                                               time_milliseconds=5000)
            return False

        stream = kodion.utils.select_stream(context, streams)

        if stream is None:
            return False

        uri_item = UriItem(stream['url'])
        return uri_item

    def on_search(self, search_text, context, re_match):
        client = self.get_client(context)
        offset = context.get_param('offset', None)
        limit = context.get_param('limit', None)
        return self._response_to_items(context, client.search(query=search_text, offset=offset, limit=limit))

    def on_root(self, context, re_match):
        result = []

        client = self.get_client(context)

        # channels
        channel_response = context.get_function_cache().get(FunctionCache.ONE_HOUR, client.get_channels)
        result.extend(self._response_to_items(context, channel_response))

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        return result


    pass