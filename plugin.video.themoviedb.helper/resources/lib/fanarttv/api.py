import xbmc
import xbmcgui
from resources.lib.addon.cache import CACHE_EXTENDED
from resources.lib.api.request import RequestAPI
from resources.lib.container.listitem import ListItem
from resources.lib.addon.plugin import ADDON, get_language
from resources.lib.addon.setutils import del_empty_keys
from resources.lib.addon.decorators import busy_dialog
from resources.lib.addon.parser import try_int
# from resources.lib.addon.decorators import timer_report


API_URL = 'http://webservice.fanart.tv/v3'
ARTWORK_TYPES = {
    'movies': {
        'clearart': ['hdmovieclearart', 'movieclearart'],
        'clearlogo': ['hdmovielogo', 'movielogo'],
        'discart': ['moviedisc'],
        'poster': ['movieposter'],
        'fanart': ['moviebackground'],
        'landscape': ['moviethumb'],
        'banner': ['moviebanner']},
    'tv': {
        'clearart': ['hdclearart', 'clearart'],
        'clearlogo': ['hdtvlogo', 'clearlogo'],
        'characterart': ['characterart'],
        'poster': ['tvposter'],
        'fanart': ['showbackground'],
        'landscape': ['tvthumb'],
        'banner': ['tvbanner']}}


def add_extra_art(source, output={}):
    if not source:
        return output
    output.update({u'fanart{}'.format(x): i['url'] for x, i in enumerate(source, 1) if i.get('url')})
    return output


class FanartTV(RequestAPI):
    def __init__(
            self,
            api_key='fcca59bee130b70db37ee43e63f8d6c1',
            client_key=ADDON.getSettingString('fanarttv_clientkey'),
            language=get_language(),
            cache_only=False,
            cache_refresh=False):
        super(FanartTV, self).__init__(
            req_api_name='FanartTV',
            req_api_url=API_URL,
            req_api_key=u'api_key={}'.format(api_key))
        self.req_api_key = u'api_key={0}'.format(api_key) if api_key else self.req_api_key
        self.req_api_key = u'{0}&client_key={1}'.format(self.req_api_key, client_key) if client_key else self.req_api_key
        self.language = language[:2] if language else 'en'
        self.cache_only = cache_only
        self.cache_refresh = cache_refresh
        self.req_strip.append(('&client_key={}'.format(client_key), ''))

    def get_artwork_request(self, ftv_id, ftv_type):
        """
        ftv_type can be 'movies' 'tv'
        ftv_id is tmdb_id|imdb_id for movies and tvdb_id for tv
        """
        if not ftv_type or not ftv_id:
            return
        return self.get_request(
            ftv_type, ftv_id,
            cache_force=7,  # Force the cache to save a dummy dict for 7 days so that we don't bother requesting 404s multiple times
            cache_fallback={'dummy': None},
            cache_days=CACHE_EXTENDED,
            cache_only=self.cache_only,
            cache_refresh=self.cache_refresh)

    def _get_artwork_type(self, ftv_id, ftv_type, artwork_type):
        if not artwork_type:
            return
        response = self.get_artwork_request(ftv_id, ftv_type)
        if not response:
            return
        return response.get(artwork_type) or []

    def get_artwork_type(self, ftv_id, ftv_type, artwork_type):
        return self._cache.use_cache(
            self._get_artwork_type, ftv_id, ftv_type, artwork_type,
            cache_name=u'FanartTV.type.{}.{}.{}.{}'.format(self.language, ftv_id, ftv_type, artwork_type),
            cache_only=self.cache_only,
            cache_refresh=self.cache_refresh)

    def _get_best_artwork(self, ftv_id, ftv_type, artwork_type):
        artwork = self.get_artwork_type(ftv_id, ftv_type, artwork_type)
        best_like = -1
        best_item = None
        for i in artwork:
            if i.get('lang', '') == self.language:
                return i.get('url', '')
            if (i.get('lang', '') == 'en' or not i.get('lang')) and try_int(i.get('likes', 0)) > try_int(best_like):
                best_item = i.get('url', '')
                best_like = i.get('likes', 0)
        return best_item

    def get_best_artwork(self, ftv_id, ftv_type, artwork_type):
        return self._cache.use_cache(
            self._get_best_artwork, ftv_id, ftv_type, artwork_type,
            cache_name=u'FanartTV.best.{}.{}.{}.{}'.format(self.language, ftv_id, ftv_type, artwork_type),
            cache_only=self.cache_only,
            cache_refresh=self.cache_refresh)

    def _get_artwork_func(self, ftv_id, ftv_type, artwork_type, get_list=False):
        func = self.get_best_artwork if not get_list else self.get_artwork_type
        return func(ftv_id, ftv_type, artwork_type)

    def get_movies_clearart(self, ftv_id, get_list=False):
        artwork = self._get_artwork_func(ftv_id, 'movies', 'hdmovieclearart', get_list=get_list)
        return artwork or self._get_artwork_func(ftv_id, 'movies', 'movieclearart', get_list=get_list)

    def get_movies_clearlogo(self, ftv_id, get_list=False):
        artwork = self._get_artwork_func(ftv_id, 'movies', 'hdmovielogo', get_list=get_list)
        return artwork or self._get_artwork_func(ftv_id, 'movies', 'movielogo', get_list=get_list)

    def get_movies_discart(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'movies', 'moviedisc', get_list=get_list)

    def get_movies_poster(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'movies', 'movieposter', get_list=get_list)

    def get_movies_fanart(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'movies', 'moviebackground', get_list=get_list)

    def get_movies_landscape(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'movies', 'moviethumb', get_list=get_list)

    def get_movies_banner(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'movies', 'moviebanner', get_list=get_list)

    def get_tv_clearart(self, ftv_id, get_list=False):
        artwork = self._get_artwork_func(ftv_id, 'tv', 'hdclearart', get_list=get_list)
        return artwork or self._get_artwork_func(ftv_id, 'tv', 'clearart', get_list=get_list)

    def get_tv_clearlogo(self, ftv_id, get_list=False):
        artwork = self._get_artwork_func(ftv_id, 'tv', 'hdtvlogo', get_list=get_list)
        return artwork or self._get_artwork_func(ftv_id, 'tv', 'clearlogo', get_list=get_list)

    def get_tv_banner(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'tv', 'tvbanner', get_list=get_list)

    def get_tv_landscape(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'tv', 'tvthumb', get_list=get_list)

    def get_tv_fanart(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'tv', 'showbackground', get_list=get_list)

    def get_tv_poster(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'tv', 'tvposter', get_list=get_list)

    def get_tv_characterart(self, ftv_id, get_list=False):
        return self._get_artwork_func(ftv_id, 'tv', 'characterart', get_list=get_list)

    def get_tv_all_artwork(self, ftv_id):
        if self.get_artwork_request(ftv_id, 'tv'):  # Check we can get the request first so we don't re-ask eight times if it 404s
            return add_extra_art(self.get_tv_fanart(ftv_id, get_list=True), del_empty_keys({
                'clearart': self.get_tv_clearart(ftv_id),
                'clearlogo': self.get_tv_clearlogo(ftv_id),
                'banner': self.get_tv_banner(ftv_id),
                'landscape': self.get_tv_landscape(ftv_id),
                'fanart': self.get_tv_fanart(ftv_id),
                'characterart': self.get_tv_characterart(ftv_id),
                'poster': self.get_tv_poster(ftv_id)}))

    def get_movies_all_artwork(self, ftv_id):
        if self.get_artwork_request(ftv_id, 'movies'):  # Check we can get the request first so we don't re-ask eight times if it 404s
            return add_extra_art(self.get_movies_fanart(ftv_id, get_list=True), del_empty_keys({
                'clearart': self.get_movies_clearart(ftv_id),
                'clearlogo': self.get_movies_clearlogo(ftv_id),
                'banner': self.get_movies_banner(ftv_id),
                'landscape': self.get_movies_landscape(ftv_id),
                'fanart': self.get_movies_fanart(ftv_id),
                'poster': self.get_movies_poster(ftv_id),
                'discart': self.get_movies_discart(ftv_id)}))

    def get_all_artwork(self, ftv_id, ftv_type):
        if ftv_type == 'movies':
            return self.get_movies_all_artwork(ftv_id)
        if ftv_type == 'tv':
            return self.get_tv_all_artwork(ftv_id)

    def refresh_all_artwork(self, ftv_id, ftv_type, ok_dialog=True, container_refresh=True):
        self.cache_refresh = True
        with busy_dialog():
            artwork = self.get_all_artwork(ftv_id, ftv_type)
        if ok_dialog and not artwork:
            xbmcgui.Dialog().ok('FanartTV', ADDON.getLocalizedString(32217).format(ftv_type, ftv_id))
        if ok_dialog and artwork:
            xbmcgui.Dialog().ok('FanartTV', ADDON.getLocalizedString(32218).format(
                ftv_type, ftv_id, ', '.join([k.capitalize() for k, v in artwork.items() if v])))
        if artwork and container_refresh:
            xbmc.executebuiltin('Container.Refresh')
            xbmc.executebuiltin('UpdateLibrary(video,/fake/path/to/force/refresh/on/home)')
        return artwork

    def get_artwork(self, ftv_id, ftv_type, artwork_type, get_list=False):
        if ftv_type == 'movies':
            if artwork_type == 'clearart':
                return self.get_movies_clearart(ftv_id, get_list=get_list)
            if artwork_type == 'clearlogo':
                return self.get_movies_clearlogo(ftv_id, get_list=get_list)
            if artwork_type == 'banner':
                return self.get_movies_banner(ftv_id, get_list=get_list)
            if artwork_type == 'landscape':
                return self.get_movies_landscape(ftv_id, get_list=get_list)
            if artwork_type == 'fanart':
                return self.get_movies_fanart(ftv_id, get_list=get_list)
            if artwork_type == 'poster':
                return self.get_movies_poster(ftv_id, get_list=get_list)
        if ftv_type == 'tv':
            if artwork_type == 'discart':
                return self.get_tv_discart(ftv_id, get_list=get_list)
            if artwork_type == 'clearart':
                return self.get_tv_clearart(ftv_id, get_list=get_list)
            if artwork_type == 'clearlogo':
                return self.get_tv_clearlogo(ftv_id, get_list=get_list)
            if artwork_type == 'banner':
                return self.get_tv_banner(ftv_id, get_list=get_list)
            if artwork_type == 'landscape':
                return self.get_tv_landscape(ftv_id, get_list=get_list)
            if artwork_type == 'fanart':
                return self.get_tv_fanart(ftv_id, get_list=get_list)
            if artwork_type == 'poster':
                return self.get_tv_poster(ftv_id, get_list=get_list)
            if artwork_type == 'characterart':
                return self.get_tv_characterart(ftv_id, get_list=get_list)

    def select_artwork(self, ftv_id, ftv_type, container_refresh=True, blacklist=[]):
        if ftv_type not in ['movies', 'tv']:
            return
        with busy_dialog():
            artwork = self.get_artwork_request(ftv_id, ftv_type)
        if not artwork:
            return xbmcgui.Dialog().notification('FanartTV', ADDON.getLocalizedString(32217).format(ftv_type, ftv_id))

        # Choose Type
        _artwork_types = ['poster', 'fanart', 'clearart', 'clearlogo', 'landscape', 'banner']
        _artwork_types.append('discart' if ftv_type == 'movies' else 'characterart')
        artwork_types = [i for i in _artwork_types if i not in blacklist]  # Remove types that we previously looked for
        choice = xbmcgui.Dialog().select(xbmc.getLocalizedString(13511), artwork_types)
        if choice == -1:
            return

        # Get artwork of user's choosing
        artwork_type = artwork_types[choice]
        artwork_items = self.get_artwork(ftv_id, ftv_type, artwork_type, get_list=True)

        # If there was not artwork of that type found then blacklist it before re-prompting
        if not artwork_items:
            xbmcgui.Dialog().notification('FanartTV', ADDON.getLocalizedString(32217).format(ftv_type, ftv_id))
            blacklist.append(artwork_types[choice])
            return self.select_artwork(ftv_id, ftv_type, container_refresh, blacklist)

        # Choose artwork from options
        items = [
            ListItem(
                label=i.get('url'),
                label2=ADDON.getLocalizedString(32219).format(i.get('lang', ''), i.get('likes', 0), i.get('id', '')),
                art={'thumb': i.get('url')}).get_listitem() for i in artwork_items if i.get('url')]
        choice = xbmcgui.Dialog().select(xbmc.getLocalizedString(13511), items, useDetails=True)
        if choice == -1:  # If user hits back go back to main menu rather than exit completely
            return self.select_artwork(ftv_id, ftv_type, container_refresh, blacklist)

        # Cache our choice as the best artwork forever since it was selected manually
        # Some types have have HD and SD variants so set cache for both
        for i in ARTWORK_TYPES.get(ftv_type, {}).get(artwork_type, []):
            success = self._cache.set_cache(
                artwork_items[choice].get('url'),
                cache_name=u'FanartTV.best.{}.{}.{}.{}'.format(self.language, ftv_id, ftv_type, i),
                cache_days=10000)
        if success and container_refresh:
            xbmc.executebuiltin('Container.Refresh')
            xbmc.executebuiltin('UpdateLibrary(video,/fake/path/to/force/refresh/on/home)')

    def manage_artwork(self, ftv_id=None, ftv_type=None):
        if not ftv_id or not ftv_type:
            return
        choice = xbmcgui.Dialog().contextmenu([
            ADDON.getLocalizedString(32220),
            ADDON.getLocalizedString(32221)])
        if choice == -1:
            return
        if choice == 0:
            return self.select_artwork(ftv_id=ftv_id, ftv_type=ftv_type)
        if choice == 1:
            return self.refresh_all_artwork(ftv_id=ftv_id, ftv_type=ftv_type)
