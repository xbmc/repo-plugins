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
"""Classes and functions responsible for interacting with the remote JSON-RPC API"""

import logging
from pprint import pformat
from typing import List, Dict, Any

from libs import simple_requests as requests
from libs.exceptions import NoDataError, RemoteKodiError
from libs.kodi_service import ADDON, get_remote_kodi_url

logger = logging.getLogger(__name__)


class BaseJsonRpcApi:
    kodi_url = get_remote_kodi_url(with_credentials=False)
    method: str

    def send_json_rpc(self):
        """
        Send JSON-RPC to remote Kodi
        """
        request = {
            'jsonrpc': '2.0',
            'method': self.method,
            'params': self.get_params(),
            'id': '1',
        }
        logger.debug('JSON-RPC request: %s', pformat(request))
        auth = None
        login = ADDON.getSetting('kodi_login')
        password = ADDON.getSetting('kodi_password')
        if login:
            auth = (login, password)
        try:
            json_reply = requests.post(self.kodi_url + '/jsonrpc', json=request,
                                       auth=auth, verify=False).json()
        except requests.RequestException as exc:
            raise RemoteKodiError(self.kodi_url) from exc
        logger.debug('JSON-RPC reply: %s', pformat(json_reply))
        return json_reply

    def get_params(self) -> Dict[str, Any]:
        """Get params to send to Kodi JSON-RPC API"""
        raise NotImplementedError


class BaseMediaItemsRetriever(BaseJsonRpcApi):
    properties: List[str]
    sort = Dict[str, str]

    def __init__(self, content, tvshowid=None, season=None):
        self._content = content
        self._tvshowid = tvshowid
        self._season = season

    def get_params(self) -> Dict[str, Any]:
        params = {
            'properties': self.properties,
            'sort': self.sort,
        }
        if self._tvshowid is not None:
            params['tvshowid'] = self._tvshowid
        if self._season is not None:
            params['season'] = self._season
        return params

    def get_media_items(self) -> List[Dict[str, Any]]:
        """
        Get the list of media items for Kodi database
        
        :raises: NoDataError when media items are not retrieved via JSON-RPC
        """
        try:
            return self.send_json_rpc()['result'][self._content]
        except KeyError as exc:
            raise NoDataError(
                f'Unable to retrieve {self._content} from remote media library') from exc


class GetMovies(BaseMediaItemsRetriever):
    method = 'VideoLibrary.GetMovies'
    properties = [
        'title',
        'genre',
        'year',
        'rating',
        'director',
        'trailer',
        'tagline',
        'plot',
        'plotoutline',
        'originaltitle',
        'playcount',
        'writer',
        'studio',
        'mpaa',
        'cast',
        'country',
        'streamdetails',
        'top250',
        'votes',
        'file',
        'sorttitle',
        'resume',
        'dateadded',
        'art',
        'premiered',
    ]
    sort = {'order': 'ascending', 'method': 'label'}


class GetRecentlyAddedMovies(GetMovies):
    method = 'VideoLibrary.GetRecentlyAddedMovies'
    sort = {'order': 'descending', 'method': 'dateadded'}


class GetTVShows(BaseMediaItemsRetriever):
    method = 'VideoLibrary.GetTVShows'
    properties = [
        'title',
        'genre',
        'year',
        'rating',
        'plot',
        'studio',
        'mpaa',
        'cast',
        'episode',
        'playcount',
        'premiered',
        'votes',
        'file',
        'originaltitle',
        'sorttitle',
        'season',
        'watchedepisodes',
        'dateadded',
        'tag',
        'art',
        'userrating',
        'ratings',
        'runtime',
        'uniqueid',
    ]
    sort = {'order': 'ascending', 'method': 'label'}


class GetSeasons(BaseMediaItemsRetriever):
    method = 'VideoLibrary.GetSeasons'
    properties = [
        'season',
        'showtitle',
        'playcount',
        'episode',
        'tvshowid',
        'watchedepisodes',
        'art',
        'title',
    ]
    sort = {'order': 'ascending', 'method': 'season'}


class GetEpisodes(BaseMediaItemsRetriever):
    method = 'VideoLibrary.GetEpisodes'
    properties = [
        'title',
        'plot',
        'votes',
        'rating',
        'writer',
        'firstaired',
        'playcount',
        'runtime',
        'director',
        'productioncode',
        'season',
        'episode',
        'originaltitle',
        'showtitle',
        'cast',
        'streamdetails',
        'file',
        'resume',
        'tvshowid',
        'dateadded',
        'uniqueid',
        'art',
        'specialsortseason',
        'specialsortepisode',
        'seasonid',
    ]
    sort = {'order': 'ascending', 'method': 'label'}


class GetRecentlyAddedEpisodes(GetEpisodes):
    method = 'VideoLibrary.GetRecentlyAddedEpisodes'
    sort = {'order': 'descending', 'method': 'dateadded'}


class GetMusicVideos(BaseMediaItemsRetriever):
    method = 'VideoLibrary.GetMusicVideos'
    properties = [
            'title',
            'playcount',
            'runtime',
            'director',
            'studio',
            'year',
            'plot',
            'album',
            'artist',
            'genre',
            'track',
            'streamdetails',
            'lastplayed',
            'file',
            'resume',
            'dateadded',
            'art',
            'rating',
            'premiered',
        ]
    sort = {'order': 'ascending', 'method': 'label'}


class GetRecentlyAddedMusicVideos(GetMusicVideos):
    method = 'VideoLibrary.GetRecentlyAddedMusicVideos'
    sort = {'order': 'descending', 'method': 'dateadded'}


class SetMovieDetails(BaseJsonRpcApi):
    method = 'VideoLibrary.SetMovieDetails'

    def __init__(self):
        super().__init__()
        self._params = None

    def get_params(self) -> Dict[str, Any]:
        return self._params

    def set_details(self, **kwargs):
        self._params = kwargs
        self.send_json_rpc()


class SetEpisodeDetails(SetMovieDetails):
    method = 'VideoLibrary.SetEpisodeDetails'


SET_DETAILS_API_MAP = {
    'movieid': SetMovieDetails,
    'episodeid': SetEpisodeDetails,
}


def update_playcount(item_id_param, item_id, playcount):
    api_class = SET_DETAILS_API_MAP[item_id_param]
    api = api_class()
    kwargs = {
        item_id_param: item_id,
        'playcount': playcount,
        'resume': {'position': 0.0, 'total': 0.0},
    }
    api.set_details(**kwargs)


def update_resume(item_id_param, item_id, position, total):
    api_class = SET_DETAILS_API_MAP[item_id_param]
    api = api_class()
    api.set_details(**{item_id_param: item_id, 'resume': {'position': position, 'total': total}})
