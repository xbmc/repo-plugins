# -*- coding: utf-8 -*-
'''
    Reddit Music
    ~~~~~~~~~~~~

    An XBMC addon for watching and listenting to music found on a variety of
    subreddits.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
import operator
from xbmcswift2 import Plugin
from resources.lib.subreddits import subreddits
from resources.lib import mediahosts, playlists, reddit


plugin = Plugin()
plugin.register_module(playlists.playlists, '/playlists')
red = reddit.Reddit(user_agent='XBMC')


STRINGS = {
    'browse_subreddits': 30010,
    'my_playlists': 30011,
    'add_to_playlist': 30012,
}


def _(string_id):
    return plugin.get_string(STRINGS[string_id])


def _run(endpoint, **items):
    '''Returns a RunPlugin string for use in a context menu.

    :param endpoint: The endpoint to be used with plugin.url_for().
    :param **items: Any keyword args to be passed to plugin.url_for().
    '''
    return 'XBMC.RunPlugin(%s)' % plugin.url_for(endpoint, **items)


@plugin.route('/')
def index():
    '''Display main menu'''
    items = [
        {'label': _('browse_subreddits'),
         'path': plugin.url_for('show_subreddits')},

        {'label': _('my_playlists'),
         'path': plugin.url_for('playlists.show_playlists')},
    ]
    return items


@plugin.route('/r/')
def show_subreddits():
    '''Displays list of subreddits'''
    items = [{
        'label': name,
        'path': plugin.url_for('show_views', name=name),
        'info': {
            'description': desc,
        },
    } for name, desc in subreddits.items()]
    return sorted(items, key=operator.itemgetter('label'))


@plugin.route('/r/<name>')
def show_views(name):
    '''Displays the various views available for a subreddit'''
    views = ['hot', 'new', 'controversial', 'top']
    items = [{
        'label': view,
        'path': plugin.url_for('show_sub', name=name, view=view),
    } for view in views]
    return items


@plugin.route('/r/<name>/<view>')
@plugin.route('/r/<name>/<view>/before/<before>', 'show_sub_before')
@plugin.route('/r/<name>/<view>/after/<after>', 'show_sub_after')
def show_sub(name, view, before=None, after=None):
    '''Displays items for a given subreddit name and view.

    :param name: A subreddit name, e.g. 'listentothis'
    :param view: A subreddit view, one of ['top', 'new', 'hot',
                 'controversial']
    :param before: For a given listing of items, the before id. Used for
                   pagination to go the previous page.
    :param before: For a given listing of items, the after id. Used for
                   pagination to go the next page.
    '''
    links, (_before, _after) = red.get_links(name, view=view, limit=100,
                                             before=before, after=after)

    # Filter out self posts and media sources we can't parse
    items = [create_playable_item(link) for link in links
             if link['domain'] in mediahosts.HOST_STRINGS]

    # Sometimes we can't parse a playable path and create_playable_item will
    # return None. Filter these out.
    valid_items = [item for item in items if item is not None]

    # Each time we show a listing with playable items, we store the items in
    # temporary storage. Then, if a user add the item to a playlist, we already
    # have all the metadata available.
    temp_items = plugin.get_storage('temp_items')
    temp_items.clear()

    # Need to use the same referenced dict object for the cache, so we call
    # update() instead of assigning to a new dict.
    temp_items.update((item['path'], item) for item in valid_items)

    # pagination list items
    if _after:
        valid_items.insert(0, {
            'label': u'Next »',
            'path': plugin.url_for('show_sub_after', name=name, view=view,
                                   after=_after),
        })

    # reddit includes a 'before' for the first page of results, we ignore
    # because that request will return 0 links.
    if _before and (before or after):
        valid_items.insert(0, {
            'label': u'« Previous',
            'path': plugin.url_for('show_sub_before', name=name, view=view,
                                   before=_before),
        })

    update_listing = before is not None or after is not None
    return plugin.finish(valid_items, update_listing=update_listing)


def create_playable_item(link):
    '''Returns a list item dict for a give reddit link dict. If a playable URL
    cannot be parsed, None will be returned.
    '''
    item = {
        'label': link['title'],
        'is_playable': True,
    }

    url = mediahosts.resolve(link['url'])
    if url is None:
        return None
    item['path'] = url

    try:
        item['thumbnail'] = link['media']['oembed']['thumbnail_url']
    except TypeError:
        pass

    try:
        item['info'] = {
            'plot': link['media']['oembed']['description'],
        }
    except TypeError:
        pass

    my_playlists = plugin.get_storage('my_playlists')
    ctx_items = [(_('add_to_playlist') % name,
                  _run('playlists.add_to_playlist', playlist=name,
                       url=item['path']))
                 for name in my_playlists.keys()]
    item['context_menu'] = ctx_items

    return item


if __name__ == '__main__':
    plugin.run()
