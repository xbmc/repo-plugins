"""A guide programme as the whole add-on sees it: URL param, age rating, type, artwork, colours.

Standard library only: the fast play path (quickplay) imports it.
"""

import re

from resources.lib.util import isotime

# Plugin URL form of a programme: "start~end~flags~age" (UTC times, content_flags,
# rating_age or empty), see from_param.
SEPARATOR = "~"


def param(p, known_age=True, then=None):
    """Return the plugin URL's value for a guide programme (also the XMLTV catchup-id).

    :param known_age: False: a missing rating is looked up in the guide at play time
    :param then: KODI_RESUME for a list item with Kodi's resume point (see kodi_resume)
    """
    flags = p.get("content_flags") if isinstance(p.get("content_flags"), list) else []
    age = rating_age(p.get("ratings"))
    parts = [p["start_time"], p["end_time"], ".".join(flags), ("" if known_age else "?") if age is None else str(age)]
    return SEPARATOR.join(parts + ([then] if then else []))


def bookmark_id(station, start, end):
    """Return the provider's bookmark id of a catch-up programme."""
    return "_".join((station, start, end))


def from_bookmark_id(mark_id):
    """Return (station, start, end) of a bookmark_id; None if it is not one (a film's, say)."""
    parts = (mark_id or "").split("_")
    return tuple(parts) if len(parts) == 3 else None


def rating_number(rating):
    """Return the number a rating says: "12+" 12, "18" and "18+" 18; None for none or "0-99" (all ages)."""
    m = re.match(r"^(\d+)\+?$", str(rating or "").strip())
    return int(m.group(1)) if m else None


def rating_age(rating):
    """Return the age a rating locks from: "12+" 12, "18" 18, "18+" 19 (adult), "0-99" 0; None: not rated."""
    rating = str(rating or "").strip()
    if rating == "18+":
        return 19
    if rating == "0-99":
        return 0
    return rating_number(rating)


def from_param(param):
    """Return {"start", "end", "flags", "age"} of a programme param (see param); None if it is not one.

    Without an age (3 parts or "?") "age" is missing and the lock looks it up in the guide.
    A fifth part sets "resume" (see kodi_resume) or "continue".
    """
    parts = (param or "").split(SEPARATOR)
    if len(parts) not in (3, 4, 5):
        return None
    try:
        end = isotime.stamp(parts[1])
        isotime.stamp(parts[0])
    except ValueError:
        return None
    out = {"start": parts[0], "end": end, "flags": set(filter(None, parts[2].split(".")))}
    if len(parts) >= 4 and parts[3] != "?":
        out["age"] = int(parts[3]) if parts[3].isdigit() else None
    if len(parts) == 5 and parts[4] in (RESUME, FROM_START):
        out["resume"] = parts[4] == RESUME
    elif len(parts) == 5 and parts[4] == CONTINUE:
        out["continue"] = True
    return out


# Ends a param of a list item with Kodi's resume point: Kodi asks and passes the answer in argv[3].
KODI_RESUME = "kodi"
RESUME = "resume"
FROM_START = "start"
# Resume without asking (an airing from a favourite's list); the add-on seeks itself.
CONTINUE = "continue"


def resumed(param):
    """Return the programme param that resumes where it was left off."""
    return _with_tail(param, RESUME)


def continued(param):
    """Return the programme param that resumes without asking (see CONTINUE)."""
    return _with_tail(param, CONTINUE)


def from_beginning(param):
    """Return the programme param that plays from the beginning without asking."""
    return _with_tail(param, FROM_START)


def _with_tail(param, tail):
    parts = param.split(SEPARATOR)
    if len(parts) == 3:
        parts.append("?")  # age unknown
    return SEPARATOR.join(parts[:4] + [tail])


def kodi_resume(param, argv):
    """Return the programme param with Kodi's answer in place of KODI_RESUME (others unchanged)."""
    head, sep, tail = (param or "").rpartition(SEPARATOR)
    if not sep or tail != KODI_RESUME:
        return param
    answer = argv[3] if len(argv) > 3 else ""
    return head + sep + (RESUME if answer == "resume:true" else FROM_START)


# The guide data rarely carries an image itself.
PROGRAM_IMAGE = "https://ottapp-akamai-client-a.proda.dtp.tv3cloud.com/images/images/program/%s/16x9/keyartmedium.jpg"
# By kind ("program"/"series"), id and shape: 2:3 poster (310x465) and 16:9 (711x400, sharper
# than the guide's 426x240). Every item of a sampled block had both (2026-10-30).
ARTWORK = "https://ottapp-akamai-client-a.proda.dtp.tv3cloud.com/images/images/%s/%s/%s/keyartxlarge.jpg"
# Guide flags shown as tags: flag -> string id.
ACCESS_TAGS = {"has_audio_description": 30214, "has_sign_language": 30215}


# Provider categories -> DVB content types (ETSI EN 300 468, table 29): Kodi colours the
# guide by type while showing the provider's text.
DVB_GENRES = {
    # 0x1_ movie / drama
    "Dráma": 0x10,
    "Sorozatok": 0x10,
    "Családi": 0x10,
    "Rövidfilm": 0x10,
    "Krimi": 0x11,
    "Thriller": 0x11,
    "Kaland": 0x12,
    "Akció": 0x12,
    "Háborús": 0x12,
    "Western": 0x12,
    "Katasztrófafilm": 0x12,
    "Sci-fi": 0x13,
    "Fantasy": 0x13,
    "Horror": 0x13,
    "Misztikus": 0x13,
    "Vígjáték": 0x14,
    "Szappanopera": 0x15,
    "Romantikus": 0x16,
    "Történelmi": 0x17,
    "Életrajzi": 0x17,
    "Felnőtt": 0x18,
    # 0x2_ news / current affairs
    "Hír- és politikai műsorok": 0x20,
    "Magazin műsorok": 0x22,
    "Dokumentum": 0x23,
    # 0x3_ show
    "Szórakoztató": 0x30,
    "Valóságshow": 0x30,
    "Stand-up comedy": 0x32,
    "Talk-show": 0x33,
    # 0x4_ sports
    "Sport": 0x40,
    "Golf": 0x40,
    "Labdarúgás": 0x43,
    "Futsal": 0x43,
    "Tenisz": 0x44,
    "Kézilabda": 0x45,
    "Kosárlabda": 0x45,
    "Röplabda": 0x45,
    "Baseball": 0x45,
    "Jégkorong": 0x45,
    "Atlétika": 0x46,
    "Torna, gimnasztika": 0x46,
    "Autó-motor sport": 0x47,
    "Vízilabda": 0x48,
    "Télisport": 0x49,
    "Lovassport": 0x4A,
    "Küzdősport": 0x4B,
    # 0x5_ children
    "Animáció": 0x55,
    "Bábfilm": 0x55,
    # 0x6_ music
    "Zene": 0x60,
    "Musical": 0x65,
    # 0x7_ arts / culture
    "Kultúra, színház": 0x71,
    "Vallás": 0x73,
    # 0x9_ education / science
    "Ismeretterjesztő": 0x90,
    "Természetfilm": 0x91,
    # 0xA_ leisure
    "Életmód": 0xA0,
    "Fitnesz": 0xA4,
    "Gasztronómia": 0xA5,
    "Reklám": 0xA6,
    # Channel-only categories, for programmes without a known one (Közszolgálati,
    # Helyi TV and Rádió are mixed, so absent).
    "Filmek, sorozatok": 0x10,
    "Hírek": 0x20,
    "Gyerekeknek": 0x50,
    "Közösségi": 0x80,
    "Idegennyelvű": 0xB0,
}
# Estuary's guide colours per DVB content type.
DVB_COLOURS = {
    0x10: "FFDB7817",  # movie / drama
    0x20: "FF649A64",  # news
    0x30: "FFDBD917",  # show
    0x40: "FFED0E28",  # sports
    0x50: "FF17DBC2",  # children
    0x60: "FF41EA4D",  # music
    0x70: "FF0043EC",  # arts / culture
    0x80: "FFC6C8CB",  # social / political
    0x90: "FF9E209E",  # education / science
    0xA0: "FF9393CF",  # leisure
    0xB0: "FF1DA1B1",  # special
}


def channel_colour(channel):
    """Return the guide colour of a channel's first category that has one, or None (mixed content)."""
    for genre in channel.get("genres") or []:
        if genre in DVB_GENRES:
            return DVB_COLOURS.get(DVB_GENRES[genre] & 0xF0)
    return None


SERIES_GENRES = {"Sorozatok", "Szappanopera"}


def kind(p):
    """Return "movie", "series" or "other" (news, magazines, sport...).

    By category, not series id: news and magazines have one too.
    """
    if p.get("show_type") == "Movie":
        return "movie"
    names = {g.get("name") for g in p.get("genres") or []}
    return "series" if names & SERIES_GENRES else "other"


def watchable_back(p):
    """Return whether a guide programme is in the archive ("ct" flag)."""
    return "ct" in (p.get("content_flags") if isinstance(p.get("content_flags"), list) else [])


def image(p):
    """Return a guide programme's picture URL; None without one."""
    image = p.get("image") or p.get("poster_image_url")
    if not image and p.get("program_id"):
        image = PROGRAM_IMAGE % p["program_id"].lower()
    return image or None


def poster(kind, item_id):
    """Return the 2:3 poster of a programme or series (see ARTWORK); None without an id."""
    return ARTWORK % (kind, item_id.lower(), "2x3") if item_id else None


def fanart(p):
    """Return a programme's background picture: the sharper one by its id, else its guide picture."""
    return ARTWORK % ("program", p["program_id"].lower(), "16x9") if p.get("program_id") else image(p)


def duration(start, end):
    """Return the seconds between two ISO times; None if either is missing or not one."""
    try:
        seconds = int(isotime.stamp(end) - isotime.stamp(start))
    except (AttributeError, TypeError, ValueError):
        return None
    return seconds if seconds > 0 else None


def access_tags(p):
    """Return the string ids of a programme's accessibility flags (see ACCESS_TAGS)."""
    return [string for flag, string in ACCESS_TAGS.items() if p.get(flag)]


def details(p):
    """Return what Kodi shows of a guide programme (see resolveditem.list_item).

    A resolved item replaces Kodi's guide entry, so it must carry everything shown.
    """
    details = {
        "title": p.get("description") or "",
        "episode": p.get("episode_name") or "",
        "plot": (p.get("full_description") or "").strip(),
        "genres": [g["name"] for g in p.get("genres") or [] if g.get("name")],
        "type": kind(p),
        "image": image(p),
    }
    made, numbers = played_year(p), season_episode(p)
    if made:
        details["year"] = made
    if numbers:
        details["season"], details["number"] = numbers
    return details


def media_type(kind, episodic):
    """Return Kodi's media type: "episode" wherever there are episode details.

    Kodi shows "season x episode: title" only for episodes, and cartoons and magazines have them too.
    """
    return "episode" if episodic or kind == "series" else {"movie": "movie"}.get(kind, "video")


def year(p):
    """Return a programme's production year; None without a valid one."""
    year = str(p.get("release_year") or "")
    return int(year) if year.isdigit() and len(year) == 4 else None


def played_year(p):
    """Return the year to give a programme being played: a movie's or a numbered episode's; else None.

    Trakt and Simkl take a played item with a year but no season and episode for a movie
    (a news programme with its year would be "Híradó (2026)").
    """
    return year(p) if kind(p) == "movie" or season_episode(p) else None


def season_episode(p):
    """Return a programme's (season, episode), both from 1; None without both."""
    try:
        season, episode = int(p.get("season_number") or 0), int(p.get("episode_number") or 0)
    except ValueError:
        return None
    return (season, episode) if season and episode else None
