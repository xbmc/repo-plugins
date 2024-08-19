from xbmcgui import ListItem as KodiListItem
from jurialmunkey.parser import try_int, merge_two_dicts
from infotagger.listitem import ListItemInfoTag
from tmdbhelper.lib.addon.consts import ACCEPTED_MEDIATYPES, PARAM_WIDGETS_RELOAD, PARAM_WIDGETS_RELOAD_FORCED
from tmdbhelper.lib.addon.plugin import ADDONPATH, PLUGINPATH, convert_media_type, get_setting, get_condvisibility, get_localized, encode_url
from tmdbhelper.lib.addon.tmdate import is_unaired_timestamp
from tmdbhelper.lib.addon.logger import kodi_log
from jurialmunkey.window import get_property

""" Lazyimports
from tmdbhelper.lib.items.context import ContextMenu
"""


_is_skinshortcuts = get_condvisibility("Window.IsVisible(script-skinshortcuts.xml)") or get_property('IsSkinShortcut')
_is_skinshortcuts_standard = _is_skinshortcuts and get_property('IsStandardSkinShortcut')
_int_default_select = get_setting('default_select', 'int')
_is_only_resolve_strm = get_setting('only_resolve_strm')
_is_hide_unaired_movies = get_setting('hide_unaired_movies')
_is_hide_unaired_episodes = get_setting('hide_unaired_episodes')
_is_flatten_seasons = get_setting('flatten_seasons')
_is_nextaired_linklibrary = get_setting('nextaired_linklibrary')
_is_trakt_watchedindicators = get_setting('trakt_watchedindicators')


def ListItem(*args, **kwargs):
    """ Factory to build ListItem object """
    factory = {
        'movie': _Movie,
        'tvshow': _Tvshow,
        'season': _Season,
        'episode': _Episode,
        'video': _Video,
        'set': _Collection,
        'studio': _Studio,
        'keyword': _Keyword,
        'person': _Person}
    if kwargs.get('next_page'):
        return _NextPage(*args, **kwargs)._configure()
    if kwargs.get('infoproperties', {}).get('tmdb_type') == 'person':
        return _Person(*args, **kwargs)
    mediatype = kwargs.get('infolabels', {}).get('mediatype')
    try:
        return factory[mediatype](*args, **kwargs)
    except KeyError:
        return _ListItem(*args, **kwargs)


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
        self.next_page = next_page

    def set_art_fallbacks(self):
        if not self.art.get('icon'):
            self.art['icon'] = self.art.get('poster') or f'{ADDONPATH}/resources/icons/themoviedb/default.png'
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

    @property
    def trakt_type(self):
        return convert_media_type(self.infolabels.get('mediatype'), 'trakt')

    @property
    def tmdb_type(self):
        return convert_media_type(self.infolabels.get('mediatype'), 'tmdb', parent_type=True)

    @property
    def ftv_type(self):
        return convert_media_type(self.infolabels.get('mediatype'), 'ftv')

    @property
    def ftv_id(self):
        return None

    @property
    def tmdb_id(self):
        return self.unique_ids.get('tmdb')

    @property
    def season(self):
        return None

    @property
    def episode(self):
        return

    def is_unaired(self, format_label=None, check_hide_settings=True, no_date=True):
        return

    def unaired_bool(self):
        return False

    def set_context_menu(self, additions=None):
        from tmdbhelper.lib.items.context import ContextMenu
        self.context_menu += ContextMenu(self).get()
        if not additions:
            return
        self.context_menu += additions

    def set_playcount(self, playcount):
        return

    def set_details(self, details=None, reverse=False, override=False):
        if not details:
            return
        self.stream_details = merge_two_dicts(details.get('stream_details', {}), self.stream_details, reverse=reverse)
        self.infolabels = merge_two_dicts(details.get('infolabels', {}), self.infolabels, reverse=reverse)
        self.infoproperties = merge_two_dicts(details.get('infoproperties', {}), self.infoproperties, reverse=reverse)
        self.art = merge_two_dicts(details.get('art', {}), self.art, reverse=reverse)
        self.unique_ids = merge_two_dicts(details.get('unique_ids', {}), self.unique_ids, reverse=reverse)
        self.cast = self.cast or details.get('cast', [])
        if not override:
            return
        self.label = details.get('label') or self.label
        self.infolabels['title'] = details.get('infolabels', {}).get('title') or self.infolabels.get('title')
        self.infolabels['tvshowtitle'] = details.get('infolabels', {}).get('tvshowtitle') or self.infolabels.get('tvshowtitle')

    def _set_params_reroute_skinshortcuts(self):
        if not _is_skinshortcuts_standard:
            self.params['widget'] = 'true'
        # Reroute sortable lists to display options in skinshortcuts
        if self.infoproperties.get('is_sortable'):
            self.params['parent_info'] = self.params['info']
            self.params['info'] = 'trakt_sortby'
        # Add param to empty search to ensure reloads
        if self.params.get('info') == 'search' and not self.params.get('query'):
            self.params['reload'] = 'forced'

    def set_params_reroute(self, is_fanarttv=False, extended=None, is_cacheonly=False):
        if _is_skinshortcuts and self.path.startswith(PLUGINPATH):
            self._set_params_reroute_skinshortcuts()

        # Reroute for extended sorting of trakt list by inprogress to open up next folder
        if extended == 'inprogress':
            self.params['info'] = 'trakt_upnext'

        # Reconfigure details item into play/browse etc.
        if self.params.get('info') == 'details':
            return self._set_params_reroute_details()

        # Copy some params to next folder path
        if not self.is_folder:
            return
        if is_cacheonly:
            self.params['cacheonly'] = is_cacheonly
        if is_fanarttv:
            self.params['fanarttv'] = is_fanarttv
            return

    def _set_params_reroute_details(self):
        return  # Done in child class

    def set_episode_label(self, format_label=None):
        return  # Done in child class

    def set_uids_to_info(self):
        for k, v in self.unique_ids.items():
            if not v:
                continue
            self.infoproperties[f'{k}_id'] = v

    def set_params_to_info(self, widget=None):
        for k, v in self.params.items():
            if not k or not v:
                continue
            self.infoproperties[f'item.{k}'] = v
        if self.params.get('tmdb_type'):
            self.infoproperties['item.type'] = self.params['tmdb_type']
        if widget:
            self.infoproperties['widget'] = widget

    def get_url(self):
        def _get_url(path, reload=None, widget=None, **params):
            url = encode_url(path, **params)
            reload_param = PARAM_WIDGETS_RELOAD_FORCED if reload == 'forced' else None  # Note reload not std builtin but param absorbed in kwargs
            if widget and widget.lower() == 'true':
                reload_param = PARAM_WIDGETS_RELOAD
                url = f'{url}&widget=true&{PARAM_WIDGETS_RELOAD}'
            if reload_param:
                url = f'{url}&{reload_param}'
            return url
        return _get_url(self.path, **self.params)

    def get_listitem(self, offscreen=True):
        if self.infolabels.get('mediatype') not in ACCEPTED_MEDIATYPES:
            self.infolabels.pop('mediatype', None)
        self.infolabels['path'] = self.get_url()

        listitem = KodiListItem(label=self.label, label2=self.label2, path=self.infolabels['path'], offscreen=offscreen)
        listitem.setLabel2(self.label2)
        listitem.setArt(self.set_art_fallbacks())

        if self.library != 'pictures':
            info_tag = ListItemInfoTag(listitem)
            info_tag.set_info(self.infolabels)
            info_tag.set_unique_ids(self.unique_ids)
            info_tag.set_cast(self.cast)
            info_tag.set_stream_details(self.stream_details)
            info_tag.set_resume_point(self.infoproperties)

        listitem.setProperties(self.infoproperties)
        listitem.addContextMenuItems(self.context_menu)

        return listitem


class _NextPage(_ListItem):
    def _configure(self):
        """ Run at class initialisation to configure next_page item. Returns self """
        self.label = get_localized(33078)
        self.art['icon'] = f'{ADDONPATH}/resources/icons/themoviedb/nextpage.png'
        self.art['landscape'] = f'{ADDONPATH}/resources/icons/themoviedb/nextpage_wide.png'
        self.infoproperties['specialsort'] = 'bottom'
        self.params = self.parent_params.copy()
        self.params['page'] = self.next_page
        self.params.pop('update_listing', None)  # Just in case we updated the listing for search results
        self.path = PLUGINPATH
        self.is_folder = True
        return self


class _Keyword(_ListItem):
    def _set_params_reroute_details(self):
        self.params['info'] = 'discover'
        self.params['tmdb_type'] = 'movie'
        self.params['with_keywords'] = self.unique_ids.get('tmdb')
        self.params['with_id'] = 'True'
        self.is_folder = True


class _Studio(_ListItem):
    def _set_params_reroute_details(self):
        self.params['info'] = 'discover'
        self.params['tmdb_type'] = 'movie'
        self.params['with_companies'] = self.unique_ids.get('tmdb')
        self.params['with_id'] = 'True'
        self.is_folder = True


class _Person(_ListItem):
    def _set_params_reroute_details(self):
        self.params['info'] = 'related'
        self.params['tmdb_type'] = 'person'
        self.params['tmdb_id'] = self.unique_ids.get('tmdb')
        self.is_folder = False

    @property
    def tmdb_type(self):
        return 'person'


class _Collection(_ListItem):
    def _set_params_reroute_details(self):
        self.params['info'] = 'collection'


class _Video(_ListItem):
    def is_unaired(self, format_label=u'[COLOR=ffcc0000][I]{}[/I][/COLOR]', check_hide_settings=True, no_date=True):
        try:
            if not is_unaired_timestamp(self.infolabels.get('premiered'), no_date):
                return
            if format_label:
                self.label = format_label.format(self.label)
        except Exception as exc:
            kodi_log(f'Error: {exc}', 1)
        if not check_hide_settings:
            return True
        return self.unaired_bool()

    def _set_params_reroute_default(self):
        if not _int_default_select:
            self.params['info'] = 'play'
            if not _is_only_resolve_strm:
                self.infoproperties['isPlayable'] = 'true'
        else:
            self.params['info'] = 'related'
        self.is_folder = False
        self.context_menu.insert(0, (
            '$ADDON[plugin.video.themoviedb.helper 32322]',
            f'RunPlugin({self.get_url()}&ignore_default=true)',))

    def _set_params_reroute_details(self):
        self._set_params_reroute_default()

    def _set_contextmenu_choosedefault(self, tmdb_type, tmdb_id, season=None, episode=None):
        name = self.infolabels.get('tvshowtitle') or self.infolabels.get('title') or self.label
        path = f'set_chosenplayer={name},tmdb_type={tmdb_type},tmdb_id={tmdb_id}'

        if season is not None:
            path = f'{path},season={season}'
            if episode is not None:
                path = f'{path},episode={episode}'

        self.context_menu.append((
            '$ADDON[plugin.video.themoviedb.helper 32476]',
            f'Runscript(plugin.video.themoviedb.helper,{path})',))


class _Movie(_Video):
    @property
    def ftv_id(self):
        return self.unique_ids.get('tmdb')

    def set_playcount(self, playcount):
        playcount = try_int(playcount)
        # Setting playcount to 0 overrides internal playcount from Kodi to allow Trakt to set unwatched
        # Not setting playcount at all will allow Kodi to manage internally instead
        if not _is_trakt_watchedindicators and not playcount:
            return
        self.infolabels['playcount'] = playcount

    def unaired_bool(self):
        if _is_hide_unaired_movies:
            return True

    def _set_params_reroute_details(self):
        self._set_contextmenu_choosedefault('movie', self.unique_ids.get('tmdb'))
        self._set_params_reroute_default()


class _Tvshow(_Video):
    @property
    def ftv_id(self):
        return self.unique_ids.get('tvdb')

    def _set_playcount(self, playcount):
        ip, il = self.infoproperties, self.infolabels
        totalepisodes = try_int(il.get('episode'))
        if not totalepisodes:
            return
        ip['totalepisodes'] = totalepisodes
        if playcount is None:  # Check None instead of "if not playcount" because 0 is valid value
            return
        playcount = try_int(playcount)
        ip['watchedepisodes'] = playcount
        ip['unwatchedepisodes'] = totalepisodes - playcount
        ip['watchedprogress'] = int(playcount * 100 / totalepisodes)
        if ip['unwatchedepisodes']:
            playcount = 0
        il['playcount'] = playcount

    def set_playcount(self, playcount):
        self._set_playcount(playcount)
        season_count = try_int(self.infolabels.get('season'))
        if season_count > 0:
            self.infoproperties['totalseasons'] = season_count

    def unaired_bool(self):
        if _is_hide_unaired_episodes:
            return True

    def _set_params_reroute_details(self):
        self._set_contextmenu_choosedefault('tv', self.unique_ids.get('tmdb'))
        if _int_default_select:
            self.params['info'] = 'related'
            self.is_folder = False
            return
        self.params['info'] = 'flatseasons' if _is_flatten_seasons else 'seasons'


class _Season(_Tvshow):
    @property
    def ftv_id(self):
        return self.unique_ids.get('tvshow.tvdb')

    @property
    def tmdb_id(self):
        return self.unique_ids.get('tvshow.tmdb')

    @property
    def season(self):
        return self.infolabels.get('season')

    def _set_params_reroute_details(self):
        self._set_contextmenu_choosedefault('tv', self.unique_ids.get('tvshow.tmdb'), season=self.infolabels.get('season'))
        self.params['info'] = 'episodes'

    def set_playcount(self, playcount):
        self._set_playcount(playcount)


class _Episode(_Tvshow):
    @property
    def ftv_id(self):
        return self.unique_ids.get('tvshow.tvdb')

    @property
    def tmdb_id(self):
        return self.unique_ids.get('tvshow.tmdb')

    @property
    def season(self):
        return self.infolabels.get('season')

    @property
    def episode(self):
        return self.infolabels.get('episode')

    def set_playcount(self, playcount):
        playcount = try_int(playcount)
        # Setting playcount to 0 overrides internal playcount from Kodi to allow Trakt to set unwatched
        # Not setting playcount at all will allow Kodi to manage internally instead
        if not _is_trakt_watchedindicators and not playcount:
            return
        self.infolabels['playcount'] = playcount

    def _set_params_reroute_details(self):
        self._set_contextmenu_choosedefault(
            'tv', self.unique_ids.get('tvshow.tmdb'),
            season=self.infolabels.get('season'),
            episode=self.infolabels.get('episode'))
        if (self.parent_params.get('info') == 'library_nextaired'
                and _is_nextaired_linklibrary
                and self.infoproperties.get('tvshow.dbid')):
            self.path = f'videodb://tvshows/titles/{self.infoproperties["tvshow.dbid"]}/'
            self.params = {}
            self.is_folder = True
            return
        self._set_params_reroute_default()

    def set_episode_label(self, format_label=u'{season}x{episode:0>2}. {label}'):
        if self.infoproperties.pop('no_label_formatting', None):
            return
        season = try_int(self.infolabels.get('season', 0))
        episode = try_int(self.infolabels.get('episode', 0))
        if not episode:
            return
        self.label = format_label.format(season=season, episode=episode, label=self.infolabels.get('title', ''))
