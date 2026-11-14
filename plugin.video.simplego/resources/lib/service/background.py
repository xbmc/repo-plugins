"""Background service: starts playback for the plugin (see playservice), and keeps the Kodi TV playlist and guide fresh."""

import threading
import time

import xbmc

from resources.lib import clientfactory
from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.login import loginstate
from resources.lib.service import playservice
from resources.lib.tv import exportprogress
from resources.lib.tv import kodipvr

FIRST_DELAY = 60
# Changes made outside the settings dialog (the channel list's context menu) settle this
# long; inside the dialog they count when it closes.
SETTINGS_DEBOUNCE = 2
# Kodi's own guide day settings raise no event for us: they are looked at this often.
KODI_CHECK_EVERY = 30
# The account's rows (devices change elsewhere too) and the login's expiry: checked this often.
ACCOUNT_CHECK_EVERY = 24 * 3600
# What a channel start would wait for once due (see provider.playback.Playback.get_ready): looked at this often,
# and done this long before it is due.
READY_EVERY = 15 * 60
READY_AHEAD = 3600


class _Monitor(xbmc.Monitor):
    changed_at = 0
    on_power = None  # on_power(method) for Kodi going to sleep and waking up (see playservice)

    def onSettingsChanged(self):
        kodiutil.reload_settings()

    def onNotification(self, sender, method, data):
        if self.on_power and method in ("System.OnSleep", "System.OnWake"):
            self.on_power(method)
        self.changed_at = time.time()


def _export(progress):
    """Run one Kodi TV refresh, in its own thread so the playing streams are kept meanwhile.

    :param progress: an exportprogress.BackgroundProgress (shown for a user's change), or a silent exportprogress.Progress
    """
    result = None
    try:
        client = clientfactory.make_client()
        try:
            result = kodipvr.export(client, progress=progress)
        except provider.AuthError as e:
            # A refused login: the public guide still keeps Kodi TV going.
            kodiutil.log("login refused (%s), exporting the public guide" % e, xbmc.LOGWARNING)
            client.guest = True
            result = kodipvr.export(client, progress=progress)
        kodiutil.log("Kodi TV files refreshed: %d channels, %d programmes" % result)
    except Exception as e:  # noqa: BLE001 - keep the service alive; the next round retries
        kodiutil.log("Kodi TV refresh failed: %s" % e, xbmc.LOGWARNING)
    finally:
        progress.close(result)


def _get_ready():
    started = time.time()
    try:
        clientfactory.shared_client().get_ready(READY_AHEAD)
    except Exception as e:  # noqa: BLE001 - the next look, or the channel start itself, tries again
        kodiutil.log("getting ready ahead failed: %s" % e, xbmc.LOGWARNING)
        return
    if time.time() - started > 0.2:  # a look that found nothing due takes no time
        kodiutil.log("got ready ahead in %.2fs" % (time.time() - started))


def _show_login_state():
    try:
        client = clientfactory.make_client()
        loginstate.show_login_state(client)
        loginstate.warn_if_login_runs_out(client)
    except Exception as e:  # noqa: BLE001 - only the settings' rows wait for it
        kodiutil.log("login state check failed: %s" % e, xbmc.LOGWARNING)


class ExportSchedule:
    """When the service exports Kodi TV's files, and whether it shows that it does.

    A user's change is exported visibly, the schedule's runs silently. The first waits
    FIRST_DELAY after Kodi starts so it does not slow the start; the last export counts across starts.
    """

    def __init__(self):
        try:
            last = float(kodiutil.addon().getSetting("pvr_last_at"))
        except ValueError:
            last = 0
        self.last = max(last, time.time() - (kodipvr.refresh_hours() or 24) * 3600 + FIRST_DELAY)
        days = kodipvr.guide_days()
        self.fingerprint = kodipvr.settings_fingerprint(days)
        kodipvr.show_guide_days(days)
        self.kodi_checked = time.time()
        self.asked = self.due = False
        self.requested = False  # by another process (channel order, favourites, the parental lock)
        self.exporting = None

    def look(self, monitor):
        """Note what asks for an export: a change of the settings or elsewhere, the clock, a login."""
        home = kodiutil.home()
        # A change exports once the settings dialog is closed (made elsewhere: right away).
        if home.getProperty(kodiutil.EXPORT_REQUEST):
            home.clearProperty(kodiutil.EXPORT_REQUEST)
            monitor.changed_at = time.time()
            self.requested = True
        dialog_open = xbmc.getCondVisibility("Window.IsActive(addonsettings)")
        if monitor.changed_at and not dialog_open and time.time() - monitor.changed_at > SETTINGS_DEBOUNCE:
            monitor.changed_at = 0
            self.asked = self.asked or self.requested or self._changed(kodipvr.settings_fingerprint())
            self.requested = False
        elif time.time() - self.kodi_checked > KODI_CHECK_EVERY:
            self.kodi_checked = time.time()
            days = kodipvr.guide_days()
            kodipvr.show_guide_days(days)
            self.asked = self.asked or self._changed(kodipvr.settings_fingerprint(days))
        hours = kodipvr.refresh_hours()
        self.due = self.due or (hours > 0 and time.time() - self.last >= hours * 3600)
        # Logged in or out: the guide switches between the public and the subscriber's.
        if home.getProperty(kodiutil.LOGIN_CHANGED):
            home.clearProperty(kodiutil.LOGIN_CHANGED)
            clientfactory.forget_shared_client()
            threading.Thread(target=_show_login_state, daemon=True).start()
            self.asked = True
        if not kodipvr.enabled():
            self.asked = self.due = False

    def _changed(self, fingerprint):
        """Return whether settings with this fingerprint need an export; one already run for them counts."""
        wanted = kodipvr.wants_export(fingerprint, self.fingerprint)
        self.fingerprint = fingerprint
        return wanted

    def export_if_wanted(self):
        """Start the export asked for, unless one still runs (it follows that one)."""
        if not (self.asked or self.due) or (self.exporting and self.exporting.is_alive()):
            return
        progress = exportprogress.BackgroundProgress() if self.asked else exportprogress.Progress()
        self.asked = self.due = False
        self.last = time.time()
        self.fingerprint = kodipvr.settings_fingerprint()
        self.exporting = threading.Thread(target=_export, args=(progress,), daemon=True)
        self.exporting.start()


class RoundTimes:
    """What the service's once-a-second rounds cost, logged (debug) once an hour: with and without a stream."""

    EVERY = 3600

    def __init__(self, now=None):
        self.since = now or time.time()
        self.times = {True: [], False: []}

    def add(self, seconds, busy, now=None):
        """Count one round; once an hour has passed, log the hour's and start anew."""
        self.times[bool(busy)].append(seconds)
        now = now or time.time()
        if now - self.since >= self.EVERY:
            kodiutil.log("service rounds in the last hour: %s" % self.summary(), xbmc.LOGDEBUG)
            self.since, self.times = now, {True: [], False: []}

    def summary(self):
        """Return the rounds counted, idle and with a stream: how many, mean and longest."""
        parts = []
        for busy, label in ((False, "idle"), (True, "with a stream")):
            times = self.times[busy]
            if times:
                parts.append(
                    "%s %d, mean %.1f ms, max %.1f ms" % (label, len(times), 1000 * sum(times) / len(times), 1000 * max(times))
                )
        return "; ".join(parts) or "none"


def run():
    """Run the service until Kodi exits."""
    monitor = _Monitor()
    # Playback first: channels switch fast from the start; the account check may take a while.
    player = playservice.PlayService().start()
    monitor.on_power = player.on_power
    schedule = ExportSchedule()
    kodipvr.show_state()  # the settings' TV menu row: its state, also after an update
    account_checked = 0
    ready_looked = time.time() - READY_EVERY + FIRST_DELAY  # not while Kodi starts
    rounds = RoundTimes()
    try:
        while not monitor.abortRequested():
            began = time.time()
            try:
                if time.time() - account_checked > ACCOUNT_CHECK_EVERY:
                    account_checked = time.time()
                    threading.Thread(target=_show_login_state, daemon=True).start()
                if time.time() - ready_looked > READY_EVERY:
                    ready_looked = time.time()
                    threading.Thread(target=_get_ready, daemon=True).start()
                player.tick()
                schedule.look(monitor)
                schedule.export_if_wanted()
            except Exception as e:  # noqa: BLE001 - one round's failure must not end the service
                kodiutil.log("service round failed: %s" % e, xbmc.LOGWARNING)
            rounds.add(time.time() - began, player.busy())
            if monitor.waitForAbort(1):
                break
    finally:
        player.stop()
