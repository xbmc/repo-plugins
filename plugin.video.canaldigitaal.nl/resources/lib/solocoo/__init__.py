# -*- coding: utf-8 -*-
""" Solocoo API """
from __future__ import absolute_import, division, unicode_literals

SOLOCOO_API = 'https://tvapi.solocoo.tv/v1'


class Channel:
    """ Channel Object """

    def __init__(self, uid, station_id, title, icon, preview, number, epg_now=None, epg_next=None, replay=False, radio=False, available=None, pin=None):
        """
        :param Epg epg_now:     The currently playing program on this channel.
        :param Epg epg_next:    The next playing program on this channel.
        """
        self.uid = uid
        self.station_id = station_id
        self.title = title
        self.icon = icon
        self.preview = preview
        self.number = number
        self.epg_now = epg_now
        self.epg_next = epg_next
        self.replay = replay
        self.radio = radio

        self.available = available
        self.pin = pin

    def __repr__(self):
        return "%r" % self.__dict__

    def get_combi_id(self):
        """ Return a combination of the uid and the station_id. """
        return "%s:%s" % (self.uid, self.station_id)


class StreamInfo:
    """ Stream information """

    def __init__(self, url, protocol, drm_protocol, drm_license_url, drm_certificate):
        self.url = url
        self.protocol = protocol
        self.drm_protocol = drm_protocol
        self.drm_license_url = drm_license_url
        self.drm_certificate = drm_certificate

    def __repr__(self):
        return "%r" % self.__dict__


class Epg:
    """ Program object """

    def __init__(self, uid, title, description, cover, preview, start, end, duration, channel_id, formats, genres, replay,
                 restart, age, series_id=None, season=None, episode=None, credit=None, available=None):
        """

        :type credit: list[Credit]
        """
        self.uid = uid
        self.title = title
        self.description = description
        self.cover = cover
        self.preview = preview
        self.start = start
        self.end = end
        self.duration = duration

        self.age = age
        self.channel_id = channel_id

        self.formats = formats
        self.genres = genres

        self.replay = replay
        self.restart = restart

        self.series_id = series_id
        self.season = season
        self.episode = episode

        self.credit = credit or []

        self.available = available

    def __repr__(self):
        return "%r" % self.__dict__


class EpgSeries:
    """ EpgSeries object """

    def __init__(self, uid, title, description, cover, preview, channel_id, formats, genres, age):
        self.uid = uid
        self.title = title
        self.description = description
        self.cover = cover
        self.preview = preview

        self.age = age
        self.channel_id = channel_id

        self.formats = formats
        self.genres = genres

    def __repr__(self):
        return "%r" % self.__dict__


class Credit:
    """ Credit object """

    ROLE_ACTOR = 'Actor'
    ROLE_COMPOSER = 'Composer'
    ROLE_DIRECTOR = 'Director'
    ROLE_GUEST = 'Guest'
    ROLE_PRESENTER = 'Presenter'
    ROLE_PRODUCER = 'Producer'

    def __init__(self, role, person, character=None):
        self.role = role
        self.person = person
        self.character = character

    def __repr__(self):
        return "%r" % self.__dict__


class VodCatalog:
    """ Catalog object for VOD """

    def __init__(self, uid, title, cover):
        self.uid = uid
        self.title = title
        self.cover = cover

    def __repr__(self):
        return "%r" % self.__dict__


class VodGenre:
    """ Genre object for VOD """

    GENRE_MAP = {
        "sg.ui.genre.actionadventure": "Action & Adventure",
        "sg.ui.genre.carsmotors": "Cars & Motors",
        "sg.ui.genre.factualentertainment": "Factual Entertainment",
        "sg.ui.genre.naturalhistory": "Natural History",
    }

    def __init__(self, uid, title, query):
        self.uid = uid
        self.title = title
        self.query = query

    @classmethod
    def map_label(cls, label):
        """ Map the label to a Genre """
        genre = cls.GENRE_MAP.get(label)
        if genre is not None:
            return genre

        # Fallback to something based on the id
        return label.split('.')[-1].title()

    def __repr__(self):
        return "%r" % self.__dict__


class VodMovie:
    """ Movie object for VOD """

    def __init__(self, uid, title, year, duration, age, cover, preview, credit=None, trailer=None, available=None):
        """

        :type credit: list[Credit]
        """
        self.uid = uid
        self.title = title
        self.year = year
        self.duration = duration
        self.age = age
        self.cover = cover
        self.preview = preview

        self.credit = credit or []
        self.trailer = trailer
        self.available = available

    def __repr__(self):
        return "%r" % self.__dict__


class VodSeries:
    """ Series object for VOD """

    def __init__(self, uid, title, year, age, cover, preview, credit=None, available=None):
        """

        :type credit: list[Credit]
        """
        self.uid = uid
        self.title = title
        self.year = year
        self.age = age
        self.cover = cover
        self.preview = preview

        self.credit = credit or []
        self.available = available

    def __repr__(self):
        return "%r" % self.__dict__


class VodSeason:
    """ Season object for VOD """

    def __init__(self, uid, title, query):
        """

        :type credit: list[Credit]
        """
        self.uid = uid
        self.title = title
        self.query = query

    def __repr__(self):
        return "%r" % self.__dict__


class VodEpisode:
    """ Episode object for VOD """

    def __init__(self, uid, title, year, duration, age, cover, preview, series_id, season, episode, credit=None):
        """

        :type credit: list[Credit]
        """
        self.uid = uid
        self.title = title
        self.year = year
        self.duration = duration
        self.age = age
        self.cover = cover
        self.preview = preview

        self.series_id = series_id
        self.season = season
        self.episode = episode

        self.credit = credit or []

    def __repr__(self):
        return "%r" % self.__dict__
