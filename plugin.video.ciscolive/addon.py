"""
Cisco Live On-Demand - Kodi Video Plugin v2.0

Browse and stream Cisco Live on-demand sessions with a TV-optimized UX.
Features: in-category search, combined filters, watch history, smart sorting.
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources", "lib"))

try:
    from urllib.parse import parse_qsl, urlencode, quote_plus
except ImportError:
    from urlparse import parse_qsl
    from urllib import urlencode, quote_plus

import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmc
import xbmcvfs

from resources.lib import rainfocus
from resources.lib import brightcove
from resources.lib import history

ADDON = xbmcaddon.Addon()
ADDON_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
ADDON_ARGS = sys.argv[2]

# Settings helpers
def _setting_bool(key, default=False):
    try:
        return ADDON.getSettingBool(key)
    except Exception:
        return default

def _setting_int(key, default=0):
    try:
        return ADDON.getSettingInt(key)
    except Exception:
        return default

SHOW_NO_VIDEO = _setting_bool("show_no_video", False)
SHOW_CODES = _setting_bool("show_session_codes", False)


def build_url(action, **kwargs):
    params = {"action": action}
    params.update(kwargs)
    return "{}?{}".format(ADDON_URL, urlencode(params))


def get_params():
    return dict(parse_qsl(ADDON_ARGS.lstrip("?")))


# ---------------------------------------------------------------------------
# Level color badges
# ---------------------------------------------------------------------------

LEVEL_COLORS = {
    "Introductory": ("green", "[COLOR green]\u25cf[/COLOR]"),
    "Intermediate": ("yellow", "[COLOR yellow]\u25cf[/COLOR]"),
    "Advanced":     ("orange", "[COLOR orange]\u25cf[/COLOR]"),
    "Expert":       ("red",    "[COLOR red]\u25cf[/COLOR]"),
    "General":      ("white",  "[COLOR white]\u25cf[/COLOR]"),
}


def _level_badge(level):
    entry = LEVEL_COLORS.get(level)
    if entry:
        return "{} {}".format(entry[1], level)
    return level


# ---------------------------------------------------------------------------
# Main Menu (content-first)
# ---------------------------------------------------------------------------

def main_menu():
    xbmcplugin.setContent(ADDON_HANDLE, "videos")

    items = [
        ("New Releases",                  build_url("new_releases"),  "DefaultRecentlyAddedVideos.png"),
        ("Browse by Event",               build_url("events"),        "DefaultVideoPlaylists.png"),
        ("Browse by Category",            build_url("categories"),    "DefaultGenre.png"),
        ("Search All Sessions",           build_url("search"),        "DefaultAddonsSearch.png"),
        ("Continue Watching",             build_url("history"),       "DefaultRecentlyAddedVideos.png"),
        ("About",                         build_url("about"),         "DefaultAddonHelper.png"),
    ]
    for label, url, icon in items:
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon})
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# ---------------------------------------------------------------------------
# New Releases
# ---------------------------------------------------------------------------

def show_new_releases():
    show_session_list(filter_key="search.featuredsessions", filter_val="New_Releases")


# ---------------------------------------------------------------------------
# Browse by Event / Technology / Level / Session Type
# ---------------------------------------------------------------------------

def show_events():
    # Try dynamic discovery first, fall back to hardcoded
    events = rainfocus.discover_event_sections()
    if not events:
        events = rainfocus.get_events()

    for ev in events:
        name = ev["name"]
        total = ev.get("total", "")
        catalog = ev.get("catalog", "current")
        section_id = ev.get("section_id", "")
        label = "{} ({})".format(name, total) if total else name
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": "DefaultVideoPlaylists.png"})
        if section_id:
            # Current catalog: use section-based browsing
            url = build_url("event_section", section_id=section_id,
                             event_name=name, filter_label=name)
        else:
            # Legacy catalog: use text search + client-side filter
            url = build_url("list", search_text=name,
                             event_name=name, filter_label=name,
                             catalog="legacy")
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def show_technologies():
    for t in rainfocus.get_technologies():
        li = xbmcgui.ListItem(t["name"])
        li.setArt({"icon": "DefaultGenre.png"})
        url = build_url("list", filter_key="search.technology", filter_val=t["id"],
                         filter_label=t["name"])
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def show_event_section(section_id, event_name="", page=0,
                       tech_filter="", level_filter="", keyword=""):
    """Browse sessions from a specific event section (current catalog).
    
    tech_filter and level_filter can be comma-separated lists of IDs
    for multi-select filtering (e.g. "scpsSkillLevel_cadvanced,scpsSkillLevel_bintermediate").
    """
    xbmcplugin.setContent(ADDON_HANDLE, "videos")

    # Parse multi-value filters
    tech_ids = [t for t in tech_filter.split(",") if t]
    level_ids = [l for l in level_filter.split(",") if l]

    # Build common nav params for filter/pagination URLs
    nav_base = {"section_id": section_id, "event_name": event_name}
    if tech_filter:
        nav_base["tech_filter"] = tech_filter
    if level_filter:
        nav_base["level_filter"] = level_filter
    if keyword:
        nav_base["keyword"] = keyword

    # -- Sticky filter bar at top (page 0 only) --
    if page == 0:
        has_any_filter = bool(tech_ids or level_ids or keyword)

        # Active filter summary + clear option
        if has_any_filter:
            parts = []
            if tech_ids:
                tech_lookup = {t["id"]: t["name"] for t in rainfocus.get_technologies()}
                names = [tech_lookup.get(tid, tid) for tid in tech_ids]
                parts.append("Tech: " + ", ".join(names))
            if level_ids:
                level_lookup = {lv["id"]: lv["name"] for lv in rainfocus.get_levels()}
                names = [level_lookup.get(lid, lid) for lid in level_ids]
                parts.append("Level: " + ", ".join(names))
            if keyword:
                parts.append('"{}"'.format(keyword))

            clear_label = "[COLOR red]X  Clear filter: {}[/COLOR]".format(
                " + ".join(parts))
            li = xbmcgui.ListItem(clear_label)
            li.setArt({"icon": "DefaultIconError.png"})
            url = build_url("event_section", section_id=section_id,
                             event_name=event_name)
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

        # Technology filter (show current selection or "Filter by")
        tech_label = "[COLOR cyan]Filter by Technology[/COLOR]"
        if tech_ids:
            tech_lookup = {t["id"]: t["name"] for t in rainfocus.get_technologies()}
            names = [tech_lookup.get(tid, tid) for tid in tech_ids]
            tech_label = "[COLOR cyan]Technology: {} (change)[/COLOR]".format(
                ", ".join(names))
        li = xbmcgui.ListItem(tech_label)
        li.setArt({"icon": "DefaultGenre.png"})
        url = build_url("event_filter_pick", filter_type="technology",
                         **nav_base)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

        # Level filter
        level_label = "[COLOR cyan]Filter by Technical Level[/COLOR]"
        if level_ids:
            level_lookup = {lv["id"]: lv["name"] for lv in rainfocus.get_levels()}
            names = [level_lookup.get(lid, lid) for lid in level_ids]
            level_label = "[COLOR cyan]Level: {} (change)[/COLOR]".format(
                ", ".join(names))
        li = xbmcgui.ListItem(level_label)
        li.setArt({"icon": "DefaultProgram.png"})
        url = build_url("event_filter_pick", filter_type="level",
                         **nav_base)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

        # Keyword search
        kw_label = "[COLOR cyan]Search within this event[/COLOR]"
        if keyword:
            kw_label = '[COLOR cyan]Search: "{}" (change)[/COLOR]'.format(keyword)
        li = xbmcgui.ListItem(kw_label)
        li.setArt({"icon": "DefaultAddonsSearch.png"})
        url = build_url("event_keyword_search", **nav_base)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    # -- Build API filters (repeated keys for multi-value) --
    filters = {}
    if tech_ids:
        filters["search.technology"] = tech_ids
    if level_ids:
        filters["search.technicallevel"] = level_ids
    if keyword:
        filters["search"] = keyword

    result = rainfocus.search_event_sessions(
        section_id=section_id, page=page, page_size=rainfocus.PAGE_SIZE,
        event_name=event_name, filters=filters)
    items = result.get("items", [])
    total = result.get("total", 0)

    if not items and page == 0:
        xbmcgui.Dialog().notification(
            "Cisco Live", "No sessions found", xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return

    for item in items:
        _add_session_item(item)

    # Pagination
    next_offset = (page + 1) * rainfocus.PAGE_SIZE
    effective_total = min(total, rainfocus.MAX_RESULTS)
    if next_offset < effective_total:
        total_pages = (effective_total + rainfocus.PAGE_SIZE - 1) // rainfocus.PAGE_SIZE
        current_page = page + 1
        pg_label = "More sessions... (page {} of {})".format(
            current_page + 1, total_pages)
        li = xbmcgui.ListItem("[COLOR yellow]{}[/COLOR]".format(pg_label))
        li.setArt({"icon": "DefaultFolderBack.png"})
        pg_params = dict(nav_base)
        pg_params["page"] = str(page + 1)
        url = build_url("event_section", **pg_params)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
    xbmc.executebuiltin("Container.SetViewMode(500)")


def _event_filter_pick(filter_type, section_id, event_name,
                        tech_filter="", level_filter="", keyword=""):
    """Show a multiselect dialog to pick technology or level filters."""
    dialog = xbmcgui.Dialog()

    if filter_type == "technology":
        options = rainfocus.get_technologies()
        title = "Select Technologies (multi-select)"
        current_ids = [t for t in tech_filter.split(",") if t]
    elif filter_type == "level":
        options = rainfocus.get_levels()
        title = "Select Technical Levels (multi-select)"
        current_ids = [l for l in level_filter.split(",") if l]
    else:
        return

    names = [o["name"] for o in options]

    # Pre-select currently active filters
    preselect = []
    for i, o in enumerate(options):
        if o["id"] in current_ids:
            preselect.append(i)

    selected = dialog.multiselect(title, names, preselect=preselect)
    if selected is None:
        return  # Cancelled

    # Build new filter value (comma-separated IDs)
    new_ids = ",".join(options[i]["id"] for i in selected)

    if filter_type == "technology":
        tech_filter = new_ids
    elif filter_type == "level":
        level_filter = new_ids

    show_event_section(section_id=section_id, event_name=event_name,
                        page=0, tech_filter=tech_filter,
                        level_filter=level_filter, keyword=keyword)


def _event_keyword_search(section_id, event_name,
                           tech_filter="", level_filter="", keyword=""):
    """Prompt for a keyword search within an event."""
    kb = xbmc.Keyboard(keyword, "Search within {}".format(event_name or "event"))
    kb.doModal()
    if not kb.isConfirmed():
        return
    query = kb.getText().strip()

    show_event_section(section_id=section_id, event_name=event_name,
                        page=0, tech_filter=tech_filter,
                        level_filter=level_filter, keyword=query)


def show_levels():
    for lv in rainfocus.get_levels():
        li = xbmcgui.ListItem(_level_badge(lv["name"]))
        li.setArt({"icon": "DefaultProgram.png"})
        url = build_url("list", filter_key="search.technicallevel", filter_val=lv["id"],
                         filter_label=lv["name"])
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def show_session_types():
    for st in rainfocus.get_session_types():
        li = xbmcgui.ListItem(st["name"])
        li.setArt({"icon": "DefaultVideoPlaylists.png"})
        url = build_url("list", filter_key="search.sessiontype", filter_val=st["id"],
                         filter_label=st["name"])
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def show_categories():
    items = [
        ("Technology",      build_url("technologies"),  "DefaultGenre.png"),
        ("Technical Level", build_url("levels"),         "DefaultProgram.png"),
    ]
    for label, url, icon in items:
        li = xbmcgui.ListItem(label)
        li.setArt({"icon": icon})
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)


# ---------------------------------------------------------------------------
# Search (global + in-category)
# ---------------------------------------------------------------------------

def do_search(filter_key=None, filter_val=None, filter_label=None):
    """Search sessions. If filter params given, search within that category."""
    if filter_label:
        prompt = "Search within {}".format(filter_label)
    else:
        prompt = "Search Cisco Live Sessions"
    kb = xbmc.Keyboard("", prompt)
    kb.doModal()
    if not kb.isConfirmed():
        return
    query = kb.getText().strip()
    if not query:
        return
    show_session_list(search_text=query, filter_key=filter_key,
                      filter_val=filter_val, filter_label=filter_label)


# ---------------------------------------------------------------------------
# Refine filters (add filters on top of current)
# ---------------------------------------------------------------------------

def do_refine(filter_key=None, filter_val=None, filter_label=None,
              search_text=None):
    """Let user pick an additional filter to combine with current one."""
    dialog = xbmcgui.Dialog()

    # Build refine options based on what's NOT already filtered
    options = []
    option_data = []

    if filter_key != "search.event":
        options.append("Filter by Event")
        option_data.append(("event", rainfocus.get_events()))
    if filter_key != "search.technology":
        options.append("Filter by Technology")
        option_data.append(("tech", rainfocus.get_technologies()))
    if filter_key != "search.technicallevel":
        options.append("Filter by Technical Level")
        option_data.append(("level", rainfocus.get_levels()))
    if filter_key != "search.sessiontype":
        options.append("Filter by Session Type")
        option_data.append(("type", rainfocus.get_session_types()))

    if not options:
        dialog.notification("Cisco Live", "No additional filters available",
                            xbmcgui.NOTIFICATION_INFO)
        return

    choice = dialog.select("Refine: {}".format(filter_label or "Results"), options)
    if choice < 0:
        return

    kind, items = option_data[choice]

    # Show sub-choices
    names = [i["name"] for i in items]
    sub = dialog.select("Select", names)
    if sub < 0:
        return

    selected = items[sub]

    # Map kind to API filter key
    key_map = {
        "event": "search.event",
        "tech": "search.technology",
        "level": "search.technicallevel",
        "type": "search.sessiontype",
    }
    new_key = key_map[kind]
    new_val = selected["id"]
    new_label = selected["name"]

    # Build combined filter label
    combined_label = filter_label or ""
    if combined_label:
        combined_label = "{} + {}".format(combined_label, new_label)
    else:
        combined_label = new_label

    # Build combined filters as extra_filters string (key=val pairs)
    # We pass the original filter as filter_key/filter_val and new one as extra
    extra = "{}={}".format(new_key, new_val)

    show_session_list(filter_key=filter_key, filter_val=filter_val,
                      filter_label=combined_label, search_text=search_text,
                      extra_filters=extra)


# ---------------------------------------------------------------------------
# Sort dialog
# ---------------------------------------------------------------------------

SORT_OPTIONS = [
    ("Default", "default"),
    ("Title A-Z", "title_asc"),
    ("Title Z-A", "title_desc"),
    ("Shortest first", "duration_asc"),
    ("Longest first", "duration_desc"),
]

def do_sort(filter_key=None, filter_val=None, filter_label=None,
            search_text=None, extra_filters=None):
    """Show sort options and re-display list with chosen sort."""
    dialog = xbmcgui.Dialog()
    names = [s[0] for s in SORT_OPTIONS]
    choice = dialog.select("Sort by", names)
    if choice < 0:
        return
    sort_by = SORT_OPTIONS[choice][1]
    show_session_list(filter_key=filter_key, filter_val=filter_val,
                      filter_label=filter_label, search_text=search_text,
                      extra_filters=extra_filters, sort_by=sort_by)


# ---------------------------------------------------------------------------
# Session List (the core browsing view)
# ---------------------------------------------------------------------------

def show_session_list(page=0, filter_key=None, filter_val=None,
                      filter_label=None, search_text=None,
                      extra_filters=None, sort_by="default",
                      event_name=None, catalog=None):
    """List sessions with in-category search, refine, sort, and pagination."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")

    # Determine which API profile to use
    profile_id = None
    if catalog == "legacy":
        profile_id = rainfocus.LEGACY_PROFILE_ID
    elif catalog == "current":
        profile_id = rainfocus.CURRENT_PROFILE_ID

    # Build API filters
    filters = {}
    if filter_key and filter_val:
        filters[filter_key] = filter_val
    if search_text:
        filters["search"] = search_text
    if extra_filters:
        for pair in extra_filters.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                filters[k] = v

    # Common URL params for navigation items
    nav_params = {}
    if filter_key:
        nav_params["filter_key"] = filter_key
        nav_params["filter_val"] = filter_val
    if filter_label:
        nav_params["filter_label"] = filter_label
    if search_text:
        nav_params["search_text"] = search_text
    if extra_filters:
        nav_params["extra_filters"] = extra_filters
    if event_name:
        nav_params["event_name"] = event_name
    if catalog:
        nav_params["catalog"] = catalog

    # -- Top navigation items --

    # 1. Search within this category
    if filter_key or search_text:
        search_label = "Search within {}".format(
            filter_label or "these results")
        li = xbmcgui.ListItem(search_label)
        li.setArt({"icon": "DefaultAddonsSearch.png"})
        url = build_url("search_in", **nav_params)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    # 2. Refine (add more filters)
    if filter_key:
        refine_label = "Refine results..."
        li = xbmcgui.ListItem(refine_label)
        li.setArt({"icon": "DefaultAddonService.png"})
        url = build_url("refine", **nav_params)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    # 3. Sort
    current_sort = "Default"
    for name, key in SORT_OPTIONS:
        if key == sort_by:
            current_sort = name
            break
    sort_label = "Sort: {}".format(current_sort)
    li = xbmcgui.ListItem(sort_label)
    li.setArt({"icon": "DefaultIconInfo.png"})
    url = build_url("sort", **nav_params)
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    # -- Fetch sessions --
    result = rainfocus.search_sessions(
        page=page, page_size=rainfocus.PAGE_SIZE, filters=filters,
        profile_id=profile_id)
    items = result.get("items", [])
    total = result.get("total", 0)

    # Client-side event filtering (API doesn't support search.event)
    if event_name:
        items = [i for i in items if i.get("event") == event_name]

    if not items and page == 0:
        xbmcgui.Dialog().notification(
            "Cisco Live", "No sessions found", xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return

    # Client-side sort
    if sort_by == "title_asc":
        items.sort(key=lambda x: x.get("title", "").lower())
    elif sort_by == "title_desc":
        items.sort(key=lambda x: x.get("title", "").lower(), reverse=True)
    elif sort_by == "duration_asc":
        items.sort(key=lambda x: x.get("duration", 0))
    elif sort_by == "duration_desc":
        items.sort(key=lambda x: x.get("duration", 0), reverse=True)

    # Add session items
    for item in items:
        _add_session_item(item)

    # Pagination
    next_offset = (page + 1) * rainfocus.PAGE_SIZE
    effective_total = min(total, rainfocus.MAX_RESULTS)
    if next_offset < effective_total:
        total_pages = (effective_total + rainfocus.PAGE_SIZE - 1) // rainfocus.PAGE_SIZE
        current_page = page + 1
        pg_label = "\u25b6 More sessions... (page {} of {})".format(
            current_page + 1, total_pages)
        li = xbmcgui.ListItem("[COLOR yellow]{}[/COLOR]".format(pg_label))
        li.setArt({"icon": "DefaultFolderBack.png"})
        pg_params = dict(nav_params)
        pg_params["page"] = str(page + 1)
        if sort_by != "default":
            pg_params["sort_by"] = sort_by
        url = build_url("list", **pg_params)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
    # Set Wall view (500) as default for session lists
    xbmc.executebuiltin("Container.SetViewMode(500)")

def _add_session_item(item):
    """Add a single session to the directory listing."""
    title = item.get("title", "")
    code = item.get("code", "")
    has_video = item.get("has_video", False)

    # Skip no-video sessions unless setting enabled
    if not has_video and not SHOW_NO_VIDEO:
        return

    # Label: title only by default, or "CODE - Title" if setting enabled
    if SHOW_CODES and code:
        label = "{} - {}".format(code, title)
    else:
        label = title

    if not has_video:
        label = "[COLOR grey]{}[/COLOR]".format(label)

    li = xbmcgui.ListItem(label)

    # Build subtitle parts
    sub_parts = []
    if item.get("technologies"):
        sub_parts.append(item["technologies"][0])
    if item.get("level"):
        sub_parts.append(_level_badge(item["level"]))
    if item.get("duration") and item["duration"] > 0:
        mins = int(item["duration"] / 60)
        if mins >= 60:
            sub_parts.append("{}h {}m".format(mins // 60, mins % 60))
        else:
            sub_parts.append("{} min".format(mins))
    if sub_parts:
        li.setLabel2(" \u2022 ".join(sub_parts))

    # Build detailed plot
    speakers = ", ".join(s for s in item.get("speakers", []) if s)
    abstract = item.get("abstract", "")
    event = item.get("event", "")
    level = item.get("level", "")
    techs = ", ".join(item.get("technologies", []))
    stype = item.get("session_type", "")

    plot_parts = []
    if event:
        plot_parts.append("[B]Event:[/B] {}".format(event))
    if code:
        plot_parts.append("[B]Session:[/B] {}".format(code))
    if stype:
        plot_parts.append("[B]Type:[/B] {}".format(stype))
    if level:
        plot_parts.append("[B]Level:[/B] {}".format(level))
    if techs:
        plot_parts.append("[B]Technology:[/B] {}".format(techs))
    if speakers:
        plot_parts.append("[B]Speaker(s):[/B] {}".format(speakers))
    if not has_video:
        plot_parts.append("")
        plot_parts.append("[COLOR red]No video recording available[/COLOR]")
    if abstract:
        plot_parts.append("")
        plot_parts.append(abstract)

    info_tag = li.getVideoInfoTag()
    info_tag.setTitle(title)
    info_tag.setPlot("\n".join(plot_parts))
    if item.get("duration"):
        info_tag.setDuration(int(item["duration"]))
    if event:
        info_tag.setStudios([event])

    # Thumbnails
    photos = [p for p in item.get("speaker_photos", []) if p]
    if photos:
        li.setArt({"thumb": photos[0]})

    # Fanart
    fanart = os.path.join(
        ADDON.getAddonInfo("path"), "resources", "media", "fanart.jpg")
    if os.path.exists(fanart):
        li.setArt({"fanart": fanart})

    if has_video:
        li.setProperty("IsPlayable", "true")
        video_id = item["video_ids"][0]
        url = build_url("play", video_id=video_id,
                         session_id=item.get("id", ""),
                         title=title, code=code,
                         event=item.get("event", ""))
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)
    else:
        url = build_url("info", session_id=item.get("id", ""))
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)


# ---------------------------------------------------------------------------
# Playback
# ---------------------------------------------------------------------------

def play_video(video_id, title="", session_id="", code="", event=""):
    """Resolve and play a Brightcove video."""
    xbmc.log("CiscoLive: Resolving video {} (session={})".format(
        video_id, session_id), xbmc.LOGINFO)

    # Record in watch history
    history.add(session_id=session_id, title=title, video_id=video_id,
                code=code, event=event)

    # Resolve video stream via Brightcove
    try:
        stream_url, mime_type = brightcove.best_stream(video_id, prefer_hls=True)
    except Exception as e:
        xbmc.log("CiscoLive: Video resolution error: {}".format(e), xbmc.LOGERROR)
        stream_url, mime_type = None, None

    if not stream_url:
        xbmcgui.Dialog().notification(
            "Cisco Live",
            "Video unavailable. Check your network connection.",
            xbmcgui.NOTIFICATION_ERROR, 5000)
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())
        return

    li = xbmcgui.ListItem(path=stream_url)
    if "m3u8" in stream_url or "mpegurl" in (mime_type or "").lower():
        li.setMimeType("application/vnd.apple.mpegurl")
        li.setProperty("inputstream", "inputstream.adaptive")
        li.setProperty("inputstream.adaptive.manifest_type", "hls")
    elif "dash" in stream_url or "dash" in (mime_type or "").lower():
        li.setMimeType("application/dash+xml")
        li.setProperty("inputstream", "inputstream.adaptive")
        li.setProperty("inputstream.adaptive.manifest_type", "mpd")
    else:
        li.setMimeType(mime_type or "video/mp4")
    li.setContentLookup(False)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, li)


# ---------------------------------------------------------------------------
# Watch History
# ---------------------------------------------------------------------------

def show_history():
    """Show recently watched sessions."""
    xbmcplugin.setContent(ADDON_HANDLE, "videos")
    entries = history.get_recent(50)

    if not entries:
        xbmcgui.Dialog().notification(
            "Cisco Live", "No watch history yet", xbmcgui.NOTIFICATION_INFO)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        return

    # Clear history option at top
    li = xbmcgui.ListItem("[COLOR red]X  Clear watch history[/COLOR]")
    li.setArt({"icon": "DefaultIconError.png"})
    url = build_url("clear_history")
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=True)

    for entry in entries:
        title = entry.get("title", "Unknown")
        code = entry.get("code", "")
        event = entry.get("event", "")
        video_id = entry.get("video_id", "")

        if SHOW_CODES and code:
            label = "{} - {}".format(code, title)
        else:
            label = title

        li = xbmcgui.ListItem(label)
        if event:
            li.setLabel2(event)
        li.setProperty("IsPlayable", "true")

        info_tag = li.getVideoInfoTag()
        info_tag.setTitle(title)
        if event:
            info_tag.setPlot("[B]Event:[/B] {}\n[B]Session:[/B] {}".format(
                event, code))

        url = build_url("play", video_id=video_id,
                         session_id=entry.get("session_id", ""),
                         title=title, code=code, event=event)
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, isFolder=False)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)


def clear_history():
    if xbmcgui.Dialog().yesno("Cisco Live", "Clear all watch history?"):
        history.clear()
        xbmcgui.Dialog().notification(
            "Cisco Live", "History cleared", xbmcgui.NOTIFICATION_INFO)
    xbmc.executebuiltin("Container.Refresh")


# ---------------------------------------------------------------------------
# Session Info
# ---------------------------------------------------------------------------

def show_info(session_id):
    item = rainfocus.get_session(session_id)
    if not item:
        xbmcgui.Dialog().notification(
            "Cisco Live", "Session not found", xbmcgui.NOTIFICATION_WARNING)
        return
    lines = [
        "[B]{}[/B]".format(item.get("title", "")),
        "",
        "Event: {}".format(item.get("event", "N/A")),
        "Session: {}".format(item.get("code", "N/A")),
        "Type: {}".format(item.get("session_type", "N/A")),
        "Level: {}".format(item.get("level", "N/A")),
        "Speaker(s): {}".format(", ".join(item.get("speakers", [])) or "N/A"),
        "",
        item.get("abstract", "No description available."),
    ]
    xbmcgui.Dialog().textviewer(
        item.get("code", "Session Info"), "\n".join(lines))


# ---------------------------------------------------------------------------
# About
# ---------------------------------------------------------------------------

def show_about():
    """Show plugin information."""
    version = ADDON.getAddonInfo("version")
    lines = [
        "[B]Cisco Live On-Demand[/B]",
        "Version {}".format(version),
        "",
        "Browse and stream 14,000+ Cisco Live technical sessions",
        "from events spanning 2018-2026.",
        "",
        "All videos are freely accessible without authentication.",
        "",
        "[B]Features:[/B]",
        "• Browse by event, technology, and technical level",
        "• Search across all sessions",
        "• Multi-select filtering",
        "• Watch history tracking",
        "• Direct Brightcove streaming",
        "",
        "[B]Source:[/B]",
        "github.com/martap79/plugin.video.ciscolive",
        "",
        "[B]Website:[/B]",
        "ciscolive.com/on-demand",
    ]
    xbmcgui.Dialog().textviewer("About Cisco Live On-Demand", "\n".join(lines))


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

def router():
    params = get_params()
    action = params.get("action", "")

    if action == "":
        main_menu()
    elif action == "new_releases":
        show_new_releases()
    elif action == "events":
        show_events()
    elif action == "event_section":
        show_event_section(
            section_id=params.get("section_id", ""),
            event_name=params.get("event_name", ""),
            page=int(params.get("page", "0")),
            tech_filter=params.get("tech_filter", ""),
            level_filter=params.get("level_filter", ""),
            keyword=params.get("keyword", ""),
        )
    elif action == "event_filter_pick":
        _event_filter_pick(
            filter_type=params.get("filter_type", ""),
            section_id=params.get("section_id", ""),
            event_name=params.get("event_name", ""),
            tech_filter=params.get("tech_filter", ""),
            level_filter=params.get("level_filter", ""),
            keyword=params.get("keyword", ""),
        )
    elif action == "event_keyword_search":
        _event_keyword_search(
            section_id=params.get("section_id", ""),
            event_name=params.get("event_name", ""),
            tech_filter=params.get("tech_filter", ""),
            level_filter=params.get("level_filter", ""),
            keyword=params.get("keyword", ""),
        )
    elif action == "technologies":
        show_technologies()
    elif action == "levels":
        show_levels()
    elif action == "session_types":
        show_session_types()
    elif action == "categories":
        show_categories()
    elif action == "search":
        do_search()
    elif action == "search_in":
        do_search(filter_key=params.get("filter_key"),
                  filter_val=params.get("filter_val"),
                  filter_label=params.get("filter_label"))
    elif action == "refine":
        do_refine(filter_key=params.get("filter_key"),
                  filter_val=params.get("filter_val"),
                  filter_label=params.get("filter_label"),
                  search_text=params.get("search_text"))
    elif action == "sort":
        do_sort(filter_key=params.get("filter_key"),
                filter_val=params.get("filter_val"),
                filter_label=params.get("filter_label"),
                search_text=params.get("search_text"),
                extra_filters=params.get("extra_filters"))
    elif action == "about":
        show_about()
    elif action == "history":
        show_history()
    elif action == "clear_history":
        clear_history()
    elif action == "list":
        show_session_list(
            page=int(params.get("page", "0")),
            filter_key=params.get("filter_key"),
            filter_val=params.get("filter_val"),
            filter_label=params.get("filter_label"),
            search_text=params.get("search_text"),
            extra_filters=params.get("extra_filters"),
            sort_by=params.get("sort_by", "default"),
            event_name=params.get("event_name"),
            catalog=params.get("catalog"),
        )
    elif action == "play":
        play_video(
            params.get("video_id", ""),
            params.get("title", ""),
            params.get("session_id", ""),
            params.get("code", ""),
            params.get("event", ""),
        )
    elif action == "info":
        show_info(params.get("session_id", ""))
    else:
        main_menu()


if __name__ == "__main__":
    router()
