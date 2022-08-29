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
from utils import (capitalize, find_entry, from_unicode, html_to_kodi, reformat_url,
                   reformat_image_url, shorten_link, to_unicode, unescape)


class Metadata:
    """This class creates appropriate Kodi ListItem metadata from single item json api data"""

    def __init__(self, _favorites, _resumepoints):
        self._favorites = _favorites
        self._resumepoints = _resumepoints

    @staticmethod
    def get_studio(api_data):
        """Get studio string from single item json api data"""

        # VRT MAX Search API or VRT MAX Suggest API
        if api_data.get('episodeType') or api_data.get('type') == 'program':
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

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return ''

        # Not Found
        return ''

    def get_context_menu(self, api_data, program_name, cache_file):
        """Get context menu"""
        from addon import plugin
        favorite_marker = ''
        watchlater_marker = ''
        context_menu = []

        # WATCH LATER
        if self._resumepoints.is_activated():
            episode_id = api_data.get('episodeId')

            # VRT MAX Search API
            if api_data.get('episodeType'):
                title = api_data.get('title')

            # VRT MAX Schedule API (some are missing vrt.whatson-id)
            elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
                title = api_data.get('title')

            if episode_id is not None:
                # We need to ensure forward slashes are quoted
                title = to_unicode(quote_plus(from_unicode(title)))
                if self._resumepoints.is_watchlater(episode_id):
                    extras = {}
                    # If we are in a watchlater menu, move cursor down before removing a favorite
                    if plugin.path.startswith('/resumepoints/watchlater'):
                        extras = dict(move_down=True)
                    # Unwatch context menu
                    context_menu.append((
                        capitalize(localize(30402)),
                        'RunPlugin(%s)' % url_for('unwatchlater', episode_id=episode_id, title=title, **extras)
                    ))
                    watchlater_marker = '[COLOR={highlighted}]ᶫ[/COLOR]'
                else:
                    # Watch context menu
                    context_menu.append((
                        capitalize(localize(30401)),
                        'RunPlugin(%s)' % url_for('watchlater', episode_id=episode_id, title=title)
                    ))

        # FOLLOW PROGRAM
        if self._favorites.is_activated():

            # VRT MAX Search API
            if api_data.get('episodeType'):
                program_id = api_data.get('programId')
                program_title = api_data.get('programTitle')
                program_type = api_data.get('programType')
                follow_suffix = localize(30410) if program_type != 'oneoff' else ''  # program
                follow_enabled = True

            # VRT MAX Suggest API
            elif api_data.get('type') == 'program':
                # FIXME: No program_id in Suggest API
                program_id = None
                program_title = api_data.get('title')
                follow_suffix = ''
                follow_enabled = True

            # VRT MAX Schedule API (some are missing vrt.whatson-id)
            elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
                program_id = api_data.get('programId')
                program_title = api_data.get('title')
                follow_suffix = localize(30410)  # program
                follow_enabled = bool(api_data.get('url'))

            if follow_enabled and program_name:
                program_title = to_unicode(quote_plus(from_unicode(program_title)))  # We need to ensure forward slashes are quoted
                if self._favorites.is_favorite(program_name):
                    extras = {}
                    # If we are in a favorites menu, move cursor down before removing a favorite
                    if plugin.path.startswith('/favorites'):
                        extras = dict(move_down=True)
                    context_menu.append((
                        localize(30412, title=follow_suffix),  # Unfollow
                        'RunPlugin(%s)' % url_for('unfollow', program_name=program_name, title=program_title, program_id=program_id, **extras)
                    ))
                    favorite_marker = '[COLOR={highlighted}]ᵛ[/COLOR]'
                else:
                    context_menu.append((
                        localize(30411, title=follow_suffix),  # Follow
                        'RunPlugin(%s)' % url_for('follow', program_name=program_name, title=program_title, program_id=program_id)
                    ))

        # GO TO PROGRAM
        if api_data.get('programType') != 'oneoff' and program_name:
            if plugin.path.startswith(('/favorites/offline', '/favorites/recent', '/offline', '/recent',
                                       '/resumepoints/continue', '/resumepoints/watchlater', '/tvguide')):
                context_menu.append((
                    localize(30417),  # Go to program
                    'Container.Update(%s)' % url_for('programs', program_name=program_name, season='allseasons')
                ))

        # REFRESH MENU
        context_menu.append((
            localize(30413),  # Refresh menu
            'RunPlugin(%s)' % url_for('delete_cache', cache_file=cache_file)
        ))

        return context_menu, colour(favorite_marker), colour(watchlater_marker)

    @staticmethod
    def get_asset_str(api_data):
        """Get asset_str from single item json api data"""
        asset_str = None

        # VRT MAX Search API
        if api_data.get('episodeType'):
            asset_str = '{program} - {season} - {title}'.format(
                program=api_data.get('programTitle'),
                season=api_data.get('seasonTitle'),
                title=api_data.get('title')
            ).lower()
        return asset_str

    @staticmethod
    def get_video_id(api_data):
        """Get video_id from single item json api data"""
        video_id = None

        # VRT MAX Search API
        if api_data.get('episodeType'):
            video_id = api_data.get('videoId')

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            video_id = api_data.get('videoId')

        return video_id

    def get_playcount(self, api_data):
        """Get playcount from single item json api data"""
        playcount = -1
        # Only fill in playcount when using VRT MAX resumepoints because setting playcount breaks standard Kodi watched status
        if self._resumepoints.is_activated():
            video_id = self.get_video_id(api_data)
            if video_id:
                position = self._resumepoints.get_position(video_id)
                total = self._resumepoints.get_total(video_id)
                if position and total and position > total - SECONDS_MARGIN:
                    playcount = 1
        return playcount

    def get_properties(self, api_data):
        """Get properties from single item json api data"""
        properties = {}

        # Only fill in properties when using VRT MAX resumepoints because setting resumetime/totaltime breaks standard Kodi watched status
        if self._resumepoints.is_activated():
            video_id = self.get_video_id(api_data)
            if video_id:
                # We need to ensure forward slashes are quoted
                program_title = to_unicode(quote_plus(from_unicode(api_data.get('programTitle'))))

                url = reformat_url(api_data.get('url', ''), 'medium')
                properties.update(video_id=video_id, url=url, title=program_title)

                position = self._resumepoints.get_position(video_id)
                total = self._resumepoints.get_total(video_id)
                # Master over Kodi watch status
                if position and total and SECONDS_MARGIN < position < total - SECONDS_MARGIN:
                    properties['resumetime'] = position
                    properties['totaltime'] = total
                    log(2, '[Metadata] manual resumetime set to {position}', position=position)

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

        # VRT MAX Search API
        if api_data.get('episodeType'):
            return api_data.get('programTitle', '???')

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return api_data.get('title', '???')

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return api_data.get('title', 'Untitled')

        # Not Found
        return ''

    @staticmethod
    def get_mpaa(api_data):
        """Get film rating string from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            if api_data.get('ageGroup'):
                return api_data.get('ageGroup')

        # Not Found
        return ''

    @staticmethod
    def get_duration(api_data):
        """Get duration int from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            return api_data.get('duration', int()) * 60  # Minutes to seconds

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
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

        # VRT MAX Search API
        if api_data.get('episodeType'):
            if season is not False:
                plot = html_to_kodi(api_data.get('programShortDescription', ''))

                # Add additional metadata to plot
                plot_meta = ''
                if api_data.get('allowedRegion') == 'BE':
                    plot_meta += localize(30201) + '\n\n'  # Geo-blocked
                plot = '%s[B]%s[/B]\n%s' % (plot_meta, api_data.get('programTitle'), plot)
                return colour(plot)

            # Add additional metadata to plot
            plot_meta = ''
            # Only display when a video disappears if it is within the next 3 months
            if api_data.get('offTime'):
                offtime = dateutil.parser.parse(api_data.get('offTime'))

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

            # Add product placement
            if api_data.get('productPlacement') is True:
                if plot_meta:
                    plot_meta += '  '
                plot_meta += '[B]PP[/B]'

            # Add film rating
            rating = self.get_mpaa(api_data)
            if rating:
                if plot_meta:
                    plot_meta += '  '
                plot_meta += '[B]%s[/B]' % rating

            plot = html_to_kodi(api_data.get('description', ''))

            if plot_meta:
                plot = '%s\n\n%s' % (plot_meta, plot)

            permalink = shorten_link(api_data.get('permalink')) or api_data.get('externalPermalink')
            if permalink and get_setting_bool('showpermalink', default=False):
                plot = '%s\n\n[COLOR={highlighted}]%s[/COLOR]' % (plot, permalink)
            return colour(plot)

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            plot = unescape(api_data.get('description', '???'))
            # permalink = shorten_link(api_data.get('programUrl'))
            # if permalink and get_setting_bool('showpermalink', default=False):
            #     plot = '%s\n\n[COLOR={highlighted}]%s[/COLOR]' % (plot, permalink)
            return colour(plot)

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            now = datetime.now(dateutil.tz.tzlocal())
            epg = self.parse(date, now)
            plot = '[B]{datelong}[/B]\n{start} - {end}\n\n{description}'.format(
                datelong=localize_datelong(epg),
                start=api_data.get('start'),
                end=api_data.get('end'),
                description=html_to_kodi(api_data.get('description', '')),
            )
            return colour(plot)

        # Not Found
        return ''

    @staticmethod
    def get_plotoutline(api_data, season=False):
        """Get plotoutline string from single item json api data"""
        # VRT MAX Search API
        if api_data.get('episodeType'):
            if season is not False:
                plotoutline = html_to_kodi(api_data.get('programDescription', '') or api_data.get('programShortDescription', ''))
                return plotoutline

            plotoutline = html_to_kodi(api_data.get('subtitle', ''))
            return plotoutline

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return html_to_kodi(api_data.get('shortDescription', '') or api_data.get('subtitle', ''))

        # Not Found
        return ''

    def get_season(self, api_data):
        """Get season int from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            # If this is a oneoff video and the season is a year, don't return a season
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return ''
            try:
                season = int(api_data.get('seasonNumber'))
            except (TypeError, ValueError):
                try:
                    season = int(api_data.get('seasonName'))
                except (TypeError, ValueError):
                    season = api_data.get('seasonTitle')
            return season

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return None

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return None

        # Not Found
        return None

    def get_episode(self, api_data):
        """Get episode int from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            # If this is a oneoff video and the season is a year, don't return an episode
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return ''
            try:
                episode = int(api_data.get('episodeNumber'))
            except (TypeError, ValueError):
                episode = int()
            return episode

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return int()

        # Not Found
        return int()

    @staticmethod
    def get_date(api_data):
        """Get date string from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            import dateutil.parser
            return dateutil.parser.parse(api_data.get('onTime')).strftime('%d.%m.%Y')

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return ''

        # Not Found
        return ''

    def get_aired(self, api_data):
        """Get aired string from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
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

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
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

        # VRT MAX Search API
        if api_data.get('episodeType'):
            import dateutil.parser
            return dateutil.parser.parse(api_data.get('onTime')).strftime('%Y-%m-%d %H:%M:%S')

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return ''

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return ''

        # Not Found
        return ''

    @staticmethod
    def get_year(api_data):
        """Get year integer from single item json api data"""
        from datetime import datetime

        # VRT MAX Search API
        if api_data.get('episodeType'):
            # Add proper year information when season falls in range
            # NOTE: Estuary skin is using premiered/aired year, which is incorrect
            try:
                if int(api_data.get('seasonTitle')) in range(1900, datetime.now().year + 1):
                    return int(api_data.get('seasonTitle'))
            except (TypeError, ValueError):
                pass
            return int()

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return int()

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return int()

        # Not Found
        return ''

    def get_mediatype(self, api_data, season=False):
        """Get art dict from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            if season is not False:
                return 'season'

            # If this is a oneoff (e.g. movie) and we get a year of release, do not set 'aired'
            if api_data.get('programType') == 'oneoff' and self.get_year(api_data):
                return 'movie'

            return 'episode'

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            return ''  # NOTE: We do not use 'tvshow' as it won't show as a folder

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            return 'episode'

        return ''

    @staticmethod
    def get_art(api_data, season=False):
        """Get art dict from single item json api data"""
        art_dict = {}

        # VRT MAX Search API
        if api_data.get('episodeType'):
            if season is not False:
                if get_setting_bool('showfanart', default=True):
                    art_dict['fanart'] = reformat_image_url(api_data.get('programImageUrl', 'DefaultSets.png'))
                    if season != 'allseasons':
                        art_dict['thumb'] = reformat_image_url(api_data.get('videoThumbnailUrl', art_dict.get('fanart')))
                    else:
                        art_dict['thumb'] = art_dict.get('fanart')
                    art_dict['banner'] = art_dict.get('fanart')
                    if api_data.get('programAlternativeImageUrl'):
                        art_dict['cover'] = reformat_image_url(api_data.get('programAlternativeImageUrl'))
                        art_dict['poster'] = reformat_image_url(api_data.get('programAlternativeImageUrl'))
                else:
                    art_dict['thumb'] = 'DefaultSets.png'
            else:
                if get_setting_bool('showfanart', default=True):
                    art_dict['thumb'] = reformat_image_url(api_data.get('videoThumbnailUrl', 'DefaultAddonVideo.png'))
                    art_dict['fanart'] = reformat_image_url(api_data.get('programImageUrl', art_dict.get('thumb')))
                    art_dict['banner'] = art_dict.get('fanart')
                    if api_data.get('programAlternativeImageUrl'):
                        art_dict['cover'] = reformat_image_url(api_data.get('programAlternativeImageUrl'))
                        art_dict['poster'] = reformat_image_url(api_data.get('programAlternativeImageUrl'))
                else:
                    art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            if get_setting_bool('showfanart', default=True):
                art_dict['thumb'] = reformat_image_url(api_data.get('thumbnail', 'DefaultAddonVideo.png'))
                art_dict['fanart'] = art_dict.get('thumb')
                art_dict['banner'] = art_dict.get('fanart')
                if api_data.get('alternativeImage'):
                    art_dict['cover'] = reformat_image_url(api_data.get('alternativeImage'))
                    art_dict['poster'] = reformat_image_url(api_data.get('alternativeImage'))
            else:
                art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        if api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            if get_setting_bool('showfanart', default=True):
                art_dict['thumb'] = reformat_image_url(api_data.get('image', 'DefaultAddonVideo.png'))
                art_dict['fanart'] = art_dict.get('thumb')
                art_dict['banner'] = art_dict.get('fanart')
            else:
                art_dict['thumb'] = 'DefaultAddonVideo.png'

            return art_dict

        # Not Found
        return art_dict

    def get_info_labels(self, api_data, season=False, date=None, channel=None):
        """Get infoLabels dict from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            info_labels = dict(
                title=self.get_title(api_data, season=season),
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
                mpaa=self.get_mpaa(api_data),
                tagline=self.get_plotoutline(api_data, season=season),
                duration=self.get_duration(api_data),
                mediatype=self.get_mediatype(api_data, season=season),
                studio=self.get_studio(api_data),
                year=self.get_year(api_data),
                tag=self.get_tag(api_data),
            )
            return info_labels

        # VRT MAX Suggest API
        if api_data.get('type') == 'program':
            info_labels = dict(
                tvshowtitle=self.get_tvshowtitle(api_data),
                plot=self.get_plot(api_data),
                mediatype=self.get_mediatype(api_data, season=season),
                studio=self.get_studio(api_data),
                tag=self.get_tag(api_data),
            )
            return info_labels

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
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
    def get_title(api_data, season=False):
        """Get an appropriate video title"""

        if season is not False:
            title = '%s %s' % (localize(30131), season)  # Season X
            return title

        # VRT MAX Search API
        if api_data.get('episodeType'):
            title = html_to_kodi(api_data.get('title') or api_data.get('shortDescription', '???'))

        # VRT MAX Suggest API
        elif api_data.get('type') == 'program':
            title = api_data.get('title', '???')

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            title = html_to_kodi(api_data.get('subtitle', '???'))

        return title

    @staticmethod
    def get_label(api_data, titletype=None, return_sort=False):
        """Get an appropriate label string matching the type of listing and VRT MAX provided displayOptions from single item json api data"""

        # VRT MAX Search API
        if api_data.get('episodeType'):

            program_type = api_data.get('programType')
            if not titletype:
                titletype = program_type

            label = html_to_kodi(api_data.get('title', '') or api_data.get('shortDescription', ''))
            sort = 'unsorted'
            ascending = True

            if titletype == 'mixed_episodes':
                ascending = False
                label = '[B]%s[/B] - %s' % (api_data.get('programTitle'), label)
                sort = 'dateadded'

            elif titletype in ('reeksaflopend', 'reeksoplopend'):

                if (api_data.get('seasonNumber') and api_data.get('episodeNumber')):
                    sort = 'episode'

                if titletype == 'reeksaflopend':
                    ascending = False

            elif titletype == 'daily':
                import dateutil.parser
                label = '%s - %s' % (dateutil.parser.parse(api_data.get('onTime')).strftime('%d/%m'), label)
                ascending = False
                sort = 'dateadded'

            elif titletype == 'oneoff':
                label = api_data.get('program', label)
                sort = 'label'

        # VRT MAX Suggest API
        elif api_data.get('type') == 'program':
            label = api_data.get('title', '???')

        # VRT MAX Schedule API (some are missing vrt.whatson-id)
        elif api_data.get('vrt.whatson-id') or api_data.get('startTime'):
            title = html_to_kodi(api_data.get('subtitle', '') or api_data.get('shortDescription', ''))
            label = '{start} - [B]{program}[/B]{title}'.format(
                start=api_data.get('start'),
                program=api_data.get('title'),
                title=' - ' + title if title else '',
            )

        # Not Found
        else:
            label = ''

        if return_sort:
            return colour(label), sort, ascending

        return colour(label)

    @staticmethod
    def get_tag(api_data):
        """Return categories for a given episode"""

        # VRT MAX Search API
        if api_data.get('episodeType'):
            from data import CATEGORIES
            return sorted([localize(find_entry(CATEGORIES, 'id', category, {}).get('msgctxt', category))
                           for category in api_data.get('categories', [])])

        # VRT MAX Suggest API
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
