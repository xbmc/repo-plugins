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

from urllib2 import urlopen, HTTPError, URLError, unquote
import re

from BeautifulSoup import BeautifulSoup


class NetworkError(Exception):
    pass


class Scraper():

    MAIN_URL = 'http://www.videobash.com'

    CONTENT_TYPES = {
        'video': 'videos',
        'image': 'photos'
    }

    CATEGORIES = {
        'videos': (
            'All',
            'Animals',
            'Animation',
            'Cars',
            'Funny',
            'Music',
            'News-TV',
            'Pranks',
            'Science-Tech',
            'Sports',
            'Stand-Up',
        ),
        'photos': (
            'All',
            'Animals',
            'Cute Girls',
            'Funny',
            'Memes',
            'Motivational',
            'Other',
            'Wtf',
        )
    }

    SORT_METHODS = {
        'Most Recent': 'mr',
        'Top Rated': 'tr',
        'Most Viewed': 'mv'
    }

    TIME_PERIODS = {
        'All Time': '',
        'Daily': 'd',
        'Weekly': 'w',
        'Monthly': 'm'
    }

    def __init__(self, content_type='video'):
        self.set_content_type(content_type)

    def set_content_type(self, content_type):
        if not content_type in self.CONTENT_TYPES.keys():
            raise TypeError('Unknown content type: %s' % content_type)
        self.content_type = self.CONTENT_TYPES[content_type]

    def get_categories(self):
        categories = [{
            'title': category,
            'id': category.lower()
        } for category in self.CATEGORIES[self.content_type]]
        return categories

    def get_sort_methods(self):
        sort_methods = [{
            'title:': t,
            'id': i
        } for t, i in self.SORT_METHODS.iteritems()]
        return sort_methods

    def get_time_periods(self):
        time_periods = [{
            'title:': t,
            'id': i
        } for t, i in self.TIME_PERIODS.iteritems()]
        return time_periods

    def get_items(self, **kwargs):
        items = []
        url = self._build_url(**kwargs)
        tree = self._get_tree(url)
        li_re = re.compile('thumbs-video-wrapper')
        for li in tree.findAll('li', {'class': li_re}):
            img = li.find('img')
            items.append({
                'title': img['alt'],
                'thumb': img['src'],
                'id': self._generate_id(img.parent['href'])
            })
        has_next_page = tree.find('li', {'id': 'paginator_next'}) is not None
        return items, has_next_page

    def get_item_url(self, item_id):
        url = '%(main_url)s/%(content_type)s_show/%(item_id)s' % {
            'main_url': self.MAIN_URL,
            'content_type': self.content_type[0:-1],
            'item_id': item_id,
        }
        if self.content_type == 'photos':
            tree = self._get_tree(url)
            element = tree.find('img', {'id': 'imageContent'})
            return element['src']
        elif self.content_type == 'videos':
            html = self._get_url(url)
            re_video_url = re.compile('file=" \+ \'http://\' \+ \'(.+?)\';')
            file_param = re.search(re_video_url, html).group(1)
            return 'http://%s' % unquote(file_param)
        pass

    def _build_url(self, **kwargs):
        url = '%(main_url)s/%(content_type)s/%(category)s' % {
            'main_url': self.MAIN_URL,
            'content_type': self.content_type,
            'category': kwargs.get('category') or 'all'
        }
        if kwargs.get('sort_method') in self.SORT_METHODS.keys():
            url += '/%s' % self.SORT_METHODS[kwargs['sort_method']]
            if kwargs.get('time_period') in self.TIME_PERIODS.keys():
                url += '/%s' % self.TIME_PERIODS[kwargs['time_period']]
        if kwargs.get('page') and int(kwargs['page']) > 0:
            url += '?page=%d' % int(kwargs['page'])
        return url

    def _get_url(self, url):
        self.log('opening url: %s' % url)
        try:
            html = urlopen(url).read()
        except HTTPError, error:
            self.log('HTTPError: %s' % error)
            raise NetworkError('HTTPError: %s' % error)
        except URLError, error:
            self.log('URLError: %s' % error)
            raise NetworkError('URLError: %s' % error)
        self.log('got %d bytes' % len(html))
        return html

    def _get_tree(self, url):
        html = self._get_url(url)
        tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
        return tree

    @staticmethod
    def _generate_id(link):
        return link.split('/')[-1]

    @staticmethod
    def log(text):
        print 'Scraper: %s' % repr(text)

if __name__ == '__main__':
    scraper = Scraper()
    for content_type in ('videos', 'photos'):
        scraper.set_content_type(content_type)
        for category in scraper.get_categories():
            items, hnp = scraper.get_items(category=category['id'])
