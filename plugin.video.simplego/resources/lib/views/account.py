"""The account's actions: logging in and out, its devices, the parental lock."""

import xbmc
import xbmcgui

from resources.lib import kodiutil
from resources.lib import parental
from resources.lib.login import loginstate
from resources.lib.login import phonelogin
from resources.lib.views import rows

_s = kodiutil.string


class AccountViews:
    """The account's actions (see plugin.ROUTES).

    :param call: the plugin call (see views.call.Call)
    """

    def __init__(self, call):
        self._call = call

    def do_login(self):
        """Log in through the phone (QR code), then refresh the listing."""
        # Phone only: unlike a browser login, it adds no device besides Kodi itself.
        text = phonelogin.wait_for_token(self._call.client)
        if text:
            self._call.client.login_with_refresh_token(text)
            loginstate.login_changed()
            xbmcgui.Dialog().notification(kodiutil.name(), _s(30022))
            xbmc.executebuiltin("Container.Refresh")

    def do_logout(self):
        """Log out after asking, then refresh the listing."""
        if xbmcgui.Dialog().yesno(kodiutil.name(), _s(30023)):
            self._call.client.logout()
            loginstate.login_changed()
            xbmc.executebuiltin("Container.Refresh")

    def do_devices(self):
        """List the account's devices; pick one to remove it.

        This Kodi is listed but not removable (that would only log it out). The provider's
        set-top boxes are left out: they take no slot of the device limit.
        """
        client = self._call.client
        dialog = xbmcgui.Dialog()
        position = 0
        while True:
            devices = [d for d in client.devices() if not is_stb(d)]
            labels = [device_label(client, d) for d in devices]
            if not labels:
                return
            choice = dialog.select(_s(30043), labels, preselect=min(position, len(labels) - 1))
            if choice < 0:
                return
            position = choice
            device = devices[choice]
            if is_current(client, device):
                continue
            if dialog.yesno(_s(30034), _s(30036), nolabel=_s(30047), yeslabel=_s(30046)):
                client.remove_device(device["id"])
                dialog.notification(kodiutil.name(), _s(30037))
                loginstate.show_account(client, fresh=True)

    def do_parental(self):
        """Change the parental lock (run from the settings): the account's PIN first."""
        if not parental.ask_pin(self._call.client):
            return
        dialog = xbmcgui.Dialog()
        current = parental.settings()
        age = current["age"] if current["age"] in parental.AGES else 0
        choice = dialog.select(_s(30149), [_s(i) for i in parental.AGE_LABELS], preselect=parental.AGES.index(age))
        if choice < 0:
            return
        unrated = dialog.yesno(_s(30148), _s(30162), nolabel=_s(30165), yeslabel=_s(30164))
        adult = dialog.yesno(_s(30148), _s(30163), nolabel=_s(30165), yeslabel=_s(30164))
        # The open settings dialog would write its old copy back on close: close, write, reopen.
        reopen = xbmc.getCondVisibility("Window.IsActive(addonsettings)")
        if reopen:
            kodiutil.close_settings()
        parental.save({"age": parental.AGES[choice], "unrated": unrated, "adult": adult})
        # The Kodi TV channels follow the adult setting: the service exports.
        kodiutil.home().setProperty(kodiutil.EXPORT_REQUEST, "1")
        if reopen:
            kodiutil.open_settings()


def is_current(client, device):
    """Return whether the account's device is this Kodi."""
    return bool(device.get("current_device") or device.get("id") == client.device_id)


def device_label(client, device):
    """Return a device's row in the devices list: its name, this Kodi's said so."""
    name = device.get("name") or "?"
    if is_current(client, device):
        return rows.greyed(_s(30035) % name)
    return name


def is_stb(device):
    """Return whether a device is one of the provider's own boxes (left out of the devices list)."""
    # device_type "AndroidStb" (the Smartbox): the web page's "STB Eszközök".
    return "stb" in (device.get("device_type") or "").lower()
