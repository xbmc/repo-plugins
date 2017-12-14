###############################################################################
#
# MIT License
#
# Copyright (c) 2017 Lee Smith
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
###############################################################################

import traceback
# Workaround for 'Failed to import _strptime because the import lock is held by another thread.'
from datetime import datetime
import operator
import _strptime  # pylint: disable=unused-import

from kodiswift import Plugin

from resources.lib import api


PAGE_SIZE = 9

plugin = Plugin(addon_id='plugin.video.btsportvideo')


def categories():
    yield {'label': u'[B]{}[/B]'.format(plugin.get_string(30002)),
           'path': plugin.url_for('search')}
    yield {'label': u'[B]{}[/B]'.format(plugin.get_string(30001)),
           'path': plugin.url_for('show_videos_by_category_first_page', category='all')}
    for category in api.categories():
        yield {'label': category,
               'path': plugin.url_for('show_videos_by_category_first_page',
                                      category=category)}


def items(func, route, page, **kwargs):
    videos, npages = func(page=page, page_size=PAGE_SIZE, **kwargs)

    if page > 1:
        yield {
            'label': u'[B]<< {} ({})[/B]'.format(plugin.get_string(30003), page - 1),
            'path': plugin.url_for(route, page=page - 1, **kwargs)
        }
    if page < npages:
        yield {
            'label': u'[B]{} ({}) >> [/B]'.format(plugin.get_string(30004), page + 1),
            'path': plugin.url_for(route, page=page + 1, **kwargs)
        }

    for video in videos:
        yield {
            'label': video.title,
            'thumbnail': video.thumbnail,
            'path': video.url,
            'info': {
                'date': video.date.strftime('%d.%m.%Y'),
                'duration': video.duration
            },
            'is_playable': True
        }


def show_videos(func, route, page, update_listing, **kwargs):
    return plugin.finish(
        items(func, route, page, **kwargs),
        sort_methods=['playlist_order', 'date', 'title', 'duration'],
        update_listing=update_listing
    )


def previous_search_items():
    for search_term, _timestamp in sorted(plugin.get_storage('searches').items(),
                                          key=operator.itemgetter(1),
                                          reverse=True):
        yield {
            'label': search_term,
            'path': plugin.url_for('show_search_results_first_page', term=search_term)
        }


@plugin.cached_route('/')
def index():
    return list(categories())


@plugin.route('/videos/<category>', name='show_videos_by_category_first_page',
              options={'update_listing': False})
@plugin.route('/videos/<category>/<page>')
def show_videos_by_category(category, page='1', update_listing=True):
    return show_videos(api.videos, 'show_videos_by_category', int(page),
                       update_listing, category=category)


@plugin.route('/search/term/<term>', name='show_search_results_first_page',
              options={'update_listing': False})
@plugin.route('/search/term/<term>/<page>')
def show_search_results(term, page='1', update_listing=True):
    plugin.get_storage('searches')[term] = datetime.now()
    return show_videos(api.search_results, 'show_search_results', int(page),
                       update_listing, term=term)


@plugin.route('/search/input')
def new_search():
    term = plugin.keyboard(heading=plugin.get_string(30002))
    if term:
        url = plugin.url_for('show_search_results_first_page', term=term)
        plugin.request.url = url
        return plugin.redirect(url)
    return plugin.redirect(plugin.url_for('search'))


@plugin.route('/search')
def search():
    yield {
        'label': u'[B]{}[/B]'.format(plugin.get_string(30005)),
        'path': plugin.url_for('new_search')
    }
    for item in previous_search_items():
        yield item


if __name__ == '__main__':
    import rollbar.kodi
    try:
        plugin.run()
    except Exception as exc:
        plugin.log.error(traceback.format_exc())
        if rollbar.kodi.error_report_requested(exc):
            rollbar.kodi.report_error(
                access_token='cc56a52c62c5418ebc87f97b1aa44669',
                version=plugin.addon.getAddonInfo('version'),
                url=plugin.request.url
            )
