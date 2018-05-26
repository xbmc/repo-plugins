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
from datetime import datetime
import operator
# Workaround for 'Failed to import _strptime because the import lock is held by another thread.'
import _strptime  # pylint: disable=unused-import

from kodiswift import Plugin, xbmcgui  # pylint: disable=wrong-import-order

from resources.lib import api


PAGE_SIZE = 9

plugin = Plugin(addon_id='plugin.video.btsportvideo')


def category_items():
    yield {'label': u'[B]{}[/B]'.format('Live Channels'),
           'path': plugin.url_for('channels')}
    yield {'label': u'[B]{}[/B]'.format(plugin.get_string(30002)),
           'path': plugin.url_for('search')}

    categories = list(api.categories())
    yield {'label': u'[B]{}[/B]'.format(plugin.get_string(30001)),
           'path': plugin.url_for('show_videos_by_category_first_page',
                                  path=categories[0].path)}
    for category in categories[1:]:
        yield {'label': category.title,
               'path': plugin.url_for('show_videos_by_category_first_page',
                                      path=category.path)}


def page_link_items(route, page, npages, **kwargs):
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


def video_items(videos):
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


def show_videos(links, videos, update_listing):
    return plugin.finish(
        list(links) + list(video_items(videos)),
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


@plugin.cached(ttl=30)
def avs_session(user, password):
    if not all((user, password)):
        plugin.open_settings()

    session = api.login(user, password)
    if session is None:
        xbmcgui.Dialog().ok(plugin.get_string(30011), plugin.get_string(30012))
        return None
    return api.sport_login(session)


@plugin.cached(ttl=7*24*60) # Cache query text for a week
def query_text(path):
    return api.query_text(path)


@plugin.route('/')
def index():
    return list(category_items())


@plugin.route('/videos/<path>', name='show_videos_by_category_first_page',
              options={'update_listing': False})
@plugin.route('/videos/<path>/<page>')
def show_videos_by_category(path, page='1', update_listing=True):
    results, npages = api.video_results(query_text(path), int(page), PAGE_SIZE)
    links = page_link_items('show_videos_by_category', int(page), npages, path=path)
    return show_videos(links, results, update_listing)


@plugin.route('/search/term/<term>', name='show_search_results_first_page',
              options={'update_listing': False})
@plugin.route('/search/term/<term>/<page>')
def show_search_results(term, page='1', update_listing=True):
    plugin.get_storage('searches')[term] = datetime.now()
    results, npages = api.search_results(term, int(page), PAGE_SIZE)
    links = page_link_items('show_search_results', int(page), npages, term=term)
    return show_videos(links, results, update_listing)


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


@plugin.cached_route('/channels')
def channels():
    return [
        {
            'label': u'[B]{}[/B]'.format(channel.name),
            'path': plugin.url_for('play_channel', channel_id=channel.channel_id),
            'thumbnail': channel.thumbnail,
            'is_playable': True,
            'info': {
                'title': channel.name
            }
        }
        for channel in api.CHANNELS
    ]


@plugin.route('/channels/play/<channel_id>')
def play_channel(channel_id):
    session = avs_session(plugin.get_setting('user'), plugin.get_setting('password'))
    try:
        url = api.hls_url(session, channel_id=channel_id)
    except api.BTError as exc:
        xbmcgui.Dialog().ok(plugin.get_string(30013), "[COLOR=red]{}[/COLOR]".format(exc))
        url = None
    plugin.set_resolved_url(url)


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
