# -*- coding: utf-8 -*-
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""Implements a VRTPlayer class"""

from __future__ import absolute_import, division, unicode_literals
from apihelper import ApiHelper
from favorites import Favorites
from helperobjects import TitleItem
from kodiutils import (colour, delete_cached_thumbnail, end_of_directory, get_addon_info,
                       get_setting, get_setting_bool, has_credentials,
                       has_inputstream_adaptive, localize, kodi_version_major, log_error,
                       ok_dialog, play, set_setting, show_listing, ttl, url_for,
                       wait_for_resumepoints)
from resumepoints import ResumePoints
from utils import find_entry, realpage


class VRTPlayer:
    """An object providing all methods for Kodi menu generation"""

    def __init__(self):
        """Initialise object"""
        self._favorites = Favorites()
        self._resumepoints = ResumePoints()
        self._apihelper = ApiHelper(self._favorites, self._resumepoints)
        wait_for_resumepoints()

    def show_main_menu(self):
        """The VRT NU add-on main menu"""
        # self._favorites.refresh(ttl=ttl('indirect'))
        main_items = []

        # Only add 'My favorites' when it has been activated
        if self._favorites.is_activated():
            main_items.append(TitleItem(
                label=localize(30010),  # My favorites
                path=url_for('favorites_menu'),
                art_dict=dict(thumb='DefaultFavourites.png'),
                info_dict=dict(plot=localize(30011)),
            ))

        main_items.extend([
            TitleItem(label=localize(30012),  # All programs
                      path=url_for('programs'),
                      art_dict=dict(thumb='DefaultMovieTitle.png'),
                      info_dict=dict(plot=localize(30013))),
            TitleItem(label=localize(30014),  # Categories
                      path=url_for('categories'),
                      art_dict=dict(thumb='DefaultGenre.png'),
                      info_dict=dict(plot=localize(30015))),
            TitleItem(label=localize(30016),  # Channels
                      path=url_for('channels'),
                      art_dict=dict(thumb='DefaultTags.png'),
                      info_dict=dict(plot=localize(30017))),
            TitleItem(label=localize(30018),  # Live TV
                      path=url_for('livetv'),
                      art_dict=dict(thumb='DefaultTVShows.png'),
                      info_dict=dict(plot=localize(30019))),
            TitleItem(label=localize(30020),  # Recent items
                      path=url_for('recent'),
                      art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png'),
                      info_dict=dict(plot=localize(30021))),
            TitleItem(label=localize(30022),  # Soon offline
                      path=url_for('offline'),
                      art_dict=dict(thumb='DefaultYear.png'),
                      info_dict=dict(plot=localize(30023))),
            TitleItem(label=localize(30024),  # Featured content
                      path=url_for('featured'),
                      art_dict=dict(thumb='DefaultCountry.png'),
                      info_dict=dict(plot=localize(30025))),
            TitleItem(label=localize(30026),  # TV guide
                      path=url_for('tvguide'),
                      art_dict=dict(thumb='DefaultAddonTvInfo.png'),
                      info_dict=dict(plot=localize(30027))),
            TitleItem(label=localize(30028),  # Search
                      path=url_for('search'),
                      art_dict=dict(thumb='DefaultAddonsSearch.png'),
                      info_dict=dict(plot=localize(30029))),
        ])
        show_listing(main_items, cache=False)  # No category
        self._version_check()

    def _version_check(self):
        first_run, settings_version, addon_version = self._first_run()
        if first_run:
            # 2.0.0 version: changed plugin:// url interface: show warning that Kodi favourites and what-was-watched will break
            if settings_version == '' and has_credentials():
                ok_dialog(localize(30978), localize(30979))

            if addon_version == '2.2.1':
                # 2.2.1 version: changed artwork: delete old cached artwork
                delete_cached_thumbnail(get_addon_info('fanart').replace('.png', '.jpg'))
                delete_cached_thumbnail(get_addon_info('icon'))
                # 2.2.1 version: moved tokens: delete old tokens
                from tokenresolver import TokenResolver
                TokenResolver().delete_tokens()

            # Make user aware that timeshift functionality will not work without ISA when user starts up the first time
            if settings_version == '' and kodi_version_major() > 17 and not has_inputstream_adaptive():
                ok_dialog(message=localize(30988))

    @staticmethod
    def _first_run():
        '''Check if this add-on version is run for the first time'''

        # Get version from settings.xml
        settings_version = get_setting('version', default='')

        # Get version from addon.xml
        addon_version = get_addon_info('version')

        # Compare versions (settings_version was not present in version 1.10.0 and older)
        settings_comp = tuple(map(int, settings_version.split('+')[0].split('.'))) if settings_version != '' else (1, 10, 0)
        addon_comp = tuple(map(int, addon_version.split('+')[0].split('.')))

        if addon_comp > settings_comp:
            # New version found, save addon version to settings
            set_setting('version', addon_version)
            return True, settings_version, addon_version

        return False, settings_version, addon_version

    def show_favorites_menu(self):
        """The VRT NU addon 'My programs' menu"""
        self._favorites.refresh(ttl=ttl('indirect'))
        favorites_items = [
            TitleItem(label=localize(30040),  # My programs
                      path=url_for('favorites_programs'),
                      art_dict=dict(thumb='DefaultMovieTitle.png'),
                      info_dict=dict(plot=localize(30041))),
            TitleItem(label=localize(30048),  # My recent items
                      path=url_for('favorites_recent'),
                      art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png'),
                      info_dict=dict(plot=localize(30049))),
            TitleItem(label=localize(30050),  # My soon offline
                      path=url_for('favorites_offline'),
                      art_dict=dict(thumb='DefaultYear.png'),
                      info_dict=dict(plot=localize(30051))),
        ]

        # Only add 'My watch later' and 'Continue watching' when it has been activated
        if self._resumepoints.is_activated():
            favorites_items.append(TitleItem(
                label=localize(30052),  # My watch later
                path=url_for('resumepoints_watchlater'),
                art_dict=dict(thumb='DefaultVideoPlaylists.png'),
                info_dict=dict(plot=localize(30053)),
            ))
            favorites_items.append(TitleItem(
                label=localize(30054),  # Continue Watching
                path=url_for('resumepoints_continue'),
                art_dict=dict(thumb='DefaultInProgressShows.png'),
                info_dict=dict(plot=localize(30055)),
            ))

        if get_setting_bool('addmymovies', default=True):
            favorites_items.append(
                TitleItem(label=localize(30042),  # My movies
                          path=url_for('categories', category='films'),
                          art_dict=dict(thumb='DefaultAddonVideo.png'),
                          info_dict=dict(plot=localize(30043))),
            )

        if get_setting_bool('addmydocu', default=True):
            favorites_items.append(
                TitleItem(label=localize(30044),  # My documentaries
                          path=url_for('favorites_docu'),
                          art_dict=dict(thumb='DefaultMovies.png'),
                          info_dict=dict(plot=localize(30045))),
            )

        if get_setting_bool('addmymusic', default=True):
            favorites_items.append(
                TitleItem(label=localize(30046),  # My music
                          path=url_for('favorites_music'),
                          art_dict=dict(thumb='DefaultAddonMusic.png'),
                          info_dict=dict(plot=localize(30047))),
            )

        show_listing(favorites_items, category=30010, cache=False)  # My favorites

        # Show dialog when no favorites were found
        if not self._favorites.programs():
            ok_dialog(heading=localize(30415), message=localize(30416))

    def show_favorites_docu_menu(self):
        """The VRT NU add-on 'My documentaries' listing menu"""
        self._favorites.refresh(ttl=ttl('indirect'))
        self._resumepoints.refresh(ttl=ttl('indirect'))
        episode_items, sort, ascending, content = self._apihelper.list_episodes(category='docu', season='allseasons', programtype='oneoff')
        show_listing(episode_items, category=30044, sort=sort, ascending=ascending, content=content, cache=False)

    def show_favorites_music_menu(self):
        """The VRT NU add-on 'My music' listing menu"""
        self._favorites.refresh(ttl=ttl('indirect'))
        self._resumepoints.refresh(ttl=ttl('indirect'))
        episode_items, sort, ascending, content = self._apihelper.list_episodes(category='muziek', season='allseasons', programtype='oneoff')
        show_listing(episode_items, category=30046, sort=sort, ascending=ascending, content=content, cache=False)

    def show_tvshow_menu(self, use_favorites=False):
        """The VRT NU add-on 'All programs' listing menu"""
        # My favorites menus may need more up-to-date favorites
        self._favorites.refresh(ttl=ttl('direct' if use_favorites else 'indirect'))
        self._resumepoints.refresh(ttl=ttl('direct' if use_favorites else 'indirect'))
        tvshow_items = self._apihelper.list_tvshows(use_favorites=use_favorites)
        show_listing(tvshow_items, category=30440, sort='label', content='tvshows')  # A-Z

    def show_category_menu(self, category=None):
        """The VRT NU add-on 'Categories' listing menu"""
        if category:
            self._favorites.refresh(ttl=ttl('indirect'))
            self._resumepoints.refresh(ttl=ttl('indirect'))
            tvshow_items = self._apihelper.list_tvshows(category=category)
            from data import CATEGORIES
            category_msgctxt = find_entry(CATEGORIES, 'id', category).get('msgctxt')
            show_listing(tvshow_items, category=category_msgctxt, sort='label', content='tvshows')
        else:
            category_items = self._apihelper.list_categories()
            show_listing(category_items, category=30014, sort='unsorted', content='files')  # Categories

    def show_channels_menu(self, channel=None):
        """The VRT NU add-on 'Channels' listing menu"""
        if channel:
            from tvguide import TVGuide
            self._favorites.refresh(ttl=ttl('indirect'))
            self._resumepoints.refresh(ttl=ttl('indirect'))
            channel_items = self._apihelper.list_channels(channels=[channel])  # Live TV
            channel_items.extend(TVGuide().get_channel_items(channel=channel))  # TV guide
            channel_items.extend(self._apihelper.list_youtube(channels=[channel]))  # YouTube
            channel_items.extend(self._apihelper.list_tvshows(channel=channel))  # TV shows
            from data import CHANNELS
            channel_name = find_entry(CHANNELS, 'name', channel).get('label')
            show_listing(channel_items, category=channel_name, sort='unsorted', content='tvshows', cache=False)  # Channel
        else:
            channel_items = self._apihelper.list_channels(live=False)
            show_listing(channel_items, category=30016, cache=False)

    def show_featured_menu(self, feature=None):
        """The VRT NU add-on 'Featured content' listing menu"""
        if feature:
            self._favorites.refresh(ttl=ttl('indirect'))
            self._resumepoints.refresh(ttl=ttl('indirect'))
            programs = None
            sort = 'label'
            content = 'tvshows'
            ascending = True
            if feature.startswith('jcr_'):
                media = self._apihelper.get_featured_media_from_web(feature.split('jcr_')[1])
                if media.get('mediatype') == 'episodes':
                    variety = 'featured.{name}'.format(name=media.get('name').strip().lower().replace(' ', '_'))
                    media_items, sort, ascending, content = self._apihelper.list_episodes(episode_id=media.get('medialist'), variety=variety)
                elif media.get('mediatype') == 'tvshows':
                    feature = None
                    media_items = self._apihelper.list_tvshows(feature=feature, programs=media.get('medialist'))
            else:
                media_items = self._apihelper.list_tvshows(feature=feature, programs=programs)
            from data import FEATURED
            feature_msgctxt = None
            feature = find_entry(FEATURED, 'id', feature)
            if feature:
                feature_msgctxt = feature.get('msgctxt')
            show_listing(media_items, category=feature_msgctxt, sort=sort, ascending=ascending, content=content, cache=False)
        else:
            featured_items = self._apihelper.list_featured()
            show_listing(featured_items, category=30024, sort='label', content='files')

    def show_livetv_menu(self):
        """The VRT NU add-on 'Live TV' listing menu"""
        channel_items = self._apihelper.list_channels()
        show_listing(channel_items, category=30018, cache=False)

    def show_episodes_menu(self, program, season=None):
        """The VRT NU add-on episodes listing menu"""
        self._favorites.refresh(ttl=ttl('indirect'))
        self._resumepoints.refresh(ttl=ttl('indirect'))
        episode_items, sort, ascending, content = self._apihelper.list_episodes(program=program, season=season)
        # FIXME: Translate program in Program Title
        show_listing(episode_items, category=program.title(), sort=sort, ascending=ascending, content=content, cache=False)

    def show_recent_menu(self, page=0, use_favorites=False):
        """The VRT NU add-on 'Most recent' and 'My most recent' listing menu"""

        # My favorites menus may need more up-to-date favorites
        self._favorites.refresh(ttl=ttl('direct' if use_favorites else 'indirect'))
        self._resumepoints.refresh(ttl=ttl('direct' if use_favorites else 'indirect'))
        episode_items, sort, ascending, content = self._apihelper.list_episodes(page=page, use_favorites=use_favorites, variety='recent')

        # Add 'More...' entry at the end
        recent = 'favorites_recent' if use_favorites else 'recent'
        episode_items.append(TitleItem(
            label=colour(localize(30300)),
            path=url_for(recent, page=realpage(page) + 1),
            art_dict=dict(thumb='DefaultRecentlyAddedEpisodes.png'),
            info_dict={},
        ))

        show_listing(episode_items, category=30020, sort=sort, ascending=ascending, content=content, cache=False)

    def show_offline_menu(self, page=0, use_favorites=False):
        """The VRT NU add-on 'Soon offline' and 'My soon offline' listing menu"""

        # My favorites menus may need more up-to-date favorites
        self._favorites.refresh(ttl=ttl('direct' if use_favorites else 'indirect'))
        self._resumepoints.refresh(ttl=ttl('direct' if use_favorites else 'indirect'))
        episode_items, sort, ascending, content = self._apihelper.list_episodes(page=page, use_favorites=use_favorites, variety='offline')

        # Add 'More...' entry at the end
        # if len(episode_items) == items_per_page:
        offline = 'favorites_offline' if use_favorites else 'offline'
        episode_items.append(TitleItem(
            label=localize(30300),
            path=url_for(offline, page=realpage(page) + 1),
            art_dict=dict(thumb='DefaultYear.png'),
            info_dict={},
        ))

        show_listing(episode_items, category=30022, sort=sort, ascending=ascending, content=content, cache=False)

    def show_watchlater_menu(self, page=0):
        """The VRT NU add-on 'My watch later' listing menu"""

        # My watch later menu may need more up-to-date favorites
        self._favorites.refresh(ttl=ttl('direct'))
        self._resumepoints.refresh(ttl=ttl('direct'))
        page = realpage(page)
        episode_items, sort, ascending, content = self._apihelper.list_episodes(page=page, variety='watchlater')
        show_listing(episode_items, category=30052, sort=sort, ascending=ascending, content=content, cache=False)

    def show_continue_menu(self, page=0):
        """The VRT NU add-on 'Continue waching' listing menu"""

        # Continue watching menu may need more up-to-date favorites
        self._favorites.refresh(ttl=ttl('direct'))
        self._resumepoints.refresh(ttl=ttl('direct'))
        page = realpage(page)
        episode_items, sort, ascending, content = self._apihelper.list_episodes(page=page, variety='continue')
        show_listing(episode_items, category=30054, sort=sort, ascending=ascending, content=content, cache=False)

    def play_latest_episode(self, program):
        """A hidden feature in the VRT NU add-on to play the latest episode of a program"""
        video = self._apihelper.get_latest_episode(program)
        if not video:
            log_error('Play latest episode failed, program {program}', program=program)
            ok_dialog(message=localize(30954))
            end_of_directory()
            return
        self.play(video)

    def play_episode_by_air_date(self, channel, start_date, end_date):
        """Play an episode of a program given the channel and the air date in iso format (2019-07-06T19:35:00)"""
        video = self._apihelper.get_episode_by_air_date(channel, start_date, end_date)
        if video and video.get('errorlabel'):
            ok_dialog(message=localize(30986, title=video.get('errorlabel')))
            end_of_directory()
            return
        if not video:
            log_error('Play episode by air date failed, channel {channel}, start_date {start}', channel=channel, start=start_date)
            ok_dialog(message=localize(30954))
            end_of_directory()
            return
        self.play(video)

    def play_episode_by_episode_id(self, episode_id):
        """Play an episode of a program given the episode_id"""
        video = self._apihelper.get_single_episode(episode_id=episode_id)
        if not video:
            log_error('Play episode by episode_id failed, episode_id {episode_id}', episode_id=episode_id)
            ok_dialog(message=localize(30954))
            end_of_directory()
            return
        self.play(video)

    def play_upnext(self, episode_id):
        """Play the next episode of a program by episode_id"""
        video = self._apihelper.get_single_episode(episode_id=episode_id)
        if not video:
            log_error('Play Up Next with episodeId {episode_id} failed', episode_id=episode_id)
            ok_dialog(message=localize(30954))
            end_of_directory()
            return
        self.play(video)

    @staticmethod
    def play(video):
        """A wrapper for playing video items"""
        from tokenresolver import TokenResolver
        from streamservice import StreamService
        _tokenresolver = TokenResolver()
        _streamservice = StreamService(_tokenresolver)
        stream = _streamservice.get_stream(video)
        if stream is None:
            end_of_directory()
            return
        play(stream, video.get('listitem'))
