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
from BeautifulSoup import BeautifulSoup as BS, SoupStrainer as SS
from urlparse import urljoin
from resources.lib.videohosts import resolve
import re

from resources.lib.favorites import favorites
from xbmcswift import xbmcgui

__plugin_name__ = 'New Academic Earth'
__plugin_id__ = 'plugin.video.academicearth'

plugin = Plugin(__plugin_name__, __plugin_id__, filepath=__file__)
plugin.register_module(favorites, '/favorites')

BASE_URL = 'http://academicearth.org'
def full_url(path):
    return urljoin(BASE_URL, path)

def htmlify(url):
    return BS(download_page(url), convertEntities=BS.HTML_ENTITIES)

def filter_free(items):
    return filter(lambda item: not item['label'].startswith('Online'), items)

@plugin.route('/')
def show_index():
    items = [
        {'label': plugin.get_string(30200), 'url': plugin.url_for('show_subjects')},
        {'label': plugin.get_string(30201), 'url': plugin.url_for('show_universities')},
        {'label': plugin.get_string(30202), 'url': plugin.url_for('show_instructors')},
        {'label': plugin.get_string(30203), 'url': plugin.url_for('show_top_instructors')},
        {'label': plugin.get_string(30204), 'url': plugin.url_for('show_playlists')},
        {'label': plugin.get_string(30205), 'url': plugin.url_for('favorites.show_favorites')},
    ]
    return plugin.add_items(items)

@plugin.route('/subjects/', url=full_url('subjects'))
def show_subjects(url):
    html = htmlify(url)
    subjects = html.findAll('a', {'class': 'subj-links'})

    items = [{
        'label': subject.div.string.strip(),
        'url': plugin.url_for('show_topics', url=full_url(subject['href'])),
    } for subject in subjects]

    # Filter out non-free subjects
    items = filter(lambda item: item['label'] != 'Courses for Credit', items)

    return plugin.add_items(items)

@plugin.route('/universities/', url=full_url('universities'))
def show_universities(url):
    html = htmlify(url)
    universities = html.findAll('a', {'class': 'subj-links'})

    items = [{
        'label': item.div.string.strip(),
        'url': plugin.url_for('show_topics', url=full_url(item['href'])),
    } for item in universities]

    return plugin.add_items(items)

@plugin.route('/instructors/', page='1')
@plugin.route('/instructors/<page>/', name='show_instructors_page')
def show_instructors(page):
    def get_pagination(html):
        items = []
        previous = html.find('span', {'class': 'tab-nav-arrow tab-nav-arrow-l'})
        if int(page) > 1:
            items.append({
                'label': '< Previous',
                'url': plugin.url_for('show_instructors_page', page=str(int(page)-1)),
            })

        next = html.find('span', {'class': 'tab-nav-arrow tab-nav-arrow-r'})
        if next:
            items.append({
                'label': 'Next >',
                'url': plugin.url_for('show_instructors_page', page=str(int(page)+1)),
            })
        return items

    url = full_url('speakers/page:%s' % page)
    html = htmlify(url)
    speakers = html.findAll('div', {'class': 'blue-hover'})

    items = [{
        'label': item.div.string,
        'url': plugin.url_for('show_instructor_courses', url=full_url(item.a['href'])),
    } for item in speakers]

    # Add pagination
    return plugin.add_items(get_pagination(html) + items)

@plugin.route('/topinstructors/', url=BASE_URL)
def show_top_instructors(url):
    html = htmlify(url)
    menu = html.find('ul', {'id': 'categories-accordion'})
    speakers = menu.findAll('a', {'class': 'accordion-item', 'href': lambda h: '/speakers/' in h})

    items = [{
        'label': item.string,
        'url': plugin.url_for('show_instructor_courses', url=full_url(item['href'])),
    } for item in speakers]

    return plugin.add_items(items)

@plugin.route('/playlists/', url=full_url('playlists'))
def show_playlists(url):
    html = htmlify(url)
    playlists = html.find('ol', {'class': 'playlist-list'}).findAll('li', recursive=False)

    items = [{
        'label': item.h4.findAll('a')[-1].string,
        'url': plugin.url_for('show_lectures', url=full_url(item.a['href'])),
        'thumbnail': full_url(item.find('img', {'width': '144'})['src']),
    } for item in playlists]

    return plugin.add_items(items)



@plugin.route('/instructors/courses/<url>/')
def show_instructor_courses(url):
    html = htmlify(url)
    parent_div = html.find('div', {'class': 'results-list'})
    courses_lectures = parent_div.findAll('li')

    courses = filter(lambda item: '/courses/' in item.h4.a['href'], courses_lectures)
    lectures = filter(lambda item: '/lectures/' in item.h4.a['href'], courses_lectures)

    course_items = [{
        'label': item.h4.a.string,
        'url': plugin.url_for('show_lectures', url=full_url(item.h4.a['href'])),
        'thumbnail': full_url(item.find('img', {'width': '144'})['src']),
    } for item in courses]

    lecture_items = [{
        'label': '%s: %s' % (plugin.get_string(30206), item.h4.a.string),
        'url': plugin.url_for('watch_lecture', url=full_url(item.h4.a['href'])),
        'thumbnail': full_url(item.find('img', {'class': 'thumb-144'})['src']),
        'is_folder': False,
        'is_playable': True,
    } for item in lectures]

    return plugin.add_items(course_items + lecture_items)

@plugin.route('/topics/<url>/')
def show_topics(url):
    html = htmlify(url)
    topics = html.findAll('a', {'class': 'tab-details-link '})

    items = [{
        'label': topic.string,
        'url': plugin.url_for('show_courses', url=full_url(topic['href'])),
    } for topic in topics]

    # Filter out non free topics
    items = filter_free(items)

    # If we only have one item, just redirect to the show_topics page,
    # there's no need to display a single item in the list
    if len(items) == 1:
        return plugin.redirect(items[0]['url'])

    return plugin.add_items(items)

@plugin.route('/courses/<url>/')
@plugin.route('/courses/<url>/<page>/', name='show_courses_page')
def show_courses(url, page='1'):
    def get_pagination(html):
        items = []
        if int(page) > 1:
            items.append({
                'label': '< Previous',
                'url': plugin.url_for('show_courses_page', url=url, page=str(int(page)-1)),
            })

        next = html.find('span', {'class': 'tab-nav-arrow tab-nav-arrow-r'})
        if next:
            items.append({
                'label': 'Next >',
                'url': plugin.url_for('show_courses_page', url=url, page=str(int(page)+1)),
            })
        return items

    html = htmlify('%s/page:%s' % (url, page))
    courses_lectures = html.findAll('div', {'class': 'thumb'})

    # Some of the results can be a standalone lecture, not a link to a course
    # page. We need to display these separately.
    courses = filter(lambda item: '/courses/' in item.a['href'], courses_lectures)
    lectures = filter(lambda item: '/lectures/' in item.a['href'], courses_lectures)

    course_items = [{
        'label': item.parent.find('a', {'class': 'editors-picks-title'}).string,
        'url': plugin.url_for('show_lectures', url=full_url(item.a['href'])),
        'thumbnail': full_url(item.find('img', {'class': 'thumb-144'})['src']),
    } for item in courses]

    lecture_items = [{
        'label': '%s: %s' % (plugin.get_string(30206),
            item.parent.find('a', {'class': 'editors-picks-title'}).string),
        'url': plugin.url_for('watch_lecture', url=full_url(item.a['href'])),
        'thumbnail': full_url(item.find('img', {'class': 'thumb-144'})['src']),
        'is_folder': False,
        'is_playable': True,
    } for item in lectures]

    pagination_items = get_pagination(html)
    return plugin.add_items(pagination_items + course_items + lecture_items)

@plugin.route('/lectures/<url>/')
def show_lectures(url):
    def get_plot(item):
        if item.p:
            return item.p.string
        return ''

    def get_add_to_favorites_url(item):
        path = item.find('a', {'class': 'add'})
        if path:
            return (plugin.get_string(30300), # Add to favorites
                    'XBMC.RunPlugin(%s)' % favorites.url_for(
                        'favorites.add_lecture',
                        url=full_url(path)['href']
            ))
        return

    html = htmlify(url)
    parent_div = html.find('div', {'class': 'results-list'})
    lectures = parent_div.findAll('li')

    items = [{
        'label': item.h4.a.string,
        'url': plugin.url_for('watch_lecture', url=full_url(item.h4.a['href'])),
        'thumbnail': full_url(item.find('img', {'class': 'thumb-144'})['src']),
        'is_folder': False,
        'is_playable': True,
        # Call to get_plot is because we are using this view to parse a course page
        # and also parse a playlist page. The playlist pages don't contain a lecture
        # description.
        'info': {'plot': get_plot(item)},
        'context_menu': [
            (plugin.get_string(30300), # Add to favorites
             'XBMC.RunPlugin(%s)' % favorites.url_for(
                'favorites.add_lecture',
                url=full_url(item.find('a', {'class': 'add'})['href'])
            )),
        ],

    } for item in lectures]

    return plugin.add_items(items)

@plugin.route('/watch/<url>/')
def watch_lecture(url):
    src = download_page(url)

    # First attempt to look for easy flv urls
    pattern = re.compile(r'flashVars.flvURL = "(.+?)"')
    m = pattern.search(src)
    if m:
        resolved_url = m.group(1)
    else:
        resolved_url = resolve(src)
    if resolved_url:
        return plugin.set_resolved_url(resolved_url)

    xbmcgui.Dialog().ok(plugin.get_string(30000), plugin.get_string(30400))
    raise Exception, 'No video url found. Please alert plugin author.'


if __name__ == '__main__':
    plugin.run()
