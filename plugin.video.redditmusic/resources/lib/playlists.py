'''
    redditmusic.resources.lib.playlists
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module contains an xbmcswift2.Module for handling the playlists
    interaction for the addon.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
from xbmcswift2 import module, xbmc, xbmcgui


playlists = module.Module('playlists')


STRINGS = {
    'reddit_music': 30000,
    'create_playlist': 30100,
    'delete_playlist': 30101,
    'remove_item': 30102,
    'enter_playlist_name': 30103,
    'confirm_delete': 30104,
}


def _(string_id):
    return playlists.get_string(STRINGS[string_id])


def _run(endpoint, **items):
    '''Returns a RunPlugin string for use in a context menu.

    :param endpoint: The endpoint to be used with playlists.url_for().
    :param **items: Any keyword args to be passed to playlists.url_for().
    '''
    return 'XBMC.RunPlugin(%s)' % playlists.url_for(endpoint, **items)


@playlists.route('/')
def show_playlists():
    '''Displays the 'Create Playlist' item as well as items for any playlists
    the user has created.
    '''
    my_playlists = playlists.plugin.get_storage('my_playlists')

    create = {
        'label': _('create_playlist'),
        'path': playlists.url_for('create_playlist'),
    }

    items = [{
        'label': name,
        'path': playlists.url_for('show_playlist', name=name),
        'context_menu': [(_('delete_playlist'),
                         _run('remove_playlist', playlist=name)), ]
    } for name in sorted(my_playlists.keys())]

    return [create] + items


@playlists.route('/playlists/show/<name>/')
def show_playlist(name):
    '''Displays a user's custom playlist. The playlist items are persisted via
    plugin storage.
    '''
    my_playlists = playlists.plugin.get_storage('my_playlists')
    items = my_playlists[name]

    # Augment the existing list items with a context menu item to 'Remove from
    # Playlist'.
    for item in items:
        ctx_items = [
            (_('remove_item'),
             _run('remove_from_playlist', playlist=name, url=item['path']))
        ]
        item['context_menu'] = ctx_items

    return items


@playlists.route('/new/')
def create_playlist():
    '''Creates a new empty user named playlist. User's can add playlist items
    from the context menu of playable items elsewhere in the addon.
    '''
    name = playlists.keyboard(heading=_('enter_playlist_name'))

    my_playlists = playlists.plugin.get_storage('my_playlists')
    if name and name not in my_playlists.keys():
        my_playlists[name] = []
    return playlists.plugin.finish(show_playlists(), update_listing=True)


@playlists.route('/remove/<playlist>/')
def remove_playlist(playlist):
    '''Deletes a user specified playlist. If the playlist is not empty, the
    user will be presented with a yes/no confirmation dialog before deletion.
    '''
    my_playlists = playlists.plugin.get_storage('my_playlists')
    num_items = len(my_playlists[playlist])

    delete = True
    if num_items > 0:
        dialog = xbmcgui.Dialog()
        delete = dialog.yesno(_('reddit_music'), _('confirm_delete'))

    if delete:
        del my_playlists[playlist]
        my_playlists.sync()
        xbmc.executebuiltin('Container.Refresh')


@playlists.route('/remove/<playlist>/<url>/')
def remove_from_playlist(playlist, url):
    '''Deletes an item from the given playlist whose url matches the provided
    url.
    '''
    # We don't have the full item in temp_items, so have to iterate over items
    # in the list and match on url
    my_playlists = playlists.plugin.get_storage('my_playlists')
    try:
        match = (item for item in my_playlists[playlist]
                 if item['path'] == url).next()
        my_playlists[playlist].remove(match)
        my_playlists.sync()
        xbmc.executebuiltin('Container.Refresh')
    except StopIteration:
        pass


@playlists.route('/add/<playlist>/<url>/')
def add_to_playlist(playlist, url):
    '''Adds an item to the given playlist. The list item added will be pulled
    from temp_items storage and matched on the provided url.
    '''
    temp_items = playlists.plugin.get_storage('temp_items')
    item = temp_items[url]
    my_playlists = playlists.plugin.get_storage('my_playlists')
    my_playlists[playlist].append(item)
    my_playlists.sync()
