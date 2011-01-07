#!/usr/bin/env python
# Copyright 2011 Jonathan Beluch. 
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
Classic Cinema XBMC Plugin

Watch movies found on http://www.classiccinemaonline.com

author:         Jonathan Beluch
project url:    https://github.com/jbeluch/xbmc-classic-cinema
git url:        git://github.com/jbeluch/xbmc-classic-cinema.git
version:        0.7.1

Please report any issues at https://github.com/jbeluch/xbmc-classic-cinema/issues
'''

from resources.lib.xbmcvideoplugin import XBMCVideoPlugin, XBMCVideoPluginHandler
from resources.lib.xbmccommon import (urlread, async_urlread, DialogProgress, 
    parse_url_qs, XBMCVideoPluginException)
from urllib import urlencode
from BeautifulSoup import BeautifulSoup as BS, SoupStrainer as SS
import resources.lib.googlevideo as gv
import re
import urlparse
try:
    import json
except ImportError:
    import simplejson as json

PLUGIN_NAME = 'Classic Cinema'
PLUGIN_ID = 'plugin.video.classiccinema'

class BasePluginHandler(XBMCVideoPluginHandler):
    base_url = 'http://www.classiccinemaonline.com'
    genres_url = 'http://www.classiccinemaonline.com/1/index.php'

    def urljoin(self, path):
        return urlparse.urljoin(self.base_url, path)


class DisplayGenresHandler(BasePluginHandler):
    '''Handler for parsing genres from http://www.classiccinemaonline.com/1/index.php'''
    def run(self):
        src = urlread(self.genres_url)
        #fix terrible html so beautiful soup doesn't barf
        src = src.replace('</font color>', '</font>')
        src = src.replace(r'<ol class=\"latestnews \">', '<ol class="latestnews">')

        div_tag =  BS(src, parseOnlyThese=SS('div', {'id': 'rightcol'}))
        dirs = [{'name': a.span.string.replace('&amp;', '&'),
                 'url': self.urljoin(a['href']).replace('&amp;', '&'),
                 'mode': '1'}
                 for a in div_tag.find('div', {'class': 'moduletable'})('a')]
        app.add_dirs(dirs)


class DisplayMoviesHandler(BasePluginHandler):
    '''Handler for parsing movies from a genre page.  
    
    Example genre url:
    http://www.classiccinemaonline.com/1/index.php?option=com_content&view=category&id=88&Itemid=760
    '''
    def run(self):
        # Initialize the progress dialog right away.  If we wait too long, then
        # the auto generated popup shows and it has the caption of 'Retrieving items....'
        self.dp = DialogProgress(app.getls(30010))

        # By default, classiccinema shows only 10 movies, so must send a POST request
        # to the same url, but include the id and limit parameters
        #POST data, limit=0 returns all items
        params = parse_url_qs(self.args['url'])
        data = {'id': params['id'], 'limit': '0'}
        src = urlread(self.args['url'], urlencode(data))

        tr_tags = BS(src, parseOnlyThese=SS('tr', {'class': re.compile('sectiontableentry')}))

        #urls for each of the movies pages
        urls = [self.urljoin(tr.a['href']) for tr in tr_tags]

        #get scraped info for each of the movie pages
        infos = self.parse_movie_pages(urls)

        #build dirs for sending to add_dirs()
        dirs = [{'name': info['info']['title'],
                 'url': url.replace('&amp;', '&'),
                 'tn': info.get('tn', ''),
                 'mode': '2',
                 'info': info['info']} for url, info in zip(urls, infos)]

        #filter dirs which don't have a url
        dirs = filter(lambda d: d['url'] != None, dirs)

        #sort dirs by name and add to UI
        sorted_dirs = sorted(dirs, key=lambda d: d['name'])
        app.add_resolvable_dirs(sorted_dirs)

    def parse_movie_pages(self, urls):
        self.dp.set_num_items(len(urls))
        srcs = async_urlread(urls, self.dp)
        return map(self.parse_movie_page, srcs)

    def parse_movie_page(self, src):
        '''Scrapes a movie page and returns a dict with info'''
        #results dict
        res = {'info': {}} 

        #get <meta> tags and parse title and description
        meta_tags = BS(src, parseOnlyThese=SS('meta'))

        #set default title so the UI listitem isn't blank if we don't match anything
        res['info']['title'] = app.getls(30011) 

        #attempt to parse title and year if it exists
        title_year = meta_tags.find('meta', {'name': 'title'})
        if title_year:
            #set title to the entire content attribute of the meta tag in case
            #we don't match a title and a year below
            res['info']['title'] = title_year['content']

            #attempt to match a title and a year:
            # 'The Lone Ranger (2004)'
            p = r'(?P<title>.+?)\((?P<year>\d+)\)'
            m = re.match(p, title_year['content'])
            if m:
                res['info']['title'] = m.group('title')
                res['info']['year'] =  int(m.group('year'))

        #attempt to parse the description meta tag if it exists
        description = meta_tags.find('meta', {'name': 'description'})
        if description:
            res['info']['plot'] = description['content']

        #get the poster image to use as thumbnail if available on page
        img_tags = BS(src, parseOnlyThese=SS('img', {'src': re.compile('/posters/')}))
        if len(img_tags) > 0:
            res['tn'] = self.urljoin(img_tags.find('img')['src'])

        return res

class PlayMovieHandler(BasePluginHandler):
    '''Handles playing of movies.  The site contains movies embedded from
    google video and archive.org.
    '''
    def get_googlevideo_url(self, src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        url = gv.get_flv_url(url=embed_tags.find('embed')['src'])
        if not url:
            raise XBMCVideoPluginException(app.getls(30013))
        return url

    def get_archive_url(self, src):
        embed_tags = BS(src, parseOnlyThese=SS('embed'))
        flashvars = embed_tags.find('embed')['flashvars']
        obj = json.loads(flashvars.split('=', 1)[1].replace("'", '"'))
        base_url = obj['clip']['baseUrl']
        path = obj['playlist'][1]['url'] 
        return urlparse.urljoin(base_url, path)

    def run(self):
        src = urlread(self.args['url'])

        #there are 2 kinds of videos on the site, google video and archive.org
        if src.find('googleplayer') > 0:
            url = self.get_googlevideo_url(src)
        elif src.find('flowplayer') > 0:
            url = self.get_archive_url(src) 
        else:
            raise XBMCVideoPluginException(app.getls(30012))

        app.set_resolved_url(url)

if __name__ == '__main__':
    settings = {'default_handler': DisplayGenresHandler,
                'plugin_id': PLUGIN_ID, 
                'plugin_name': PLUGIN_NAME}
    app = XBMCVideoPlugin(
        [('0', DisplayGenresHandler),
         ('1', DisplayMoviesHandler),
         ('2', PlayMovieHandler),
        ], **settings
    )
    app.run()
