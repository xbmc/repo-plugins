"""The channel lists the add-on shows, in the account's own order: Live channels and My channels."""

import os

import xbmc

from resources.lib import kodiutil
from resources.lib import parental
from resources.lib import provider
from resources.lib.data import onair
from resources.lib.util import atomicfile

# My channels: the manager's list, without the guide (see view).
MANAGE = "manage"
# The subscribed channels the user deactivated: the lists show them greyed out at the bottom, with
# no programme (and so nothing read or fetched for it). The lists' only: Kodi TV hides channels itself.
DEACTIVATED = os.path.join(kodiutil.PROFILE, "deactivated.json")


def listed(client, scope):
    """Return the web guide's channel list "subscribed" or "all"; without a login the public one.

    Adult channels only where the parental lock shows them (as the web player).
    """
    if not client.authed:
        return client.channel_list(kind="all")
    hide_adult = parental.hides_adult(client)
    channels = [c for c in client.channel_list(scope=scope or "subscribed") if not (hide_adult and c.get("adult"))]
    # The account's own channel order (the web's "Csatornáim"), if set; the rest after it.
    try:
        order = {channel_id: i for i, channel_id in enumerate(client.channel_order())}
    except provider.ApiError as e:
        kodiutil.log("channel order unavailable: %s" % e, xbmc.LOGWARNING)
        order = {}
    if order:
        channels.sort(key=lambda c: order.get(str(c["id"]), len(order)))
    return channels


def view(client, scope=None):
    """Return what a channel list shows (see views.channels), as JSON can carry it.

    {"channels" (in the lists' default order, see grouped), "now"/"next" (programmes by
    station), "subscribed" (channel ids; None: all can play), "favourites" (channel ids; None
    without a login), "deactivated" (channel ids), "ordered" (own order set)}.

    :param scope: MANAGE for My channels (no guide); else Live channels
    :raises provider.AuthError: the login was refused
    """
    channels = listed(client, "all")
    subscribed = client.subscribed_ids() if client.authed else None
    favourites = [c["id"] for c in client.channel_list(scope="favourite")] if client.authed else None
    off = deactivated() if client.authed else set()
    channels = grouped(channels, subscribed, favourites, off)
    on_air = {}
    if scope != MANAGE:
        try:
            on_air = client.now_and_next(onair.BLOCKS)
        except provider.ApiError as e:
            kodiutil.log("EPG unavailable: %s" % e, xbmc.LOGWARNING)
        # A deactivated channel's row has no programme, nor one outside the subscription.
        shown = {c["station_id"] for c in channels if str(c["id"]) not in off and (subscribed is None or c["id"] in subscribed)}
        on_air = {station: pair for station, pair in on_air.items() if station in shown}
    return {
        "channels": channels,
        "now": {station: now for station, (now, _) in on_air.items()},
        "next": {station: following for station, (_, following) in on_air.items() if following},
        "subscribed": None if subscribed is None else sorted(subscribed),
        "favourites": favourites,
        "deactivated": sorted(off),
        "ordered": bool(client.authed and client.channel_order()),
    }


def grouped(channels, subscribed, favourites, off):
    """Return the channels in the lists' default order, each group in the order given.

    Favourites first, then the other subscribed channels, the deactivated ones, and those outside
    the subscription last. A deactivated or unsubscribed favourite goes with its own group.

    :param subscribed: the subscribed channel ids; None: all are
    :param favourites: the favourite channel ids; None: none
    :param off: the deactivated channel ids, as strings (see deactivated)
    """
    favourites = set(favourites or ())

    def group(c):
        if subscribed is not None and c["id"] not in subscribed:
            return 3
        if str(c["id"]) in off:
            return 2
        return 0 if c["id"] in favourites else 1

    return sorted(channels, key=group)  # stable: the given order within a group


def deactivated():
    """Return the ids of the channels the user deactivated (as strings); none if there is no such list."""
    return set(atomicfile.read_json(DEACTIVATED, []))


def set_deactivated(channel_id, on):
    """Deactivate a channel in the lists, or activate it again (see DEACTIVATED)."""
    off = deactivated()
    if on:
        off.add(str(channel_id))
    else:
        off.discard(str(channel_id))
    atomicfile.write_json(DEACTIVATED, sorted(off))


def for_kodi_tv(client):
    """Return Kodi TV's channels: the subscribed ones, favourites marked; without a login the public list."""
    channels = listed(client, "subscribed")
    if client.authed:
        favourites = {c["id"] for c in client.channel_list(scope="favourite")}
        channels = [dict(c, favourite=c["id"] in favourites) for c in channels]
    return channels


def by_station(client):
    """Return the subscribed channels by station ID (how airings and positions name a channel)."""
    return {c["station_id"]: c for c in listed(client, "subscribed")}


def archive_enabled(client):
    """Return whether the account has Archive TV (catch-up) on; True without a login (playing logs in first).

    It is per account, switched on by an "Archív TV" consent in the provider's apps (not the web player).
    """
    if not client.authed:
        return True
    return bool(client.valid_account().get("catchup_enabled"))
