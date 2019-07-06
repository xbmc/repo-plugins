# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Dag Wieers (@dagwieers) <dag@wieers.com>
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Implements a VRT NU TV guide '''

from __future__ import absolute_import, division, unicode_literals
from datetime import datetime, timedelta
import json
import dateutil.parser
import dateutil.tz

try:  # Python 3
    from urllib.parse import quote
    from urllib.request import build_opener, install_opener, ProxyHandler, urlopen
except ImportError:  # Python 2
    from urllib2 import build_opener, install_opener, ProxyHandler, urlopen, quote

from resources.lib import CHANNELS, favorites, metadatacreator, statichelper
from resources.lib.helperobjects import TitleItem

DATE_STRINGS = {
    '-2': 30330,  # 2 days ago
    '-1': 30331,  # Yesterday
    '0': 30332,  # Today
    '1': 30333,  # Tomorrow
    '2': 30334,  # In 2 days
}

DATES = {
    '-1': 'yesterday',
    '0': 'today',
    '1': 'tomorrow',
}


class TVGuide:
    ''' This implements a VRT TV-guide that offers Kodi menus and TV guide info '''

    VRT_TVGUIDE = 'https://www.vrt.be/bin/epg/schedule.%Y-%m-%d.json'

    def __init__(self, _kodi):
        ''' Initializes TV-guide object '''
        self._kodi = _kodi
        self._favorites = favorites.Favorites(_kodi)

        self._proxies = _kodi.get_proxies()
        install_opener(build_opener(ProxyHandler(self._proxies)))
        self._showfanart = _kodi.get_setting('showfanart', 'true') == 'true'

    def show_tvguide(self, date=None, channel=None):
        ''' Offer a menu depending on the information provided '''

        if not date:
            date_items = self.show_date_menu()
            self._kodi.show_listing(date_items, content='files')

        elif not channel:
            channel_items = self.show_channel_menu(date)
            self._kodi.show_listing(channel_items)

        else:
            episode_items = self.show_episodes(date, channel)
            self._kodi.show_listing(episode_items, content='episodes', cache=False)

    def show_date_menu(self):
        ''' Offer a menu to select the TV-guide date '''
        epg = datetime.now(dateutil.tz.tzlocal())
        # Daily EPG information shows information from 6AM until 6AM
        if epg.hour < 6:
            epg += timedelta(days=-1)
        date_items = []
        for i in range(7, -30, -1):
            day = epg + timedelta(days=i)
            title = self._kodi.localize_datelong(day)

            # Highlight today with context of 2 days
            if str(i) in DATE_STRINGS:
                if i == 0:
                    title = '[COLOR yellow][B]%s[/B], %s[/COLOR]' % (self._kodi.localize(DATE_STRINGS[str(i)]), title)
                else:
                    title = '[B]%s[/B], %s' % (self._kodi.localize(DATE_STRINGS[str(i)]), title)

            # Make permalinks for today, yesterday and tomorrow
            if str(i) in DATES:
                date = DATES[str(i)]
            else:
                date = day.strftime('%Y-%m-%d')
            cache_file = 'schedule.%s.json' % date
            date_items.append(TitleItem(
                title=title,
                path=self._kodi.url_for('tvguide', date=date),
                art_dict=dict(thumb='DefaultYear.png', fanart='DefaultYear.png'),
                info_dict=dict(plot=self._kodi.localize_datelong(day)),
                context_menu=[(self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file=cache_file))],
            ))
        return date_items

    def show_channel_menu(self, date):
        ''' Offer a menu to select the channel '''
        now = datetime.now(dateutil.tz.tzlocal())
        epg = self.parse(date, now)
        datelong = self._kodi.localize_datelong(epg)

        channel_items = []
        for channel in CHANNELS:
            if channel.get('name') not in ('een', 'canvas', 'ketnet'):
                continue

            fanart = 'resource://resource.images.studios.coloured/%(studio)s.png' % channel
            thumb = 'resource://resource.images.studios.white/%(studio)s.png' % channel
            plot = '%s\n%s' % (self._kodi.localize(30301).format(**channel), datelong)
            channel_items.append(TitleItem(
                title=channel.get('label'),
                path=self._kodi.url_for('tvguide', date=date, channel=channel.get('name')),
                art_dict=dict(thumb=thumb, fanart=fanart),
                info_dict=dict(plot=plot, studio=channel.get('studio')),
            ))
        return channel_items

    def show_episodes(self, date, channel):
        ''' Show episodes for a given date and channel '''
        now = datetime.now(dateutil.tz.tzlocal())
        epg = self.parse(date, now)
        datelong = self._kodi.localize_datelong(epg)
        epg_url = epg.strftime(self.VRT_TVGUIDE)

        self._favorites.get_favorites(ttl=60 * 60)

        cache_file = 'schedule.%s.json' % date
        if date in ('today', 'yesterday', 'tomorrow'):
            # Try the cache if it is fresh
            schedule = self._kodi.get_cache(cache_file, ttl=60 * 60)
            if not schedule:
                self._kodi.log_notice('URL get: ' + epg_url, 'Verbose')
                schedule = json.load(urlopen(epg_url))
                self._kodi.update_cache(cache_file, schedule)
        else:
            self._kodi.log_notice('URL get: ' + epg_url, 'Verbose')
            schedule = json.load(urlopen(epg_url))

        name = channel
        try:
            channel = next(c for c in CHANNELS if c.get('name') == name)
            episodes = schedule.get(channel.get('id'), [])
        except StopIteration:
            episodes = []
        episode_items = []
        for episode in episodes:
            metadata = metadatacreator.MetadataCreator()
            title = episode.get('title', 'Untitled')
            start = episode.get('start')
            end = episode.get('end')
            start_date = dateutil.parser.parse(episode.get('startTime'))
            end_date = dateutil.parser.parse(episode.get('endTime'))
            metadata.datetime = start_date
            url = episode.get('url')
            metadata.tvshowtitle = title
            label = '%s - %s' % (start, title)
            # NOTE: Do not use startTime and endTime as we don't want duration with seconds granularity
            start_time = dateutil.parser.parse(start)
            end_time = dateutil.parser.parse(end)
            if end_time < start_time:
                end_time = end_time + timedelta(days=1)
            metadata.duration = (end_time - start_time).total_seconds()
            metadata.plot = '[B]%s[/B]\n%s\n%s - %s\n[I]%s[/I]' % (title, datelong, start, end, channel.get('label'))
            metadata.brands.append(channel.get('studio'))
            metadata.mediatype = 'episode'
            if self._showfanart:
                thumb = episode.get('image', 'DefaultAddonVideo.png')
            else:
                thumb = 'DefaultAddonVideo.png'
            metadata.icon = thumb
            context_menu = []
            if url:
                video_url = statichelper.add_https_method(url)
                path = self._kodi.url_for('play_url', video_url=video_url)
                if start_date <= now <= end_date:  # Now playing
                    label = '[COLOR yellow]%s[/COLOR] %s' % (label, self._kodi.localize(30302))
                program = statichelper.url_to_program(episode.get('url'))
                if self._favorites.is_activated():
                    program_title = quote(title.encode('utf-8'), '')
                    if self._favorites.is_favorite(program):
                        context_menu = [(self._kodi.localize(30412), 'RunPlugin(%s)' % self._kodi.url_for('unfollow', program=program, title=program_title))]
                        label += '[COLOR yellow]°[/COLOR]'
                    else:
                        context_menu = [(self._kodi.localize(30411), 'RunPlugin(%s)' % self._kodi.url_for('follow', program=program, title=program_title))]
            else:
                # This is a non-actionable item
                path = None
                if start_date < now <= end_date:  # Now playing
                    label = '[COLOR gray]%s[/COLOR] %s' % (label, self._kodi.localize(30302))
                else:
                    label = '[COLOR gray]%s[/COLOR]' % label
            context_menu.append((self._kodi.localize(30413), 'RunPlugin(%s)' % self._kodi.url_for('delete_cache', cache_file=cache_file)))
            metadata.title = label
            episode_items.append(TitleItem(
                title=label,
                path=path,
                art_dict=dict(thumb=thumb, icon='DefaultAddonVideo.png', fanart=thumb),
                info_dict=metadata.get_info_dict(),
                is_playable=True,
                context_menu=context_menu,
            ))
        return episode_items

    def episode_description(self, episode):
        ''' Return a formatted description for an episode '''
        return '{start} - {end}\n» [B]{title}[/B]'.format(**episode)

    def live_description(self, channel):
        ''' Return the EPG information for current and next live program '''
        now = datetime.now(dateutil.tz.tzlocal())
        epg = now
        # Daily EPG information shows information from 6AM until 6AM
        if epg.hour < 6:
            epg += timedelta(days=-1)
        # Try the cache if it is fresh
        schedule = self._kodi.get_cache('schedule.today.json', ttl=60 * 60)
        if not schedule:
            epg_url = epg.strftime(self.VRT_TVGUIDE)
            self._kodi.log_notice('URL get: ' + epg_url, 'Verbose')
            schedule = json.load(urlopen(epg_url))
            self._kodi.update_cache('schedule.today.json', schedule)
        name = channel
        try:
            channel = next(c for c in CHANNELS if c.get('name') == name)
            episodes = iter(schedule[channel.get('id')])
        except StopIteration:
            return ''

        description = ''
        while True:
            try:
                episode = next(episodes)
            except StopIteration:
                break
            start_date = dateutil.parser.parse(episode.get('startTime'))
            end_date = dateutil.parser.parse(episode.get('endTime'))
            if start_date <= now <= end_date:  # Now playing
                description = '[COLOR yellow][B]%s[/B] %s[/COLOR]\n' % (self._kodi.localize(30421), self.episode_description(episode))
                try:
                    description += '[B]%s[/B] %s' % (self._kodi.localize(30422), self.episode_description(next(episodes)))
                except StopIteration:
                    break
                break
            elif now < start_date:  # Nothing playing now, but this may be next
                description = '[B]%s[/B] %s\n' % (self._kodi.localize(30422), self.episode_description(episode))
                try:
                    description += '[B]%s[/B] %s' % (self._kodi.localize(30422), self.episode_description(next(episodes)))
                except StopIteration:
                    break
                break
        if not description:
            # Add a final 'No transmission' program
            description = '[COLOR yellow][B]%s[/B] %s - 06:00\n» %s[/COLOR]' % (self._kodi.localize(30421), episode.get('end'), self._kodi.localize(30423))
        return description

    def parse(self, date, now):
        ''' Parse a given string and return a datetime object
            This supports 'today', 'yesterday' and 'tomorrow'
            It also compensates for TV-guides covering from 6AM to 6AM
        '''
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
