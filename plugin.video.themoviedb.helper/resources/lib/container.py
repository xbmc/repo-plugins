import sys
import resources.lib.utils as utils
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
from resources.lib.tmdb import TMDb
from resources.lib.omdb import OMDb
from resources.lib.kodilibrary import KodiLibrary
from resources.lib.listitem import ListItem
from resources.lib.globals import LANGUAGES, BASEDIR, TYPE_CONVERSION, TMDB_LISTS, TMDB_CATEGORIES, APPEND_TO_RESPONSE
try:
    from urllib.parse import parse_qsl  # Py3
except ImportError:
    from urlparse import parse_qsl  # Py2
_handle = int(sys.argv[1])
_addon = xbmcaddon.Addon()
_addonname = 'plugin.video.themoviedb.helper'
_prefixname = 'TMDbHelper.'
_dialog = xbmcgui.Dialog()
_languagesetting = _addon.getSettingInt('language')
_language = LANGUAGES[_languagesetting]
_cache_long = _addon.getSettingInt('cache_details_days')
_cache_short = _addon.getSettingInt('cache_list_days')
_tmdb_apikey = _addon.getSetting('tmdb_apikey')
_tmdb = TMDb(api_key=_tmdb_apikey, language=_language, cache_long=_cache_long, cache_short=_cache_short,
             append_to_response=APPEND_TO_RESPONSE, addon_name=_addonname)
_omdb_apikey = _addon.getSetting('omdb_apikey')
_omdb = OMDb(api_key=_omdb_apikey, cache_long=_cache_long, cache_short=_cache_short, addon_name=_addonname) if _omdb_apikey else None
_kodimoviedb = KodiLibrary(dbtype='movie')
_koditvshowdb = KodiLibrary(dbtype='tvshow')


class Container(object):
    def __init__(self):
        self.paramstring = sys.argv[2][1:] if sys.version_info.major == 3 else sys.argv[2][1:].decode("utf-8")
        self.params = dict(parse_qsl(self.paramstring))
        self.plugincategory = 'TMDb Helper'
        self.containercontent = ''
        self.library = 'video'
        self.router()

    def start_container(self):
        xbmcplugin.setPluginCategory(_handle, self.plugincategory)  # Container.PluginCategory
        xbmcplugin.setContent(_handle, self.containercontent)  # Container.Content

    def finish_container(self):
        xbmcplugin.endOfDirectory(_handle)

    def get_tmdb_id(self):
        if not self.params.get('tmdb_id'):
            itemtype = TMDB_LISTS.get(self.params.get('info'), {}).get('tmdb_check_id', self.params.get('type'))
            self.params['tmdb_id'] = _tmdb.get_tmdb_id(itemtype=itemtype, imdb_id=self.params.get('imdb_id'), query=self.params.get('query'), year=self.params.get('year'))

    def textviewer(self):
        _dialog.textviewer(self.params.get('header'), self.params.get('text'))

    def imageviewer(self):
        xbmc.executebuiltin('ShowPicture({0})'.format(self.params.get('image')))

    def list_basedir(self):
        self.start_container()
        for category_info in BASEDIR:
            category = TMDB_LISTS.get(category_info, {})
            for tmdb_type in category.get('types', []):
                label = category.get('name', '').format(TYPE_CONVERSION.get(tmdb_type, {}).get('plural', ''))
                listitem = ListItem(label=label)
                listitem.create_listitem(_handle, info=category_info, type=tmdb_type)
        self.finish_container()

    def list_items(self, itemlist, dbtype=None, nexttype=None, info=None, url_info=None, url_tmdb=True):
        if itemlist:
            self.start_container()
            dbiditems = []
            tmdbitems = []
            added_items = []
            detailed_item = None
            tv_detailed_item = None
            ratings_awards = None
            for item in itemlist:
                # DUPLICATE CHECKING
                add_item = u'{0}{1}'.format(item.get('label'), item.get('poster'))
                if add_item in added_items:
                    continue
                added_items.append(add_item)

                # URL ENCODING
                item['url'] = item.get('url') if item.get('url') else {'info': url_info}
                item['url']['type'] = nexttype if nexttype else self.params.get('type')
                if url_tmdb and item.get('tmdb_id'):
                    item['url']['tmdb_id'] = item.get('tmdb_id')

                # SPECIAL URL ENCODING FOR TEXT AND IMAGE VIEWERS
                if item['url'].get('info') == 'imageviewer':
                    item['url'] = {'info': 'imageviewer', 'image': item.get('icon')}
                elif item['url'].get('info') == 'textviewer':
                    item['url'] = {'info': 'textviewer', 'header': item.get('label'), 'text': item.get('infolabels', {}).get('plot')}

                # SPECIAL TREATMENT OF SEASONS AND EPISODES
                if self.params.get('info') in ['seasons', 'episodes'] or item['url'].get('type') in ['season', 'episode']:
                    item['url']['tmdb_id'] = self.params.get('tmdb_id')
                    item['url']['season'] = item.get('infolabels', {}).get('season')
                    item['url']['episode'] = item.get('infolabels', {}).get('episode')
                    if not tv_detailed_item:
                        tv_detailed_item = _tmdb.get_detailed_item('tv', self.params.get('tmdb_id'), season=self.params.get('season', None))
                    if tv_detailed_item:
                        item = utils.del_empty_keys(item)
                        item['infolabels'] = utils.del_empty_keys(item.get('infolabels', {}))
                        item['infoproperties'] = utils.del_empty_keys(item.get('infoproperties', {}))
                        item['infolabels'] = utils.merge_two_dicts(tv_detailed_item.get('infolabels', {}), item.get('infolabels', {}))
                        item['infoproperties'] = utils.merge_two_dicts(tv_detailed_item.get('infoproperties', {}), item.get('infoproperties', {}))
                        item = utils.merge_two_dicts(tv_detailed_item, item)

                # ADD CACHED TMDB DETAILS
                if item['url'].get('type') in ['movie', 'tv']:
                    detailed_item = _tmdb.get_detailed_item(item['url'].get('type'), item['url'].get('tmdb_id'), cache_only=True)
                    if detailed_item:
                        detailed_item['infolabels'] = utils.merge_two_dicts(item.get('infolabels', {}), detailed_item.get('infolabels', {}))
                        detailed_item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), detailed_item.get('infoproperties', {}))
                        detailed_item['label'] = item.get('label')
                        item = utils.merge_two_dicts(item, detailed_item)

                # ADD CACHED OMDB RATINGS AND AWARDS
                if _omdb and item['url'].get('type') == 'movie' and item.get('infolabels', {}).get('imdbnumber'):
                    ratings_awards = _omdb.get_ratings_awards(imdb_id=item.get('infolabels', {}).get('imdbnumber'), cache_only=True)
                    if ratings_awards:
                        item['infoproperties'] = utils.merge_two_dicts(item.get('infoproperties', {}), ratings_awards)

                # GET DBID
                kodidatabase = None
                if item['url'].get('type') == 'movie':
                    kodidatabase = _kodimoviedb
                elif item['url'].get('type') == 'tv':
                    kodidatabase = _koditvshowdb
                if kodidatabase:
                    item['dbid'] = kodidatabase.get_dbid(imdb_id=item.get('infolabels', {}).get('imdbnumber'), originaltitle=item.get('infolabels', {}).get('originaltitle'), title=item.get('infolabels', {}).get('title'), year=item.get('infolabels', {}).get('year'))

                # ADD TO APPROPRIATE LIST FOR SORTING
                if item.get('dbid'):
                    dbiditems.append(item)
                else:
                    tmdbitems.append(item)

            # RECREATE ITEMLIST WITH DBIDITEMS FIRST THEN BUILD LISTITEMS
            itemlist = dbiditems + tmdbitems
            for item in itemlist:
                url = item.pop('url', {})
                item.setdefault('infolabels', {})['mediatype'] = dbtype if dbtype else ''
                listitem = ListItem(library=self.library, **item)
                listitem.create_listitem(_handle, **url)
            self.finish_container()

            # SET SOME SPECIAL PROPERTIES
            if self.params.get('prop_id'):
                window_prop = '{0}{1}.NumDBIDItems'.format(_prefixname, self.params.get('prop_id'))
                xbmcgui.Window(10000).setProperty(window_prop, str(len(dbiditems)))
                window_prop = '{0}{1}.NumTMDBItems'.format(_prefixname, self.params.get('prop_id'))
                xbmcgui.Window(10000).setProperty(window_prop, str(len(tmdbitems)))

    def list_tmdb(self, *args, **kwargs):
        if self.params.get('type'):
            category = TMDB_LISTS.get(self.params.get('info', ''), {})
            path = category.get('path', '').format(**self.params)
            kwparams = utils.make_kwparams(self.params)
            kwparams = utils.merge_two_dicts(kwparams, kwargs)
            kwparams.setdefault('key', category.get('key', 'results'))
            url_info = TMDB_LISTS.get(self.params.get('info'), {}).get('url_info', 'details')
            itemlist = _tmdb.get_list(path, *args, **kwparams)
            itemtype = TMDB_LISTS.get(self.params.get('info'), {}).get('itemtype') or self.params.get('type') or ''
            nexttype = TMDB_LISTS.get(self.params.get('info'), {}).get('nexttype', None)
            self.plugincategory = category.get('name', '').format(TYPE_CONVERSION.get(itemtype, {}).get('plural', ''))
            self.containercontent = TYPE_CONVERSION.get(itemtype, {}).get('container', '')
            self.list_items(itemlist, dbtype=TYPE_CONVERSION.get(itemtype, {}).get('dbtype'), nexttype=nexttype, url_info=url_info)

    def list_details(self):
        # GET THE DETAILED ITEM FROM TMDb
        if self.params.get('type') == 'episode':
            itemdetails = _tmdb.get_detailed_item('tv', self.params.get('tmdb_id'), self.params.get('season'), self.params.get('episode'))
        else:
            itemdetails = _tmdb.get_detailed_item(self.params.get('type'), self.params.get('tmdb_id'))

        # ADD OMDb RATINGS
        if _omdb and itemdetails and self.params.get('type') == 'movie' and itemdetails.get('infolabels', {}).get('imdbnumber'):
            ratings_awards = _omdb.get_ratings_awards(imdb_id=itemdetails.get('infolabels', {}).get('imdbnumber'))
            if ratings_awards:
                itemdetails['infoproperties'] = utils.merge_two_dicts(itemdetails.get('infoproperties', {}), ratings_awards)

        # SET DETAILED ITEM AS FIRST ITEM AND BUILD RELEVANT CATEGORIES
        if itemdetails:
            itemlist = []
            itemlist.append(itemdetails)
            for category in TMDB_CATEGORIES:
                if self.params.get('type') in TMDB_LISTS.get(category, {}).get('types'):
                    categoryitem = itemdetails.copy()
                    categoryitem['label'] = TMDB_LISTS.get(category, {}).get('name')
                    categoryitem['url'] = categoryitem.get('url', {}).copy()
                    categoryitem['url']['info'] = category
                    itemlist.append(categoryitem)
            self.plugincategory = itemdetails.get('label')
            self.containercontent = TYPE_CONVERSION.get(self.params.get('type'), {}).get('container', '')
            self.list_items(itemlist, dbtype=TYPE_CONVERSION.get(self.params.get('type'), {}).get('dbtype', ''))

    def list_credits(self, key='cast'):
        itemlist = _tmdb.get_credits_list(self.params.get('type'), self.params.get('tmdb_id'), key)
        self.plugincategory = key.capitalize()
        self.containercontent = 'actors'
        self.list_items(itemlist, nexttype='person', url_info='details')

    def list_search(self):
        if not self.params.get('query'):
            self.params['query'] = _dialog.input('Enter Search Query', type=xbmcgui.INPUT_ALPHANUM)
        if self.params.get('query'):
            self.list_tmdb(query=self.params.get('query'), year=self.params.get('year'))

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
        elif self.params.get('info') in BASEDIR:
            self.list_tmdb()
        elif self.params.get('info') in TMDB_LISTS and TMDB_LISTS.get(self.params.get('info'), {}).get('path'):
            self.get_tmdb_id()
            self.list_tmdb()
        elif not self.params:
            self.list_basedir()
