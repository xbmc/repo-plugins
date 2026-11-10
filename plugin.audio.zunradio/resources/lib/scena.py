# SPDX-License-Identifier: GPL-2.0-or-later
"""The ZUN radio scene over the whole screen, as the full screen player on zunradio.cz.

The window (resources/skins/Default/1080i/zunradio-scena.xml) shows the cover in a red card,
the artist and title in red fields, the station logo and the show. The dots, rings and waves
that move to the beat come from the visualisation add-on visualization.zunradio: a skin
visualisation control always shows the visualisation chosen in the Kodi settings, so the scene
selects it while it is open and puts back the previous choice when it closes (also after a crash,
see restore_visualisation). Without that add-on the scene shows still dots instead.

The scene is a whole window (WindowXML), not a dialog over the previous window: under a dialog
Kodi keeps drawing that window, Estuary runs a second instance of the visualisation in its
background, and that hidden instance answered the window about the beat (LibreELEC on RPi4
pumped unevenly, Lada 2026-11-08).
"""

import json
import os

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import kodiutils

VIS_ID = 'visualization.zunradio'
VIS_SETTING = 'musicplayer.visualisation'
WINDOW_VISUALISATION = 12006
SMALL_FROM = 34  # characters; longer texts get a smaller font

# Actions that leave the scene open: nothing, pause, stop, play, screenshot, volume, mute,
# volume amplification, mouse movement, toggle full screen, play/pause, no operation
KEEP_ACTIONS = {0, 12, 13, 79, 85, 88, 89, 90, 91, 93, 94, 107, 199, 229, 999}


def _rpc(method, params):
    answer = json.loads(xbmc.executeJSONRPC(json.dumps(
        {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
    return answer.get('result')


def _profile_file(addon, name):
    profile = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
    return os.path.join(profile, name)


def _restore_file(addon):
    return _profile_file(addon, 'vizualizace-pred-scenou.json')


def vis_in_repository():
    """True when an add-on repository offers visualization.zunradio (not installed yet)."""
    result = _rpc('Addons.GetAddons', {'type': 'xbmc.player.musicviz', 'installed': False}) or {}
    return any(item.get('addonid') == VIS_ID for item in result.get('addons') or [])


def restore_visualisation(addon):
    """Put back the visualisation chosen before the scene, if the scene did not do it."""
    path = _restore_file(addon)
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding='utf-8') as f:
            previous = json.load(f).get('vizualizace', '')
        _rpc('Settings.SetSettingValue', {'setting': VIS_SETTING, 'value': previous})
    except (OSError, ValueError):
        pass
    try:
        os.remove(path)
    except OSError:
        pass


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

    def _vis_available(self):
        return xbmc.getCondVisibility('System.HasAddon({0}) + System.AddonIsEnabled({0})'.format(VIS_ID))

    def _offer_visualisation(self):
        """Once: offer the visualisation for the dots to the beat, where a repository has it.

        The add-on cannot require it (Kodi installs only required dependencies, and a required one
        would block this add-on where no repository offers the visualisation, LibreELEC and
        CoreELEC so far). Kodi itself asks before it installs (InstallAddon). The button in the
        settings of the add-on does the same on demand (plugin.install_visualisation).
        """
        if (not self._addon.getSettings().getBool('scena_vizualizace')
                or xbmc.getCondVisibility('System.HasAddon({})'.format(VIS_ID))):
            return
        path = _profile_file(self._addon, 'nabidka-vizualizace.json')
        if os.path.exists(path) or not vis_in_repository():
            return
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'nabidnuto': True}, f)
        except OSError:
            return
        xbmcgui.Dialog().notification(self._addon.getLocalizedString(30000),
                                      self._addon.getLocalizedString(30106),
                                      self._addon.getAddonInfo('icon'), 8000)
        xbmc.executebuiltin('InstallAddon({})'.format(VIS_ID), True)
        kodiutils.log('Visualisation offered, installed: {}'.format(
            xbmc.getCondVisibility('System.HasAddon({})'.format(VIS_ID))))

    def _select_visualisation(self):
        """Select visualization.zunradio for the time of the scene. True when it is selected."""
        if not self._addon.getSettings().getBool('scena_vizualizace') or not self._vis_available():
            return False
        current = (_rpc('Settings.GetSettingValue', {'setting': VIS_SETTING}) or {}).get('value', '')
        if current == VIS_ID:
            return True
        path = _restore_file(self._addon)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({'vizualizace': current}, f)
        except OSError:
            return False
        return bool(_rpc('Settings.SetSettingValue', {'setting': VIS_SETTING, 'value': VIS_ID}))

    def open(self, now_playing=None):
        if self.is_open:
            return
        self._offer_visualisation()
        with_vis = self._select_visualisation()
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
            restore_visualisation(self._addon)

    def finish_if_closed(self):
        """After the user closed or left the window: put the visualisation back. True when closed."""
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
