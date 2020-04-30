# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Implements a class for video metadata"""

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.parse import quote_plus
except ImportError:  # Python 2
    from urllib import quote_plus

from data import CHANNELS, SECONDS_MARGIN
from kodiutils import colour, get_setting_bool, localize, localize_datelong, log, url_for
from utils import (add_https_proto, assetpath_to_id, capitalize, find_entry, from_unicode,
                   html_to_kodilabel, reformat_url, shorten_link, to_unicode, unescape,
                   url_to_episode)


class Metadata:
    """This class creates appropriate Kodi ListItem metadata from single item json api data"""

    def __init__(self, _favorites, _resumepoints):
        self._favorites = _favorites
        self._resumepoints = _resumepoints

    @staticmethod
    def get_studio(api_data):
        """Get studio string from single item json api data"""

        # VRT NU Search API or VRT NU Suggest API
        if api_data.get('type') == 'episode' or api_data.get('type') == 'program':
            brands = api_data.get('programBrands', []) or api_data.get('brands', [])
            if brands:
                try:
                    channel = next(c for c in CHANNELS if c.get('name') == brands[0])
                except StopIteration:
                    # Retain original (unknown) brand, unless it is empty
                    studio = brands[0] or 'VRT'
                else:
                    studio = channel.get('studio')
            else:
                # No brands ? Use VRT instead
                studio = 'VRT'
            return studio

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return ''

        # Not Found
        return ''

    def get_context_menu(self, api_data, program, cache_file):
        """Get context menu"""
        from addon import plugin
        favorite_marker = ''
        watchlater_marker = ''
        context_menu = []

        # WATCH LATER
        if self._resumepoints.is_activated():
            asset_id = self.get_asset_id(api_data)

            # VRT NU Search API
            if api_data.get('type') == 'episode':
                program_title = api_data.get('program')

            # VRT NU Schedule API (some are missing vrt.whatson-id)
            elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
                program_title = api_data.get('title')

            if asset_id is not None:
                # We need to ensure forward slashes are quoted
                program_title = to_unicode(quote_plus(from_unicode(program_title)))
                url = url_to_episode(api_data.get('url', ''))
                if self._resumepoints.is_watchlater(asset_id):
                    extras = {}
                    # If we are in a watchlater menu, move cursor down before removing a favorite
                    if plugin.path.startswith('/resumepoints/watchlater'):
                        extras = dict(move_down=True)
                    # Unwatch context menu
                    context_menu.append((
                        capitalize(localize(30402)),
                        'RunPlugin(%s)' % url_for('unwatchlater', asset_id=asset_id, title=program_title, url=url, **extras)
                    ))
                    watchlater_marker = '[COLOR={highlighted}]ᶫ[/COLOR]'
                else:
                    # Watch context menu
                    context_menu.append((
                        capitalize(localize(30401)),
                        'RunPlugin(%s)' % url_for('watchlater', asset_id=asset_id, title=program_title, url=url)
                    ))

        # FOLLOW PROGRAM
        if self._favorites.is_activated():

            # VRT NU Search API
            if api_data.get('type') == 'episode':
                program_title = api_data.get('program')
                program_type = api_data.get('programType')
                follow_suffix = localize(30410) if program_type != 'oneoff' else ''  # program
                follow_enabled = True

            # VRT NU Suggest API
            elif api_data.get('type') == 'program':
                program_title = api_data.get('title')
                follow_suffix = ''
                follow_enabled = True

            # VRT NU Schedule API (some are missing vrt.whatson-id)
            elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
                program_title = api_data.get('title')
                follow_suffix = localize(30410)  # program
                follow_enabled = bool(api_data.get('url'))

            if follow_enabled and program:
                program_title = to_unicode(quote_plus(from_unicode(program_title)))  # We need to ensure forward slashes are quoted
                if self._favorites.is_favorite(program):
                    extras = {}
                    # If we are in a favorites menu, move cursor down before removing a favorite
                    if plugin.path.startswith('/favorites'):
                        extras = dict(move_down=True)
                    context_menu.append((
                        localize(30412, title=follow_suffix),  # Unfollow
                        'RunPlugin(%s)' % url_for('unfollow', program=program, title=program_title, **extras)
                    ))
                    favorite_marker = '[COLOR={highlighted}]ᵛ[/COLOR]'
                else:
                    context_menu.append((
                        localize(30411, title=follow_suffix),  # Follow
                        'RunPlugin(%s)' % url_for('follow', program=program, title=program_title)
                    ))

        # GO TO PROGRAM
        if api_data.get('programType') != 'oneoff' and program:
            if plugin.path.startswith(('/favorites/offline', '/favorites/recent', '/offline', '/recent',
                                       '/resumepoints/continue', '/resumepoints/watchlater', '/tvguide')):
                context_menu.append((
                    localize(30417),  # Go to program
                    'Container.Update(%s)' % url_for('programs', program=program, season='allseasons')
                ))

        # REFRESH MENU
        context_menu.append((
            localize(30413),  # Refresh menu
            'RunPlugin(%s)' % url_for('delete_cache', cache_file=cache_file)
        ))

        return context_menu, colour(favorite_marker), colour(watchlater_marker)

    @staticmethod
    def get_asset_id(api_data):
        """Get asset_id from single item json api data"""
        asset_id = None

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            asset_id = assetpath_to_id(api_data.get('assetPath'))

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            asset_id = assetpath_to_id(api_data.get('assetPath'))

        # Fallback to VRT NU website scraping
        if not asset_id and api_data.get('url'):
            from webscraper import get_asset_id
            asset_id = get_asset_id(add_https_proto(api_data.get('url')))

        return asset_id

    def get_playcount(self, api_data):
        """Get playcount from single item json api data"""
        playcount = -1
        # Only fill in playcount when using VRT NU resumepoints because setting playcount breaks standard Kodi watched status
        if self._resumepoints.is_activated():
            asset_id = self.get_asset_id(api_data)
            if asset_id:
                position = self._resumepoints.get_position(asset_id)
                total = self._resumepoints.get_total(asset_id)
                if position and total and position > total - SECONDS_MARGIN:
                    playcount = 1
        return playcount

    def get_properties(self, api_data):
        """Get properties from single item json api data"""
        properties = {}

        # Only fill in properties when using VRT NU resumepoints because setting resumetime/totaltime breaks standard Kodi watched status
        if self._resumepoints.is_activated():
            asset_id = self.get_asset_id(api_data)
            if asset_id:
                # We need to ensure forward slashes are quoted
                program_title = to_unicode(quote_plus(from_unicode(api_data.get('program'))))

                url = reformat_url(api_data.get('url', ''), 'medium')
                properties.update(asset_id=asset_id, url=url, title=program_title)

                position = self._resumepoints.get_position(asset_id)
                total = self._resumepoints.get_total(asset_id)
                # Master over Kodi watch status
                if position and total and SECONDS_MARGIN < position < total - SECONDS_MARGIN:
                    properties['resumetime'] = position
                    properties['totaltime'] = total
                    log(2, '[Metadata] manual resumetime set to %d' % position)

            episode = self.get_episode(api_data)
            season = self.get_season(api_data)
            if episode and season:
                properties['episodeno'] = 's%se%s' % (season, episode)

            year = self.get_year(api_data)
            if year:
                properties['year'] = year

        return properties

    @staticmethod
    def get_tvshowtitle(api_data):
        """Get tvshowtitle string from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            return api_data.get('program', '???')

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return api_data.get('title', '???')

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return api_data.get('title', 'Untitled')

        # Not Found
        return ''

    @staticmethod
    def get_duration(api_data):
        """Get duration int from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            return api_data.get('duration', int()) * 60  # Minutes to seconds

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            from datetime import timedelta
            import dateutil.parser
            start_time = dateutil.parser.parse(api_data.get('startTime'))
            end_time = dateutil.parser.parse(api_data.get('endTime'))
            if end_time < start_time:
                end_time = end_time + timedelta(days=1)
            return (end_time - start_time).total_seconds()

        # Not Found
        return ''

    def get_plot(self, api_data, season=False, date=None):
        """Get plot string from single item json api data"""
        from datetime import datetime
        import dateutil.parser
        import dateutil.tz

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                plot = html_to_kodilabel(api_data.get('programDescription', ''))

                # Add additional metadata to plot
                plot_meta = ''
                if api_data.get('allowedRegion') == 'BE':
                    plot_meta += localize(30201) + '\n\n'  # Geo-blocked
                plot = '%s[B]%s[/B]\n%s' % (plot_meta, api_data.get('program'), plot)
                return colour(plot)

            # Add additional metadata to plot
            plot_meta = ''
            # Only display when a video disappears if it is within the next 3 months
            if api_data.get('assetOffTime'):
                offtime = dateutil.parser.parse(api_data.get('assetOffTime'))

                # Show the remaining days/hours the episode is still available
                if offtime:
                    now = datetime.now(dateutil.tz.tzlocal())
                    remaining = offtime - now
                    if remaining.days / 365 > 5:
                        pass  # If it is available for more than 5 years, do not show
                    elif remaining.days / 365 > 2:
                        plot_meta += localize(30202, years=int(remaining.days / 365))  # X years remaining
                    elif remaining.days / 30.5 > 3:
                        plot_meta += localize(30203, months=int(remaining.days / 30.5))  # X months remaining
                    elif remaining.days > 1:
                        plot_meta += localize(30204, days=remaining.days)  # X days to go
                    elif remaining.days == 1:
                        plot_meta += localize(30205)  # 1 day to go
                    elif remaining.seconds // 3600 > 1:
                        plot_meta += localize(30206, hours=remaining.seconds // 3600)  # X hours to go
                    elif remaining.seconds // 3600 == 1:
                        plot_meta += localize(30207)  # 1 hour to go
                    else:
                        plot_meta += localize(30208, minutes=remaining.seconds // 60)  # X minutes to go

            if api_data.get('allowedRegion') == 'BE':
                if plot_meta:
                    plot_meta += '  '
                plot_meta += localize(30201)  # Geo-blocked

            plot = html_to_kodilabel(api_data.get('description', ''))

            if plot_meta:
                plot = '%s\n\n%s' % (plot_meta, plot)

            permalink = shorten_link(api_data.get('permalink')) or api_data.get('externalPermalink')
            if permalink and get_setting_bool('showpermalink', default=False):
                plot = '%s\n\n[COLOR={highlighted}]%s[/COLOR]' % (plot, permalink)
            return colour(plot)

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            plot = unescape(api_data.get('description', '???'))
            # permalink = shorten_link(api_data.get('programUrl'))
            # if permalink and get_setting_bool('showpermalink', default=False):
            #     plot = '%s\n\n[COLOR={highlighted}]%s[/COLOR]' % (plot, permalink)
            return colour(plot)

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            now = datetime.now(dateutil.tz.tzlocal())
            epg = self.parse(date, now)
            plot = '[B]{datelong}[/B]\n{start} - {end}\n\n{description}'.format(
                datelong=localize_datelong(epg),
                start=api_data.get('start'),
                end=api_data.get('end'),
                description=html_to_kodilabel(api_data.get('description', '')),
            )
            return colour(plot)

        # Not Found
        return ''

    @staticmethod
    def get_plotoutline(api_data, season=False):
        """Get plotoutline string from single item json api data"""
        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                plotoutline = html_to_kodilabel(api_data.get('programDescription', ''))
                return plotoutline

            if api_data.get('displayOptions', {}).get('showShortDescription'):
                plotoutline = html_to_kodilabel(api_data.get('shortDescription', ''))
                return plotoutline

            plotoutline = api_data.get('subtitle')
            return plotoutline

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return html_to_kodilabel(api_data.get('shortDescription', '') or api_data.get('subtitle', ''))

        # Not Found
        return ''

    def get_season(self, api_data):
        """Get season int from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            # If this is a oneoff video and the season is a year, don't return a season
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return ''
            try:
                season = int(api_data.get('seasonTitle'))
            except ValueError:
                try:
                    season = int(api_data.get('seasonName'))
                except ValueError:
                    season = api_data.get('seasonTitle')
            return season

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return None

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return None

        # Not Found
        return None

    def get_episode(self, api_data):
        """Get episode int from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            # If this is a oneoff video and the season is a year, don't return an episode
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return ''
            try:
                episode = int(api_data.get('episodeNumber'))
            except ValueError:
                episode = int()
            return episode

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return int()

        # Not Found
        return int()

    @staticmethod
    def get_date(api_data):
        """Get date string from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            import dateutil.parser
            return dateutil.parser.parse(api_data.get('assetOnTime')).strftime('%d.%m.%Y')

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return ''

        # Not Found
        return ''

    def get_aired(self, api_data):
        """Get aired string from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            # FIXME: Due to a bug in Kodi, ListItem.Year, as shown in Info pane, is based on 'aired' when set
            # If this is a oneoff (e.g. movie) and we get a year of release, do not set 'aired'
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return ''
            aired = ''
            if api_data.get('broadcastDate'):
                from datetime import datetime
                import dateutil.tz
                aired = datetime.fromtimestamp(api_data.get('broadcastDate', 0) / 1000, dateutil.tz.UTC).strftime('%Y-%m-%d')
            return aired

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            aired = dateutil.parser.parse(api_data.get('startTime')).astimezone(dateutil.tz.UTC).strftime('%Y-%m-%d')
            return aired

        # Not Found
        return ''

    @staticmethod
    def get_dateadded(api_data):
        """Get dateadded string from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            import dateutil.parser
            return dateutil.parser.parse(api_data.get('assetOnTime')).strftime('%Y-%m-%d %H:%M:%S')

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return ''

        # Not Found
        return ''

    @staticmethod
    def get_year(api_data):
        """Get year integer from single item json api data"""
        from datetime import datetime

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            # Add proper year information when season falls in range
            # NOTE: Estuary skin is using premiered/aired year, which is incorrect
            try:
                if int(api_data.get('seasonTitle')) in range(1900, datetime.now().year + 1):
                    return int(api_data.get('seasonTitle'))
            except ValueError:
                pass
            return int()

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return int()

        # Not Found
        return ''

    def get_mediatype(self, api_data, season=False):
        """Get art dict from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                return 'season'

            # If this is a oneoff (e.g. movie) and we get a year of release, do not set 'aired'
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return 'movie'

            return 'episode'

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''  # NOTE: We do not use 'tvshow' as it won't show as a folder

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return 'episode'

        return ''

    @staticmethod
    def get_art(api_data, season=False):
        """Get art dict from single item json api data"""
        art_dict = {}

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                if get_setting_bool('showfanart', default=True):
                    art_dict['fanart'] = add_https_proto(api_data.get('programImageUrl', 'DefaultSets.png'))
                    art_dict['banner'] = art_dict.get('fanart')
                    if season != 'allseasons':
                        art_dict['thumb'] = add_https_proto(api_data.get('videoThumbnailUrl', art_dict.get('fanart')))
                    else:
                        art_dict['thumb'] = art_dict.get('fanart')
                else:
                    art_dict['thumb'] = 'DefaultSets.png'
            else:
                if get_setting_bool('showfanart', default=True):
                    art_dict['thumb'] = add_https_proto(api_data.get('videoThumbnailUrl', 'DefaultAddonVideo.png'))
                    art_dict['fanart'] = add_https_proto(api_data.get('programImageUrl', art_dict.get('thumb')))
                    art_dict['banner'] = art_dict.get('fanart')
                else:
                    art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            if get_setting_bool('showfanart', default=True):
                art_dict['thumb'] = add_https_proto(api_data.get('thumbnail', 'DefaultAddonVideo.png'))
                art_dict['fanart'] = art_dict.get('thumb')
                art_dict['banner'] = art_dict.get('fanart')
            else:
                art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            if get_setting_bool('showfanart', default=True):
                art_dict['thumb'] = add_https_proto(api_data.get('image', 'DefaultAddonVideo.png'))
                art_dict['fanart'] = art_dict.get('thumb')
                art_dict['banner'] = art_dict.get('fanart')
            else:
                art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # Not Found
        return art_dict

    def get_info_labels(self, api_data, season=False, date=None, channel=None):
        """Get infoLabels dict from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            info_labels = dict(
                title=self.get_title(api_data),
                # sorttitle=self.get_title(api_data),  # NOTE: Does not appear to work
                tvshowtitle=self.get_tvshowtitle(api_data),
                # date=self.get_date(api_data),  # NOTE: Not sure when or how this is used
                aired=self.get_aired(api_data),
                dateadded=self.get_dateadded(api_data),
                episode=self.get_episode(api_data),
                season=self.get_season(api_data),
                playcount=self.get_playcount(api_data),
                plot=self.get_plot(api_data, season=season),
                plotoutline=self.get_plotoutline(api_data, season=season),
                tagline=self.get_plotoutline(api_data, season=season),
                duration=self.get_duration(api_data),
                mediatype=self.get_mediatype(api_data, season=season),
                studio=self.get_studio(api_data),
                year=self.get_year(api_data),
                tag=self.get_tag(api_data),
            )
            return info_labels

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            info_labels = dict(
                tvshowtitle=self.get_tvshowtitle(api_data),
                plot=self.get_plot(api_data),
                mediatype=self.get_mediatype(api_data, season=season),
                studio=self.get_studio(api_data),
                tag=self.get_tag(api_data),
            )
            return info_labels

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            info_labels = dict(
                title=self.get_title(api_data),
                # sorttitle=self.get_title(api_data),  # NOTE: Does not appear to work
                tvshowtitle=self.get_tvshowtitle(api_data),
                aired=self.get_aired(api_data),
                plot=self.get_plot(api_data, date=date),
                duration=self.get_duration(api_data),
                mediatype=self.get_mediatype(api_data, season=season),
                studio=channel.get('studio'),
            )
            return info_labels

        # Not Found
        return {}

    @staticmethod
    def get_title(api_data):
        """Get an appropriate video title"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            title = api_data.get('title') or api_data.get('shortDescription', '???')

        # VRT NU Suggest API
        elif api_data.get('type') == 'program':
            title = api_data.get('title', '???')

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            title = api_data.get('subtitle', '???')

        return title

    @staticmethod
    def get_label(api_data, titletype=None, return_sort=False):
        """Get an appropriate label string matching the type of listing and VRT NU provided displayOptions from single item json api data"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            display_options = api_data.get('displayOptions', {})

            # NOTE: Hard-code showing seasons because it is unreliable (i.e; Thuis or Down the Road have it disabled)
            display_options['showSeason'] = True

            program_type = api_data.get('programType')
            if not titletype:
                titletype = program_type

            if display_options.get('showEpisodeTitle'):
                label = html_to_kodilabel(api_data.get('title', '') or api_data.get('shortDescription', ''))
            elif display_options.get('showShortDescription'):
                label = html_to_kodilabel(api_data.get('shortDescription', '') or api_data.get('title', ''))
            else:
                label = html_to_kodilabel(api_data.get('title', '') or api_data.get('shortDescription', ''))

            sort = 'unsorted'
            ascending = True

            if titletype in ('continue', 'offline', 'recent', 'watchlater'):
                ascending = False
                label = '[B]%s[/B] - %s' % (api_data.get('program'), label)
                sort = 'dateadded'

            elif titletype in ('reeksaflopend', 'reeksoplopend'):

                if titletype == 'reeksaflopend':
                    ascending = False

                # NOTE: This is disable on purpose as 'showSeason' is not reliable
                if (display_options.get('showSeason') is False and display_options.get('showEpisodeNumber')
                        and api_data.get('seasonName') and api_data.get('episodeNumber')):
                    try:
                        label = 'S%02dE%02d: %s' % (int(api_data.get('seasonName')), int(api_data.get('episodeNumber')), label)
                    except ValueError:
                        # Season may not always be a perfect number
                        sort = 'episode'
                    else:
                        sort = 'dateadded'
                elif display_options.get('showEpisodeNumber') and api_data.get('episodeNumber') and ascending:
                    # NOTE: Do not prefix with "Episode X" when sorting by episode
                    # label = '%s %s: %s' % (localize(30132), api_data.get('episodeNumber'), label)
                    sort = 'episode'
                elif display_options.get('showBroadcastDate') and api_data.get('formattedBroadcastShortDate'):
                    label = '%s - %s' % (api_data.get('formattedBroadcastShortDate'), label)
                    sort = 'dateadded'
                else:
                    sort = 'dateadded'

            elif titletype == 'daily':
                ascending = False
                label = '%s - %s' % (api_data.get('formattedBroadcastShortDate'), label)
                sort = 'dateadded'

            elif titletype == 'oneoff':
                label = api_data.get('program', label)
                sort = 'label'

        # VRT NU Suggest API
        elif api_data.get('type') == 'program':
            label = api_data.get('title', '???')

        # VRT NU Schedule API (some are missing vrt.whatson-id)
        elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            title = html_to_kodilabel(api_data.get('subtitle', '') or api_data.get('shortDescription', ''))
            label = '{start} - [B]{program}[/B]{title}'.format(
                start=api_data.get('start'),
                program=api_data.get('title'),
                title=' - ' + title if title else '',
            )
            now = datetime.now(dateutil.tz.tzlocal())
            start_date = dateutil.parser.parse(api_data.get('startTime'))
            end_date = dateutil.parser.parse(api_data.get('endTime'))
            if api_data.get('url'):
                if start_date <= now <= end_date:  # Now playing
                    label = '[COLOR={highlighted}]%s[/COLOR] %s' % (label, localize(30301))
            else:
                # This is a non-actionable item
                if start_date < now <= end_date:  # Now playing
                    label = '[COLOR={greyedout}]%s[/COLOR] %s' % (label, localize(30301))
                else:
                    label = '[COLOR={greyedout}]%s[/COLOR]' % label

        # Not Found
        else:
            label = ''

        if return_sort:
            return colour(label), sort, ascending

        return colour(label)

    @staticmethod
    def get_tag(api_data):
        """Return categories for a given episode"""

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            from data import CATEGORIES
            return sorted([localize(find_entry(CATEGORIES, 'id', category).get('msgctxt'))
                           for category in api_data.get('categories')])

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ['Series']

        return []

    @staticmethod
    def parse(date, now):
        """Parse a given string and return a datetime object
            This supports 'today', 'yesterday' and 'tomorrow'
            It also compensates for TV-guides covering from 6AM to 6AM
       """
        from datetime import timedelta
        import dateutil.parser

        if date == 'today':
            if now.hour < 6:
                return now + timedelta(days=-1)
            return now
        if date == 'yesterday':
            if now.hour < 6:
                return now + timedelta(days=-2)
            return now + timedelta(days=-1)
        if date == 'tomorrow':
            if now.hour < 6:
                return now
            return now + timedelta(days=1)
        return dateutil.parser.parse(date)
