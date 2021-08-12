import xbmc
import xbmcgui
import resources.lib.addon.window as window
from resources.lib.addon.parser import try_int
from resources.lib.addon.plugin import kodi_log, ADDON
from resources.lib.addon.decorators import busy_dialog
from resources.lib.tmdb.api import TMDb

PREFIX_PATH = 'Path.'
PREFIX_QUERY = 'Query'
PREFIX_CURRENT = 'Path.Current'
PREFIX_ADDPATH = 'Path.To.Add'
PREFIX_POSITION = 'Position'
PREFIX_INSTANCE = 'Instance'
PREFIX_COMMAND = 'Command'
ID_VIDEOINFO = 12003
CONTAINER_ID = 9999


def _configure_path(path):
    path = path.replace('info=play', 'info=details')
    path = path.replace('info=seasons', 'info=details')
    path = path.replace('info=related', 'info=details')
    # TODO: Check if we still need this "extended=True" param
    if 'extended=True' not in path:
        path = u'{}&{}'.format(path, 'extended=True')
    return path


class _EventLoop():
    def _call_exit(self, return_info=False):
        self.return_info = return_info
        self.exit = True

    def _on_exit(self):
        if self.xbmc_monitor.abortRequested():
            del self.xbmc_monitor
            return

        # Clear our properties
        self.reset_properties()

        # Close video info dialog
        if window.is_visible(ID_VIDEOINFO):
            window.close(ID_VIDEOINFO)
            window.wait_until_active(ID_VIDEOINFO, invert=True, poll=0.1)

        # Close base window
        if window.is_visible(self.window_id):
            xbmc.executebuiltin('Action(Back)')
            window.wait_until_active(self.window_id, invert=True, poll=0.1)

        # If we don't have the return param then try to re-open original info
        if self.return_info and not self.params.get('return'):
            if window.wait_until_active(self.window_id, invert=True, poll=0.1, timeout=1):
                xbmc.executebuiltin('Action(Info)')

        # Clear our instance property because we left
        window.get_property(PREFIX_INSTANCE, clear_property=True)

    def _on_add(self):
        self.position += 1
        self.set_properties(self.position, window.get_property(PREFIX_ADDPATH))
        window.wait_for_property(PREFIX_ADDPATH, None, True)  # Clear property before continuing

    def _on_back(self):
        # Get current position and clear it
        name = u'{}{}'.format(PREFIX_PATH, self.position)
        window.wait_for_property(name, None, True)

        # If it was first position then let's exit
        if not self.position > 1:
            return self._call_exit(True)

        # Otherwise set previous position to current position
        self.position -= 1
        name = u'{}{}'.format(PREFIX_PATH, self.position)
        self.set_properties(self.position, window.get_property(name))

    def _on_change(self):
        # On first run the base window won't be open yet so don't check for it
        base_id = None if self.first_run else self.window_id

        # Close the info dialog first before doing anything
        if window.is_visible(ID_VIDEOINFO):
            window.close(ID_VIDEOINFO)

            # If we timeout or user forced back out of base window then we exit
            if not window.wait_until_active(ID_VIDEOINFO, base_id, invert=True):
                return self._call_exit()

        # On last position let's exit
        if self.position == 0:
            return self._call_exit(True)

        # On first run let's open our base window
        if self.first_run:
            window.activate(self.window_id)
            if not window.wait_until_active(self.window_id, poll=0.5):
                return self._call_exit()

        # Set our base window
        base_window = xbmcgui.Window(self.kodi_id)

        # Check that base window has correct control ID and clear it out
        control_list = base_window.getControl(CONTAINER_ID)
        if not control_list:
            kodi_log(u'SKIN ERROR!\nControl {} unavailable in Window {}'.format(CONTAINER_ID, self.window_id), 1)
            return self._call_exit()
        control_list.reset()

        # Wait for the container to update before doing anything
        if not window.wait_until_updated(container_id=CONTAINER_ID, instance_id=self.window_id):
            return self._call_exit()

        # Open the info dialog
        base_window.setFocus(control_list)
        xbmc.executebuiltin(u'SetFocus({},0,absolute)'.format(CONTAINER_ID))
        xbmc.executebuiltin('Action(Info)')
        if not window.wait_until_active(ID_VIDEOINFO, self.window_id):
            return self._call_exit()

        # Set current_path to added_path because we've now updated everything
        # Set first_run to False because we've now finished our first run through
        self.current_path = self.added_path
        self.first_run = False

    def event_loop(self):
        window.wait_for_property(PREFIX_INSTANCE, 'True', True)
        while not self.xbmc_monitor.abortRequested() and not self.exit:
            # Path added so let's put it in the queue
            if window.get_property(PREFIX_ADDPATH):
                self._on_add()

            # Exit called so let's exit
            elif window.get_property(PREFIX_COMMAND) == 'exit':
                self._call_exit()

            # Path changed so let's update
            elif self.current_path != self.added_path:
                self._on_change()
                self.xbmc_monitor.waitForAbort(0.5)

            # User force quit so let's exit
            elif not window.is_visible(self.window_id):
                self._call_exit()

            # User pressed back and closed video info window
            elif not window.is_visible(ID_VIDEOINFO):
                self._on_back()
                self.xbmc_monitor.waitForAbort(0.5)

            # Nothing happened this round so let's loop and wait
            else:
                self.xbmc_monitor.waitForAbort(0.5)

        self._on_exit()


class WindowManager(_EventLoop):
    def __init__(self, **kwargs):
        self.window_id = None
        if kwargs.get('call_auto'):
            self.window_id = try_int(kwargs['call_auto'])
            self.kodi_id = self.window_id + 10000 if self.window_id < 10000 else self.window_id
        self.position = 0
        self.added_path = None
        self.current_path = None
        self.return_info = False
        self.first_run = True
        self.params = kwargs
        self.exit = False
        self.xbmc_monitor = xbmc.Monitor()

    def reset_properties(self):
        self.position = 0
        self.added_path = None
        self.current_path = None
        window.get_property(PREFIX_COMMAND, clear_property=True)
        window.get_property(PREFIX_CURRENT, clear_property=True)
        window.get_property(PREFIX_POSITION, clear_property=True)
        window.get_property(u'{}0'.format(PREFIX_PATH), clear_property=True)
        window.get_property(u'{}1'.format(PREFIX_PATH), clear_property=True)

    def set_properties(self, position=1, path=None):
        self.position = position
        self.added_path = path or ''
        window.get_property(PREFIX_CURRENT, set_property=path)
        window.get_property(u'{}{}'.format(PREFIX_PATH, position), set_property=path)
        window.get_property(PREFIX_POSITION, set_property=position)

    def call_auto(self):
        if window.get_property(PREFIX_INSTANCE):
            # Already instance running and has window open so let's exit
            if window.is_visible(self.window_id):
                return
            # Do some clean-up because we didn't exit cleanly last time
            window.get_property(PREFIX_INSTANCE, clear_property=True)
            self.reset_properties()

        # Start up our service to monitor the windows
        return self.event_loop()

    def add_path(self, path):
        path = _configure_path(path)

        # Check that user didn't click twice by accident
        if path == window.get_property(PREFIX_CURRENT):
            return

        # Set our path to the window property so we can add it
        window.wait_for_property(PREFIX_ADDPATH, path, True)
        self.call_auto()

    def add_query(self, query, tmdb_type):
        with busy_dialog():
            tmdb_id = TMDb().get_tmdb_id_from_query(tmdb_type, query, header=query, use_details=True, auto_single=True)
        if not tmdb_id:
            xbmcgui.Dialog().notification('TMDbHelper', ADDON.getLocalizedString(32310).format(query))
            return
        url = 'plugin://plugin.video.themoviedb.helper/?info=details&tmdb_type={}&tmdb_id={}'
        url = url.format(tmdb_type, tmdb_id)
        return self.add_path(url)

    def close_dialog(self):
        window.wait_for_property(PREFIX_COMMAND, 'exit', True)
        window.wait_for_property(PREFIX_INSTANCE, None)
        self._call_exit()
        self._on_exit()
        self.call_window()

    def call_window(self):
        if self.params.get('playmedia'):
            return xbmc.executebuiltin(u'PlayMedia(\"{}\")'.format(self.params['playmedia']))
        if self.params.get('call_id'):
            return xbmc.executebuiltin(u'ActivateWindow({})'.format(self.params['call_id']))
        if self.params.get('call_path'):
            return xbmc.executebuiltin(u'ActivateWindow(videos, {}, return)'.format(self.params['call_path']))
        if self.params.get('call_update'):
            return xbmc.executebuiltin(u'Container.Update({})'.format(self.params['call_update']))

    def router(self):
        if self.params.get('add_path'):
            return self.add_path(self.params['add_path'])
        if self.params.get('add_query') and self.params.get('tmdb_type'):
            return self.add_query(self.params['add_query'], self.params['tmdb_type'])
        if self.params.get('close_dialog') or self.params.get('reset_path'):
            return self.close_dialog()
        self.call_window()
