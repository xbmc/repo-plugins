# -*- coding: utf-8 -*-

# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Implements a VRTPlayer class '''

from __future__ import absolute_import, division, unicode_literals
from resources.lib import favorites, vrtapihelper
from resources.lib.helperobjects import TitleItem
from resources.lib.statichelper import realpage


class VRTPlayer:
    ''' An object providing all methods for Kodi menu generation '''

    def __init__(self, _kodi):
        ''' Initialise object '''
        self._kodi = _kodi
        self._favorites = favorites.Favorites(_kodi)
        self._apihelper = vrtapihelper.VRTApiHelper(_kodi, self._favorites)

    def show_main_menu_items(self):
        ''' The VRT NU add-on main menu '''
        self._favorites.get_favorites(ttl=60 * 60)
        main_items = []

        # Only add 'My programs' when it has been activated
        if self._favorites.is_activated():
            main_items.append(TitleItem(
                title=self._kodi.localize(30010),  # My programs
                path=self._kodi.url_for('favorites_menu'),
                art_dict=dict(thumb='icons/settings/profiles.png', fanart='icons/settings/profiles.png'),
                info_dict=dict(plot=self._kodi.localize(30011))
            ))

        main_items.extend([
            TitleItem(title=self._kodi.localize(30012),  # A-Z listing
                      path=self._kodi.url_for('programs'),
                      art_dict=dict(thumb='DefaultMovieTitle.png', fanart='DefaultMovieTitle.png'),
                      info_dict=dict(plot=self._kodi.localize(30013))),
            TitleItem(title=self._kodi.localize(30014),  # Categories
                      path=self._kodi.url_for('categories'),
                      art_dict=dict(thumb='DefaultGenre.png', fanart='DefaultGenre.png'),
                      info_dict=dict(plot=self._kodi.localize(30015))),
            TitleItem(title=self._kodi.localize(30016),  # Channels
                      path=self._kodi.url_for('channels'),
                      art_dict=dict(thumb='DefaultTags.png', fanart='DefaultTags.png'),
                      info_dict=dict(plot=self._kodi.localize(30017))),
            TitleItem(title=self._kodi.localize(30018),  # Live TV
                      path=self._kodi.url_for('livetv'),
                      # art_dict=dict(thumb='DefaultAddonPVRClient.png', fanart='DefaultAddonPVRClient.png'),
                      art_dict=dict(thumb='DefaultTVShows.png', fanart='DefaultTVShows.png'),
                      info_dict=dict(plot=self._kodi.localize(30019))),
            TitleItem(title=self._kodi.localize(30020),  # Recent items
                      path=self._kodi.url_for('recent'),
                      art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png', fanart='DefaultRecentlyAddedEpisodes.png'),
                      info_dict=dict(plot=self._kodi.localize(30021))),
            TitleItem(title=self._kodi.localize(30022),  # Soon offline
                      path=self._kodi.url_for('offline'),
                      art_dict=dict(thumb='DefaultYear.png', fanart='DefaultYear.png'),
                      info_dict=dict(plot=self._kodi.localize(30023))),
            TitleItem(title=self._kodi.localize(30024),  # Featured content
                      path=self._kodi.url_for('featured'),
                      art_dict=dict(thumb='DefaultCountry.png', fanart='DefaultCountry.png'),
                      info_dict=dict(plot=self._kodi.localize(30025))),
            TitleItem(title=self._kodi.localize(30026),  # TV guide
                      path=self._kodi.url_for('tvguide'),
                      art_dict=dict(thumb='DefaultAddonTvInfo.png', fanart='DefaultAddonTvInfo.png'),
                      info_dict=dict(plot=self._kodi.localize(30027))),
            TitleItem(title=self._kodi.localize(30028),  # Search
                      path=self._kodi.url_for('search'),
                      art_dict=dict(thumb='DefaultAddonsSearch.png', fanart='DefaultAddonsSearch.png'),
                      info_dict=dict(plot=self._kodi.localize(30029))),
        ])
        self._kodi.show_listing(main_items)

        # NOTE: In the future we can implement a LooseVersion check, now we can simply check if version is empty (pre-2.0.0)
        # from distutils.version import LooseVersion
        settings_version = self._kodi.get_setting('version', '')
        if settings_version == '' and self._kodi.has_credentials():  # New major version, favourites and what-was-watched will break
            self._kodi.show_ok_dialog(self._kodi.localize(30978), self._kodi.localize(30979))
        addon_version = self._kodi.get_addon_info('version')
        if settings_version != addon_version:
            self._kodi.set_setting('version', addon_version)

    def show_favorites_menu_items(self):
        ''' The VRT NU addon 'My Programs' menu '''
        self._favorites.get_favorites(ttl=60 * 60)
        favorites_items = [
            TitleItem(title=self._kodi.localize(30040),  # My A-Z listing
                      path=self._kodi.url_for('favorites_programs'),
                      art_dict=dict(thumb='DefaultMovieTitle.png', fanart='DefaultMovieTitle.png'),
                      info_dict=dict(plot=self._kodi.localize(30041))),
            TitleItem(title=self._kodi.localize(30046),  # My recent items
                      path=self._kodi.url_for('favorites_recent'),
                      art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png', fanart='DefaultRecentlyAddedEpisodes.png'),
                      info_dict=dict(plot=self._kodi.localize(30047))),
            TitleItem(title=self._kodi.localize(30048),  # My soon offline
                      path=self._kodi.url_for('favorites_offline'),
                      art_dict=dict(thumb='DefaultYear.png', fanart='DefaultYear.png'),
                      info_dict=dict(plot=self._kodi.localize(30049))),
        ]

        if self._kodi.get_setting('addmymovies', 'true') == 'true':
            favorites_items.append(
                TitleItem(title=self._kodi.localize(30042),  # My movies
                          path=self._kodi.url_for('categories', category='films'),
                          art_dict=dict(thumb='DefaultAddonVideo.png', fanart='DefaultAddonVideo.png'),
                          info_dict=dict(plot=self._kodi.localize(30043))),
            )

        if self._kodi.get_setting('addmydocu', 'true') == 'true':
            favorites_items.append(
                TitleItem(title=self._kodi.localize(30044),  # My documentaries
                          path=self._kodi.url_for('favorites_docu'),
                          art_dict=dict(thumb='DefaultMovies.png', fanart='DefaultMovies.png'),
                          info_dict=dict(plot=self._kodi.localize(30045))),
            )

        self._kodi.show_listing(favorites_items)

        # Show dialog when no favorites were found
        if not self._favorites.titles():
            self._kodi.show_ok_dialog(heading=self._kodi.localize(30415), message=self._kodi.localize(30416))

    def show_favorites_docu_menu_items(self):
        ''' The VRT NU add-on 'My documentaries' listing menu '''
        self._favorites.get_favorites(ttl=60 * 60)
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(category='docu', season='allseasons', programtype='oneoff')
        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content)

    def show_tvshow_menu_items(self, use_favorites=False):
        ''' The VRT NU add-on 'A-Z' listing menu '''
        # My programs menus may need more up-to-date favorites
        self._favorites.get_favorites(ttl=5 * 60 if use_favorites else 60 * 60)
        tvshow_items = self._apihelper.get_tvshow_items(use_favorites=use_favorites)
        self._kodi.show_listing(tvshow_items, sort='label', content='tvshows')

    def show_category_menu_items(self, category=None):
        ''' The VRT NU add-on 'Categories' listing menu '''
        if category:
            self._favorites.get_favorites(ttl=60 * 60)
            tvshow_items = self._apihelper.get_tvshow_items(category=category)
            self._kodi.show_listing(tvshow_items, sort='label', content='tvshows')
        else:
            category_items = self._apihelper.get_category_items()
            self._kodi.show_listing(category_items, sort='unsorted', content='files')

    def show_channels_menu_items(self, channel=None):
        ''' The VRT NU add-on 'Channels' listing menu '''
        if channel:
            self._favorites.get_favorites(ttl=60 * 60)
            # Add Live TV channel entry
            channel_item = self._apihelper.get_channel_items(channels=[channel])
            youtube_item = self._apihelper.get_youtube_items(channels=[channel])
            tvshow_items = self._apihelper.get_tvshow_items(channel=channel)
            self._kodi.show_listing(channel_item + youtube_item + tvshow_items, sort='unsorted', content='tvshows')
        else:
            channel_items = self._apihelper.get_channel_items(live=False)
            self._kodi.show_listing(channel_items, cache=False)

    def show_featured_menu_items(self, feature=None):
        ''' The VRT NU add-on 'Featured content' listing menu '''
        if feature:
            self._favorites.get_favorites(ttl=60 * 60)
            tvshow_items = self._apihelper.get_tvshow_items(feature=feature)
            self._kodi.show_listing(tvshow_items, sort='label', content='tvshows')
        else:
            featured_items = self._apihelper.get_featured_items()
            self._kodi.show_listing(featured_items, sort='label', content='files')

    def show_livestream_items(self):
        ''' The VRT NU add-on 'Live TV' listing menu '''
        channel_items = self._apihelper.get_channel_items()
        self._kodi.show_listing(channel_items, cache=False)

    def show_episodes(self, program, season=None):
        ''' The VRT NU add-on episodes listing menu '''
        self._favorites.get_favorites(ttl=60 * 60)
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(program=program, season=season)
        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content)

    def show_recent(self, page=0, use_favorites=False):
        ''' The VRT NU add-on 'Most recent' and 'My most recent' listing menu '''
        # My programs menus may need more up-to-date favorites
        self._favorites.get_favorites(ttl=5 * 60 if use_favorites else 60 * 60)
        page = realpage(page)
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(page=page, use_favorites=use_favorites, variety='recent')

        # Add 'More...' entry at the end
        if len(episode_items) == 50:
            if use_favorites:
                recent = 'favorites_recent'
            else:
                recent = 'recent'
            episode_items.append(TitleItem(
                title=self._kodi.localize(30300),
                path=self._kodi.url_for(recent, page=page + 1),
                art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png', fanart='DefaultRecentlyAddedEpisodes.png'),
                info_dict=dict(),
            ))

        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content, cache=False)

    def show_offline(self, page=0, use_favorites=False):
        ''' The VRT NU add-on 'Soon offline' and 'My soon offline' listing menu '''
        # My programs menus may need more up-to-date favorites
        self._favorites.get_favorites(ttl=5 * 60 if use_favorites else 60 * 60)
        page = realpage(page)
        episode_items, sort, ascending, content = self._apihelper.get_episode_items(page=page, use_favorites=use_favorites, variety='offline')

        # Add 'More...' entry at the end
        if len(episode_items) == 50:
            if use_favorites:
                offline = 'favorites_offline'
            else:
                offline = 'offline'
            episode_items.append(TitleItem(
                title=self._kodi.localize(30300),
                path=self._kodi.url_for(offline, page=page + 1),
                art_dict=dict(thumb='DefaultYear.png', fanart='DefaultYear.png'),
                info_dict=dict(),
            ))

        self._kodi.show_listing(episode_items, sort=sort, ascending=ascending, content=content)

    def play_latest_episode(self, program):
        ''' A hidden feature in the VRT NU add-on to play the latest episode of a program '''
        video = self._apihelper.get_latest_episode(program)
        if not video:
            self._kodi.log_error('Play latest episode failed, program %s' % program)
            self._kodi.show_ok_dialog(message=self._kodi.localize(30954))
            self._kodi.end_of_directory()
            return
        self.play(video)

    def play_episode_by_air_date(self, channel, start_date, end_date):
        ''' Play an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00) '''
        video = self._apihelper.get_episode_by_air_date(channel, start_date, end_date)
        if video and video.get('video_title'):
            self._kodi.show_ok_dialog(message=self._kodi.localize(30986) % video.get('video_title'))
            self._kodi.end_of_directory()
            return
        if not video:
            self._kodi.log_error('Play episode by air date failed, channel %s, start_date %s' % (channel, start_date))
            self._kodi.show_ok_dialog(message=self._kodi.localize(30954))
            self._kodi.end_of_directory()
            return
        self.play(video)

    def play(self, params):
        ''' A wrapper for playing video items '''
        from resources.lib import streamservice, tokenresolver
        _tokenresolver = tokenresolver.TokenResolver(self._kodi)
        _streamservice = streamservice.StreamService(self._kodi, _tokenresolver)
        stream = _streamservice.get_stream(params)
        if stream is not None:
            self._kodi.play(stream)
