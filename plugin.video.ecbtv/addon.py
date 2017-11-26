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

import itertools
import traceback

from kodiswift import Plugin
import rollbar.kodi

from resources.lib import api


PAGE_SIZE = 9

plugin = Plugin(addon_id='plugin.video.ecbtv')


def tournaments():
    return itertools.chain(
        itertools.islice(api.england_tournaments(), 3),
        api.county_tournaments()
    )


def top_level_categories():
    for tournament in tournaments():
        yield {'label': tournament.name,
               'path': plugin.url_for('show_videos_by_reference_first_page',
                                      reference=tournament.reference)}
    yield {'label': plugin.get_string(30002),
           'path': plugin.url_for('show_all_videos_first_page')}
    yield {'label': plugin.get_string(30005),
           'path': plugin.url_for('show_videos_by_reference_first_page',
                                  reference=api.england().reference)}
    yield {'label': plugin.get_string(30006), 'path': plugin.url_for('show_player_categories')}
    yield {'label': plugin.get_string(30007), 'path': plugin.url_for('show_counties')}
    yield {'label': plugin.get_string(30001), 'path': plugin.url_for('search')}


def subcategories(categories, route):
    for category in categories:
        yield {'label': category.name,
               'thumbnail': category.thumbnail,
               'path': plugin.url_for(route, category=category.name)}


def entity_items(entities):
    for entity in entities:
        yield {'label': entity.name,
               'thumbnail': entity.thumbnail,
               'path': plugin.url_for('show_videos_by_reference_first_page',
                                      reference=entity.reference)}


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


@plugin.cached()
def counties():
    return list(api.counties())


@plugin.cached()
def player_categories():
    return list(api.player_categories())


@plugin.cached()
def players(category):
    return list(api.players(category))


@plugin.cached_route('/')
def index():
    return list(top_level_categories())


@plugin.route('/counties', name='show_counties', options={'func': counties})
def show_entities(func):
    return plugin.finish(entity_items(func()), sort_methods=['label'])


@plugin.route('/players')
def show_player_categories():
    return plugin.finish(
        subcategories(player_categories(), 'show_players'),
        sort_methods=['label']
    )


@plugin.route('/players/<category>')
def show_players(category):
    return plugin.finish(entity_items(players(category)), sort_methods=['label'])


@plugin.route('/videos/all', name='show_all_videos_first_page', options={'update_listing': False})
@plugin.route('/videos/all/<page>')
def show_all_videos(page='1', update_listing=True):
    return show_videos(api.videos, 'show_all_videos', int(page), update_listing)


@plugin.route('/videos/<reference>', name='show_videos_by_reference_first_page', options={'update_listing': False})
@plugin.route('/videos/<reference>/<page>')
def show_videos_by_reference(reference, page='1', update_listing=True):
    return show_videos(api.videos, 'show_videos_by_reference', int(page), update_listing, reference=reference)


@plugin.route('/search/<term>', name='show_search_results_first_page', options={'update_listing': False})
@plugin.route('/search/<term>/<page>')
def show_search_results(term, page='1', update_listing=True):
    return show_videos(api.search_results, 'show_search_results', int(page), update_listing, term=term)


@plugin.route('/search')
def search():
    term = plugin.keyboard(heading=plugin.get_string(30001))
    if term:
        url = plugin.url_for('show_search_results_first_page', term=term)
        plugin.redirect(url)


if __name__ == '__main__':
    try:
        plugin.run()
    except Exception as exc:
        if rollbar.kodi.error_report_requested(exc):
            rollbar.kodi.report_error(
                access_token='222e7ea9c2e74fd989c48b448a58978e',
                version=plugin.addon.getAddonInfo('version'),
                url=plugin.request.url
            )
        plugin.log.error(traceback.format_exc())
