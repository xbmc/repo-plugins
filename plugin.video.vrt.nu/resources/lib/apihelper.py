# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
''' Implements an ApiHelper class with common VRT NU API functionality '''

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.error import HTTPError
    from urllib.parse import quote_plus, unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, Request, urlopen
except ImportError:  # Python 2
    from urllib import quote_plus
    from urllib2 import build_opener, install_opener, ProxyHandler, Request, HTTPError, unquote, urlopen

import statichelper
from data import CHANNELS
from helperobjects import TitleItem
from metadata import Metadata


class ApiHelper:
    ''' A class with common VRT NU API functionality '''

    _VRT_BASE = 'https://www.vrt.be'
    _VRTNU_SEARCH_URL = 'https://vrtnu-api.vrt.be/search'
    _VRTNU_SUGGEST_URL = 'https://vrtnu-api.vrt.be/suggest'
    _VRTNU_SCREENSHOT_URL = 'https://vrtnu-api.vrt.be/screenshots'

    def __init__(self, _kodi, _favorites):
        ''' Constructor for the ApiHelper class '''
        self._kodi = _kodi
        self._favorites = _favorites
        self._showfanart = _kodi.get_setting('showfanart', 'true') == 'true'
        self._showpermalink = _kodi.get_setting('showpermalink', 'false') == 'true'
        self._metadata = Metadata(_kodi, _favorites)

        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))

    def get_tvshows(self, category=None, channel=None, feature=None):
        ''' Get all TV shows for a given category, channel or feature, optionally filtered by favorites '''
        params = dict()

        if category:
            params['facets[categories]'] = category
            cache_file = 'category.%s.json' % category

        if channel:
            params['facets[programBrands]'] = channel
            cache_file = 'channel.%s.json' % channel

        if feature:
            params['facets[programTags.title]'] = feature
            cache_file = 'featured.%s.json' % feature

        # If no facet-selection is done, we return the A-Z listing
        if not category and not channel and not feature:
            params['facets[transcodingStatus]'] = 'AVAILABLE'  # Required for getting results in Suggests API
            cache_file = 'programs.json'
        tvshows = self._kodi.get_cache(cache_file, ttl=60 * 60)  # Try the cache if it is fresh
        if not tvshows:
            import json
            querystring = '&'.join('{}={}'.format(key, value) for key, value in list(params.items()))
            suggest_url = self._VRTNU_SUGGEST_URL + '?' + querystring
            self._kodi.log('URL get: {url}', 'Verbose', url=unquote(suggest_url))
            tvshows = json.load(urlopen(suggest_url))
            self._kodi.update_cache(cache_file, tvshows)

        return tvshows

    def list_tvshows(self, category=None, channel=None, feature=None, use_favorites=False):
        ''' List all TV shows for a given category, channel or feature, optionally filtered by favorites '''

        # Get tvshows
        tvshows = self.get_tvshows(category=category, channel=channel, feature=feature)

        # Get oneoffs
        if self._kodi.get_setting('showoneoff', 'true') == 'true':
            cache_file = 'oneoff.json'
            oneoffs = self.get_episodes(variety='oneoff', cache_file=cache_file)
        else:
            # Return empty list
            oneoffs = []

        return self.__map_tvshows(tvshows, oneoffs, use_favorites=use_favorites, cache_file=cache_file)

    def tvshow_to_listitem(self, tvshow, program, cache_file):
        ''' Return a ListItem based on a Suggests API result '''

        label = self._metadata.get_label(tvshow)

        if program:
            context_menu, favorite_marker = self._metadata.get_context_menu(tvshow, program, cache_file)
            label += favorite_marker

        return TitleItem(
            title=label,
            path=self._kodi.url_for('programs', program=program),
            art_dict=self._metadata.get_art(tvshow),
            info_dict=self._metadata.get_info_labels(tvshow),
            context_menu=context_menu,
        )

    def list_episodes(self, program=None, season=None, category=None, feature=None, programtype=None, page=None, use_favorites=False, variety=None):
        ''' Construct a list of episode or season TitleItems from VRT NU Search API data and filtered by favorites '''
        # Caching
        cache_file = None
        if variety:
            if use_favorites:
                cache_file = 'my-%s-%s.json' % (variety, page)
            else:
                cache_file = '%s-%s.json' % (variety, page)

        # Titletype
        titletype = None
        if variety:
            titletype = variety

        # Get data from api or cache
        episodes = self.get_episodes(program=program, season=season, category=category, feature=feature, programtype=programtype,
                                     page=page, use_favorites=use_favorites, variety=variety, cache_file=cache_file)

        if isinstance(episodes, tuple):
            seasons = episodes[0]
            episodes = episodes[1]
            return self.__map_seasons(program, seasons, episodes)

        return self.__map_episodes(episodes, titletype=titletype, season=season, use_favorites=use_favorites, cache_file=cache_file)

    def __map_episodes(self, episodes, titletype=None, season=None, use_favorites=False, cache_file=None):
        ''' Construct a list of TV show episodes TitleItems based on Search API query and filtered by favorites '''
        episode_items = []
        sort = 'episode'
        ascending = True
        content = 'episodes'

        if use_favorites:
            favorite_programs = self._favorites.programs()

        for episode in episodes:
            # VRT API workaround: seasonTitle facet behaves as a partial match regex,
            # so we have to filter out the episodes from seasons that don't exactly match.
            if season and season != 'allseasons' and episode.get('seasonTitle') != season:
                continue

            program = statichelper.url_to_program(episode.get('programUrl'))
            if use_favorites and program not in favorite_programs:
                continue

            # Support search highlights
            highlight = episode.get('highlight')
            if highlight:
                for key in highlight:
                    episode[key] = statichelper.convert_html_to_kodilabel(highlight.get(key)[0])

            list_item, sort, ascending = self.episode_to_listitem(episode, program, cache_file, titletype)
            episode_items.append(list_item)

        return episode_items, sort, ascending, content

    def __map_seasons(self, program, seasons, episodes):
        import random
        season_items = []
        sort = 'label'
        ascending = True
        content = 'seasons'

        episode = random.choice(episodes)
        info_labels = self._metadata.get_info_labels(episode, season=True)
        program_type = episode.get('programType')

        # Reverse sort seasons if program_type is 'reeksaflopend' or 'daily'
        if program_type in ('daily', 'reeksaflopend'):
            ascending = False

        # Add an "* All seasons" list item
        if self._kodi.get_global_setting('videolibrary.showallitems') is True:
            season_items.append(TitleItem(
                title=self._kodi.localize(30096),
                path=self._kodi.url_for('programs', program=program, season='allseasons'),
                art_dict=self._metadata.get_art(episode, season='allseasons'),
                info_dict=info_labels,
            ))

        # NOTE: Sort the episodes ourselves, because Kodi does not allow to set to 'ascending'
        seasons = sorted(seasons, key=lambda k: k['key'], reverse=not ascending)

        for season in seasons:
            season_key = season.get('key', '')
            try:
                # If more than 300 episodes exist, we may end up with an empty season (Winteruur)
                episode = random.choice([e for e in episodes if e.get('seasonName') == season_key])
            except IndexError:
                episode = episodes[0]

            label = '%s %s' % (self._kodi.localize(30094), season_key)
            season_items.append(TitleItem(
                title=label,
                path=self._kodi.url_for('programs', program=program, season=season_key),
                art_dict=self._metadata.get_art(episode, season=True),
                info_dict=info_labels,
            ))
        return season_items, sort, ascending, content

    def __map_tvshows(self, tvshows, oneoffs, use_favorites=False, cache_file=None):
        ''' Construct a list of TV show and Oneoff TitleItems and filtered by favorites '''
        items = []

        if use_favorites:
            favorite_programs = self._favorites.programs()

        # Create list of oneoff programs from oneoff episodes
        oneoff_programs = [statichelper.url_to_program(episode.get('programUrl')) for episode in oneoffs]

        for tvshow in tvshows:
            program = statichelper.url_to_program(tvshow.get('targetUrl'))

            if use_favorites and program not in favorite_programs:
                continue

            if program in oneoff_programs:
                # Add the oneoff listitem(s), yes, we can't guarantee there's only one per program so attempt to list all
                for index in [n for n, o in enumerate(oneoff_programs) if o == program]:
                    items.append(self.episode_to_listitem(oneoffs[index], program, cache_file, titletype='oneoff')[0])
            else:
                # Add the tvshow listitem
                items.append(self.tvshow_to_listitem(tvshow, program, cache_file))

        return items

    def episode_to_listitem(self, episode, program, cache_file, titletype):
        ''' Return a ListItem based on a Search API result '''

        label, sort, ascending = self._metadata.get_label(episode, titletype, return_sort=True)

        if program:
            context_menu, favorite_marker = self._metadata.get_context_menu(episode, program, cache_file)
            label += favorite_marker

        info_labels = self._metadata.get_info_labels(episode)
        info_labels['title'] = label

        return TitleItem(
            title=label,
            path=self._kodi.url_for('play_id', video_id=episode.get('videoId'), publication_id=episode.get('publicationId')),
            art_dict=self._metadata.get_art(episode),
            info_dict=info_labels,
            context_menu=context_menu,
            is_playable=True,
        ), sort, ascending

    def list_search(self, keywords, page=0):
        ''' Search VRT NU content for a given string '''
        episodes = self.get_episodes(keywords=keywords, page=page)
        return self.__map_episodes(episodes, titletype='recent')

    def get_single_episode(self, whatson_id):
        ''' Get single episode by whatsonId '''
        video = None
        api_data = self.get_episodes(whatson_id=whatson_id, variety='single')
        if len(api_data) == 1:
            episode = api_data[0]
            video_item = TitleItem(
                title=self._metadata.get_label(episode),
                art_dict=self._metadata.get_art(episode),
                info_dict=self._metadata.get_info_labels(episode),
            )
            video = dict(listitem=video_item, video_id=episode.get('videoId'), publication_id=episode.get('publicationId'))
        return video

    def get_episode_by_air_date(self, channel_name, start_date, end_date=None):
        ''' Get an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00) '''
        import json
        from datetime import datetime, timedelta
        import dateutil.parser
        import dateutil.tz
        offairdate = None
        channel = statichelper.find_entry(CHANNELS, 'name', channel_name)
        if not channel:
            return None
        try:
            onairdate = dateutil.parser.parse(start_date, default=datetime.now(dateutil.tz.gettz('Europe/Brussels')))
        except ValueError:
            return None

        if end_date:
            try:
                offairdate = dateutil.parser.parse(end_date, default=datetime.now(dateutil.tz.gettz('Europe/Brussels')))
            except ValueError:
                return None
        video = None
        episode_guess_off = None
        now = datetime.now(dateutil.tz.gettz('Europe/Brussels'))
        if onairdate.hour < 6:
            schedule_date = onairdate - timedelta(days=1)
        else:
            schedule_date = onairdate
        schedule_datestr = schedule_date.isoformat().split('T')[0]
        url = 'https://www.vrt.be/bin/epg/schedule.%s.json' % schedule_datestr
        schedule_json = json.load(urlopen(url))
        episodes = schedule_json.get(channel.get('id'), [])
        if offairdate:
            mindate = min(abs(offairdate - dateutil.parser.parse(episode.get('endTime'))) for episode in episodes)
            episode_guess_off = next((episode for episode in episodes if abs(offairdate - dateutil.parser.parse(episode.get('endTime'))) == mindate), None)

        mindate = min(abs(onairdate - dateutil.parser.parse(episode.get('startTime'))) for episode in episodes)
        episode_guess_on = next((episode for episode in episodes if abs(onairdate - dateutil.parser.parse(episode.get('startTime'))) == mindate), None)
        offairdate_guess = dateutil.parser.parse(episode_guess_on.get('endTime'))
        if (episode_guess_off and episode_guess_on.get('vrt.whatson-id') == episode_guess_off.get('vrt.whatson-id')
                or (not episode_guess_off and episode_guess_on)):
            video = self.get_single_episode(episode_guess_on.get('vrt.whatson-id'))
            if video:
                return video

            # Airdate live2vod feature: use livestream cache of last 24 hours if no video was found

            if now - timedelta(hours=24) <= dateutil.parser.parse(episode_guess_on.get('endTime')) <= now:
                start_date = onairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19]
                end_date = offairdate_guess.astimezone(dateutil.tz.UTC).isoformat()[0:19]

            # Offairdate defined
            if offairdate and now - timedelta(hours=24) <= offairdate <= now:
                start_date = onairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19]
                end_date = offairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19]

            if start_date and end_date:
                video_item = TitleItem(
                    title=self._metadata.get_label(episode_guess_on),
                    art_dict=self._metadata.get_art(episode_guess_on),
                    info_dict=self._metadata.get_info_labels(episode_guess_on, channel=channel, date=start_date)
                )
                video = dict(
                    listitem=video_item,
                    video_id=channel.get('live_stream_id'),
                    start_date=start_date,
                    end_date=end_date,
                )
                return video

            video = dict(
                errorlabel=episode_guess_on.get('title')
            )
        return video

    def get_latest_episode(self, program):
        ''' Get the latest episode of a program '''
        video = None
        api_data = self.get_episodes(program=program, variety='single')
        if len(api_data) == 1:
            episode = api_data[0]
        self._kodi.log(str(episode))
        video_item = TitleItem(
            title=self._metadata.get_label(episode),
            art_dict=self._metadata.get_art(episode),
            info_dict=self._metadata.get_info_labels(episode),
        )
        video = dict(listitem=video_item, video_id=episode.get('videoId'), publication_id=episode.get('publicationId'))
        return video

    def get_episodes(self, program=None, season=None, category=None, feature=None, programtype=None, keywords=None, whatson_id=None,
                     page=None, use_favorites=False, variety=None, cache_file=None):
        ''' Get episodes or season data from VRT NU Search API '''

        # Contruct params
        if page:
            page = statichelper.realpage(page)
            all_items = False
            params = {
                'from': ((page - 1) * 50) + 1,
                'i': 'video',
                'size': 50,
            }
        elif variety == 'single':
            all_items = False
            params = {
                'i': 'video',
                'size': '1',
            }
        else:
            all_items = True
            params = {
                'i': 'video',
                'size': '300',
            }

        if variety:
            season = 'allseasons'

            if variety == 'offline':
                from datetime import datetime
                import dateutil.tz
                params['facets[assetOffTime]'] = datetime.now(dateutil.tz.gettz('Europe/Brussels')).strftime('%Y-%m-%d')

            if variety == 'oneoff':
                params['facets[programType]'] = 'oneoff'

            if use_favorites:
                program_urls = [statichelper.program_to_url(p, 'long') for p in self._favorites.programs()]
                params['facets[programUrl]'] = '[%s]' % (','.join(program_urls))
            elif variety in ('offline', 'recent'):
                channel_filter = [channel.get('name') for channel in CHANNELS if self._kodi.get_setting(channel.get('name'), 'true') == 'true']
                params['facets[programBrands]'] = '[%s]' % (','.join(channel_filter))

        if program:
            params['facets[programUrl]'] = statichelper.program_to_url(program, 'long')

        if season and season != 'allseasons':
            params['facets[seasonTitle]'] = season

        if category:
            params['facets[categories]'] = category

        if feature:
            params['facets[programTags.title]'] = feature

        if programtype:
            params['facets[programType]'] = programtype

        if keywords:
            season = 'allseasons'
            params['q'] = quote_plus(statichelper.from_unicode(keywords))
            params['highlight'] = 'true'

        if whatson_id:
            params['facets[whatsonId]'] = whatson_id

        # Construct VRT NU Search API Url and get api data
        querystring = '&'.join('{}={}'.format(key, value) for key, value in list(params.items()))
        search_url = self._VRTNU_SEARCH_URL + '?' + querystring

        import json
        if cache_file:
            # Get api data from cache if it is fresh
            search_json = self._kodi.get_cache(cache_file, ttl=60 * 60)
            if not search_json:
                self._kodi.log('URL get: {url}', 'Verbose', url=unquote(search_url))
                req = Request(search_url)
                try:
                    search_json = json.load(urlopen(req))
                except HTTPError as exc:
                    url_length = len(req.get_selector())
                    if exc.code == 413 and url_length > 8192:
                        self._kodi.show_ok_dialog(heading='HTTP Error 413', message=self._kodi.localize(30967))
                        self._kodi.log_error('HTTP Error 413: Exceeded maximum url length: '
                                             'VRT Search API url has a length of %d characters.' % url_length)
                        return []
                    if exc.code == 400 and 7600 <= url_length <= 8192:
                        self._kodi.show_ok_dialog(heading='HTTP Error 400', message=self._kodi.localize(30967))
                        self._kodi.log_error('HTTP Error 400: Probably exceeded maximum url length: '
                                             'VRT Search API url has a length of %d characters.' % url_length)
                        return []
                    raise
                self._kodi.update_cache(cache_file, search_json)
        else:
            self._kodi.log('URL get: {url}', 'Verbose', url=unquote(search_url))
            search_json = json.load(urlopen(search_url))

        # Check for multiple seasons
        seasons = None
        if 'facets[seasonTitle]' not in unquote(search_url):
            facets = search_json.get('facets', dict()).get('facets')
            seasons = next((f.get('buckets', []) for f in facets if f.get('name') == 'seasons' and len(f.get('buckets', [])) > 1), None)

        episodes = search_json.get('results', [{}])
        show_seasons = bool(season != 'allseasons')

        # Return seasons
        if show_seasons and seasons:
            return (seasons, episodes)

        api_pages = search_json.get('meta').get('pages').get('total')
        api_page_size = search_json.get('meta').get('pages').get('size')
        total_results = search_json.get('meta').get('total_results')

        if all_items and total_results > api_page_size:
            for api_page in range(1, api_pages):
                api_page_url = search_url + '&from=' + str(api_page * api_page_size + 1)
                api_page_json = json.load(urlopen(api_page_url))
                episodes += api_page_json.get('results', [{}])

        # Return episodes
        return episodes

    def get_live_screenshot(self, channel):
        ''' Get a live screenshot for a given channel, only supports Eén, Canvas and Ketnet '''
        url = '%s/%s.jpg' % (self._VRTNU_SCREENSHOT_URL, channel)
        self._kodi.delete_cached_thumbnail(url)
        return url

    def list_channels(self, channels=None, live=True):
        ''' Construct a list of channel ListItems, either for Live TV or the TV Guide listing '''
        from tvguide import TVGuide
        _tvguide = TVGuide(self._kodi)

        channel_items = []
        for channel in CHANNELS:
            if channels and channel.get('name') not in channels:
                continue

            context_menu = []
            art_dict = dict()

            # Try to use the white icons for thumbnails (used for icons as well)
            if self._kodi.get_cond_visibility('System.HasAddon(resource.images.studios.white)') == 1:
                art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**channel)
            else:
                art_dict['thumb'] = 'DefaultTags.png'

            if not live:
                path = self._kodi.url_for('channels', channel=channel.get('name'))
                label = channel.get('label')
                plot = '[B]%s[/B]' % channel.get('label')
                is_playable = False
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video')
                stream_dict = []
            elif channel.get('live_stream') or channel.get('live_stream_id'):
                if channel.get('live_stream_id'):
                    path = self._kodi.url_for('play_id', video_id=channel.get('live_stream_id'))
                elif channel.get('live_stream'):
                    path = self._kodi.url_for('play_url', video_url=channel.get('live_stream'))
                label = self._kodi.localize(30101, **channel)
                # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
                if channels and len(channels) == 1:
                    label = '[B]%s[/B]' % label
                is_playable = True
                if channel.get('name') in ['een', 'canvas', 'ketnet']:
                    if self._showfanart:
                        art_dict['fanart'] = self.get_live_screenshot(channel.get('name', art_dict.get('fanart')))
                    plot = '%s\n\n%s' % (self._kodi.localize(30102, **channel), _tvguide.live_description(channel.get('name')))
                else:
                    plot = self._kodi.localize(30102, **channel)
                # NOTE: Playcount is required to not have live streams as "Watched"
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video', playcount=0, duration=0)
                stream_dict = dict(duration=0)
                context_menu.append((self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file='channel.%s.json' % channel)))
            else:
                # Not a playable channel
                continue

            channel_items.append(TitleItem(
                title=label,
                path=path,
                art_dict=art_dict,
                info_dict=info_dict,
                stream_dict=stream_dict,
                context_menu=context_menu,
                is_playable=is_playable,
            ))

        return channel_items

    def list_youtube(self, channels=None):
        ''' Construct a list of youtube ListItems, either for Live TV or the TV Guide listing '''

        youtube_items = []

        if self._kodi.get_cond_visibility('System.HasAddon(plugin.video.youtube)') == 0 or self._kodi.get_setting('showyoutube') == 'false':
            return youtube_items

        for channel in CHANNELS:
            if channels and channel.get('name') not in channels:
                continue

            context_menu = []
            art_dict = dict()

            # Try to use the white icons for thumbnails (used for icons as well)
            if self._kodi.get_cond_visibility('System.HasAddon(resource.images.studios.white)') == 1:
                art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**channel)
            else:
                art_dict['thumb'] = 'DefaultTags.png'

            if channel.get('youtube'):
                path = channel.get('youtube')
                label = self._kodi.localize(30103, **channel)
                # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
                if channels and len(channels) == 1:
                    label = '[B]%s[/B]' % label
                plot = self._kodi.localize(30104, **channel)
                # NOTE: Playcount is required to not have live streams as "Watched"
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video', playcount=0)
                context_menu.append((self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file='channel.%s.json' % channel)))
            else:
                # Not a playable channel
                continue

            youtube_items.append(TitleItem(
                title=label,
                path=path,
                art_dict=art_dict,
                info_dict=info_dict,
                context_menu=context_menu,
                is_playable=False,
            ))

        return youtube_items

    def list_featured(self):
        ''' Construct a list of featured Listitems '''
        from data import FEATURED

        featured_items = []
        for feature in self.localize_features(FEATURED):
            featured_name = feature.get('name')
            featured_items.append(TitleItem(
                title=featured_name,
                path=self._kodi.url_for('featured', feature=feature.get('id')),
                art_dict=dict(thumb='DefaultCountry.png'),
                info_dict=dict(plot='[B]%s[/B]' % feature.get('name'), studio='VRT'),
            ))
        return featured_items

    def localize_features(self, featured):
        ''' Return a localized and sorted listing '''
        from copy import deepcopy
        features = deepcopy(featured)

        for feature in features:
            for key, val in list(feature.items()):
                if key == 'name':
                    feature[key] = self._kodi.localize_from_data(val, featured)

        return sorted(features, key=lambda x: x.get('name'))

    def list_categories(self):
        ''' Construct a list of category ListItems '''
        categories = []

        # Try the cache if it is fresh
        categories = self._kodi.get_cache('categories.json', ttl=7 * 24 * 60 * 60)

        # Try to scrape from the web
        if not categories:
            try:
                categories = self.get_categories()
            except Exception:  # pylint: disable=broad-except
                categories = []
            else:
                self._kodi.update_cache('categories.json', categories)

        # Use the cache anyway (better than hard-coded)
        if not categories:
            categories = self._kodi.get_cache('categories.json', ttl=None)

        # Fall back to internal hard-coded categories if all else fails
        from data import CATEGORIES
        if not categories:
            categories = CATEGORIES

        category_items = []
        for category in self.localize_categories(categories, CATEGORIES):
            if self._showfanart:
                thumbnail = category.get('thumbnail', 'DefaultGenre.png')
            else:
                thumbnail = 'DefaultGenre.png'
            category_items.append(TitleItem(
                title=category.get('name'),
                path=self._kodi.url_for('categories', category=category.get('id')),
                art_dict=dict(thumb=thumbnail, icon='DefaultGenre.png'),
                info_dict=dict(plot='[B]%s[/B]' % category.get('name'), studio='VRT'),
            ))
        return category_items

    def localize_categories(self, categories, categories2):
        ''' Return a localized and sorted listing '''

        for category in categories:
            for key, val in list(category.items()):
                if key == 'name':
                    category[key] = self._kodi.localize_from_data(val, categories2)

        return sorted(categories, key=lambda x: x.get('name'))

    def get_categories(self):
        ''' Return a list of categories by scraping the website '''
        from bs4 import BeautifulSoup, SoupStrainer
        self._kodi.log('URL get: https://www.vrt.be/vrtnu/categorieen/', 'Verbose')
        response = urlopen('https://www.vrt.be/vrtnu/categorieen/')
        tiles = SoupStrainer('nui-list--content')
        soup = BeautifulSoup(response.read(), 'html.parser', parse_only=tiles)

        categories = []
        for tile in soup.find_all('nui-tile'):
            categories.append(dict(
                id=tile.get('href').split('/')[-2],
                thumbnail=self.get_category_thumbnail(tile),
                name=self.get_category_title(tile),
            ))

        return categories

    def get_category_thumbnail(self, element):
        ''' Return a category thumbnail, if available '''
        if self._showfanart:
            raw_thumbnail = element.find(class_='media').get('data-responsive-image', 'DefaultGenre.png')
            return statichelper.add_https_method(raw_thumbnail)
        return 'DefaultGenre.png'

    @staticmethod
    def get_category_title(element):
        ''' Return a category title, if available '''
        found_element = element.find('a')
        if found_element:
            return statichelper.strip_newlines(found_element.contents[0])
        # FIXME: We should probably fall back to something sensible here, or raise an exception instead
        return ''
