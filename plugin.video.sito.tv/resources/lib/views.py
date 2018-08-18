# -*- coding: utf-8 -*-
from resources.lib.sito import _lang
from resources.lib.utils import *
from resources.lib.api import *
from kodiswift import xbmcgui, xbmc


class ViewMode(object):
    ListView = None
    IconWall = 50


def open_magnet(magnet_link):
    log("open magnet: %s" % magnet_link)
    if magnet_link:
        try:
            start_bitx(magnet_link)
            kodi_go_back()
            return
        except Exception as ex:
            log("BitX magnet start error: %s" % ex, level=xbmc.LOGERROR)

    notice(_lang(33023), _lang(33022), 2500)
    kodi_go_back()


def kodi_go_back():
    # Go back in navigation.
    xbmc.executebuiltin("Action(Back)")


def custom_action(argv=None):
    log("custom_action: %s" % argv)
    if argv and len(argv) > 2:
        action = argv[2]
        if action == 'add_to_favorites':
            if len(argv) > 3 and argv[3]:
                entry_id = argv[3]
                log("add_to_favorites by EntryID: %s" % entry_id)
        elif action == 'update_plugin':
            check_update()
        elif action == 'authorization':
            pass
        elif action == 'show_log':
            pass
        elif action == 'bug_report':
            report_text = plugin.keyboard('', _lang(33030))
            if report_text and len(report_text.decode('utf-8')) >= 1:
                # {"title":"SiTo Feedback","description":"","email":"unknown"}
                api('feedback', '{"title":"SiTo Feedback","description":"'+report_text.replace('"', '\\"')+'","email":"unknown"}', method='POST')


# /..
@plugin.route('/', root=True)
def action_index():
    result = [
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(MOVIES_COLOR, _lang(33001)),
            'path': plugin.url_for('action_category', category='movies'),
            'poster': plugin.addon.getAddonInfo('icon'),
            'info': {'plot': _lang(33002)}
        }, 'movies'),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(COLOR_DISABLED, _lang(33003)),
            'path': plugin.url_for('action_ok_dialog',
                                   title='SiTo.tv',
                                   text=_lang(33004)),
            'poster': plugin.addon.getAddonInfo('icon'),
            'info': {'plot': _lang(33005)}
        }, 'tvshows'),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(COLOR_WHITE, _lang(33006)),
            'path': plugin.url_for('action_custom_action', action='Addon.OpenSettings(%s)' % PLUGIN_ID),
            'info': {'plot': _lang(33007)}
        }, 'settings')
    ]
    log("index route")
    return plugin.finish(result, view_mode=ViewMode.IconWall)


# /<category>
@plugin.route('/<category>')
def action_category(category):
    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    name = _lang(33003) if category == 'tvshows' else _lang(33001)
    all_color = TVSHOWS_COLOR if category == 'tvshows' else MOVIES_COLOR

    result = [
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(all_color, _lang(33008)),
            'path': plugin.url_for('action_category_media', category=category),
            'info': {'plot': _lang(33014)}
        }, category),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(GENRE_COLOR, _lang(33009)),
            'path': plugin.url_for('action_category_genres', category=category),
            'info': {'plot': _lang(33015)}
        }, category),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(ALPHABET_COLOR, _lang(33010)),
            'path': plugin.url_for('action_category_alphabet', category=category),
            'info': {'plot': _lang(33016)}
        }, category),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(COLOR_DISABLED, _lang(33011)),
            'path': plugin.url_for('action_ok_dialog',
                                   title='SiTo.tv',
                                   text=_lang(33045)),
            'info': {'plot': _lang(33017)}
        }, category),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(SEARCH_COLOR, _lang(33012)),
            'path': plugin.url_for('action_category_search', category=category),
            'info': {'plot': _lang(33018)}
        }, category),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(LAST_VIEWED_COLOR, _lang(33013)),
            'path': plugin.url_for('action_category_last_viewed', category=category),
            'info': {'plot': _lang(33019)}
        }, category),
        prepare_list_item({
            'label': '[COLOR {}]{}[/COLOR]'.format(all_color, _lang(33006)),
            'path': plugin.url_for('action_custom_action', action='Addon.OpenSettings(%s)' % PLUGIN_ID),
            'info': {'plot': _lang(33007)}
        }, 'settings')
    ]

    log("index %s route" % name)
    return plugin.finish(result, view_mode=ViewMode.ListView)


# /<category>/genres

@plugin.route('/<category>/genres')
def action_category_genres(category):
    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    name = _lang(33003) if category == 'tvshows' else _lang(33001)
    all_color = TVSHOWS_COLOR if category == 'tvshows' else MOVIES_COLOR

    result = [
        prepare_list_item({
            'label': '[COLOR %s][B]Any genre[/B][/COLOR]' % all_color,
            'path': plugin.url_for('action_category_media', category=category),
            'info': {'plot': '%s of any genre' % name}
        }, category)
    ]

    for genre in genres_list:
        result.insert(len(result), prepare_list_item({
            'label': "[COLOR %s]%s[/COLOR]" % (GENRE_COLOR, genre),
            'path': plugin.url_for('action_category_media_genre', category=category, genre=genre),
            'info': {'plot': '%s %s' % (genre, name)}
        }, category))

    log("genres %s route" % name)
    return result


# /<category>/alphabet

@plugin.route('/<category>/alphabet')
def action_category_alphabet(category):
    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    name = _lang(33003) if category == 'tvshows' else _lang(33001)
    all_color = TVSHOWS_COLOR if category == 'tvshows' else MOVIES_COLOR

    result = [
        prepare_list_item({
            'label': '[COLOR %s]All %s[/COLOR]' % (all_color, name),
            'path': plugin.url_for('action_category_media', category=category),
            'info': {'plot': 'All %s' % name}
        }, category)
    ]

    for letter in "A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z".split(","):
        result.insert(len(result), prepare_list_item({
            'label': "[B]%s[/B]" % letter,
            'path': plugin.url_for('action_category_media_search', category=category, search_term=letter),
            'info': {'plot': '%s by the [B]%s[/B] letter' % (name, letter)}
        }, category))

    log("alphabet %s route" % name)
    return result


# /<category>/last_viewed

@plugin.route('/<category>/last_viewed')
def action_category_last_viewed(category):
    log('show last viewed %s' % category)
    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    items = create_kodi_last_viewed_list(category)
    return plugin.finish(items, update_listing=False)


# /<category>/playlists/list_..

@plugin.route('/<category>/playlists/list_-_1', name='action_category_playlists', options={'page': '1', 'search_term': NONE})
@plugin.route('/<category>/playlists/list_<search_term>_1', name='action_category_playlists_search', options={'page': '1'})
@plugin.route('/<category>/playlists/list_<search_term>_<page>')
def action_category_playlists_page(category, page, search_term):
    log('show %s playlists at %s page // search_term=%s' % (category, page, search_term))

    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    page = int(page)  # all url params are strings by default

    # sort_params = 'year:desc,rating:desc,title:asc'
    sort_params = 'updated_date:desc,created_date:desc'
    parameters = {'page': page, 'sort': sort_params, 'limit': '25'}

    if search_term and search_term != NONE:
        # Alphabet lookup
        if len(search_term) == 1:
            search_term = "^" + search_term

        parameters['filter'] = '{"title":"%s"}' % search_term

    request_key = 'movie' if category == 'movies' else 'series'
    data = api('%s/playlists' % request_key, params=parameters)
    items = create_kodi_playlists_list(data, page, category, search_term)
    return plugin.finish(items, update_listing=False)


# /<category>/playlists/show_playlist_..

@plugin.route('/<category>/playlists/show_playlist_<playlist_id>')
def action_category_playlist_show(category, playlist_id):
    log('show %s playlist %s' % (category, playlist_id))

    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    items = create_kodi_playlist_list(playlist_id, category)
    # sort_methods=['title', 'date']
    return plugin.finish(items, update_listing=False)


# /<category>/search

@plugin.route('/<category>/search')
def action_category_search(category):
    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    name = _lang(33003) if category == 'tvshows' else _lang(33001)
    while True:
        search_term = plugin.keyboard('', _lang(33034))
        if search_term is None:
            kodi_go_back()
            return

        if len(search_term.decode('utf-8')) >= 2:
            store['last_search_term'] = search_term
            break
        else:
            notice(_lang(33021), _lang(33020))

    url = plugin.url_for('action_category_media_search', category=category, search_term=search_term)
    plugin.redirect(url)


# /<category>/list_..

@plugin.route('/<category>/list_-_-_1', name='action_category_media', options={'genre': NONE, 'page': '1', 'search_term': NONE})
@plugin.route('/<category>/list_<genre>_-_1', name='action_category_media_genre', options={'page': '1', 'search_term': NONE})
@plugin.route('/<category>/list_-_<search_term>_1', name='action_category_media_search', options={'genre': NONE, 'page': '1'})
@plugin.route('/<category>/list_<genre>_<search_term>_<page>')
def action_category_media_page(category, genre, page, search_term):
    log('show category %s at %s page // genre=%s / search_term=%s' % (category, page, genre, search_term))

    if category != 'movies' and category != 'tvshows':
        return result_not_supported_category(category)

    page = int(page)  # all url params are strings by default

    # sort_params = 'year:desc,rating:desc,title:asc'
    sort_params = 'year:desc,rating:desc'
    parameters = {'page': page, 'sort': sort_params, 'limit': '40'}

    # Alphabet lookup
    if search_term and search_term != NONE and len(search_term) == 1:
        search_term = "^" + search_term

    if genre and genre != NONE and search_term and search_term != NONE:
        parameters['filter'] = '{"genres":"%s","title":"%s"}' % (genre, search_term)
    if genre and genre != NONE:
        parameters['filter'] = '{"genres":"%s"}' % genre
    elif search_term and search_term != NONE:
        parameters['filter'] = '{"title":"%s"}' % search_term

    data = api(category, params=parameters)
    items = create_kodi_list(data, page, category, genre, search_term)

    # sort_methods=['title', 'date']
    return plugin.finish(items, update_listing=False)


# /tvshows/show/..

@plugin.route('/tvshows/show_<entry_id>', name='action_tvshow', options={'season': '', 'episode': '', 'magnet_link': None})
@plugin.route('/tvshows/show_<entry_id>/<season>', name='action_tvshow_season', options={'episode': '', 'magnet_link': None})
@plugin.route('/tvshows/show_<entry_id>/<season>/<episode>', name='action_tvshow_episode', options={'magnet_link': None})
@plugin.route('/tvshows/show_<entry_id>/<season>/<episode>/<magnet_link>')
def action_tvshow_episode_exact(entry_id, season, episode, magnet_link):
    log("show tvshow %s, season = %s, episode=%s" % (entry_id, season, episode))

    if episode and episode != NONE:
        magnet_links = get_tvshow_magnets_for_id(entry_id, season, episode, magnet_link, track=True)
        if not isinstance(magnet_links, list):
            return open_magnet(magnet_links)

        items = create_kodi_magnet_list(magnet_links, entry_id, season, episode)
        return plugin.finish(items, update_listing=False)

    if not season or season == NONE:
        items = create_kodi_tvshow_seasons_list(entry_id)
    else:
        items = create_kodi_tvshow_episodes_list(entry_id, season)

    # sort_methods=['title', 'date']
    return plugin.finish(items, update_listing=False)


# /movies/show/..

@plugin.route('/movies/show_<entry_id>', name='action_movie', options={'magnet_link': None})
@plugin.route('/movies/show_<entry_id>/<magnet_link>')
def action_movie_exact(entry_id, magnet_link):
    magnet_links = get_movie_magnets_for_id(entry_id, magnet_link, track=True)
    if not isinstance(magnet_links, list):
        return open_magnet(magnet_links)

    items = create_kodi_magnet_list(magnet_links, entry_id, season=NONE, episode=NONE)
    return plugin.finish(items, update_listing=False)


# /custom_action/..

@plugin.route('/custom_action/<action>')
def action_custom_action(action):
    log("action_custom_action: %s" % action)
    xbmc.executebuiltin(action)


@plugin.route('/ok_dialog/<title>/<text>')
def action_ok_dialog(title, text):
    ret = xbmcgui.Dialog().ok(title, text)

