# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Implements a class for video metadata '''

from __future__ import absolute_import, division, unicode_literals

try:  # Python 3
    from urllib.parse import quote_plus
except ImportError:  # Python 2
    from urllib import quote_plus

import statichelper
from data import CHANNELS


class Metadata:
    ''' This class creates appropriate Kodi ListItem metadata from single item json api data '''

    def __init__(self, _kodi, _favorites):
        self._kodi = _kodi
        self._favorites = _favorites
        self._showfanart = _kodi.get_setting('showfanart', 'true') == 'true'
        self._showpermalink = _kodi.get_setting('showpermalink', 'false') == 'true'

    @staticmethod
    def get_studio(api_data):
        ''' Get studio string from single item json api data '''

        # VRT NU Search API or VRT NU Suggest API
        if api_data.get('type') == 'episode' or api_data.get('type') == 'program':
            brands = api_data.get('programBrands', []) or api_data.get('brands', [])
            if brands:
                try:
                    channel = next(c for c in CHANNELS if c.get('name') == brands[0])
                    studio = channel.get('studio')
                except StopIteration:
                    # Retain original (unknown) brand, unless it is empty
                    studio = brands[0] or 'VRT'
            else:
                # No brands ? Use VRT instead
                studio = 'VRT'
            return studio

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return ''

        # Not Found
        return ''

    def get_context_menu(self, api_data, program, cache_file):
        ''' Get context menu '''
        from addon import plugin
        favorite_marker = ''
        context_menu = []
        if self._favorites.is_activated():

            # VRT NU Search API
            if api_data.get('type') == 'episode':
                program_title = api_data.get('program')
                program_type = api_data.get('programType')
                follow_suffix = self._kodi.localize(30410) if program_type != 'oneoff' else ''
                follow_enabled = True

            # VRT NU Suggest API
            elif api_data.get('type') == 'program':
                program_title = api_data.get('title')
                follow_suffix = ''
                follow_enabled = True

            # VRT NU Schedule API
            elif api_data.get('vrt.whatson-id'):
                program_title = api_data.get('title')
                follow_suffix = self._kodi.localize(30410)
                follow_enabled = bool(api_data.get('url'))

            if follow_enabled:
                program_title = statichelper.to_unicode(quote_plus(statichelper.from_unicode(program_title)))  # We need to ensure forward slashes are quoted
                if self._favorites.is_favorite(program):
                    extras = dict()
                    # If we are in a favorites menu, move cursor down before removing a favorite
                    if plugin.path.startswith('/favorites'):
                        extras = dict(move_down=True)
                    # Unfollow context menu
                    context_menu.append((
                        self._kodi.localize(30412, title=follow_suffix),
                        'RunPlugin(%s)' % self._kodi.url_for('unfollow', program=program, title=program_title, **extras)
                    ))
                    favorite_marker = '[COLOR yellow]ᵛ[/COLOR]'
                else:
                    # Follow context menu
                    context_menu.append((
                        self._kodi.localize(30411, title=follow_suffix),
                        'RunPlugin(%s)' % self._kodi.url_for('follow', program=program, title=program_title)
                    ))

        # Go to program context menu
        if plugin.path.startswith(('/favorites/offline', '/favorites/recent', '/offline', '/recent')):
            plugin_url = self._kodi.url_for('programs', program=program, season='allseasons')
            # FIXME: Because of a bug in ActivateWindow(), return does not work
            # context_menu.append((self._kodi.localize(30417), 'ActivateWindow(Videos,%s,return)' % plugin_url))
            context_menu.append((self._kodi.localize(30417), 'ActivateWindow(Videos,%s)' % plugin_url))

        # Refresh context menu
        context_menu.append((self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file=cache_file)))

        return context_menu, favorite_marker

    def get_properties(self, api_data):
        ''' Get properties from single item json api data '''
        properties = dict()

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            episode = self.get_episode(api_data)
            season = self.get_season(api_data)
            if episode and season:
                properties['episodeno'] = 's%se%s' % (season, episode)

            duration = self.get_duration(api_data)
            if duration:
                properties['totaltime'] = duration

            year = self.get_year(api_data)
            if year:
                properties['year'] = year

        return properties

    @staticmethod
    def get_tvshowtitle(api_data):
        ''' Get tvshowtitle string from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            return api_data.get('program', '???')

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return api_data.get('title', '???')

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return api_data.get('title', 'Untitled')

        # Not Found
        return ''

    @staticmethod
    def get_duration(api_data):
        ''' Get duration int from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            return api_data.get('duration', int()) * 60  # Minutes to seconds

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            from datetime import timedelta
            import dateutil.parser
            start_time = dateutil.parser.parse(api_data.get('startTime'))
            end_time = dateutil.parser.parse(api_data.get('endTime'))
            if end_time < start_time:
                end_time = end_time + timedelta(days=1)
            return (end_time - start_time).total_seconds()

        # Not Found
        return ''

    def get_plot(self, api_data, season=False, date=None, channel=None):
        ''' Get plot string from single item json api data '''
        from datetime import datetime
        import dateutil.parser
        import dateutil.tz

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                plot = statichelper.convert_html_to_kodilabel(api_data.get('programDescription'))

                # Add additional metadata to plot
                plot_meta = ''
                if api_data.get('allowedRegion') == 'BE':
                    # Show Geo-blocked
                    plot_meta += self._kodi.localize(30201) + '\n'
                plot = '%s[B]%s[/B]\n%s' % (plot_meta, api_data.get('program'), plot)
                return plot

            plot = statichelper.convert_html_to_kodilabel(api_data.get('description'))
            now = datetime.now(dateutil.tz.tzlocal())

            # Add additional metadata to plot
            plot_meta = ''
            # Only display when a video disappears if it is within the next 3 months
            if api_data.get('assetOffTime'):
                offtime = dateutil.parser.parse(api_data.get('assetOffTime'))

                # Show the remaining days/hours the episode is still available
                if offtime:
                    remaining = offtime - now
                    if remaining.days / 365 > 5:
                        pass  # If it is available for more than 5 years, do not show
                    elif remaining.days / 365 > 2:
                        plot_meta += self._kodi.localize(30202, years=int(remaining.days / 365))  # X years remaining
                    elif remaining.days / 30.5 > 3:
                        plot_meta += self._kodi.localize(30203, months=int(remaining.days / 30.5))  # X months remaining
                    elif remaining.days > 1:
                        plot_meta += self._kodi.localize(30204, days=remaining.days)  # X days to go
                    elif remaining.days == 1:
                        plot_meta += self._kodi.localize(30205)  # 1 day to go
                    elif int(remaining.seconds / 3600) > 1:
                        plot_meta += self._kodi.localize(30206, hours=int(remaining.seconds / 3600))  # X hours to go
                    elif int(remaining.seconds / 3600) == 1:
                        plot_meta += self._kodi.localize(30207)  # 1 hour to go

            if api_data.get('allowedRegion') == 'BE':
                # Show Geo-blocked
                plot_meta += self._kodi.localize(30201)

            plot = '%s\n%s' % (plot_meta, plot)

            permalink = statichelper.shorten_link(api_data.get('permalink')) or api_data.get('externalPermalink')
            if self._showpermalink and permalink:
                plot = '%s\n\n[COLOR yellow]%s[/COLOR]' % (plot, permalink)
            return plot

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            plot = statichelper.unescape(api_data.get('description', '???'))
            permalink = statichelper.shorten_link(api_data.get('targetUrl'))
            if self._showpermalink and permalink:
                plot = '%s\n\n[COLOR yellow]%s[/COLOR]' % (plot, permalink)
            return plot

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            title = '%s - %s' % (api_data.get('start'), api_data.get('title'))
            now = datetime.now(dateutil.tz.tzlocal())
            epg = self.parse(date, now)
            datelong = self._kodi.localize_datelong(epg)
            start = api_data.get('start')
            end = api_data.get('end')
            plot = '[B]%s[/B]\n%s\n%s - %s\n[I]%s[/I]' % (title, datelong, start, end, channel.get('label'))
            return plot

        # Not Found
        return ''

    @staticmethod
    def get_plotoutline(api_data, season=False):
        ''' Get plotoutline string from single item json api data '''
        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                plotoutline = statichelper.convert_html_to_kodilabel(api_data.get('programDescription'))
                return plotoutline

            if api_data.get('displayOptions', dict()).get('showShortDescription'):
                plotoutline = statichelper.convert_html_to_kodilabel(api_data.get('shortDescription'))
                return plotoutline

            plotoutline = api_data.get('subtitle')
            return plotoutline

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return ''

        # Not Found
        return ''

    @staticmethod
    def get_season(api_data):
        ''' Get season int from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            try:
                season = int(api_data.get('seasonTitle'))
            except ValueError:
                try:
                    season = int(api_data.get('seasonName'))
                except ValueError:
                    season = None
            return season

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return None

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return None

        # Not Found
        return None

    @staticmethod
    def get_episode(api_data):
        ''' Get episode int from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            try:
                episode = int(api_data.get('episodeNumber'))
            except ValueError:
                episode = int()
            return episode

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return int()

        # Not Found
        return int()

    @staticmethod
    def get_date(api_data):
        ''' Get date string from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            import dateutil.parser
            return dateutil.parser.parse(api_data.get('assetOnTime')).strftime('%d.%m.%Y')

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return ''

        # Not Found
        return ''

    @staticmethod
    def get_aired(api_data):
        ''' Get aired string from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            from datetime import datetime
            import dateutil.tz
            aired = ''
            if api_data.get('broadcastDate'):
                aired = datetime.fromtimestamp(api_data.get('broadcastDate', 0) / 1000, dateutil.tz.UTC).strftime('%Y-%m-%d')
            return aired

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            aired = dateutil.parser.parse(api_data.get('startTime')).astimezone(dateutil.tz.UTC).strftime('%Y-%m-%d')
            return aired

        # Not Found
        return ''

    @staticmethod
    def get_dateadded(api_data):
        ''' Get dateadded string from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            import dateutil.parser
            return dateutil.parser.parse(api_data.get('assetOnTime')).strftime('%Y-%m-%d %H:%M:%S')

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return ''

        # Not Found
        return ''

    @staticmethod
    def get_year(api_data):
        ''' Get year integer from single item json api data '''
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

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            return int()

        # Not Found
        return ''

    def get_art(self, api_data, season=False):
        ''' Get art dict from single item json api data '''
        art_dict = dict()

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            if season:
                if self._showfanart:
                    art_dict['fanart'] = statichelper.add_https_method(api_data.get('programImageUrl', 'DefaultSets.png'))
                    art_dict['banner'] = art_dict.get('fanart')
                    if season != 'allseasons':
                        art_dict['thumb'] = statichelper.add_https_method(api_data.get('videoThumbnailUrl', art_dict.get('fanart')))
                    else:
                        art_dict['thumb'] = art_dict.get('fanart')
                else:
                    art_dict['thumb'] = 'DefaultSets.png'
            else:
                if self._showfanart:
                    art_dict['thumb'] = statichelper.add_https_method(api_data.get('videoThumbnailUrl', 'DefaultAddonVideo.png'))
                    art_dict['fanart'] = statichelper.add_https_method(api_data.get('programImageUrl', art_dict.get('thumb')))
                    art_dict['banner'] = art_dict.get('fanart')
                else:
                    art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            if self._showfanart:
                art_dict['thumb'] = statichelper.add_https_method(api_data.get('thumbnail', 'DefaultAddonVideo.png'))
                art_dict['fanart'] = art_dict.get('thumb')
                art_dict['banner'] = art_dict.get('fanart')
            else:
                art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            if self._showfanart:
                art_dict['thumb'] = api_data.get('image', 'DefaultAddonVideo.png')
                art_dict['fanart'] = art_dict.get('thumb')
                art_dict['banner'] = art_dict.get('fanart')
            else:
                art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # Not Found
        return art_dict

    def get_info_labels(self, api_data, season=False, date=None, channel=None):
        ''' Get infoLabels dict from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            titletype = api_data.get('programType')
            episode_label = self.get_label(api_data, titletype)
            info_labels = dict(
                title=episode_label,
                tvshowtitle=self.get_tvshowtitle(api_data),
                date=self.get_date(api_data),
                aired=self.get_aired(api_data),
                dateadded=self.get_dateadded(api_data),
                episode=self.get_episode(api_data),
                season=self.get_season(api_data),
                plot=self.get_plot(api_data, season=season),
                plotoutline=self.get_plotoutline(api_data, season=season),
                tagline=self.get_plotoutline(api_data, season=season),
                duration=self.get_duration(api_data),
                mediatype=api_data.get('type', 'episode'),
                studio=self.get_studio(api_data),
                year=self.get_year(api_data)
            )
            return info_labels

        # VRT NU Suggest API
        if api_data.get('type') == 'program':
            info_labels = dict(
                tvshowtitle=self.get_tvshowtitle(api_data),
                plot=self.get_plot(api_data),
                studio=self.get_studio(api_data)
            )
            return info_labels

        # VRT NU Schedule API
        if api_data.get('vrt.whatson-id'):
            info_labels = dict(
                title=self.get_label(api_data),
                tvshowtitle=self.get_tvshowtitle(api_data),
                aired=self.get_aired(api_data),
                plot=self.get_plot(api_data, date=date, channel=channel),
                duration=self.get_duration(api_data),
                mediatype=api_data.get('type', 'episode'),
                studio=channel.get('studio')
            )
            return info_labels

        # Not Found
        return dict()

    def get_label(self, api_data, titletype=None, return_sort=False):
        ''' Get an appropriate label string matching the type of listing and VRT NU provided displayOptions from single item json api data '''

        # VRT NU Search API
        if api_data.get('type') == 'episode':
            display_options = api_data.get('displayOptions', dict())

            # NOTE: Hard-code showing seasons because it is unreliable (i.e; Thuis or Down the Road have it disabled)
            display_options['showSeason'] = True

            program_type = api_data.get('programType')
            if not titletype:
                titletype = program_type

            if display_options.get('showEpisodeTitle'):
                label = statichelper.convert_html_to_kodilabel(api_data.get('title') or api_data.get('shortDescription'))
            elif display_options.get('showShortDescription'):
                label = statichelper.convert_html_to_kodilabel(api_data.get('shortDescription') or api_data.get('title'))
            else:
                label = statichelper.convert_html_to_kodilabel(api_data.get('title') or api_data.get('shortDescription'))

            sort = 'unsorted'
            ascending = True

            if titletype in ('offline', 'recent'):
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
                        sort = 'dateadded'
                    except Exception:  # pylint: disable=broad-except
                        # Season may not always be a perfect number
                        sort = 'episode'
                elif display_options.get('showEpisodeNumber') and api_data.get('episodeNumber') and ascending:
                    # NOTE: Do not prefix with "Episode X" when sorting by episode
                    # label = '%s %s: %s' % (self._kodi.localize(30095), api_data.get('episodeNumber'), label)
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

        # VRT NU Schedule API
        elif api_data.get('vrt.whatson-id'):
            from datetime import datetime
            import dateutil.parser
            import dateutil.tz
            label = '%s - %s' % (api_data.get('start'), api_data.get('title'))
            now = datetime.now(dateutil.tz.tzlocal())
            start_date = dateutil.parser.parse(api_data.get('startTime'))
            end_date = dateutil.parser.parse(api_data.get('endTime'))
            if api_data.get('url'):
                if start_date <= now <= end_date:  # Now playing
                    label = '[COLOR yellow]%s[/COLOR] %s' % (label, self._kodi.localize(30301))
            else:
                # This is a non-actionable item
                if start_date < now <= end_date:  # Now playing
                    label = '[COLOR gray]%s[/COLOR] %s' % (label, self._kodi.localize(30301))
                else:
                    label = '[COLOR gray]%s[/COLOR]' % label

        # Not Found
        else:
            label = ''

        if return_sort:
            return label, sort, ascending

        return label

    @staticmethod
    def parse(date, now):
        ''' Parse a given string and return a datetime object
            This supports 'today', 'yesterday' and 'tomorrow'
            It also compensates for TV-guides covering from 6AM to 6AM
        '''
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
