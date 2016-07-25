from xbmcswift2 import Plugin
from api import API


plugin = Plugin()
api = API(plugin)


@plugin.route('/')
def index():
    return api.get_modes()


@plugin.route('/mode/<mode>')
def show_categories(mode):
    return api.get_categories(mode)


@plugin.route('/mode/<mode>/category/<category>')
def show_subcategories(mode, category):
    return api.get_subcategories(mode, category)


@plugin.route('/editors_choice')
def show_editors_choice():
    return api.get_editors_choice()


@plugin.route('/mode/<mode>/category/<category>/index/<index>')
def show_items(mode, category, index='1'):
    return api.get_items(mode, category, plugin.request.args['link'][0], index)


@plugin.route('/search')
def show_search():
    query = plugin.keyboard(heading=plugin.get_string(30103))
    if query:
        url = plugin.url_for('show_search_results', query=query, index='1')
        plugin.redirect(url)


@plugin.route('/search/<query>/index/<index>')
def show_search_results(query, index='1'):
    return api.search_items(query, index)


@plugin.route('/favorites')
def show_favorites():
    return api.get_favorites()


@plugin.route('/favorites/add/<title>/<station_id>')
def add_to_favorites(title, station_id):
    if api.add_favorite(title, station_id):
        plugin.notify(plugin.get_string(30122).encode('utf-8'))
    else:
        plugin.notify(plugin.get_string(30124).encode('utf-8'))


@plugin.route('/favorites/remove/<station_id>')
def remove_from_favorites(station_id):
    removed = api.remove_favorite(station_id)
    plugin.redirect(plugin.url_for('index'))
    if removed:
        plugin.notify(plugin.get_string(30123).encode('utf-8'))


if __name__ == '__main__':
    plugin.run()
    plugin.set_content('songs')
    # cache = plugin.get_storage('favorites')
    # cache.clear()
