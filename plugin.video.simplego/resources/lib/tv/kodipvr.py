"""Kodi TV: when and how the playlist and guide are exported, and IPTV Simple's instance.

iptvfiles.py writes the files.
"""

import os
import time
from urllib.parse import urlencode

import xbmc
import xbmcgui
import xbmcvfs

from resources.lib import kodiutil
from resources.lib import parental
from resources.lib.data import channellist
from resources.lib.data import onair
from resources.lib.tv import iptvfiles
from resources.lib.tv import iptvsimple
from resources.lib.util import homelock
from resources.lib.util import localtime

PVR_DIR = "special://profile/addon_data/%s/%s/" % (kodiutil.ADDON_ID, iptvfiles.OUT_DIR)
PVR_M3U = PVR_DIR + iptvfiles.PLAYLIST
PVR_EPG = PVR_DIR + iptvfiles.GUIDE

# The most days the provider's guide API serves (verified 2026-10-27).
GUIDE_MAX_PAST = 7
GUIDE_MAX_AHEAD = 13

# Only these settings change the Kodi TV files; others need no export.
SETTINGS = ("pvr_enabled", "info_movie", "info_series", "info_other", "colours")

# Home window property: when the running export started; how long a second one waits,
# and when a mark counts as a crashed export's leftover.
EXPORT_PROPERTY = "%s.exporting" % kodiutil.ADDON_ID
EXPORT_WAIT = 300
EXPORT_STALE = 900

# Home window property: the settings fingerprint the last (or running) export is for.
EXPORTED_PROPERTY = "%s.exported" % kodiutil.ADDON_ID


def guide_days():
    """Return (days back, days ahead) to fetch: Kodi's guide "days to display", capped at the provider's."""
    past = _int(kodiutil.kodi_setting("epg.pastdaystodisplay"), 1)
    ahead = _int(kodiutil.kodi_setting("epg.futuredaystodisplay"), 3)
    return max(0, min(past, GUIDE_MAX_PAST)), max(1, min(ahead, GUIDE_MAX_AHEAD))


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def show_guide_days(days=None):
    """Update the settings' read-only "Days" row: where the numbers come from."""
    kodiutil.set_setting("epg_days_info", kodiutil.string(30133) % (days or guide_days()))


def refresh_hours():
    """Return how often the service fetches channels and guide from the provider, in hours; 0: never by itself."""
    return kodiutil.addon().getSettingInt("pvr_interval")


def show_state(on=None):
    """Write the TV menu's state ("On"/"Off") on the settings' row that switches it (see views.tv.TvViews.do_tv_toggle)."""
    on = enabled() if on is None else on
    kodiutil.set_setting("tv_menu", kodiutil.string(30225 if on else 30226))


def enabled():
    """Return whether the Kodi TV export is switched on."""
    return kodiutil.addon().getSettingBool("pvr_enabled")


def settings_fingerprint(days=None):
    """Return everything an export's files depend on besides the provider's data: when it changes, export again."""
    addon = kodiutil.addon()
    return tuple(addon.getSetting(key) for key in SETTINGS) + (days or guide_days()) + tuple(sorted(parental.settings().items()))


def wants_export(fingerprint, last):
    """Return whether settings with this fingerprint need an export, `last` being the one exported for before.

    An export another process ran meanwhile (switching the TV menu on) counts.
    """
    return fingerprint != last and repr(fingerprint) != kodiutil.home().getProperty(EXPORTED_PROPERTY)


def export(client, restart=True, progress=None, pause=None):
    """Rewrite the IPTV Simple playlist and guide.

    IPTV Simple re-reads files at the same paths on its own schedule. When our instance's
    settings changed, Kodi must restart for it to read them: the add-on never disables or
    enables another add-on (IPTV Simple crashed, taking Kodi down, when disabled while starting).

    One export at a time across Kodi's add-on processes; a second one waits.

    :param progress: see iptvfiles.export, plus the stages "wait" and "channels"
    :param pause: see iptvfiles.export
    """
    report = progress or (lambda stage, done=0, total=0: None)
    home = kodiutil.home()
    monitor = xbmc.Monitor()
    lock = homelock.HomeLock(home, EXPORT_PROPERTY, EXPORT_STALE)
    waited = time.time()
    while not monitor.abortRequested() and not lock.try_take():
        if time.time() - waited > EXPORT_WAIT:
            lock.take()
            break
        report("wait")
        monitor.waitForAbort(0.5)
    # Marked done from its start, so the settings change that started it does not start another.
    before = home.getProperty(EXPORTED_PROPERTY)
    home.setProperty(EXPORTED_PROPERTY, repr(settings_fingerprint()))
    try:
        return _export(client, restart, report, pause)
    except BaseException:
        home.setProperty(EXPORTED_PROPERTY, before)
        raise
    finally:
        lock.release()


def _export(client, restart, report, pause):
    addon = kodiutil.addon()
    s = kodiutil.string
    base = "plugin://%s/" % kodiutil.ADDON_ID
    started = time.monotonic()
    report("channels")
    channels = [dict(c, groups=[s(30107)]) if c.get("favourite") else c for c in channellist.for_kodi_tv(client)]
    if not channellist.archive_enabled(client):
        channels = [dict(c, catchup=False) for c in channels]
    stats = {"channels": time.monotonic() - started}
    result = iptvfiles.export(
        client,
        channels,
        kodiutil.PROFILE,
        lambda **kw: base + "?" + urlencode(kw),
        **dict(zip(("past_days", "days_ahead"), guide_days(), strict=True)),
        block_dir=onair.BLOCKS,
        info_types=sorted(kodiutil.cast_kinds()),
        progress=report,
        stats=stats,
        pause=pause,
    )
    kodiutil.log(
        "Kodi TV export: %d channels, %d programmes in %.1fs (channels %.1fs; guide %.1fs, %d blocks fetched, %d kept;"
        " info pages %.1fs, %d fetched, %d blocks read; %s %.1fs, %d blocks made anew)"
        % (
            result
            + (time.monotonic() - started, stats["channels"], stats["guide"], stats.get("fetched", 0), stats.get("cached", 0))
            + (stats["info"], stats.get("pages", 0), stats.get("read", 0))
            + ("unchanged, not rewritten" if stats.get("unchanged") else "writing",)
            + (stats["write"], stats.get("rendered", 0))
        )
    )
    now = time.time()
    last = s(30126) % (("%s %s" % (localtime.local_date(now), localtime.local_clock(now)),) + tuple(result))
    # The public guide (no login, or a refused one) lacks channels of the subscription.
    addon.setSetting("pvr_last", last if client.authed else "%s · %s" % (last, s(30127)))
    # For the service's schedule: a Kodi start does not export again before it is due.
    addon.setSetting("pvr_last_at", str(int(time.time())))
    changed = has_iptv_simple() and update_instance(iptv_profile())
    if changed:
        kodiutil.log("IPTV Simple instance updated")
    if restart and changed:
        xbmcgui.Dialog().notification(kodiutil.name(), s(30243), sound=False)
    return result


def iptv_profile():
    """Return IPTV Simple's profile folder (where its instance files are)."""
    return xbmcvfs.translatePath("special://profile/addon_data/%s/" % iptvsimple.IPTV_SIMPLE)


def has_iptv_simple():
    """Return whether IPTV Simple is installed."""
    return xbmc.getCondVisibility("System.HasAddon(%s)" % iptvsimple.IPTV_SIMPLE)


def install_iptv_simple():
    """Install IPTV Simple (Kodi asks first); whether it is there afterwards."""
    if has_iptv_simple():
        return True
    # InstallAddon returns before the download finishes.
    xbmc.executebuiltin("InstallAddon(%s)" % iptvsimple.IPTV_SIMPLE, True)
    monitor = xbmc.Monitor()
    for _ in range(120):
        if has_iptv_simple() or monitor.waitForAbort(0.5):
            break
    return has_iptv_simple()


def update_instance(profile, create=False):
    """Run iptvsimple.update_instance for our files and return its answer."""
    colours = kodiutil.addon().getSettingBool("colours")
    return iptvsimple.update_instance(profile, PVR_M3U, PVR_EPG, create=create, colours=colours)


def switch_on(client, progress):
    """Show the channels and the guide in Kodi's TV menu: IPTV Simple, our instance, a first export.

    :param progress: a Progress for the export
    :return: (channel count, programme count, whether Kodi must restart to show them); None if
        IPTV Simple could not be installed
    :raises iptvfiles.Cancelled: the export was stopped; nothing is switched on
    """
    if not install_iptv_simple():
        return None
    addon = kodiutil.addon()
    # Instance first, so the export finds it unchanged and says nothing of its own.
    changed = update_instance(kodiutil.ensure_dir(iptv_profile()), create=True)
    # On before the export, so the export is the one for these settings (see wants_export).
    addon.setSettingBool("pvr_enabled", True)
    try:
        n_channels, n_progs = export(client, restart=False, progress=progress)
    except BaseException:
        addon.setSettingBool("pvr_enabled", False)
        raise
    show_state(True)
    return n_channels, n_progs, changed


def switch_off(progress=None):
    """Take the channels and the guide out of Kodi's TV menu: our instance and its files go.

    The guide blocks and cast stay: the plugin's lists use them too.

    :param progress: progress(percent) as its files go
    :return: whether our IPTV Simple instance was there (then Kodi must restart for it to go)
    """
    report = progress or (lambda percent: None)
    addon = kodiutil.addon()
    addon.setSettingBool("pvr_enabled", False)
    show_state(False)
    addon.setSetting("pvr_last", "")
    instance = iptvsimple.instance_file(iptv_profile(), PVR_M3U)
    removed = os.path.exists(instance)
    if removed:
        os.remove(instance)
        report(10)
    report(90)
    for name in iptvfiles.OUTPUT_FILES + (iptvfiles.STATE, iptvfiles.KEYS):
        path = os.path.join(xbmcvfs.translatePath(PVR_DIR), name)
        if os.path.exists(path):
            os.remove(path)
    return removed
