# -*- coding: utf-8 -*-
""" VTM GO API """

from __future__ import absolute_import, division, unicode_literals

API_ENDPOINT = 'https://lfvp-api.dpgmedia.net'
API_ANDROID_ENDPOINT = 'https://lfvp-android-api.dpgmedia.net'

# These seem to be hardcoded
STOREFRONT_MAIN = 'main'
STOREFRONT_MOVIES = 'movies'
STOREFRONT_SHORTIES = 'shorties'
STOREFRONT_KIDS = 'kids'


class Profile:
    """ Defines a profile under your account. """

    def __init__(self, key=None, product=None, name=None, gender=None, birthdate=None, color=None, color2=None):
        """
        :type key: str
        :type product: str
        :type name: str
        :type gender: str
        :type birthdate: str
        :type color: str
        :type color2: str
        """
        self.key = key
        self.product = product
        self.name = name
        self.gender = gender
        self.birthdate = birthdate
        self.color = color
        self.color2 = color2

    def __repr__(self):
        return "%r" % self.__dict__


class LiveChannel:
    """ Defines a tv channel that can be streamed live """

    def __init__(self, key=None, channel_id=None, name=None, logo=None, background=None, epg=None, geoblocked=False):
        """
        :type key: str
        :type channel_id: str
        :type name: str
        :type logo: str
        :type background: str
        :type epg: list[LiveChannelEpg]
        :type geoblocked: bool
        """
        self.key = key
        self.channel_id = channel_id
        self.name = name
        self.logo = logo
        self.background = background
        self.epg = epg
        self.geoblocked = geoblocked

    def __repr__(self):
        return "%r" % self.__dict__


class LiveChannelEpg:
    """ Defines a program that is broadcast on a live tv channel"""

    def __init__(self, title=None, start=None, end=None):
        """
        :type title: str
        :type start: datetime.datetime
        :type end: datetime.datetime
        """
        self.title = title
        self.start = start
        self.end = end

    def __repr__(self):
        return "%r" % self.__dict__


class Category:
    """ Defines a category from the catalog """

    def __init__(self, category_id=None, title=None, content=None):
        """
        :type category_id: str
        :type title: str
        :type content: list[Union[Movie, Program, Episode]]
        """
        self.category_id = category_id
        self.title = title
        self.content = content

    def __repr__(self):
        return "%r" % self.__dict__


class Movie:
    """ Defines a Movie """

    def __init__(self, movie_id=None, name=None, description=None, year=None, poster=None, thumb=None, fanart=None, duration=None,
                 remaining=None, geoblocked=None, channel=None, legal=None, aired=None, my_list=None):
        """
        :type movie_id: str
        :type name: str
        :type description: str
        :type year: int
        :type poster: str
        :type thumb: str
        :type fanart: str
        :type duration: int
        :type remaining: str
        :type geoblocked: bool
        :type channel: Optional[str]
        :type legal: str
        :type aired: str
        :type my_list: bool
        """
        self.movie_id = movie_id
        self.name = name
        self.description = description if description else ''
        self.year = year
        self.poster = poster
        self.thumb = thumb
        self.fanart = fanart
        self.duration = duration
        self.remaining = remaining
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.aired = aired
        self.my_list = my_list

    def __repr__(self):
        return "%r" % self.__dict__


class Program:
    """ Defines a Program """

    def __init__(self, program_id=None, name=None, description=None, year=None, poster=None, thumb=None, fanart=None, seasons=None,
                 geoblocked=None, channel=None, legal=None, my_list=None):
        """
        :type program_id: str
        :type name: str
        :type description: str
        :type year: int
        :type poster: str
        :type thumb: str
        :type fanart: str
        :type seasons: dict[int, Season]
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        :type my_list: bool
        """
        self.program_id = program_id
        self.name = name
        self.description = description if description else ''
        self.year = year
        self.poster = poster
        self.thumb = thumb
        self.fanart = fanart
        self.seasons = seasons if seasons else {}
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.my_list = my_list

    def __repr__(self):
        return "%r" % self.__dict__


class Season:
    """ Defines a Season """

    def __init__(self, number=None, episodes=None, channel=None, legal=None):
        """
        :type number: str
        :type episodes: dict[int, Episode]
        :type channel: str
        :type legal: str
        """
        self.number = int(number)
        self.episodes = episodes if episodes else {}
        self.channel = channel
        self.legal = legal

    def __repr__(self):
        return "%r" % self.__dict__


class Episode:
    """ Defines an Episode """

    def __init__(self, episode_id=None, program_id=None, program_name=None, number=0, season=0, name=None, description=None, poster=None, thumb=None,
                 fanart=None, duration=None, remaining=None, geoblocked=None, channel=None, legal=None, aired=None, progress=None, watched=False,
                 next_episode=None):
        """
        :type episode_id: str
        :type program_id: str
        :type program_name: str
        :type number: int
        :type season: int
        :type name: str
        :type description: str
        :type poster: str
        :type thumb: str
        :type fanart: str
        :type duration: int
        :type remaining: int
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        :type aired: str
        :type progress: int
        :type watched: bool
        :type next_episode: Episode
        """
        import re
        self.episode_id = episode_id
        self.program_id = program_id
        self.program_name = program_name
        self.number = int(number)
        self.season = int(season)
        if number:
            self.name = re.compile('^%d. ' % number).sub('', name)  # Strip episode from name
        else:
            self.name = name
        self.description = description if description else ''
        self.poster = poster
        self.thumb = thumb
        self.fanart = fanart
        self.duration = int(duration) if duration else None
        self.remaining = int(remaining) if remaining is not None else None
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.aired = aired
        self.progress = progress
        self.watched = watched
        self.next_episode = next_episode

    def __repr__(self):
        return "%r" % self.__dict__


class ResolvedStream:
    """ Defines a stream that we can play"""

    def __init__(self, program=None, program_id=None, title=None, duration=None, url=None, license_key=None, subtitles=None, cookies=None):
        """
        :type program: str|None
        :type program_id: int|None
        :type title: str
        :type duration: str|None
        :type url: str
        :type license_key: str
        :type subtitles: list[str]
        :type cookies: dict
        """
        self.program = program
        self.program_id = program_id
        self.title = title
        self.duration = duration
        self.url = url
        self.license_key = license_key
        self.subtitles = subtitles
        self.cookies = cookies

    def __repr__(self):
        return "%r" % self.__dict__
