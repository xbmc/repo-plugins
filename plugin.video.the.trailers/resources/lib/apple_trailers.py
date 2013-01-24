#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import os
import re
import time
from BeautifulSoup import BeautifulStoneSoup as BS
from urllib import unquote, urlencode
from urllib2 import urlopen, Request, HTTPError, URLError
from exceptions import NetworkError


class AppleTrailers(object):

    SOURCE_ID = 'apple'

    MAIN_URL = 'http://trailers.apple.com/trailers/home/xml/current.xml'
    MOVIE_URL = 'http://trailers.apple.com/moviesxml/s/%s/index.xml'
    BACKUP_MOVIE_URL='http://trailers.apple.com/trailers/%s/includes/playlists/web.inc'
    BACKUP_MOVIE_BASE='http://trailers.apple.com/trailers/%s/'
    '''
    TRAILER_QUALITIES = [{'title': 'iPod',
                          'id': 'i320.m4v'},
                         {'title': 'Small',
                          'id': 'h320.mov'},
                         {'title': 'Medium',
                          'id': 'h480.mov'},
                         {'title': 'Large',
                          'id': 'h640w.mov'},
                         {'title': 'HD480p',
                          'id': 'h480p.mov'},
                         {'title': 'HD720p',
                          'id': 'h720p.mov'},
                         {'title': 'HD1080p',
                          'id': 'h1080p.mov'}, ]
    '''
    TRAILER_QUALITIES = [{'title': 'iPod',
                          'id': 'i320.m4v'},
                         {'title': 'HD480p',
                          'id': 'h480p.mov'},
                         {'title': 'HD720p',
                          'id': 'h720p.mov'},
                         {'title': 'HD1080p',
                          'id': 'h1080p.mov'}, ]
    FILTER_CRITERIA = [
#        {'title': 'year',
#         'id': 'year'},
        {'title': 'genre',
         'id': 'genre'},
    ]

    UA = 'QuickTime/7.6.5 (qtver=7.6.5;os=Windows NT 5.1Service Pack 3)'

    def __init__(self, cache_path):
        self.cache_path = cache_path
        if not os.path.isdir(self.cache_path):
            os.makedirs(self.cache_path)
        self.movies = self.__get_movies()

    def get_movies(self, filters={}):
        if filters:
            filtered_movies = []
            for m in self.movies:
                match = True
                for field, content in filters.items():
                    match = match and content in m.get(field)
                if match:
                    filtered_movies.append(m)
            return filtered_movies
        else:
            return self.movies

    def get_single_movie(self, movie_title):
        movies = [m for m in self.movies if m['title'] == movie_title]
        if len(movies) == 1:
            return movies[0]
        else:
            raise Exception('Multiple or 0 matches in get_single_movie!')

    def get_filter_criteria(self):
        self.__log('get_filter_criteria')
        return self.FILTER_CRITERIA

    def get_filter_content(self, criteria):
        self.__log('get_filter_content started with criteria: %s' % criteria)
        assert criteria in self.FILTER_CRITERIA
        items = [{'title': content,
                  'id': content}
                 for content in self.__filter(self.movies, criteria)]
        return items

    def get_trailer_types(self, movie_title):
        self.__log('get_trailer_types started with movie_title: %s'
                   % movie_title)
        movie = self.get_single_movie(movie_title)
        url = self.MOVIE_URL % movie['movie_string']
        trailer_types = []
        try:
            cache_filename = '%s.xml' % movie['movie_string'].split('/')[1]
            tree = self.__get_tree(url, cache_filename=cache_filename)
            r_type = re.compile('/moviesxml/s/.+?/.+?/(.+?).xml')
            for t in tree.findAll('gotourl', {'target': 'main'}):
                if t.find('b'):
                    type_string = re.search(r_type, t['url']).group(1)
                    trailer_types.append({'title': t['draggingname'],
                                    'id': type_string})
        except:            
            t_url=self.BACKUP_MOVIE_URL % movie['movie_string']
            cache_filename='%swebinc.xml' % movie['movie_string'].split('/')[1] 
            tree=self.__get_tree(t_url,cache_filename=cache_filename)
            for t in tree.findAll('div',{'class':'column first'}):
                if t.find('h3'):
                    trailer_types.append({'title': t.find('h3').getText(),'id':t.find('h3').getText().lower().replace(" ","")})


        return trailer_types

    def get_trailer_qualities(self, movie_title):
        self.__log('get_trailer_qualities started with movie_title: %s'
                   % movie_title)
        return self.TRAILER_QUALITIES

    def get_trailer(self, movie_title, quality_id, trailer_type='trailer'):
        self.__log(('get_trailer started with movie_title: %s '
                    'trailer_type: %s quality_id: %s')
                    % (movie_title, trailer_type, quality_id))
        movie = self.get_single_movie(movie_title)
        url = self.MOVIE_URL % movie['movie_string']
        try:
            if trailer_type != 'trailer':
                url = url.replace('index', trailer_type)
            cache_filename = '%s-%s.xml' % (movie['movie_string'].split('/')[1],
                                            trailer_type)
            html = self.__get_url(url, cache_filename=cache_filename)
            r_section = re.compile('<array>(.*?)</array>', re.DOTALL)
            section = re.search(r_section, html).group(1)
            tree = BS(section, convertEntities=BS.XML_ENTITIES)
            trailers = []
            for s in tree.findAll('dict'):
                for k in s.findAll('key'):
                    if k.string == 'previewURL':
                        url = k.nextSibling.string
                        if quality_id in url:
                            return ('%s?|User-Agent=%s' % (url, self.UA))
        except:            
            url=self.BACKUP_MOVIE_BASE % movie['movie_string']
            tree = None
            if quality_id=='h480p.mov':
                cache=(movie['movie_string'].split('/')[1])+trailer_type+quality_id+'.xml'
                tree=self.__get_tree(url + 'itsxml/25-'+trailer_type+'.xml',cache_filename=cache)
            if quality_id=='h720p.mov':
                cache=(movie['movie_string'].split('/')[1])+trailer_type+quality_id+'.xml'
                tree=self.__get_tree(url + 'itsxml/26-'+trailer_type+'.xml',cache_filename=cache)
            if quality_id=='h1080p.mov':
                cache=(movie['movie_string'].split('/')[1])+trailer_type+quality_id+'.xml'
                tree=self.__get_tree(url + 'itsxml/27-'+trailer_type+'.xml',cache_filename=cache)
            for s in tree.findAll('dict'):
                for k in s.findAll('key'):                
                    if k.string == 'URL':
                        url = k.nextSibling.string
                        if quality_id in url:
                            return ('%s?|User-Agent=%s' % (url, self.UA))

    def __get_movies(self):
        self.__log('__get_movies started')
        url = self.MAIN_URL
        r_movie_string = re.compile('/trailers/(.+?)/images/')
        tree = self.__get_tree(url)
        movies = []
        for m in tree.findAll('movieinfo'):
            movie = {'movie_id': m.get('id'),
                     'title': m.title.string.replace(u'\u2019', '\''),
                     'duration': m.runtime.string,
                     'mpaa': m.rating.string,
                     'studio': m.studio.string,
                     'post_date': self.__format_date(m.postdate.string),
                     'release_date': self.__format_date(m.releasedate.string),
                     'year': self.__format_year(m.releasedate.string),
                     'copyright': m.copyright.string,
                     'director': m.director.string,
                     'plot': m.description.string,
                     'thumb': m.poster.xlarge.string, }
            if m.genre:
                movie['genre'] = [g.string.strip() for g in m.genre.contents]
            if m.cast:
                movie['cast'] = [c.string.strip() for c in m.cast.contents]
            movie_string = re.search(r_movie_string,
                                     m.poster.location.string).group(1)
            movie['movie_string'] = movie_string
            movies.append(movie)
        self.__log('get_movies finished with %d elements' % len(movies))
        return movies

    def __format_date(self, date_str):
        if date_str:
            y, m, d = date_str.split('-')
            return '.'.join((d, m, y, ))
        else:
            return ''

    def __format_year(self, date_str):
        if date_str:
            return date_str.split('-', 1)[0]
        else:
            return 0

    def __filter(self, ld, f):
        ll = [d[f] for d in ld if d.get(f)]
        if isinstance(ll[0], list):
            s = set([i for ll in ll for i in ll])
        else:
            s = set(ll)
        return sorted(s)

    def __get_tree(self, url, referer=None, cache_filename=None):
        html = self.__get_url(url, referer, cache_filename)
        tree = BS(html, convertEntities=BS.XML_ENTITIES)
        return tree

    def __get_url(self, url, referer=None, cache_filename=None):
        self.__log('__get_url started with url=%s, cache_filename=%s'
                   % (url, cache_filename))
        filename = cache_filename or url.rsplit('/')[-1]
        cache_file = os.path.join(self.cache_path, filename)
        try:
            cache_file_date = os.path.getmtime(cache_file)
        except:
            cache_file_date = 0
        if time.time() - 3600 > cache_file_date:
            self.__log('__get_url opening url: %s' % url)
            req = Request(url)
            if referer:
                req.add_header('Referer', referer)
            req.add_header('Accept', ('text/html,application/xhtml+xml,'
                                      'application/xml;q=0.9,*/*;q=0.8'))
            req.add_header('User-Agent', self.UA)
            try:
                html = urlopen(req).read()
            except HTTPError:
                raise NetworkError(HTTPError)
            except URLError:
                raise NetworkError(URLError)
            open(cache_file, 'w').write(html)
        else:
            self.__log('__get_url using cachefile: %s' % cache_file)
            html = open(cache_file, 'r').read()
        self.__log('__get_url got %d bytes' % len(html))
        return html

    def __log(self, msg):
        print('Apple scraper: %s' % msg)