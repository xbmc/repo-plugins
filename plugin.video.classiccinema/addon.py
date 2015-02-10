'''
    Classic Cinema Addon for XBMC
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Watch films from http://classiccinemaonline.com.

    :copyright: (c) 2012 by Jonathan Beluch
    :license: GPLv3, see LICENSE.txt for more details.
'''
from xbmcswift2 import Plugin, xbmcgui
from resources.lib import api


plugin = Plugin()


# Warn users that some menus may be empty
user_data = plugin.get_storage('user_data')
if 'not_first_time' not in user_data.keys():
    dialog = xbmcgui.Dialog()
    dialog.ok(
        'Classic Cinema',
        'The website has recently changed so all of the old',
        'films are not yet uploaded to the new website.'
    )
    user_data['not_first_time'] = True


@plugin.route('/')
def show_browse_methods():
    '''Default view. Displays the different ways to browse the site.'''
    items = [{
        'label': ctg,
        'path': plugin.url_for('show_genres', category=ctg),
    } for ctg in api.get_categories()]
    return items


@plugin.route('/categories/<category>')
def show_genres(category):
    items = [{
        'label': title,
        'path': plugin.url_for('show_films', genre_url=url),
    } for title, url in api.get_genres_flat(category)]
    return items


@plugin.route('/genres/<genre_url>')
def show_films(genre_url):
    plugin.log.info(genre_url)
    items = [{
        'label': title,
        'path': plugin.url_for('play_film', url=url),
        'is_playable': True,
    } for title, url in api.get_films(genre_url)]
    return items


@plugin.route('/play/<url>')
def play_film(url):
    film = api.get_film(url)

    # TODO: pass full listitem once xbmcswift2 supports it
    return plugin.set_resolved_url(film['url'])


if __name__ == '__main__':
    plugin.run()
