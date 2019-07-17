# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Implements a VRTApiHelper class with common VRT NU API functionality '''

from __future__ import absolute_import, division, unicode_literals
from resources.lib import CHANNELS, CATEGORIES, metadatacreator, statichelper
from resources.lib.helperobjects import TitleItem

try:  # Python 3
    from urllib.parse import quote_plus, unquote, urlencode
    from urllib.request import build_opener, install_opener, ProxyHandler, urlopen
except ImportError:  # Python 2
    from urllib import quote_plus, urlencode
    from urllib2 import build_opener, install_opener, ProxyHandler, unquote, urlopen


class VRTApiHelper:
    ''' A class with common VRT NU API functionality '''

    _VRT_BASE = 'https://www.vrt.be'
    _VRTNU_SEARCH_URL = 'https://vrtnu-api.vrt.be/search'
    _VRTNU_SUGGEST_URL = 'https://vrtnu-api.vrt.be/suggest'
    _VRTNU_SCREENSHOT_URL = 'https://vrtnu-api.vrt.be/screenshots'

    def __init__(self, _kodi, _favorites):
        ''' Constructor for the VRTApiHelper class '''
        self._kodi = _kodi
        self._favorites = _favorites

        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))

        self._showfanart = _kodi.get_setting('showfanart', 'true') == 'true'
        self._showpermalink = _kodi.get_setting('showpermalink', 'false') == 'true'

    def get_tvshow_items(self, category=None, channel=None, feature=None, use_favorites=False):
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
            params['facets[transcodingStatus]'] = 'AVAILABLE'
            cache_file = 'programs.json'

        # Get programs
        suggest_json = self._kodi.get_cache(cache_file, ttl=60 * 60)  # Try the cache if it is fresh
        if not suggest_json:
            import json
            suggest_url = self._VRTNU_SUGGEST_URL + '?' + urlencode(params)
            self._kodi.log_notice('URL get: ' + unquote(suggest_url), 'Verbose')
            suggest_json = json.load(urlopen(suggest_url))
            self._kodi.update_cache(cache_file, suggest_json)

        # Get oneoffs
        if self._kodi.get_setting('showoneoff', 'true') == 'true':
            oneoff_cache = 'oneoff.json'
            search_json = self._kodi.get_cache(oneoff_cache, ttl=30 * 60)  # Try the cache if it is fresh
            if not search_json:
                import json
                params = {
                    'facets[programType]': 'oneoff',
                    'size': '300',
                }
                search_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
                self._kodi.log_notice('URL get: ' + unquote(search_url), 'Verbose')
                search_json = json.load(urlopen(search_url))
                self._kodi.update_cache(oneoff_cache, search_json)
            oneoffs = search_json.get('results', [])
        else:
            # Return empty list
            oneoffs = []

        return self._map_to_tvshow_items(suggest_json, oneoffs, use_favorites=use_favorites, cache_file=cache_file)

    def _map_to_tvshow_items(self, tvshows, oneoffs, use_favorites=False, cache_file=None):
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

    def tvshow_to_listitem(self, tvshow, program, cache_file):
        ''' Return a ListItem based on a Suggests API result '''
        metadata = metadatacreator.MetadataCreator()
        metadata.tvshowtitle = tvshow.get('title', '???')
        metadata.plot = statichelper.unescape(tvshow.get('description', '???'))
        metadata.brands.extend(tvshow.get('brands', []))
        metadata.permalink = statichelper.shorten_link(tvshow.get('targetUrl'))
        # NOTE: This adds episode_count to label, would be better as metadata
        # title = '%s  [LIGHT][COLOR yellow]%s[/COLOR][/LIGHT]' % (tvshow.get('title', '???'), tvshow.get('episode_count', '?'))
        label = tvshow.get('title', '???')
        if self._showfanart:
            thumbnail = statichelper.add_https_method(tvshow.get('thumbnail', 'DefaultAddonVideo.png'))
        else:
            thumbnail = 'DefaultAddonVideo.png'
        if self._favorites.is_activated():
            program_title = quote_plus(statichelper.from_unicode(tvshow.get('title')))  # We need to ensure forward slashes are quoted
            if self._favorites.is_favorite(program):
                context_menu = [(self._kodi.localize(30412), 'RunPlugin(%s)' % self._kodi.url_for('unfollow', program=program, title=program_title))]
                label += '[COLOR yellow]ᵛ[/COLOR]'
            else:
                context_menu = [(self._kodi.localize(30411), 'RunPlugin(%s)' % self._kodi.url_for('follow', program=program, title=program_title))]
        else:
            context_menu = []
        context_menu.append((self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file=cache_file)))
        return TitleItem(
            title=label,
            path=self._kodi.url_for('programs', program=program),
            art_dict=dict(thumb=thumbnail, icon='DefaultAddonVideo.png', fanart=thumbnail),
            info_dict=metadata.get_info_dict(),
            context_menu=context_menu,
        )

    def get_latest_episode(self, program):
        ''' Get the latest episode of a program '''
        import json
        video = None
        params = {
            'facets[programUrl]': statichelper.program_to_url(program, 'long'),
            'i': 'video',
            'size': '1',
        }
        search_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
        self._kodi.log_notice('URL get: ' + unquote(search_url), 'Verbose')
        search_json = json.load(urlopen(search_url))
        if search_json.get('meta', {}).get('total_results') != 0:
            episode = list(search_json.get('results'))[0]
            video = dict(video_id=episode.get('videoId'), publication_id=episode.get('publicationId'))
        return video

    def get_episode_by_air_date(self, channel_name, start_date, end_date=None):
        ''' Get an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00) '''
        import json
        from datetime import datetime, timedelta
        import dateutil.parser
        import dateutil.tz
        offairdate = None
        try:
            channel = next(c for c in CHANNELS if c.get('name') == channel_name)
        except StopIteration:
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
        onairdate_isostr = onairdate.isoformat()
        url = 'https://www.vrt.be/bin/epg/schedule.%s.json' % onairdate_isostr.split('T')[0]
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
            if episode_guess_on.get('url'):
                video_url = statichelper.add_https_method(episode_guess_on.get('url'))
                video = dict(video_url=video_url)
            # Airdate live2vod feature
            elif now - timedelta(hours=24) <= dateutil.parser.parse(episode_guess_on.get('endTime')) <= now:
                video = dict(
                    video_id=channel.get('live_stream_id'),
                    start_date=onairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19],
                    end_date=offairdate_guess.astimezone(dateutil.tz.UTC).isoformat()[0:19],
                )
            elif offairdate and now - timedelta(hours=24) <= offairdate <= now:
                video = dict(
                    video_id=channel.get('live_stream_id'),
                    start_date=onairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19],
                    end_date=offairdate.astimezone(dateutil.tz.UTC).isoformat()[0:19],
                )
            else:
                video_title = episode_guess_on.get('title')
                video = dict(video_title=video_title)
        return video

    def get_episode_items(self, program=None, season=None, category=None, feature=None, programtype=None, page=None, use_favorites=False, variety=None):
        ''' Construct a list of TV show episodes TitleItems based on API query and filtered by favorites '''
        titletype = None
        all_items = True
        episode_items = []
        sort = 'episode'
        ascending = True
        content = 'episodes'

        # Recent items
        if variety in ('offline', 'recent'):
            titletype = 'recent'
            all_items = False
            page = statichelper.realpage(page)
            params = {
                'from': ((page - 1) * 50) + 1,
                'i': 'video',
                'size': 50,
            }

            if variety == 'offline':
                from datetime import datetime
                import dateutil.tz
                params['facets[assetOffTime]'] = datetime.now(dateutil.tz.gettz('Europe/Brussels')).strftime('%Y-%m-%d')

            if use_favorites:
                program_urls = [statichelper.program_to_url(p, 'long') for p in self._favorites.programs()]
                params['facets[programUrl]'] = '[%s]' % (','.join(program_urls))
                cache_file = 'my-%s-%s.json' % (variety, page)
            else:
                channel_filter = [channel.get('name') for channel in CHANNELS if self._kodi.get_setting(channel.get('name'), 'true') == 'true']
                params['facets[programBrands]'] = '[%s]' % (','.join(channel_filter))
                cache_file = '%s-%s.json' % (variety, page)

            # Try the cache if it is fresh
            search_json = self._kodi.get_cache(cache_file, ttl=60 * 60)
            if not search_json:
                import json
                search_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
                self._kodi.log_notice('URL get: ' + unquote(search_url), 'Verbose')
                search_json = json.load(urlopen(search_url))
                self._kodi.update_cache(cache_file, search_json)
            return self._map_to_episode_items(search_json.get('results', []), titletype=variety, use_favorites=use_favorites, cache_file=cache_file)

        params = {
            'i': 'video',
            'size': '300',
        }

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

        search_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
        results, episodes = self._get_season_episode_data(search_url, season, all_items=all_items)

        if results.get('episodes'):
            return self._map_to_episode_items(results.get('episodes', []), titletype=titletype, season=season, use_favorites=use_favorites)

        if results.get('seasons'):
            return self._map_to_season_items(program, results.get('seasons'), episodes)

        return episode_items, sort, ascending, content

    def _get_season_data(self, search_json):
        ''' Return a list of seasons '''
        facets = search_json.get('facets', dict()).get('facets')
        seasons = next((f.get('buckets', []) for f in facets if f.get('name') == 'seasons' and len(f.get('buckets', [])) > 1), None)
        return seasons

    def _get_season_episode_data(self, search_url, season, all_items=True):
        ''' Return a list of episodes for a given season '''
        import json
        self._kodi.log_notice('URL get: ' + unquote(search_url), 'Verbose')
        show_seasons = bool(not season == 'allseasons')
        search_json = json.load(urlopen(search_url))
        seasons = self._get_season_data(search_json) if 'facets[seasonTitle]' not in unquote(search_url) else None
        episodes = search_json.get('results', [{}])
        if show_seasons and seasons:
            return dict(seasons=seasons), episodes
        pages = search_json.get('meta').get('pages').get('total')
        page_size = search_json.get('meta').get('pages').get('size')
        total_results = search_json.get('meta').get('total_results')
        if all_items and total_results > page_size:
            for page in range(1, pages):
                page_url = search_url + '&from=' + str(page * page_size + 1)
                self._kodi.log_notice('URL get: ' + unquote(page_url), 'Verbose')
                page_json = json.load(urlopen(page_url))
                episodes += page_json.get('results', [{}])
        return dict(episodes=episodes), None

    def _map_to_episode_items(self, episodes, titletype=None, season=None, use_favorites=False, cache_file=None):
        ''' Construct a list of TV show episodes TitleItems based on Search API query and filtered by favorites '''
        sort = 'episode'
        ascending = True

        if use_favorites:
            favorite_programs = self._favorites.programs()

        episode_items = []
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

        return episode_items, sort, ascending, 'episodes'

    def episode_to_listitem(self, episode, program, cache_file, titletype):
        ''' Return a ListItem based on a Search API result '''
        from datetime import datetime
        import dateutil.parser
        import dateutil.tz
        now = datetime.now(dateutil.tz.tzlocal())

        display_options = episode.get('displayOptions', dict())

        # NOTE: Hard-code showing seasons because it is unreliable (i.e; Thuis or Down the Road have it disabled)
        display_options['showSeason'] = True

        if titletype is None:
            titletype = episode.get('programType')

        metadata = metadatacreator.MetadataCreator()
        metadata.tvshowtitle = episode.get('program')
        if episode.get('broadcastDate') != -1:
            metadata.datetime = datetime.fromtimestamp(episode.get('broadcastDate', 0) / 1000, dateutil.tz.UTC)

        metadata.duration = (episode.get('duration', 0) * 60)  # Minutes to seconds
        metadata.plot = statichelper.convert_html_to_kodilabel(episode.get('description'))
        metadata.brands.extend(episode.get('programBrands', []) or episode.get('brands', []))
        metadata.geoblocked = episode.get('allowedRegion') == 'BE'
        if display_options.get('showShortDescription'):
            short_description = statichelper.convert_html_to_kodilabel(episode.get('shortDescription'))
            metadata.plotoutline = short_description
            metadata.subtitle = short_description
        else:
            metadata.plotoutline = episode.get('subtitle')
            metadata.subtitle = episode.get('subtitle')
        metadata.season = episode.get('seasonTitle')
        metadata.episode = episode.get('episodeNumber')
        metadata.mediatype = episode.get('type', 'episode')
        metadata.permalink = statichelper.shorten_link(episode.get('permalink')) or episode.get('externalPermalink')
        if episode.get('assetOnTime'):
            metadata.ontime = dateutil.parser.parse(episode.get('assetOnTime'))
        if episode.get('assetOffTime'):
            metadata.offtime = dateutil.parser.parse(episode.get('assetOffTime'))

        # Add additional metadata to plot
        plot_meta = ''
        if metadata.geoblocked:
            # Show Geo-blocked
            plot_meta += self._kodi.localize(30201)

        # Only display when a video disappears if it is within the next 3 months
        if metadata.offtime is not None and (metadata.offtime - now).days < 93:
            # Show date when episode is removed
            plot_meta += self._kodi.localize(30202).format(date=self._kodi.localize_dateshort(metadata.offtime))
            # Show the remaining days/hours the episode is still available
            if (metadata.offtime - now).days > 0:
                plot_meta += self._kodi.localize(30203).format(days=(metadata.offtime - now).days)
            else:
                plot_meta += self._kodi.localize(30204).format(hours=int((metadata.offtime - now).seconds / 3600))

        if plot_meta:
            metadata.plot = '%s\n%s' % (plot_meta, metadata.plot)

        if self._showpermalink and metadata.permalink:
            metadata.plot = '%s\n\n[COLOR yellow]%s[/COLOR]' % (metadata.plot, metadata.permalink)

        label, sort, ascending = self._make_label(episode, titletype, options=display_options)
        if self._favorites.is_activated():
            program_title = quote_plus(statichelper.from_unicode(episode.get('program')))  # We need to ensure forward slashes are quoted
            if self._favorites.is_favorite(program):
                context_menu = [(self._kodi.localize(30412), 'RunPlugin(%s)' % self._kodi.url_for('unfollow', program=program, title=program_title))]
                label += '[COLOR yellow]ᵛ[/COLOR]'
            else:
                context_menu = [(self._kodi.localize(30411), 'RunPlugin(%s)' % self._kodi.url_for('follow', program=program, title=program_title))]
        else:
            context_menu = []
        context_menu.append((self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file=cache_file)))

        if self._showfanart:
            thumb = statichelper.add_https_method(episode.get('videoThumbnailUrl', 'DefaultAddonVideo.png'))
            fanart = statichelper.add_https_method(episode.get('programImageUrl', thumb))
        else:
            thumb = 'DefaultAddonVideo.png'
            fanart = 'DefaultAddonVideo.png'
        metadata.title = label

        return TitleItem(
            title=label,
            path=self._kodi.url_for('play_id', video_id=episode.get('videoId'), publication_id=episode.get('publicationId')),
            art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=fanart, banner=fanart),
            info_dict=metadata.get_info_dict(),
            context_menu=context_menu,
            is_playable=True,
        ), sort, ascending

    def _map_to_season_items(self, program, seasons, episodes):
        ''' Construct a list of TV show season TitleItems based on Search API query and filtered by favorites '''
        import random

        season_items = []
        sort = 'label'
        ascending = True

        episode = random.choice(episodes)
        program_type = episode.get('programType')
        if self._showfanart:
            fanart = statichelper.add_https_method(episode.get('programImageUrl', 'DefaultSets.png'))
        else:
            fanart = 'DefaultSets.png'

        metadata = metadatacreator.MetadataCreator()
        metadata.tvshowtitle = episode.get('program')
        metadata.plot = statichelper.convert_html_to_kodilabel(episode.get('programDescription'))
        metadata.plotoutline = statichelper.convert_html_to_kodilabel(episode.get('programDescription'))
        metadata.brands.extend(episode.get('programBrands', []) or episode.get('brands', []))
        metadata.geoblocked = episode.get('allowedRegion') == 'BE'
        metadata.season = episode.get('seasonTitle')

        # Add additional metadata to plot
        plot_meta = ''
        if metadata.geoblocked:
            # Show Geo-blocked
            plot_meta += self._kodi.localize(30201) + '\n'
        metadata.plot = '%s[B]%s[/B]\n%s' % (plot_meta, episode.get('program'), metadata.plot)

        # Reverse sort seasons if program_type is 'reeksaflopend' or 'daily'
        if program_type in ('daily', 'reeksaflopend'):
            ascending = False

        # Add an "* All seasons" list item
        if self._kodi.get_global_setting('videolibrary.showallitems') is True:
            season_items.append(TitleItem(
                title=self._kodi.localize(30096),
                path=self._kodi.url_for('programs', program=program, season='allseasons'),
                art_dict=dict(thumb=fanart, icon='DefaultSets.png', fanart=fanart),
                info_dict=metadata.get_info_dict(),
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
            if self._showfanart:
                fanart = statichelper.add_https_method(episode.get('programImageUrl', 'DefaultSets.png'))
                thumbnail = statichelper.add_https_method(episode.get('videoThumbnailUrl', fanart))
            else:
                fanart = 'DefaultSets.png'
                thumbnail = 'DefaultSets.png'
            label = '%s %s' % (self._kodi.localize(30094), season_key)
            season_items.append(TitleItem(
                title=label,
                path=self._kodi.url_for('programs', program=program, season=season_key),
                art_dict=dict(thumb=thumbnail, icon='DefaultSets.png', fanart=fanart),
                info_dict=metadata.get_info_dict(),
            ))
        return season_items, sort, ascending, 'seasons'

    def get_search_items(self, keywords, page=0):
        ''' Search VRT NU content for a given string '''
        import json

        page = statichelper.realpage(page)
        params = {
            'from': ((page - 1) * 50) + 1,
            'i': 'video',
            'size': 50,
            'q': keywords,
            'highlight': 'true',
        }
        search_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
        self._kodi.log_notice('URL get: ' + unquote(search_url), 'Verbose')
        search_json = json.load(urlopen(search_url))

        episodes = search_json.get('results', [{}])
        return self._map_to_episode_items(episodes, titletype='recent')

    def get_live_screenshot(self, channel):
        ''' Get a live screenshot for a given channel, only supports Eén, Canvas and Ketnet '''
        url = '%s/%s.jpg' % (self._VRTNU_SCREENSHOT_URL, channel)
        self.__delete_cached_thumbnail(url)
        return url

    def __delete_cached_thumbnail(self, url):
        ''' Remove a cached thumbnail from Kodi in an attempt to get a realtime live screenshot '''
        crc = self.__get_crc32(url)
        ext = url.split('.')[-1]
        path = 'special://thumbnails/%s/%s.%s' % (crc[0], crc, ext)
        self._kodi.delete_file(path)

    @staticmethod
    def __get_crc32(string):
        ''' Return the CRC32 checksum for a given string '''
        string = string.lower()
        string_bytes = bytearray(string.encode())
        crc = 0xffffffff
        for b in string_bytes:
            crc = crc ^ (b << 24)
            for _ in range(8):
                if crc & 0x80000000:
                    crc = (crc << 1) ^ 0x04C11DB7
                else:
                    crc = crc << 1
            crc = crc & 0xFFFFFFFF
        return '%08x' % crc

    def _make_label(self, result, titletype, options=None):
        ''' Return an appropriate label matching the type of listing and VRT NU provided displayOptions '''
        if options is None:
            options = dict()

        if options.get('showEpisodeTitle'):
            label = statichelper.convert_html_to_kodilabel(result.get('title') or result.get('shortDescription'))
        elif options.get('showShortDescription'):
            label = statichelper.convert_html_to_kodilabel(result.get('shortDescription') or result.get('title'))
        else:
            label = statichelper.convert_html_to_kodilabel(result.get('title') or result.get('shortDescription'))

        sort = 'unsorted'
        ascending = True

        if titletype in ('offline', 'recent'):
            ascending = False
            label = '[B]%s[/B] - %s' % (result.get('program'), label)
            sort = 'dateadded'

        elif titletype in ('reeksaflopend', 'reeksoplopend'):

            if titletype == 'reeksaflopend':
                ascending = False

            # NOTE: This is disable on purpose as 'showSeason' is not reliable
            if options.get('showSeason') is False and options.get('showEpisodeNumber') and result.get('seasonName') and result.get('episodeNumber'):
                try:
                    label = 'S%02dE%02d: %s' % (int(result.get('seasonName')), int(result.get('episodeNumber')), label)
                    sort = 'dateadded'
                except Exception:
                    # Season may not always be a perfect number
                    sort = 'episode'
            elif options.get('showEpisodeNumber') and result.get('episodeNumber') and ascending:
                # NOTE: Do not prefix with "Episode X" when sorting by episode
                # label = '%s %s: %s' % (self._kodi.localize(30095), result.get('episodeNumber'), label)
                sort = 'episode'
            elif options.get('showBroadcastDate') and result.get('formattedBroadcastShortDate'):
                label = '%s - %s' % (result.get('formattedBroadcastShortDate'), label)
                sort = 'dateadded'
            else:
                sort = 'dateadded'

        elif titletype == 'daily':
            ascending = False
            label = '%s - %s' % (result.get('formattedBroadcastShortDate'), label)
            sort = 'dateadded'

        elif titletype == 'oneoff':
            label = result.get('program', label)
            sort = 'label'

        return label, sort, ascending

    def get_channel_items(self, channels=None, live=True):
        ''' Construct a list of channel ListItems, either for Live TV or the TV Guide listing '''
        from resources.lib import tvguide
        _tvguide = tvguide.TVGuide(self._kodi)

        channel_items = []
        for channel in CHANNELS:
            if channels and channel.get('name') not in channels:
                continue

            fanart = 'resource://resource.images.studios.coloured/%(studio)s.png' % channel
            thumb = 'resource://resource.images.studios.white/%(studio)s.png' % channel

            if not live:
                path = self._kodi.url_for('channels', channel=channel.get('name'))
                label = channel.get('label')
                plot = '[B]%s[/B]' % channel.get('label')
                is_playable = False
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video')
                stream_dict = []
                context_menu = []
            elif channel.get('live_stream') or channel.get('live_stream_id'):
                if channel.get('live_stream_id'):
                    path = self._kodi.url_for('play_id', video_id=channel.get('live_stream_id'))
                elif channel.get('live_stream'):
                    path = self._kodi.url_for('play_url', video_url=channel.get('live_stream'))
                label = self._kodi.localize(30101).format(**channel)
                # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
                if channels and len(channels) == 1:
                    label = '[B]%s[/B]' % label
                is_playable = True
                if channel.get('name') in ['een', 'canvas', 'ketnet']:
                    if self._showfanart:
                        fanart = self.get_live_screenshot(channel.get('name', fanart))
                    plot = '%s\n\n%s' % (self._kodi.localize(30102).format(**channel), _tvguide.live_description(channel.get('name')))
                else:
                    plot = self._kodi.localize(30102).format(**channel)
                # NOTE: Playcount is required to not have live streams as "Watched"
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video', playcount=0, duration=0)
                stream_dict = dict(duration=0)
                context_menu = [(self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file='channel.%s.json' % channel))]
            else:
                # Not a playable channel
                continue

            channel_items.append(TitleItem(
                title=label,
                path=path,
                art_dict=dict(thumb=thumb, fanart=fanart),
                info_dict=info_dict,
                stream_dict=stream_dict,
                context_menu=context_menu,
                is_playable=is_playable,
            ))

        return channel_items

    def get_youtube_items(self, channels=None, live=True):
        ''' Construct a list of channel ListItems, either for Live TV or the TV Guide listing '''

        youtube_items = []

        if self._kodi.get_cond_visibility('System.HasAddon(plugin.video.youtube)') == 0 or self._kodi.get_setting('showyoutube') == 'false':
            return youtube_items

        for channel in CHANNELS:
            if channels and channel.get('name') not in channels:
                continue

            fanart = 'resource://resource.images.studios.coloured/%(studio)s.png' % channel
            thumb = 'resource://resource.images.studios.white/%(studio)s.png' % channel

            if channel.get('youtube'):
                path = channel.get('youtube')
                label = self._kodi.localize(30103).format(**channel)
                # A single Live channel means it is the entry for channel's TV Show listing, so make it stand out
                if channels and len(channels) == 1:
                    label = '[B]%s[/B]' % label
                plot = self._kodi.localize(30104).format(**channel)
                # NOTE: Playcount is required to not have live streams as "Watched"
                info_dict = dict(title=label, plot=plot, studio=channel.get('studio'), mediatype='video', playcount=0)
                context_menu = [(self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file='channel.%s.json' % channel))]
            else:
                # Not a playable channel
                continue

            youtube_items.append(TitleItem(
                title=label,
                path=path,
                art_dict=dict(thumb=thumb, fanart=fanart),
                info_dict=info_dict,
                context_menu=context_menu,
                is_playable=False,
            ))

        return youtube_items

    def get_featured_items(self):
        ''' Construct a list of featured Listitems '''
        from resources.lib import FEATURED

        featured_items = []
        for feature in FEATURED:
            featured_name = self._kodi.localize_from_data(feature.get('name'), FEATURED)
            featured_items.append(TitleItem(
                title=featured_name,
                path=self._kodi.url_for('featured', feature=feature.get('id')),
                art_dict=dict(thumb='DefaultCountry.png', fanart='DefaultCountry.png'),
                info_dict=dict(plot='[B]%s[/B]' % featured_name, studio='VRT'),
            ))
        return featured_items

    def get_category_items(self):
        ''' Construct a list of category ListItems '''
        categories = []

        # Try the cache if it is fresh
        categories = self._kodi.get_cache('categories.json', ttl=7 * 24 * 60 * 60)

        # Try to scrape from the web
        if not categories:
            try:
                categories = self.get_categories(self._proxies)
            except Exception:
                categories = []
            else:
                self._kodi.update_cache('categories.json', categories)

        # Use the cache anyway (better than hard-coded)
        if not categories:
            categories = self._kodi.get_cache('categories.json', ttl=None)

        # Fall back to internal hard-coded categories if all else fails
        if not categories:
            categories = CATEGORIES

        category_items = []
        for category in categories:
            if self._showfanart:
                thumbnail = category.get('thumbnail', 'DefaultGenre.png')
            else:
                thumbnail = 'DefaultGenre.png'
            category_name = self._kodi.localize_from_data(category.get('name'), CATEGORIES)
            category_items.append(TitleItem(
                title=category_name,
                path=self._kodi.url_for('categories', category=category.get('id')),
                art_dict=dict(thumb=thumbnail, icon='DefaultGenre.png', fanart=thumbnail),
                info_dict=dict(plot='[B]%s[/B]' % category_name, studio='VRT'),
            ))
        return category_items

    def get_categories(self, proxies=None):
        ''' Return a list of categories by scraping the website '''
        from bs4 import BeautifulSoup, SoupStrainer
        self._kodi.log_notice('URL get: https://www.vrt.be/vrtnu/categorieen/', 'Verbose')
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
