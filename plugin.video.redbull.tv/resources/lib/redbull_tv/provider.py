# -*- coding: utf-8 -*-
import datetime
import urlparse
from xml.dom.minidom import _append_child
from resources.lib.kodion.items import DirectoryItem, VideoItem, NextPageItem, UriItem

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
        return self._response_to_items(context, client.do_raw(path=path, offset=offset, limit=limit))

    def _response_to_items(self, context, response):
        client = self.get_client(context)

        def _get_image(_item, _name, _width=None, _height=None, fallback=''):
            _image = _item.get('images', {}).get(_name, {}).get('uri', '')
            if _image:
                if _width and _height:
                    _image = '%s/width=%d,height=%d' % (_image, _width, _height)
                    pass
                elif _width:
                    _image = '%s/width=%d' % (_image, _width)
                    pass
                elif _height:
                    _image = '%s/height=%d' % (_image, _height)
                    pass
                pass
            elif fallback:
                return fallback

            return _image

        def _get_path_from_url(_item, _name):
            url = _item.get('meta', {}).get('links', {}).get(_name, '')
            path = client.url_to_path(url)
            if not path or path == '/':
                return ''

            path = 'redbull/%s' % path
            return path.replace('//', '/')

        def _do_channel_item(_item):
            _title = _item['title']

            # change main => 'Red Bull TV'
            _channel_id = _item['id']
            if _channel_id == 'main':
                _title = u'Red Bull TV'
                pass
            _image = _get_image(_item, 'portrait', _width=440)
            _fanart = _get_image(_item, 'background', _width=1280, _height=720, fallback=self.get_fanart(context))

            _path = _get_path_from_url(_item, 'self')
            _channel_item = DirectoryItem(_title, uri=context.create_uri([_path], params={'channel_id': _channel_id}),
                                          image=_image, fanart=_fanart)
            return _channel_item

        def _do_channel_content(_item):
            _result = []

            _show_sub_channels = context.get_param('sub-channels', '1') == '1'
            _make_bold = False
            _sub_channels = _item.get('sub_channels', [])
            if not _show_sub_channels:
                _sub_channels = []
                pass
            if len(_sub_channels) > 0:
                _make_bold = True
                pass

            # Map for sub menus of each channel
            # main is an exception: will always be empty and filled up manually
            _channel_sub_category_dict = {'main': [],
                                          'live': ['featured']}
            _channel_id = context.get_param('channel_id', '')
            if _channel_id == 'sports' and _show_sub_channels:
                _channel_sub_category_dict['sports'] = []
                pass

            _sub_categories = _channel_sub_category_dict.get(_channel_id, ['shows', 'films', 'videos', 'clips'])
            for _sub_category in _sub_categories:
                _sub_category_path = _get_path_from_url(_item, _sub_category)
                if _sub_category_path:
                    _title = context.localize(self._local_map['redbull.%s' % _sub_category]);
                    if _make_bold:
                        _title = '[B]%s[/B]' % _title
                        pass
                    _sub_category_item = DirectoryItem(_title, uri=context.create_uri([_sub_category_path]))
                    _sub_category_item.set_fanart(self.get_fanart(context))
                    _result.append(_sub_category_item)
                    pass
                pass

            # Live
            if _channel_id == 'live':
                # Upcoming
                _upcoming_item = DirectoryItem('Upcoming', context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                              {'limit': '100',
                                                                               'event_type': 'upcoming',
                                                                               'next_page_allowed': '0'}))
                _upcoming_item.set_fanart(self.get_fanart(context))
                _result.append(_upcoming_item)

                # Replays
                _replays_item = DirectoryItem('Replays', context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                            {'limit': '100',
                                                                             'event_type': 'replay',
                                                                             'next_page_allowed': '0'}))
                _replays_item.set_fanart(self.get_fanart(context))
                _result.append(_replays_item)

                # try to find a live stream
                _new_params = {}
                _new_params.update(context.get_params())
                _new_params['event_type'] = 'live'
                _new_params['next_page_allowed'] = '0'
                _new_path = '/channels/live/'
                _new_context = context.clone(new_path=_new_path, new_params=_new_params)
                _live_result = self._response_to_items(_new_context,
                                                       client.do_raw(path='videos/event_streams', limit=100))
                if len(_live_result) > 0:
                    for _item in _live_result:
                        _result.append(_item)
                        pass
                    pass
                pass

            # Red Bull TV needs some different sub menus
            if _channel_id == 'main':
                # Featured
                _featured_shows_item = DirectoryItem('Featured', context.create_uri(['redbull', 'featured']))
                _featured_shows_item.set_fanart(self.get_fanart(context))
                _result.append(_featured_shows_item)

                # Upcoming Live Events
                _upcoming_live_events_item = DirectoryItem('Upcoming Live Events',
                                                           context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                              {'limit': '100',
                                                                               'event_type': 'upcoming',
                                                                               'next_page_allowed': '0'}))
                _upcoming_live_events_item.set_fanart(self.get_fanart(context))
                _result.append(_upcoming_live_events_item)

                # Featured Shows
                _featured_shows_item = DirectoryItem('Featured Shows', context.create_uri(['redbull', 'shows']))
                _featured_shows_item.set_fanart(self.get_fanart(context))
                _result.append(_featured_shows_item)

                # Latest Films
                _latest_films_item = DirectoryItem('Latest Films',
                                                   context.create_uri(['redbull', 'channels', 'sports', 'films']))
                _latest_films_item.set_fanart(self.get_fanart(context))
                _result.append(_latest_films_item)

                # Recently Added
                _recently_added_item = DirectoryItem('Recently Added', context.create_uri(['redbull', 'videos']))
                _recently_added_item.set_fanart(self.get_fanart(context))
                _result.append(_recently_added_item)

                # Past Live Events
                _past_live_events_item = DirectoryItem('Past Live Events',
                                                       context.create_uri(['redbull', 'videos', 'event_streams'],
                                                                          {'limit': '100',
                                                                           'event_type': 'replay',
                                                                           'next_page_allowed': '0'}))
                _past_live_events_item.set_fanart(self.get_fanart(context))
                _result.append(_past_live_events_item)
                pass

            # in case of sport we show 'All Sports' like the web page
            if _channel_id == 'sports' and _show_sub_channels:
                new_params = {}
                new_params.update(context.get_params())
                new_params['sub-channels'] = '0'
                new_context = context.clone(new_params=new_params)
                _all_sports_items = DirectoryItem('All Sports', uri=new_context.get_uri())
                _all_sports_items.set_fanart(self.get_fanart(context))
                _result.append(_all_sports_items)
                pass

            # sub channels
            for _sub_channel in _sub_channels:
                _channel_item = _do_channel_item(_sub_channel)
                _result.append(_channel_item)
                pass
            return _result

        def _do_show_item(_item, make_bold=False):
            _title = _item['title']
            if make_bold:
                _title = '[B]%s[/B]' % _title
                pass
            _image = _get_image(_item, 'portrait', _width=440)
            _fanart = _get_image(_item, 'background', _width=1280, _height=720, fallback=self.get_fanart(context))

            _path = _get_path_from_url(_item, 'episodes')
            # in the case of the main channel, we sometime get no correct uri for the episodes of the show
            # we try to compensate the problem here
            if not _path or _path == '/':
                _show_id = _item['id']
                _path = 'redbull/shows/%s/episodes' % _show_id
                pass
            _show_item = DirectoryItem(_title, uri=context.create_uri([_path]), image=_image, fanart=_fanart)
            return _show_item

        def _do_video_item(_item):
            _title = _item['title']
            _subtitle = _item.get('subtitle', '')
            if _subtitle:
                _title = '%s - %s' % (_title, _subtitle)
                pass
            _image = _get_image(_item, 'landscape', _width=440)

            # we try to get a nice background based on the show
            _show = _item.get('show', {})
            if not _show or _show is None:
                _show = {}
                pass
            _fanart = _get_image(_show, 'background', _width=1280, _height=720, fallback=self.get_fanart(context))

            _path = _get_path_from_url(_item, 'self')
            _video_id = _item['id']
            _video_item = VideoItem(_title, uri=context.create_uri(['play'], {'video_id': _video_id}), image=_image,
                                    fanart=_fanart)

            _plot = _item.get('long_description', _item.get('short_description', ''))
            _video_item.set_plot(_plot)

            _duration = _item.get('duration', '')
            if _duration:
                try:
                    _duration = kodion.utils.datetime_parser.parse(_duration)
                    _seconds = _duration.second
                    _seconds += _duration.minute * 60
                    _seconds += _duration.hour * 60 * 60
                    _video_item.set_duration_from_seconds(_seconds)
                except:
                    _duration = ''
                    pass
                pass

            # update events based on their status
            _stream = _item.get('stream', {})
            if _stream is None:
                _stream = {}
                pass
            _status = _stream.get('status', '')
            if _status in ['replay', 'complete']:
                # _video_item.set_title('[B][Replay][/B] %s' % _video_item.get_title())
                # do nothing
                pass
            elif _status in ['live']:
                _video_item.set_title('[B][Live][/B] %s' % _video_item.get_title())
                pass
            elif _status in ['pre-event', 'soon']:
                try:
                    _starts_at = _stream.get('starts_at', '')
                    start_time = _published = kodion.utils.datetime_parser.parse(_starts_at)
                    date_str = context.format_date_short(start_time)
                    time_str = context.format_time(start_time)
                    _video_item.set_title('[B]%s %s (GMT)[/B] %s' % (date_str, time_str, _video_item.get_title()))
                except:
                    _video_item.set_title('[B][Upcoming][/B] %s' % _video_item.get_title())
                    pass
                pass

            # Fallback: we try to calculate a duration based on the event
            if not _duration:
                try:
                    _starts_at = _stream.get('starts_at', '')
                    _ends_at = _stream.get('ends_at', '')
                    if _starts_at and _ends_at:
                        start_time = _published = kodion.utils.datetime_parser.parse(_starts_at)
                        end_time = _published = kodion.utils.datetime_parser.parse(_ends_at)
                        _duration = end_time - start_time
                        _video_item.set_duration_from_seconds(_duration.seconds)
                        pass
                except:
                    # do nothing
                    pass
                pass

            _published = _item.get('published_on', '')
            if _published:
                _published = kodion.utils.datetime_parser.parse(_published)
                if isinstance(_published, datetime.date):
                    _published = datetime.datetime(_published.year, _published.month, _published.day, 0, 0, 0, 0)
                    pass
                _video_item.set_aired_from_datetime(_published)
                _video_item.set_date_from_datetime(_published)
                _video_item.set_year(_published.year)
                _video_item.set_premiered_from_datetime(_published)
                pass

            _season = _item.get('season_number', 1)
            if _season and _season is not None:
                _video_item.set_season(int(_season))
                pass

            _episode = _item.get('episode_number', 1)
            if _episode and _episode is not None:
                _video_item.set_episode(int(_episode))
                pass
            return _video_item

        result = []

        response_type = response.get('type', '')
        # channel
        if response_type:
            if response_type == 'channel':
                result.extend(_do_channel_content(response))
            return result

        # channels
        channels = []
        response_channels = response.get('channels', [])
        for response_channel in response_channels:
            channel_item = _do_channel_item(response_channel)
            channels.append(channel_item)
            pass
        result.extend(channels)

        # shows
        shows = []
        response_shows = response.get('shows', [])
        for response_show in response_shows:
            show_item = _do_show_item(response_show)
            shows.append(show_item)
            pass

        # videos
        videos = []
        response_videos = response.get('videos', [])
        event_type = context.get_param('event_type', '')
        for response_video in response_videos:
            if not event_type:
                video_item = _do_video_item(response_video)
                videos.append(video_item)
                pass
            else:
                # filter based on an event type
                stream = response_video.get('stream', {})
                if stream is None:
                    stream = {}
                    pass
                status = stream.get('status', '')
                if (event_type == 'replay' and status in ['replay', 'complete']) or (
                                event_type == 'upcoming' and status in ['pre-event', 'soon']) or (
                                event_type == 'live' and status in ['live']):
                    video_item = _do_video_item(response_video)
                    videos.append(video_item)
                    pass
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
                video_item = _do_video_item(featured_item)
                videos.append(video_item)
                pass
            elif feature_type == 'series':
                show_item = _do_show_item(featured_item)
                shows.append(show_item)
                pass
            else:
                raise kodion.KodionException('Unknown feature type "%s"' % feature_type)
            pass

        search_results = response.get('search_results', [])
        for search_result in search_results:
            search_result_type = search_result.get('type', '')
            if search_result_type == 'clip' or search_result_type == 'episode' or search_result_type == 'film':
                video_item = _do_video_item(search_result)
                videos.append(video_item)
                pass
            elif search_result_type == 'series':
                show_item = _do_show_item(search_result, make_bold=True)
                shows.append(show_item)
                pass
            else:
                raise kodion.KodionException('Unknown search result type "%s"' % search_result_type)
            pass

        result.extend(shows)
        result.extend(videos)

        if len(shows) > 0:
            context.set_content_type(kodion.constants.content_type.TV_SHOWS)
            pass

        if len(videos) > 0:
            context.set_content_type(kodion.constants.content_type.EPISODES)
            pass

        # meta (next page)
        next_page_allowed = context.get_param('next_page_allowed', '1') == '1'
        next_page = _get_path_from_url(response, 'next_page')
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
        def _compare(item):
            vq = context.get_settings().get_video_quality()
            return vq - item['format'].get('height', 0)

        video_id = context.get_param('video_id', '')
        if not video_id:
            return False

        client = self.get_client(context)
        streams = client.get_streams(video_id, bandwidth=1)  # middle
        stream = kodion.utils.find_best_fit(streams, _compare)

        if stream.get('upcoming', False):
            context.get_ui().show_notification(context.localize(self._local_map['redbull.event.upcoming']),
                                               time_milliseconds=5000)
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
        result.extend(self._response_to_items(context, client.get_channels()))

        # search
        search_item = kodion.items.SearchItem(context, image=context.create_resource_path('media', 'search.png'),
                                              fanart=self.get_fanart(context))
        result.append(search_item)

        return result

    pass