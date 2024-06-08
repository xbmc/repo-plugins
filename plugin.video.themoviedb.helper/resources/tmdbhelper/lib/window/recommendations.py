import xbmcgui
from xbmc import Monitor
from itertools import zip_longest
from tmdbhelper.lib.items.router import Router
from tmdbhelper.lib.addon.dialog import BusyDialog
from tmdbhelper.lib.addon.thread import ParallelThread
from tmdbhelper.lib.addon.plugin import get_infolabel, executebuiltin, get_condvisibility, ADDONPATH
from tmdbhelper.lib.api.tmdb.api import TMDb
from jurialmunkey.window import get_property, WindowProperty, wait_until_active
from jurialmunkey.parser import parse_paramstring, reconfigure_legacy_params
from threading import Thread


TMDB_QUERY_PARAMS = ('imdb_id', 'tvdb_id', 'query', 'year', 'episode_year',)
TMDB_AFFIX = '&fanarttv=false&cacheonly=true'
PROP_LIST_VISIBLE = 'List_{}_Visible'
PROP_LIST_ISUPDATING = 'List_{}_IsUpdating'
PROP_HIDEINFO = 'Recommendations.HideInfo'
PROP_HIDERECS = 'Recommendations.HideRecs'
PROP_TMDBTYPE = 'Recommendations.TMDbType'
PROP_ISACTIVE = 'Recommendations.IsActive'
PROP_JSONDUMP = 'Recommendations.JSONDump'
PROP_ONCLOSED = 'Recommendations.OnClosed'

ACTION_CONTEXT_MENU = (117,)
ACTION_SHOW_INFO = (11,)
ACTION_SELECT = (7, )
ACTION_CLOSEWINDOW = (9, 10, 92, 216, 247, 257, 275, 61467, 61448,)
ID_VIDEOINFO = 12003


"""
Runscript(plugin.video.themoviedb.helper,recommendations=)
recommendations=list_id(int)|paramstring(str)|related(bool)|action(str) [Separate multiples with || ]
    * The lists to add. Separate additional lists with ||
    * list_id: the container that the items will be added
    * paramstring: the tmdbhelper base path such as info=cast
    * related: whether to add related query params to the paramstring
    * action: the action to perform. can be info|play|text or a Kodi builtin
window_id=window_id(int)
    * The custom window that will act as the base window
setproperty=property(str)
    * Sets Window(Home).Property(TMDbHelper.{property}) to True oninfo until infodialog closes
tmdb_type=type(str)
    * The type of item for related paramstrings
tmdb_id=tmdb_id(int)
    * The tmdb_id for the base item lookup. Optionally can use other standard query= params for lookup
context=builtin(str)
    * The Kodi builtin to call oncontextmenu action
    * If ommitted then standard action for list will be performed

script-tmdbhelper-recommendations.xml
<onload>SetProperty(Action_{list_id},action)</onload>
    * Set an action for an undefined list
"""


class WindowRecommendations(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self._kwargs = kwargs
        self._initialised = False
        self._state = None
        self._monitor = Monitor()
        self._tmdb_api = TMDb()
        self._tmdb_type = get_property(PROP_TMDBTYPE, kwargs['tmdb_type'])
        self._tmdb_affix = f"&nextpage=false{kwargs.get('affix') or TMDB_AFFIX}"
        self._tmdb_query = {i: kwargs[i] for i in TMDB_QUERY_PARAMS if kwargs.get(i)}
        self._tmdb_id = kwargs.get('tmdb_id') or self._tmdb_api.get_tmdb_id(tmdb_type=self._tmdb_type, **self._tmdb_query)
        self._recommendations = sorted(kwargs['recommendations'].split('||'))
        self._recommendations = {
            int(list_id): {'list_id': int(list_id), 'url': url, 'related': related.lower() == 'true', 'action': action}
            for list_id, url, related, action in (i.split('|') for i in self._recommendations)}
        self._queue = (i for i in self._recommendations)
        self._context_action = kwargs.get('context')
        self._window_id = kwargs['window_id']
        self._focus_id = int(kwargs['focus_id']) if 'focus_id' in kwargs else None
        self._window_manager = kwargs['window_manager']
        self._window_properties = {
            k.replace('winprop_', ''): v
            for k, v in kwargs.items()
            if k and k.startswith('winprop_')}
        self._setproperty = kwargs.get('setproperty')

    def onInit(self):
        for k, v in self._window_properties.items():
            self.setProperty(k, v)

        # Check if previously initialised to avoid rebuilding on doModal() when backtracking
        if self._initialised:
            return
        self._initialised = True

        if not self._tmdb_id or not self._recommendations:
            return self.do_close()

        _next_id, _listitems = self._build_next()
        if not _listitems or not _next_id:
            return self.do_close()
        _list_id = self._add_items(_next_id, _listitems)
        _list_id = self._focus_id or _list_id  # Allow skinner to override first list default focus

        Thread(target=self._build_all_in_groups, args=[3, _list_id]).start()  # Don't block closing
        self.setProperty(PROP_LIST_VISIBLE.format('Main'), 'True')

    def _build_next(self):
        try:
            _next_id = next(self._queue)
        except StopIteration:
            return (None, None)
        _listitems = self.build_list(_next_id)
        return (_next_id, _listitems) if _listitems else self._build_next()

    def _build_all_in_groups(self, x, list_id):
        """ Build remaining queue in threaded groups of x items
        PRO: Balances performance for displaying next list in queue and building all lists
        CON: Queued lists might be added slightly out of order
        """
        def _threaditem(i):
            self._add_items(i, self.build_list(i))

        _mon = Monitor()
        for _items in zip_longest(*[iter(self._queue)] * x, fillvalue=None):
            with ParallelThread(_items, _threaditem):
                if list_id:
                    _mon.waitForAbort(0.1)  # Wait to ensure first list is visible
                    self.setFocusId(list_id)  # Setfocus to first list id or custom control
                    list_id = None

    def onAction(self, action):
        _action_id = action.getId()
        if _action_id in ACTION_CLOSEWINDOW:
            return self.do_close()
        if _action_id in ACTION_SHOW_INFO:
            return self.do_action()
        if _action_id in ACTION_CONTEXT_MENU:
            return executebuiltin(self._context_action) if self._context_action else self.do_action()
        if _action_id in ACTION_SELECT:
            return self.do_action()

    def do_close(self):
        self._state = 'onback'
        self.close()

    def do_action(self):
        focus_id = self.getFocusId()
        _action = self.getProperty(f'Action_{focus_id}') or self._recommendations.get(focus_id, {}).get('action')
        if not _action:
            return
        if _action == 'info':
            return self.do_info(focus_id)
        if _action in ['play', 'browse']:
            return self.do_play(focus_id, _action)
        if _action == 'text':
            return self.do_text(focus_id)
        return executebuiltin(_action)

    def do_info(self, focus_id):
        if not focus_id:
            return
        try:
            path = get_infolabel(f'Container({focus_id}).ListItem.FolderPath')
            params = reconfigure_legacy_params(**parse_paramstring(path.split('?')[1]))
            tmdb_type = params['tmdb_type']
            tmdb_id = params['tmdb_id']
        except (TypeError, IndexError, KeyError, AttributeError):
            return
        self._state = 'oninfo'
        self._window_manager.on_info(tmdb_type, tmdb_id, setproperty=self._setproperty)

    def do_text(self, focus_id):
        if not focus_id:
            return
        xbmcgui.Dialog().textviewer('', get_infolabel(f'Container({focus_id}).ListItem.Plot'))

    def do_play(self, focus_id, action):
        if not focus_id:
            return

        with BusyDialog():
            path = get_infolabel(f'Container({focus_id}).ListItem.FolderPath')
            self._window_manager.on_exit()
            self.close()

        if action == 'play':
            builtin = f'PlayMedia({path},playlist_type_hint=1)'
        elif get_condvisibility('Window.IsVisible(MyVideoNav.xml)'):
            builtin = f'Container.Update({path})'
        else:
            builtin = f'ActivateWindow(videos,{path},return)'
        executebuiltin(builtin)

    def _get_items(self, path):
        listitems = Router(-1, path).get_directory(items_only=True) or []
        listitems = [li.get_listitem(offscreen=True) for li in listitems if li]
        return listitems

    def _add_items(self, list_id, listitems):
        if not list_id or not listitems:
            return
        try:
            _lst = self.getControl(list_id)
        except (RuntimeError, TypeError):  # List with that ID doesn't exist so don't build it
            return
        _lst.addItems(listitems)
        self.setProperty(PROP_LIST_VISIBLE.format(list_id), 'True')
        return list_id

    def build_list(self, list_id):
        try:
            self.getControl(list_id)
        except (RuntimeError, TypeError):  # List with that ID doesn't exist so don't build it
            return

        self.setProperty(PROP_LIST_ISUPDATING.format(list_id), 'True')

        affx = f'&tmdb_type={self._tmdb_type}&tmdb_id={self._tmdb_id}' if self._recommendations[list_id]['related'] else ''
        path = f'{self._recommendations[list_id]["url"]}{affx}{self._tmdb_affix}'

        _listitems = self._get_items(path)
        self.clearProperty(PROP_LIST_ISUPDATING.format(list_id))
        return _listitems


class WindowRecommendationsManager():
    def __init__(self, recommendations, window_id, **kwargs):
        self._window_id = int(window_id) + 10000 if int(window_id) < 10000 else int(window_id)
        self._recommendations = recommendations
        self._kwargs = kwargs
        self._gui = None
        self._history = []
        self._mon = Monitor()
        self._current_path = None
        self._current_dump = None

    def router(self):
        if self._recommendations == 'onaction':
            return self.on_exit(**self._kwargs)
        if self._recommendations == 'onback':
            return
        if get_property(PROP_ISACTIVE):
            return self.on_active()
        with WindowProperty((PROP_ISACTIVE, 'True')):
            self.on_info_new() if self._recommendations == 'oninfo' else self.open_recommendations()

    def wait_until_active(self, *args, **kwargs):
        return wait_until_active(*args, xbmc_monitor=self._mon, **kwargs)

    def is_exiting(self):
        if xbmcgui.getCurrentWindowId() != self._window_id:
            return True
        if get_property(PROP_ONCLOSED):
            return True
        return False

    def on_active(self):
        if self.is_exiting():
            return
        self.dump_kwargs()

    def on_info_new(self):
        _tmdb_type = self._kwargs['tmdb_type']
        _tmdb_query = {i: self._kwargs[i] for i in TMDB_QUERY_PARAMS if self._kwargs.get(i)}
        _tmdb_id = self._kwargs.get('tmdb_id') or TMDb().get_tmdb_id(tmdb_type=_tmdb_type, **_tmdb_query)
        if not _tmdb_type or not _tmdb_id:
            return
        self.dump_kwargs(update_current_dump=True)
        self.on_info(_tmdb_type, _tmdb_id)

    def dump_kwargs(self, update_current_dump=False):
        from json import dumps
        data = self._kwargs.copy()
        data['recommendations'] = self._recommendations
        data['window_id'] = self._window_id
        data = dumps(data, separators=(',', ':'))
        if update_current_dump:
            self._current_dump = data
        data = get_property(PROP_JSONDUMP, set_property=data)
        return data

    def open_recommendations(self):
        with BusyDialog():
            self.dump_kwargs(update_current_dump=True)
            self._gui = WindowRecommendations(
                'script-tmdbhelper-recommendations.xml', ADDONPATH, 'default', '1080i',
                recommendations=self._recommendations, window_id=self._window_id, window_manager=self, **self._kwargs)
        self._gui.doModal()
        return self._gui

    def on_join(self, t, path):
        if self.is_exiting():
            return self.on_exit()

        data = None

        # While INFO is active wait in loop until new action or we exit
        while t.is_alive() and not self._mon.abortRequested():

            # If the action trigger changed lets do something
            data = get_property(PROP_JSONDUMP)
            if self._current_dump != data:
                break
            data = None

            # We got an Exit command so we force quit out
            if self.is_exiting():
                return self.on_exit()

            # We sit in a loop and poll ever 100ms
            self._mon.waitForAbort(0.1)

        # Check that the currently active info dialog is the one we want to act
        if self._current_path != path:
            return

        if data:
            from tmdbhelper.lib.files.futils import json_loads as loads
            data = loads(data)

        # The trigger changed so lets open the recommendations window
        if data and self._window_id == data.pop('window_id'):
            self._recommendations = data.pop('recommendations')
            self._kwargs = data
            _gui = self._gui
            data = self._current_dump
            self.open_recommendations()

            # If RECS closed because ONBACK then we need to go back to the previous info and join it
            if self._gui._state == 'onback':
                self._gui = _gui
                self._current_path = path
                return self.on_join(t, path)

        return self.on_back() if self._history and not self.is_exiting() else self.on_exit()

    def on_info(self, tmdb_type, tmdb_id, setproperty=None):
        with BusyDialog():
            listitem = self.get_listitem(tmdb_type, tmdb_id)
            if not listitem:
                return
            self._current_path = listitem.getPath()

        get_property(PROP_HIDEINFO, clear_property=True)
        with WindowProperty((PROP_HIDERECS, 'True'), (setproperty, 'True')):
            self.add_history()
            t = self.open_info(listitem, self._gui.close if self._gui else None, threaded=True)
            self.wait_until_active(ID_VIDEOINFO, poll=0.1)  # Wait to allow info dialog to open

        return self.on_join(t, listitem.getPath())

    def on_back(self, setproperty=None):
        with BusyDialog():
            listitem = self.get_listitem(**self.pop_history())
            if not listitem:
                return self.on_exit()
            self._current_path = listitem.getPath()

        get_property(PROP_HIDERECS, clear_property=True)
        with WindowProperty((PROP_HIDEINFO, 'True'), (setproperty, 'True')):
            get_property(PROP_TMDBTYPE, self._gui._tmdb_type)
            t = self.open_info(listitem, threaded=True)
            self.wait_until_active(ID_VIDEOINFO, poll=0.1)  # Wait to allow info dialog to open
            self._gui.doModal()

        # Thread joins when Recs and Info close
        return self.on_join(t, listitem.getPath())

    def pop_history(self):
        try:
            self._gui, meta, data = self._history.pop()
            return meta
        except IndexError:
            return

    def add_history(self):
        if not self._gui or not self._gui._tmdb_type or not self._gui._tmdb_id:
            return
        meta = {'tmdb_type': self._gui._tmdb_type, 'tmdb_id': self._gui._tmdb_id}
        data = get_property(PROP_JSONDUMP)
        self._history.append((self._gui, meta, data))
        return meta

    def open_info(self, listitem, func=None, threaded=False):
        executebuiltin(f'Dialog.Close(movieinformation,true)')
        executebuiltin(f'Dialog.Close(pvrguideinfo,true)')
        func() if func else None
        if xbmcgui.getCurrentWindowId() != self._window_id:
            executebuiltin(f'ActivateWindow({self._window_id})')
            self.wait_until_active(self._window_id, poll=0.1)
        self._current_dump = ''
        get_property(PROP_JSONDUMP, clear_property=True)
        if threaded:
            t = Thread(target=xbmcgui.Dialog().info, args=[listitem])
            t.start()
            return t
        xbmcgui.Dialog().info(listitem)

    @staticmethod
    def get_listitem(tmdb_type, tmdb_id):
        try:
            _path = f"info=details&tmdb_type={tmdb_type}&tmdb_id={tmdb_id}"
            return Router(-1, _path).get_directory(items_only=True)[0].get_listitem()
        except (TypeError, IndexError, KeyError, AttributeError, NameError):
            return

    def on_exit(self, builtin=None, after=False, **kwargs):
        cond = self.is_exiting()
        with WindowProperty((PROP_ONCLOSED, 'True')):
            executebuiltin(builtin) if builtin and not after else None
            executebuiltin(f'Dialog.Close(movieinformation,true)')
            executebuiltin(f'Dialog.Close(pvrguideinfo,true)')
            self.wait_until_active(ID_VIDEOINFO, invert=True, poll=0.1)
            if not cond and xbmcgui.getCurrentWindowId() == self._window_id:
                _win = xbmcgui.Window(self._window_id)
                _win.close() if _win else None
            self.wait_until_active(self._window_id, invert=True, poll=0.1)
            executebuiltin(builtin) if builtin and after else None
            for _gui, meta, data in self._history:
                del _gui
            get_property(PROP_HIDEINFO, clear_property=True)
            get_property(PROP_HIDERECS, clear_property=True)
            get_property(PROP_TMDBTYPE, clear_property=True)
            get_property(PROP_ISACTIVE, clear_property=True)
            get_property(PROP_JSONDUMP, clear_property=True)
