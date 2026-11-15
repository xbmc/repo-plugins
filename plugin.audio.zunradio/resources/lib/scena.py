# SPDX-License-Identifier: GPL-2.0-or-later
"""The ZUN radio scene over the whole screen, as the full screen player on zunradio.cz.

The window (resources/skins/Default/1080i/zunradio-scena.xml) shows the cover in a red card,
the artist and title in red fields, the station logo and the show. The dots, rings and waves
that move to the beat come from the visualisation add-on visualization.zunradio: a skin
visualisation control always shows the visualisation chosen in the Kodi settings, so the scene
shows it only when the user has chosen visualization.zunradio there (Player > Music >
Visualisation). The add-on only reads that setting and never installs the visualisation (add-on
rules, review of 1.0.0). Otherwise the scene shows still dots instead.

The scene is a whole window (WindowXML), not a dialog over the previous window: under a dialog
Kodi keeps drawing that window, Estuary runs a second instance of the visualisation in its
background, and that hidden instance answered the window about the beat (LibreELEC on RPi4
pumped unevenly, Lada 2026-11-08).
"""

import json

import xbmc
import xbmcgui

from resources.lib import kodiutils

VIS_ID = 'visualization.zunradio'
VIS_SETTING = 'musicplayer.visualisation'
WINDOW_VISUALISATION = 12006
SMALL_FROM = 34  # characters; longer texts get a smaller font

# Actions that leave the scene open: nothing, pause, stop, play, screenshot, volume, mute,
# volume amplification, mouse movement, toggle full screen, play/pause, no operation
KEEP_ACTIONS = {0, 12, 13, 79, 85, 88, 89, 90, 91, 93, 94, 107, 199, 229, 999}


def chosen_visualisation():
    """The visualisation chosen in the Kodi settings (read only)."""
    answer = json.loads(xbmc.executeJSONRPC(json.dumps(
        {'jsonrpc': '2.0', 'id': 1, 'method': 'Settings.GetSettingValue',
         'params': {'setting': VIS_SETTING}})))
    return (answer.get('result') or {}).get('value', '')


class SceneWindow(xbmcgui.WindowXML):
    """Any key closes the scene, as a screensaver; volume and playback keys do not."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.closed = False

    def onAction(self, action):
        if action.getId() in KEEP_ACTIONS:
            return
        self.closed = True
        self.close()


class Scene:
    def __init__(self, addon):
        self._addon = addon
        self._window = None
        self._window_id = 0
        self._shown = {}

    @property
    def is_open(self):
        return self._window is not None and not self._window.closed

    def with_visualisation(self):
        """True when the scene shows visualization.zunradio: wanted in the settings of this add-on,
        installed, enabled and chosen by the user in the Kodi settings."""
        return (self._addon.getSettings().getBool('scena_vizualizace')
                and xbmc.getCondVisibility(
                    'System.HasAddon({0}) + System.AddonIsEnabled({0})'.format(VIS_ID))
                and chosen_visualisation() == VIS_ID)

    def open(self, now_playing=None):
        if self.is_open:
            return
        with_vis = self.with_visualisation()
        self._window = SceneWindow('zunradio-scena.xml', self._addon.getAddonInfo('path'),
                                   'Default', '1080i')
        self._shown = {}
        self._set('vis', 'zun' if with_vis else '')
        self._set('heading', self._addon.getLocalizedString(30020).upper())
        self.update(now_playing)
        xbmc.executebuiltin('InhibitScreensaver(true)')
        # Kodi refuses to activate a window while a modal dialog is open, typically "busy" while
        # the list of this add-on loads again after the visualisation window closed (slower
        # devices longer). Wait for it, check that the window is active, try again if not.
        # Windows of add-ons have ids from 13000 (WINDOW_PYTHON_START); the id is kept to notice
        # when the user leaves the scene another way (Home key).
        self._window_id = 0
        for _ in range(3):
            self._wait_for_modal_dialogs()
            before = xbmcgui.getCurrentWindowId()
            self._window.show()
            for _ in range(40):
                current = xbmcgui.getCurrentWindowId()
                if current != before and current >= 13000:
                    self._window_id = current
                    break
                xbmc.sleep(50)
            if self._window_id:
                break
        kodiutils.log('Scene open (window {}, visualisation {})'.format(self._window_id, with_vis))
        if not self._window_id:
            kodiutils.log('The scene window did not open', xbmc.LOGWARNING)
            self.close()

    @staticmethod
    def _wait_for_modal_dialogs(timeout=5.0):
        for _ in range(int(timeout * 10)):
            if not xbmc.getCondVisibility('System.HasActiveModalDialog'):
                return
            xbmc.sleep(100)

    def close(self):
        if self._window is not None:
            if not self._window.closed:
                self._window.close()
            self._window = None
            self._window_id = 0
            xbmc.executebuiltin('InhibitScreensaver(false)')

    def finish_if_closed(self):
        """After the user closed or left the window: clean up. True when closed."""
        left = bool(self._window_id) and xbmcgui.getCurrentWindowId() != self._window_id
        if self._window is not None and (self._window.closed or left):
            self.close()
            return True
        return False

    def _set(self, key, value):
        if self._shown.get(key) != value:
            self._shown[key] = value
            self._window.setProperty(key, value)

    def update(self, now_playing=None):
        """Texts and pictures from what Kodi shows for the playing item (kept current by the
        service, in step with the audio), the record label from the track information."""
        if self._window is None:
            return
        artist = xbmc.getInfoLabel('MusicPlayer.Artist')
        title = xbmc.getInfoLabel('MusicPlayer.Title')
        # The show from the track information: Kodi clears the album with every ICY title
        show = (now_playing.show if now_playing is not None and now_playing.show
                else xbmc.getInfoLabel('MusicPlayer.Album'))
        same_track = (now_playing is not None and now_playing.title
                      and now_playing.title.casefold() == title.casefold())
        if not artist and not title:
            artist = self._addon.getLocalizedString(30000)
        # The show always, also at premieres, which have the show instead of the artist too
        # (Lada 2026-11-08); the claim only when the show is unknown
        if not show:
            show = self._addon.getLocalizedString(30021)
        self._set('cover', xbmc.getInfoLabel('Player.Art(thumb)'))
        self._set('artist', artist.upper())
        self._set('small_artist', 'true' if len(artist) > SMALL_FROM else '')
        self._set('title', title.upper())
        self._set('small_title', 'true' if len(title) > SMALL_FROM else '')
        self._set('show', show.upper())
        self._set('label', now_playing.label.upper() if same_track and now_playing.label else '')
        self._set('labellogo', now_playing.label_logo if same_track else '')
