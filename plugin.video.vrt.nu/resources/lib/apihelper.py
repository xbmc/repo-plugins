# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements an ApiHelper class with common VRT NU API functionality"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.parse import quote_plus, unquote
except ImportError:  # Python 2
    from urllib import quote_plus
    from urllib2 import unquote

from data import CHANNELS
from helperobjects import TitleItem
from kodiutils import (delete_cached_thumbnail, get_cache, get_cached_url_json, get_global_setting,
                       get_setting_bool, get_setting_int, get_url_json, has_addon, localize,
                       localize_from_data, log, ttl, update_cache, url_for)
from metadata import Metadata
from utils import (add_https_proto, html_to_kodi, find_entry, from_unicode, play_url_to_id,
                   program_to_url, realpage, url_to_program, youtube_to_plugin_url)


class ApiHelper:
    """A class with common VRT NU API functionality"""

    _VRTNU_SEARCH_URL = 'https://vrtnu-api.vrt.be/search'
    _VRTNU_SUGGEST_URL = 'https://vrtnu-api.vrt.be/suggest'
    _VRTNU_SCREENSHOT_URL = 'https://vrtnu-api.vrt.be/screenshots'

    def __init__(self, _favorites, _resumepoints):
        """Constructor for the ApiHelper class"""
        self._favorites = _favorites
        self._resumepoints = _resumepoints
        self._metadata = Metadata(_favorites, _resumepoints)

    def get_tvshows(self, category=None, channel=None, feature=None):
        """Get all TV shows for a given category, channel or feature, optionally filtered by favorites"""
        params = {}

        if category:
            params['facets[categories]'] = category
            cache_file = 'category.{category}.json'.format(category=category)

        if channel:
            params['facets[programBrands]'] = channel
            cache_file = 'channel.{channel}.json'.format(channel=channel)

        if feature:
            params['facets[programTags.title]'] = feature
            cache_file = 'featured.{feature}.json'.format(feature=feature)

        # If no facet-selection is done, we return the 'All programs' listing
        if not category and not channel and not feature:
            params['facets[transcodingStatus]'] = 'AVAILABLE'  # Required for getting results in Suggests API
            cache_file = 'programs.json'

        querystring = '&'.join('{}={}'.format(key, value) for key, value in list(params.items()))
        suggest_url = self._VRTNU_SUGGEST_URL + '?' + querystring
        return get_cached_url_json(url=suggest_url, cache=cache_file, ttl=ttl('indirect'), fail=[])

    def list_tvshows(self, category=None, channel=None, feature=None, programs=None, use_favorites=False):
        """List all TV shows for a given category, channel, feature or list of programNames, optionally filtered by favorites"""

        # Get tvshows
        tvshows = self.get_tvshows(category=category, channel=channel, feature=feature)

        # Filter tvshows using a list of programNames
        if programs:
            filtered_tvshows = []
            for tvshow in tvshows:
                if tvshow.get('programName') in programs:
                    filtered_tvshows.append(tvshow)
            tvshows = filtered_tvshows

        # Get oneoffs
        if get_setting_bool('showoneoff', default=True):
            cache_file = 'oneoff.json'
            oneoffs = self.get_episodes(variety='oneoff', cache_file=cache_file)
        else:
            cache_file = None
            # Return empty list
            oneoffs = []

        return self.__map_tvshows(tvshows, oneoffs, use_favorites=use_favorites, cache_file=cache_file)

    def tvshow_to_listitem(self, tvshow, program, cache_file):
        """Return a ListItem based on a Suggests API result"""
        label = self._metadata.get_label(tvshow)

        if program:
            context_menu, favorite_marker, _ = self._metadata.get_context_menu(tvshow, program, cache_file)
            label += favorite_marker

        return TitleItem(
            label=label,
            path=url_for('programs', program=program),
            art_dict=self._metadata.get_art(tvshow),
            info_dict=self._metadata.get_info_labels(tvshow),
            context_menu=context_menu,
        )

    def list_episodes(self, program=None, season=None, category=None, feature=None, programtype=None,
                      page=None, items_per_page=None, use_favorites=False, variety=None, sort_key=None, whatson_id=None):
        """Construct a list of episode or season TitleItems from VRT NU Search API data and filtered by favorites"""
        # Caching
        if not variety:
            cache_file = None
        else:
            cache_file = '{my}{variety}{page}.json'.format(
                my='my-' if use_favorites else '',
                variety=variety,
                page='-{}'.format(page) if sort_key is None and page is not None else '',
            )

        # Titletype
        titletype = None
        # FIXME: Find a better way to determine cache file and mixed episodes titletype
        if variety and variety.startswith('featured.') or variety in ('continue', 'offline', 'recent', 'watchlater'):
            titletype = 'mixed_episodes'
        else:
            titletype = variety

        # Get data from api or cache
        if sort_key:
            episodes = self.get_episodes(program=program, season=season, category=category, feature=feature, programtype=programtype,
                                         use_favorites=use_favorites, variety=variety, cache_file=cache_file, whatson_id=whatson_id)
            episodes = sorted(episodes, key=lambda k: k[sort_key])[(page * items_per_page) - items_per_page:page * items_per_page]
        else:
            episodes = self.get_episodes(program=program, season=season, category=category, feature=feature, programtype=programtype,
                                         page=page, use_favorites=use_favorites, variety=variety, cache_file=cache_file, whatson_id=whatson_id)

        if isinstance(episodes, tuple):
            seasons = episodes[0]
            episodes = episodes[1]
            return self.__map_seasons(program, seasons, episodes)

        return self.__map_episodes(episodes, titletype=titletype, season=season, use_favorites=use_favorites, cache_file=cache_file)

    def __map_episodes(self, episodes, titletype=None, season=None, use_favorites=False, cache_file=None):
        """Construct a list of TV show episodes TitleItems based on Search API query and filtered by favorites"""
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

            program = url_to_program(episode.get('programUrl'))
            if use_favorites and program not in favorite_programs:
                continue

            # Support search highlights
            highlight = episode.get('highlight')
            if highlight:
                for key in highlight:
                    episode[key] = html_to_kodi(highlight.get(key)[0])

            list_item, sort, ascending = self.episode_to_listitem(episode, program, cache_file, titletype)
            episode_items.append(list_item)

        return episode_items, sort, ascending, content

    def __map_seasons(self, program, seasons, episodes):
        import random
        season_items = []
        sort = 'label'
        ascending = True
        content = 'files'

        episode = random.choice(episodes)
        program_type = episode.get('programType')

        # Reverse sort seasons if program_type is 'reeksaflopend' or 'daily'
        if program_type in ('daily', 'reeksaflopend'):
            ascending = False

        # Add an "* All seasons" list item
        if get_global_setting('videolibrary.showallitems') is True:
            season_items.append(TitleItem(
                label=localize(30133),  # All seasons
                path=url_for('programs', program=program, season='allseasons'),
                art_dict=self._metadata.get_art(episode, season='allseasons'),
                info_dict=dict(tvshowtitle=self._metadata.get_tvshowtitle(episode),
                               plot=self._metadata.get_plot(episode, season='allseasons'),
                               plotoutline=self._metadata.get_plotoutline(episode, season='allseasons'),
                               tagline=self._metadata.get_plotoutline(episode, season='allseasons'),
                               mediatype=self._metadata.get_mediatype(episode, season='allseasons'),
                               studio=self._metadata.get_studio(episode),
                               tag=self._metadata.get_tag(episode)),
            ))

        # NOTE: Sort the episodes ourselves, because Kodi does not allow to set to 'ascending'
        seasons = sorted(seasons, key=lambda k: k['key'], reverse=not ascending)

        for season in seasons:
            season_key = season.get('key', '')
            # If more than 300 episodes exist, we may end up with an empty season (Winteruur)
            try:
                episode = random.choice([e for e in episodes if e.get('seasonName') == season_key])
            except IndexError:
                episode = episodes[0]

            season_items.append(TitleItem(
                label=self._metadata.get_title(episode, season=season_key),
                path=url_for('programs', program=program, season=season_key),
                art_dict=self._metadata.get_art(episode, season=season_key),
                info_dict=self._metadata.get_info_labels(episode, season=season_key),
                prop_dict=self._metadata.get_properties(episode),
            ))
        return season_items, sort, ascending, content

    def __map_tvshows(self, tvshows, oneoffs, use_favorites=False, cache_file=None):
        """Construct a list of TV show and Oneoff TitleItems and filtered by favorites"""
        items = []

        if use_favorites:
            favorite_programs = self._favorites.programs()

        # Create list of oneoff programs from oneoff episodes
        oneoff_programs = [url_to_program(episode.get('programUrl')) for episode in oneoffs]

        for tvshow in tvshows:
            program = url_to_program(tvshow.get('programUrl'))

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
        """Return a ListItem based on a Search API result"""

        label, sort, ascending = self._metadata.get_label(episode, titletype, return_sort=True)

        if program:
            context_menu, favorite_marker, watchlater_marker = self._metadata.get_context_menu(episode, program, cache_file)
            label += favorite_marker + watchlater_marker

        info_labels = self._metadata.get_info_labels(episode)
        # FIXME: Due to a bug in Kodi, ListItem.Title is used when Sort methods are used, not ListItem.Label
        info_labels['title'] = label

        return TitleItem(
            label=label,
            path=url_for('play_id', video_id=episode.get('videoId'), publication_id=episode.get('publicationId')),
            art_dict=self._metadata.get_art(episode),
            info_dict=info_labels,
            prop_dict=self._metadata.get_properties(episode),
            context_menu=context_menu,
            is_playable=True,
        ), sort, ascending

    def list_search(self, keywords, page=0):
        """Search VRT NU content for a given string"""
        episodes = self.get_episodes(keywords=keywords, page=page)
        return self.__map_episodes(episodes, titletype='mixed_episodes')

    def get_upnext(self, info):
        """Get up next data from VRT Search API"""
        program = info.get('program')
        path = info.get('path')
        season = None
        current_ep_no = None

        # Get current episode unique identifier
        ep_id = play_url_to_id(path)

        # Get all episodes from current program and sort by program, seasonTitle and episodeNumber
        episodes = sorted(self.get_episodes(keywords=program), key=lambda k: (k.get('program'), k.get('seasonTitle'), k.get('episodeNumber')))
        upnext = {}
        for episode in episodes:
            if ep_id.get('whatson_id') == episode.get('whatsonId') or \
               ep_id.get('video_id') == episode.get('videoId') or \
               ep_id.get('video_url') == episode.get('url'):
                season = episode.get('seasonTitle')
                current_ep_no = episode.get('episodeNumber')
                program = episode.get('program')
                upnext['current'] = episode
                try:
                    next_episode = episodes[episodes.index(episode) + 1]
                except IndexError:
                    pass
                else:
                    if next_episode.get('program') == program and next_episode.get('episodeNumber') != current_ep_no:
                        upnext['next'] = next_episode

        current_ep = upnext.get('current')
        next_ep = upnext.get('next')

        if next_ep is None:
            if current_ep is not None and current_ep.get('episodeNumber') == current_ep.get('seasonNbOfEpisodes') is not None:
                log(2, '[Up Next] Already at last episode of last season for {program} S{season}E{episode}',
                    program=program, season=season, episode=current_ep_no)
            elif season and current_ep_no:
                log(2, '[Up Next] No api data found for {program} S{season}E{episode}',
                    program=program, season=season, episode=current_ep_no)
            else:
                log(2, '[Up Next] No api data found for {program}', program=program)
            return None

        art = self._metadata.get_art(current_ep)
        current_episode = dict(
            episodeid=current_ep.get('videoId'),
            tvshowid=current_ep.get('programUrl'),
            title=self._metadata.get_title(current_ep),
            art={
                'tvshow.poster': art.get('thumb'),
                'thumb': art.get('thumb'),
                'tvshow.fanart': art.get('fanart'),
                'tvshow.landscape': art.get('thumb'),
                'tvshow.clearart': None,
                'tvshow.clearlogo': None,
            },
            plot=self._metadata.get_plot(current_ep),
            showtitle=self._metadata.get_tvshowtitle(current_ep),
            playcount=info.get('playcount'),
            season=self._metadata.get_season(current_ep),
            episode=self._metadata.get_episode(current_ep),
            rating=info.get('rating'),
            firstaired=self._metadata.get_aired(current_ep),
            runtime=info.get('runtime'),
        )

        art = self._metadata.get_art(next_ep)
        next_episode = dict(
            episodeid=next_ep.get('videoId'),
            tvshowid=next_ep.get('programUrl'),
            title=self._metadata.get_title(next_ep),
            art={
                'tvshow.poster': art.get('thumb'),
                'thumb': art.get('thumb'),
                'tvshow.fanart': art.get('fanart'),
                'tvshow.landscape': art.get('thumb'),
                'tvshow.clearart': None,
                'tvshow.clearlogo': None,
            },
            plot=self._metadata.get_plot(next_ep),
            showtitle=self._metadata.get_tvshowtitle(next_ep),
            playcount=None,
            season=self._metadata.get_season(next_ep),
            episode=self._metadata.get_episode(next_ep),
            rating=None,
            firstaired=self._metadata.get_aired(next_ep),
            runtime=self._metadata.get_duration(next_ep),
        )

        play_info = dict(
            video_id=next_ep.get('videoId'),
        )

        next_info = dict(
            current_episode=current_episode,
            next_episode=next_episode,
            play_info=play_info,
        )
        return next_info

    def get_single_episode_data(self, video_id=None, whatson_id=None, video_url=None):
        """Get single episode api data by videoId, whatsonId or url"""
        episode = None
        api_data = list()
        if video_id:
            api_data = self.get_episodes(video_id=video_id, variety='single')
        elif whatson_id:
            api_data = self.get_episodes(whatson_id=whatson_id, variety='single')
        elif video_url:
            api_data = self.get_episodes(video_url=video_url, variety='single')
        if len(api_data) == 1:
            episode = api_data[0]
        return episode

    def get_single_episode(self, video_id=None, whatson_id=None, video_url=None):
        """Get single episode by videoId, whatsonId or url"""
        video = None
        episode = self.get_single_episode_data(video_id=video_id, whatson_id=whatson_id, video_url=video_url)
        if episode:
            video_item = TitleItem(
                label=self._metadata.get_label(episode),
                art_dict=self._metadata.get_art(episode),
                info_dict=self._metadata.get_info_labels(episode),
                prop_dict=self._metadata.get_properties(episode),
            )
            video = dict(listitem=video_item, video_id=episode.get('videoId'), publication_id=episode.get('publicationId'))
        return video

    def get_episode_by_air_date(self, channel_name, start_date, end_date=None):
        """Get an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00)"""
        channel = find_entry(CHANNELS, 'name', channel_name)
        if not channel:
            return None

        from datetime import datetime, timedelta
        import dateutil.parser
        import dateutil.tz
        offairdate = None
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
        now = datetime.now(dateutil.tz.gettz('Europe/Brussels'))
        if onairdate.hour < 6:
            schedule_date = onairdate - timedelta(days=1)
        else:
            schedule_date = onairdate
        schedule_datestr = schedule_date.isoformat().split('T')[0]
        url = 'https://www.vrt.be/bin/epg/schedule.{date}.json'.format(date=schedule_datestr)
        schedule_json = get_url_json(url, fail={})
        episodes = schedule_json.get(channel.get('id'), [])
        if not episodes:
            return None

        # Guess the episode
        episode_guess = None
        if not offairdate:
            mindate = min(abs(onairdate - dateutil.parser.parse(episode.get('startTime'))) for episode in episodes)
            episode_guess = next((episode for episode in episodes if abs(onairdate - dateutil.parser.parse(episode.get('startTime'))) == mindate), None)
        else:
            duration = offairdate - onairdate
            midairdate = onairdate + timedelta(seconds=duration.total_seconds() / 2)
            mindate = min(abs(midairdate
                              - (dateutil.parser.parse(episode.get('startTime'))
                                 + timedelta(seconds=(dateutil.parser.parse(episode.get('endTime'))
                                                      - dateutil.parser.parse(episode.get('startTime'))).total_seconds() / 2))) for episode in episodes)
            episode_guess = next((episode for episode in episodes
                                  if abs(midairdate
                                         - (dateutil.parser.parse(episode.get('startTime'))
                                            + timedelta(seconds=(dateutil.parser.parse(episode.get('endTime'))
                                                                 - dateutil.parser.parse(episode.get('startTime'))).total_seconds() / 2))) == mindate), None)

        if episode_guess and episode_guess.get('vrt.whatson-id', None):
            offairdate_guess = dateutil.parser.parse(episode_guess.get('endTime'))
            video = self.get_single_episode(whatson_id=episode_guess.get('vrt.whatson-id'))
            if video:
                return video

            # Airdate live2vod feature: use livestream cache of last 24 hours if no video was found

            if now - timedelta(hours=24) <= dateutil.parser.parse(episode_guess.get('endTime')) <= now:
                start_date = onairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19]
                end_date = offairdate_guess.astimezone(dateutil.tz.UTC).isoformat()[0:19]

            # Offairdate defined
            if offairdate and now - timedelta(hours=24) <= offairdate <= now:
                start_date = onairdate.astimezone(dateutil.tz.UTC).isoformat()[:19]
                end_date = offairdate.astimezone(dateutil.tz.UTC).isoformat()[:19]

            if start_date and end_date:
                info = self._metadata.get_info_labels(episode_guess, channel=channel, date=start_date)
                live2vod_title = '{} ({})'.format(info.get('tvshowtitle'), localize(30454))  # from livestream cache
                info.update(tvshowtitle=live2vod_title)
                video_item = TitleItem(
                    label=self._metadata.get_label(episode_guess),
                    art_dict=self._metadata.get_art(episode_guess),
                    info_dict=info,
                    prop_dict=self._metadata.get_properties(episode_guess),
                )
                video = dict(
                    listitem=video_item,
                    video_id=channel.get('live_stream_id'),
                    start_date=start_date,
                    end_date=end_date,
                )
                return video

            video = dict(
                errorlabel=episode_guess.get('title')
            )
        return video

    def get_latest_episode(self, program):
        """Get the latest episode of a program"""
        api_data = self.get_episodes(program=program, variety='single')
        if len(api_data) != 1:
            return None
        episode = api_data[0]
        log(2, str(episode))
        video_item = TitleItem(
            label=self._metadata.get_label(episode),
            art_dict=self._metadata.get_art(episode),
            info_dict=self._metadata.get_info_labels(episode),
            prop_dict=self._metadata.get_properties(episode),
        )
        video = dict(listitem=video_item, video_id=episode.get('videoId'), publication_id=episode.get('publicationId'))
        return video

    def get_episodes(self, program=None, season=None, episodes=None, category=None, feature=None, programtype=None, keywords=None,
                     whatson_id=None, video_id=None, video_url=None, page=None, use_favorites=False, variety=None, cache_file=None):
        """Get episodes or season data from VRT NU Search API"""

        # Contruct params
        if page:
            page = realpage(page)
            all_items = False
            items_per_page = get_setting_int('itemsperpage', default=50)
            params = {
                'from': ((page - 1) * items_per_page) + 1,
                'i': 'video',
                'size': items_per_page,
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
            params['facets[allowedRegion]'] = '[BE,WORLD]'

        if variety:
            season = 'allseasons'

            if variety == 'offline':
                from datetime import datetime, timedelta
                import dateutil.tz
                now = datetime.now(dateutil.tz.gettz('Europe/Brussels'))
                off_dates = [(now + timedelta(days=day)).strftime('%Y-%m-%d') for day in range(0, 7)]
                params['facets[assetOffTime]'] = '[%s]' % (','.join(off_dates))

            if variety == 'oneoff':
                params['facets[episodeNumber]'] = '[0,1]'  # This to avoid VRT NU metadata errors (see #670)
                params['facets[programType]'] = 'oneoff'

            if variety == 'watchlater':
                self._resumepoints.refresh(ttl=ttl('direct'))
                episode_urls = self._resumepoints.watchlater_urls()
                params['facets[url]'] = '[%s]' % (','.join(episode_urls))

            if variety == 'continue':
                self._resumepoints.refresh(ttl=ttl('direct'))
                episode_urls = self._resumepoints.resumepoints_urls()
                params['facets[url]'] = '[%s]' % (','.join(episode_urls))

            if use_favorites:
                program_urls = [program_to_url(p, 'medium') for p in self._favorites.programs()]
                params['facets[programUrl]'] = '[%s]' % (','.join(program_urls))
            elif variety in ('offline', 'recent'):
                channel_filter = []
                for channel in CHANNELS:
                    if channel.get('vod') is True and get_setting_bool(channel.get('name'), default=True):
                        channel_filter.append(channel.get('name'))
                params['facets[programBrands]'] = '[%s]' % (','.join(channel_filter))

        if program:
            params['facets[programUrl]'] = program_to_url(program, 'medium')

        if season and season != 'allseasons':
            params['facets[seasonTitle]'] = season

        if episodes:
            params['facets[episodeNumber]'] = '[%s]' % (','.join(str(episode) for episode in episodes))

        if category:
            params['facets[categories]'] = category

        if feature:
            params['facets[programTags.title]'] = feature

        if programtype:
            params['facets[programType]'] = programtype

        if keywords:
            if not season:
                season = 'allseasons'
            params['q'] = quote_plus(from_unicode(keywords))
            params['highlight'] = 'true'

        if whatson_id:
            if isinstance(whatson_id, list):
                season = 'allseasons'
                params['facets[whatsonId]'] = '[%s]' % (','.join(str(item) for item in whatson_id))
            else:
                params['facets[whatsonId]'] = whatson_id

        if video_id:
            params['facets[videoId]'] = video_id

        if video_url:
            params['facets[url]'] = video_url

        # Construct VRT NU Search API Url and get api data
        querystring = '&'.join('{}={}'.format(key, value) for key, value in list(params.items()))
        search_url = self._VRTNU_SEARCH_URL + '?' + querystring.replace(' ', '%20')  # Only encode spaces to minimize url length
        if cache_file:
            search_json = get_cached_url_json(url=search_url, cache=cache_file, ttl=ttl('indirect'), fail={})
        else:
            search_json = get_url_json(url=search_url, fail={})

        # Check for multiple seasons
        seasons = []
        if 'facets[seasonTitle]' not in unquote(search_url):
            facets = search_json.get('facets', {}).get('facets')
            if facets:
                seasons = next((f.get('buckets', []) for f in facets if f.get('name') == 'seasons' and len(f.get('buckets', [])) > 1), None)
            # Experimental: VRT Search API only returns a maximum of 10 seasons, to get all seasons we need to use the "model.json" API
            if seasons and program and len(seasons) == 10:
                season_json = get_url_json('https://www.vrt.be/vrtnu/a-z/%s.model.json' % program)
                season_items = None
                try:
                    season_items = season_json.get(':items').get('parsys').get(':items').get('container') \
                                              .get(':items').get('banner').get(':items').get('navigation').get(':items')
                except AttributeError:
                    pass
                if season_items:
                    seasons = []
                    for item in season_items:
                        seasons.append(dict(key=item.lstrip('0')))

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
                api_page_json = get_url_json(api_page_url)
                if api_page_json is not None:
                    episodes += api_page_json.get('results', [{}])

        # Return episodes
        return episodes

    def get_live_screenshot(self, channel):
        """Get a live screenshot for a given channel, only supports Eén, Canvas and Ketnet"""
        url = '%s/%s.jpg' % (self._VRTNU_SCREENSHOT_URL, channel)
        delete_cached_thumbnail(url)
        return url

    def list_channels(self, channels=None, live=True):
        """Construct a list of channel ListItems, either for Live TV or the TV Guide listing"""
        from tvguide import TVGuide
        _tvguide = TVGuide()

        channel_items = []
        for channel in CHANNELS:
            if channels and channel.get('name') not in channels:
                continue

            context_menu = []
            art_dict = {}

            # Try to use the white icons for thumbnails (used for icons as well)
            if has_addon('resource.images.studios.white'):
                art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**channel)
            else:
                art_dict['thumb'] = 'DefaultTags.png'

            if not live:
                path = url_for('channels', channel=channel.get('name'))
                label = channel.get('label')
                plot = '[B]%s[/B]' % channel.get('label')
                is_playable = False
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video')
                stream_dict = []
                prop_dict = {}
            elif channel.get('live_stream') or channel.get('live_stream_id'):
                if channel.get('live_stream_id'):
                    path = url_for('play_id', video_id=channel.get('live_stream_id'))
                elif channel.get('live_stream'):
                    path = url_for('play_url', video_url=channel.get('live_stream'))
                label = localize(30141, **channel)  # Channel live
                playing_now = _tvguide.playing_now(channel.get('name'))
                if playing_now:
                    label += ' [COLOR=yellow]| %s[/COLOR]' % playing_now
                # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
                if channels and len(channels) == 1:
                    label = '[B]%s[/B]' % label
                is_playable = True
                if channel.get('name') in ['een', 'canvas', 'ketnet']:
                    if get_setting_bool('showfanart', default=True):
                        art_dict['fanart'] = self.get_live_screenshot(channel.get('name', art_dict.get('fanart')))
                    plot = '%s\n\n%s' % (localize(30142, **channel), _tvguide.live_description(channel.get('name')))
                else:
                    plot = localize(30142, **channel)  # Watch live
                # NOTE: Playcount and resumetime are required to not have live streams as "Watched" and resumed
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video', playcount=0, duration=0)
                prop_dict = dict(resumetime=0)
                stream_dict = dict(duration=0)
                context_menu.append((
                    localize(30413),  # Refresh menu
                    'RunPlugin(%s)' % url_for('delete_cache', cache_file='channel.{channel}.json'.format(channel=channel)),
                ))
            else:
                # Not a playable channel
                continue

            channel_items.append(TitleItem(
                label=label,
                path=path,
                art_dict=art_dict,
                info_dict=info_dict,
                prop_dict=prop_dict,
                stream_dict=stream_dict,
                context_menu=context_menu,
                is_playable=is_playable,
            ))

        return channel_items

    @staticmethod
    def list_youtube(channels=None):
        """Construct a list of youtube ListItems, either for Live TV or the TV Guide listing"""

        youtube_items = []

        if not has_addon('plugin.video.youtube') or not get_setting_bool('showyoutube', default=True):
            return youtube_items

        for channel in CHANNELS:
            if channels and channel.get('name') not in channels:
                continue

            art_dict = {}

            # Try to use the white icons for thumbnails (used for icons as well)
            if has_addon('resource.images.studios.white'):
                art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**channel)
            else:
                art_dict['thumb'] = 'DefaultTags.png'

            for youtube in channel.get('youtube', []):
                path = youtube_to_plugin_url(youtube['url'])
                label = localize(30143, **youtube)  # Channel on YouTube
                # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
                if channels and len(channels) == 1:
                    label = '[B]%s[/B]' % label
                plot = localize(30144, **youtube)  # Watch on YouTube
                # NOTE: Playcount is required to not have live streams as "Watched"
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video', playcount=0)

                context_menu = [(
                    localize(30413),  # Refresh menu
                    'RunPlugin(%s)' % url_for('delete_cache', cache_file='channel.{channel}.json'.format(channel=channel)),
                )]

                youtube_items.append(TitleItem(
                    label=label,
                    path=path,
                    art_dict=art_dict,
                    info_dict=info_dict,
                    context_menu=context_menu,
                    is_playable=False,
                ))

        return youtube_items

    def list_featured(self, online=False):
        """Construct a list of featured Listitems"""
        featured = []
        if online:
            featured = self.get_featured_from_api()
        else:
            from data import FEATURED

            # Add VRT NU website featured items
            featured.extend(self.get_featured_from_web())

            # Add hardcoded VRT Search API featured items
            for feature in self.localize_features(FEATURED):
                featured.append(feature)

        featured_items = []
        for feature in featured:
            featured_name = feature.get('name')
            featured_items.append(TitleItem(
                label=featured_name,
                path=url_for('featured', feature=feature.get('id')),
                art_dict=dict(thumb='DefaultCountry.png'),
                info_dict=dict(plot='[B]%s[/B]' % feature.get('name'), studio='VRT'),
            ))
        return featured_items

    def get_featured_from_api(self):
        """Return a list of featured items from VRT NU Search API"""
        episodes = self.get_episodes(season='allseasons')
        taglist = []
        featured = []
        for episode in episodes:
            for tag in episode.get('programTags'):
                if tag.get('parentTitle') not in ['Kanaal', 'Categorie', 'brands']:
                    title = tag.get('title').capitalize()
                    name = tag.get('name')
                    if name not in taglist:
                        taglist.append(name)
                        featured.append(dict(name=title, id=name))
        return featured

    @staticmethod
    def get_featured_from_web():
        """Return a list of featured items from VRT NU website using AEM JSON Exporter"""
        featured = []
        data = get_url_json('https://www.vrt.be/vrtnu/jcr:content/par.model.json')
        if data is not None:
            items = data.get(':items')
            if items:
                for item in items:
                    filled = items.get(item).get('items')
                    if filled:
                        featured.append(dict(name=items.get(item).get('title'), id='jcr_%s' % item))
        return featured

    @staticmethod
    def get_featured_media_from_web(feature):
        """Return a list of featured media from VRT NU website using AEM JSON Exporter"""
        media = []
        data = get_url_json('https://www.vrt.be/vrtnu/jcr:content/par/%s.model.json' % feature)
        if data is not None:
            for item in data.get('items'):
                mediatype = 'tvshows'
                for action in item.get('actions'):
                    if 'episode' in action.get('type'):
                        mediatype = 'episodes'
                if mediatype == 'episodes':
                    media.append(item.get('whatsonId'))
                else:
                    media.append(item.get('programName'))
        return dict(name=data.get('title'), mediatype=mediatype, medialist=media)

    @staticmethod
    def localize_features(featured):
        """Return a localized and sorted listing"""
        from copy import deepcopy
        features = deepcopy(featured)

        for feature in features:
            for key, val in list(feature.items()):
                if key == 'name':
                    feature[key] = localize_from_data(val, featured)

        return sorted(features, key=lambda x: x.get('name'))

    @staticmethod
    def valid_categories(categories):
        """Check if categories contain all necessary keys and values"""
        return bool(categories) and all(item.get('id') and item.get('name') for item in categories)

    @staticmethod
    def get_online_categories():
        """Return a list of categories from the VRT NU website"""
        categories = []
        categories_json = get_url_json('https://www.vrt.be/vrtnu/categorieen/jcr:content/par/categories.model.json')
        if categories_json is not None:
            categories = []
            for category in categories_json.get('items'):
                categories.append(dict(
                    id=category.get('name'),
                    thumbnail=add_https_proto(category.get('image').get('src')),
                    name=category.get('title'),
                ))
        return categories

    def get_categories(self):
        """Return a list of categories"""
        cache_file = 'categories.json'

        # Try the cache if it is fresh
        categories = get_cache(cache_file, ttl=7 * 24 * 60 * 60)
        if self.valid_categories(categories):
            return categories

        # Try online categories json
        categories = self.get_online_categories()
        if self.valid_categories(categories):
            from json import dumps
            update_cache(cache_file, dumps(categories))
            return categories

        # Fall back to internal hard-coded categories
        from data import CATEGORIES
        log(2, 'Fall back to internal hard-coded categories')
        return CATEGORIES

    def list_categories(self):
        """Construct a list of category ListItems"""
        categories = self.get_categories()
        category_items = []
        from data import CATEGORIES
        for category in self.localize_categories(categories, CATEGORIES):
            if get_setting_bool('showfanart', default=True):
                thumbnail = category.get('thumbnail', 'DefaultGenre.png')
            else:
                thumbnail = 'DefaultGenre.png'
            category_items.append(TitleItem(
                label=category.get('name'),
                path=url_for('categories', category=category.get('id')),
                art_dict=dict(thumb=thumbnail, icon='DefaultGenre.png'),
                info_dict=dict(plot='[B]%s[/B]' % category.get('name'), studio='VRT'),
            ))
        return category_items

    @staticmethod
    def localize_categories(categories, categories2):
        """Return a localized and sorted listing"""

        for category in categories:
            for key, val in list(category.items()):
                if key == 'name':
                    category[key] = localize_from_data(val, categories2)

        return sorted(categories, key=lambda x: x.get('name'))
