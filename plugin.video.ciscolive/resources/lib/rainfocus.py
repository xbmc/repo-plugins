"""
RainFocus API client for Cisco Live on-demand library.

Handles session catalog search, filtering, and detail fetching.
Uses the website widget ID (M7n14I8sz0pklW1vybwVRdKrgdREj8sR) which returns
the full 8,493-session catalog with proper pagination.

API limits:
- Max 50 items per page
- Max 500 items per search (paginationMax=500)
- Filtered searches (by event/tech/level) paginate within their result set
"""

import json
import time
import hashlib
import os

try:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urllib import urlencode

# Cache directory inside Kodi userdata
try:
    import xbmcaddon
    import xbmcvfs
    _ADDON = xbmcaddon.Addon()
    CACHE_DIR = os.path.join(
        xbmcvfs.translatePath(_ADDON.getAddonInfo("profile")), "cache"
    )
except Exception:
    CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")


API_URL = "https://events.rainfocus.com/api/{endpoint}"

# Two API profiles: legacy catalog (2018-2021) and current catalog (2022+)
LEGACY_PROFILE_ID = "Na3vqYdAlJFSxhYTYQGuMbpafMqftalz"
CURRENT_PROFILE_ID = "HEedDIRblcZk7Ld3KHm1T0VUtZog9eG9"
API_PROFILE_ID = CURRENT_PROFILE_ID  # default for new code

WIDGET_ID = "M7n14I8sz0pklW1vybwVRdKrgdREj8sR"
BRIGHTCOVE_ACCOUNT = "5647924234001"
BRIGHTCOVE_PLAYER = "SyK2FdqjM"

HEADERS = {
    "Origin": "https://ciscolive.cisco.com",
    "Referer": "https://www.ciscolive.com/on-demand/on-demand-library.html",
    "rfApiProfileId": API_PROFILE_ID,
    "rfWidgetId": WIDGET_ID,
    "Content-Type": "application/x-www-form-urlencoded",
}

# Pagination limits enforced by RainFocus
PAGE_SIZE = 50
MAX_RESULTS = 500  # paginationMax

# Cache TTL in seconds
CACHE_TTL = 21600  # 6 hours (content doesn't change frequently)

# Known events across both catalogs, sorted newest first
# Current catalog (CURRENT_PROFILE_ID) has 2022+ events
# Legacy catalog (LEGACY_PROFILE_ID) has 2018-2021 events
# Event "name" matches the item["event"] field from the API
EVENTS = [
    {"name": "2026 Amsterdam", "catalog": "current"},
    {"name": "2025 San Diego", "catalog": "current"},
    {"name": "2025 Melbourne", "catalog": "current"},
    {"name": "2025 Amsterdam", "catalog": "current"},
    {"name": "2024 Las Vegas", "catalog": "current"},
    {"name": "2024 Melbourne", "catalog": "current"},
    {"name": "2024 Amsterdam", "catalog": "current"},
    {"name": "2023 Las Vegas", "catalog": "current"},
    {"name": "2023 Melbourne", "catalog": "current"},
    {"name": "2023 Amsterdam", "catalog": "current"},
    {"name": "2022 Las Vegas", "catalog": "current"},
    {"name": "2022 Melbourne", "catalog": "current"},
    {"name": "Cisco Live 2021", "catalog": "legacy"},
    {"name": "Cisco Live US 2020", "catalog": "legacy"},
    {"name": "Cisco Live EMEA 2020", "catalog": "legacy"},
    {"name": "Cisco Live APJC 2020", "catalog": "legacy"},
    {"name": "Cisco Live US 2019", "catalog": "legacy"},
    {"name": "Cisco Live EMEA 2019", "catalog": "legacy"},
    {"name": "Cisco Live ANZ 2019", "catalog": "legacy"},
    {"name": "Cisco Live LATAM 2019", "catalog": "legacy"},
    {"name": "Cisco Live US 2018", "catalog": "legacy"},
    {"name": "Cisco Live EMEA 2018", "catalog": "legacy"},
    {"name": "Cisco Live ANZ 2018", "catalog": "legacy"},
    {"name": "Cisco Live LATAM 2018", "catalog": "legacy"},
]

# Known technology filter IDs
TECHNOLOGIES = [
    {"id": "scpsTechnology_5g", "name": "5G"},
    {"id": "scpsTechnology_analtics1", "name": "Analytics"},
    {"id": "scpsTechnology_analytics", "name": "Analytics & Automation"},
    {"id": "scpsTechnology_automation", "name": "Automation"},
    {"id": "scpsTechnology_cloud", "name": "Cloud"},
    {"id": "scpsTechnology_collaboration", "name": "Collaboration"},
    {"id": "scpsTechnology_dataCenter", "name": "Data Center"},
    {"id": "scpsTechnology_dataCenterManagement", "name": "Data Center Management"},
    {"id": "scpsTechnology_enterpriseArchitecture", "name": "Enterprise Architecture"},
    {"id": "scpsTechnology_enterprisenetworks", "name": "Enterprise Networks"},
    {"id": "scpsTechnology_internetofthingsiot", "name": "Internet of Things (IoT)"},
    {"id": "scpsTechnology_mobility", "name": "Mobility"},
    {"id": "scpsTechnology_nfv", "name": "NFV"},
    {"id": "scpsTechnology_networkManagement", "name": "Network Management"},
    {"id": "scpsTechnology_networkTransformation", "name": "Network Transformation"},
    {"id": "scpsTechnology_programmability", "name": "Programmability"},
    {"id": "scpsTechnology_routing", "name": "Routing"},
    {"id": "1555524473529007Qkew", "name": "SD-WAN"},
    {"id": "scpsTechnology_sdn", "name": "SDN"},
    {"id": "scpsTechnology_security", "name": "Security"},
    {"id": "scpsTechnology_serviceProvider", "name": "Service Provider"},
    {"id": "scpsTechnology_softwareDefinedNetworking", "name": "Software Defined Networking"},
    {"id": "scpsTechnology_softwareanalytics", "name": "Software and Analytics"},
    {"id": "scpsTechnology_storageNetworking", "name": "Storage Networking"},
    {"id": "scpsTechnology_videoContentDelivery", "name": "Video and Content Delivery"},
    {"id": "scpsTechnology_voiceUnifiedCommunication", "name": "Voice and Unified Communication"},
]

# Known technical levels
LEVELS = [
    {"id": "scpsSkillLevel_aintroductory", "name": "Introductory"},
    {"id": "scpsSkillLevel_bintermediate", "name": "Intermediate"},
    {"id": "scpsSkillLevel_cadvanced", "name": "Advanced"},
    {"id": "scpsSkillLevel_dgeneral", "name": "General"},
]

# Known session types
SESSION_TYPES = [
    {"id": "scpsSessionType_breakoutSession", "name": "Breakout Session"},
    {"id": "scpsSessionType_devnetSession", "name": "DevNet Session"},
    {"id": "scpsSessionType_instructorLed", "name": "Instructor-Led Lab"},
    {"id": "scpsSessionType_keynotes", "name": "Keynote"},
    {"id": "scpsSessionType_techSeminar", "name": "Technical Seminar"},
    {"id": "scpsSessionType_walkInSelfPaced", "name": "Walk-in Self-Paced Lab"},
]


def _cache_path(key):
    os.makedirs(CACHE_DIR, exist_ok=True)
    h = hashlib.md5(key.encode()).hexdigest()
    return os.path.join(CACHE_DIR, h + ".json")


def _cache_get(key):
    path = _cache_path(key)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if time.time() - data.get("_ts", 0) > CACHE_TTL:
            return None
        return data.get("payload")
    except Exception:
        return None


def _cache_set(key, payload):
    path = _cache_path(key)
    try:
        with open(path, "w") as f:
            json.dump({"_ts": time.time(), "payload": payload}, f)
    except Exception:
        pass


def _cached_fetch(cache_key, fetch_fn):
    """Check cache first, otherwise call fetch_fn(), cache the result, and return it."""
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    result = fetch_fn()
    if result is not None:
        _cache_set(cache_key, result)
    return result


def _api_post(endpoint, params, profile_id=None):
    """POST to RainFocus API and return parsed JSON.
    
    params values can be strings or lists. Lists produce repeated keys
    (e.g. {"search.technology": ["a", "b"]} -> "search.technology=a&search.technology=b").
    """
    url = API_URL.format(endpoint=endpoint)
    # Build body with support for repeated keys (list values)
    pairs = []
    for k, v in params.items():
        if isinstance(v, list):
            for item in v:
                pairs.append((k, item))
        else:
            pairs.append((k, v))
    body = urlencode(pairs).encode("utf-8")
    headers = dict(HEADERS)
    if profile_id:
        headers["rfApiProfileId"] = profile_id
    req = Request(url, data=body, headers=headers)
    try:
        resp = urlopen(req, timeout=30)
        return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError) as e:
        raise RuntimeError("RainFocus API error: {}".format(e))


def search_sessions(page=0, page_size=PAGE_SIZE, filters=None, profile_id=None):
    """
    Search the session catalog.

    Args:
        page: Page number (0-indexed)
        page_size: Results per page (max 50, enforced by API)
        filters: dict of search filters, e.g. {"search": "network"}
        profile_id: Override the API profile (for legacy vs current catalog)

    Returns:
        dict with keys: items (list), total (int), page, page_size
    """
    effective_size = min(page_size, PAGE_SIZE)
    offset = page * effective_size

    # API caps at 500 results
    if offset >= MAX_RESULTS:
        return {"items": [], "total": 0, "page": page, "page_size": effective_size}

    params = {
        "type": "session",
        "size": str(effective_size),
        "from": str(offset),
    }
    if filters:
        params.update(filters)

    cache_key = "search:{}:{}".format(profile_id or "default",
                                       json.dumps(params, sort_keys=True))
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _api_post("search", params, profile_id=profile_id)
    section = data.get("sectionList", [{}])[0] if data.get("sectionList") else {}
    items = section.get("items", [])
    total = section.get("total", 0)

    result = {
        "items": [_parse_item(i) for i in items],
        "total": total,
        "page": page,
        "page_size": effective_size,
    }
    _cache_set(cache_key, result)
    return result


def discover_event_sections():
    """
    Discover all events dynamically using sections=true.

    The current catalog returns events as sections when sections=true is passed.
    Each section represents one event (e.g. "2025 San Diego") with its own total.

    Returns:
        list of dicts with keys: name, section_id, total, catalog
    """
    cache_key = "event_sections"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    events = []

    # Current catalog (2022+) - requires sections=true
    try:
        data = _api_post("search", {
            "type": "session", "size": "1", "sections": "true"
        }, profile_id=CURRENT_PROFILE_ID)
        for s in data.get("sectionList", []):
            sid = s.get("sectionId", "")
            total = s.get("total", 0)
            items = s.get("items", [])
            name = items[0].get("event", "") if items else ""
            if name and sid != "otherItems":
                events.append({
                    "name": name,
                    "section_id": sid,
                    "total": total,
                    "catalog": "current",
                })
    except Exception:
        pass

    # Legacy catalog (2018-2021) - no sections, discover from items
    try:
        legacy_events = {}
        for offset in range(0, 500, 50):
            data = _api_post("search", {
                "type": "session", "size": "50", "from": str(offset)
            }, profile_id=LEGACY_PROFILE_ID)
            for s in data.get("sectionList", []):
                for item in s.get("items", []):
                    ev = item.get("event", "")
                    if ev and ev not in legacy_events:
                        legacy_events[ev] = 0
                    if ev:
                        legacy_events[ev] += 1
        for name, count in sorted(legacy_events.items(), reverse=True):
            events.append({
                "name": name,
                "section_id": "",
                "total": count,
                "catalog": "legacy",
            })
    except Exception:
        pass

    if events:
        _cache_set(cache_key, events)
    return events


def search_event_sessions(section_id, page=0, page_size=PAGE_SIZE,
                          event_name=None, filters=None):
    """
    Fetch sessions from a specific event section (current catalog).

    Uses sections=true with pagination. The API paginates within each section
    independently, so from/size apply per-section.

    Args:
        section_id: The sectionId from discover_event_sections()
        page: Page number (0-indexed)
        page_size: Results per page
        event_name: Event name for cache key / fallback filtering
        filters: Additional search filters

    Returns:
        dict with keys: items (list), total (int), page, page_size
    """
    effective_size = min(page_size, PAGE_SIZE)
    offset = page * effective_size

    if offset >= MAX_RESULTS:
        return {"items": [], "total": 0, "page": page, "page_size": effective_size}

    params = {
        "type": "session",
        "size": str(effective_size),
        "from": str(offset),
        "sections": "true",
    }
    if filters:
        params.update(filters)

    # Build a stable cache key (convert lists to sorted comma-joined strings)
    cache_params = {}
    for k, v in params.items():
        cache_params[k] = ",".join(sorted(v)) if isinstance(v, list) else v
    cache_key = "eventsec:{}:{}".format(section_id,
                                         json.dumps(cache_params, sort_keys=True))
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _api_post("search", params, profile_id=CURRENT_PROFILE_ID)

    # Find the matching section
    target_items = []
    target_total = 0
    for s in data.get("sectionList", []):
        if s.get("sectionId") == section_id:
            target_items = s.get("items", [])
            target_total = s.get("total", 0)
            break

    result = {
        "items": [_parse_item(i) for i in target_items],
        "total": target_total,
        "page": page,
        "page_size": effective_size,
    }
    _cache_set(cache_key, result)
    return result


def get_session(session_id):
    """Fetch a single session by its RainFocus ID."""
    cache_key = "session:" + session_id
    cached = _cache_get(cache_key)
    if cached:
        return cached

    data = _api_post("session", {"id": session_id})
    items = data.get("items", [])
    if not items:
        return None
    result = _parse_item(items[0])
    _cache_set(cache_key, result)
    return result


def get_events():
    """Return the list of known Cisco Live events."""
    return EVENTS


def get_technologies():
    """Return the list of technology filter categories."""
    return TECHNOLOGIES


def get_levels():
    """Return the list of technical level filters."""
    return LEVELS


def get_session_types():
    """Return the list of session type filters."""
    return SESSION_TYPES


def brightcove_url(video_id):
    """Build a Brightcove player URL for the given video ID."""
    return (
        "https://players.brightcove.net/{account}/{player}_default/"
        "index.html?videoId={vid}"
    ).format(account=BRIGHTCOVE_ACCOUNT, player=BRIGHTCOVE_PLAYER, vid=video_id)


def discover_events():
    """
    Try to discover events dynamically from API search results.
    Falls back to hardcoded EVENTS list if discovery fails.
    
    Returns:
        List of event dicts with id, name, sessions
    """
    try:
        # Do a search with no filters to get all events
        result = search_sessions(page=0, page_size=1, filters={})
        
        # Extract unique events from section headers
        events_found = []
        data = _api_post("search", {"type": "session", "size": "1", "from": "0"})
        
        for section in data.get("sectionList", []):
            heading = section.get("sectionHeading", "")
            if heading and heading not in [e["name"] for e in events_found]:
                # Try to infer an ID from the name
                event_id = heading.lower().replace(" ", "").replace("-", "")
                events_found.append({
                    "id": event_id,
                    "name": heading,
                    "sessions": section.get("total", 0)
                })
        
        if events_found:
            return events_found
    except Exception:
        pass
    
    # Fallback to hardcoded list
    return EVENTS


def _parse_item(item):
    """Extract the fields we care about from a raw RainFocus session item."""
    videos = item.get("videos", [])
    video_ids = [v["url"] for v in videos if v.get("url")]

    participants = item.get("participants", [])
    speakers = [p.get("fullName", p.get("globalFullName", "")) for p in participants]
    speaker_photos = [p.get("photoURL", p.get("globalPhotoURL", "")) for p in participants]

    # Get technology/level from attributevalues
    techs = []
    level = ""
    session_type = ""
    for av in item.get("attributevalues", []):
        attr = av.get("attribute", "")
        val = av.get("value", "")
        if attr == "Technology":
            techs.append(val)
        elif attr == "Technical Level":
            level = val
        elif attr in ("Session Type", "Type"):
            session_type = val

    duration = 0.0
    if item.get("times"):
        duration = float(item["times"][0].get("length", 0)) * 60  # minutes to seconds

    return {
        "id": item.get("sessionID", item.get("externalID", "")),
        "code": item.get("code", ""),
        "title": item.get("title", ""),
        "abstract": item.get("abstract", ""),
        "event": item.get("event", ""),
        "event_label": item.get("eventLabel", ""),
        "event_code": item.get("eventCode", ""),
        "speakers": speakers,
        "speaker_photos": speaker_photos,
        "technologies": techs,
        "level": level,
        "session_type": session_type or item.get("type", ""),
        "video_ids": video_ids,
        "duration": duration,
        "has_video": len(video_ids) > 0,
    }
