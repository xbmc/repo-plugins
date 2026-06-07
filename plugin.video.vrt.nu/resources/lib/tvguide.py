# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements a VRT MAX TV guide"""

from datetime import datetime, timedelta
import dateutil.parser
import dateutil.tz

from api import get_epg_episodes, get_epg_list
from data import CHANNELS, RELATIVE_DATES
from helperobjects import TitleItem
from kodiutils import (colour, get_cached_url_json, has_addon, localize,
                       localize_datelong, show_listing, themecolour, ttl, url_for)
from utils import find_entry, parse_duration


class TVGuide:
    """This implements a VRT TV-guide that offers Kodi menus and TV guide info"""

    VRT_TVGUIDE = 'https://www.vrt.be/bin/epg/schedule.%Y-%m-%d.json'

    def __init__(self):
        """Initializes TV-guide object"""

    def show_tvguide(self, date=None, channel=None, end_cursor=None):
        """Offer a menu depending on the information provided"""

        if not date and not channel:
            date_items = self.get_date_items()
            show_listing(date_items, category=30026, content='files')  # TV guide

        elif not channel:
            channel_items = self.get_channel_items(date=date)
            entry = find_entry(RELATIVE_DATES, 'id', date)
            date_name = localize(entry.get('msgctxt')) if entry else date
            show_listing(channel_items, category=date_name)

        elif not date:
            date_items = self.get_date_items(channel=channel)
            channel_name = find_entry(CHANNELS, 'name', channel).get('label')
            show_listing(date_items, category=channel_name, content='files', selected=7)

        else:
            episode_items = self.get_episode_items(date, channel, end_cursor)
            channel_name = find_entry(CHANNELS, 'name', channel).get('label')
            entry = find_entry(RELATIVE_DATES, 'id', date)
            date_name = localize(entry.get('msgctxt')) if entry else date
            show_listing(episode_items, category='%s / %s' % (channel_name, date_name), content='episodes', cache=False)

    @staticmethod
    def get_date_items(channel=None):
        """Offer a menu to select the TV-guide date"""

        epg = datetime.now(dateutil.tz.tzlocal())
        # Daily EPG information shows information from 6AM until 6AM
        if epg.hour < 6:
            epg += timedelta(days=-1)
        date_items = []
        for offset in range(7, -8, -1):
            day = epg + timedelta(days=offset)
            label = localize_datelong(day)
            date = day.strftime('%Y-%m-%d')

            # Highlight today with context of 2 days
            entry = find_entry(RELATIVE_DATES, 'offset', offset)
            if entry:
                date_name = localize(entry.get('msgctxt'))
                if entry.get('permalink'):
                    date = entry.get('id')
                if offset == 0:
                    label = '[COLOR={highlighted}][B]{name}[/B], {date}[/COLOR]'.format(highlighted=themecolour('highlighted'), name=date_name, date=label)
                else:
                    label = '[B]{name}[/B], {date}'.format(name=date_name, date=label)

            plot = '[B]{datelong}[/B]'.format(datelong=localize_datelong(day))

            # Show channel list or channel episodes
            if channel:
                path = url_for('tvguide', date=date, channel=channel)
            else:
                path = url_for('tvguide', date=date)

            cache_file = 'schedule.{date}.json'.format(date=date)
            date_items.append(TitleItem(
                label=label,
                path=path,
                art_dict={'thumb': 'DefaultYear.png'},
                info_dict={'plot': plot},
                context_menu=[(
                    localize(30413),  # Refresh menu
                    'RunPlugin(%s)' % url_for('delete_cache', cache_file=cache_file)
                )],
            ))
        return date_items

    def get_channel_items(self, date=None, channel=None):
        """Offer a menu to select the channel"""
        if date:
            now = datetime.now(dateutil.tz.tzlocal())
            epg = self.parse(date, now)
            datelong = localize_datelong(epg)

        channel_items = []
        for chan in CHANNELS:
            # Only some channels are supported
            if not chan.get('has_tvguide'):
                continue

            # If a channel is requested, stop processing if it is no match
            if channel and channel != chan.get('name'):
                continue

            art_dict = {}

            # Try to use the white icons for thumbnails (used for icons as well)
            if has_addon('resource.images.studios.white'):
                art_dict['thumb'] = 'resource://resource.images.studios.white/{studio}.png'.format(**chan)
            else:
                art_dict['thumb'] = 'DefaultTags.png'

            if date:
                label = chan.get('label')
                path = url_for('tvguide', date=date, channel=chan.get('name'), end_cursor='1')
                plot = '[B]%s[/B]\n%s' % (datelong, localize(30302, **chan))
            else:
                label = '[B]%s[/B]' % localize(30303, **chan)
                path = url_for('tvguide_channel', channel=chan.get('name'))
                plot = '%s\n\n%s' % (localize(30302, **chan), self.live_description(chan.get('name')))

            context_menu = [(
                localize(30413),  # Refresh menu
                'RunPlugin(%s)' % url_for('delete_cache', cache_file='channel.{channel}.json'.format(channel=chan.get('name'))),
            )]

            channel_items.append(TitleItem(
                label=label,
                path=path,
                art_dict=art_dict,
                context_menu=context_menu,
                info_dict={'plot': plot, 'studio': chan.get('studio')},
            ))
        return channel_items

    def get_episode_items(self, date, channel, end_cursor=None):
        """Show episodes for a given date and channel"""
        now = datetime.now(dateutil.tz.tzlocal())
        epg_date = self.parse(date, now)
        episode_items = get_epg_episodes(date=epg_date.strftime('%Y-%m-%d'), channel=channel, page=end_cursor)
        return episode_items

    def get_epg_data(self):
        """Return EPG data"""
        from base64 import b64decode

        now = datetime.now(dateutil.tz.tzlocal())
        epg_data = {}
        tz_brussels = dateutil.tz.gettz('Europe/Brussels')

        epg_dates = [now + timedelta(days=i) for i in range(-7, 8)]
        for epg_date in epg_dates:

            for channel in CHANNELS:
                if not channel.get('has_tvguide'):
                    continue

                epg_id = channel.get('epg_id')
                epg_data.setdefault(epg_id, [])

                data, _ = get_epg_list(channel.get('name'), epg_date.strftime('%Y-%m-%d'))

                previous_stop_dt = None
                for item in data:
                    node = item.get('node', {}) or item
                    stream = None
                    ep_code = None

                    # Decode start datetime
                    if node.get('tileType') == 'livestream':
                        start_str = node.get('livestream').get('startDateTime')
                    else:
                        comp_id = node.get('componentId', '').lstrip('#')
                        decoded = b64decode(comp_id.encode('utf-8')).decode('utf-8')
                        start_str = decoded.split('#1')[2].split('|')[0]

                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))

                    if node.get('livestream'):
                        episode = node.get('livestream').get('episode')
                    else:
                        episode = node.get('episode')
                    duration = timedelta(0)

                    if node.get('progress'):
                        duration = timedelta(seconds=node.get('progress').get('durationInSeconds'))
                    elif episode and (dur_raw := episode.get('durationRaw')):
                        duration = parse_duration(dur_raw)

                    if duration == timedelta(0) and node.get('statusMeta'):
                        minutes_str = node['statusMeta'][0].get('value', '').split()[0]
                        if minutes_str.isdigit():
                            duration = timedelta(minutes=int(minutes_str))

                    stop_dt = start_dt + (duration or timedelta())

                    epg_start_dt = previous_stop_dt or start_dt
                    previous_stop_dt = stop_dt

                    # Common conversion
                    start_iso = epg_start_dt.astimezone(tz_brussels).isoformat()
                    stop_iso = stop_dt.astimezone(tz_brussels).isoformat()

                    # Fill EPG entry
                    if episode:
                        program = episode.get('program', {})
                        title = program.get('title')
                        description = episode.get('description')
                        subtitle = episode.get('subtitle')
                        image = ((episode.get('image') or {}).get('templateUrl') or '').split('?')[0]
                        genre = (episode.get('analytics') or {}).get('categories')
                        date = (episode.get('analytics') or {}).get('airDate')

                        watch_action = episode.get('watchAction', {})
                        video_id = watch_action.get('videoId')
                        publication_id = watch_action.get('publicationId')
                        if node.get('available'):
                            stream = url_for('play_id', video_id=video_id, publication_id=publication_id)

                        program_type = program.get('programType')
                        season = episode.get('season', {})
                        if (
                            program_type == 'series'
                            and (title_raw := season.get('titleRaw', '')).isnumeric()
                            and isinstance(ep_no := episode.get('episodeNumberRaw'), int)
                        ):
                            se_no = int(title_raw)
                            ep_code = f'S{se_no:02d}E{ep_no:02d}'
                    else:
                        title = node.get('title')
                        description = subtitle = genre = date = None
                        image = (node.get('image') or {}).get('templateUrl') if node.get('image') else None

                    epg_data[epg_id].append({
                        'start': start_iso,
                        'stop': stop_iso,
                        'title': title,
                        'description': description,
                        'subtitle': subtitle,
                        'episode': ep_code,
                        'genre': genre,
                        'image': image,
                        'date': date,
                        'stream': stream,
                    })

        return epg_data

    def playing_now(self, channel):
        """Return the EPG information for what is playing now"""
        now = datetime.now(dateutil.tz.tzlocal())
        epg = now
        # Daily EPG information shows information from 6AM until 6AM
        if epg.hour < 6:
            epg += timedelta(days=-1)

        entry = find_entry(CHANNELS, 'name', channel)
        if not entry:
            return ''

        epg_url = epg.strftime(self.VRT_TVGUIDE)
        schedule = get_cached_url_json(url=epg_url, cache='schedule.today.json', ttl=ttl('indirect'), fail={})
        episodes = iter(schedule.get(entry.get('id'), []))

        while True:
            try:
                episode = next(episodes)
            except StopIteration:
                break
            start_date = dateutil.parser.parse(episode.get('startTime'))
            end_date = dateutil.parser.parse(episode.get('endTime'))
            if start_date <= now <= end_date:  # Now playing
                return episode.get('title')
        return ''

    @staticmethod
    def episode_description(episode):
        """Return a formatted description for an episode"""
        return '{start} - {end}\n» {title}'.format(**episode)

    def live_description(self, channel):
        """Return the EPG information for current and next live program"""
        now = datetime.now(dateutil.tz.tzlocal())
        epg = now
        # Daily EPG information shows information from 6AM until 6AM
        if epg.hour < 6:
            epg += timedelta(days=-1)

        entry = find_entry(CHANNELS, 'name', channel)
        if not entry:
            return ''

        epg_url = epg.strftime(self.VRT_TVGUIDE)
        schedule = get_cached_url_json(url=epg_url, cache='schedule.today.json', ttl=ttl('indirect'), fail={})
        episodes = iter(schedule.get(entry.get('id'), []))

        description = ''
        episode = None
        while True:
            try:
                episode = next(episodes)
            except StopIteration:
                break
            start_date = dateutil.parser.parse(episode.get('startTime'))
            end_date = dateutil.parser.parse(episode.get('endTime'))
            if start_date <= now <= end_date:  # Now playing
                description = '[COLOR={highlighted}][B]%s[/B] %s[/COLOR]\n' % (localize(30421), self.episode_description(episode))
                try:
                    description += '[B]%s[/B] %s' % (localize(30422), self.episode_description(next(episodes)))
                except StopIteration:
                    break
                break
            if now < start_date:  # Nothing playing now, but this may be next
                description = '[B]%s[/B] %s\n' % (localize(30422), self.episode_description(episode))
                try:
                    description += '[B]%s[/B] %s' % (localize(30422), self.episode_description(next(episodes)))
                except StopIteration:
                    break
                break
        if episode and not description:
            # Add a final 'No transmission' program
            description = '[COLOR={highlighted}][B]%s[/B] %s - 06:00\n» %s[/COLOR]' % (localize(30421), episode.get('end'), localize(30423))
        return colour(description)

    @staticmethod
    def parse(date, now):
        """Parse a given string and return a datetime object
            This supports 'today', 'yesterday' and 'tomorrow'
            It also compensates for TV-guides covering from 6AM to 6AM
       """
        entry = find_entry(RELATIVE_DATES, 'id', date)
        if not entry:
            return dateutil.parser.parse(date)

        offset = entry.get('offset')
        if now.hour < 6:
            return now + timedelta(days=offset - 1)

        return now + timedelta(days=offset)
