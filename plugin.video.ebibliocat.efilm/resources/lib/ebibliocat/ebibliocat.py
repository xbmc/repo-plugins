"""eFilm application service; Kodi rendering and routing live in UI.py."""

import json
import math
from urllib.parse import quote

import xbmc
import xbmcgui
import xbmcplugin
from bs4 import BeautifulSoup

from resources.lib.ebibliocat import http as HTTP, home as Home, playback as Playback
from resources.lib.ebibliocat.catalog import PAGE_SIZE, episode_product, movie_selection, video_from_product
from resources.lib.ebibliocat.ebibliostrings import EBiblioStrings
from resources.lib.ebibliocat.efilmapi import WEB_BASE, EfilmSession
from resources.lib.ebibliocat.errors import Cancelled, EfilmError
from resources.lib.ebibliocat.validation import (
    object_response,
    page_response,
    positive_id,
    valid_id,
    valid_product,
)
from resources.lib.video.foldervideo import FolderVideo


class EBibliocat:
    def __init__(self, addon_path, addon):
        self.addon = addon
        self.addon_path = addon_path
        self.strs = EBiblioStrings(addon)
        language = xbmc.getLanguage(xbmc.ISO_639_1)
        self.language = language if language in ("ca", "es", "en") else "en"
        self.session = EfilmSession(addon, self.language)
        self.page_summary = ""

    def signIn(self, username, password):
        try:
            self.session.login(username, password)
        except EfilmError as error:
            if error.status in (400, 401):
                raise EfilmError("signin_failed") from None
            raise

    def signOut(self):
        self.session.clear()

    def _notify(self, key):
        xbmcgui.Dialog().notification(
            "eBiblioCat eFilm", self.strs.get(key), xbmcgui.NOTIFICATION_ERROR, 6000
        )

    def _product_detail(self, product_id, slug, series_id=None, series_slug=None):
        path = (
            "series-detail/{}/{}".format(positive_id(series_id), quote(series_slug, safe=""))
            if series_id is not None
            else "audiovisual-detail/{}/{}".format(positive_id(product_id), quote(slug, safe=""))
        )
        html = HTTP.request(WEB_BASE + self.language + "/" + path, as_json=False)
        soup = BeautifulSoup(html, "html.parser")
        script = soup.find("script", id="__NEXT_DATA__", type="application/json")
        try:
            data = json.loads(script.string)
            props = object_response(data["props"]["pageProps"])
            product = (
                episode_product(props["collectionProp"], product_id)
                if series_id is not None
                else object_response(props["productInit"])
            )
            self.session.set_localization_from_headers(props.get("headers"))
            if not valid_id(product.get("id")) or str(product["id"]) != str(product_id):
                raise EfilmError("invalid_response")
            return product
        except (AttributeError, KeyError, TypeError, ValueError):
            raise EfilmError("invalid_response") from None

    def _choose_track(self, product, product_id):
        tracks, names, seen = [], [], set()
        for track in product.get("languages") or []:
            if not isinstance(track, dict):
                continue
            if track.get("audiovisual") is not None and str(track["audiovisual"]) != str(product_id):
                continue
            language, subtitle = track.get("language"), track.get("subtitle")
            if not isinstance(language, dict) or not isinstance(subtitle, dict):
                continue
            pair = language.get("id"), subtitle.get("id")
            if not valid_id(pair[0]) or not valid_id(pair[1]) or pair in seen:
                continue
            seen.add(pair)
            tracks.append(pair)
            names.append(
                "{} — {}".format(
                    language.get("name_" + self.language) or language.get("name") or str(pair[0]),
                    subtitle.get("name_" + self.language) or subtitle.get("name") or str(pair[1]),
                )
            )
        if not tracks:
            raise EfilmError("no_tracks")
        selection = xbmcgui.Dialog().select(self.strs.get("choose_tracks"), names) if len(tracks) > 1 else 0
        if selection < 0:
            raise Cancelled()
        return tracks[selection]

    def _confirm(self, product, resume=False):
        return xbmcgui.Dialog().yesno(
            self.strs.get("resume_title" if resume else "borrow_title"),
            self.strs.get("resume_confirm" if resume else "borrow_confirm", title=product.get("name") or ""),
            nolabel=self.strs.get("cancel"),
            yeslabel=self.strs.get("resume" if resume else "borrow"),
        )

    def playProduct(self, product_id, slug, handle, series_id=None, series_slug=None):
        resolved = False
        try:
            if not self.session.has_session():
                raise EfilmError("session_expired")
            product = self._product_detail(product_id, slug, series_id, series_slug)
            language_id, subtitle_id = self._choose_track(product, product_id)
            # ISA is required for this integration. DRM is checked before borrowing if advertised;
            # providers that reveal it only after lending are checked again in make_item().
            drm = product.get("drm_type") or product.get("license_type")
            if drm:
                aliases = {"widevine": "com.widevine.alpha", "playready": "com.microsoft.playready"}
                drm = aliases.get(str(drm).lower(), str(drm).lower())
            Playback.check_dependencies("mpd", drm)
            with self.session.loan_guard(product_id):
                loan_id = self.session.find_active_loan(product_id)
                if not self._confirm(product, resume=bool(loan_id)):
                    raise Cancelled()
                if not loan_id:
                    try:
                        loan_id = self.session.make_loan(product_id)["id"]
                    except EfilmError as error:
                        if error.status == 400:
                            raise EfilmError("loan_rejected", status=400) from None
                        raise
                try:
                    playback = self.session.get_playback(loan_id, language_id, subtitle_id)
                except EfilmError as error:
                    if error.status not in (404, 410):
                        raise
                    # Only offer another borrow when an authoritative read confirms no active loan.
                    if self.session.find_active_loan(product_id):
                        raise
                    self._notify("loan_expired")
                    if not self._confirm(product):
                        raise Cancelled()
                    loan_id = self.session.make_loan(product_id)["id"]
                    playback = self.session.get_playback(loan_id, language_id, subtitle_id)
                item = self._makePlaybackItem(playback, product)
                xbmcplugin.setResolvedUrl(handle, True, item)
                resolved = True
        except Cancelled:
            pass
        except EfilmError as error:
            xbmc.log("eFilm playback failed: " + error.message, xbmc.LOGDEBUG)
            self._notify(error.message)
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            xbmc.log("eFilm playback failed: invalid response or local I/O", xbmc.LOGDEBUG)
            self._notify("invalid_response")
        finally:
            if not resolved:
                xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem())

    def _makePlaybackItem(self, playback, product):
        return Playback.make_item(Playback.parse_stream(playback), product.get("name") or "eFilm")

    def listHome(self):
        return [
            FolderVideo(self.strs.get(key), "1", key)
            for key in (
                "all_movies",
                "alphabet",
                "search",
                "genres",
                "lists",
                "series",
                "refresh",
                "clear_cache",
            )
        ]

    def listLists(self):
        try:
            folders = Home.from_entries(self.session.visible_lists(), self.language)
            if folders:
                return folders
        except EfilmError as error:
            if error.message not in ("network_error", "service_error", "invalid_response"):
                raise
            xbmc.log("eFilm list directory unavailable; using fallback", xbmc.LOGDEBUG)
        return Home.getList(self.strs)

    def listCollection(self, list_id, page=1):
        result = self.session.list_elements(list_id, page)
        rows, has_next = page_response(result)
        items = []
        for entry in rows:
            if not isinstance(entry, dict):
                continue
            collection = entry.get("collections")
            if valid_product(collection) and collection["type"] == "serie":
                items.append(self._series_folder(collection))
                continue
            product = entry.get("products")
            if valid_product(product) and product["type"] == "audiovisual":
                video = video_from_product(product)
                if video:
                    items.append(video)
        following = (
            FolderVideo(self.strs.get("next"), str(page + 1), "collection:" + str(list_id))
            if has_next
            else None
        )
        return [items, following]

    def listMovies(
        self, page=1, genre_id=None, term="", letter="", refresh=False, progress=None, cancelled=None
    ):
        products = self.session.movies(refresh, progress, cancelled)
        selected = movie_selection(products, genre_id, term, letter)
        total = max(1, math.ceil(len(selected) / PAGE_SIZE))
        page = max(1, min(page, total))
        self.page_summary = self.strs.get("page", current=page, total=total, count=len(selected))
        start = (page - 1) * PAGE_SIZE
        videos = [video_from_product(p) for p in selected[start : start + PAGE_SIZE]]
        mode = "all_movies" if genre_id is None else "genre:" + str(genre_id)
        previous = [FolderVideo(self.strs.get("previous"), str(page - 1), mode)] if page > 1 else []
        following = FolderVideo(self.strs.get("next"), str(page + 1), mode) if page < total else None
        return [previous + videos, following]

    def listGenres(self):
        return [FolderVideo(g["name"], "1", "genre:" + str(g["id"])) for g in self.session.genres()]

    @staticmethod
    def _series_folder(product):
        cover = product.get("cover") if isinstance(product.get("cover"), str) else ""
        return FolderVideo(product["name"], "1", "series:" + str(product["id"]), cover, cover)

    def listSeries(self, page=1):
        result = self.session.series(page)
        rows, following = page_response(result)
        folders = [self._series_folder(p) for p in rows if valid_product(p)]
        if page > 1:
            folders.insert(0, FolderVideo(self.strs.get("previous"), str(page - 1), "series"))
        if following:
            folders.append(FolderVideo(self.strs.get("next"), str(page + 1), "series"))
        return folders

    def listSeasons(self, series_id):
        detail = self.session.series_detail(series_id)
        cover = detail.get("cover") if isinstance(detail.get("cover"), str) else ""
        return [
            FolderVideo(
                self.strs.get("season", number=season["season"]),
                str(season["season"]),
                "season:" + str(series_id),
                cover,
                cover,
            )
            for season in detail["seasons"]
            if isinstance(season, dict)
            and valid_id(season.get("season"))
            and isinstance(season.get("chapters"), list)
            and season["chapters"]
        ]

    def listEpisodes(self, series_id, season_number):
        detail = self.session.series_detail(series_id)
        videos = []
        for season in detail["seasons"]:
            if not isinstance(season, dict) or str(season.get("season")) != str(season_number):
                continue
            chapters = season.get("chapters")
            if not isinstance(chapters, list):
                continue
            for number, product in enumerate(chapters, 1):
                if not valid_product(product):
                    continue
                product = dict(product, season=int(season_number), episode=number)
                video = video_from_product(product)
                if video:
                    video.url = "efilm://episode/{}/{}/{}/{}".format(
                        series_id,
                        quote(detail.get("slug") or "series", safe=""),
                        product["id"],
                        quote(product["slug"], safe=""),
                    )
                    videos.append(video)
        return [videos, None]

    @staticmethod
    def getVideo(data):
        return video_from_product(data)
