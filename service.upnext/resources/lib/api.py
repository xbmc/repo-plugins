# -*- coding: utf-8 -*-
# GNU General Public License v2.0 (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, unicode_literals
from xbmc import sleep
from utils import event, get_setting_bool, get_setting_int, jsonrpc, log as ulog


class Api:
    """Main API class"""
    _shared_state = {}

    def __init__(self):
        """Constructor for Api class"""
        self.__dict__ = self._shared_state
        self.data = {}
        self.encoding = 'base64'

    def log(self, msg, level=2):
        """Log wrapper"""
        ulog(msg, name=self.__class__.__name__, level=level)

    def has_addon_data(self):
        return self.data

    def reset_addon_data(self):
        self.data = {}

    def addon_data_received(self, data, encoding='base64'):
        self.log('addon_data_received called with data %s' % data, 2)
        self.data = data
        self.encoding = encoding

    @staticmethod
    def play_kodi_item(episode):
        jsonrpc(method='Player.Open', id=0, params=dict(item=dict(episodeid=episode.get('episodeid'))))

    def get_next_in_playlist(self, position):
        result = jsonrpc(method='Playlist.GetItems', params=dict(
            playlistid=1,
            limits=dict(start=position + 1, end=position + 2),
            properties=['art', 'dateadded', 'episode', 'file', 'firstaired', 'lastplayed',
                        'playcount', 'plot', 'rating', 'resume', 'runtime', 'season',
                        'showtitle', 'streamdetails', 'title', 'tvshowid', 'writer'],
        ))

        if not result:
            return None

        self.log('Got details of next playlist item %s' % result, 2)
        if result.get('result', {}).get('items') is None:
            return None

        item = result.get('result', {}).get('items', [])[0]
        if item.get('type') != 'episode':
            return None

        item['episodeid'] = item.get('id')
        item['tvshowid'] = item.get('tvshowid', item.get('id'))
        return item

    def play_addon_item(self):
        if self.data.get('play_url'):
            self.log('Playing the next episode directly: %(play_url)s' % self.data, 2)
            jsonrpc(method='Player.Open', params=dict(item=dict(file=self.data.get('play_url'))))
        else:
            self.log('Sending %(encoding)s data to add-on to play: %(play_info)s' % dict(encoding=self.encoding, **self.data), 2)
            event(message=self.data.get('id'), data=self.data.get('play_info'), sender='upnextprovider', encoding=self.encoding)

    def handle_addon_lookup_of_next_episode(self):
        if not self.data:
            return None
        self.log('handle_addon_lookup_of_next_episode episode returning data %(next_episode)s' % self.data, 2)
        return self.data.get('next_episode')

    def handle_addon_lookup_of_current_episode(self):
        if not self.data:
            return None
        self.log('handle_addon_lookup_of_current episode returning data %(current_episode)s' % self.data, 2)
        return self.data.get('current_episode')

    def notification_time(self, total_time=None):
        # Alway use metadata, when available
        if self.data.get('notification_time'):
            return int(self.data.get('notification_time'))

        # Some consumers send the offset when the credits start (e.g. Netflix)
        if total_time and self.data.get('notification_offset'):
            return total_time - int(self.data.get('notification_offset'))

        # Use a customized notification time, when configured
        if total_time and get_setting_bool('customAutoPlayTime'):
            if total_time > 60 * 60:
                return get_setting_int('autoPlayTimeXL')
            if total_time > 40 * 60:
                return get_setting_int('autoPlayTimeL')
            if total_time > 20 * 60:
                return get_setting_int('autoPlayTimeM')
            if total_time > 10 * 60:
                return get_setting_int('autoPlayTimeS')
            return get_setting_int('autoPlayTimeXS')

        # Use one global default, regardless of episode length
        return get_setting_int('autoPlaySeasonTime')

    def get_now_playing(self):
        # Seems to work too fast loop whilst waiting for it to become active
        result = dict()
        while not result.get('result'):
            result = jsonrpc(method='Player.GetActivePlayers')
            self.log('Got active player %s' % result, 2)

        if not result.get('result'):
            return None

        playerid = result.get('result')[0].get('playerid')

        # Get details of the playing media
        self.log('Getting details of now playing media', 2)
        result = jsonrpc(method='Player.GetItem', params=dict(
            playerid=playerid,
            properties=['episode', 'genre', 'playcount', 'plotoutline', 'season', 'showtitle', 'tvshowid'],
        ))
        self.log('Got details of now playing media %s' % result, 2)
        return result

    def handle_kodi_lookup_of_episode(self, tvshowid, current_file, include_watched, current_episode_id):
        result = jsonrpc(method='VideoLibrary.GetEpisodes', params=dict(
            tvshowid=tvshowid,
            properties=['art', 'dateadded', 'episode', 'file', 'firstaired', 'lastplayed',
                        'playcount', 'plot', 'rating', 'resume', 'runtime', 'season',
                        'showtitle', 'streamdetails', 'title', 'tvshowid', 'writer'],
            sort=dict(method='episode'),
        ))

        if not result.get('result'):
            return None

        self.log('Got details of next up episode %s' % result, 2)
        sleep(100)

        # Find the next unwatched and the newest added episodes
        return self.find_next_episode(result, current_file, include_watched, current_episode_id)

    def handle_kodi_lookup_of_current_episode(self, tvshowid, current_episode_id):
        result = jsonrpc(method='VideoLibrary.GetEpisodes', params=dict(
            tvshowid=tvshowid,
            properties=['art', 'dateadded', 'episode', 'file', 'firstaired', 'lastplayed',
                        'playcount', 'plot', 'rating', 'resume', 'runtime', 'season',
                        'showtitle', 'streamdetails', 'title', 'tvshowid', 'writer'],
            sort=dict(method='episode'),
        ))

        if not result.get('result'):
            return None

        self.log('Find current episode called', 2)
        sleep(100)

        # Find the next unwatched and the newest added episodes
        episodes = result.get('result', {}).get('episodes', [])
        for idx, episode in enumerate(episodes):
            # Find position of current episode
            if current_episode_id == episode.get('episodeid'):
                self.log('Find current episode found episode in position: %d' % idx, 2)
                return episode

        # No next episode found
        self.log('No next episode found', 1)
        return None

    @staticmethod
    def showtitle_to_id(title):
        result = jsonrpc(method='VideoLibrary.GetTVShows', id='libTvShows', params=dict(properties=['title']))

        for tvshow in result.get('result', {}).get('tvshows', []):
            if tvshow.get('label') == title:
                return tvshow.get('tvshowid')
        return '-1'

    @staticmethod
    def get_episode_id(showid, show_season, show_episode):
        show_season = int(show_season)
        show_episode = int(show_episode)
        result = jsonrpc(method='VideoLibrary.GetEpisodes', params=dict(
            properties=['episode', 'season'],
            tvshowid=int(showid),
        ))

        episodeid = 0
        for episode in result.get('result', {}).get('episodes', []):
            if episode.get('episodeid') and episode.get('season') == show_season and episode.get('episode') == show_episode:
                episodeid = episode.get('episodeid')

        return episodeid

    def find_next_episode(self, result, current_file, include_watched, current_episode_id):
        found_match = False
        episodes = result.get('result', {}).get('episodes', [])
        for episode in episodes:
            # Find position of current episode
            if current_episode_id == episode.get('episodeid'):
                found_match = True
                continue
            # Check if it may be a multi-part episode
            if episode.get('file') == current_file:
                continue
            # Skip already watched episodes?
            if not include_watched and episode.get('playcount') > 0:
                continue
            if found_match:
                return episode

        # No next episode found
        self.log('No next episode found', 1)
        return None
