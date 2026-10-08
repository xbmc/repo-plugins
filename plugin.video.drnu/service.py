#
#      Copyright (C) 2014 Tommy Winther, TermeHansen
#
#  https://github.com/xbmc-danish-addons/plugin.video.drnu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
"""Kodi service: request-cache maintenance and background re-cache.

Runs for the lifetime of Kodi and hourly:
- expires old responses and VACUUMs the requests-cache sqlite database
- runs the re-cache crawl daily at the time set in 'recache.time', gated on
  Kodi being idle (setting recache.service.idle), so an always-on media
  center keeps its cache fresh on its own schedule
"""
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import xbmc
import xbmcaddon
import xbmcgui
from xbmcvfs import translatePath

from resources.lib import tvapi
from resources.lib.kodiutils import get_setting, tr
from resources.lib.recachescheduler import _close_dialog, recache_pass
from resources.lib.servicecleanup import run_cleanup

CHECK_INTERVAL_SECONDS = 60 * 60
IDLE_SECONDS = 300


def idle_and_not_playing() -> bool:
    """True when Kodi has been idle long enough and nothing is playing."""
    if xbmc.getCondVisibility('Player.playing'):
        return False
    return xbmc.getGlobalIdleTime() >= IDLE_SECONDS


def _log(msg: str, level: int = xbmc.LOGINFO) -> None:
    """Log straight to Kodi, bypassing kodiutils.log's log.debug gate.

    Service information, warnings and errors must reach a default Kodi log;
    routing them through kodiutils.log would hide them unless the user
    enabled the addon's debug toggle.
    """
    xbmc.log(msg, level)


def cleanup_once(cache_path: Path) -> None:
    """One cache maintenance pass, skipped while playback is active to avoid
    sqlite contention with the addon."""
    if xbmc.getCondVisibility('Player.playing'):
        return
    if run_cleanup(get_setting, cache_path, _log):
        _log('drnu service: vacuumed the request cache db')


def make_bg_dialog() -> Optional[xbmcgui.DialogProgressBG]:
    """Create the background progress dialog, or None if Kodi refuses.

    DialogProgressBG.create() raises outside a GUI context (e.g. a headless
    service start) and can raise after Kodi has already registered the
    handle; the crawl itself does not need the dialog, so degrade to running
    without progress instead of failing, closing any half-created dialog so
    a leak cannot leave the corner progress bar stuck at 0%.
    """
    dialog = xbmcgui.DialogProgressBG()
    try:
        dialog.create('DR TV', tr(30524))
    except RuntimeError as e:
        _log(f'drnu service: DialogProgressBG.create FAILED: {e}', xbmc.LOGWARNING)
        _close_dialog(dialog)
        return None
    return dialog


def recache_once(cache_path: Path, shutdown_check: Callable[[], bool]) -> None:
    """Run the scheduled re-cache crawl when due (idle-gated by default).

    shutdown_check is passed on to the crawl so an exit request can stop it
    between requests, independent of the idle gate setting.
    """
    if recache_pass(get_setting, lambda: tvapi.Api(cache_path, tr, get_setting, _log),
                    cache_path, datetime.now(), idle_and_not_playing,
                    make_bg_dialog, log_func=_log, shutdown_check=shutdown_check):
        _log('drnu service: re-cache job finished')


def run(monitor: xbmc.Monitor, cleanup: Callable[[], None], interval_seconds: int) -> None:
    """Service loop: clean on startup, then once per interval until Kodi exits."""
    while not monitor.abortRequested():
        try:
            cleanup()
        except Exception:
            _log(traceback.format_exc(), xbmc.LOGERROR)
        monitor.waitForAbort(interval_seconds)


def main() -> None:
    cache_path = Path(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
    # the profile directory does not exist on a fresh install; without it the
    # first RecacheState.save would raise FileNotFoundError every hour until
    # the user opens the add-on
    cache_path.mkdir(parents=True, exist_ok=True)
    monitor = xbmc.Monitor()
    run(monitor, lambda: (cleanup_once(cache_path),
                          recache_once(cache_path, monitor.abortRequested)),
        CHECK_INTERVAL_SECONDS)


if __name__ == '__main__':
    main()
