import xbmc
import xbmcgui
from resources.lib.addon.constants import ACCEPTED_MEDIATYPES
from resources.lib.addon.plugin import ADDON, ADDONPATH, PLUGINPATH, kodi_log, convert_media_type
from resources.lib.addon.parser import try_int, encode_url
from resources.lib.addon.timedate import is_unaired_timestamp
from resources.lib.addon.setutils import merge_two_dicts
from resources.lib.container.context import ContextMenu
# from resources.lib.addon.decorators import timer_report


def ListItem(*args, **kwargs):
    """ Factory to build ListItem object """
    factory = {
        'none': _ListItem,
        'movie': _Movie,
        'tvshow': _Tvshow,
        'season': _Season,
        'episode': _Episode,
        'video': _Video,
        'set': _Collection,
        'studio': _Studio,
        'keyword': _Keyword,
        'person': _Person}
    mediatype = kwargs.get('infolabels', {}).get('mediatype')
    if kwargs.get('infoproperties', {}).get('tmdb_type') == 'person':
        mediatype = 'person'
    if mediatype not in factory:
        mediatype = 'none'
    return factory[mediatype](*args, **kwargs)


class _ListItem(object):
    def __init__(
            self, label=None, label2=None, path=None, library=None, is_folder=True, params=None, next_page=None,
            parent_params=None, infolabels=None, infoproperties=None, art=None, cast=None,
            context_menu=None, stream_details=None, unique_ids=None,
            **kwargs):
        self.label = label or ''
        self.label2 = label2 or ''
        self.path = path or PLUGINPATH
        self.params = params or {}
        self.parent_params = parent_params or {}
        self.library = library or 'video'
        self.is_folder = is_folder
        self.infolabels = infolabels or {}
        self.infoproperties = infoproperties or {}
        self.art = art or {}
        self.cast = cast or []
        self.context_menu = context_menu or []
        self.stream_details = stream_details or {}
        self.unique_ids = unique_ids or {}
        self._set_as_next_page(next_page)

    def _set_as_next_page(self, next_page=None):
        if not next_page:
            return
        self.label = xbmc.getLocalizedString(33078)
        self.art['thumb'] = u'{}/resources/icons/tmdb/nextpage.png'.format(ADDONPATH)
        self.art['landscape'] = u'{}/resources/icons/tmdb/nextpage_wide.png'.format(ADDONPATH)
        self.infoproperties['specialsort'] = 'bottom'
        self.params = self.parent_params.copy()
        self.params['page'] = next_page
        self.params.pop('update_listing', None)  # Just in case we updated the listing for search results
        self.path = PLUGINPATH
        self.is_folder = True

    def set_art_fallbacks(self):
        if not self.art.get('thumb'):
            self.art['thumb'] = u'{}/resources/poster.png'.format(ADDONPATH)
        if not self.art.get('fanart'):
            self.art['fanart'] = u'{}/fanart.jpg'.format(ADDONPATH)
        return self.art

    def set_thumb_to_art(self, prefer_landscape=False):
        if prefer_landscape:
            if self.art.get('landscape'):
                self.art['thumb'] = self.art['landscape']
                return self.art['landscape']
            if self.art.get('tvshow.landscape'):
                self.art['thumb'] = self.art['tvshow.landscape']
                return self.art['tvshow.landscape']
        if self.art.get('fanart'):
            self.art['thumb'] = self.art['fanart']
            return self.art['fanart']
        if self.art.get('tvshow.fanart'):
            self.art['thumb'] = self.art['tvshow.fanart']
            return self.art['tvshow.fanart']

    def get_trakt_type(self):
        return convert_media_type(self.infolabels.get('mediatype'), 'trakt')

    def get_tmdb_type(self):
        return convert_media_type(self.infolabels.get('mediatype'), 'tmdb', parent_type=True)

    def get_ftv_type(self):
        return convert_media_type(self.infolabels.get('mediatype'), 'ftv')

    def get_ftv_id(self):
        return None

    def get_tmdb_id(self):
        return self.unique_ids.get('tmdb')

    def is_unaired(self, format_label=None, check_hide_settings=True, no_date=True):
        return

    def unaired_bool(self):
        return False

    def set_context_menu(self):
        for k, v in ContextMenu(self).get():
            self.infoproperties[k] = v

    def set_playcount(self, playcount):
        return

    def set_details(self, details=None, reverse=False):
        if not details:
            return
        self.stream_details = merge_two_dicts(details.get('stream_details', {}), self.stream_details, reverse=reverse)
        self.infolabels = merge_two_dicts(details.get('infolabels', {}), self.infolabels, reverse=reverse)
        self.infoproperties = merge_two_dicts(details.get('infoproperties', {}), self.infoproperties, reverse=reverse)
        self.art = merge_two_dicts(details.get('art', {}), self.art, reverse=reverse)
        self.unique_ids = merge_two_dicts(details.get('unique_ids', {}), self.unique_ids, reverse=reverse)
        self.cast = self.cast or details.get('cast', [])

    def _set_params_reroute_skinshortcuts(self):
        self.params['widget'] = 'true'
        # Reroute sortable lists to display options in skinshortcuts
        if self.infoproperties.get('tmdbhelper.context.sorting'):
            self.params['parent_info'] = self.params['info']
            self.params['info'] = 'trakt_sortby'

    def set_params_reroute(self, ftv_forced_lookup=False, flatten_seasons=False):
        if xbmc.getCondVisibility("Window.IsVisible(script-skinshortcuts.xml)"):
            self._set_params_reroute_skinshortcuts()

        if ftv_forced_lookup:  # Take fanarttv param from parent list with us onto subsequent pages
            self.params['fanarttv'] = ftv_forced_lookup

        if self.params.get('info') == 'details':  # Reconfigure details item into play/browse etc.
            self._set_params_reroute_details(flatten_seasons)

    def _set_params_reroute_details(self, flatten_seasons):
        return  # Done in child class

    def set_episode_label(self, format_label=None):
        return  # Done in child class

    def set_uids_to_info(self):
        for k, v in self.unique_ids.items():
            if not v:
                continue
            self.infoproperties[u'{}_id'.format(k)] = v

    def set_params_to_info(self, widget=None):
        for k, v in self.params.items():
            if not k or not v:
                continue
            self.infoproperties[u'item.{}'.format(k)] = v
        if self.params.get('tmdb_type'):
            self.infoproperties['item.type'] = self.params['tmdb_type']
        if widget:
            self.infoproperties['widget'] = widget

    def get_url(self):
        return encode_url(self.path, **self.params)

    def get_listitem(self):
        if self.infolabels.get('mediatype') not in ACCEPTED_MEDIATYPES:
            self.infolabels.pop('mediatype', None)
        self.infolabels['path'] = self.get_url()
        listitem = xbmcgui.ListItem(label=self.label, label2=self.label2, path=self.infolabels['path'])
        listitem.setLabel2(self.label2)
        listitem.setInfo(self.library, self.infolabels)
        listitem.setArt(self.set_art_fallbacks())
        if self.library == 'pictures':
            return listitem
        listitem.setUniqueIDs(self.unique_ids)
        listitem.setProperties(self.infoproperties)
        listitem.setCast(self.cast)
        listitem.addContextMenuItems(self.context_menu)

        if not self.stream_details:
            return listitem
        for k, v in self.stream_details.items():
            if not k or not v:
                continue
            for i in v:
                if not i:
                    continue
                listitem.addStreamInfo(k, i)
        return listitem


class _Keyword(_ListItem):
    def _set_params_reroute_details(self, flatten_seasons):
        self.params['info'] = 'discover'
        self.params['tmdb_type'] = 'movie'
        self.params['with_keywords'] = self.unique_ids.get('tmdb')
        self.params['with_id'] = 'True'
        self.is_folder = True


class _Studio(_ListItem):
    def _set_params_reroute_details(self, flatten_seasons):
        self.params['info'] = 'discover'
        self.params['tmdb_type'] = 'movie'
        self.params['with_companies'] = self.unique_ids.get('tmdb')
        self.params['with_id'] = 'True'
        self.is_folder = True


class _Person(_ListItem):
    def _set_params_reroute_details(self, flatten_seasons):
        self.params['info'] = 'related'
        self.params['tmdb_type'] = 'person'
        self.params['tmdb_id'] = self.unique_ids.get('tmdb')
        self.is_folder = False

    def get_tmdb_type(self):
        return 'person'


class _Collection(_ListItem):
    def _set_params_reroute_details(self, flatten_seasons):
        self.params['info'] = 'collection'


class _Video(_ListItem):
    def is_unaired(self, format_label=u'[COLOR=ffcc0000][I]{}[/I][/COLOR]', check_hide_settings=True, no_date=True):
        try:
            if not is_unaired_timestamp(self.infolabels.get('premiered'), no_date):
                return
            if format_label:
                self.label = format_label.format(self.label)
        except Exception as exc:
            kodi_log(u'Error: {}'.format(exc), 1)
        if not check_hide_settings:
            return True
        return self.unaired_bool()

    def _set_params_reroute_default(self):
        if not ADDON.getSettingInt('default_select'):
            self.params['info'] = 'play'
            if not ADDON.getSettingBool('only_resolve_strm'):
                self.infoproperties['isPlayable'] = 'true'
        else:
            self.params['info'] = 'related'
        self.is_folder = False
        self.infoproperties['tmdbhelper.context.playusing'] = u'{}&ignore_default=true'.format(self.get_url())

    def _set_params_reroute_details(self, flatten_seasons):
        self._set_params_reroute_default()


class _Movie(_Video):
    def get_ftv_id(self):
        return self.unique_ids.get('tmdb')

    def set_playcount(self, playcount):
        playcount = try_int(playcount)
        if not playcount:
            return
        self.infolabels['playcount'] = playcount
        self.infolabels['overlay'] = 5

    def unaired_bool(self):
        if ADDON.getSettingBool('hide_unaired_movies'):
            return True

    def _set_params_reroute_details(self, flatten_seasons):
        self._set_params_reroute_default()


class _Tvshow(_Video):
    def get_ftv_id(self):
        return self.unique_ids.get('tvdb')

    def set_playcount(self, playcount):
        playcount = try_int(playcount)
        if not try_int(self.infolabels.get('episode')):
            return
        ip, il = self.infoproperties, self.infolabels
        ip['watchedepisodes'] = playcount
        ip['totalepisodes'] = try_int(il.get('episode'))
        ip['unwatchedepisodes'] = ip.get('totalepisodes') - try_int(ip.get('watchedepisodes'))
        if not playcount or ip.get('unwatchedepisodes'):
            return
        il['playcount'] = playcount
        il['overlay'] = 5

    def unaired_bool(self):
        if ADDON.getSettingBool('hide_unaired_episodes'):
            return True

    def _set_params_reroute_details(self, flatten_seasons):
        if ADDON.getSettingInt('default_select'):
            self.params['info'] = 'related'
            self.is_folder = False
            return
        self.params['info'] = 'flatseasons' if flatten_seasons else 'seasons'


class _Season(_Tvshow):
    def get_ftv_id(self):
        return self.unique_ids.get('tvshow.tvdb')

    def get_tmdb_id(self):
        return self.unique_ids.get('tvshow.tmdb')

    def _set_params_reroute_details(self, flatten_seasons):
        self.params['info'] = 'episodes'


class _Episode(_Tvshow):
    def get_ftv_id(self):
        return self.unique_ids.get('tvshow.tvdb')

    def get_tmdb_id(self):
        return self.unique_ids.get('tvshow.tmdb')

    def set_playcount(self, playcount):
        playcount = try_int(playcount)
        if not playcount:
            return
        self.infolabels['playcount'] = playcount
        self.infolabels['overlay'] = 5

    def _set_params_reroute_details(self, flatten_seasons):
        if (self.parent_params.get('info') == 'library_nextaired'
                and ADDON.getSettingBool('nextaired_linklibrary')
                and self.infoproperties.get('tvshow.dbid')):
            self.path = u'videodb://tvshows/titles/{}/'.format(self.infoproperties['tvshow.dbid'])
            self.params = {}
            self.is_folder = True
            return
        self._set_params_reroute_default()

    def set_episode_label(self, format_label=u'{season}x{episode:0>2}. {label}'):
        season = try_int(self.infolabels.get('season', 0))
        episode = try_int(self.infolabels.get('episode', 0))
        if not season or not episode:
            return
        self.label = format_label.format(season=season, episode=episode, label=self.infolabels.get('title', ''))
