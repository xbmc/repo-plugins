from tmdbhelper.lib.addon.tmdate import get_timedelta, get_datetime_today
from tmdbhelper.lib.addon.plugin import ADDONPATH, PLUGINPATH, convert_type, get_localized, ADDON
from jurialmunkey.parser import merge_two_items
from tmdbhelper.lib.items.builder import ItemBuilder
from tmdbhelper.lib.items.container import Container
from tmdbhelper.lib.addon.consts import TVDB_DISCLAIMER, NODE_BASEDIR


def _build_basedir_item(i, t, space):
    item = i.copy()
    item['label'] = item['label'].format(space=space, item_type=convert_type(t, 'plural') if space else '')
    item['params'] = i.get('params', {}).copy()
    item['params']['tmdb_type'] = t
    if item.pop('sorting', False):
        item.setdefault('infoproperties', {})['is_sortable'] = 'True'
        item['context_menu'] = [(
            get_localized(32309),
            u'Runscript(plugin.video.themoviedb.helper,sort_list,{})'.format(
                u','.join(f'{k}={v}' for k, v in item['params'].items())))]
        item['params']['list_name'] = item['label']
    item.pop('types', None)
    item.pop('filters', None)
    return item


def _build_basedir(item_type=None, basedir=None):
    if not basedir:
        return []
    space = '' if item_type else ' '  # Type not added to label when single type so dont need spaces
    return [
        _build_basedir_item(i, t, space)
        for i in basedir for t in i.get('types', [])
        if not item_type or item_type == t]


def _get_basedir_list(item_type=None, trakt=False, tmdb=False, mdblist=False, tvdb=False):
    basedir = []
    if tmdb:
        basedir += _get_basedir_tmdb()
    if trakt:
        basedir += _get_basedir_trakt()
    if mdblist:
        basedir += _get_basedir_mdblist()
    if tvdb:
        basedir += _get_basedir_tvdb()
    return _build_basedir(item_type, basedir)


def _get_play_item():
    return [
        {
            'label': get_localized(208),
            'params': {'info': 'play'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'},
            'types': ['movie', 'episode']}]


def _get_basedir_details():
    return [
        {
            'label': get_localized(33054),
            'params': {'info': 'seasons'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/episodes.png'},
            'types': ['tv', 'episode']},
        {
            'label': get_localized(32192),
            'params': {'info': 'collection'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/movies.png'},
            'types': ['movie']},
        {
            'label': get_localized(20360),
            'params': {'info': 'episodes'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/episodes.png'},
            'types': ['episode']},
        {
            'label': get_localized(206),
            'params': {'info': 'cast'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/cast.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(32223),
            'params': {'info': 'recommendations'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/recommended.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(32224),
            'params': {'info': 'similar'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/similar.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(32225),
            'params': {'info': 'crew'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/cast.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(32226),
            'params': {'info': 'posters'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/images.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(20445),
            'params': {'info': 'fanart'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/images.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(21861),
            'params': {'info': 'movie_keywords'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/tags.png'},
            'types': ['movie']},
        {
            'label': get_localized(32188),
            'params': {'info': 'reviews'},
            'path': PLUGINPATH,
            'art': {
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/reviews.png',
                'landscape': f'{ADDONPATH}/fanart.jpg'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(32227),
            'params': {'info': 'stars_in_movies'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/movies.png'},
            'types': ['person']},
        {
            'label': get_localized(32228),
            'params': {'info': 'stars_in_tvshows'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/tv.png'},
            'types': ['person']},
        {
            'label': get_localized(32229),
            'params': {'info': 'crew_in_movies'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/movies.png'},
            'types': ['person']},
        {
            'label': get_localized(32230),
            'params': {'info': 'crew_in_tvshows'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/tv.png'},
            'types': ['person']},
        {
            'label': get_localized(32191),
            'params': {'info': 'images'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/images.png'},
            'types': ['person']},
        {
            'label': get_localized(32231),
            'params': {'info': 'episode_thumbs'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/images.png'},
            'types': ['episode']},
        {
            'label': get_localized(10025),
            'params': {'info': 'videos'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/movies.png'},
            'types': ['movie', 'tv', 'episode']},
        {
            'label': get_localized(32345),
            'params': {'info': 'episode_groups'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/episodes.png'},
            'types': ['tv']},
        {
            'label': get_localized(32232),
            'params': {'info': 'trakt_inlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/trakt.png'},
            'types': ['movie', 'tv', 'episode']}]


def _get_basedir_random():
    return [
        {
            'label': u'{} {{item_type}}{{space}}{}'.format(
                get_localized(590), get_localized(515)),
            'types': ['movie', 'tv'],
            'params': {'info': 'random_genres'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/genre.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{}'.format(
                get_localized(590), get_localized(32117)),
            'types': ['movie'],
            'params': {'info': 'random_keyword'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32199)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_becauseyouwatched'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/recommended.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32200)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_becausemostwatched'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/recommended.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32204)),
            'types': ['movie', 'tv', 'both'],
            'params': {'info': 'random_trending'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/trend.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32175)),
            'types': ['movie', 'tv', 'both'],
            'params': {'info': 'random_popular'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/popular.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32205)),
            'types': ['movie', 'tv', 'both'],
            'params': {'info': 'random_mostplayed'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mostplayed.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32414)),
            'types': ['movie', 'tv', 'both'],
            'params': {'info': 'random_mostviewers'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mostplayed.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32206)),
            'types': ['movie', 'tv', 'both'],
            'params': {'info': 'random_anticipated'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/anticipated.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32300)),
            'types': ['list'],
            'params': {'info': 'random_trendinglists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/trendinglist.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32301)),
            'types': ['list'],
            'params': {'info': 'random_popularlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/popularlist.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32302)),
            'types': ['list'],
            'params': {'info': 'random_likedlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/likedlist.png'}},
        {
            'label': u'{} {}{{space}}{{item_type}}'.format(
                get_localized(590), get_localized(32303)),
            'types': ['list'],
            'params': {'info': 'random_mylists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mylists.png'}}
    ]


def _get_basedir_trakt_genre_types(genre, tmdb_type):
    items = []

    endpoints = [d for d in _get_basedir_trakt() if d.get('filters')]

    for i in endpoints:
        item = {}
        item['label'] = i['label'].format(space=' ', item_type=f'{genre.capitalize()} {convert_type(tmdb_type, "plural")}')
        item['infolabels'] = {}
        item['infoproperties'] = {}
        item['params'] = i.get('params', {}).copy()
        item['params']['tmdb_type'] = tmdb_type
        item['params']['genres'] = genre
        item['art'] = i.get('art', {}).copy()
        item['unique_ids'] = {'slug': i.get('slug')}
        items.append(item)

    return items


def _get_basedir_nodes(filename=None, basedir=None):
    from json import loads
    from tmdbhelper.lib.files.futils import get_files_in_folder, read_file

    basedir = basedir or NODE_BASEDIR
    files = get_files_in_folder(basedir, r'.*\.json')

    if not files:
        return []

    def _get_node(file):
        data = read_file(basedir + file)
        meta = loads(data) or {}
        if not meta:
            return
        return {
            'label': meta.get('name') or '',
            'types': ['both'],
            'params': {'info': 'dir_custom_node', 'filename': file, 'basedir': basedir},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': meta.get('icon') or ''}}

    if not filename:
        return [i for i in (_get_node(file) for file in files) if i]

    if filename not in files:
        return []

    def _get_item(item):
        if not item:
            return
        return {
            'label': item.get('name') or '',
            'path': item.get('path') or PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': item.get('icon') or ''}}
    try:
        data = read_file(basedir + filename)
        meta = loads(data) or {}
        return [i for i in (_get_item(item) for item in meta['list']) if i]
    except (KeyError, TypeError):
        return []


def _get_basedir_tvdb():
    return [
        {
            'label': get_localized(32460),
            'types': ['both'],
            'params': {'info': 'dir_tvdb_awards'},
            'path': PLUGINPATH,
            'infolabels': {'plot': TVDB_DISCLAIMER},
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/tvdb/tvdb.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(135)),
            'types': ['movie', 'tv'],
            'params': {'info': 'dir_tvdb_genres'},
            'path': PLUGINPATH,
            'infolabels': {'plot': TVDB_DISCLAIMER},
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/tvdb/tvdb.png'}},
    ]


def _get_basedir_mdblist():
    return [
        {
            'label': get_localized(32421),
            'types': ['both'],
            'params': {'info': 'mdblist_toplists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/mdblist/mdblist.png'}},
        {
            'label': get_localized(32211),
            'types': ['both'],
            'params': {'info': 'mdblist_yourlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/mdblist/mdblist.png'}},
        {
            'label': get_localized(32361),
            'types': ['both'],
            'params': {'info': 'mdblist_searchlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/mdblist/mdblist.png'}}]


def _get_basedir_trakt():
    return [
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32192)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_collection'},
            'path': PLUGINPATH,
            'sorting': True,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/watchlist.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(1036)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_favorites'},
            'path': PLUGINPATH,
            'sorting': True,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/watchlist.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32193)),
            'types': ['movie', 'tv', 'season', 'episode'],
            'params': {'info': 'trakt_watchlist'},
            'path': PLUGINPATH,
            'sorting': True,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/watchlist.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32456)),
            'types': ['movie', 'tv', 'season', 'episode'],
            'params': {'info': 'trakt_watchlist_released'},
            'path': PLUGINPATH,
            'sorting': True,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/watchlist.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32457)),
            'types': ['movie', 'tv', 'season', 'episode'],
            'params': {'info': 'trakt_watchlist_anticipated'},
            'path': PLUGINPATH,
            'sorting': True,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/watchlist.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32194)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_history'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/recentlywatched.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32195)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_mostwatched'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mostwatched.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32196)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_inprogress'},
            'path': PLUGINPATH,
            'sorting': True,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/inprogress.png'}},
        {
            'label': get_localized(32406),
            'types': ['tv'],
            'params': {'info': 'trakt_ondeck'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/inprogress.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32078)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_towatch'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/watchlist.png'}},
        {
            'label': get_localized(32197),
            'types': ['tv'],
            'params': {'info': 'trakt_nextepisodes'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/inprogress.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32198)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_recommendations'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/recommended.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32199)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_becauseyouwatched'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/recommended.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32200)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_becausemostwatched'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/recommended.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{}'.format(get_localized(32201), get_localized(32202)),
            'types': ['tv'],
            'params': {'info': 'trakt_myairing'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/airing.png'}},
        {
            'label': get_localized(32459),
            'types': ['tv'],
            'params': {'info': 'trakt_airingnext'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{}'.format(get_localized(32201), get_localized(32203)),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_trakt'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{} {}'.format(get_localized(32201), get_localized(32203), get_localized(32416)),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_trakt', 'endpoint': 'premieres'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{} {}'.format(get_localized(32201), get_localized(32203), get_localized(842)),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_trakt', 'endpoint': 'new'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{}'.format(get_localized(32186), get_localized(32203)),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_trakt', 'user': 'false'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{} {}'.format(get_localized(32186), get_localized(32203), get_localized(32416)),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_trakt', 'endpoint': 'premieres', 'user': 'false'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{} {{item_type}}{{space}}{} {}'.format(get_localized(32186), get_localized(32203), get_localized(842)),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_trakt', 'endpoint': 'new', 'user': 'false'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/calendar.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(135)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_genres'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/genres.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32204)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_trending'},
            'filters': True,
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/trend.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32175)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_popular'},
            'filters': True,
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/popular.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32205)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_mostplayed'},
            'filters': True,
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mostplayed.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32414)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_mostviewers'},
            'filters': True,
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mostplayed.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32206)),
            'types': ['movie', 'tv'],
            'params': {'info': 'trakt_anticipated'},
            'filters': True,
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/anticipated.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32207)),
            'types': ['movie'],
            'params': {'info': 'trakt_boxoffice'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/boxoffice.png'}},
        {
            'label': get_localized(32208),
            'types': ['both'],
            'params': {'info': 'trakt_trendinglists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/trendinglist.png'}},
        {
            'label': get_localized(32209),
            'types': ['both'],
            'params': {'info': 'trakt_popularlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/popularlist.png'}},
        {
            'label': get_localized(32210),
            'types': ['both'],
            'params': {'info': 'trakt_likedlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/likedlist.png'}},
        {
            'label': get_localized(32211),
            'types': ['both'],
            'params': {'info': 'trakt_mylists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mylists.png'}},
        {
            'label': get_localized(32361),
            'types': ['both'],
            'params': {'info': 'trakt_searchlists'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/trakt/mylist.png'}}]


def _get_basedir_tmdb():
    return [
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(137)),
            'types': ['movie', 'tv', 'person'],
            'params': {'info': 'dir_search'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/search.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32175)),
            'types': ['movie', 'tv', 'person'],
            'params': {'info': 'popular'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/popular.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32176)),
            'types': ['movie', 'tv'],
            'params': {'info': 'top_rated'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/toprated.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32177)),
            'types': ['movie'],
            'params': {'info': 'upcoming'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/upcoming.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32178)),
            'types': ['movie', 'tv', 'person'],
            'params': {'info': 'trending_day'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/upcoming.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32179)),
            'types': ['movie', 'tv', 'person'],
            'params': {'info': 'trending_week'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/upcoming.png'}},
        {
            'label': get_localized(32180),
            'types': ['movie'],
            'params': {'info': 'now_playing'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/intheatres.png'}},
        {
            'label': get_localized(32181),
            'types': ['tv'],
            'params': {'info': 'airing_today'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/airing.png'}},
        {
            'label': get_localized(32182),
            'types': ['tv'],
            'params': {'info': 'on_the_air'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/airing.png'}},
        {
            'label': get_localized(32183),
            'types': ['tv'],
            'params': {'info': 'dir_calendar_library'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/airing.png'}},
        {
            'label': get_localized(32458),
            'types': ['tv'],
            'params': {'info': 'library_airingnext'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/airing.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(135)),
            'types': ['movie', 'tv'],
            'params': {'info': 'genres'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/genre.png'}},
        {
            'label': u'{{item_type}}{{space}}{}'.format(get_localized(32411)),
            'types': ['movie', 'tv'],
            'params': {'info': 'watch_providers'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/airing.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32184)),
            'types': ['movie'],
            'params': {'info': 'revenue_movies'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32185)),
            'types': ['movie', 'tv'],
            'params': {'info': 'most_voted'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{}{{space}}{{item_type}}'.format(get_localized(32186)),
            'types': ['collection', 'keyword', 'network', 'studio'],
            'params': {'info': 'all_items'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}}]


def _get_basedir_main():
    return [
        {
            'label': get_localized(342),
            'types': [None],
            'params': {'info': 'dir_movie'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/movies.png'}},
        {
            'label': get_localized(20343),
            'types': [None],
            'params': {'info': 'dir_tv'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/tv.png'}},
        {
            'label': get_localized(32172),
            'types': [None],
            'params': {'info': 'dir_person'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/cast.png'}},
        {
            'label': get_localized(137),
            'types': [None],
            'params': {'info': 'dir_multisearch'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/search.png'}},
        {
            'label': get_localized(32174),
            'types': [None],
            'params': {'info': 'dir_discover'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/discover.png'}},
        {
            'label': get_localized(32173),
            'types': [None],
            'params': {'info': 'dir_random'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/randomise.png'}},
        {
            'label': u'TheMovieDb',
            'types': [None],
            'params': {'info': 'dir_tmdb'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'Trakt',
            'types': [None],
            'params': {'info': 'dir_trakt'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/trakt.png'}},
        {
            'label': u'TVDb',
            'types': [None],
            'params': {'info': 'dir_tvdb'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/tvdb/tvdb.png'}},
        {
            'label': u'MDbList',
            'types': [None],
            'params': {'info': 'dir_mdblist'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/mdblist/mdblist.png'}},
        {
            'label': u'Nodes',
            'types': [None],
            'params': {'info': 'dir_custom_node'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'Settings',
            'types': [None],
            'params': {'info': 'dir_settings'},
            'path': PLUGINPATH,
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/settings.png'}}]


def _get_basedir_calendar_items():
    return [
        {
            'label': get_localized(32280),
            'params': {'startdate': -14, 'days': 14},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': get_localized(32281),
            'params': {'startdate': -7, 'days': 7},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': get_localized(32282),
            'params': {'startdate': -1, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': get_localized(33006),
            'params': {'startdate': 0, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': get_localized(33007),
            'params': {'startdate': 1, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{weekday}',
            'params': {'startdate': 2, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{weekday}',
            'params': {'startdate': 3, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{weekday}',
            'params': {'startdate': 4, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{weekday}',
            'params': {'startdate': 5, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': u'{weekday}',
            'params': {'startdate': 6, 'days': 1},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': get_localized(32284),
            'params': {'startdate': 0, 'days': 7},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}},
        {
            'label': get_localized(32285),
            'params': {'startdate': 0, 'days': 14},
            'path': PLUGINPATH,
            'info_types': ['trakt_calendar', 'library_nextaired'],
            'art': {
                'landscape': f'{ADDONPATH}/fanart.jpg',
                'icon': f'{ADDONPATH}/resources/icons/themoviedb/default.png'}}]


def _get_basedir_calendar(info=None, endpoint=None, user=None):
    items = []
    today = get_datetime_today()
    for i in _get_basedir_calendar_items():
        if info not in i['info_types']:
            continue
        date = today + get_timedelta(days=i.get('params', {}).get('startdate', 0))
        i['label'] = i['label'].format(weekday=date.strftime('%A'))
        i['params']['info'] = info
        if endpoint:
            i['params']['endpoint'] = endpoint
        if user:
            i['params']['user'] = user
        items.append(i)
    return items


def get_basedir_details(tmdb_type, tmdb_id, season=None, episode=None, detailed_item=None, include_play=False):
    base_item = detailed_item or {}
    base_item.setdefault('params', {})
    base_item.setdefault('infolabels', {})
    base_item['path'] = PLUGINPATH
    base_item['params']['tmdb_id'] = tmdb_id
    base_item['params']['tmdb_type'] = tmdb_type
    base_item['params']['info'] = 'details'

    basedir_items = []
    if tmdb_type == 'movie':
        base_item['infolabels']['mediatype'] = 'movie'
        basedir_items = _build_basedir('movie', _get_play_item()) if include_play else []
        basedir_items += _build_basedir('movie', _get_basedir_details())
    elif tmdb_type == 'tv' and season is not None and episode is not None:
        base_item['params']['season'] = season
        base_item['params']['episode'] = episode
        base_item['infolabels']['mediatype'] = 'episode'
        basedir_items = _build_basedir('episode', _get_play_item()) if include_play else []
        basedir_items += _build_basedir('episode', _get_basedir_details())
    elif tmdb_type == 'tv' and season is not None:
        base_item['params']['info'] = 'episodes'
        base_item['params']['season'] = season
        base_item['infolabels']['mediatype'] = 'season'
        basedir_items = _build_basedir('season', _get_basedir_details())
    elif tmdb_type == 'tv':
        base_item['params']['info'] = 'seasons'
        base_item['infolabels']['mediatype'] = 'tvshow'
        basedir_items = _build_basedir('tv', _get_basedir_details())
    elif tmdb_type == 'person':
        base_item['infolabels']['mediatype'] = 'video'
        basedir_items = _build_basedir('person', _get_basedir_details())

    items = [merge_two_items(base_item, i) for i in basedir_items if i]

    if detailed_item:
        return [base_item] + items
    return items


class ListBaseDir(Container):
    def get_items(self, info=None, **kwargs):
        route = {
            'dir_movie': lambda: _get_basedir_list('movie', tmdb=True, trakt=True),
            'dir_tv': lambda: _get_basedir_list('tv', tmdb=True, trakt=True),
            'dir_person': lambda: _get_basedir_list('person', tmdb=True, trakt=True),
            'dir_tmdb': lambda: _get_basedir_list(None, tmdb=True),
            'dir_trakt': lambda: _get_basedir_list(None, trakt=True),
            'dir_mdblist': lambda: _get_basedir_list(None, mdblist=True),
            'dir_tvdb': lambda: _get_basedir_list(None, tvdb=True),
            'dir_random': lambda: _build_basedir(None, _get_basedir_random()),
            'dir_calendar_trakt': lambda: _get_basedir_calendar(info='trakt_calendar', endpoint=kwargs.get('endpoint'), user=kwargs.get('user')),
            'dir_calendar_library': lambda: _get_basedir_calendar(info='library_nextaired'),
            'dir_custom_node': lambda: _get_basedir_nodes(filename=kwargs.get('filename'), basedir=kwargs.get('basedir')),
            'dir_trakt_genre': lambda: _get_basedir_trakt_genre_types(genre=kwargs.get('genre'), tmdb_type=kwargs.get('tmdb_type')),
            'dir_settings': lambda: ADDON.openSettings()
        }
        func = route.get(info, lambda: _build_basedir(None, _get_basedir_main()))
        return func()


class ListDetails(Container):
    def get_items(self, tmdb_type, tmdb_id, season=None, episode=None, **kwargs):
        def _get_container_content():
            if tmdb_type == 'tv' and season and episode:
                return convert_type('episode', 'container')
            elif tmdb_type == 'tv' and season:
                return convert_type('season', 'container')
            return convert_type(tmdb_type, 'container')
        base_item = ItemBuilder(tmdb_api=self.tmdb_api).get_item(tmdb_type, tmdb_id, season, episode)
        base_item = base_item['listitem'] if base_item else {}
        base_item = self.omdb_api.get_item_ratings(base_item) if self.omdb_api else base_item
        items = get_basedir_details(tmdb_type, tmdb_id, season, episode, base_item)
        self.container_content = _get_container_content()
        self.kodi_db = self.get_kodi_database(tmdb_type)
        return items
