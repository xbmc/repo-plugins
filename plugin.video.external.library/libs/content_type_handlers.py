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
"""Classes that are responsible for processing supported content types: Movies, TV Shows etc."""

import enum
from typing import Type, List, Dict, Any, Optional, Tuple, Iterable
from urllib.parse import urljoin, quote

import xbmcplugin

from libs import json_rpc_api
from libs.kodi_service import GettextEmulator, get_remote_kodi_url, ADDON_ID, ADDON, get_plugin_url

__all__ = [
    'MoviesHandler',
    'RecentMoviesHandler',
    'TvShowsHandler',
    'SeasonsHandler',
    'EpisodesHandler',
    'RecentEpisodesHandler',
]

_ = GettextEmulator.gettext

REMOTE_KODI_URL = get_remote_kodi_url(with_credentials=True)
VIDEO_URL = urljoin(REMOTE_KODI_URL, 'vfs')


# pylint: disable=unused-argument
class BaseContentTypeHandler:
    mediatype: str
    item_is_folder: bool
    should_save_to_mem_storage: bool
    api_class: Type[json_rpc_api.BaseMediaItemsRetriever]

    def __init__(self, tvshowid: Optional[int] = None,
                 season: Optional[int] = None,
                 parent_category: Optional[str] = None):
        self._tvshowid = tvshowid
        self._season = season
        self._parent_category = parent_category
        self._api = self.api_class(self.content, self._tvshowid, self._season)

    @property
    def content(self) -> str:
        return f'{self.mediatype}s'

    def get_media_items(self) -> Iterable[Dict[str, Any]]:
        yield from self._api.get_media_items()

    def get_plugin_category(self) -> str:
        raise NotImplementedError

    def get_item_url(self, media_info: Dict[str, Any]) -> str:
        raise NotImplementedError

    def get_item_context_menu(self, media_info: Dict[str, Any]) -> List[Tuple[str, str]]:
        return []

    def get_sort_methods(self) -> List[int]:
        return [
            xbmcplugin.SORT_METHOD_TITLE_IGNORE_THE,
            xbmcplugin.SORT_METHOD_TITLE,
            xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE,
            xbmcplugin.SORT_METHOD_LABEL,
            xbmcplugin.SORT_METHOD_VIDEO_YEAR,
            xbmcplugin.SORT_METHOD_COUNTRY,
            xbmcplugin.SORT_METHOD_STUDIO,
            xbmcplugin.SORT_METHOD_GENRE,
            xbmcplugin.SORT_METHOD_MPAA_RATING,
            xbmcplugin.SORT_METHOD_PLAYCOUNT,
        ]


class PlayableContentMixin:
    item_is_folder = False
    should_save_to_mem_storage = True

    def get_item_context_menu(self, media_info: Dict[str, Any]) -> List[Tuple[str, str]]:
        if media_info['playcount']:
            caption = f'[COLOR=yellow][B]{_("Mark as unwatched")}[/B][/COLOR]'
            playcount_to_set = 0
        else:
            caption = f'[COLOR=green][B]{_("Mark as watched")}[/B][/COLOR]'
            playcount_to_set = 1
        item_id_param = f'{self.mediatype}id'
        item_id = media_info[item_id_param]
        command = f'RunScript({ADDON_ID},' \
                  f'update_playcount,{item_id_param},{item_id},{playcount_to_set})'
        return [(caption, command)]

    def get_item_url(self, media_info: Dict[str, Any]) -> str:
        if ADDON.getSettingBool('files_on_shares'):
            return media_info['file']
        return f'{VIDEO_URL}/{quote(media_info["file"])}'


class MoviesHandler(PlayableContentMixin, BaseContentTypeHandler):
    mediatype = 'movie'
    api_class = json_rpc_api.GetMovies

    def get_plugin_category(self) -> str:
        return _('Movies')


class RecentMoviesHandler(MoviesHandler):
    api_class = json_rpc_api.GetRecentlyAddedMovies

    def get_plugin_category(self) -> str:
        return _('Recently added movies')

    def get_sort_methods(self) -> List[int]:
        return []


class TvShowsHandler(BaseContentTypeHandler):
    mediatype = 'tvshow'
    item_is_folder = True
    should_save_to_mem_storage = False
    api_class = json_rpc_api.GetTVShows

    class FlattenSeasons(enum.IntEnum):
        NEVER = 0
        IF_ONE_SEASON = 1
        ALWAYS = 2

    def get_plugin_category(self) -> str:
        return _('TV Shows')

    def get_media_items(self) -> Iterable[Dict[str, Any]]:
        for media_item in super().get_media_items():
            if media_item['episode']:
                yield media_item

    def get_item_url(self, media_info: Dict[str, Any]) -> str:
        parent_category = media_info.get('title') or media_info['label']
        tvshowid = media_info['tvshowid']
        if ADDON.getSettingInt('flatten_seasons') == self.FlattenSeasons.ALWAYS:
            return get_plugin_url(content_type='episodes', tvshowid=tvshowid,
                                  parent_category=parent_category)
        if ADDON.getSettingInt('flatten_seasons') == self.FlattenSeasons.IF_ONE_SEASON:
            if media_info['season'] == 1:
                return get_plugin_url(content_type='episodes', tvshowid=tvshowid,
                                      parent_category=parent_category)
        return get_plugin_url(content_type='seasons', tvshowid=tvshowid,
                              parent_category=parent_category)


class SeasonsHandler(BaseContentTypeHandler):
    mediatype = 'season'
    item_is_folder = True
    should_save_to_mem_storage = False
    api_class = json_rpc_api.GetSeasons

    def get_plugin_category(self) -> str:
        return f'{self._parent_category} / {_("Seasons")}'

    def get_item_url(self, media_info: Dict[str, Any]) -> str:
        season_title = media_info.get('title') or media_info['label']
        parent_category = f'{media_info["showtitle"]} / {season_title}'
        return get_plugin_url(content_type='episodes', tvshowid=media_info['tvshowid'],
                              season=media_info['season'], parent_category=parent_category)

    def get_sort_methods(self) -> List[int]:
        return [
            xbmcplugin.SORT_METHOD_TITLE,
            xbmcplugin.SORT_METHOD_LABEL,
            xbmcplugin.SORT_METHOD_PLAYCOUNT,
        ]


class EpisodesHandler(PlayableContentMixin, BaseContentTypeHandler):
    mediatype = 'episode'
    api_class = json_rpc_api.GetEpisodes

    def get_plugin_category(self) -> str:
        return self._parent_category

    def get_sort_methods(self) -> List[int]:
        return [
            xbmcplugin.SORT_METHOD_EPISODE,
            xbmcplugin.SORT_METHOD_DATE,
        ] + super().get_sort_methods()


class RecentEpisodesHandler(EpisodesHandler):
    api_class = json_rpc_api.GetRecentlyAddedEpisodes

    def get_plugin_category(self) -> str:
        return _('Recently added episodes')

    def get_sort_methods(self) -> List[int]:
        return []


class MusicVideosHandler(PlayableContentMixin, BaseContentTypeHandler):
    mediatype = 'musicvideo'
    api_class = json_rpc_api.GetMusicVideos

    def get_plugin_category(self) -> str:
        return _('Music videos')

    def get_sort_methods(self) -> List[int]:
        return [
            xbmcplugin.SORT_METHOD_ALBUM,
            xbmcplugin.SORT_METHOD_ARTIST,
            xbmcplugin.SORT_METHOD_ARTIST_IGNORE_THE,
            xbmcplugin.SORT_METHOD_TRACKNUM,
        ] + super().get_sort_methods()


class RecentMusicVideosHandler(MusicVideosHandler):
    api_class = json_rpc_api.GetRecentlyAddedMusicVideos

    def get_plugin_category(self) -> str:
        return _('Recently added music videos')

    def get_sort_methods(self) -> List[int]:
        return []
