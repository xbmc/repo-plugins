# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from resources.lib import CHANNELS, actions, metadatacreator, statichelper
from resources.lib.helperobjects import TitleItem

try:
    from urllib.parse import urlencode, unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, urlopen
except ImportError:
    from urllib import urlencode
    from urllib2 import build_opener, install_opener, ProxyHandler, urlopen, unquote


class VRTApiHelper:

    _VRT_BASE = 'https://www.vrt.be'
    _VRTNU_SEARCH_URL = 'https://vrtnu-api.vrt.be/search'
    _VRTNU_SUGGEST_URL = 'https://vrtnu-api.vrt.be/suggest'
    _VRTNU_SCREENSHOT_URL = 'https://vrtnu-api.vrt.be/screenshots'

    def __init__(self, _kodi, _favorites):
        self._kodi = _kodi
        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))
        self._showfanart = _kodi.get_setting('showfanart') == 'true'
        self._showpermalink = _kodi.get_setting('showpermalink') == 'true'
        self._favorites = _favorites
        self._channel_filter = [channel.get('name') for channel in CHANNELS if _kodi.get_setting(channel.get('name')) == 'true']

    def get_tvshow_items(self, category=None, channel=None, use_favorites=False):
        params = dict()

        if category:
            params['facets[categories]'] = category
            cache_file = 'category.%s.json' % category

        if channel:
            params['facets[programBrands]'] = channel
            cache_file = 'channel.%s.json' % channel

        # If no facet-selection is done, we return the A-Z listing
        if not category and not channel:
            params['facets[transcodingStatus]'] = 'AVAILABLE'
            cache_file = 'programs.json'

        # Try the cache if it is fresh
        api_json = self._kodi.get_cache(cache_file, ttl=60 * 60)
        if not api_json:
            import json
            api_url = self._VRTNU_SUGGEST_URL + '?' + urlencode(params)
            self._kodi.log_notice('URL get: ' + unquote(api_url), 'Verbose')
            api_json = json.load(urlopen(api_url))
            self._kodi.update_cache(cache_file, api_json)
        return self._map_to_tvshow_items(api_json, use_favorites=statichelper.boolean(use_favorites))

    def _map_to_tvshow_items(self, tvshows, use_favorites=False):
        tvshow_items = []
        if statichelper.boolean(use_favorites):
            favorite_names = self._favorites.names()
        for tvshow in tvshows:
            if statichelper.boolean(use_favorites) and tvshow.get('programName') not in favorite_names:
                continue
            metadata = metadatacreator.MetadataCreator()
            metadata.tvshowtitle = tvshow.get('title', '???')
            metadata.plot = statichelper.unescape(tvshow.get('description', '???'))
            metadata.brands = tvshow.get('brands')
            metadata.permalink = statichelper.shorten_link(tvshow.get('targetUrl'))
            # NOTE: This adds episode_count to label, would be better as metadata
            # title = '%s  [LIGHT][COLOR yellow]%s[/COLOR][/LIGHT]' % (tvshow.get('title', '???'), tvshow.get('episode_count', '?'))
            label = tvshow.get('title', '???')
            if self._showfanart:
                thumbnail = statichelper.add_https_method(tvshow.get('thumbnail', 'DefaultAddonVideo.png'))
            else:
                thumbnail = 'DefaultAddonVideo.png'
            if self._favorites.is_activated():
                program_path = statichelper.unique_path(tvshow.get('targetUrl'))
                program = tvshow.get('title').encode('utf-8')
                if self._favorites.is_favorite(program_path):
                    params = dict(action='unfollow', program=program, path=program_path)
                    context_menu = [(self._kodi.localize(30412), 'RunPlugin(plugin://plugin.video.vrt.nu?%s)' % urlencode(params))]
                else:
                    params = dict(action='follow', program=program, path=program_path)
                    context_menu = [(self._kodi.localize(30411), 'RunPlugin(plugin://plugin.video.vrt.nu?%s)' % urlencode(params))]
            else:
                context_menu = []
            # Cut vrtbase url off since it will be added again when searching for episodes
            # (with a-z we dont have the full url)
            video_url = statichelper.add_https_method(tvshow.get('targetUrl')).replace(self._VRT_BASE, '')
            tvshow_items.append(TitleItem(
                title=label,
                url_dict=dict(action=actions.LISTING_EPISODES, video_url=video_url),
                is_playable=False,
                art_dict=dict(thumb=thumbnail, icon='DefaultAddonVideo.png', fanart=thumbnail),
                video_dict=metadata.get_video_dict(),
                context_menu=context_menu,
            ))
        return tvshow_items

    def get_episode_items(self, path=None, page=None, show_seasons=False, use_favorites=False, variety=None):
        titletype = None
        season_key = None
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

            if statichelper.boolean(use_favorites):
                params['facets[programName]'] = '[%s]' % (','.join(self._favorites.names()))
                cache_file = 'my-%s-%s.json' % (variety, page)
            else:
                params['facets[programBrands]'] = '[%s]' % ','.join(self._channel_filter)
                cache_file = '%s-%s.json' % (variety, page)

            # Try the cache if it is fresh
            api_json = self._kodi.get_cache(cache_file, ttl=60 * 60)
            if not api_json:
                import json
                api_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
                self._kodi.log_notice('URL get: ' + unquote(api_url), 'Verbose')
                api_json = json.load(urlopen(api_url))
                self._kodi.update_cache(cache_file, api_json)
            episode_items, sort, ascending, content = self._map_to_episode_items(api_json.get('results', []), titletype=variety, use_favorites=statichelper.boolean(use_favorites))

        elif path:
            if '.relevant/' in path:
                params = {
                    'facets[programUrl]': '//www.vrt.be' + path.replace('.relevant/', '/'),
                    'i': 'video',
                    'size': '150',
                }
                api_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
            else:
                api_url = path

            path = unquote(path)
            if 'facets[seasonTitle]' in path:
                season_key = path.split('facets[seasonTitle]=')[1]

            results, episodes = self._get_season_episode_data(api_url, show_seasons=show_seasons, all_items=all_items)

            if results.get('episodes'):
                episode_items, sort, ascending, content = self._map_to_episode_items(results.get('episodes'), titletype=titletype, season_key=season_key, use_favorites=use_favorites)
            elif results.get('seasons'):
                episode_items, sort, ascending, content = self._map_to_season_items(api_url, results.get('seasons'), episodes)

        return episode_items, sort, ascending, content

    def _get_season_data(self, api_json):
        facets = api_json.get('facets', dict()).get('facets')
        seasons = next((f.get('buckets', []) for f in facets if f.get('name') == 'seasons' and len(f.get('buckets', [])) > 1), None)
        return seasons

    def _get_season_episode_data(self, api_url, show_seasons, all_items=True):
        import json
        self._kodi.log_notice('URL get: ' + unquote(api_url), 'Verbose')
        api_json = json.load(urlopen(api_url))
        seasons = self._get_season_data(api_json)
        episodes = api_json.get('results', [{}])
        if show_seasons and seasons:
            return dict(seasons=seasons), episodes
        pages = api_json.get('meta').get('pages').get('total')
        page_size = api_json.get('meta').get('pages').get('size')
        total_results = api_json.get('meta').get('total_results')
        if all_items and total_results > page_size:
            for page in range(1, pages):
                page_url = api_url + '&from=' + str(page * page_size + 1)
                self._kodi.log_notice('URL get: ' + unquote(page_url), 'Verbose')
                page_json = json.load(urlopen(page_url))
                episodes += page_json.get('results', [{}])
        return dict(episodes=episodes), None

    def _map_to_episode_items(self, episodes, titletype=None, season_key=None, use_favorites=False):
        from datetime import datetime
        import dateutil.parser
        import dateutil.tz
        now = datetime.now(dateutil.tz.tzlocal())
        sort = 'episode'
        ascending = True
        if statichelper.boolean(use_favorites):
            favorite_names = self._favorites.names()
        episode_items = []
        for episode in episodes:
            # VRT API workaround: seasonTitle facet behaves as a partial match regex,
            # so we have to filter out the episodes from seasons that don't exactly match.
            if season_key and episode.get('seasonTitle') != season_key:
                continue

            if statichelper.boolean(use_favorites) and episode.get('programName') not in favorite_names:
                continue

            # Support search highlights
            highlight = episode.get('highlight')
            if highlight:
                for key in highlight:
                    episode[key] = statichelper.convert_html_to_kodilabel(highlight.get(key)[0])

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
            metadata.brands = episode.get('programBrands') or episode.get('brands')
            metadata.geolocked = episode.get('allowedRegion') == 'BE'
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
            if metadata.geolocked:
                # Show Geo-locked
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

            if self._favorites.is_activated():
                program_path = statichelper.unique_path(episode.get('programUrl'))
                program = episode.get('program').encode('utf-8')
                if self._favorites.is_favorite(program_path):
                    params = dict(action='unfollow', program=program, path=program_path)
                    context_menu = [(self._kodi.localize(30412), 'RunPlugin(plugin://plugin.video.vrt.nu?%s)' % urlencode(params))]
                else:
                    params = dict(action='follow', program=program, path=program_path)
                    context_menu = [(self._kodi.localize(30411), 'RunPlugin(plugin://plugin.video.vrt.nu?%s)' % urlencode(params))]
            else:
                context_menu = []

            if self._showfanart:
                thumb = statichelper.add_https_method(episode.get('videoThumbnailUrl', 'DefaultAddonVideo.png'))
                fanart = statichelper.add_https_method(episode.get('programImageUrl', thumb))
            else:
                thumb = 'DefaultAddonVideo.png'
                fanart = 'DefaultAddonVideo.png'
            video_url = statichelper.add_https_method(episode.get('url'))
            label, sort, ascending = self._make_label(episode, titletype, options=display_options)
            metadata.title = label
            episode_items.append(TitleItem(
                title=label,
                url_dict=dict(action=actions.PLAY, video_url=video_url, video_id=episode.get('videoId'), publication_id=episode.get('publicationId')),
                is_playable=True,
                art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=fanart),
                video_dict=metadata.get_video_dict(),
                context_menu=context_menu,
            ))

        return episode_items, sort, ascending, 'episodes'

    def _map_to_season_items(self, api_url, seasons, episodes):
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
        metadata.brands = episode.get('programBrands') or episode.get('brands')
        metadata.geolocked = episode.get('allowedRegion') == 'BE'
        metadata.season = episode.get('seasonTitle')

        # Add additional metadata to plot
        plot_meta = ''
        if metadata.geolocked:
            # Show Geo-locked
            plot_meta += self._kodi.localize(30201) + '\n'
        metadata.plot = '%s[B]%s[/B]\n%s' % (plot_meta, episode.get('program'), metadata.plot)

        # Reverse sort seasons if program_type is 'reeksaflopend' or 'daily'
        if program_type in ('daily', 'reeksaflopend'):
            ascending = False

        # Add an "* All seasons" list item
        if self._kodi.get_global_setting('videolibrary.showallitems') is True:
            season_items.append(TitleItem(
                title=self._kodi.localize(30096),
                url_dict=dict(action=actions.LISTING_ALL_EPISODES, video_url=api_url),
                is_playable=False,
                art_dict=dict(thumb=fanart, icon='DefaultSets.png', fanart=fanart),
                video_dict=metadata.get_video_dict(),
            ))

        # NOTE: Sort the episodes ourselves, because Kodi does not allow to set to 'ascending'
        seasons = sorted(seasons, key=lambda k: k['key'], reverse=not ascending)

        for season in seasons:
            season_key = season['key']
            try:
                # If more than 150 episodes exist, we may end up with an empty season (Winteruur)
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
            params = {'facets[seasonTitle]': season_key}
            path = api_url + '&' + urlencode(params)
            season_items.append(TitleItem(
                title=label,
                url_dict=dict(action=actions.LISTING_EPISODES, video_url=path),
                is_playable=False,
                art_dict=dict(thumb=thumbnail, icon='DefaultSets.png', fanart=fanart),
                video_dict=metadata.get_video_dict(),
            ))
        return season_items, sort, ascending, 'seasons'

    def search(self, search_string, page=0):
        import json

        page = statichelper.realpage(page)
        params = {
            'from': ((page - 1) * 50) + 1,
            'i': 'video',
            'size': 50,
            'q': search_string,
            'highlight': 'true',
        }
        api_url = 'https://search.vrt.be/search?' + urlencode(params)
        self._kodi.log_notice('URL get: ' + unquote(api_url), 'Verbose')
        api_json = json.load(urlopen(api_url))

        episodes = api_json.get('results', [{}])
        episode_items, sort, ascending, content = self._map_to_episode_items(episodes, titletype='recent')
        return episode_items, sort, ascending, content

    def get_live_screenshot(self, channel):
        url = '%s/%s.jpg' % (self._VRTNU_SCREENSHOT_URL, channel)
        self.__delete_cached_thumbnail(url)
        return url

    def __delete_cached_thumbnail(self, url):
        crc = self.__get_crc32(url)
        ext = url.split('.')[-1]
        path = 'special://thumbnails/%s/%s.%s' % (crc[0], crc, ext)
        self._kodi.delete_file(path)

    @staticmethod
    def __get_crc32(string):
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
            sort = 'dateadded'
            label = '[B]%s[/B] - %s' % (result.get('program'), label)

        elif titletype in ('reeksaflopend', 'reeksoplopend'):

            if titletype == 'reeksaflopend':
                ascending = False

            # NOTE: This is disable on purpose as 'showSeason' is not reliable
            if options.get('showSeason') is False and options.get('showEpisodeNumber') and result.get('seasonName') and result.get('episodeNumber'):
                try:
                    sort = 'dateadded'
                    label = 'S%02dE%02d: %s' % (int(result.get('seasonName')), int(result.get('episodeNumber')), label)
                except Exception:
                    # Season may not always be a perfect number
                    sort = 'episode'
            elif options.get('showEpisodeNumber') and result.get('episodeNumber') and ascending:
                # NOTE: Sort the episodes ourselves, because Kodi does not allow to set to 'descending'
                # sort = 'episode'
                sort = 'label'
                label = '%s %s: %s' % (self._kodi.localize(30095), result.get('episodeNumber'), label)
            elif options.get('showBroadcastDate') and result.get('formattedBroadcastShortDate'):
                sort = 'dateadded'
                label = '%s - %s' % (result.get('formattedBroadcastShortDate'), label)
            else:
                sort = 'dateadded'

        elif titletype == 'daily':
            ascending = False
            sort = 'dateadded'
            label = '%s - %s' % (result.get('formattedBroadcastShortDate'), label)

        elif titletype == 'oneoff':
            sort = 'label'

        return label, sort, ascending

    def get_channel_items(self, action=actions.PLAY, channels=None):
        from resources.lib import tvguide
        _tvguide = tvguide.TVGuide(self._kodi)

        fanart_path = 'resource://resource.images.studios.white/%(studio)s.png'
        icon_path = 'resource://resource.images.studios.white/%(studio)s.png'
        # NOTE: Wait for resource.images.studios.coloured v0.16 to be released
        # icon_path = 'resource://resource.images.studios.coloured/%(studio)s.png'

        channel_items = []
        for channel in CHANNELS:
            if channel.get('name') not in channels:
                continue

            icon = icon_path % channel
            fanart = fanart_path % channel

            if action == actions.LISTING_CHANNELS:
                url_dict = dict(action=action, channel=channel.get('name'))
                label = channel.get('label')
                plot = '[B]%s[/B]' % channel.get('label')
                is_playable = False
            else:
                url_dict = dict(action=action)
                label = self._kodi.localize(30101).format(**channel)
                is_playable = True
                if channel.get('name') in ['een', 'canvas', 'ketnet']:
                    if self._showfanart:
                        fanart = self.get_live_screenshot(channel.get('name', fanart))
                    plot = '%s\n\n%s' % (self._kodi.localize(30102).format(**channel), _tvguide.live_description(channel.get('name')))
                else:
                    plot = self._kodi.localize(30102).format(**channel)
                if channel.get('live_stream'):
                    url_dict['video_url'] = channel.get('live_stream')
                if channel.get('live_stream_id'):
                    url_dict['video_id'] = channel.get('live_stream_id')

            channel_items.append(TitleItem(
                title=label,
                url_dict=url_dict,
                is_playable=is_playable,
                art_dict=dict(thumb=icon, icon=icon, fanart=fanart),
                video_dict=dict(
                    title=label,
                    plot=plot,
                    studio=channel.get('studio'),
                    mediatype='video',
                ),
            ))

        return channel_items

    def get_category_items(self):
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
            from resources.lib import CATEGORIES
            categories = CATEGORIES

        category_items = []
        for category in categories:
            if self._showfanart:
                thumbnail = category.get('thumbnail', 'DefaultGenre.png')
            else:
                thumbnail = 'DefaultGenre.png'
            category_items.append(TitleItem(
                title=category.get('name'),
                url_dict=dict(action=actions.LISTING_CATEGORY_TVSHOWS, category=category.get('id')),
                is_playable=False,
                art_dict=dict(thumb=thumbnail, icon='DefaultGenre.png', fanart=thumbnail),
                video_dict=dict(plot='[B]%s[/B]' % category.get('name'), studio='VRT'),
            ))
        return category_items

    def get_categories(self, proxies=None):
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
        if self._showfanart:
            raw_thumbnail = element.find(class_='media').get('data-responsive-image', 'DefaultGenre.png')
            return statichelper.add_https_method(raw_thumbnail)
        return 'DefaultGenre.png'

    @staticmethod
    def get_category_title(element):
        found_element = element.find('a')
        if found_element:
            return statichelper.strip_newlines(found_element.contents[0])
        return ''
