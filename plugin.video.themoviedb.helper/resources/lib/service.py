import sys
import xbmc
import xbmcgui
from resources.lib.plugin import Plugin
import resources.lib.utils as utils
_setmain = {'label', 'icon', 'poster', 'thumb', 'fanart', 'tmdb_id', 'imdb_id'}
_setinfo = {
    'title', 'originaltitle', 'tvshowtitle', 'plot', 'rating', 'votes', 'premiered', 'year', 'imdbnumber', 'tagline',
    'status', 'episode', 'season', 'genre', 'set', 'studio', 'country', 'MPAA', 'director', 'writer', 'trailer'}
_setprop = {
    'tvdb_id', 'biography', 'birthday', 'age', 'deathday', 'character', 'department', 'job', 'known_for', 'role',
    'born', 'creator', 'aliases', 'budget', 'revenue', 'set.tmdb_id', 'set.name', 'set.poster', 'set.fanart',
    'awards', 'metacritic_rating', 'imdb_rating', 'imdb_votes', 'rottentomatoes_rating', 'rottentomatoes_image',
    'rottentomatoes_reviewtotal', 'rottentomatoes_reviewsfresh', 'rottentomatoes_reviewsrotten',
    'rottentomatoes_consensus', 'rottentomatoes_usermeter', 'rottentomatoes_userreviews', 'trakt_rating', 'trakt_votes'}


class ServiceMonitor(Plugin):
    def __init__(self):
        super(ServiceMonitor, self).__init__()
        self.kodimonitor = xbmc.Monitor()
        self.container = 'Container.'
        self.containeritem = 'ListItem.'
        self.cur_item = 0
        self.pre_item = 1
        self.pre_folder = None
        self.cur_folder = None
        self.properties = set()
        self.indxproperties = set()
        self.home = xbmcgui.Window(10000)
        self.run_monitor()

    def run_monitor(self):
        self.home.setProperty('TMDbHelper.ServiceStarted', 'True')
        while not self.kodimonitor.abortRequested():
            if xbmc.getCondVisibility("!Skin.HasSetting(TMDbHelper.Service)"):
                self.kodimonitor.waitForAbort(30)

            # skip when modal dialogs are opened (e.g. textviewer in musicinfo dialog)
            elif xbmc.getCondVisibility(
                    "Window.IsActive(DialogSelect.xml) | Window.IsActive(progressdialog) | "
                    "Window.IsActive(contextmenu) | Window.IsActive(busydialog)"):
                self.kodimonitor.waitForAbort(2)

            # skip when container scrolling
            elif xbmc.getCondVisibility(
                    "Container.OnScrollNext | Container.OnScrollPrevious | Container.Scrolling"):
                if (self.properties or self.indxproperties) and self.get_cur_item() != self.pre_item:
                    self.clear_properties()
                self.kodimonitor.waitForAbort(1)  # Maybe clear props here too

            # media window is opened or widgetcontainer set - start listitem monitoring!
            elif xbmc.getCondVisibility(
                    "Window.IsMedia | !String.IsEmpty(Window(Home).Property(TMDbHelper.WidgetContainer)) | Window.IsVisible(movieinformation)"):
                self.get_listitem()
                self.kodimonitor.waitForAbort(0.15)

            # clear window props
            elif self.properties or self.indxproperties:
                self.clear_properties()

            else:
                self.kodimonitor.waitForAbort(1)

    def get_cur_item(self):
        self.dbtype = self.get_dbtype()
        self.imdb_id = self.get_infolabel('IMDBNumber')
        self.query = self.get_infolabel('TvShowTitle') or self.get_infolabel('Title') or self.get_infolabel('Label')
        self.year = self.get_infolabel('year')
        self.season = self.get_infolabel('Season') if self.dbtype == 'episodes' else ''
        self.episode = self.get_infolabel('Episode') if self.dbtype == 'episodes' else ''
        if not sys.version_info.major == 3:
            self.query = self.query.decode('utf-8')
        return u'{0}.{1}.{2}.{3}.{4}'.format(self.imdb_id, self.query, self.year, self.season, self.episode)

    def get_listitem(self):
        try:
            self.get_container()
            self.cur_item = self.get_cur_item()
            if self.cur_item == self.pre_item:
                return  # Don't get details if we already did last time!
            self.pre_item = self.cur_item

            self.cur_folder = '{0}{1}{2}'.format(
                self.container, xbmc.getInfoLabel(self.get_dbtype()),
                xbmc.getInfoLabel('{0}NumItems'.format(self.container)))
            if self.cur_folder != self.pre_folder:
                self.clear_properties()  # Clear props if the folder changed
                self.pre_folder = self.cur_folder

            if self.dbtype in ['tvshows', 'seasons', 'episodes']:
                tmdbtype = 'tv'
            elif self.dbtype in ['movies']:
                tmdbtype = 'movie'
            elif self.dbtype in ['sets']:
                tmdbtype = 'collection'
            elif self.dbtype in ['actors', 'directors']:
                tmdbtype = 'person'
            else:
                return

            self.home.setProperty('TMDbHelper.IsUpdating', 'True')

            tmdb_id = self.get_tmdb_id(tmdbtype, self.imdb_id, self.query, self.year)
            details = self.tmdb.get_detailed_item(tmdbtype, tmdb_id, season=self.season, episode=self.episode)
            details = self.get_omdb_ratings(details) if self.dbtype == 'movies' else details
            details = self.get_trakt_ratings(
                details, tmdbtype=tmdbtype, tmdb_id=tmdb_id, season=self.season,
                episode=self.episode) if self.dbtype in ['movies', 'tvshows', 'seasons', 'episodes'] else details

            if not details:
                self.clear_properties()
                return

            self.set_properties(details)

        except Exception as exc:
            utils.kodi_log('Func: get_listitem\n{0}'.format(exc), 1)

    def clear_property(self, key):
        try:
            self.home.clearProperty('TMDbHelper.ListItem.{0}'.format(key))
        except Exception as exc:
            utils.kodi_log('Func: clear_property\n{0}{1}'.format(key, exc), 1)

    def clear_properties(self):
        for k in self.properties:
            self.clear_property(k)
        self.properties = set()
        for k in self.indxproperties:
            self.clear_property(k)
        self.indxproperties = set()
        self.pre_item = None

    def set_property(self, key, value):
        try:
            self.home.setProperty('TMDbHelper.ListItem.{0}'.format(key), u'{0}'.format(value))
        except Exception as exc:
            utils.kodi_log('{0}{1}'.format(key, exc), 1)

    def set_indx_properties(self, dictionary):
        if not isinstance(dictionary, dict):
            return

        indxprops = set()
        for k, v in dictionary.items():
            if k in self.properties:
                continue
            try:
                v = v or ''
                self.set_property(k, v)
                indxprops.add(k)
            except Exception as exc:
                utils.kodi_log('k: {0} v: {1} e: {2}'.format(k, v, exc), 1)

        for k in (self.indxproperties - indxprops):
            self.clear_property(k)
        self.indxproperties = indxprops.copy()

    def set_iter_properties(self, dictionary, keys):
        if not isinstance(dictionary, dict):
            return
        for k in keys:
            try:
                v = dictionary.get(k)
                v = v or ''
                if isinstance(v, list):
                    try:
                        v = ' / '.join(v)
                    except Exception as exc:
                        utils.kodi_log('Func: set_iter_properties - list\n{0}'.format(exc), 1)
                self.properties.add(k)
                self.set_property(k, v)
            except Exception as exc:
                'k: {0} e: {1}'.format(k, exc)

    def set_list_properties(self, items, key, prop):
        if not isinstance(items, list):
            return
        try:
            joinlist = [i.get(key) for i in items[:10] if i.get(key)]
            joinlist = ' / '.join(joinlist)
            self.properties.add(prop)
            self.set_property(prop, joinlist)
        except Exception as exc:
            utils.kodi_log('Func: set_list_properties\n{0}'.format(exc), 1)

    def set_time_properties(self, duration):
        try:
            minutes = duration // 60 % 60
            hours = duration // 60 // 60
            totalmin = duration // 60
            self.set_property('Duration', totalmin)
            self.set_property('Duration_H', hours)
            self.set_property('Duration_M', minutes)
            self.set_property('Duration_HHMM', '{0:02d}:{1:02d}'.format(hours, minutes))
            self.properties.update(['Duration', 'Duration_H', 'Duration_M', 'Duration_HHMM'])
        except Exception as exc:
            'Func: set_time_properties\n{0}'.format(exc)

    def set_properties(self, item):
        self.set_iter_properties(item, _setmain)
        self.set_time_properties(item.get('infolabels', {}).get('duration', 0))
        self.set_list_properties(item.get('cast', []), 'name', 'cast')
        self.set_iter_properties(item.get('infolabels', {}), _setinfo)
        self.set_iter_properties(item.get('infoproperties', {}), _setprop)
        self.set_indx_properties(item.get('infoproperties', {}))
        self.home.clearProperty('TMDbHelper.IsUpdating')

    def get_container(self):
        widgetid = utils.try_parse_int(self.home.getProperty('TMDbHelper.WidgetContainer'))
        self.container = 'Container({0}).'.format(widgetid) if widgetid else 'Container.'
        self.containeritem = '{0}ListItem.'.format(self.container) if not xbmc.getCondVisibility("Window.IsVisible(movieinformation)") else 'ListItem.'

    def get_dbtype(self):
        dbtype = xbmc.getInfoLabel('{0}DBTYPE'.format(self.containeritem))
        return '{0}s'.format(dbtype) if dbtype else xbmc.getInfoLabel('Container.Content()') or ''

    def get_infolabel(self, infolabel):
        return xbmc.getInfoLabel('{0}{1}'.format(self.containeritem, infolabel))

    def get_position(self):
        return xbmc.getInfoLabel('{0}CurrentItem'.format(self.container))

    def get_tmdb_id(self, itemtype, imdb_id=None, query=None, year=None):
        try:
            if imdb_id and imdb_id.startswith('tt'):
                return self.tmdb.get_tmdb_id(itemtype=itemtype, imdb_id=imdb_id)
            return self.tmdb.get_tmdb_id(itemtype=itemtype, query=query, year=year)
        except Exception as exc:
            utils.kodi_log('Func: get_tmdb_id\n{0}'.format(exc), 1)
            return
