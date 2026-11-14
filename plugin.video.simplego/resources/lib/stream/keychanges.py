"""Where a programme watched back changes its encryption key (standard library only).

Such a programme plays in parts, one per key (see manifest.ManifestRewriter._key_changes).

Keys are taken to change once per run, never back: a track's first and last
fragment say whether its key changes, and a binary search finds where (a dozen
fragment heads for a film). Other tracks change at the same moments, so two
heads around each of the video's changes usually settle them.
"""

from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor

from resources.lib.stream import dash

# A track group: its AdaptationSet, the representation read (all qualities share a key),
# the timeline's timescale and (start, duration) segments.
Group = namedtuple("Group", "aset tag scale segments")


class Unknown(Exception):
    """A fragment needed to find a key change could not be read."""


def groups(asets, mpd_url):
    """Return the encrypted track groups of a manifest's adaptation sets, with their timelines."""
    out = []
    for aset in asets:
        tags = dash.representations(aset)
        template = dash.SEGMENT_TEMPLATE.search(aset)
        if not tags or not template or not dash.init_url(aset, tags[0], mpd_url):
            continue
        scale, segments = dash.parse_timeline(template.group(0))
        if segments:
            out.append(Group(aset, dash.smallest(tags), scale, segments))
    return out


def video_index(track_groups):
    """Return the index of the video group; 0 if there is none."""
    return next((i for i, g in enumerate(track_groups) if dash.is_video(g.aset)), 0)


def find(track_groups, key, hint=None):
    """Return each group's indexes of the segments that start a new key: [[...], ...] in group order.

    :param key: key(group, n) returns (pssh, kid) of the group's n-th fragment (it may raise Unknown)
    :param hint: what this returned for the programme before; taken as it is if it fits
    """
    if _fits(track_groups, hint):
        return hint
    video = track_groups[video_index(track_groups)]
    at = search(video, key)
    times = [video.segments[i][0] / video.scale for i in at]

    def changes(group):
        return at if group is video else near(group, key, times)

    with ThreadPoolExecutor(max_workers=len(track_groups)) as pool:
        return list(pool.map(changes, track_groups))


def _fits(track_groups, hint):
    """Tell whether changes found before still fit these timelines."""
    if hint is None or len(hint) != len(track_groups):
        return False
    return all(i < len(g.segments) for g, found in zip(track_groups, hint, strict=True) for i in found)


def search(group, key):
    """Return the indexes of a group's segments that start a new key, by binary search."""
    out, low, high = [], 0, len(group.segments) - 1
    while key(group, low)[1] != key(group, high)[1]:
        first, a, b = key(group, low)[1], low, high
        while b - a > 1:
            middle = (a + b) // 2
            if key(group, middle)[1] == first:
                a = middle
            else:
                b = middle
        out.append(b)
        low = b
    return out


def near(group, key, times):
    """Return where a group changes keys, looking only around the video's changes (`times`).

    A group that does not change right there is searched on its own (see search).
    """
    out = []
    for seconds in times:
        i = dash.first_at(group.segments, group.scale, seconds)
        if not 0 < i < len(group.segments) or key(group, i - 1)[1] == key(group, i)[1]:
            return search(group, key)
        out.append(i)
    return out
