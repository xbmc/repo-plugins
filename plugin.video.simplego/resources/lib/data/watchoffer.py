"""What to offer when an airing is no longer watched back: its programme onto the favourites, else off Continue watching.

A favourite lists the programme's next airings (see views.programmes): a series as a whole, a film itself.
Offered only with an airing to come on a channel of the subscription: the provider leaves out a favourite
with no airing (seen 2026-11-02: taken without a word, never listed), and one with none is no use either.
One question at most: the removal only when there is no favourite to offer.
"""

from resources.lib import provider
from resources.lib.data import channellist
from resources.lib.data import continuelist
from resources.lib.data import guidedata
from resources.lib.data import onair
from resources.lib.util import isotime
from resources.lib.util import localtime


def offer(client, channel_id, start):
    """Return what to offer for the airing at `start` ("...Z") on a channel: {"id", "kind", "title", "next"}.

    "next" is its next airing, as said ("2026.11.05. 20:00, Mozi+ HD"). None if the guide does not know it,
    it is a favourite already, or no airing of it is to come.
    """
    programme = onair.on_air(client, client.station_of(channel_id), start)[0]
    if not programme:
        return None
    if guidedata.kind(programme) == "series" and programme.get("series_id"):
        wanted = {"id": programme["series_id"], "kind": "series"}
    elif programme.get("program_id"):
        wanted = {"id": programme["program_id"], "kind": "program"}
    else:
        return None
    if wanted["id"] in {item.get("id") for item in client.watchlist()}:
        return None
    coming = next_airing(client, wanted["id"], wanted["kind"])
    if not coming:
        return None
    airing, channel = coming
    return dict(
        wanted,
        title=programme.get("description") or "",
        next="%s, %s" % (localtime.local_time(airing["start_utc"]), channel["name"]),
    )


def next_airing(client, item_id, kind):
    """Return (the next airing to come, its channel) of a series or a programme on a subscribed channel; None if none."""
    channels = channellist.by_station(client)
    now = isotime.iso()
    coming = sorted(
        (a for a in client.airings(item_id, kind)[1] if a.get("start_utc", "") > now and str(a.get("station_id")) in channels),
        key=lambda a: a["start_utc"],
    )
    return (coming[0], channels[str(coming[0]["station_id"])]) if coming else None


def removal(client, channel_id, start):
    """Return {"mark": its row's id} to offer off Continue watching if the airing at `start` is listed there; None if not."""
    mark = continuelist.find(client.station_of(channel_id), start, client.bookmarks())
    return {"mark": mark["id"]} if mark else None


def offer_for_play(client, channel_id, programme):
    """Return offer(), else removal(), for a play address's programme (see guidedata.from_param); None if neither."""
    airing = guidedata.from_param(programme)
    if not airing:
        return None
    try:
        return offer(client, channel_id, airing["start"]) or removal(client, channel_id, airing["start"])
    except provider.ApiError:  # no guide, favourites or positions to tell by: the message alone
        return None
