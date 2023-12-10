# Copyright (C) 2023, Roman Miroshnychenko aka Roman V.M.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import sys
from urllib.parse import parse_qsl

import xbmcplugin
from xbmcgui import Dialog, ListItem

from libs.content_type_handlers import (
    MoviesHandler,
    RecentMoviesHandler,
    TvShowsHandler,
    SeasonsHandler,
    EpisodesHandler,
    RecentEpisodesHandler,
    MusicVideosHandler,
    RecentMusicVideosHandler,
)
from libs.exceptions import NoDataError, RemoteKodiError
from libs.kodi_service import ADDON, ADDON_ID, GettextEmulator, get_plugin_url
from libs.media_info_service import set_info, set_art
from libs.mem_storage import MemStorage

logger = logging.getLogger(__name__)
_ = GettextEmulator.gettext

HANDLE = int(sys.argv[1])

DIALOG = Dialog()

MEM_STORAGE = MemStorage()

CONTENT_TYPE_HANDLERS = {
    'movies': MoviesHandler,
    'recent_movies': RecentMoviesHandler,
    'tvshows': TvShowsHandler,
    'seasons': SeasonsHandler,
    'episodes': EpisodesHandler,
    'recent_episodes': RecentEpisodesHandler,
    'music_videos': MusicVideosHandler,
    'recent_music_videos': RecentMusicVideosHandler,
}


def root():
    """Root action"""
    xbmcplugin.setPluginCategory(HANDLE,
                                 _('Kodi Medialibrary on {kodi_host}').format(
                                     kodi_host=ADDON.getSettingString('kodi_host')))
    if ADDON.getSettingBool('show_movies'):
        list_item = ListItem(f'[{_("Movies")}]')
        list_item.setArt({'icon': 'DefaultMovies.png', 'thumb': 'DefaultMovies.png'})
        url = get_plugin_url(content_type='movies')
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
    if ADDON.getSettingBool('show_recent_movies'):
        list_item = ListItem(f'[{_("Recently added movies")}]')
        list_item.setArt({'icon': 'DefaultRecentlyAddedMovies.png',
                          'thumb': 'DefaultRecentlyAddedMovies.png'})
        url = get_plugin_url(content_type='recent_movies')
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
    if ADDON.getSettingBool('show_tvshows'):
        list_item = ListItem(f'[{_("TV Shows")}]')
        list_item.setArt({'icon': 'DefaultTVShows.png', 'thumb': 'DefaultTVShows.png'})
        url = get_plugin_url(content_type='tvshows')
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
    if ADDON.getSettingBool('show_recent_episodes'):
        list_item = ListItem(f'[{_("Recently added episodes")}]')
        list_item.setArt({'icon': 'DefaultRecentlyAddedEpisodes.png',
                          'thumb': 'DefaultRecentlyAddedEpisodes.png'})
        url = get_plugin_url(content_type='recent_episodes')
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
    if ADDON.getSettingBool('show_music_videos'):
        list_item = ListItem(f'[{_("Music videos")}]')
        list_item.setArt({'icon': 'DefaultMusicVideos.png', 'thumb': 'DefaultMusicVideos.png'})
        url = get_plugin_url(content_type='music_videos')
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
    if ADDON.getSettingBool('show_recent_music_videos'):
        list_item = ListItem(f'[{_("Recently added music videos")}]')
        list_item.setArt({'icon': 'DefaultRecentlyAddedMusicVideos.png',
                          'thumb': 'DefaultRecentlyAddedMusicVideos.png'})
        url = get_plugin_url(content_type='recent_music_videos')
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)


def show_media_items(content_type, tvshowid=None, season=None, parent_category=None):
    content_type_handler_class = CONTENT_TYPE_HANDLERS.get(content_type)
    if content_type_handler_class is None:
        raise RuntimeError(f'Unknown content type: {content_type}')
    content_type_handler = content_type_handler_class(tvshowid, season, parent_category)
    xbmcplugin.setPluginCategory(HANDLE, content_type_handler.get_plugin_category())
    xbmcplugin.setContent(HANDLE, content_type_handler.content)
    try:
        media_items = content_type_handler.get_media_items()
    except NoDataError:
        logger.exception('Unable to retrieve %s from the remote Kodi library',
                         content_type)
        DIALOG.notification(ADDON_ID, _('Unable to retrieve data from the remote Kodi library!'),
                            icon='error')
        return
    except RemoteKodiError as exc:
        logger.exception('Unable to connect to %s', str(exc))
        DIALOG.notification(ADDON_ID, _('Unable to connect to the remote Kodi host!'), icon='error')
        return
    logger.debug('Creating a list of %s items...', content_type)
    directory_items = []
    mem_storage_items = []
    for media_info in media_items:
        list_item = ListItem(media_info.get('title') or media_info.get('label', ''))
        if art := media_info.get('art'):
            set_art(list_item, art)
        info_tag = list_item.getVideoInfoTag()
        set_info(info_tag, media_info, content_type_handler.mediatype)
        list_item.addContextMenuItems(content_type_handler.get_item_context_menu(media_info))
        directory_items.append((
            content_type_handler.get_item_url(media_info),
            list_item,
            content_type_handler.item_is_folder,
        ))
        if content_type_handler.should_save_to_mem_storage:
            item_id_param = f'{content_type_handler.mediatype}id'
            mem_storage_items.append({
                'item_id_param': item_id_param,
                item_id_param: media_info[item_id_param],
                'file': media_info['file'],
                'playcount': media_info.get('playcount', 0),
            })
    xbmcplugin.addDirectoryItems(HANDLE, directory_items, len(directory_items))
    MEM_STORAGE[f'__{ADDON_ID}_media_list__'] = mem_storage_items
    for sort_method in content_type_handler.get_sort_methods():
        xbmcplugin.addSortMethod(HANDLE, sort_method)
    logger.debug('Finished creating a list of %s items.', content_type)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    logger.debug('Called addon with params: %s', str(sys.argv))
    if 'content_type' not in params:
        root()
    else:
        if (tvshowid := params.get('tvshowid')) is not None:
            tvshowid = int(tvshowid)
        if (season := params.get('season')) is not None:
            season = int(season)
        parent_category = params.get('parent_category')
        show_media_items(params['content_type'], tvshowid, season, parent_category)
    xbmcplugin.endOfDirectory(HANDLE)
