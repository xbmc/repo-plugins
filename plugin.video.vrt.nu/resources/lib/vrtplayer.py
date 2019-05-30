# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, unicode_literals
from resources.lib import actions, statichelper, streamservice, tokenresolver
from resources.lib.helperobjects import TitleItem


class VRTPlayer:
    ''' An object providing all methods for Kodi menu generation '''

    def __init__(self, _kodi, _favorites, _apihelper):
        ''' Initialise object '''
        self._kodi = _kodi
        self._favorites = _favorites
        self._apihelper = _apihelper

    def show_main_menu_items(self):
        ''' The VRT NU add-on main menu '''
        main_items = []

        # Only add 'My programs' when it has been activated
        if self._favorites.is_activated():
            main_items.append(TitleItem(
                title=self._kodi.localize(30010),  # My programs
                url_dict=dict(action=actions.LISTING_FAVORITES),
                is_playable=False,
                art_dict=dict(thumb='icons/settings/profiles.png', icon='icons/settings/profiles.png', fanart='icons/settings/profiles.png'),
                video_dict=dict(plot=self._kodi.localize(30011))
            ))

        main_items.extend([
            TitleItem(title=self._kodi.localize(30012),  # A-Z listing
                      url_dict=dict(action=actions.LISTING_AZ_TVSHOWS),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultMovieTitle.png', icon='DefaultMovieTitle.png', fanart='DefaultMovieTitle.png'),
                      video_dict=dict(plot=self._kodi.localize(30013))),
            TitleItem(title=self._kodi.localize(30014),  # Categories
                      url_dict=dict(action=actions.LISTING_CATEGORIES),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultGenre.png', icon='DefaultGenre.png', fanart='DefaultGenre.png'),
                      video_dict=dict(plot=self._kodi.localize(30015))),
            TitleItem(title=self._kodi.localize(30016),  # Channels
                      url_dict=dict(action=actions.LISTING_CHANNELS),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultTags.png', icon='DefaultTags.png', fanart='DefaultTags.png'),
                      video_dict=dict(plot=self._kodi.localize(30017))),
            TitleItem(title=self._kodi.localize(30018),  # Live TV
                      url_dict=dict(action=actions.LISTING_LIVE),
                      is_playable=False,
                      # art_dict=dict(thumb='DefaultAddonPVRClient.png', icon='DefaultAddonPVRClient.png', fanart='DefaultAddonPVRClient.png'),
                      art_dict=dict(thumb='DefaultTVShows.png', icon='DefaultTVShows.png', fanart='DefaultTVShows.png'),
                      video_dict=dict(plot=self._kodi.localize(30019))),
            TitleItem(title=self._kodi.localize(30020),  # Recent items
                      url_dict=dict(action=actions.LISTING_RECENT),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png', icon='DefaultRecentlyAddedEpisodes.png', fanart='DefaultRecentlyAddedEpisodes.png'),
                      video_dict=dict(plot=self._kodi.localize(30021))),
            TitleItem(title=self._kodi.localize(30022),  # Soon offline
                      url_dict=dict(action=actions.LISTING_OFFLINE),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultYear.png', icon='DefaultYear.png', fanart='DefaultYear.png'),
                      video_dict=dict(plot=self._kodi.localize(30023))),
            TitleItem(title=self._kodi.localize(30024),  # TV guide
                      url_dict=dict(action=actions.LISTING_TVGUIDE),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultAddonTvInfo.png', icon='DefaultAddonTvInfo.png', fanart='DefaultAddonTvInfo.png'),
                      video_dict=dict(plot=self._kodi.localize(30025))),
            TitleItem(title=self._kodi.localize(30026),  # Search
                      url_dict=dict(action=actions.SEARCH),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultAddonsSearch.png', icon='DefaultAddonsSearch.png', fanart='DefaultAddonsSearch.png'),
                      video_dict=dict(plot=self._kodi.localize(30027))),
        ])
        self._kodi.show_listing(main_items)

    def show_favorites_menu_items(self):
        ''' The VRT NU addon 'My Programs' menu '''
        favorites_items = [
            TitleItem(title=self._kodi.localize(30040),  # My A-Z listing
                      url_dict=dict(action=actions.LISTING_AZ_TVSHOWS, use_favorites=True),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultMovieTitle.png', icon='DefaultMovieTitle.png', fanart='DefaultMovieTitle.png'),
                      video_dict=dict(plot=self._kodi.localize(30041))),
            TitleItem(title=self._kodi.localize(30042),  # My recent items
                      url_dict=dict(action=actions.LISTING_RECENT, use_favorites=True),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png', icon='DefaultRecentlyAddedEpisodes.png', fanart='DefaultRecentlyAddedEpisodes.png'),
                      video_dict=dict(plot=self._kodi.localize(30043))),
            TitleItem(title=self._kodi.localize(30044),  # My soon offline
                      url_dict=dict(action=actions.LISTING_OFFLINE, use_favorites=True),
                      is_playable=False,
                      art_dict=dict(thumb='DefaultYear.png', icon='DefaultYear.png', fanart='DefaultYear.png'),
                      video_dict=dict(plot=self._kodi.localize(30045))),
        ]
        self._kodi.show_listing(favorites_items)

        # Show dialog when no favorites were found
        if not self._favorites.names():
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30415), message=self._kodi.localize(30416))

    def show_tvshow_menu_items(self, category=None, use_favorites=False):
        ''' The VRT NU add-on 'A-Z' listing menu '''
        tvshow_items = self._apihelper.get_tvshow_items(category=category, use_favorites=use_favorites)
        self._kodi.show_listing(tvshow_items, sort='label', content='tvshows')

    def show_category_menu_items(self):
        ''' The VRT NU add-on 'Categories' listing menu '''
        category_items = self._apihelper.get_category_items()
        self._kodi.show_listing(category_items, sort='label', content='files')

    def show_channels_menu_items(self, channel=None):
        ''' The VRT NU add-on 'Channels' listing menu '''
        if channel:
            tvshow_items = self._apihelper.get_tvshow_items(channel=channel)
            self._kodi.show_listing(tvshow_items, sort='label', content='tvshows')
        else:
            from resources.lib import CHANNELS
            channel_items = self._apihelper.get_channel_items(action=actions.LISTING_CHANNELS, channels=[c.get('name') for c in CHANNELS])
            self._kodi.show_listing(channel_items, cache=False)

    def show_livestream_items(self):
        ''' The VRT NU add-on 'Live TV' listing menu '''
        channel_items = self._apihelper.get_channel_items(action=actions.PLAY, channels=['een', 'canvas', 'sporza', 'ketnet-jr', 'ketnet', 'stubru', 'mnm'])
        self._kodi.show_listing(channel_items, cache=False)

    def show_episodes(self, path):
        ''' The VRT NU add-on episodes listing menu '''
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(path=path, show_seasons=True)
        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content)

    def show_all_episodes(self, path):
        ''' The VRT NU add-on '* All seasons' listing menu '''
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(path=path)
        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content)

    def show_recent(self, page=0, use_favorites=False):
        ''' The VRT NU add-on 'Most recent' and 'My most recent' listing menu '''
        page = statichelper.realpage(page)
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(page=page, use_favorites=use_favorites, variety='recent')

        # Add 'More...' entry at the end
        if len(episode_items) == 50:
            episode_items.append(TitleItem(
                title=self._kodi.localize(30300),
                url_dict=dict(action=actions.LISTING_RECENT, page=page + 1, use_favorites=use_favorites),
                is_playable=False,
                art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png', icon='DefaultRecentlyAddedEpisodes.png', fanart='DefaultRecentlyAddedEpisodes.png'),
                video_dict=dict(),
            ))

        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content, cache=False)

    def show_offline(self, page=0, use_favorites=False):
        ''' The VRT NU add-on 'Soon offline' and 'My soon offline' listing menu '''
        page = statichelper.realpage(page)
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(page=page, use_favorites=use_favorites, variety='offline')

        # Add 'More...' entry at the end
        if len(episode_items) == 50:
            episode_items.append(TitleItem(
                title=self._kodi.localize(30300),
                url_dict=dict(action=actions.LISTING_OFFLINE, page=page + 1, use_favorites=use_favorites),
                is_playable=False,
                art_dict=dict(thumb='DefaultYear.png', icon='DefaultYear.png', fanart='DefaultYear.png'),
                video_dict=dict(),
            ))

        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content)

    def search(self, search_string=None, page=None):
        ''' The VRT NU add-on Search functionality and results '''
        page = statichelper.realpage(page)

        if search_string is None:
            search_string = self._kodi.get_search_string()

        if not search_string:
            self._kodi.end_of_directory()
            return

        search_items, sort, ascending, content = self._apihelper.search(search_string, page=page)
        if not search_items:
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30098), message=self._kodi.localize(30099).format(keywords=search_string))
            self._kodi.end_of_directory()
            return

        # Add 'More...' entry at the end
        if len(search_items) == 50:
            search_items.append(TitleItem(
                title=self._kodi.localize(30300),
                url_dict=dict(action=actions.SEARCH, query=search_string, page=page + 1),
                is_playable=False,
                art_dict=dict(thumb='DefaultAddonSearch.png', icon='DefaultAddonSearch.png', fanart='DefaultAddonSearch.png'),
                video_dict=dict(),
            ))

        self._kodi.container_update(replace=True)
        self._kodi.show_listing(search_items, sort=sort, ascending=ascending, content=content, cache=False)

    def play(self, params):
        ''' A wrapper for playing video items '''
        _tokenresolver = tokenresolver.TokenResolver(self._kodi)
        _streamservice = streamservice.StreamService(self._kodi, _tokenresolver)
        stream = _streamservice.get_stream(params)
        if stream is not None:
            self._kodi.play(stream)
