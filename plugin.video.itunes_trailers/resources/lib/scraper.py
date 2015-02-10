#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2013 Tristan Fischer (sphere@dersphere.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from BeautifulSoup import BeautifulSoup, BeautifulStoneSoup
from email.utils import parsedate_tz
import json
import urllib2
import re

BASE_URL = 'http://trailers.apple.com/trailers'
COVER_BASE_URL = 'http://trailers.apple.com'
USER_AGENT = 'iTunes'


class NetworkError(Exception):
    pass


class MovieScraper(object):

    MOVIES_URL = BASE_URL + '/home/feeds/%s.json'

    def get_all_movies(self, limit, filter_dict=None):
        return self._get_movies('studios', limit, filter_dict)

    def get_most_popular_movies(self, limit, filter_dict=None):
        return self._get_movies('most_pop', limit, filter_dict)

    def get_exclusive_movies(self, limit, filter_dict=None):
        return self._get_movies('exclusive', limit, filter_dict)

    def get_most_recent_movies(self, limit, filter_dict=None):
        return self._get_movies('just_added', limit, filter_dict)

    def _get_movies(self, source, limit, filter_dict):

        def __poster(url):
            if not url.startswith('http'):
                url = COVER_BASE_URL + url
            return url.replace('poster', 'poster-xlarge')

        def __background(url):
            if not url.startswith('http'):
                url = COVER_BASE_URL + url
            return url.replace('poster', 'background')

        def __date(date_str):
            if date_str:
                d = parsedate_tz(date_str)
                return '%02d.%02d.%04d' % (d[2], d[1], d[0])
            return ''

        def __recent_date(t_list):
            d = max((parsedate_tz(d['postdate']) for d in t_list))
            return '%02d.%02d.%04d' % (d[2], d[1], d[0])

        def __location(loc_str):
            return '/'.join(loc_str.split('/')[2:4])

        def __types(t_list):
            return ', '.join(t['type'] for t in t_list)

        def __is_hd(t_list):
            return any(t for t in t_list if t.get('hd'))

        for i, movie in enumerate(self.__get_json(source)):
            if limit and i == limit:
                break
            if filter_dict:
                for criteria, content in filter_dict.items():
                    if not content in movie.get(criteria):
                        continue
            movie['background'] = __background(movie['poster'])
            movie['poster'] = __poster(movie['poster'])
            movie['releasedate'] = __date(movie.get('releasedate'))
            movie['postdate'] = __recent_date(movie['trailers'])
            movie['year'] = movie['releasedate'].split('.')[-1]
            movie['location'] = __location(movie['location'])
            movie['genre'] = ', '.join(movie.get('genre', []))
            movie['types'] = __types(movie['trailers'])
            movie['types_count'] = len(movie['trailers'])
            yield movie

    def __get_json(self, source):
        url = self.MOVIES_URL % source
        headers = {'User-Agent': USER_AGENT}
        req = urllib2.Request(url, None, headers)
        try:
            return json.load(urllib2.urlopen(req))
        except AttributeError:
            # json.load is only python >= 2.7
            return json.loads(urllib2.urlopen(req).read())
        except urllib2.HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)


class TrailerScraper(object):

    TRAILERS_URL = BASE_URL + '/%s/includes/playlists/web.inc'
    BACKGROUND_URL = BASE_URL + '/%s/images/background.jpg'
    PLAY_LIST_URL = BASE_URL + '/%s/itsxml/26-%s.xml'
    RE_URL = '<key>URL</key><string>(.+?)</string>'
    RE_DURATION = '<key>duration</key><integer>(.+?)</integer>'



    def get_trailers(self, location):

        def __thumb(url):
            if not url.startswith('http'):
                url = COVER_BASE_URL + url
            return url

        def __trailer_urls(trailer_url):
            return [trailer_url.replace('h720p', res)
                    for res in ('h480p', 'h720p', 'h1080p')]

        tree = self.__get_tree(self.TRAILERS_URL % location)
        for li in tree.findAll('li', {'class': re.compile('trailer')}):
            slug = li.find('h3').string.replace(' ', '').replace('-', '').lower()
            playlist = self.__get_url(self.PLAY_LIST_URL % (location, slug))
            trailer_url = re.search(self.RE_URL, playlist).group(1)
            duration = int(re.search(self.RE_DURATION, playlist).group(1)) / 1000
            trailer = {
                'title': li.find('h3').string,
                'date': '',
                'duration': duration,
                'thumb': __thumb(li.find('img')['src']),
                'background': self.BACKGROUND_URL % location,
                'urls': __trailer_urls(trailer_url)
            }
            yield trailer

    def __get_tree(self, url):
        return BeautifulSoup(self.__get_url(url))

    def __get_url(self, url):
        headers = {'User-Agent': USER_AGENT}
        req = urllib2.Request(url, None, headers)
        print 'Opening URL: %s' % url
        try:
            return urllib2.urlopen(req).read()
        except urllib2.HTTPError, error:
            print error
            raise NetworkError('HTTPError: %s' % error)


class MoviePlotScraper(object):

    MOVIES_URL = BASE_URL + '/home/xml/current.xml'

    def get_movie_plots(self):
        tree = self.__get_tree(self.MOVIES_URL)
        movie_plots = {}
        for movie in tree.findAll('movieinfo'):
            title = movie.find('info').find('title').string
            plot = movie.find('info').find('description').string
            movie_plots[title] = plot
        return movie_plots

    def __get_tree(self, url):
        headers = {'User-Agent': USER_AGENT}
        req = urllib2.Request(url, None, headers)
        print 'Opening URL: %s' % url
        try:
            return BeautifulStoneSoup(urllib2.urlopen(req).read())
        except urllib2.HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
