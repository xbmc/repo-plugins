# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - sleep-timer warning dialog
#
# Shown by the service a configurable number of minutes before the sleep timer stops
# playback. A centred panel counts down M:SS live and offers two choices:
#   - Cancel timer  : turn the sleep timer off (keep playing).
#   - Restart timer : re-arm the full sleep duration from now.
# Closing it another way (Back) just dismisses the countdown and lets the timer run to
# its deadline; if the countdown reaches zero untouched it returns 'expire' so the
# caller stops playback.
#
# The skin lives in resources/skins/Default/1080i/script-channelme-sleep.xml; the control
# IDs below must stay in sync with it.

import threading

import xbmc
import xbmcgui

from resources.lib import storage

# ----------------------------------------------------------------------------
# Control IDs (must match the skin XML)
# ----------------------------------------------------------------------------

HEADING = 6000
COUNTDOWN = 6001
MESSAGE = 6010
CANCEL_BTN = 6002
RESTART_BTN = 6003

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92


# ============================================================================
# The warning window
# ============================================================================

class SleepWarning(xbmcgui.WindowXMLDialog):
    """A live M:SS countdown with Cancel / Restart. Sets `result` to one of
    'cancel' / 'restart' / 'dismiss' / 'expire' before closing."""

    def __init__(self, *args, **kwargs):
        self.remaining = int(kwargs.get('remaining', 120))
        self.result = None
        self._stop = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def onInit(self):
        self.getControl(HEADING).setLabel(storage.L(32207))
        self.getControl(MESSAGE).setLabel(storage.L(32208))
        self.getControl(CANCEL_BTN).setLabel(storage.L(32209))
        self.getControl(RESTART_BTN).setLabel(storage.L(32210))
        self._paint()
        self.setFocusId(RESTART_BTN)
        # A tiny helper thread ticks the countdown label once a second. It only sets a
        # label (safe from a worker thread); it never creates GUI controls.
        self._ticker = threading.Thread(target=self._tick)
        self._ticker.daemon = True
        self._ticker.start()

    def onClick(self, control_id):
        if control_id == CANCEL_BTN:
            self.result = 'cancel'
            self._finish()
        elif control_id == RESTART_BTN:
            self.result = 'restart'
            self._finish()

    def onAction(self, action):
        if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self.result = 'dismiss'      # let the timer keep running to its deadline
            self._finish()

    # ------------------------------------------------------------------
    # Countdown
    # ------------------------------------------------------------------

    def _paint(self):
        minutes, seconds = divmod(max(0, self.remaining), 60)
        try:
            self.getControl(COUNTDOWN).setLabel('{0}:{1:02d}'.format(minutes, seconds))
        except Exception:
            pass

    def _tick(self):
        while not self._stop and self.remaining > 0:
            xbmc.sleep(1000)
            if self._stop:
                return
            # If the user stopped playback themselves, the timer is moot.
            if not xbmc.Player().isPlaying():
                self.result = 'cancel'
                self._finish()
                return
            self.remaining -= 1
            self._paint()
        if not self._stop:               # reached zero untouched
            self.result = 'expire'
            self._finish()

    def _finish(self):
        self._stop = True
        try:
            self.close()
        except Exception:
            pass


# ----------------------------------------------------------------------------
# Entry point used by the service
# ----------------------------------------------------------------------------

def show(remaining_seconds):
    """Show the warning and block until the user decides or the countdown expires.
    Returns 'cancel' / 'restart' / 'dismiss' / 'expire'."""
    dialog = SleepWarning('script-channelme-sleep.xml', storage.ADDON_PATH, 'Default', '1080i',
                          remaining=remaining_seconds)
    dialog.doModal()
    result = dialog.result or 'dismiss'
    del dialog
    return result
