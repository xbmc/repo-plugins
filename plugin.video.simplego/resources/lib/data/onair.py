"""What is on a channel, from the guide blocks kept in the profile.

The Kodi TV export keeps the blocks of its days; without it, a block is
fetched the first time something in it is asked for, and kept.
"""

import os
import time

from resources.lib import kodiutil
from resources.lib.util import isotime

# The guide blocks every part reads, where the Kodi TV export keeps them ("iptv" is
# iptvfiles.OUT_DIR, repeated here to keep this module's imports light).
BLOCKS = os.path.join(kodiutil.PROFILE, "iptv", "blocks")
# What on_air answered a moment ago, by (station, when): a channel start asks the same
# programme three times, each a guide block read and parsed otherwise.
RECENT = 10
_recent = {}


def on_air(client, station, when):
    """Return (programme, its end) on the station at `when` (seconds or "...Z"); (None, None) if unknown."""
    if isinstance(when, str):
        when = isotime.stamp(when)
    if not station:
        return None, None
    now = time.time()
    seen = _recent.get((station, when))
    if seen and now - seen[0] < RECENT:
        return seen[1]
    found = client.programme_at(station, when, BLOCKS)
    for key in [k for k, (at, _) in _recent.items() if now - at >= RECENT]:
        _recent.pop(key, None)
    _recent[(station, when)] = (now, found)
    return found


def on_air_check(client, station, test):
    """Return a check for the proxy: `test` of the programme now on the station (False if none is known).

    The answer holds until the programme ends.
    """
    known = {"until": 0, "answer": False}

    def check():
        now = time.time()
        if station and now >= known["until"]:
            programme, end = on_air(client, station, now)
            known["answer"] = bool(programme) and test(programme)
            known["until"] = end or now + 60
        return known["answer"]

    return check
