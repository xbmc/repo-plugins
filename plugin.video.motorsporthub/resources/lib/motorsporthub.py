"""Motorsport Hub — Kodi video add-on.

Reads the same public snapshot the web app uses (no key, no secret) and turns
it into Kodi directories. Nothing is hosted or re-streamed: YouTube items are
handed to the official YouTube add-on, FAST channels play their public HLS URL.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE = sys.argv[0]

SNAPSHOT_URL = "https://watch.prototipo.nl/data/snapshot.json"
SITE_URL = "https://motorsport.prototipo.nl"
CACHE_SECONDS = 120

_cache = {"at": 0, "data": None}


def log(msg):
    xbmc.log("[MotorsportHub] %s" % msg, xbmc.LOGINFO)


def spoilers_on():
    return ADDON.getSettingBool("spoilers")


def snapshot():
    """Fetch the public catalog, cached briefly so browsing stays snappy."""
    now = time.time()
    if _cache["data"] and now - _cache["at"] < CACHE_SECONDS:
        return _cache["data"]
    req = urllib.request.Request(
        SNAPSHOT_URL, headers={"User-Agent": "MotorsportHub-Kodi/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.load(resp)
    _cache["at"] = now
    _cache["data"] = data
    return data


def url_for(**kwargs):
    return BASE + "?" + urllib.parse.urlencode(kwargs)


ADDON_PATH = ADDON.getAddonInfo("path")
FANART = os.path.join(ADDON_PATH, "resources", "fanart.jpg")
ICON = os.path.join(ADDON_PATH, "resources", "icon.png")


def art_for(item):
    """Give every item real artwork so skins show tiles, not folder icons."""
    thumb = item.get("thumbnail") or ""
    return {"thumb": thumb or ICON, "icon": thumb or ICON,
            "poster": thumb or ICON, "banner": thumb,
            "fanart": FANART}


def category_art(data, cid):
    """Use the artwork of the best-known source in a category as its cover."""
    for s in data.get("sources", []):
        if cid in (s.get("catalogs") or []) and s.get("thumbnail"):
            return art_for(s)
    return {"thumb": ICON, "icon": ICON, "poster": ICON, "fanart": FANART}


def add_dir(label, url, art=None, plot=""):
    li = xbmcgui.ListItem(label=label)
    li.setArt(art or {})
    li.setInfo("video", {"title": label, "plot": plot})
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=True)


def add_playable(label, url, art=None, plot=""):
    li = xbmcgui.ListItem(label=label)
    li.setArt(art or {})
    li.setInfo("video", {"title": label, "plot": plot})
    li.setProperty("IsPlayable", "true")
    xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=False)


def root():
    data = snapshot()
    live = [l for l in data.get("live", []) if not l.get("upcoming")]
    cal = data.get("calendar", [])
    cats = data.get("categories", [])

    live_art = {"thumb": "https://i.ytimg.com/vi/%s/hqdefault.jpg" % live[0]["videoId"],
                "poster": "https://i.ytimg.com/vi/%s/hqdefault.jpg" % live[0]["videoId"],
                "fanart": FANART} if live else {"thumb": ICON, "poster": ICON, "fanart": FANART}
    add_dir("[COLOR red]● Live Now[/COLOR] (%d)" % len(live),
            url_for(action="live"), live_art,
            plot="Every official channel streaming right now.")
    cal_art = art_for(cal[0]) if cal else {"thumb": ICON, "poster": ICON, "fanart": FANART}
    add_dir("This Weekend (%d)" % len(cal), url_for(action="calendar"), cal_art,
            plot="Upcoming sessions in your own timezone.")

    for c in cats:
        cid = c.get("id")
        if cid in ("live_now", "calendar"):
            continue
        count = len([s for s in data.get("sources", [])
                     if cid in (s.get("catalogs") or [])])
        if not count:
            continue
        add_dir("%s (%d)" % (c.get("name", cid), count),
                url_for(action="category", id=cid), category_art(data, cid),
                plot="%d official sources." % count)

    xbmcplugin.endOfDirectory(HANDLE)


def live_list():
    data = snapshot()
    spoil = spoilers_on()
    items = [l for l in data.get("live", []) if not l.get("upcoming")]
    if not items:
        add_dir("Nothing live right now — check This Weekend",
                url_for(action="calendar"))
    for l in items:
        name = l.get("sourceName", "Live")
        title = l.get("title") or name
        label = "[COLOR red]● LIVE[/COLOR]  %s" % (title if spoil else name)
        art = {"thumb": "https://i.ytimg.com/vi/%s/hqdefault.jpg" % l["videoId"]} if spoil \
            else {"thumb": l.get("thumbnail") or ""}
        add_playable(label, url_for(action="play_yt", id=l["videoId"]), art,
                     plot="" if spoil else "Live broadcast — title hidden to avoid spoilers.")
    xbmcplugin.endOfDirectory(HANDLE)


def calendar_list():
    data = snapshot()
    by_id = {s["id"]: s for s in data.get("sources", [])}
    events = data.get("calendar", [])
    if not events:
        add_dir("No sessions in the next 7 days", url_for(action="root"))
    for ev in events:
        when = time.strftime("%a %d %b, %H:%M", time.localtime(ev["ms"] / 1000))
        label = "%s  —  %s" % (when, ev.get("name", ""))
        src = by_id.get(ev.get("sourceId"))
        plot = "%s%s" % (ev.get("league", ""),
                         " · " + ev["venue"] if ev.get("venue") else "")
        if src:
            add_dir(label, url_for(action="source", id=src["id"]),
                    art_for(ev), plot)
        else:
            add_dir(label, url_for(action="calendar"), art_for(ev), plot)
    xbmcplugin.endOfDirectory(HANDLE)


def category_list(cid):
    data = snapshot()
    live_ids = {l["sourceId"] for l in data.get("live", []) if not l.get("upcoming")}
    for s in data.get("sources", []):
        if cid not in (s.get("catalogs") or []):
            continue
        label = s.get("name", "?")
        if s["id"] in live_ids:
            label = "[COLOR red]● LIVE[/COLOR]  " + label
        elif s.get("hls") or s.get("type") == "fast_channel":
            label = "[COLOR orange]Live TV[/COLOR]  " + label
        add_dir(label, url_for(action="source", id=s["id"]), art_for(s),
                s.get("notes", ""))
    xbmcplugin.endOfDirectory(HANDLE)


def source_entry(sid):
    """A single source: play it if we can, otherwise explain where it lives."""
    data = snapshot()
    src = next((s for s in data.get("sources", []) if s["id"] == sid), None)
    if not src:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    live = next((l for l in data.get("live", [])
                 if l.get("sourceId") == sid and not l.get("upcoming")), None)
    if live:
        add_playable("[COLOR red]● Watch live[/COLOR]  %s" % src["name"],
                     url_for(action="play_yt", id=live["videoId"]), art_for(src))
    if src.get("hls"):
        add_playable("[COLOR orange]Live TV[/COLOR]  %s" % src["name"],
                     url_for(action="play_hls", url=src["hls"]), art_for(src))
    if src.get("channelId"):
        add_dir("Open channel in YouTube",
                "plugin://plugin.video.youtube/channel/%s/" % src["channelId"],
                art_for(src), src.get("notes", ""))
    if not live and not src.get("hls") and not src.get("channelId"):
        add_dir("Visit %s" % (src.get("url") or SITE_URL), url_for(action="root"),
                art_for(src), src.get("notes", ""))
    xbmcplugin.endOfDirectory(HANDLE)


def play_youtube(video_id):
    """Hand playback to the official YouTube add-on — we never touch the stream."""
    path = "plugin://plugin.video.youtube/play/?video_id=%s" % video_id
    li = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def play_hls(url):
    li = xbmcgui.ListItem(path=url)
    li.setMimeType("application/x-mpegurl")
    li.setContentLookup(False)
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def run():
    args = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    action = args.get("action", "root")
    xbmcplugin.setContent(HANDLE, "videos")
    xbmcplugin.addSortMethod(HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    try:
        if action == "live":
            live_list()
        elif action == "calendar":
            calendar_list()
        elif action == "category":
            category_list(args.get("id", ""))
        elif action == "source":
            source_entry(args.get("id", ""))
        elif action == "play_yt":
            play_youtube(args.get("id", ""))
        elif action == "play_hls":
            play_hls(args.get("url", ""))
        else:
            root()
    except Exception as exc:  # noqa: BLE001 - surface the problem to the user
        log("error: %s" % exc)
        xbmcgui.Dialog().notification("Motorsport Hub",
                                      "Could not load the catalog",
                                      xbmcgui.NOTIFICATION_ERROR, 4000)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)


