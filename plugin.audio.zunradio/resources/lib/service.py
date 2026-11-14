# SPDX-License-Identifier: GPL-2.0-or-later
"""The service: while ZUN radio plays, it shows the track on air with its cover.

The service sleeps when nothing or something else plays. During ZUN radio it
downloads the track information every 20 seconds and updates the playing item
with xbmc.Player().updateInfoTag(), in step with the audio (see sync.py).
When the user switches to full screen (the visualisation window, also the
screensaver of music), it shows the ZUN scene instead (see scena.py).
"""

import time
import traceback
from urllib.parse import urlencode

import xbmc
import xbmcaddon
import xbmcgui

from resources.lib import api, kodiutils, scena, sync

CHECK_INTERVAL = 1.0  # seconds between checks of what is playing
SCENE_INTERVAL = 0.5  # the same while the scene is open
PLAY_TIMEOUT = 30.0  # seconds the scene waits for ZUN radio started for it
# A busy dialog is modal; named too, in case a Kodi version does not count it
BUSY = ('System.HasActiveModalDialog | Window.IsActive(busydialog)'
        ' | Window.IsActive(busydialognocancel)')


def playing_zun(player):
    """True when Kodi plays ZUN radio from this add-on or from a direct stream URL."""
    if not player.isPlayingAudio():
        return False
    try:
        path = player.getPlayingItem().getPath()
    except RuntimeError:  # playback stopped in the meantime
        return False
    return path.startswith(kodiutils.PLUGIN_PREFIX) or api.is_zun_stream(path)


def read_shown(player):
    tag = player.getMusicInfoTag()
    return sync.Shown(tag.getTitle(), tag.getArtist(), tag.getAlbum())


def apply_now_playing(player, addon, now_playing):
    """Update the playing item and return what Kodi shows afterwards."""
    # A copy of the playing item keeps its path, so Kodi accepts the update
    item = player.getPlayingItem()
    kodiutils.set_now_playing(item, now_playing, addon)
    player.updateInfoTag(item)
    return read_shown(player)


def leave_visualisation_window(monitor):
    """Close the standard visualisation window, so that only the scene shows a visualisation."""
    xbmc.executebuiltin('Action(Back)')
    for _ in range(50):  # up to 5 s: slower devices (RPi) close the window with an animation
        if xbmcgui.getCurrentWindowId() != scena.WINDOW_VISUALISATION:
            return True
        if monitor.waitForAbort(0.1):
            return False
    return False


def wait_for_quiet_gui(monitor, quiet=0.5, timeout=15.0, step=0.1):
    """True once no dialog has been open for `quiet` seconds (False after `timeout` or on exit).

    A busy dialog shows only after 100 ms of waiting, so a single look could miss one that is
    about to show, typically the list of this add-on loading again after the scene item.
    """
    needed = max(1, int(round(quiet / step)))
    calm = 0
    for _ in range(int(round(timeout / step))):
        if xbmc.getCondVisibility(BUSY):
            calm = 0
        else:
            calm += 1
            if calm >= needed:
                return True
        if monitor.waitForAbort(step):
            return False
    return False


def start_zun(player, monitor):
    """Play the default stream for the scene once Kodi waits for nothing (see plugin.request_scene)."""
    if not wait_for_quiet_gui(monitor):
        kodiutils.log('Kodi stayed busy, ZUN radio not started for the scene', xbmc.LOGWARNING)
        return False
    player.play('{}?{}'.format(kodiutils.PLUGIN_PREFIX,
                               urlencode({'action': 'play', 'stream': api.DEFAULT_STREAM.id})))
    return True


def run():
    addon = xbmcaddon.Addon()
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    synchronizer = sync.Synchronizer(
        fetch=lambda: api.fetch_now_playing(kodiutils.user_agent(addon)),
        read_shown=lambda: read_shown(player),
        apply=lambda now_playing: apply_now_playing(player, addon, now_playing),
        log=kodiutils.log,
    )
    scene = scena.Scene(addon)
    home = xbmcgui.Window(kodiutils.HOME_WINDOW)
    scena.restore_visualisation(addon)  # after a crash while the scene was open
    kodiutils.log('Service started')
    active = False
    play_requested = 0.0  # when the service started ZUN radio for the scene (time.monotonic)
    while not monitor.abortRequested():
        if playing_zun(player):
            active = True
            try:
                synchronizer.tick()
            except RuntimeError as error:  # playback stopped during the update
                kodiutils.log('Update skipped: {}'.format(error))
            try:
                scene.finish_if_closed()
                if home.getProperty(kodiutils.SCENE_REQUEST):
                    home.clearProperty(kodiutils.SCENE_REQUEST)
                    if not scene.is_open:
                        scene.open(synchronizer.applied)
                if (not scene.is_open and xbmcgui.getCurrentWindowId() == scena.WINDOW_VISUALISATION
                        and addon.getSettings().getBool('scena_na_celou')):
                    if leave_visualisation_window(monitor):
                        scene.open(synchronizer.applied)
                    else:
                        kodiutils.log('The visualisation window did not close, no scene', xbmc.LOGWARNING)
                if scene.is_open:
                    scene.update(synchronizer.applied)
            except Exception:  # pylint: disable=broad-except  # the service must keep running
                kodiutils.log('Scene failed: {}'.format(traceback.format_exc()), xbmc.LOGERROR)
                try:
                    scene.close()
                except Exception:  # pylint: disable=broad-except
                    pass
        elif active:
            active = False
            synchronizer.reset()
            scene.close()
        else:
            scene.finish_if_closed()
            request = home.getProperty(kodiutils.SCENE_REQUEST)
            if request == kodiutils.SCENE_PLAY:
                # The scene item while ZUN radio does not play: start it, the scene opens with it
                home.setProperty(kodiutils.SCENE_REQUEST, kodiutils.SCENE_OPEN)
                play_requested = time.monotonic()
                if not start_zun(player, monitor):
                    home.clearProperty(kodiutils.SCENE_REQUEST)
            elif request and time.monotonic() - play_requested > PLAY_TIMEOUT:
                home.clearProperty(kodiutils.SCENE_REQUEST)  # ZUN radio did not start
        if monitor.waitForAbort(SCENE_INTERVAL if scene.is_open else CHECK_INTERVAL):
            break
    scene.close()
    kodiutils.log('Service stopped')
