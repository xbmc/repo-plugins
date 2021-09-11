import random
import xbmcgui
from resources.lib.kodi.rpc import get_kodi_library
from resources.lib.addon.plugin import convert_type, PLUGINPATH
from resources.lib.addon.constants import TRAKT_BASIC_LISTS, TRAKT_SYNC_LISTS, TRAKT_LIST_OF_LISTS
from resources.lib.addon.plugin import ADDON
from resources.lib.addon.parser import try_int, encode_url
from resources.lib.api.mapping import get_empty_item
from resources.lib.addon.timedate import get_calendar_name
from resources.lib.trakt.api import get_sort_methods


class TraktLists():
    def list_trakt(self, info, tmdb_type, page=None, randomise=False, **kwargs):
        if tmdb_type == 'both':
            return self.list_mixed(info)
        info_model = TRAKT_BASIC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        trakt_type = convert_type(tmdb_type, 'trakt')
        items = self.trakt_api.get_basic_list(
            path=info_model.get('path', '').format(trakt_type=trakt_type, **kwargs),
            trakt_type=trakt_type,
            params=info_model.get('params'),
            page=page,
            authorize=info_model.get('authorize', False),
            sort_by=info_model.get('sort_by', None),
            sort_how=info_model.get('sort_how', None),
            extended=info_model.get('extended', None),
            randomise=randomise)
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        return items

    def list_mixed(self, info, **kwargs):
        info_model = TRAKT_BASIC_LISTS.get(info)
        items = self.trakt_api.get_mixed_list(
            path=info_model.get('path', ''),
            trakt_types=['movie', 'show'],
            authorize=info_model.get('authorize', False),
            extended=info_model.get('extended', None))
        self.tmdb_cache_only = False
        self.library = 'video'
        self.container_content = 'movies'
        self.kodi_db = self.get_kodi_database('both')
        return items

    def list_sync(self, info, tmdb_type, page=None, **kwargs):
        info_model = TRAKT_SYNC_LISTS.get(info)
        info_tmdb_type = info_model.get('tmdb_type') or tmdb_type
        items = self.trakt_api.get_sync_list(
            sync_type=info_model.get('sync_type', ''),
            trakt_type=convert_type(tmdb_type, 'trakt'),
            page=page,
            params=info_model.get('params'),
            sort_by=kwargs.get('sort_by', None) or info_model.get('sort_by', None),
            sort_how=kwargs.get('sort_how', None) or info_model.get('sort_how', None))
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(info_tmdb_type)
        self.library = convert_type(info_tmdb_type, 'library')
        self.container_content = convert_type(info_tmdb_type, 'container')
        return items

    def list_lists(self, info, page=None, **kwargs):
        info_model = TRAKT_LIST_OF_LISTS.get(info)
        items = self.trakt_api.get_list_of_lists(
            path=info_model.get('path', '').format(**kwargs),
            page=page,
            authorize=info_model.get('authorize', False))
        self.library = 'video'
        return items

    def list_lists_search(self, query=None, **kwargs):
        if not query:
            kwargs['query'] = query = xbmcgui.Dialog().input(ADDON.getLocalizedString(32044))
            if not kwargs['query']:
                return
            self.container_update = u'{},replace'.format(encode_url(PLUGINPATH, **kwargs))
        items = self.trakt_api.get_list_of_lists(path=u'search/list?query={}'.format(query))
        self.library = 'video'
        return items

    def _list_trakt_sortby_item(self, i, params):
        item = get_empty_item()
        item['label'] = item['infolabels']['title'] = '{}[CR]{}'.format(params.get('list_name'), i['name'])
        item['params'] = params
        for k, v in i['params'].items():
            item['params'][k] = v
        return item

    def list_trakt_sortby(self, info, **kwargs):
        kwargs['info'] = kwargs.pop('parent_info', None)
        items = get_sort_methods() if kwargs['info'] == 'trakt_userlist' else get_sort_methods(True)
        items = [self._list_trakt_sortby_item(i, kwargs.copy()) for i in items]
        self.library = 'video'
        return items

    def list_userlist(self, list_slug, user_slug=None, page=None, **kwargs):
        response = self.trakt_api.get_custom_list(
            page=page or 1,
            list_slug=list_slug,
            user_slug=user_slug,
            sort_by=kwargs.get('sort_by', None),
            sort_how=kwargs.get('sort_how', None),
            extended=kwargs.get('extended', None),
            authorize=False if user_slug else True)
        if not response:
            return []
        self.tmdb_cache_only = False
        self.library = 'video'
        lengths = [
            len(response.get('movies', [])),
            len(response.get('tvshows', [])),
            len(response.get('persons', []))]
        if lengths.index(max(lengths)) == 0:
            self.container_content = 'movies'
        elif lengths.index(max(lengths)) == 1:
            self.container_content = 'tvshows'
        elif lengths.index(max(lengths)) == 2:
            self.container_content = 'actors'

        if lengths[0] and lengths[1]:
            self.kodi_db = self.get_kodi_database('both')
        elif lengths[0]:
            self.kodi_db = self.get_kodi_database('movie')
        elif lengths[1]:
            self.kodi_db = self.get_kodi_database('tvshow')

        return response.get('items', []) + response.get('next_page', [])

    def list_becauseyouwatched(self, info, tmdb_type, page=None, **kwargs):
        trakt_type = convert_type(tmdb_type, 'trakt')
        watched_items = self.trakt_api.get_sync_list(
            sync_type='watched',
            trakt_type=trakt_type,
            page=1,
            limit=5,
            next_page=False,
            params=None,
            sort_by='plays' if info == 'trakt_becausemostwatched' else 'watched',
            sort_how='desc')
        if not watched_items:
            return
        item = watched_items[random.randint(0, len(watched_items) - 1)]
        self.parent_params = {
            'info': 'recommendations',
            'tmdb_type': item.get('params', {}).get('tmdb_type'),
            'tmdb_id': item.get('params', {}).get('tmdb_id')}
        self.plugin_category = u'{} {}'.format(ADDON.getLocalizedString(32288), item.get('label'))
        return self.list_tmdb(
            info='recommendations',
            tmdb_type=item.get('params', {}).get('tmdb_type'),
            tmdb_id=item.get('params', {}).get('tmdb_id'),
            page=1)

    def list_inprogress(self, info, tmdb_type, page=None, **kwargs):
        if tmdb_type != 'tv':
            return self.list_sync(info, tmdb_type, page, **kwargs)
        items = self.trakt_api.get_inprogress_shows_list(
            page=page,
            params={
                'info': 'trakt_upnext',
                'tmdb_type': 'tv',
                'tmdb_id': '{tmdb_id}'},
            sort_by=kwargs.get('sort_by', None),
            sort_how=kwargs.get('sort_how', None))
        self.tmdb_cache_only = False
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = convert_type(tmdb_type, 'library')
        self.container_content = convert_type(tmdb_type, 'container')
        return items

    def list_nextepisodes(self, info, tmdb_type, page=None, **kwargs):
        if tmdb_type != 'tv':
            return
        sort_by_premiered = True if ADDON.getSettingString('trakt_nextepisodesort') == 'airdate' else False
        items = self.trakt_api.get_upnext_episodes_list(page=page, sort_by_premiered=sort_by_premiered)
        self.tmdb_cache_only = False
        # self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = 'video'
        self.container_content = 'episodes'
        self.thumb_override = ADDON.getSettingInt('calendar_art')
        return items

    def list_trakt_calendar(self, info, startdate, days, page=None, library=False, **kwargs):
        kodi_db = get_kodi_library('tv') if library else None
        items = self.trakt_api.get_calendar_episodes_list(
            try_int(startdate),
            try_int(days),
            kodi_db=kodi_db,
            user=False if library else True,
            page=page)
        self.kodi_db = kodi_db or self.get_kodi_database('tv')
        self.tmdb_cache_only = False
        self.library = 'video'
        self.container_content = 'episodes'
        self.plugin_category = get_calendar_name(startdate=try_int(startdate), days=try_int(days))
        self.thumb_override = ADDON.getSettingInt('calendar_art')
        return items

    def list_upnext(self, info, tmdb_type, tmdb_id, page=None, **kwargs):
        if tmdb_type != 'tv':
            return
        items = self.trakt_api.get_upnext_list(unique_id=tmdb_id, id_type='tmdb', page=page)
        self.tmdb_cache_only = False
        if not items:
            items = self.tmdb_api.get_episode_list(tmdb_id, 1)
            self.tmdb_cache_only = True
        self.kodi_db = self.get_kodi_database(tmdb_type)
        self.library = 'video'
        self.container_content = 'episodes'
        return items
