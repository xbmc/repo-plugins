# -*- coding: utf-8 -*-
"""Kodi user interface of TVS Player: menus, dialogs, playback."""
import time

try:
    from urllib.parse import urlencode, parse_qsl, urlparse
except ImportError:  # pragma: no cover
    from urllib import urlencode
    from urlparse import parse_qsl, urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from . import m3u, net, radiobrowser
from .store import Store, KIND_FILE, KIND_RADIO, KIND_URL

ADDON = xbmcaddon.Addon()
ADDON_NAME = ADDON.getAddonInfo("name")
ICON = ADDON.getAddonInfo("icon")
FANART = ADDON.getAddonInfo("fanart")

# Kodi language → country of the free radio stations proposed at first start
_LANGUAGE_COUNTRY = {"it": "IT", "de": "DE", "fr": "FR", "es": "ES", "pt": "PT", "nl": "NL", "pl": "PL",
                     "ru": "RU", "tr": "TR", "en": "US", "el": "GR", "ro": "RO", "hu": "HU", "cs": "CZ",
                     "sv": "SE", "da": "DK", "fi": "FI", "nb": "NO", "uk": "UA", "ar": "EG", "hi": "IN"}


def _(string_id):
    return ADDON.getLocalizedString(string_id)


def _translate_path(path):
    translate = getattr(xbmcvfs, "translatePath", None) or xbmc.translatePath
    return translate(path)


def _notify(message, error=False):
    icon = xbmcgui.NOTIFICATION_ERROR if error else ICON
    xbmcgui.Dialog().notification(ADDON_NAME, message, icon, 4000)


def _link_label(index, url):
    host = urlparse(url.split("|")[0]).hostname or ""
    return _(30024).format(index + 1) + (" · " + host if host else "")


def _set_info(item, title, stream_type, plot=""):
    """Title/plot for Kodi 20+ (InfoTag API) and Kodi 19 (setInfo)."""
    if stream_type == m3u.RADIO:
        if hasattr(item, "getMusicInfoTag"):
            tag = item.getMusicInfoTag()
            tag.setTitle(title)
            tag.setComment(plot)
        else:
            item.setInfo("music", {"title": title, "comment": plot})
    else:
        if hasattr(item, "getVideoInfoTag"):
            tag = item.getVideoInfoTag()
            tag.setTitle(title)
            tag.setPlot(plot)
            tag.setMediaType("video")
        else:
            item.setInfo("video", {"title": title, "plot": plot, "mediatype": "video"})


class Plugin(object):

    def __init__(self, argv):
        self.base = argv[0]
        self.handle = int(argv[1]) if len(argv) > 1 else -1
        query = argv[2][1:] if len(argv) > 2 and argv[2].startswith("?") else ""
        self.params = dict(parse_qsl(query))
        self.store = Store(_translate_path(ADDON.getAddonInfo("profile")))

    def url(self, **params):
        return self.base + "?" + urlencode(params)

    def run(self):
        action = self.params.get("action", "root")
        getattr(self, "do_" + action, self.do_root)()

    # ── helpers ──────────────────────────────────────────────────────────
    def _folder(self, label, icon, **params):
        item = xbmcgui.ListItem(label=label)
        item.setArt({"icon": icon, "thumb": icon, "fanart": FANART})
        xbmcplugin.addDirectoryItem(self.handle, self.url(**params), item, isFolder=True)

    def _end(self, content="", cache=False):
        if content:
            xbmcplugin.setContent(self.handle, content)
        xbmcplugin.endOfDirectory(self.handle, cacheToDisc=cache)

    def _end_action(self):
        """Dialog-only actions opened from a folder entry: stay in the current list and refresh it."""
        if self.handle >= 0:
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
        xbmc.executebuiltin("Container.Refresh")

    def _channel_item(self, channel):
        stream_type = channel["type"]
        links = len(channel["links"])
        item = xbmcgui.ListItem(label=channel["name"], label2=(_(30038).format(links) if links > 1 else ""))
        logo = channel["logo"] or ("DefaultMusicSongs.png" if stream_type == m3u.RADIO else "DefaultTVShows.png")
        item.setArt({"icon": logo, "thumb": logo, "fanart": FANART})
        _set_info(item, channel["name"], stream_type, channel["group"])
        item.setProperty("IsPlayable", "true")
        key = {"type": stream_type, "group": channel["group"], "name": channel["name"]}
        item.addContextMenuItems([
            (_(30023), "RunPlugin(%s)" % self.url(action="links", **key)),
            (_(30021), "RunPlugin(%s)" % self.url(action="fav_add", **key)),
        ])
        xbmcplugin.addDirectoryItem(self.handle, self.url(action="play", **key), item, isFolder=False)

    # ── main menu ────────────────────────────────────────────────────────
    def do_root(self):
        self._first_start()
        self._folder(_(30000), "DefaultTVShows.png", action="groups", type=m3u.TV)
        self._folder(_(30001), "DefaultMusicSongs.png", action="groups", type=m3u.RADIO)
        self._folder(_(30002), "DefaultFavourites.png", action="favorites")
        self._folder(_(30004), "DefaultAddonsSearch.png", action="search")
        self._folder(_(30003), "DefaultPlaylist.png", action="playlists")
        self._end()

    def _first_start(self):
        """First start: the add-on provides no channels, so offer the free radio stations."""
        try:
            done = ADDON.getSettingBool("first_run_done")
        except Exception:
            done = ADDON.getSetting("first_run_done") == "true"
        if done or self.store.playlists():
            return
        ADDON.setSetting("first_run_done", "true")
        if xbmcgui.Dialog().yesno(ADDON_NAME, _(30028) + "\n\n" + _(30029)):
            self._add_radio_stations()

    # ── TV / Radio ───────────────────────────────────────────────────────
    def do_groups(self):
        stream_type = self.params.get("type", m3u.TV)
        groups = self.store.groups(stream_type)
        if not groups:
            self._folder(_(30026), "DefaultPlaylist.png", action="playlists")
            return self._end()
        total = sum(n for _g, n in groups)
        self._folder("%s (%d)" % (_(30005), total), "DefaultFolder.png", action="channels", type=stream_type, group="")
        for group, count in groups:
            self._folder("%s (%d)" % (group, count), "DefaultFolder.png",
                         action="channels", type=stream_type, group=group)
        self._end()

    def do_channels(self):
        stream_type = self.params.get("type", m3u.TV)
        group = self.params.get("group") or None
        for channel in self.store.channels(stream_type, group):
            self._channel_item(channel)
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_UNSORTED)
        xbmcplugin.addSortMethod(self.handle, xbmcplugin.SORT_METHOD_LABEL)
        self._end("songs" if stream_type == m3u.RADIO else "videos")

    # ── playback ─────────────────────────────────────────────────────────
    def _find_channel(self):
        return self.store.channel(self.params.get("type", m3u.TV), self.params.get("group", ""),
                                  self.params.get("name", ""))

    def _first_working_link(self, links):
        """Skips dead links (automatic fallback). One link, or checks disabled: no check."""
        try:
            check = ADDON.getSettingBool("probe_links")
            timeout = ADDON.getSettingInt("probe_timeout")
        except Exception:
            check, timeout = True, 4
        if not check or len(links) == 1:
            return links[0]
        for url in links:
            if net.is_reachable(url, timeout=timeout):
                return url
        # None answered in time (slow live streams): let Kodi try the first one anyway
        return links[0]

    def do_play(self):
        channel = self._find_channel()
        url = self._first_working_link(channel["links"]) if channel and channel["links"] else None
        if not url:
            _notify(_(30025), error=True)
            xbmcplugin.setResolvedUrl(self.handle, False, xbmcgui.ListItem())
            return
        item = xbmcgui.ListItem(path=url)
        _set_info(item, channel["name"], channel["type"], channel["group"])
        item.setArt({"thumb": channel["logo"] or ICON})
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def do_play_url(self):
        item = xbmcgui.ListItem(path=self.params["url"])
        _set_info(item, self.params.get("name", ""), self.params.get("type", m3u.TV))
        xbmcplugin.setResolvedUrl(self.handle, True, item)

    def do_links(self):
        channel = self._find_channel()
        if not channel:
            return
        links = channel["links"]
        index = xbmcgui.Dialog().select(channel["name"], [_link_label(i, u) for i, u in enumerate(links)])
        if index < 0:
            return
        item = xbmcgui.ListItem(label=channel["name"], path=links[index])
        _set_info(item, channel["name"], channel["type"], channel["group"])
        item.setArt({"thumb": channel["logo"] or ICON})
        xbmc.Player().play(links[index], item)

    # ── favorites ────────────────────────────────────────────────────────
    def do_fav_add(self):
        channel = self._find_channel()
        if not channel:
            return
        links = channel["links"]
        index = 0
        if len(links) > 1:
            index = xbmcgui.Dialog().select(_(30036), [_link_label(i, u) for i, u in enumerate(links)])
            if index < 0:
                return
        self.store.add_favorite({"name": channel["name"], "logo": channel["logo"], "group": channel["group"],
                                 "url": links[index], "type": channel["type"]})
        _notify(_(30031))

    def do_favorites(self):
        for fav in self.store.favorites():
            item = xbmcgui.ListItem(label=fav["name"], label2=fav["group"])
            logo = fav["logo"] or ("DefaultMusicSongs.png" if fav["type"] == m3u.RADIO else "DefaultTVShows.png")
            item.setArt({"icon": logo, "thumb": logo, "fanart": FANART})
            _set_info(item, fav["name"], fav["type"], fav["group"])
            item.setProperty("IsPlayable", "true")
            item.addContextMenuItems([
                (_(30032), "RunPlugin(%s)" % self.url(action="fav_move", url=fav["url"], offset="-1")),
                (_(30033), "RunPlugin(%s)" % self.url(action="fav_move", url=fav["url"], offset="1")),
                (_(30022), "RunPlugin(%s)" % self.url(action="fav_remove", url=fav["url"])),
            ])
            xbmcplugin.addDirectoryItem(
                self.handle, self.url(action="play_url", url=fav["url"], name=fav["name"], type=fav["type"]),
                item, isFolder=False)
        self._end("videos")

    def do_fav_remove(self):
        self.store.remove_favorite(self.params.get("url", ""))
        xbmc.executebuiltin("Container.Refresh")

    def do_fav_move(self):
        self.store.move_favorite(self.params.get("url", ""), int(self.params.get("offset", "0")))
        xbmc.executebuiltin("Container.Refresh")

    # ── search ───────────────────────────────────────────────────────────
    def do_search(self):
        query = self.params.get("q")
        if query is None:
            query = xbmcgui.Dialog().input(_(30034))
            if not query:
                return self._end_action()
            # Re-open with the query in the address, so going back does not ask again
            xbmcplugin.endOfDirectory(self.handle, succeeded=False)
            xbmc.executebuiltin("Container.Update(%s,replace)" % self.url(action="search", q=query))
            return
        for stream_type in (m3u.TV, m3u.RADIO):
            for channel in self.store.channels(stream_type, query=query):
                self._channel_item(channel)
        self._end("videos")

    # ── playlists ────────────────────────────────────────────────────────
    def do_playlists(self):
        for p in self.store.playlists():
            updated = time.strftime("%Y-%m-%d %H:%M", time.localtime(p["updated"])) if p["updated"] else _(30035)
            item = xbmcgui.ListItem(label=p["name"], label2=_(30030).format(p["count"], updated))
            item.setArt({"icon": "DefaultPlaylist.png", "thumb": "DefaultPlaylist.png", "fanart": FANART})
            item.addContextMenuItems([
                (_(30018), "RunPlugin(%s)" % self.url(action="pl_refresh", id=p["id"])),
                (_(30019), "RunPlugin(%s)" % self.url(action="pl_delete", id=p["id"])),
            ])
            xbmcplugin.addDirectoryItem(self.handle, self.url(action="playlist", id=p["id"]), item, isFolder=True)
        self._folder("[B]+ %s[/B]" % _(30006), "DefaultAddSource.png", action="pl_add_url")
        self._folder("[B]+ %s[/B]" % _(30007), "DefaultAddSource.png", action="pl_add_file")
        self._folder("[B]+ %s[/B]" % _(30008), "DefaultAddSource.png", action="pl_add_radio")
        self._end()

    def do_playlist(self):
        """One playlist: its menu (refresh / delete)."""
        p = self.store.playlist(self.params.get("id", ""))
        if not p:
            return self._end()
        self._folder(_(30018), "DefaultAddonsUpdates.png", action="pl_refresh", id=p["id"])
        self._folder(_(30019), "DefaultIconError.png", action="pl_delete", id=p["id"])
        self._end()

    def _load(self, playlist):
        """Downloads/reads the playlist, stores its channels. Returns the number of channels."""
        if playlist["kind"] == KIND_RADIO:
            try:
                limit = ADDON.getSettingInt("radio_limit")
            except Exception:
                limit = 500
            entries = radiobrowser.stations(radiobrowser.country_of(playlist["source"]), limit)
        else:
            if playlist["kind"] == KIND_FILE:
                f = xbmcvfs.File(playlist["source"])
                try:
                    text = bytes(f.readBytes())   # raw bytes: decoded below like downloads
                finally:
                    f.close()
                text = net.decode_text(text)
            else:
                text = net.get_text(playlist["source"])
            entries = m3u.parse(text, playlist["name"], playlist["type_mode"])
        if not entries:
            raise ValueError(_(30039))
        self.store.save_entries(playlist["id"], entries)
        return len(entries)

    def _load_with_progress(self, playlist, delete_on_error=False):
        progress = xbmcgui.DialogProgressBG()
        progress.create(ADDON_NAME, _(30015))
        try:
            count = self._load(playlist)
            _notify(_(30016).format(count, playlist["name"]))
            return True
        except Exception as e:
            if delete_on_error:
                self.store.delete_playlist(playlist["id"])
            xbmcgui.Dialog().ok(_(30017), "%s\n%s" % (playlist["name"], e))
            return False
        finally:
            progress.close()

    def _ask_type(self):
        index = xbmcgui.Dialog().select(_(30011), [_(30012), _(30013), _(30014)])
        return [m3u.TYPE_AUTO, m3u.TYPE_TV, m3u.TYPE_RADIO][max(index, 0)] if index >= 0 else None

    def do_pl_add_url(self):
        url = xbmcgui.Dialog().input(_(30009), "http://")
        if url and url.lower().startswith(("http://", "https://")) and len(url) > 10:
            name = xbmcgui.Dialog().input(_(30010), urlparse(url).hostname or "Playlist")
            type_mode = self._ask_type() if name else None
            if name and type_mode:
                playlist = self.store.add_playlist(name, url, KIND_URL, type_mode)
                self._load_with_progress(playlist, delete_on_error=True)
        elif url:
            xbmcgui.Dialog().ok(ADDON_NAME, _(30040))
        self._end_action()

    def do_pl_add_file(self):
        path = xbmcgui.Dialog().browseSingle(1, _(30007), "files", ".m3u|.m3u8")
        if path:
            default = path.replace("\\", "/").rsplit("/", 1)[-1].rsplit(".", 1)[0]
            name = xbmcgui.Dialog().input(_(30010), default)
            type_mode = self._ask_type() if name else None
            if name and type_mode:
                playlist = self.store.add_playlist(name, path, KIND_FILE, type_mode)
                self._load_with_progress(playlist, delete_on_error=True)
        self._end_action()

    def do_pl_add_radio(self):
        self._add_radio_stations()
        self._end_action()

    def _add_radio_stations(self):
        try:
            countries = radiobrowser.countries()
        except Exception as e:
            xbmcgui.Dialog().ok(_(30017), str(e))
            return
        language = (xbmc.getLanguage(xbmc.ISO_639_1) or "en").lower()
        wanted = _LANGUAGE_COUNTRY.get(language, "US")
        preselect = next((i for i, c in enumerate(countries) if c[0] == wanted), 0)
        labels = ["%s (%d)" % (name, count) for _code, name, count in countries]
        index = xbmcgui.Dialog().select(_(30027), labels, preselect=preselect)
        if index < 0:
            return
        code, name, _count = countries[index]
        playlist = self.store.add_playlist(_(30041).format(name), radiobrowser.source(code), KIND_RADIO,
                                           m3u.TYPE_RADIO)
        self._load_with_progress(playlist, delete_on_error=True)

    def do_pl_refresh(self):
        playlist = self.store.playlist(self.params.get("id", ""))
        if playlist:
            self._load_with_progress(playlist)
        self._end_action()

    def do_pl_delete(self):
        playlist = self.store.playlist(self.params.get("id", ""))
        if playlist and xbmcgui.Dialog().yesno(ADDON_NAME, _(30020).format(playlist["name"])):
            self.store.delete_playlist(playlist["id"])
            if self.handle >= 0:
                # Opened from the playlist's own menu (not the context menu): back to the playlists
                xbmcplugin.endOfDirectory(self.handle, succeeded=False)
                xbmc.executebuiltin("Container.Update(%s,replace)" % self.url(action="playlists"))
                return
        self._end_action()


def run(argv):
    Plugin(argv).run()
