# -*- coding: utf-8 -*-
""" Streamz API """

from __future__ import absolute_import, division, unicode_literals

API_ENDPOINT = 'https://lfvp-api.dpgmedia.net'

# These seem to be hardcoded
STOREFRONT_MAIN = 'eba52f64-92da-4fec-804b-278ebafc75fd'
STOREFRONT_MOVIES = '4f163159-15c3-452c-b275-1747b144cfa0'
STOREFRONT_SERIES = 'dba19d15-1ddf-49ef-8eb5-99c59a1fb377'
STOREFRONT_KIDS = 'a53d1ec3-ab43-4942-9d31-4f4754b4f519'
STOREFRONT_MAIN_KIDS = 'e0c175c0-a43c-4eed-bdca-e1e95a726bc0'


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

    def __init__(self, movie_id=None, name=None, description=None, year=None, cover=None, image=None, duration=None,
                 remaining=None, geoblocked=None, channel=None, legal=None, aired=None, my_list=None):
        """
        :type movie_id: str
        :type name: str
        :type description: str
        :type year: int
        :type cover: str
        :type image: str
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
        self.cover = cover
        self.image = image
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

    def __init__(self, program_id=None, name=None, description=None, cover=None, image=None, seasons=None,
                 geoblocked=None, channel=None, legal=None, my_list=None, content_hash=None):
        """
        :type program_id: str
        :type name: str
        :type description: str
        :type cover: str
        :type image: str
        :type seasons: dict[int, Season]
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        :type my_list: bool
        :type content_hash: str
        """
        self.program_id = program_id
        self.name = name
        self.description = description if description else ''
        self.cover = cover
        self.image = image
        self.seasons = seasons if seasons else {}
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal
        self.my_list = my_list
        self.content_hash = content_hash

    def __repr__(self):
        return "%r" % self.__dict__


class Season:
    """ Defines a Season """

    def __init__(self, number=None, episodes=None, cover=None, geoblocked=None, channel=None, legal=None):
        """
        :type number: str
        :type episodes: dict[int, Episode]
        :type cover: str
        :type geoblocked: bool
        :type channel: str
        :type legal: str
        """
        self.number = int(number)
        self.episodes = episodes if episodes else {}
        self.cover = cover
        self.geoblocked = geoblocked
        self.channel = channel
        self.legal = legal

    def __repr__(self):
        return "%r" % self.__dict__


class Episode:
    """ Defines an Episode """

    def __init__(self, episode_id=None, program_id=None, program_name=None, number=None, season=None, name=None,
                 description=None, cover=None, duration=None, remaining=None, geoblocked=None, channel=None, legal=None,
                 aired=None, progress=None, watched=False, next_episode=None):
        """
        :type episode_id: str
        :type program_id: str
        :type program_name: str
        :type number: int
        :type season: str
        :type name: str
        :type description: str
        :type cover: str
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
        self.number = int(number) if number else None
        self.season = int(season) if season else None
        if number:
            self.name = re.compile('^%d. ' % number).sub('', name)  # Strip episode from name
        else:
            self.name = name
        self.description = description if description else ''
        self.cover = cover
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

    def __init__(self, program=None, program_id=None, title=None, duration=None, url=None, license_url=None, subtitles=None, cookies=None):
        """
        :type program: str
        :type program_id: str
        :type title: str
        :type duration: str
        :type url: str
        :type license_url: str
        :type subtitles: list[str]
        :type cookies: dict
        """
        self.program = program
        self.program_id = program_id
        self.title = title
        self.duration = duration
        self.url = url
        self.license_url = license_url
        self.subtitles = subtitles
        self.cookies = cookies

    def __repr__(self):
        return "%r" % self.__dict__
