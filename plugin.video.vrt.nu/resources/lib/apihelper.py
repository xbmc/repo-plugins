# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements an ApiHelper class with common VRT MAX API functionality"""

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
                   realpage, youtube_to_plugin_url)


class ApiHelper:
    """A class with common VRT MAX API functionality"""

    _VRTMAX_SEARCH_URL = 'https://search7.vrt.be/search'
    _VRTMAX_SUGGEST_URL = 'https://search7.vrt.be/suggest'
    _VRTMAX_SCREENSHOT_URL = 'https://www.vrt.be/vrtmax-static/screenshots'

    def __init__(self, _favorites, _resumepoints):
        """Constructor for the ApiHelper class"""
        self._favorites = _favorites
        self._resumepoints = _resumepoints
        self._metadata = Metadata(_favorites, _resumepoints)

    def get_tvshows(self, category=None, channel=None, feature=None):
        """Get all TV shows for a given category, channel or feature, optionally filtered by favorites"""
        params = {}

        # Facet-selection
        if category:
            params['facets[categories]'] = category
            cache_file = 'category.{category}.json'.format(category=category)

        if feature:
            params['facets[programTags.title]'] = feature
            cache_file = 'featured.{feature}.json'.format(feature=feature)

        # If no facet-selection is done, we return the 'All programs' listing
        if not category and not feature:
            params['size'] = '1000'  # Required for getting results in Suggests API
            cache_file = 'programs.json'

        querystring = '&'.join('{}={}'.format(key, value) for key, value in list(params.items()))
        suggest_url = self._VRTMAX_SUGGEST_URL + '?' + querystring
        tvshows = get_cached_url_json(url=suggest_url, cache=cache_file, ttl=ttl('indirect'), fail=[])

        # Filter tvshows by channel
        if channel:
            filtered_tvshows = []
            for tvshow in tvshows:
                if tvshow.get('brands') and tvshow.get('brands')[0] == channel:
                    filtered_tvshows.append(tvshow)
            tvshows = filtered_tvshows

        return tvshows

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

        # FIXME: Get oneoffs
        cache_file = None
        oneoffs = []
        '''
        if get_setting_bool('showoneoff', default=True):
            cache_file = 'oneoff.json'
            oneoffs = self.get_episodes(variety='oneoff', cache_file=cache_file)
        else:
            cache_file = None
            # Return empty list
            oneoffs = []
        '''

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
                      page=None, use_favorites=False, variety=None, whatson_id=None, episode_id=None):
        """Construct a list of episode or season TitleItems from VRT MAX Search API data and filtered by favorites"""
        # Caching
        if not variety:
            cache_file = None
        else:
            cache_file = '{my}{variety}{page}.json'.format(
                my='my-' if use_favorites else '',
                variety=variety,
                page='-{}'.format(page) if page is not None else '',
            )

        # Titletype
        titletype = None
        # FIXME: Find a better way to determine cache file and mixed episodes titletype
        if variety and variety.startswith('featured.') or variety in ('continue', 'offline', 'recent', 'watchlater'):
            titletype = 'mixed_episodes'
        else:
            titletype = variety

        # Get data from api or cache
        episodes = self.get_episodes(program=program, season=season, category=category, feature=feature, programtype=programtype, page=page,
                                     use_favorites=use_favorites, variety=variety, cache_file=cache_file, whatson_id=whatson_id, episode_id=episode_id)

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
            # VRT API workaround: seasonId facet behaves as a partial match regex,
            # so we have to filter out the episodes from seasons that don't exactly match.
            if season and season != 'allseasons' and episode.get('seasonId') != season:
                continue

            program = episode.get('programName')
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
                episode = random.choice([e for e in episodes if e.get('seasonId') == season_key])
            except IndexError:
                episode = episodes[0]

            season_items.append(TitleItem(
                label=self._metadata.get_title(episode, season=season.get('title', '')),
                path=url_for('programs', program=program, season=season_key),
                art_dict=self._metadata.get_art(episode, season=season.get('name', '')),
                info_dict=self._metadata.get_info_labels(episode, season=season.get('title', '')),
                prop_dict=self._metadata.get_properties(episode),
            ))
        return season_items, sort, ascending, content

    def __map_tvshows(self, tvshows, oneoffs, use_favorites=False, cache_file=None):
        """Construct a list of TV show and Oneoff TitleItems and filtered by favorites"""
        items = []

        if use_favorites:
            favorite_programs = self._favorites.programs()

        # Create list of oneoff programs from oneoff episodes
        oneoff_programs = [episode.get('programName') for episode in oneoffs]

        for tvshow in tvshows:
            program = tvshow.get('programName')

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
        """Search VRT MAX content for a given string"""
        episodes = self.get_episodes(keywords=keywords, page=page)
        return self.__map_episodes(episodes, titletype='mixed_episodes')

    def get_upnext(self, info):
        """Get up next data from VRT Search API"""
        program_title = info.get('program_title')
        path = info.get('path')
        season_num = info.get('season_number')
        episode_num = info.get('episode_number')

        # Get current episode unique identifier
        ep_id = play_url_to_id(path)

        # Get all episodes from current program and sort by programTitle, seasonTitle and episodeNumber
        episodes = sorted(self.get_episodes(keywords=program_title), key=lambda k: (k.get('programTitle'), k.get('seasonTitle'), k.get('episodeNumber')))
        upnext = {}
        for episode in episodes:
            if episode.get('whatsonId') == ep_id.get('whatson_id') or \
               episode.get('videoId') == ep_id.get('video_id') or \
               episode.get('url') == ep_id.get('video_url') or \
               episode.get('episodeId') == ep_id.get('episode_id'):
                upnext['current'] = episode
                try:
                    next_episode = episodes[episodes.index(episode) + 1]
                except IndexError:
                    pass
                else:
                    if next_episode.get('programTitle') == program_title and next_episode.get('episodeNumber') != episode_num:
                        upnext['next'] = next_episode
                        break

        current_ep = upnext.get('current')
        next_ep = upnext.get('next')

        if next_ep is None:
            if current_ep is not None and current_ep.get('episodeNumber') == current_ep.get('seasonNbOfEpisodes') is not None:
                log(2, '[Up Next] Already at last episode of last season for {program_title} S{season_num}E{episode_num}',
                    program_title=program_title, season_num=season_num, episode_num=episode_num)
            elif season_num and program_title:
                log(2, '[Up Next] No api data found for {program_title} S{season_num}E{episode_num}',
                    program_title=program_title, season_num=season_num, episode_num=episode_num)
            else:
                log(2, '[Up Next] No api data found for {program_title}', program_title=program_title)
            return None

        art = self._metadata.get_art(current_ep)
        current_episode = dict(
            episodeid=current_ep.get('videoId'),
            tvshowid=current_ep.get('programName'),
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
            tvshowid=next_ep.get('programName'),
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
            episode_id=next_ep.get('episodeId'),
        )

        next_info = dict(
            current_episode=current_episode,
            next_episode=next_episode,
            play_info=play_info,
        )
        return next_info

    def get_single_episode_data(self, video_id=None, whatson_id=None, video_url=None, episode_id=None):
        """Get single episode api data by videoId, whatsonId or url"""
        episode = None
        api_data = []
        if video_id:
            api_data = self.get_episodes(video_id=video_id, variety='single')
        elif whatson_id:
            api_data = self.get_episodes(whatson_id=whatson_id, variety='single')
        elif video_url:
            api_data = self.get_episodes(video_url=video_url, variety='single')
        elif episode_id:
            api_data = self.get_episodes(episode_id=episode_id, variety='single')
        if len(api_data) == 1:
            episode = api_data[0]
        return episode

    def get_single_episode(self, video_id=None, whatson_id=None, video_url=None, episode_id=None):
        """Get single episode by videoId, whatsonId or url"""
        video = None
        episode = self.get_single_episode_data(video_id=video_id, whatson_id=whatson_id, video_url=video_url, episode_id=episode_id)
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

        if episode_guess:
            offairdate_guess = dateutil.parser.parse(episode_guess.get('endTime'))
            video = self.get_single_episode(episode_id=episode_guess.get('episodeId'))
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
        episode = next(iter(api_data), {})
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
                     whatson_id=None, episode_id=None, video_id=None, video_url=None, page=None, use_favorites=False, variety=None, cache_file=None):
        """Get episodes or season data from VRT MAX Search API"""

        # Set VRT Search API params
        all_items = True
        params = {
            'i': 'video',
            'available': 'true',
            'size': '300',
        }

        if page:
            page = realpage(page)
            all_items = False
            items_per_page = get_setting_int('itemsperpage', default=50)
            # Get 10 items more, because we get false positives that gets filtered afterwards
            api_items_per_page = items_per_page + 10
            params = {
                'from': ((page - 1) * api_items_per_page) + 1,
                'size': api_items_per_page,
            }
        elif variety == 'single':
            all_items = False

        if variety:
            season = 'allseasons'

            if variety == 'offline':
                params['orderBy'] = 'offTime'
                params['order'] = 'asc'

            if variety == 'oneoff':
                params['facets[episodeNumber]'] = '[0,1]'  # This to avoid VRT MAX metadata errors (see #670)
                params['facets[programType]'] = 'oneoff'

            if variety == 'watchlater':
                self._resumepoints.refresh_watchlater(ttl=ttl('direct'))
                episode_ids = self._resumepoints.watchlater_ids()
                params['facets[episodeId]'] = '[%s]' % (','.join(episode_ids))

            if variety == 'continue':
                self._resumepoints.refresh_continue(ttl=ttl('direct'))
                episode_ids = self._resumepoints.continue_ids()
                params['facets[episodeId]'] = '[%s]' % (','.join(episode_ids))

            if use_favorites:
                params['facets[programName]'] = '[%s]' % (','.join(self._favorites.programs()))
            elif variety in ('offline', 'recent'):
                params['q'] = 'BE'

        if program:
            params['orderBy'] = 'episodeId'
            params['order'] = 'desc'
            program_query = program.split('---')[0].replace('-', ' ')  # Convert programName to query
            program_query = program_query.replace('vrt', '').replace('nws', '')  # Remove VRT NWS
            program_query = ' '.join([word for word in program_query.split() if len(word) > 1])  # Remove single chars
            program_query = program_query[:-1] if program_query[-1].isdigit() else program_query  # Remove digit if last character
            program_query = program_query[:24]  # Trim query to 24 digits
            params['q'] = program_query

        if season and season != 'allseasons':
            params['facets[seasonId]'] = season

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

        if episode_id:
            if isinstance(episode_id, list):
                season = 'allseasons'
                params['facets[episodeId]'] = '[%s]' % (','.join(str(item) for item in episode_id))
            else:
                params['facets[episodeId]'] = episode_id

        if video_id:
            params['facets[videoId]'] = video_id

        if video_url:
            params['facets[url]'] = video_url

        # Construct VRT MAX Search API Url and get api data
        querystring = '&'.join('{}={}'.format(key, value) for key, value in list(params.items()))
        search_url = self._VRTMAX_SEARCH_URL + '?' + querystring.replace(' ', '%20')  # Only encode spaces to minimize url length
        if cache_file:
            search_json = get_cached_url_json(url=search_url, cache=cache_file, ttl=ttl('indirect'), fail={})
        else:
            search_json = get_url_json(url=search_url, fail={})

        # Check for multiple seasons
        # VRT Search API only returns a maximum of 10 seasons, to get all seasons we need to use the "model.json" API
        seasons = []
        if 'facets[seasonId]' not in unquote(search_url) and program:
            season_json = get_url_json('https://www.vrt.be/vrtmax/a-z/{}.model.json'.format(program))
            season_items = None
            try:
                season_items = season_json.get('details').get('data').get('program').get('seasons')
            except AttributeError:
                pass
            if season_items:
                seasons = []
                for item in season_items:
                    seasons.append(dict(key=item.get('id'), name=item.get('name'), title=item.get('title').get('raw')))

        episodes = search_json.get('results', [{}])
        show_seasons = bool(season != 'allseasons')

        # Check if we need to request more items
        if all_items:
            api_pages = search_json.get('meta').get('pages').get('total')
            api_page_size = search_json.get('meta').get('pages').get('size')
            total_results = search_json.get('meta').get('total_results')
            print(total_results)

            if total_results and total_results > api_page_size:
                for api_page in range(1, api_pages):
                    api_page_url = search_url + '&from=' + str(api_page * api_page_size + 1)
                    api_page_json = get_url_json(api_page_url)
                    if api_page_json is not None:
                        episodes += api_page_json.get('results', [{}])

        # FIXME: Filter episodes because faceted search is broken
        if program:
            filtered_episodes = []
            for episode in episodes:
                if episode.get('programName') == program:
                    filtered_episodes.append(episode)
            episodes = filtered_episodes
            if variety == 'single':
                episodes = [next(iter(episodes), {})]
        elif variety in ('offline', 'recent'):
            channel_filter = []
            for channel in CHANNELS:
                if channel.get('vod') is True and get_setting_bool(channel.get('name'), default=True):
                    channel_filter.append(channel.get('name'))
            filtered_episodes = []
            for episode in episodes:
                if episode.get('brands') and episode.get('brands')[0] in channel_filter:
                    filtered_episodes.append(episode)
            episodes = filtered_episodes

        # Trim filtered episodes
        if page:
            episodes = episodes[:items_per_page]

        # Return seasons
        if show_seasons and len(seasons) > 1:
            return (seasons, episodes)

        # Return episodes
        return episodes

    def get_live_screenshot(self, channel):
        """Get a live screenshot for a given channel, only supports Eén, Canvas and Ketnet"""
        url = '%s/%s.jpg' % (self._VRTMAX_SCREENSHOT_URL, channel)
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

            # Add VRT MAX website featured items
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
        """Return a list of featured items from VRT MAX Search API"""
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
        """Return a list of featured items from VRT MAX website using AEM JSON Exporter"""
        featured = []
        data = get_url_json('https://www.vrt.be/vrtmax/jcr:content/par.model.json')
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
        """Return a list of featured media from VRT MAX website using AEM JSON Exporter"""
        media = []
        data = get_url_json('https://www.vrt.be/vrtmax/jcr:content/par/%s.model.json' % feature)
        if data is not None:
            for item in data.get('items'):
                mediatype = 'tvshows'
                for action in item.get('actions'):
                    if 'episode' in action.get('type'):
                        mediatype = 'episodes'
                if mediatype == 'episodes':
                    media.append(item.get('data').get('episode').get('id'))
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
        """Return a list of categories from the VRT MAX website"""
        categories = []
        categories_json = get_url_json('https://www.vrt.be/vrtmax/categorieen/jcr:content/par/categories.model.json')
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
