# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from resources.lib.helperobjects import helperobjects
from resources.lib.vrtplayer import actions, metadatacreator, statichelper

try:
    from urllib.parse import urlencode, unquote
    from urllib.request import build_opener, install_opener, ProxyHandler, urlopen
except ImportError:
    from urllib2 import build_opener, install_opener, ProxyHandler, urlopen, unquote
    from urllib import urlencode  # pylint: disable=ungrouped-imports


class VRTApiHelper:

    _VRT_BASE = 'https://www.vrt.be'
    _VRTNU_SEARCH_URL = 'https://vrtnu-api.vrt.be/search'
    _VRTNU_SUGGEST_URL = 'https://vrtnu-api.vrt.be/suggest'
    _VRTNU_SCREENSHOT_URL = 'https://vrtnu-api.vrt.be/screenshots'

    def __init__(self, kodi_wrapper):
        self._kodi_wrapper = kodi_wrapper
        self._proxies = self._kodi_wrapper.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))
        self._showpermalink = kodi_wrapper.get_setting('showpermalink') == 'true'

    def get_tvshow_items(self, category=None, channel=None):
        import json
        params = dict()

        if category:
            params['facets[categories]'] = category
        else:
            # If no path is provided, we return the A-Z listing
            params['facets[transcodingStatus]'] = 'AVAILABLE'

        if channel:
            params['facets[programBrands]'] = channel

        api_url = self._VRTNU_SUGGEST_URL + '?' + urlencode(params)
        # tvshows = requests.get(api_url, proxies=self._proxies).json()
        tvshows = json.loads(urlopen(api_url).read())
        tvshow_items = []
        for tvshow in tvshows:
            metadata = metadatacreator.MetadataCreator()
            metadata.mediatype = 'tvshow'
            metadata.tvshowtitle = tvshow.get('title', '???')
            metadata.plot = statichelper.unescape(tvshow.get('description', '???'))
            metadata.brands = tvshow.get('brands')
            metadata.permalink = statichelper.shorten_link(tvshow.get('targetUrl'))
            # NOTE: This adds episode_count to label, would be better as metadata
            # title = '%s  [LIGHT][COLOR yellow]%s[/COLOR][/LIGHT]' % (tvshow.get('title', '???'), tvshow.get('episode_count', '?'))
            label = tvshow.get('title', '???')
            thumbnail = statichelper.add_https_method(tvshow.get('thumbnail', 'DefaultAddonVideo.png'))
            # Cut vrtbase url off since it will be added again when searching for episodes
            # (with a-z we dont have the full url)
            video_url = statichelper.add_https_method(tvshow.get('targetUrl')).replace(self._VRT_BASE, '')
            tvshow_items.append(helperobjects.TitleItem(title=label,
                                                        url_dict=dict(action=actions.LISTING_EPISODES, video_url=video_url),
                                                        is_playable=False,
                                                        art_dict=dict(thumb=thumbnail, icon='DefaultAddonVideo.png', fanart=thumbnail),
                                                        video_dict=metadata.get_video_dict()))
        return tvshow_items

    def _get_season_items(self, api_url, api_json):
        season_items = []
        sort = 'label'
        ascending = True
        if api_json.get('results'):
            episode = api_json['results'][0]
        else:
            episode = dict()
        facets = api_json.get('facets', dict()).get('facets', [])
        # Check if program has seasons
        for facet in facets:
            if facet.get('name') == 'seasons' and len(facet.get('buckets', [])) > 1:
                # Found multiple seasons, make list of seasons
                season_items, sort, ascending = self._map_to_season_items(api_url, facet.get('buckets', []), episode)
        return season_items, sort, ascending

    def get_episode_items(self, path=None, page=None):
        import json
        episode_items = []
        sort = 'episode'
        ascending = True

        # Recent items
        if page:
            entries = 50
            params = {
                'from': (page - 1) * entries,
                'i': 'video',
                'size': entries,
                'facets[transcodingStatus]': 'AVAILABLE',
                'facets[programBrands]': '[een,canvas,sporza,vrtnws,vrtnxt,radio1,radio2,klara,stubru,mnm]',
            }
            api_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
            # api_json = requests.get(api_url, proxies=self._proxies).json()
            api_json = json.loads(urlopen(api_url).read())
            episode_items, sort, ascending = self._map_to_episode_items(api_json.get('results', []), titletype='recent')

        if path:
            if '.relevant/' in path:
                params = {
                    'i': 'video',
                    'size': '150',
                    'facets[programUrl]': '//www.vrt.be' + path.replace('.relevant/', '/'),
                }
                api_url = self._VRTNU_SEARCH_URL + '?' + urlencode(params)
            else:
                api_url = path
            # api_json = requests.get(api_url, proxies=self._proxies).json()
            api_json = json.loads(urlopen(api_url).read())

            episodes = api_json.get('results', [{}])
            if episodes:
                episode = episodes[0]
            else:
                episode = dict()
            display_options = episode.get('displayOptions', dict())

            # NOTE: Hard-code showing seasons because it is unreliable (i.e; Thuis or Down the Road have it disabled)
            display_options['showSeason'] = True

            # Look for seasons items if not yet done
            season_key = None
            # path = requests.utils.unquote(path)
            path = unquote(path)
            if 'facets[seasonTitle]' in path:
                season_key = path.split('facets[seasonTitle]=')[1]
            elif display_options.get('showSeason') is True:
                episode_items, sort, ascending = self._get_season_items(api_url, api_json)

            # No season items, generate episode items
            if not episode_items:
                episode_items, sort, ascending = self._map_to_episode_items(episodes, season_key=season_key)

        return episode_items, sort, ascending

    def _map_to_episode_items(self, episodes, titletype=None, season_key=None):
        from datetime import datetime
        import dateutil.parser
        import dateutil.tz
        now = datetime.now(dateutil.tz.tzlocal())
        sort = 'episode'
        ascending = True
        episode_items = []
        for episode in episodes:
            # VRT API workaround: seasonTitle facet behaves as a partial match regex,
            # so we have to filter out the episodes from seasons that don't exactly match.
            if season_key and episode.get('seasonTitle') != season_key:
                continue

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
            metadata.season = episode.get('seasonName')
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
                plot_meta += self._kodi_wrapper.get_localized_string(30201)
            # Only display when a video disappears if it is within the next 3 months
            if metadata.offtime is not None and (metadata.offtime - now).days < 93:
                # Show date when episode is removed
                plot_meta += self._kodi_wrapper.get_localized_string(30202) % metadata.offtime.strftime(self._kodi_wrapper.get_localized_dateshort())
                # Show the remaining days/hours the episode is still available
                if (metadata.offtime - now).days > 0:
                    plot_meta += self._kodi_wrapper.get_localized_string(30203) % (metadata.offtime - now).days
                else:
                    plot_meta += self._kodi_wrapper.get_localized_string(30204) % int((metadata.offtime - now).seconds / 3600)

            if plot_meta:
                metadata.plot = '%s\n%s' % (plot_meta, metadata.plot)

            if self._showpermalink and metadata.permalink:
                metadata.plot = '%s\n\n[COLOR yellow]%s[/COLOR]' % (metadata.plot, metadata.permalink)

            thumb = statichelper.add_https_method(episode.get('videoThumbnailUrl', 'DefaultAddonVideo.png'))
            fanart = statichelper.add_https_method(episode.get('programImageUrl', thumb))
            video_url = statichelper.add_https_method(episode.get('url'))
            label, sort, ascending = self._make_label(episode, titletype, options=display_options)
            metadata.title = label
            episode_items.append(helperobjects.TitleItem(
                title=label,
                url_dict=dict(action=actions.PLAY, video_url=video_url, video_id=episode.get('videoId'), publication_id=episode.get('publicationId')),
                is_playable=True,
                art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=fanart),
                video_dict=metadata.get_video_dict(),
            ))
        return episode_items, sort, ascending

    def _map_to_season_items(self, api_url, seasons, episode):
        season_items = []
        sort = 'label'
        ascending = True

        fanart = statichelper.add_https_method(episode.get('programImageUrl', 'DefaultSets.png'))
        program_type = episode.get('programType')
        metadata = metadatacreator.MetadataCreator()
        metadata.mediatype = 'season'
        metadata.brands = episode.get('programBrands') or episode.get('brands')

        # Reverse sort seasons if program_type is 'reeksaflopend' or 'daily'
        if program_type in ('daily', 'reeksaflopend'):
            ascending = False

        # NOTE: Sort the episodes ourselves, because Kodi does not allow to set to 'ascending'
        seasons = sorted(seasons, key=lambda k: k['key'], reverse=not ascending)

        for season in seasons:
            season_key = season.get('key')
            label = '%s %s' % (self._kodi_wrapper.get_localized_string(30094), season_key)
            params = {'facets[seasonTitle]': season_key}
            path = api_url + '&' + urlencode(params)
            season_items.append(helperobjects.TitleItem(
                title=label,
                url_dict=dict(action=actions.LISTING_EPISODES, video_url=path),
                is_playable=False,
                art_dict=dict(thumb=fanart, icon='DefaultSets.png', fanart=fanart),
                video_dict=metadata.get_video_dict(),
            ))
        return season_items, sort, ascending

    def get_live_screenshot(self, channel):
        url = '%s/%s.jpg' % (self._VRTNU_SCREENSHOT_URL, channel)
        self.__delete_cached_thumbnail(url)
        return url

    def __delete_cached_thumbnail(self, url):
        crc = self.__get_crc32(url)
        ext = url.split('.')[-1]
        path = 'special://thumbnails/%s/%s.%s' % (crc[0], crc, ext)
        self._kodi_wrapper.delete_path(path)

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

        if titletype == 'recent':
            ascending = False
            sort = 'dateadded'
            label = '%s - %s' % (result.get('program'), label)

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
                label = '%s %s: %s' % (self._kodi_wrapper.get_localized_string(30095), result.get('episodeNumber'), label)
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
