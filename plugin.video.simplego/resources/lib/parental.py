"""The parental lock, kept by the add-on as the provider's apps keep it.

The server does not enforce it: each app holds its own age limit and toggles; only the
PIN is the account's (checked by the provider).
"""

import os
import time

import xbmc
import xbmcgui

from resources.lib import kodiutil
from resources.lib import provider
from resources.lib.data import guidedata
from resources.lib.data import onair
from resources.lib.util import atomicfile

# Ages of the lock's limit, as the web player offers them (19: "18+"; 0: none), and their names.
AGES = (0, 6, 12, 16, 18, 19)
AGE_LABELS = (30128, 30151, 30152, 30153, 30154, 30155)
FILE = os.path.join(kodiutil.PROFILE, "parental.json")
# As the web player starts: no age limit, unrated content locked, adult channels hidden.
DEFAULTS = {"age": 0, "unrated": True, "adult": False}
# Programmes the PIN was given for in this process, (channel, start) -> when: playing one
# again soon (the restart at a key change, see keyfollower) does not ask again.
_unlocked = {}
UNLOCKED_FOR = 6 * 3600


def settings():
    """Return this Kodi's lock settings: {"age", "unrated", "adult"} (see AGES).

    Kept in a profile file, not in settings: the open settings dialog would write its old copy back.
    """
    return dict(DEFAULTS, **atomicfile.read_json(FILE, {}))


def save(values):
    """Keep these lock settings (see settings) and show them in the settings."""
    atomicfile.write_json(FILE, values)
    show()


def show():
    """Update the settings' read-only rows for the lock."""
    values = settings()
    kodiutil.set_setting("parental_age", values["age"] if values["age"] in AGES else 0)
    kodiutil.set_setting("parental_unrated", bool(values["unrated"]))
    kodiutil.set_setting("parental_adult", bool(values["adult"]))


def lock_on(client):
    """Return whether the account has a parental lock; when unknown (no answer), it has."""
    if not client.authed:
        return False
    try:
        return client.parental_lock_enabled()
    except provider.ApiError as e:
        kodiutil.log("parental lock check failed: %s" % e, xbmc.LOGWARNING)
        return True


def hides_adult(client):
    """Return whether adult channels are left out of the lists (as the web player)."""
    return lock_on(client) and not settings()["adult"]


def locked(age, adult=False):
    """Return whether the settings hold a programme of this age (None: unrated) on an adult channel or not."""
    values = settings()
    if adult and not values["adult"]:
        return True
    if age is None:
        return values["unrated"]
    return bool(values["age"]) and age >= values["age"]


def ask_pin(client):
    """Ask the user for the account's PIN, checked by the provider; False if cancelled or wrong (which it says)."""
    pin = xbmcgui.Dialog().numeric(0, kodiutil.string(30159), "", True)
    if not pin:
        return False
    if len(pin) == 4 and pin.isdigit() and client.verify_pin(pin):
        return True
    xbmcgui.Dialog().ok(kodiutil.name(), kodiutil.string(30160))
    return False


def gate(client, channel, programme):
    """Ask for the PIN if the lock holds what is about to play (`programme`, else what is on now).

    Return the start of the programme the PIN was given for (see locked_now), else None.

    :raises provider.ParentalLockError: the lock holds it and no right PIN was given
    """
    if not lock_on(client):
        return None
    entry = client.channel_of(channel["id"]) or {}
    if programme is not None and "age" in programme:
        age, start = programme["age"], programme["start"]
    else:
        # Live, or a programme whose age the URL does not carry: from the guide.
        when = time.time() if programme is None else programme["start"]
        found = onair.on_air(client, entry.get("station_id"), when)[0] or {}
        age = guidedata.rating_age(found.get("ratings"))
        start = found.get("start_time") or (programme or {}).get("start")
    if not locked(age, entry.get("adult")):
        return None
    key = (channel["id"], start)
    if time.time() - _unlocked.get(key, 0) < UNLOCKED_FOR:
        return start
    if not ask_pin(client):
        raise provider.ParentalLockError("locked by the parental lock: age %s" % age)
    _unlocked[key] = time.time()
    return start


def locked_now(client, channel, programme, unlocked):
    """Return whether, on a live stream, the lock holds the programme now on.

    :param unlocked: the start gate returned: the programme the PIN was given for is not held
    """
    if programme.get("start_time") == unlocked or not lock_on(client):
        return False
    return locked(guidedata.rating_age(programme.get("ratings")), (client.channel_of(channel["id"]) or {}).get("adult"))
