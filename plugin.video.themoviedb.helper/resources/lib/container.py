import sys
import resources.lib.utils as utils
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
from resources.lib.tmdb import TMDb
from resources.lib.omdb import OMDb
from resources.lib.traktapi import traktAPI
from resources.lib.kodilibrary import KodiLibrary
from resources.lib.listitem import ListItem
from resources.lib.globals import LANGUAGES, BASEDIR_MAIN, BASEDIR_TMDB, BASEDIR_LISTS, TYPE_CONVERSION, TMDB_LISTS, DETAILED_CATEGORIES, APPEND_TO_RESPONSE, TRAKT_LISTS, TRAKT_LISTLISTS, TRAKT_HISTORYLISTS
try:
    from urllib.parse import parse_qsl  # Py3
except ImportError:
    from urlparse import parse_qsl  # Py2
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_addonpath = _addon.getAddonInfo('path')
_addonname = 'plugin.video.themoviedb.helper'
_prefixname = 'TMDbHelper.'
_dialog = xbmcgui.Dialog()
_languagesetting = _addon.getSettingInt('language')
_language = LANGUAGES[_languagesetting]
_mpaa_prefix = _addon.getSetting('mpaa_prefix')
_cache_long = _addon.getSettingInt('cache_details_days')
_cache_short = _addon.getSettingInt('cache_list_days')
_tmdb_apikey = _addon.getSetting('tmdb_apikey')
_tmdb = TMDb(api_key=_tmdb_apikey, language=_language, cache_long=_cache_long, cache_short=_cache_short,
             append_to_response=APPEND_TO_RESPONSE, addon_name=_addonname, mpaa_prefix=_mpaa_prefix)
_omdb_apikey = _addon.getSetting('omdb_apikey')
_omdb = OMDb(api_key=_omdb_apikey, cache_long=_cache_long, cache_short=_cache_short, addon_name=_addonname) if _omdb_apikey else None
_kodimoviedb = KodiLibrary(dbtype='movie')
_koditvshowdb = KodiLibrary(dbtype='tvshow')


def type_convert(original, converted):
    return TYPE_CONVERSION.get(original, {}).get(converted, '')


class Container(object):
    def __init__(self):
        self.paramstring = sys.argv[2][1:] if sys.version_info.major == 3 else sys.argv[2][1:].decode("utf-8")
        self.params = dict(parse_qsl(self.paramstring))
        self.dbtype = None
        self.nexttype = None
        self.url_info = None
        self.details_tv = None
        self.plugincategory = 'TMDb Helper'
        self.containercontent = ''
        self.library = 'video'
        self.router()

    def start_container(self):
        xbmcplugin.setPluginCategory(_handle, self.plugincategory)  # Container.PluginCategory
        xbmcplugin.setContent(_handle, self.containercontent)  # Container.Content

    def finish_container(self):
        xbmcplugin.endOfDirectory(_handle)

    def textviewer(self):
        _dialog.textviewer(xbmc.getInfoLabel('ListItem.Label'), xbmc.getInfoLabel('ListItem.Plot'))

    def imageviewer(self):
        xbmc.executebuiltin('ShowPicture({0})'.format(self.params.get('image')))

    def translate_discover(self):
        lookup_company = 'company'
        lookup_person = 'person'
        lookup_genre = 'genre'
        if self.params.get('with_id') and self.params.get('with_id') != 'False':
            lookup_company = None
            lookup_person = None
            lookup_genre = None
        if self.params.get('with_genres'):
            self.params['with_genres'] = _tmdb.get_translated_list(utils.split_items(self.params.get('with_genres')), lookup_genre, separator=self.params.get('with_separator'))
        if self.params.get('without_genres'):
            self.params['without_genres'] = _tmdb.get_translated_list(utils.split_items(self.params.get('without_genres')), lookup_genre, separator=self.params.get('with_separator'))
        if self.params.get('with_companies'):
            self.params['with_companies'] = _tmdb.get_translated_list(utils.split_items(self.params.get('with_companies')), lookup_company, separator='NONE')
        if self.params.get('with_people'):
            self.params['with_people'] = _tmdb.get_translated_list(utils.split_items(self.params.get('with_people')), lookup_person, separator=self.params.get('with_separator'))
        if self.params.get('with_cast'):
            self.params['with_cast'] = _tmdb.get_translated_list(utils.split_items(self.params.get('with_cast')), lookup_person, separator=self.params.get('with_separator'))
        if self.params.get('with_crew'):
            self.params['with_crew'] = _tmdb.get_translated_list(utils.split_items(self.params.get('with_crew')), lookup_person, separator=self.params.get('with_separator'))

    def url_encoding(self, item):
        url = item.get('url') or {'info': self.url_info}
        url['type'] = item.get('mixed_type') or self.nexttype or self.params.get('type')
        if item.get('tmdb_id'):
            url['tmdb_id'] = item.get('tmdb_id')
        if url.get('info') == 'imageviewer':
            item['is_folder'] = False
            url = {'info': 'imageviewer', 'image': item.get('icon')}
        if url.get('info') == 'textviewer':
            item['is_folder'] = False
            url = {'info': 'textviewer'}
        if self.params.get('info') in ['seasons', 'episodes'] or url.get('type') in ['season', 'episode']:
            url['tmdb_id'] = self.params.get('tmdb_id')
            url['season'] = item.get('infolabels', {}).get('season')
            url['episode'] = item.get('infolabels', {}).get('episode')
        item['url'] = url
        return item

    def get_tmdb_id(self):
        if not self.params.get('tmdb_id'):
            itemtype = TMDB_LISTS.get(self.params.get('info'), {}).get('tmdb_check_id', self.params.get('type'))
            self.params['tmdb_id'] = _tmdb.get_tmdb_id(itemtype=itemtype, imdb_id=self.params.get('imdb_id'), query=self.params.get('query'), year=self.params.get('year'))

    def get_details(self, item):
        if self.params.get('info') in ['seasons', 'episodes'] or item['url'].get('type') in ['season', 'episode']:
            if not self.details_tv:
                self.details_tv = _tmdb.get_detailed_item('tv', self.params.get('tmdb_id'), season=self.params.get('season', None))
            if self.details_tv:
                item = utils.del_empty_keys(item)
                item['infolabels'] = utils.del_empty_keys(item.get('infolabels', {}))
                item['infoproperties'] = utils.del_empty_keys(item.get('infoproperties', {}))
                item['infolabels'] = utils.merge_two_dicts(self.details_tv.get('infolabels', {}), item.get('infolabels', {}))
                item['infoproperties'] = utils.merge_two_dicts(self.details_tv.get('infoproperties', {}), item.get('infoproperties', {}))
                item = utils.merge_two_dicts(self.details_tv, item)
        if item['url'].get('type') in ['movie', 'tv']:
            detailed_item = _tmdb.get_detailed_item(item['url'].get('type'), item['url'].get('tmdb_id'), cache_only=True)
            if detailed_item:
                detailed_item['infolabels'] = utils.merge_two_dicts(item.get('infolabels', {}), detailed_item.get('infolabels', {}))
                detailed_item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), detailed_item.get('infoproperties', {}))
                detailed_item['label'] = item.get('label')
                item = utils.merge_two_dicts(item, detailed_item)
        if item['url'].get('type') == 'movie':
            item = self.get_omdb_ratings(item, cache_only=True)
        return item

    def get_omdb_ratings(self, item, cache_only=False):
        if _omdb and item.get('infolabels', {}).get('imdbnumber'):
            ratings_awards = _omdb.get_ratings_awards(imdb_id=item.get('infolabels', {}).get('imdbnumber'), cache_only=cache_only)
            if ratings_awards:
                item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), ratings_awards)
        return item

    def get_dbid(self, item):
        kodidatabase = None
        if item['url'].get('type') == 'movie':
            kodidatabase = _kodimoviedb
        if item['url'].get('type') == 'tv':
            kodidatabase = _koditvshowdb
        if kodidatabase:
            item['dbid'] = kodidatabase.get_dbid(imdb_id=item.get('infolabels', {}).get('imdbnumber'), originaltitle=item.get('infolabels', {}).get('originaltitle'), title=item.get('infolabels', {}).get('title'), year=item.get('infolabels', {}).get('year'))
        return item

    def list_items(self, items):
        added = []
        dbiditems = []
        tmdbitems = []
        mixed_movies = 0
        mixed_tvshows = 0
        for i in items:
            name = u'{0}{1}'.format(i.get('label'), i.get('poster'))
            if name in added:  # Don't add duplicate items
                continue
            if i.get('infolabels', {}).get('season', 1) == 0:  # Ignore Specials
                continue
            added.append(name)

            i = self.url_encoding(i)
            i = self.get_details(i)
            i = self.get_dbid(i)

            if i.get('mixed_type', '') == 'tv':
                mixed_tvshows += 1
            elif i.get('mixed_type', '') == 'movie':
                mixed_movies += 1

            if i.get('dbid'):
                dbiditems.append(i)
            else:
                tmdbitems.append(i)
        items = dbiditems + tmdbitems

        if self.params.get('type') == 'both':
            self.containercontent = 'tvshows' if mixed_tvshows > mixed_movies else 'movies'

        self.start_container()
        for i in items:
            url = i.pop('url', {})
            self.dbtype = type_convert(i.pop('mixed_type', ''), 'dbtype') or self.dbtype
            i.setdefault('infolabels', {})['mediatype'] = self.dbtype if self.dbtype and not i.get('label') == 'Next Page' else ''
            listitem = ListItem(library=self.library, **i)
            listitem.create_listitem(_handle, **url)
        self.finish_container()

        if self.params.get('prop_id'):
            window_prop = '{0}{1}.NumDBIDItems'.format(_prefixname, self.params.get('prop_id'))
            xbmcgui.Window(10000).setProperty(window_prop, str(len(dbiditems)))
            window_prop = '{0}{1}.NumTMDBItems'.format(_prefixname, self.params.get('prop_id'))
            xbmcgui.Window(10000).setProperty(window_prop, str(len(tmdbitems)))

    def list_tmdb(self, *args, **kwargs):
        if self.params.get('type'):
            cat = TMDB_LISTS.get(self.params.get('info'), {})
            url_ext = dict(parse_qsl(cat.get('url_ext', '').format(**self.params)))
            path = cat.get('path', '').format(**self.params)
            kwparams = utils.make_kwparams(self.params)
            kwparams = utils.merge_two_dicts(kwparams, kwargs)
            kwparams = utils.merge_two_dicts(kwparams, url_ext)
            kwparams.setdefault('key', cat.get('key', 'results'))
            items = _tmdb.get_list(path, *args, **kwparams)
            itemtype = cat.get('itemtype') or self.params.get('type') or ''
            self.url_info = cat.get('url_info', 'details')
            self.nexttype = cat.get('nexttype')
            self.dbtype = type_convert(itemtype, 'dbtype')
            self.plugincategory = cat.get('name', '').format(type_convert(itemtype, 'plural'))
            self.containercontent = type_convert(itemtype, 'container')
            self.list_items(items)

    def list_details(self):
        details = _tmdb.get_detailed_item('tv', self.params.get('tmdb_id'), self.params.get('season'), self.params.get('episode')) if self.params.get('type') == 'episode' else _tmdb.get_detailed_item(self.params.get('type'), self.params.get('tmdb_id'))
        if details:
            if self.params.get('type') == 'movie':
                details = self.get_omdb_ratings(details, cache_only=False)
            if self.params.get('type') in ['tv']:
                details['url'] = {'info': 'seasons'}  # Open seasons when clicking tvshow detailed item
            items = [details]
            for i in DETAILED_CATEGORIES:
                cat = TMDB_LISTS.get(i) or TRAKT_LISTS.get(i) or {}
                if self.params.get('type') in cat.get('types'):
                    item = details.copy()
                    item['label'] = cat.get('name')
                    item['url'] = cat.get('url', {}).copy()
                    item['url']['info'] = i
                    if cat.get('url_key') and item.get(cat.get('url_key')):
                        item['url'][cat.get('url_key')] = item.get(cat.get('url_key'))
                    items.append(item)
            self.dbtype = type_convert(self.params.get('type'), 'dbtype')
            self.plugincategory = details.get('label')
            self.containercontent = type_convert(self.params.get('type'), 'container')
            self.list_items(items)

    def list_search(self):
        if not self.params.get('query'):
            self.params['query'] = _dialog.input('Enter Search Query', type=xbmcgui.INPUT_ALPHANUM)
        if self.params.get('query'):
            self.list_tmdb(query=self.params.get('query'), year=self.params.get('year'))

    def list_credits(self, key='cast'):
        items = _tmdb.get_credits_list(self.params.get('type'), self.params.get('tmdb_id'), key)
        self.url_info = 'details'
        self.nexttype = 'person'
        self.plugincategory = key.capitalize()
        self.containercontent = 'actors'
        self.list_items(items)

    def list_trakthistory(self):
        _traktapi = traktAPI()
        userslug = _traktapi.get_usernameslug()
        if self.params.get('info') == 'trakt_inprogress':
            trakt_items = _traktapi.get_inprogress(userslug, limit=10)
        if self.params.get('info') == 'trakt_mostwatched':
            trakt_items = _traktapi.get_mostwatched(userslug, type_convert(self.params.get('type'), 'trakt'), limit=10)
        if self.params.get('info') == 'trakt_history':
            trakt_items = _traktapi.get_recentlywatched(userslug, type_convert(self.params.get('type'), 'trakt'), limit=10)
        items = [_tmdb.get_detailed_item(self.params.get('type'), i[1]) for i in trakt_items]
        if items:
            self.nexttype = self.params.get('type')
            self.dbtype = type_convert(self.nexttype, 'dbtype')
            self.url_info = 'trakt_upnext' if self.params.get('info') == 'trakt_inprogress' else 'details'
            self.plugincategory = type_convert(self.nexttype, 'plural')
            self.containercontent = type_convert(self.nexttype, 'container')
            self.list_items(items)

    def list_traktupnext(self):
        _traktapi = traktAPI()
        imdb_id = _tmdb.get_item_externalid(itemtype='tv', tmdb_id=self.params.get('tmdb_id'), external_id='imdb_id')
        trakt_items = _traktapi.get_upnext(imdb_id)
        items = [_tmdb.get_detailed_item(itemtype='tv', tmdb_id=self.params.get('tmdb_id'), season=i[0], episode=i[1]) for i in trakt_items]
        if items:
            itemtype = 'episode'
            self.nexttype = 'episode'
            self.url_info = 'details'
            self.dbtype = type_convert(itemtype, 'dbtype')
            self.plugincategory = type_convert(itemtype, 'plural')
            self.containercontent = type_convert(itemtype, 'container')
            self.list_items(items[:10])

    def list_traktuserlists(self):
        _traktapi = traktAPI()
        self.params['user_slug'] = self.params.get('user_slug') or _traktapi.get_usernameslug()
        path = TRAKT_LISTS.get(self.params.get('info'), {}).get('path', '').format(**self.params)
        items = _traktapi.get_listlist(path, 'list')
        icon = '{0}/resources/trakt.png'.format(_addonpath)
        self.start_container()
        for i in items:
            label = i.get('name')
            label2 = i.get('user', {}).get('name')
            infolabels = {}
            infolabels['plot'] = i.get('description')
            infolabels['rating'] = i.get('likes')
            list_slug = i.get('ids', {}).get('slug')
            user_slug = i.get('user', {}).get('ids', {}).get('slug')
            listitem = ListItem(label=label, label2=label2, icon=icon, thumb=icon, poster=icon, infolabels=infolabels)
            listitem.create_listitem(_handle, info='trakt_userlist', user_slug=user_slug, list_slug=list_slug, type=self.params.get('type'))
        self.finish_container()

    def list_trakt(self):
        items = []
        if self.params.get('type'):
            _traktapi = traktAPI()
            self.params['user_slug'] = self.params.get('user_slug') or _traktapi.get_usernameslug()
            cat = TRAKT_LISTS.get(self.params.get('info', ''), {})
            params = self.params.copy()
            itemtype = 'movie' if self.params.get('type') == 'both' else self.params.get('type', '')
            keylist = ['movie', 'show'] if self.params.get('type') == 'both' else [type_convert(itemtype, 'trakt')]
            params['type'] = type_convert(itemtype, 'trakt') + 's'
            path = cat.get('path', '').format(**params)
            trakt_items = _traktapi.get_itemlist(path, keylist=keylist, page=self.params.get('page', 1), limit=10)
            for i in trakt_items[:11]:
                item = None
                if i[0] == 'imdb':
                    item = _tmdb.get_externalid_item(i[2], i[1], 'imdb_id')
                if i[0] == 'tvdb':
                    item = _tmdb.get_externalid_item(i[2], i[1], 'tvdb_id')
                if i[0] == 'next_page':
                    item = {'label': 'Next Page', 'url': self.params.copy()}
                    item['url']['page'] = i[1]
                if item:
                    item['mixed_type'] = i[2]
                    items.append(item)
        if items:
            self.nexttype = itemtype
            self.dbtype = type_convert(itemtype, 'dbtype')
            self.url_info = cat.get('url_info', 'details')
            self.plugincategory = cat.get('name', '').format(type_convert(itemtype, 'plural'))
            self.containercontent = type_convert(itemtype, 'container') or 'movies'
            self.list_items(items)

    def list_basedir(self):
        """
        Creates a listitem for each type of each category in BASEDIR
        """
        basedir = BASEDIR_LISTS.get(self.params.get('info'), {}).get('path') or BASEDIR_MAIN
        self.start_container()
        for i in basedir:
            cat = BASEDIR_LISTS.get(i) or TMDB_LISTS.get(i) or TRAKT_LISTS.get(i) or {}
            icon = cat.get('icon', '').format(_addonpath)
            for t in cat.get('types', []):
                label = cat.get('name', '').format(type_convert(t, 'plural'))
                listitem = ListItem(label=label, icon=icon, thumb=icon, poster=icon)
                url = {'info': i, 'type': t} if t else {'info': i}
                listitem.create_listitem(_handle, **url)
        self.finish_container()

    def router(self):
        # FILTERS AND EXCLUSIONS
        _tmdb.filter_key = self.params.get('filter_key', None)
        _tmdb.filter_value = self.params.get('filter_value', None)
        _tmdb.exclude_key = self.params.get('exclude_key', None)
        _tmdb.exclude_value = self.params.get('exclude_value', None)

        # ROUTER LIST FUNCTIONS
        if self.params.get('info') == 'discover':
            self.translate_discover()
            self.list_tmdb()
        elif self.params.get('info') == 'details':
            self.get_tmdb_id()
            self.list_details()
        elif self.params.get('info') == 'search':
            self.list_search()
        elif self.params.get('info') == 'cast':
            self.get_tmdb_id()
            self.list_credits('cast')
        elif self.params.get('info') == 'crew':
            self.get_tmdb_id()
            self.list_credits('crew')
        elif self.params.get('info') == 'textviewer':
            self.textviewer()
        elif self.params.get('info') == 'imageviewer':
            self.imageviewer()
        elif self.params.get('info') in TRAKT_HISTORYLISTS:
            self.list_trakthistory()
        elif self.params.get('info') == 'trakt_upnext':
            self.list_traktupnext()
        elif self.params.get('info') in TRAKT_LISTLISTS:
            self.list_traktuserlists()
        elif self.params.get('info') in TRAKT_LISTS:
            self.list_trakt()
        elif self.params.get('info') in BASEDIR_TMDB:
            self.list_tmdb()
        elif self.params.get('info') in TMDB_LISTS and TMDB_LISTS.get(self.params.get('info'), {}).get('path'):
            self.get_tmdb_id()
            self.list_tmdb()
        elif self.params.get('info') in BASEDIR_LISTS:
            self.list_basedir()
        elif not self.params:
            self.list_basedir()
