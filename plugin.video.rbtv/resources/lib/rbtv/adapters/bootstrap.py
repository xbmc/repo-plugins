"""Wires the Kodi runtime to the add-on. Imported by main.py only."""

from __future__ import annotations

import os
from typing import Any, Sequence

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from rbtv.adapters.cache import CachedCatalog, JsonFileStore
from rbtv.adapters.favorites import FavoriteStore
from rbtv.adapters.kodi import ADDON_NAME, run
from rbtv.adapters.rbtv_api import RbtvApiCatalog
from rbtv.app import strings


def main(argv: Sequence[str]) -> None:
    addon = xbmcaddon.Addon()
    tr = addon.getLocalizedString
    profile = xbmcvfs.translatePath(addon.getAddonInfo("profile"))
    favorites = FavoriteStore(os.path.join(profile, "favorites.json"))
    bar = _ProgressBar(tr(strings.LOADING_SHOWS))

    catalog = CachedCatalog(
        RbtvApiCatalog(progress=bar.update),
        JsonFileStore(os.path.join(profile, "shows.json")),
    )

    def favorite_change(show_id: int, add: bool) -> None:
        if add:
            favorites.add(show_id)
        else:
            favorites.remove(show_id)

    def keyboard() -> str | None:
        text = xbmcgui.Dialog().input(tr(strings.SEARCH_PROMPT), type=xbmcgui.INPUT_ALPHANUM)
        return text or None

    def choose_favorites(rows: list[tuple[str, str]], preselected: list[int]) -> list[int] | None:
        entries = [xbmcgui.ListItem(label=title, label2=detail) for title, detail in rows]
        chosen = xbmcgui.Dialog().multiselect(
            tr(strings.CHOOSE_FAVORITES), entries, preselect=preselected, useDetails=True
        )
        return None if chosen is None else list(chosen)

    try:
        run(
            argv,
            xbmcplugin,
            xbmcgui,
            catalog,
            tr=tr,
            keyboard=keyboard,
            execute=xbmc.executebuiltin,
            recent_years=addon.getSettingInt("recent_years"),
            favorites=favorites.ids(),
            sort_by_date=addon.getSettingInt("sort_by_date") == 1,
            on_favorite_change=favorite_change,
            choose_favorites=choose_favorites,
            on_favorites_replaced=favorites.replace,
            date_format=xbmc.getRegion("dateshort"),
        )
    finally:
        bar.close()


class _ProgressBar:
    def __init__(self, message: str) -> None:
        self._message = message
        self._bar: Any | None = None

    def update(self, done: int, total: int) -> None:
        if self._bar is None:
            self._bar = xbmcgui.DialogProgressBG()
            self._bar.create(ADDON_NAME, self._message)
        percent = int(done * 100 / total) if total else 0
        self._bar.update(percent, message=f"{done} / {total}")

    def close(self) -> None:
        if self._bar is not None:
            self._bar.close()
