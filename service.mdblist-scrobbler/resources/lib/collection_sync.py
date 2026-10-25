import hashlib

from resources.lib import library_snapshot, sync_payload
from resources.lib.utils import local_time_to_utc_iso

CATEGORY = "collection"

# Kodi -> MDBList only: this reflects what's actually in the local library so
# MDBList's collected status is accurate. There is deliberately no pull
# direction -- Kodi can't materialize a file just because MDBList thinks it's
# collected, so a remote-only "collected" flag has nothing local to apply.
#
# Each item also carries its files' media info (resolution, HDR, audio; see
# media_info.py) as "copies", one per Kodi library entry, so two files of the
# same title (a 4K and a 1080p version) are both sent. It's kept in sync_state
# so a changed file (an upgrade in place) pushes the item again.


def _to_api_datetime(value):
    # Kodi's dateadded is naive local time; MDBList expects UTC.
    return local_time_to_utc_iso(value)


# Media-only re-pushes per run (an item already collected whose media info
# changed): the first run after upgrading would otherwise re-push the whole
# library at once; the rest follow on later runs.
MEDIA_REPUSH_PER_RUN = 1000


def _copy(record):
    """One library entry's media info as a copy, or None when nothing about the
    file is known. The key is a hash of the file path: stable across library
    rebuilds (unlike the dbid) and the same on every device sharing the file."""
    media = record.get("media") or {}
    if not media:
        return None
    digest = hashlib.sha1((record.get("file") or "").encode("utf-8")).hexdigest()[:16]
    return dict(media, copy_key="f-" + digest)


def _title_groups(records, ids_of):
    """Library entries grouped by title: entries sharing an id join one group,
    unless their ids contradict it (a different value for the same provider --
    e.g. two films mis-scraped with one imdb id stay apart). Returns
    {id(record): group}, each group a dict of merged ids and its records."""
    index, by_record = {}, {}  # "provider:value" -> group
    for record in records:
        ids = {p: v for p, v in ids_of(record).items() if v not in (None, "")}
        candidates = {id(g): g for g in (index.get("{}:{}".format(p, v)) for p, v in ids.items()) if g is not None}
        matches = [g for g in candidates.values() if all(g["ids"].get(p) in (None, v) for p, v in ids.items())]
        group = matches[0] if matches else {"ids": {}, "records": []}
        for other in matches[1:]:  # this entry bridges groups: merge them
            if any(group["ids"].get(p) not in (None, v) for p, v in other["ids"].items()):
                continue  # ...unless the groups contradict each other
            group["records"].extend(other["records"])
            for p, v in other["ids"].items():
                group["ids"].setdefault(p, v)
            for r in other["records"]:
                by_record[id(r)] = group
        group["records"].append(record)
        by_record[id(record)] = group
        for p, v in ids.items():
            group["ids"].setdefault(p, v)
        for p, v in group["ids"].items():
            index["{}:{}".format(p, v)] = group
    return by_record


def _attach_copies(items, records, key_of, ids_of):
    """Gives every item the copies of all library entries of its title (see
    _title_groups), so two entries of one film that stayed separate items (their
    ids differ) both push the full set and neither push drops the other's file.
    The item set and keys stay exactly the id-indexed ones, so sync_state keys
    never change. Media info is a bonus: an entry without it (not probed, or
    streamed) adds no copy, and the title's other copies are still sent."""
    records = [r for r in records if r["file"]]
    groups = _title_groups(records, ids_of)
    groups_of_key = {}  # entries in separate groups can still share a key
    for record in records:
        key = key_of(record)
        if key in items:
            group = groups[id(record)]
            groups_of_key.setdefault(key, {})[id(group)] = group
    for key, key_groups in groups_of_key.items():
        copies, seen = [], set()
        for record in (r for g in key_groups.values() for r in g["records"]):
            copy = _copy(record)
            if copy and copy["copy_key"] not in seen:
                seen.add(copy["copy_key"])
                copies.append(copy)
        items[key]["copies"] = copies


def _current_collected_items(snapshot):
    items = {}
    for movie in library_snapshot.iter_movies(snapshot):
        if movie["file"]:
            key = library_snapshot.canonical_movie_key(movie["ids"])
            if key:
                items[key] = {
                    "type": "movie", "ids": movie["ids"],
                    "collected_at": _to_api_datetime(movie["dateadded"]),
                    "copies": [],
                }
    for episode in library_snapshot.iter_episodes(snapshot):
        if episode["file"]:
            key = library_snapshot.canonical_episode_key(episode["show_ids"], episode["season"], episode["episode"])
            if key:
                items[key] = {
                    "type": "episode", "show_ids": episode["show_ids"],
                    "season": episode["season"], "episode": episode["episode"],
                    "collected_at": _to_api_datetime(episode["dateadded"]),
                    "copies": [],
                }
    _attach_copies(
        items, library_snapshot.iter_all_movies(snapshot),
        lambda r: library_snapshot.canonical_movie_key(r["ids"]),
        lambda r: r["ids"],
    )
    _attach_copies(
        items, library_snapshot.iter_all_episodes(snapshot),
        lambda r: library_snapshot.canonical_episode_key(r["show_ids"], r["season"], r["episode"]),
        lambda r: {"{}:{}:{}".format(p, r["season"], r["episode"]): v for p, v in r["show_ids"].items()},
    )
    return items


def _media_fields(item):
    # No "copies" for an item with no known media info, which leaves
    # MDBList's stored copies alone.
    copies = item.get("copies") or []
    return {"copies": copies} if copies else {}


def _copies_fingerprint(item):
    return sorted(tuple(sorted(c.items())) for c in item.get("copies") or [])


def _media_changed(known_item, item):
    """A collected item whose media info differs from what was last pushed
    is pushed again. State from before media info existed has none, so items
    with media info are pushed once to fill it in. No media info now (the file
    isn't probed yet, or was replaced) is unknown, never a change: the copies
    on MDBList stay until the file is read again."""
    if not item.get("copies"):
        return False
    return _copies_fingerprint(known_item) != _copies_fingerprint(item)


def _capped(value_changed, limit):
    pushed = [0]

    def changed(known_item, item):
        if pushed[0] >= limit or not value_changed(known_item, item):
            return False
        pushed[0] += 1
        return True
    return changed


def _push_add(items):
    sync_payload.push_items(CATEGORY, "/sync/collection", "collected_at", items, extra_fields=_media_fields)


def _push_remove(items):
    sync_payload.push_items_remove(CATEGORY, "/sync/collection/remove", items)


def push(snapshot, allow_remove=False):
    """Push + reconcile: anything newly present in the Kodi library is added,
    anything that dropped out (file removed/library item deleted) since the
    last run is removed from MDBList's collection -- the "clean collection"
    step, mirroring script.trakt's collection sync.

    allow_remove: see sync_payload.diff_and_reconcile. Collection sync has no
    pull direction (see the module note above), so a wrongly-pushed removal
    here has no remote-to-local self-healing path at all."""
    current = _current_collected_items(snapshot)
    return sync_payload.diff_and_reconcile(
        CATEGORY, current, _push_add, _push_remove,
        value_changed=_capped(_media_changed, MEDIA_REPUSH_PER_RUN), allow_remove=allow_remove
    )
