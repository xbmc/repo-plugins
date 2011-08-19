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
from xbmcswift import Plugin, download_page
from BeautifulSoup import BeautifulSoup as BS
from urlparse import urljoin

__plugin_name__ = 'Khan Academy'
__plugin_id__ = 'plugin.video.khanacademy'

plugin = Plugin(__plugin_name__, __plugin_id__, __file__)

BASE_URL = 'http://www.khanacademy.org'
def full_url(path):
    return urljoin(BASE_URL, path)

def htmlify(url):
    return BS(download_page(url))

# Default View
@plugin.route('/')
def show_subjects():
    '''Displays subjects from the homepage.'''
    html = htmlify(BASE_URL)
    container = html.find('div', {'id': 'library-content-main'})
    subjects = container.findAll('div', {'data-role': 'page'})

    items = [{
        'label': s.h2.string,
        'url': plugin.url_for('show_videos', subject_id=s['id']),
    } for s in subjects]
    
    return plugin.add_items(items)

@plugin.route('/videos/<subject_id>/')
def show_videos(subject_id):
    '''Displays lessons for a give subject id.'''
    html = htmlify(BASE_URL)
    subject = html.find('div', {'id': subject_id})
    videos = subject.findAll('a', {'class': 'vl'})

    items =  [{
        'label': a.span.string,
        'url': plugin.url_for('play_video', url=full_url(a['href'])),
        'is_playable': True,
        'is_folder': False,
    } for a in videos]

    return plugin.add_items(items)

@plugin.route('/play/<url>/')
def play_video(url):
    '''Resolves a lesson page's url to a playable video url.'''
    # Videos are both in .mp4 format and youtube. For simplicity's sake just
    # use mp4 for now.
    html = htmlify(url)
    a = html.find('a', {'title': 'Download this lesson'})
    plugin.set_resolved_url(a['href'])


if __name__ == '__main__': 
    plugin.run()
