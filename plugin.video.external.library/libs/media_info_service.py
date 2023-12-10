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
"""
Classes and functions that process data from JSON-RPC API and assign them to ListItem instances
"""

from typing import Dict, Any, List, Tuple, Type, Iterable, Union
from urllib.parse import urljoin, quote

import xbmc
from xbmc import InfoTagVideo, Actor
from xbmcgui import ListItem

from libs.kodi_service import get_remote_kodi_url

__all__ = ['set_info', 'set_art']

REMOTE_KODI_URL = get_remote_kodi_url(with_credentials=True)
IMAGE_URL = urljoin(REMOTE_KODI_URL, 'image')

StreamDetailsType = Union[xbmc.VideoStreamDetail, xbmc.AudioStreamDetail, xbmc.SubtitleStreamDetail]


class SimpleMediaPropertySetter:
    """
    Sets a media property from a dictionary returned by JSON-RPC API to
    xbmc.InfoTagVideo class instance
    """

    def __init__(self, media_property: str, media_info: Dict[str, Any], info_tag_method: str):
        self._property_value = media_info.get(media_property)
        self._info_tag_method = info_tag_method

    def should_set(self) -> bool:
        return bool(self._property_value)

    def get_method_args(self) -> Iterable[Any]:
        return (self._property_value,)

    def set_info_tag_property(self, info_tag: InfoTagVideo) -> None:
        args = self.get_method_args()
        method = getattr(info_tag, self._info_tag_method)
        method(*args)


class NotNoneValueSetter(SimpleMediaPropertySetter):

    def should_set(self) -> bool:
        return self._property_value is not None


class CastSetter(SimpleMediaPropertySetter):

    def get_method_args(self) -> Iterable[Any]:
        actors = []
        for actor_info in self._property_value:
            actor_thumbnail = actor_info.get('thumbnail', '')
            if actor_thumbnail:
                actor_thumbnail = f'{IMAGE_URL}/{quote(actor_thumbnail)}'
            actors.append(Actor(
                name=actor_info.get('name', ''),
                role=actor_info.get('role', ''),
                order=actor_info.get('order') or -1,
                thumbnail=actor_thumbnail
            ))
        return (actors,)


class ResumePointSetter(SimpleMediaPropertySetter):

    def get_method_args(self) -> Iterable[Any]:
        time = self._property_value.get('position', 0.0)
        totaltime = self._property_value.get('total', 0.0)
        return time, totaltime


class VideoStreamSetter(SimpleMediaPropertySetter):
    stream_type = 'video'
    stream_type_class = xbmc.VideoStreamDetail

    def should_set(self) -> bool:
        return bool(self._property_value and self._property_value.get(self.stream_type))

    @staticmethod
    def get_stream_type_args(stream_dict: Dict[str, Any]) -> Iterable[Any,]:
        return (
            stream_dict['width'],
            stream_dict['height'],
            stream_dict['aspect'],
            stream_dict['duration'],
            stream_dict['codec'],
            stream_dict['stereomode'],
            stream_dict['language'],
            stream_dict['hdrtype'],
        )

    def _get_stream_type_object(self, stream_dict) -> StreamDetailsType:
        args = self.get_stream_type_args(stream_dict)
        return self.stream_type_class(*args)

    def get_method_args(self) -> Iterable[Any]:
        args_list = []
        for stream_dict in self._property_value[self.stream_type]:
            stream_type_obj = self._get_stream_type_object(stream_dict)
            args_list.append(stream_type_obj)
        return args_list

    def set_info_tag_property(self, info_tag: InfoTagVideo) -> None:
        method = getattr(info_tag, self._info_tag_method)
        args_list = self.get_method_args()
        for arg in args_list:
            method(arg)


class AudioStreamSetter(VideoStreamSetter):
    stream_type = 'audio'
    stream_type_class = xbmc.AudioStreamDetail

    @staticmethod
    def get_stream_type_args(stream_dict: Dict[str, Any]) -> Iterable[Any]:
        return (
            stream_dict['channels'],
            stream_dict['codec'],
            stream_dict['language'],
        )


class SubtitleStreamSetter(VideoStreamSetter):
    stream_type = 'subtitle'
    stream_type_class = xbmc.SubtitleStreamDetail

    @staticmethod
    def get_stream_type_args(stream_dict: Dict[str, Any]) -> Iterable[Any]:
        return (stream_dict['language'],)


class NonNegativeValueSetter(SimpleMediaPropertySetter):

    def should_set(self) -> bool:
        return self._property_value is not None and self._property_value >= 0


class IntAsStringValueSetter(SimpleMediaPropertySetter):

    def should_set(self) -> bool:
        return bool(self._property_value
                    and self._property_value.isdigit()
                    and int(self._property_value))

    def get_method_args(self) -> Iterable[Any]:
        return (int(self._property_value),)


# The list of 3 element tuples: (
#   media property name as returned by JSON-RPC call,
#   xbmc.InfoTagVideo method name,
#   media property handler class,
# )
MEDIA_PROPERTIES: List[Tuple[str, str, Type[SimpleMediaPropertySetter]]] = [
    ('title', 'setTitle', SimpleMediaPropertySetter),
    ('genre', 'setGenres', SimpleMediaPropertySetter),
    ('year', 'setYear', SimpleMediaPropertySetter),
    ('rating', 'setRating', SimpleMediaPropertySetter),
    ('director', 'setDirectors', SimpleMediaPropertySetter),
    ('trailer', 'setTrailer', SimpleMediaPropertySetter),
    ('tagline', 'setTagLine', SimpleMediaPropertySetter),
    ('plot', 'setPlot', SimpleMediaPropertySetter),
    ('plotoutline', 'setPlotOutline', SimpleMediaPropertySetter),
    ('playcount', 'setPlaycount', NotNoneValueSetter),
    ('writer', 'setWriters', SimpleMediaPropertySetter),
    ('studio', 'setStudios', SimpleMediaPropertySetter),
    ('mpaa', 'setMpaa', SimpleMediaPropertySetter),
    ('cast', 'setCast', CastSetter),
    ('country', 'setCountries', SimpleMediaPropertySetter),
    ('streamdetails', 'addVideoStream', VideoStreamSetter),
    ('streamdetails', 'addAudioStream', AudioStreamSetter),
    ('streamdetails', 'addSubtitleStream', SubtitleStreamSetter),
    ('top250', 'setTop250', SimpleMediaPropertySetter),
    ('votes', 'setVotes', IntAsStringValueSetter),
    ('sorttitle', 'setSortTitle', SimpleMediaPropertySetter),
    ('resume', 'setResumePoint', ResumePointSetter),
    ('dateadded', 'setDateAdded', SimpleMediaPropertySetter),
    ('premiered', 'setPremiered', SimpleMediaPropertySetter),
    ('season', 'setSeason', SimpleMediaPropertySetter),
    ('episode', 'setEpisode', SimpleMediaPropertySetter),
    ('showtitle', 'setTvShowTitle', SimpleMediaPropertySetter),
    ('productioncode', 'setProductionCode', SimpleMediaPropertySetter),
    ('specialsortseason', 'setSortSeason', NonNegativeValueSetter),
    ('specialsortepisode', 'setSortEpisode', NonNegativeValueSetter),
    ('album', 'setAlbum', SimpleMediaPropertySetter),
    ('artist', 'setArtists', SimpleMediaPropertySetter),
    ('track', 'setTrack', NonNegativeValueSetter),
]


def set_info(info_tag: InfoTagVideo, media_info: Dict[str, Any], mediatype: str) -> None:
    info_tag.setMediaType(mediatype)
    for media_property, info_tag_method, setter_class in MEDIA_PROPERTIES:
        setter = setter_class(media_property, media_info, info_tag_method)
        if setter.should_set():
            setter.set_info_tag_property(info_tag)


def set_art(list_item: ListItem, raw_art: Dict[str, str]) -> None:
    art = {art_type: f'{IMAGE_URL}/{quote(raw_url)}' for art_type, raw_url in raw_art.items()}
    list_item.setArt(art)
