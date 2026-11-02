"""How far a Kodi TV export is, shown in a dialog, in the small background bar, or nowhere."""

import time

import xbmcgui

from resources.lib import kodiutil
from resources.lib.tv import iptvfiles
from resources.lib.tv import kodipvr

# The refresh button's dialog opens only after this (see LateProgressDialog).
SHOW_AFTER = 1.0


class Progress:
    """Report how far an export is, as a percentage and a line of text; the subclasses show it."""

    # Each stage's start and end percentage.
    BANDS = {"wait": (0, 0), "channels": (0, 5), "guide": (5, 55), "info": (55, 65), "build": (65, 92), "compress": (92, 100)}

    def __init__(self):
        self.past, self.ahead = kodipvr.guide_days()

    def __call__(self, stage, done=0, total=0):
        """Show how far the export is: `done` of `total` steps into `stage` (see BANDS)."""
        low, high = self.BANDS[stage]
        percent = low + (high - low) * done // total if total else low
        s = kodiutil.string
        if stage == "guide":
            # A day is eight 3-hour blocks, starting with the days back.
            day = min(done // 8, total // 8 - 1) - self.past
            # The guide's days are UTC ones: the date at their noon.
            noon = int(time.time()) // 86400 * 86400 + 43200 + day * 86400
            date = kodiutil.local_date(noon)
            line = s(30136) % (date, self.past, self.ahead)
        elif stage == "info":
            line = s(30137) % (done, total)
        elif stage == "build":
            line = s(30212) % (done, total)
        else:
            line = s({"wait": 30134, "channels": 30135, "compress": 30138}[stage])
        self.show(percent, line)

    def show(self, percent, line):
        """Show the percentage and line (a no-op here)."""

    def close(self, result=None):
        """Close the display once the export is done.

        :param result: what the export returned; None if it failed or was cancelled
        """


class ProgressDialog(Progress):
    """Report in the given DialogProgress (the export button's); its Cancel stops the export."""

    def __init__(self, dialog):
        super().__init__()
        self.dialog = dialog

    def __call__(self, stage, done=0, total=0):
        """Show how far the export is, unless the dialog was cancelled.

        :raises iptvfiles.Cancelled: the dialog's Cancel was pressed
        """
        if self.dialog.iscanceled():
            raise iptvfiles.Cancelled()
        super().__call__(stage, done, total)

    def show(self, percent, line):
        """Show the percentage and line in the dialog."""
        self.dialog.update(percent, line)


class LateProgressDialog(ProgressDialog):
    """A progress dialog that opens only once the export has taken SHOW_AFTER (the refresh button's).

    An export with nothing new is done in about a second, before a dialog would only
    flash; the small progress bar would be hidden under the settings dialog.
    """

    def __init__(self, title):
        super().__init__(None)
        self.title = title
        self.started = time.monotonic()

    def __call__(self, stage, done=0, total=0):
        """Show how far the export is (see ProgressDialog), once the dialog is due."""
        if self.dialog is None:
            Progress.__call__(self, stage, done, total)  # nothing to cancel yet
        else:
            super().__call__(stage, done, total)

    def show(self, percent, line):
        """Show the percentage and line, opening the dialog once SHOW_AFTER has passed."""
        if self.dialog is None:
            if time.monotonic() - self.started < SHOW_AFTER:
                return
            self.dialog = xbmcgui.DialogProgress()
            self.dialog.create(self.title, line)
        super().show(percent, line)

    def close(self, result=None):
        """Close the dialog, if it opened, and notify the result (see BackgroundProgress.close)."""
        if self.dialog is not None:
            self.dialog.close()
        _notify_exported(result)


class BackgroundProgress(Progress):
    """Report in Kodi's small progress bar (out of the way of watching); a notification says when it is done."""

    def __init__(self):
        super().__init__()
        self.dialog = None

    def show(self, percent, line):
        """Show the percentage and line in the progress bar, opening it at the first call."""
        if self.dialog is None:
            self.dialog = xbmcgui.DialogProgressBG()
            self.dialog.create(kodiutil.name(), line)
        self.dialog.update(percent, message=line)

    def close(self, result=None):
        """Close the progress bar and notify the result, if any (see Progress.close)."""
        if self.dialog is not None:
            self.dialog.close()
        _notify_exported(result)


def _notify_exported(result):
    if result:
        xbmcgui.Dialog().notification(kodiutil.name(), kodiutil.string(30189) % tuple(result), sound=False)
