import sys
import xbmc
import xbmcplugin
from threading import Thread
from resources.lib.addon.constants import NO_LABEL_FORMATTING, RANDOMISED_TRAKT, RANDOMISED_LISTS, TRAKT_LIST_OF_LISTS, TMDB_BASIC_LISTS, TRAKT_BASIC_LISTS, TRAKT_SYNC_LISTS, ROUTE_NO_ID, ROUTE_TMDB_ID
from resources.lib.kodi.rpc import get_kodi_library, get_movie_details, get_tvshow_details, get_episode_details, get_season_details
from resources.lib.addon.plugin import convert_type, reconfigure_legacy_params
from resources.lib.script.router import related_lists
from resources.lib.container.listitem import ListItem
from resources.lib.tmdb.api import TMDb
from resources.lib.trakt.api import TraktAPI
from resources.lib.fanarttv.api import FanartTV
from resources.lib.omdb.api import OMDb
from resources.lib.player.players import Players
from resources.lib.addon.plugin import ADDON, kodi_log
from resources.lib.container.basedir import BaseDirLists
from resources.lib.tmdb.lists import TMDbLists
from resources.lib.trakt.lists import TraktLists
from resources.lib.tmdb.search import SearchLists
from resources.lib.tmdb.discover import UserDiscoverLists
from resources.lib.api.mapping import set_show, get_empty_item
from resources.lib.addon.parser import parse_paramstring, try_int
from resources.lib.addon.setutils import split_items, random_from_list, merge_two_dicts


def filtered_item(item, key, value, exclude=False):
    boolean = False if exclude else True  # Flip values if we want to exclude instead of include
    if key and value and item.get(key) == value:
        boolean = exclude
    return boolean


class Container(TMDbLists, BaseDirLists, SearchLists, UserDiscoverLists, TraktLists):
    def __init__(self):
        self.handle = int(sys.argv[1])
        self.paramstring = sys.argv[2][1:]
        self.params = parse_paramstring(self.paramstring)
        self.parent_params = self.params
        # self.container_path = u'{}?{}'.format(sys.argv[0], self.paramstring)
        self.update_listing = False
        self.plugin_category = ''
        self.container_content = ''
        self.container_update = None
        self.container_refresh = False
        self.item_type = None
        self.kodi_db = None
        self.kodi_db_tv = {}
        self.library = None
        self.tmdb_cache_only = True
        self.tmdb_api = TMDb()
        self.trakt_watchedindicators = ADDON.getSettingBool('trakt_watchedindicators')
        self.trakt_api = TraktAPI()
        self.is_widget = True if self.params.pop('widget', '').lower() == 'true' else False
        self.hide_watched = ADDON.getSettingBool('widgets_hidewatched') if self.is_widget else False
        self.flatten_seasons = ADDON.getSettingBool('flatten_seasons')
        self.ftv_forced_lookup = self.params.pop('fanarttv', '').lower()
        self.ftv_api = FanartTV(cache_only=self.ftv_is_cache_only())
        self.omdb_api = OMDb() if ADDON.getSettingString('omdb_apikey') else None
        self.filter_key = self.params.pop('filter_key', None)
        self.filter_value = split_items(self.params.pop('filter_value', None))[0]
        self.exclude_key = self.params.pop('exclude_key', None)
        self.exclude_value = split_items(self.params.pop('exclude_value', None))[0]
        self.pagination = self.pagination_is_allowed()
        self.params = reconfigure_legacy_params(**self.params)
        self.thumb_override = 0

    def pagination_is_allowed(self):
        if self.params.pop('nextpage', '').lower() == 'false':
            return False
        if self.is_widget and not ADDON.getSettingBool('widgets_nextpage'):
            return False
        return True

    def ftv_is_cache_only(self):
        if self.ftv_forced_lookup == 'true':
            return False
        if self.ftv_forced_lookup == 'false':
            return True
        if self.is_widget and ADDON.getSettingBool('widget_fanarttv_lookup'):
            return False
        if not self.is_widget and ADDON.getSettingBool('fanarttv_lookup'):
            return False
        return True

    def _add_item(self, x, li, cache_only=True, ftv_art=None):
        li.set_details(details=self.get_tmdb_details(li, cache_only=cache_only))
        li.set_details(details=ftv_art or self.get_ftv_artwork(li), reverse=True)
        self.items_queue[x] = li

    def add_items(self, items=None, pagination=True, parent_params=None, property_params=None, kodi_db=None, cache_only=True):
        if not items:
            return
        check_is_aired = parent_params.get('info') not in NO_LABEL_FORMATTING
        hide_nodate = ADDON.getSettingBool('nodate_is_unaired')

        # Pre-game details and artwork cache for seasons/episodes before threading to avoid multiple API calls
        ftv_art = None
        if parent_params.get('info') in ['seasons', 'episodes', 'episode_groups', 'trakt_upnext']:
            details = self.tmdb_api.get_details('tv', parent_params.get('tmdb_id'), parent_params.get('season', 0), cache_only=cache_only)
            ftv_art = self.get_ftv_artwork(ListItem(parent_params=parent_params, **details))

        # Build empty queue and thread pool
        self.items_queue, pool = [None] * len(items), [None] * len(items)

        # Start item build threads
        for x, i in enumerate(items):
            if not pagination and 'next_page' in i:
                continue
            if self.item_is_excluded(i):
                continue
            li = ListItem(parent_params=parent_params, **i)
            pool[x] = Thread(target=self._add_item, args=[x, li, cache_only, ftv_art])
            pool[x].start()

        # Wait to join threads in pool first before adding item to directory
        for x, i in enumerate(pool):
            if not i:
                continue
            i.join()
            li = self.items_queue[x]
            if not li:
                continue
            li.set_episode_label()
            if check_is_aired and li.is_unaired(no_date=hide_nodate):
                continue
            li.set_details(details=self.get_kodi_details(li), reverse=True)  # Quick because local db
            li.set_playcount(playcount=self.get_playcount_from_trakt(li))  # Quick because of agressive caching of Trakt object and pre-emptive dict comprehension
            if self.hide_watched and try_int(li.infolabels.get('playcount')) != 0:
                continue
            li.set_context_menu()  # Set the context menu items
            li.set_uids_to_info()  # Add unique ids to properties so accessible in skins
            li.set_thumb_to_art(self.thumb_override == 2) if self.thumb_override else None
            li.set_params_reroute(self.ftv_forced_lookup, self.flatten_seasons)  # Reroute details to proper end point
            li.set_params_to_info(self.plugin_category)  # Set path params to properties for use in skins
            li.infoproperties.update(property_params or {})
            if self.thumb_override:
                li.infolabels.pop('dbid', None)  # Need to pop the DBID if overriding thumb otherwise Kodi overrides after item is created
            xbmcplugin.addDirectoryItem(
                handle=self.handle,
                url=li.get_url(),
                listitem=li.get_listitem(),
                isFolder=li.is_folder)

    def set_params_to_container(self, **kwargs):
        params = {}
        for k, v in kwargs.items():
            if not k or not v:
                continue
            try:
                k = u'Param.{}'.format(k)
                v = u'{}'.format(v)
                params[k] = v
                xbmcplugin.setProperty(self.handle, k, v)  # Set params to container properties
            except Exception as exc:
                kodi_log(u'Error: {}\nUnable to set param {} to {}'.format(exc, k, v), 1)
        return params

    def finish_container(self, update_listing=False, plugin_category='', container_content=''):
        xbmcplugin.setPluginCategory(self.handle, plugin_category)  # Container.PluginCategory
        xbmcplugin.setContent(self.handle, container_content)  # Container.Content
        xbmcplugin.endOfDirectory(self.handle, updateListing=update_listing)

    def item_is_excluded(self, item):
        if self.filter_key and self.filter_value:
            if self.filter_key in item.get('infolabels', {}):
                if filtered_item(item['infolabels'], self.filter_key, self.filter_value):
                    return True
            elif self.filter_key in item.get('infoproperties', {}):
                if filtered_item(item['infoproperties'], self.filter_key, self.filter_value):
                    return True
        if self.exclude_key and self.exclude_value:
            if self.exclude_key in item.get('infolabels', {}):
                if filtered_item(item['infolabels'], self.exclude_key, self.exclude_value, True):
                    return True
            elif self.exclude_key in item.get('infoproperties', {}):
                if filtered_item(item['infoproperties'], self.exclude_key, self.exclude_value, True):
                    return True

    def get_tmdb_details(self, li, cache_only=True):
        if not self.tmdb_api:
            return
        return self.tmdb_api.get_details(
            li.get_tmdb_type(),
            li.unique_ids.get('tvshow.tmdb') if li.infolabels.get('mediatype') in ['season', 'episode'] else li.unique_ids.get('tmdb'),
            li.infolabels.get('season', 0) if li.infolabels.get('mediatype') in ['season', 'episode'] else None,
            li.infolabels.get('episode') if li.infolabels.get('mediatype') == 'episode' else None,
            cache_only=cache_only)

    def get_ftv_artwork(self, li):
        if not self.ftv_api:
            return
        artwork = self.ftv_api.get_all_artwork(li.get_ftv_id(), li.get_ftv_type())
        if not artwork:
            return
        if li.infolabels.get('mediatype') in ['season', 'episode']:
            artwork = {u'tvshow.{}'.format(k): v for k, v in artwork.items() if v}
        return {'art': artwork}

    def get_playcount_from_trakt(self, li):
        if not self.trakt_watchedindicators:
            return
        if li.infolabels.get('mediatype') == 'movie':
            return self.trakt_api.get_movie_playcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb')))
        if li.infolabels.get('mediatype') == 'episode':
            return self.trakt_api.get_episode_playcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tvshow.tmdb')),
                season=li.infolabels.get('season'),
                episode=li.infolabels.get('episode'))
        if li.infolabels.get('mediatype') == 'tvshow':
            li.infolabels['episode'] = self.trakt_api.get_episodes_airedcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb')))
            return self.trakt_api.get_episodes_watchcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb')))
        if li.infolabels.get('mediatype') == 'season':
            li.infolabels['episode'] = self.trakt_api.get_episodes_airedcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb')),
                season=li.infolabels.get('season'))
            return self.trakt_api.get_episodes_watchcount(
                id_type='tmdb',
                unique_id=try_int(li.unique_ids.get('tmdb')),
                season=li.infolabels.get('season'))

    def get_kodi_database(self, tmdb_type):
        if ADDON.getSettingBool('local_db'):
            return get_kodi_library(tmdb_type)

    def get_kodi_parent_dbid(self, li):
        if not self.kodi_db:
            return
        if li.infolabels.get('mediatype') in ['movie', 'tvshow']:
            return self.kodi_db.get_info(
                info='dbid',
                imdb_id=li.unique_ids.get('imdb'),
                tmdb_id=li.unique_ids.get('tmdb'),
                tvdb_id=li.unique_ids.get('tvdb'),
                originaltitle=li.infolabels.get('originaltitle'),
                title=li.infolabels.get('title'),
                year=li.infolabels.get('year'))
        if li.infolabels.get('mediatype') in ['season', 'episode']:
            return self.kodi_db.get_info(
                info='dbid',
                imdb_id=li.unique_ids.get('tvshow.imdb'),
                tmdb_id=li.unique_ids.get('tvshow.tmdb'),
                tvdb_id=li.unique_ids.get('tvshow.tvdb'),
                title=li.infolabels.get('tvshowtitle'))

    def get_kodi_details(self, li):
        if not self.kodi_db:
            return
        dbid = self.get_kodi_parent_dbid(li)
        if not dbid:
            return
        if li.infolabels.get('mediatype') == 'movie':
            return get_movie_details(dbid)
        if li.infolabels.get('mediatype') == 'tvshow':
            return get_tvshow_details(dbid)
        if li.infolabels.get('mediatype') == 'season':
            return set_show(self.get_kodi_tvchild_details(
                tvshowid=dbid,
                season=li.infolabels.get('season'),
                is_season=True) or get_empty_item(), get_tvshow_details(dbid))
        if li.infolabels.get('mediatype') == 'episode':
            return set_show(self.get_kodi_tvchild_details(
                tvshowid=dbid,
                season=li.infolabels.get('season'),
                episode=li.infolabels.get('episode')) or get_empty_item(), get_tvshow_details(dbid))

    def get_kodi_tvchild_details(self, tvshowid, season=None, episode=None, is_season=False):
        if not tvshowid or not season or (not episode and not is_season):
            return
        library = 'season' if is_season else 'episode'
        self.kodi_db_tv[tvshowid] = self.kodi_db_tv.get(tvshowid) or get_kodi_library(library, tvshowid)
        if not self.kodi_db_tv[tvshowid].database:
            return
        dbid = self.kodi_db_tv[tvshowid].get_info('dbid', season=season, episode=episode)
        if not dbid:
            return
        details = get_season_details(dbid) if is_season else get_episode_details(dbid)
        details['infoproperties']['tvshow.dbid'] = tvshowid
        return details

    def get_container_content(self, tmdb_type, season=None, episode=None):
        if tmdb_type == 'tv' and season and episode:
            return convert_type('episode', 'container')
        elif tmdb_type == 'tv' and season:
            return convert_type('season', 'container')
        return convert_type(tmdb_type, 'container')

    def list_randomised_trakt(self, **kwargs):
        kwargs['info'] = RANDOMISED_TRAKT.get(kwargs.get('info'), {}).get('info')
        kwargs['randomise'] = True
        self.parent_params = kwargs
        return self.get_items(**kwargs)

    def list_randomised(self, **kwargs):
        params = merge_two_dicts(kwargs, RANDOMISED_LISTS.get(kwargs.get('info'), {}).get('params'))
        item = random_from_list(self.get_items(**params))
        if not item:
            return
        self.plugin_category = item.get('label')
        self.parent_params = item.get('params', {})
        return self.get_items(**item.get('params', {}))

    def get_tmdb_id(self, info, **kwargs):
        if info == 'collection':
            kwargs['tmdb_type'] = 'collection'
        return self.tmdb_api.get_tmdb_id(**kwargs)

    def _noop(self):
        return None

    def _get_items(self, func, **kwargs):
        return func['lambda'](getattr(self, func['getattr']), **kwargs)

    def get_items(self, **kwargs):
        info = kwargs.get('info')

        # Check routes that don't require ID lookups first
        route = ROUTE_NO_ID
        route.update(TRAKT_LIST_OF_LISTS)
        route.update(RANDOMISED_LISTS)
        route.update(RANDOMISED_TRAKT)

        # Early exit if we have a route
        if info in route:
            return self._get_items(route[info]['route'], **kwargs)

        # Check routes that require ID lookups second
        route = ROUTE_TMDB_ID
        route.update(TMDB_BASIC_LISTS)
        route.update(TRAKT_BASIC_LISTS)
        route.update(TRAKT_SYNC_LISTS)

        # Early exit to basedir if no route found
        if info not in route:
            return self.list_basedir(info)

        # Lookup up our TMDb ID
        if not kwargs.get('tmdb_id'):
            kwargs['tmdb_id'] = self.get_tmdb_id(**kwargs)

        return self._get_items(route[info]['route'], **kwargs)

    def get_directory(self):
        items = self.get_items(**self.params)
        if not items:
            return
        self.add_items(
            items,
            pagination=self.pagination,
            parent_params=self.parent_params,
            property_params=self.set_params_to_container(**self.params),
            kodi_db=self.kodi_db,
            cache_only=self.tmdb_cache_only if not self.ftv_api else False)
        self.finish_container(
            update_listing=self.update_listing,
            plugin_category=self.plugin_category,
            container_content=self.container_content)
        if self.container_update:
            xbmc.executebuiltin(u'Container.Update({})'.format(self.container_update))
        if self.container_refresh:
            xbmc.executebuiltin('Container.Refresh')

    def play_external(self, **kwargs):
        kodi_log(['lib.container.router - Attempting to play item\n', kwargs], 1)
        if not kwargs.get('tmdb_id'):
            kwargs['tmdb_id'] = self.tmdb_api.get_tmdb_id(**kwargs)
        Players(**kwargs).play(handle=self.handle if self.handle != -1 else None)

    def context_related(self, **kwargs):
        if not kwargs.get('tmdb_id'):
            kwargs['tmdb_id'] = self.tmdb_api.get_tmdb_id(**kwargs)
        kwargs['container_update'] = True
        related_lists(include_play=True, **kwargs)

    def router(self):
        if self.params.get('info') == 'play':
            return self.play_external(**self.params)
        if self.params.get('info') == 'related':
            return self.context_related(**self.params)
        return self.get_directory()
