"""Validated plugin routing, localized dialogs, and Kodi item rendering."""

import re
from urllib.parse import unquote

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.ebibliocat import playback as Playback
from resources.lib.ebibliocat.ebibliocat import EBibliocat
from resources.lib.ebibliocat.errors import Cancelled, EfilmError
from resources.lib.ebibliocat.validation import positive_id
from resources.lib.utils.utils import buildUrl
from resources.lib.video.foldervideo import FolderVideo


class UI:
    def __init__(self, base_url, addon_handle, args):
        addon = xbmcaddon.Addon()
        self.ebiblio = EBibliocat(xbmcvfs.translatePath(addon.getAddonInfo("path")), addon)
        self.base_url, self.addon_handle, self.args = base_url, addon_handle, args
        self.strs = self.ebiblio.strs
        self._finished = False
        self._playback = False
        self.filters = {}

    def _arg(self, key, default=""):
        value = self.args.get(key, [default])
        if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], str):
            raise EfilmError("unknown_route")
        return value[0]

    def _page(self):
        page = positive_id(self._arg("url", "1") or "1")
        if page > 10000:
            raise EfilmError("unknown_route")
        return page

    def _notice(self, key, error=False):
        xbmcgui.Dialog().notification(
            "eBiblioCat eFilm",
            self.strs.get(key),
            xbmcgui.NOTIFICATION_ERROR if error else xbmcgui.NOTIFICATION_INFO,
            6000,
        )

    def run(self, mode=None, url=None):
        # Arguments are read from self.args so validation cannot be bypassed by another caller.
        try:
            route = self._arg("mode")
            actions = {
                "": self._home,
                "login": self._login,
                "logout": self._logout,
                "all_movies": self._movies,
                "movies": self._movies,
                "alphabet": self._alphabet,
                "search": self._search,
                "genres": lambda: self.listFolder(self.ebiblio.listGenres()),
                "lists": lambda: self.listFolder(self.ebiblio.listLists()),
                "series": lambda: self.listFolder(self.ebiblio.listSeries(self._page()), "tvshows"),
                "refresh": lambda: self._movies(refresh=True),
                "clear_cache": self._clear_cache,
                "playVideo": self._play,
            }
            if route in actions:
                actions[route]()
            elif re.fullmatch(r"(collection|genre|series|season):[1-9][0-9]*", route):
                kind, identifier = route.split(":", 1)
                identifier = positive_id(identifier)
                if kind == "collection":
                    self.listVideos(self.ebiblio.listCollection(identifier, self._page()))
                elif kind == "genre":
                    self._movies(genre_id=identifier)
                elif kind == "series":
                    self.listFolder(self.ebiblio.listSeasons(identifier), "seasons")
                else:
                    self.listVideos(self.ebiblio.listEpisodes(identifier, self._page()), "episodes")
            else:
                raise EfilmError("unknown_route")
            if self.ebiblio.session.cache.used_stale:
                self._notice("stale_cache")
        except Cancelled:
            pass
        except EfilmError as error:
            xbmc.log("eFilm operation failed: " + error.message, xbmc.LOGDEBUG)
            self._notice(error.message, error=True)
        except (ValueError, TypeError, KeyError, AttributeError, OSError):
            # No arbitrary exception text, arguments, or signed URLs enter diagnostics.
            xbmc.log("eFilm operation failed: invalid data or local I/O", xbmc.LOGDEBUG)
            self._notice("invalid_response", error=True)
        finally:
            if not self._finished:
                if self._playback:
                    xbmcplugin.setResolvedUrl(self.addon_handle, False, xbmcgui.ListItem())
                else:
                    xbmcplugin.endOfDirectory(self.addon_handle, succeeded=False)
                self._finished = True

    def _home(self):
        folders = self.ebiblio.listHome()
        signed_in = self.ebiblio.session.has_session()
        key = "logout" if signed_in else "login"
        folders.append(FolderVideo(self.strs.get(key), "", key))
        self.listFolder(folders)

    def _login(self):
        if self.signIn():
            self._finish()
            xbmc.executebuiltin("Container.Update({})".format(self.base_url))
        else:
            self._finish()

    def _logout(self):
        self.ebiblio.signOut()
        self._notice("signed_out")
        self._finish()
        xbmc.executebuiltin("Container.Refresh")

    def _clear_cache(self):
        self.ebiblio.session.cache.clear()
        self._notice("cache_cleared")
        self._home()

    def _alphabet(self):
        folders = [FolderVideo(letter, "1", "all_movies") for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
        folders.append(FolderVideo(self.strs.get("other_letters"), "1", "all_movies"))
        for folder in folders:
            self._add_folder(folder, {"letter": folder.name if len(folder.name) == 1 else "#"})
        self._finish("files")

    def _search(self):
        term = xbmcgui.Dialog().input(self.strs.get("search"), type=xbmcgui.INPUT_ALPHANUM)
        if not term:
            raise Cancelled()
        self._movies(term=term)

    def _movies(self, genre_id=None, term=None, refresh=False):
        term = self._arg("term") if term is None else term
        letter = self._arg("letter")
        if len(term) > 200 or (letter and letter not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ#"):
            raise EfilmError("unknown_route")
        self.filters = {k: v for k, v in {"term": term, "letter": letter}.items() if v}
        dialog = xbmcgui.DialogProgress()
        dialog.create("eBiblioCat eFilm", self.strs.get("loading"))
        monitor = xbmc.Monitor()

        def progress(current, total):
            dialog.update(
                int(current * 100 / total), self.strs.get("loading_pages", current=current, total=total)
            )

        try:
            result = self.ebiblio.listMovies(
                self._page() if not refresh else 1,
                genre_id,
                term,
                letter,
                refresh,
                progress,
                lambda: monitor.abortRequested() or dialog.iscanceled(),
            )
        finally:
            dialog.close()
        xbmcplugin.setPluginCategory(self.addon_handle, self.ebiblio.page_summary)
        if not result[0]:
            self._notice("no_results")
        self.listVideos(result)
        if refresh:
            self._notice("catalog_refreshed")

    def _play(self):
        self._playback = True
        parts = self._arg("url").split("/")
        if len(parts) == 5 and parts[:3] == ["efilm:", "", "product"]:
            identifier, slug = positive_id(parts[3]), unquote(parts[4])
            if not slug or len(slug) > 300:
                raise EfilmError("unknown_route")
            self.ebiblio.playProduct(identifier, slug, self.addon_handle)
        elif len(parts) == 7 and parts[:3] == ["efilm:", "", "episode"]:
            series, identifier = positive_id(parts[3]), positive_id(parts[5])
            series_slug, slug = unquote(parts[4]), unquote(parts[6])
            if not series_slug or not slug or max(len(series_slug), len(slug)) > 300:
                raise EfilmError("unknown_route")
            self.ebiblio.playProduct(identifier, slug, self.addon_handle, series, series_slug)
        else:
            raise EfilmError("unknown_route")
        self._finished = True  # playProduct resolves both success and failure paths.

    def _set_info(self, item, info):
        if Playback.kodi_major() < 20:
            item.setInfo("video", info)
            return
        tag = item.getVideoInfoTag()
        setters = {
            "title": tag.setTitle,
            "plot": tag.setPlot,
            "year": tag.setYear,
            "duration": tag.setDuration,
            "genre": tag.setGenres,
            "season": tag.setSeason,
            "episode": tag.setEpisode,
            "trailer": tag.setTrailer,
        }
        for key, value in info.items():
            if key in setters:
                setters[key](value)

    def _add_folder(self, folder, extra=None):
        query = {"mode": folder.mode, "url": folder.url}
        if folder.mode in ("all_movies", "movies") or folder.mode.startswith("genre:"):
            query.update(self.filters)
        query.update(extra or {})
        item = xbmcgui.ListItem(folder.name)
        self._set_info(item, {"title": folder.name})
        item.setArt({"thumb": folder.thumbnailImage, "icon": folder.iconImage})
        xbmcplugin.addDirectoryItem(self.addon_handle, buildUrl(query, self.base_url), item, isFolder=True)

    def _finish(self, content="files"):
        xbmcplugin.setContent(self.addon_handle, content)
        xbmcplugin.endOfDirectory(self.addon_handle, cacheToDisc=False)
        self._finished = True

    def listFolder(self, folders, content="files"):
        for folder in folders:
            self._add_folder(folder)
        self._finish(content)

    def listVideos(self, result, content="movies"):
        videos, following = result
        for video in videos:
            if isinstance(video, FolderVideo):
                self._add_folder(video)
            elif video:
                item = xbmcgui.ListItem(video.title)
                self._set_info(item, video.information)
                item.setArt({"thumb": video.thumbnailImage, "icon": "DefaultVideo.png"})
                item.setProperty("IsPlayable", "true")
                url = buildUrl({"mode": "playVideo", "url": video.url}, self.base_url)
                xbmcplugin.addDirectoryItem(self.addon_handle, url, item, isFolder=False)
        if following:
            self._add_folder(following)
        self._finish(content)

    def signIn(self):
        dialog = xbmcgui.Dialog()
        username = dialog.input(self.strs.get("username"), type=xbmcgui.INPUT_ALPHANUM)
        if not username:
            return False
        password = dialog.input(
            self.strs.get("password"), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT
        )
        if not password:
            return False
        self.ebiblio.signIn(username.strip(), password)
        self._notice("signed_in")
        return True
