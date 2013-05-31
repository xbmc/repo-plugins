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

from BeautifulSoup import BeautifulSoup
from email.utils import parsedate_tz
import json
import urllib2
import re

BASE_URL = 'http://trailers.apple.com/trailers'
USER_AGENT = 'iTunes'


class NetworkError(Exception):
    pass


class MovieScraper(object):

    MOVIES_URL = BASE_URL + '/home/feeds/%s.json'
    COVER_BASE_URL = 'http://trailers.apple.com'

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
                url = self.COVER_BASE_URL + url
            return url.replace('poster', 'poster-xlarge')

        def __background(url):
            if not url.startswith('http'):
                url = self.COVER_BASE_URL + url
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
    OVERLAY_URL = BASE_URL + '/%s/includes/%s/extralarge.html'

    def get_trailers(self, location):
        tree = self.__get_tree(self.TRAILERS_URL % location)
        trailer_re = re.compile('trailer')
        for li in tree.findAll('li', {'class': trailer_re}):
            p_list = li.find('p').contents
            date_str, duration_str = p_list[0].strip(), p_list[-1].strip()
            if li.find('a', {'class': 'target-quicktimeplayer'}):
                section = li
            else:
                section = tree
            trailer_url_section = section.findAll(
                'a', {'class': 'target-quicktimeplayer'}
            )
            if trailer_url_section:
                trailer_urls = [
                    a['href'] for a in
                    trailer_url_section
                ]
            else:
                # This is hacky but also done by js on website...
                tname = li.find('h3').string.replace(' ', '').replace('-', '')
                trailer_tree = self.__get_tree(
                    self.OVERLAY_URL % (location, tname.lower())
                )
                resolution_gen_url = trailer_tree.find(
                    'a', {'class': 'movieLink'}
                )['href'].split('?')[0]
                trailer_urls = [
                    resolution_gen_url.replace('720p', res)
                    for res in ('h480p', 'h720p', 'h1080p')
                ]
            m, d, y = date_str.split()[1].split('/')
            trailer = {
                'title': li.find('h3').string,
                'date': '%s.%s.20%s' % (d, m, y),
                'duration': duration_str.split('Runtime:')[-1].strip(),
                'thumb': li.find('img')['src'],
                'background': self.BACKGROUND_URL % location,
                'urls': trailer_urls
            }
            yield trailer

    def __get_tree(self, url):
        headers = {'User-Agent': USER_AGENT}
        req = urllib2.Request(url, None, headers)
        print 'Opening URL: %s' % url
        try:
            return BeautifulSoup(urllib2.urlopen(req).read())
        except urllib2.HTTPError, error:
            raise NetworkError('HTTPError: %s' % error)
