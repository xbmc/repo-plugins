"""Kodi TV: the settings' buttons that put the channels and the guide into Kodi's TV menu or take them out."""

import xbmc
import xbmcgui

from resources.lib import kodiutil

_s = kodiutil.string
_log = kodiutil.log


class TvViews:
    """Kodi TV's actions (see views.routes).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_tv_toggle(self):
        """Switch the TV menu on or off (the settings' row, its state on the right; see kodipvr.show_state)."""
        from resources.lib.tv import kodipvr

        return self.do_tv_off() if kodipvr.enabled() else self.do_tv_on()

    def do_tv_on(self):
        """Show the channels and the guide in Kodi's TV menu (the settings' button), once confirmed."""
        from resources.lib.tv import exportprogress
        from resources.lib.tv import iptvfiles
        from resources.lib.tv import kodipvr

        dialog = xbmcgui.Dialog()
        # Installing another add-on and writing into its settings needs the user's clear yes:
        # https://kodi.wiki/view/Add-on_rules#Requirements_for_all_python_addons
        if not dialog.yesno(_s(30206), _s(30208)):
            return
        # The settings dialog saves what it shows when it closes: closed first,
        # so it does not put the switch back; opened again at the end, so it
        # lists the TV guide category.
        kodiutil.close_settings()
        progress = xbmcgui.DialogProgress()
        progress.create(_s(30224), _s(30032))
        try:
            done = kodipvr.switch_on(self._call.client, exportprogress.ProgressDialog(progress))
        except iptvfiles.Cancelled:
            done = False
        finally:
            progress.close()
        if done is None:
            dialog.ok(kodiutil.name(), _s(30031))
        elif done:
            n_channels, n_progs, changed = done
            _log("TV menu switched on (%d channels, %d programmes)" % (n_channels, n_progs))
            if changed and ask_restart(_s(30033) % (n_channels, n_progs)):
                return
            if not changed:
                dialog.ok(kodiutil.name(), _s(30144) % (n_channels, n_progs))
        kodiutil.open_settings()

    def do_tv_refresh(self):
        """Refresh the Kodi TV files now, as the schedule does (the settings' button).

        Fetches only stale blocks, so it is mostly done in a second (see exportprogress.LateProgressDialog).
        """
        from resources.lib.tv import exportprogress
        from resources.lib.tv import iptvfiles
        from resources.lib.tv import kodipvr

        # The settings dialog stays open: closing and opening it again flashes the whole window.
        progress = exportprogress.LateProgressDialog(_s(30213))
        result = None
        try:
            result = kodipvr.export(self._call.client, progress=progress)
        except iptvfiles.Cancelled:
            pass
        finally:
            progress.close(result)  # its notification says what was exported

    def do_tv_off(self):
        """Take the channels and the guide out of Kodi's TV menu (the settings' button), once confirmed."""
        from resources.lib.tv import kodipvr

        if not xbmcgui.Dialog().yesno(_s(30207), _s(30209)):
            return
        kodiutil.close_settings()
        progress = xbmcgui.DialogProgress()
        progress.create(_s(30207), _s(30211))
        try:
            removed = kodipvr.switch_off(progress.update)
        finally:
            progress.close()
        _log("TV menu switched off")
        if removed and ask_restart(_s(30210)):
            return
        kodiutil.open_settings()


def ask_restart(text):
    """Ask to restart Kodi for IPTV Simple to read our instance (see kodipvr.switch_on); whether it goes now.

    In Kodi's words where it has them ("Restart required", "Restart", "Quit"). Kodi restarts itself
    only on Windows and Linux: on Android it quits, to be started again by hand, and says so.
    """
    android = kodiutil.android()
    question = _s(30257 if android else 30258)
    yes = kodiutil.kodi_string(13009 if android else 13313)
    if not xbmcgui.Dialog().yesno(kodiutil.kodi_string(24074), "%s %s" % (text, question), yeslabel=yes):
        return False
    xbmc.executebuiltin("Quit" if android else "RestartApp")
    return True
