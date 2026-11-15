"""What the main menu says beside its rows: channel counts and the favourite programmes by type.

Made by the play service (its client and kept lists are warm, see playservice), else by the plugin.
"""

import time

from resources.lib import provider
from resources.lib.data import channellist


def counts(client):
    """Return what the main menu counts: each a count, or None if unknown; and "timed".

    The keys: subscribed, favourites, deactivated, series, other. Each part timed
    ("subscribed 3 ms"), for the debug log: which of them is worth its time.
    """
    timed = []

    def timing(name, part):
        begun = time.time()
        try:
            return part()
        except provider.ApiError:
            return None
        finally:
            timed.append("%s %d ms" % (name, (time.time() - begun) * 1000))

    subscribed = timing("subscribed", client.subscribed_ids)
    favourites = timing("favourites", lambda: client.channel_list(scope="favourite"))
    off = timing("deactivated", channellist.deactivated)
    kinds = timing("watchlist", lambda: [item.get("show_type") == "Series" for item in client.watchlist()])
    return {
        "subscribed": None if subscribed is None else len(subscribed),
        "favourites": None if favourites is None else len(favourites),
        # Only those still subscribed: a channel deactivated and since dropped from the subscription is not one.
        "deactivated": None if subscribed is None else sum(channellist.is_deactivated(i, off or set()) for i in set(subscribed)),
        # The favourite programmes by type: series, and the rest ("Program": films, but not only).
        "series": None if kinds is None else sum(kinds),
        "other": None if kinds is None else len(kinds) - sum(kinds),
        "timed": timed,
    }
