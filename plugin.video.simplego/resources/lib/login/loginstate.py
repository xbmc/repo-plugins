"""What the add-on shows of the login and the account: the settings' rows, and the login running out."""

import time

import xbmc
import xbmcgui

from resources.lib import kodiutil
from resources.lib import parental
from resources.lib import provider
from resources.lib.util import localtime

# The login runs out a year after it was made; warned this long before.
LOGIN_NOTICE = 14 * 24 * 3600


def login_changed(client):
    """Make the service export again and the settings follow, after a login or logout.

    :param client: the client that logged in or out
    """
    kodiutil.home().setProperty(kodiutil.LOGIN_CHANGED, "1")
    show_login_state(client)


def show_login_state(client):
    """Update the hidden settings that show what needs a login only to a logged-in user."""
    kodiutil.set_setting("logged_in", client.is_logged_in())
    if client.authed:
        try:
            kodiutil.set_setting("parental_enabled", bool(client.parental_lock_enabled()))
            parental.show()
            show_account(client)
        except provider.ApiError as e:
            kodiutil.log("account check failed: %s" % e, xbmc.LOGWARNING)


def show_account(client, fresh=False):
    """Update the account's read-only rows: the login, the device slots in use, the subscription."""
    info = client.valid_account(force=fresh)
    # The account's "email" is an opaque provider ID, not the address: only the expiry is shown.
    kodiutil.set_setting("account_login", kodiutil.string(30193) % _date(client.login_expires()))
    # Shown on the "My devices" button.
    kodiutil.set_setting("devices", "%s / %s" % (info.get("current_logged_in_devices", "?"), info.get("max_device_allowed", "?")))
    kodiutil.set_setting("account_subscription", info.get("account_type") or "?")
    # What the subscription has, each a read-only checkbox: one line would not fit.
    features = {
        "account_catchup": "catchup_enabled",
        "account_timeshift": "timeshift_enabled",
        "account_recording": "is_recording_enabled",
    }
    for setting_id, key in features.items():
        kodiutil.set_setting(setting_id, bool(info.get(key)))


def warn_if_login_runs_out(client):
    """Tell the user to log in again when the login runs out within LOGIN_NOTICE."""
    expires = client.login_expires()
    if client.is_logged_in() and expires and expires - time.time() < LOGIN_NOTICE:
        text = kodiutil.string(30201) % _date(expires)
        xbmcgui.Dialog().notification(kodiutil.name(), text, xbmcgui.NOTIFICATION_WARNING, 10000)


def _date(when):
    return localtime.local_date(when) if when else "?"
