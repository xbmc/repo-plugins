"""
SermonIndex for Kodi — entry point and router.

Kodi runs this file once per navigation step, with the chosen action in the
query string, and expects either a directory of items or a resolved playable
URL. There is no long-lived process and no state between steps.

    plugin://plugin.video.sermonindex/?action=speaker&slug=zac-poonen
"""

import os
import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

from resources.lib import api

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]

LETTERS = ["0-9"] + [chr(c) for c in range(ord("A"), ord("Z") + 1)]

# Our own menu art. Kodi's built-ins were the wrong words in the right places —
# Scripture drew DefaultGenre.png, which is a pair of THEATRE MASKS, and a
# sermon archive is the last place that belongs. These are four plain glyphs in
# the SermonIndex olive, so the menu reads as one thing rather than borrowed
# pieces of the skin.
MEDIA = os.path.join(ADDON.getAddonInfo("path"), "resources", "media")


def art(name):
    return os.path.join(MEDIA, "{}.png".format(name))


def tr(sid):
    return ADDON.getLocalizedString(sid)


def url(**kwargs):
    return "{}?{}".format(BASE_URL, urllib.parse.urlencode(kwargs))


def setting(key, default=None):
    try:
        val = ADDON.getSetting(key)
        return val if val not in (None, "") else default
    except Exception:
        return default


def bool_setting(key, default=True):
    try:
        return ADDON.getSettingBool(key)
    except Exception:
        return default


def page_size():
    try:
        return max(20, min(200, ADDON.getSettingInt("page_size")))
    except Exception:
        return 50


def notify(message):
    xbmcgui.Dialog().notification(ADDON.getAddonInfo("name"), message,
                                  xbmcgui.NOTIFICATION_INFO, 4000)


# ── Directory helpers ───────────────────────────────────────────────────────

def add_dir(label, target_url, art=None, plot=None):
    li = xbmcgui.ListItem(label=label)
    li.setArt(art or {"icon": "DefaultFolder.png"})
    if plot:
        _set_plot(li, label, plot)
    xbmcplugin.addDirectoryItem(HANDLE, target_url, li, isFolder=True)


def _set_plot(li, title, plot):
    """
    Kodi 20+ replaced ListItem.setInfo() with typed info tags, and setInfo is
    deprecated. Use the tag when it exists and fall back quietly when it does
    not, so this keeps working across the versions repo-plugins accepts.
    """
    try:
        tag = li.getVideoInfoTag()
        tag.setTitle(title)
        tag.setPlot(plot or "")
    except AttributeError:
        li.setInfo("video", {"title": title, "plot": plot or ""})


def sermon_item(sermon):
    """One playable sermon as a Kodi list item."""
    title = sermon.get("title") or "Untitled"
    speaker_name = sermon.get("speaker") or ""
    label = "{} — {}".format(speaker_name, title) if speaker_name else title

    li = xbmcgui.ListItem(label=label)
    art = sermon.get("thumbnailUrl") or sermon.get("image") or sermon.get("speakerImage")
    li.setArt({"thumb": art, "icon": art, "poster": art,
               "fanart": sermon.get("speakerImage") or art})

    plot_bits = [sermon.get("summary"), sermon.get("description")]
    plot = next((p for p in plot_bits if p), "")
    scripture = sermon.get("scripture")
    if scripture:
        plot = "{}\n\n{}".format(scripture if isinstance(scripture, str)
                                 else ", ".join(str(s) for s in scripture), plot).strip()

    try:
        tag = li.getVideoInfoTag()
        tag.setTitle(title)
        tag.setPlot(plot)
        tag.setDuration(api.duration_seconds(sermon))
        if speaker_name:
            tag.setArtists([speaker_name])
            tag.setStudios([speaker_name])
        genres = sermon.get("topics") or []
        if isinstance(genres, list) and genres:
            tag.setGenres([g if isinstance(g, str) else g.get("name", "") for g in genres][:6])
    except AttributeError:
        li.setInfo("video", {"title": title, "plot": plot,
                             "duration": api.duration_seconds(sermon),
                             "studio": speaker_name})

    li.setProperty("IsPlayable", "true")
    return li


def add_sermons(sermons, page, back_action):
    """
    Add a page of sermons, filtering out anything with no media.

    The filter happens BEFORE paging on purpose: page 2 should be the next 50
    playable sermons, not whatever survives from the next 50 rows.
    """
    items = [s for s in sermons if api.playable(s)]
    if not items:
        notify(tr(30009))
        xbmcplugin.endOfDirectory(HANDLE)
        return

    size = page_size()
    start = page * size
    chunk = items[start:start + size]

    for s in chunk:
        sid = s.get("id") or s.get("slug")
        xbmcplugin.addDirectoryItem(
            HANDLE, url(action="play", id=sid), sermon_item(s), isFolder=False)

    if start + size < len(items):
        nxt = dict(back_action)
        nxt["page"] = page + 1
        add_dir("{} ({}/{})".format(tr(30007), page + 2,
                                    (len(items) + size - 1) // size), url(**nxt))

    xbmcplugin.setContent(HANDLE, "videos")
    xbmcplugin.endOfDirectory(HANDLE)


# ── Screens ─────────────────────────────────────────────────────────────────

def root():
    for label, action, glyph in (
        (tr(30001), "letters", "speakers"),
        (tr(30002), "testaments", "scripture"),
        (tr(30003), "random", "random"),
        (tr(30004), "search", "search"),
    ):
        a = art(glyph)
        add_dir(label, url(action=action), {"icon": a, "thumb": a, "poster": a})
    xbmcplugin.endOfDirectory(HANDLE)


def letters():
    for letter in LETTERS:
        add_dir(letter, url(action="speakers", letter=letter),
                {"icon": art("speakers"), "thumb": art("speakers")})
    xbmcplugin.endOfDirectory(HANDLE)


def _letter_of(name):
    first = (name or "").strip()[:1].upper()
    return first if first.isalpha() else "0-9"


def speakers(letter, page=0):
    try:
        everyone = api.speakers()
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return

    matching = [s for s in everyone if _letter_of(s.get("name")) == letter]
    matching.sort(key=lambda s: (s.get("name") or "").lower())

    size = page_size()
    start = page * size
    for s in matching[start:start + size]:
        count = s.get("sermonCount") or 0
        add_dir("{}  ({})".format(s.get("name") or s.get("slug"), count),
                url(action="speaker", slug=s.get("slug")),
                {"icon": s.get("image") or art("speakers"),
                 "thumb": s.get("image") or art("speakers"),
                 "fanart": s.get("image")},
                plot=s.get("bio"))

    if start + size < len(matching):
        add_dir(tr(30007), url(action="speakers", letter=letter, page=page + 1))
    xbmcplugin.endOfDirectory(HANDLE)


def speaker(slug, page=0):
    try:
        data = api.speaker(slug)
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return
    add_sermons(data.get("sermons", []), page, {"action": "speaker", "slug": slug})


def testaments():
    a = art("scripture")
    add_dir(tr(30005), url(action="books", testament="OT"), {"icon": a, "thumb": a})
    add_dir(tr(30006), url(action="books", testament="NT"), {"icon": a, "thumb": a})
    xbmcplugin.endOfDirectory(HANDLE)


def books(testament):
    try:
        every = api.books()
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return
    for b in sorted([x for x in every if x.get("testament") == testament],
                    key=lambda x: x.get("order", 0)):
        if not b.get("sermonCount"):
            continue
        add_dir("{}  ({})".format(b.get("name"), b.get("sermonCount")),
                url(action="book", book=b.get("bookId")),
                {"icon": art("scripture"), "thumb": art("scripture")})
    xbmcplugin.endOfDirectory(HANDLE)


def book(book_id):
    try:
        data = api.book(book_id)
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return
    for ch in data.get("chaptersWithSermons", []):
        if not ch.get("sermonCount"):
            continue
        add_dir("{}  ({})".format(tr(30008).format(ch.get("chapter")), ch.get("sermonCount")),
                url(action="chapter", book=book_id, chapter=ch.get("chapter")),
                {"icon": art("scripture"), "thumb": art("scripture")})
    xbmcplugin.endOfDirectory(HANDLE)


def chapter(book_id, ch, page=0):
    try:
        data = api.chapter(book_id, ch)
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return
    sermons = data.get("sermons", []) if isinstance(data, dict) else data
    add_sermons(sermons, page, {"action": "chapter", "book": book_id, "chapter": ch})


def random_list(page=0):
    try:
        sermons = api.random_sermons()
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return
    add_sermons(sermons, page, {"action": "random"})


def search():
    """
    Speakers only, and that is a limit of the data rather than a choice.

    A sermon-title search would mean an index of all 64,227 titles; the only
    endpoint carrying them is /v2/sermons at 149 MB, which cannot be fetched on
    the kind of hardware this addon is for. A slim title index would fix it.
    """
    kb = xbmc.Keyboard("", tr(30004))
    kb.doModal()
    if not kb.isConfirmed():
        xbmcplugin.endOfDirectory(HANDLE)
        return
    needle = kb.getText().strip().lower()
    if not needle:
        xbmcplugin.endOfDirectory(HANDLE)
        return
    try:
        everyone = api.speakers()
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.endOfDirectory(HANDLE)
        return
    hits = [s for s in everyone if needle in (s.get("name") or "").lower()]
    hits.sort(key=lambda s: (s.get("name") or "").lower())
    for s in hits[:200]:
        add_dir("{}  ({})".format(s.get("name"), s.get("sermonCount") or 0),
                url(action="speaker", slug=s.get("slug")),
                {"icon": s.get("image"), "thumb": s.get("image")}, plot=s.get("bio"))
    if not hits:
        notify(tr(30009))
    xbmcplugin.endOfDirectory(HANDLE)


def play(sermon_id):
    try:
        sermon = api._get("sermons/{}".format(urllib.parse.quote(str(sermon_id))))
    except api.ApiError:
        notify(tr(30010))
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    stream, is_video = api.pick_media(
        sermon,
        source=setting("source", "archive"),
        prefer_video=bool_setting("prefer_video", True),
    )
    if not stream:
        notify(tr(30011))
        xbmcplugin.setResolvedUrl(HANDLE, False, xbmcgui.ListItem())
        return

    li = sermon_item(sermon)
    li.setPath(stream)
    if bool_setting("subtitles", True) and is_video:
        subs = api.subtitles(sermon)
        if subs:
            li.setSubtitles(subs)
    xbmcplugin.setResolvedUrl(HANDLE, True, li)


# ── Router ──────────────────────────────────────────────────────────────────

def run():
    args = dict(urllib.parse.parse_qsl(sys.argv[2][1:]))
    action = args.get("action")
    page = int(args.get("page", 0))

    if action is None:
        root()
    elif action == "letters":
        letters()
    elif action == "speakers":
        speakers(args.get("letter", "A"), page)
    elif action == "speaker":
        speaker(args.get("slug", ""), page)
    elif action == "testaments":
        testaments()
    elif action == "books":
        books(args.get("testament", "OT"))
    elif action == "book":
        book(args.get("book", ""))
    elif action == "chapter":
        chapter(args.get("book", ""), args.get("chapter", 1), page)
    elif action == "random":
        random_list(page)
    elif action == "search":
        search()
    elif action == "play":
        play(args.get("id", ""))
    else:
        root()


if __name__ == "__main__":
    run()
