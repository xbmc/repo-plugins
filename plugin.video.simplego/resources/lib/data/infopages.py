"""Programme info pages: cast, plot, type, year, episode.

Two caches: the TV export's cast (info.json in its folder) and the plugin lists' pages
(pages.json in the profile, see pages_for).
"""

import os
import time

from resources.lib.data import guidedata
from resources.lib.util import atomicfile

INFO_CACHE = "info.json"
# Info page roles Kodi has a place for (IPTV Simple passes on actors, directors and writers).
CREDIT_ROLES = {"Színész": "actor", "Rendező": "director", "Forgatókönyvíró": "writer", "Író": "writer"}
INFO_WORKERS = 3  # as provider.guide.EPG_WORKERS
PAGE_CACHE = "pages.json"
# A kept page not asked for this long is dropped.
PAGE_KEPT = 30 * 86400


def keys_of(p):
    """Return the info page holding a programme's cast as [(kind, id)]: its series' if any, else its own."""
    if p.get("series_id") and guidedata.kind(p) == "series":
        return [("series", p["series_id"])]
    return [("program", p["program_id"])] if p.get("program_id") else []


def info_for(client, wanted, out_dir, progress=None, stats=None):
    """Return {(kind, id): {"actor": [...], "director": [...], "writer": [...]}} for these info page keys.

    The guide lacks the cast. Each page is fetched once and kept in out_dir/info.json;
    pages no longer in the guide are dropped.

    :param wanted: the info page keys (see keys_of) of the programmes to add the cast to
    :param progress: progress(done, total) is called after each page fetched
    :param stats: gets the number of pages fetched ("pages")
    """
    path = os.path.join(out_dir, INFO_CACHE)
    cache = _read_info(path)
    wanted = set(wanted)
    missing = [k for k in wanted if k not in cache]
    if stats is not None:
        stats["pages"] = len(missing)
    try:
        _fetch_info(client, missing, cache, progress)
    except BaseException:
        _write_info(path, cache)  # keep what was fetched so far
        raise
    cache = {k: v for k, v in cache.items() if k in wanted}
    _write_info(path, cache)
    return cache


def _read_info(path):
    """Return the kept info pages ({(kind, id): credits}); {} if unreadable."""
    return {tuple(k.split("/", 1)): v for k, v in atomicfile.read_json(path, {}).items()}


def _write_info(path, cache):
    """Keep the info pages for the next export."""
    atomicfile.write_json(path, {"/".join(k): v for k, v in cache.items()}, ensure_ascii=False)


def pages_for(client, keys, out_dir, full=True):
    """Return {(kind, id): page} for the plugin's lists, fetching the missing ones.

    A page: "plot", "type" ("movie", "series" or "other"), "year", "season", "episode" and the
    roles (see CREDIT_ROLES).

    :param client: the provider's client, or a function returning it (called only if a page is missing)
    :param full: False when only a plot is wanted: one kept by keep_plot is enough
    """
    path = os.path.join(out_dir, PAGE_CACHE)
    kept = _read_pages(path)
    now = time.time()
    wanted = {"/".join(key): key for key in keys if key[1]}
    missing = [key for name, key in wanted.items() if name not in kept or (full and not kept[name].get("page"))]
    changed = False
    if missing:
        fetched = {}
        _fetch_info(client() if callable(client) else client, missing, fetched, read=_page_of)
        for key, page in fetched.items():
            kept["/".join(key)] = dict(page, used=now)
            changed = True
    for name in set(wanted) & set(kept):
        if kept[name].get("used", 0) < now - 86400:  # rewrite at most daily just for "used"
            kept[name]["used"], changed = now, True
    stale = [name for name, page in kept.items() if page.get("used", 0) < now - PAGE_KEPT]
    for name in stale:
        del kept[name]
    if changed or stale:
        _write_pages(path, kept)
    return {key: kept[name] for name, key in wanted.items() if name in kept}


def keep_plot(program_id, plot, out_dir):
    """Keep a programme's plot from the guide at playback, so the lists need no info page for it."""
    path = os.path.join(out_dir, PAGE_CACHE)
    kept = _read_pages(path)
    name = "program/%s" % program_id
    if program_id and plot and (kept.get(name) or {}).get("plot") != plot:
        kept[name] = dict(kept.get(name) or {}, plot=plot, used=time.time())
        _write_pages(path, kept)


def _read_pages(path):
    """Return the kept pages ({"kind/id": page}); {} if unreadable."""
    return atomicfile.read_json(path, {})


def _write_pages(path, kept):
    atomicfile.write_json(path, kept, ensure_ascii=False)


def _fetch_info(client, keys, cache, progress=None, read=None):
    """Fetch the info pages `keys` into `cache`, a few at a time; failed ones are skipped.

    :param read: read(client, key) -> what to keep of a page, or None; its cast by default
    """
    from concurrent.futures import ThreadPoolExecutor

    read = read or _credits_of
    pool = ThreadPoolExecutor(max_workers=INFO_WORKERS)
    try:
        for done, (key, info) in enumerate(zip(keys, pool.map(lambda key: read(client, key), keys)), 1):
            if info is not None:
                cache[key] = info
            if progress:
                progress(done, len(keys))
    except BaseException:
        try:
            pool.shutdown(wait=False, cancel_futures=True)
        except TypeError:  # Python before 3.9
            pool.shutdown(wait=False)
        raise
    pool.shutdown()


def _credits_of(client, key):
    """Return an info page's credits ({"actor": [...], ...}); None if unavailable."""
    page = _page_of(client, key)
    return None if page is None else {role: names for role, names in page.items() if role in CREDIT_ROLES.values()}


def _page_of(client, key):
    """Return what the lists keep of an info page (see pages_for); None if unavailable."""
    from resources.lib import provider  # lazy: only fetching a page needs it, reading the caches does not

    try:
        page = client.details(*key)
    except provider.ApiError:
        return None
    info = {
        "page": True,
        "plot": ((page.get("details") or {}).get("description") or "").strip(),
        "type": page_kind(page),
        "year": _number(page.get("release_year")),
        "season": _number(page.get("season_number")),
        "episode": _number(page.get("episode_number")),
    }
    for r in page.get("roles") or []:
        role = CREDIT_ROLES.get(r.get("role_name"))
        if role and r.get("person_name"):
            info.setdefault(role, []).append(r["person_name"])
    return info


def episode_numbers(client, program_ids, out_dir):
    """Return {program id: (season, episode)} from info pages; airings carry no numbers."""
    pages = pages_for(client, [("program", pid) for pid in program_ids if pid], out_dir)
    numbered = {key[1]: (page.get("season"), page.get("episode")) for key, page in pages.items()}
    return {pid: numbers for pid, numbers in numbered.items() if all(numbers)}


def _number(value):
    try:
        return int(value) or None
    except (TypeError, ValueError):
        return None


def page_kind(page):
    """Return an info page's programme type, as guidedata.kind: "movie", "series" or "other"."""
    genres = [
        name
        for m in (page.get("details") or {}).get("metadata") or []
        if m.get("type") == "GENRES"
        for name in (m.get("value") or "").split(",")
    ]
    return guidedata.kind({"show_type": page.get("show_type"), "genres": [{"name": g.strip()} for g in genres]})


def programme_credits(p, pages):
    """Return one programme's cast (roles only) from its info page."""
    info = {}
    for key in keys_of(p):
        info.update({role: names for role, names in (pages.get(key) or {}).items() if role in CREDIT_ROLES.values()})
    return info
