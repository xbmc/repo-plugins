# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements a VRT NU TV guide"""

from __future__ import absolute_import, division, unicode_literals
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.tz

try:  # Python 3
    from urllib.request import build_opener, install_opener, ProxyHandler
except ImportError:  # Python 2
    from urllib2 import build_opener, install_opener, ProxyHandler

from data import CHANNELS, RELATIVE_DATES
from favorites import Favorites
from helperobjects import TitleItem
from kodiutils import (get_cached_url_json, get_proxies, get_url_json, has_addon, localize,
                       localize_datelong, show_listing, ttl, url_for)
from metadata import Metadata
from resumepoints import ResumePoints
from utils import add_https_proto, find_entry, url_to_program


class TVGuide:
    """This implements a VRT TV-guide that offers Kodi menus and TV guide info"""

    VRT_TVGUIDE = 'https://www.vrt.be/bin/epg/schedule.%Y-%m-%d.json'

    def __init__(self):
        """Initializes TV-guide object"""
        self._favorites = Favorites()
        self._resumepoints = ResumePoints()
        self._metadata = Metadata(self._favorites, self._resumepoints)
        install_opener(build_opener(ProxyHandler(get_proxies())))

    def show_tvguide(self, date=None, channel=None):
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
            episode_items = self.get_episode_items(date, channel)
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
        for offset in range(7, -30, -1):
            day = epg + timedelta(days=offset)
            title = localize_datelong(day)
            date = day.strftime('%Y-%m-%d')

            # Highlight today with context of 2 days
            entry = find_entry(RELATIVE_DATES, 'offset', offset)
            if entry:
                date_name = localize(entry.get('msgctxt'))
                if entry.get('permalink'):
                    date = entry.get('id')
                if offset == 0:
                    title = '[COLOR yellow][B]{name}[/B], {date}[/COLOR]'.format(name=date_name, date=title)
                else:
                    title = '[B]{name}[/B], {date}'.format(name=date_name, date=title)

            # Show channel list or channel episodes
            if channel:
                path = url_for('tvguide', date=date, channel=channel)
            else:
                path = url_for('tvguide', date=date)

            cache_file = 'schedule.%s.json' % date
            date_items.append(TitleItem(
                title=title,
                path=path,
                art_dict=dict(thumb='DefaultYear.png'),
                info_dict=dict(plot=localize_datelong(day)),
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
                title = chan.get('label')
                path = url_for('tvguide', date=date, channel=chan.get('name'))
                plot = '%s\n%s' % (localize(30302, **chan), datelong)
            else:
                title = '[B]%s[/B]' % localize(30303, **chan)
                path = url_for('tvguide_channel', channel=chan.get('name'))
                plot = '%s\n\n%s' % (localize(30302, **chan), self.live_description(chan.get('name')))

            channel_items.append(TitleItem(
                title=title,
                path=path,
                art_dict=art_dict,
                info_dict=dict(plot=plot, studio=chan.get('studio')),
            ))
        return channel_items

    def get_episode_items(self, date, channel):
        """Show episodes for a given date and channel"""
        now = datetime.now(dateutil.tz.tzlocal())
        epg = self.parse(date, now)
        epg_url = epg.strftime(self.VRT_TVGUIDE)

        self._favorites.refresh(ttl=ttl('indirect'))

        cache_file = 'schedule.%s.json' % date
        if date in ('today', 'yesterday', 'tomorrow'):
            schedule = get_cached_url_json(url=epg_url, cache=cache_file, ttl=ttl('indirect'), fail={})
        else:
            schedule = get_url_json(url=epg_url, fail={})

        entry = find_entry(CHANNELS, 'name', channel)
        if entry:
            episodes = schedule.get(entry.get('id'), [])
        else:
            episodes = []
        episode_items = []
        for episode in episodes:

            label = self._metadata.get_label(episode)

            context_menu = []
            path = None
            if episode.get('url'):
                video_url = add_https_proto(episode.get('url'))
                path = url_for('play_url', video_url=video_url)
                program = url_to_program(episode.get('url'))
                context_menu, favorite_marker, watchlater_marker = self._metadata.get_context_menu(episode, program, cache_file)
                label += favorite_marker + watchlater_marker

            info_labels = self._metadata.get_info_labels(episode, date=date, channel=entry)
            info_labels['title'] = label

            episode_items.append(TitleItem(
                title=label,
                path=path,
                art_dict=self._metadata.get_art(episode),
                info_dict=info_labels,
                is_playable=True,
                context_menu=context_menu,
            ))
        return episode_items

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
        while True:
            try:
                episode = next(episodes)
            except StopIteration:
                break
            start_date = dateutil.parser.parse(episode.get('startTime'))
            end_date = dateutil.parser.parse(episode.get('endTime'))
            if start_date <= now <= end_date:  # Now playing
                description = '[COLOR yellow][B]%s[/B] %s[/COLOR]\n' % (localize(30421), self.episode_description(episode))
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
        if not description:
            # Add a final 'No transmission' program
            description = '[COLOR yellow][B]%s[/B] %s - 06:00\n» %s[/COLOR]' % (localize(30421), episode.get('end'), localize(30423))
        return description

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
