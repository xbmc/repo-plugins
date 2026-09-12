import json

import xbmc
import xbmcaddon

from resources.lib import live_sync, oauth, sync_orchestrator, sync_state
from resources.lib.player_monitor import PlayerMonitor
from resources.lib.timer import Timer


# Fixed, not user-configurable -- a too-low interval here is a footgun (needless
# load on both the Kodi library JSON-RPC calls and the MDBList API), and there's
# a single correct answer for "how often should this poll" that doesn't benefit
# from being exposed as a setting.
SYNC_INTERVAL_MINUTES = 1440
ACTIVITY_CHECK_INTERVAL_MINUTES = 10
# Kodi's native "Rate" UI doesn't reliably announce VideoLibrary.OnUpdate the
# way marking watched does (confirmed by log inspection), so ratings have no
# event to react to and need an actual poll -- kept cheap via
# library_snapshot.build_ratings_snapshot(), which only fetches uniqueid+userrating.
RATINGS_CHECK_INTERVAL_MINUTES = 2

ADDON_ID = "service.mdblist-scrobbler"


class MainMonitor(xbmc.Monitor):
    def __init__(self):
        super().__init__()

        self.player_monitor = PlayerMonitor()
        self._timers = {}
        # (name, interval_minutes, callback) -- one table instead of three
        # near-identical start/stop/on-timer method trios.
        self._timer_specs = (
            # allow_remove=True: the deliberate 24h reconciliation backstop,
            # trusted to actually remove things from MDBList (still subject
            # to sync_payload's magnitude circuit-breaker).
            ("sync", SYNC_INTERVAL_MINUTES, lambda: sync_orchestrator.run_async(allow_remove=True)),
            ("activity", ACTIVITY_CHECK_INTERVAL_MINUTES, lambda: sync_orchestrator.check_activity_async()),
            ("ratings", RATINGS_CHECK_INTERVAL_MINUTES, lambda: sync_orchestrator.check_ratings_local_async()),
        )

        try:
            status = "Connected" if oauth.get_access_token() else "Not connected"
            xbmcaddon.Addon().setSettingString("oauth_status", status)
        except Exception:
            pass

        self._migrate_legacy_rating_setting()

        for name, interval_minutes, callback in self._timer_specs:
            self._start_timer(name, interval_minutes, callback)

        # Catch-up sync shortly after the service starts, in addition to the
        # periodic timers and the library-scan hooks below. Deliberately
        # allow_remove=False (the default): this is the riskiest possible
        # moment to trust an empty-looking Kodi library -- the video library
        # backend may not have finished loading yet, especially right after
        # a crash-triggered restart. Additions still push immediately;
        # removals wait for the 24h timer or manual "Sync now".
        sync_orchestrator.run_async()

    def _start_timer(self, name, interval_minutes, callback):
        self._stop_timer(name)
        timer = Timer(interval_minutes * 60, callback)
        timer.start()
        self._timers[name] = timer

    def _stop_timer(self, name):
        timer = self._timers.get(name)
        if timer and timer.is_alive():
            timer.stop()

    def _bool_setting(self, setting_id, default=False):
        try:
            return xbmcaddon.Addon().getSettings().getBool(setting_id)
        except Exception:
            return default

    def _migrate_legacy_rating_setting(self):
        """One-time migration: the old rating.save.mdblist toggle was folded
        into sync.ratings.enabled (a settings.xml entry can be removed but
        Kodi still lets you read the orphaned raw value from an existing
        install's profile). Runs at most once ever, tracked in sync_state, so
        it never fights a user's later explicit choice to turn sync off."""
        if sync_state.get_migration_done("rating_save_mdblist"):
            return
        try:
            legacy_value = xbmcaddon.Addon().getSetting("rating.save.mdblist")
        except Exception:
            legacy_value = ""
        if str(legacy_value).lower() == "true":
            try:
                xbmcaddon.Addon().setSettingBool("sync.ratings.enabled", True)
            except Exception:
                pass
        sync_state.set_migration_done("rating_save_mdblist")

    def shutdown(self):
        """Called from service.py once waitForAbort() returns. Without this,
        the sync/activity/ratings Timer threads (each a plain non-daemon
        threading.Thread sitting in a wait() up to 24h long) are never told
        to stop, so they block clean interpreter exit and Kodi has to
        force-kill the whole service after its 5-second grace period
        (confirmed: "script didn't stop in 5 seconds - let's kill it" in
        kodi.log on every quit, and confirmed as this addon's own doing by
        temporarily removing it from the addons folder -- Kodi then shut
        down immediately, with no CPythonInvoker delay at all).

        xbmc.Monitor.onAbortRequested() looks like the natural hook for this
        but does NOT fire in practice (confirmed empirically: a log line at
        the top of an onAbortRequested override never appeared, even though
        the very next line in service.py -- monitor.waitForAbort() returning
        -- reliably does). waitForAbort() unblocking is itself the abort
        signal, so this is called right after it instead, rather than
        relying on a callback that doesn't run.

        Timer.stop() wakes its wait() immediately, so this returns well
        within the 5-second window. Also stops the player's
        scrobble-progress interval timer, for the same reason, in case Kodi
        is closed mid-playback."""
        for name in list(self._timers.keys()):
            self._stop_timer(name)
        self.player_monitor.stop_interval_timer()

    def onScanFinished(self, library):
        # allow_remove=False (default) -- same reasoning as the service-start
        # catch-up sync above. A scan finishing doesn't guarantee the library
        # is in a trustworthy state (e.g. a scan against a temporarily
        # unavailable network share).
        if library == "video" and self._bool_setting("sync.on_library_scan", True):
            sync_orchestrator.run_async()

    def onCleanFinished(self, library):
        # allow_remove=False (default) -- this is precisely the incident
        # vector: a "Clean Library" run against unavailable sources can strip
        # entries Kodi still actually has, and this fires right after.
        if library == "video" and self._bool_setting("sync.on_library_scan", True):
            sync_orchestrator.run_async()

    def onNotification(self, sender, method, data):
        if method == "VideoLibrary.OnUpdate":
            self._handle_video_library_update(data)
        elif sender == ADDON_ID and method.endswith("sync_now"):
            # "Sync now" (script.py) broadcasts via NotifyAll rather than
            # calling sync_orchestrator directly, since RunScript runs in a
            # separate Python process from this service -- a direct call
            # there would use a different module-level lock, so is_running()
            # could never see it (confirmed bug). This runs it here instead,
            # in the same process/lock as everything else. Kodi prefixes
            # NotifyAll messages (typically "Other.<message>"), so match on
            # suffix rather than the exact prefix.
            # allow_remove=True: explicit user intent, foreground, user is
            # watching -- same trust level as the 24h timer.
            sync_orchestrator.run_async(notify=True, allow_remove=True)

    def _handle_video_library_update(self, data):
        try:
            payload = json.loads(data)
        except (ValueError, TypeError):
            return

        item = payload.get("item") or {}
        dbtype = item.get("type")
        dbid = item.get("id")
        if dbtype not in ("movie", "episode") or dbid in (None, -1):
            return

        live_sync.handle_library_update(dbtype, dbid)

    def onSettingsChanged(self):
        self.player_monitor.load_settings()
