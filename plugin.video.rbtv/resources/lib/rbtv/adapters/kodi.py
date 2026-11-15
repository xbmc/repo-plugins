from __future__ import annotations

from typing import Any, Callable, Sequence
from urllib.parse import urlsplit

from rbtv.adapters.rbtv_api import RbtvApiError
from rbtv.app import strings
from rbtv.app.navigation import (
    DEFAULT_DATE_FORMAT,
    MenuItem,
    Navigation,
    NotFound,
    Redirect,
    Refresh,
)
from rbtv.app.strings import Translate
from rbtv.ports.catalog import Catalog

ADDON_NAME = "Rocket Beans TV"


def run(
    argv: Sequence[str],
    plugin: Any,
    gui: Any,
    catalog: Catalog,
    tr: Translate,
    keyboard: Callable[[], str | None] = lambda: None,
    execute: Callable[[str], None] = lambda builtin: None,
    recent_years: int = 0,
    favorites: set[int] | None = None,
    sort_by_date: bool = False,
    on_favorite_change: Callable[[int, bool], None] = lambda show_id, add: None,
    choose_favorites: Callable[[list[tuple[str, str]], list[int]], list[int] | None] | None = None,
    on_favorites_replaced: Callable[[set[int]], None] = lambda ids: None,
    date_format: str = DEFAULT_DATE_FORMAT,
) -> None:
    url, handle = argv[0], int(argv[1])
    query = argv[2] if len(argv) > 2 else ""
    base = "plugin://" + urlsplit(url).netloc

    try:
        navigation = Navigation(
            catalog,
            base,
            tr=tr,
            prompt=keyboard,
            recent_years=recent_years,
            favorites=favorites,
            sort_by_date=sort_by_date,
            date_format=date_format,
        )
        navigation.on_favorite_change = on_favorite_change
        navigation.on_favorites_replaced = on_favorites_replaced
        if choose_favorites:
            navigation.choose_favorites = choose_favorites
        items = navigation.dispatch(url, query)
    except (NotFound, RbtvApiError, OSError, ValueError) as exc:
        gui.Dialog().notification(ADDON_NAME, str(exc) or type(exc).__name__)
        plugin.endOfDirectory(handle, succeeded=False)
        return

    if isinstance(items, Redirect):
        plugin.endOfDirectory(handle, succeeded=False)
        if items.url:
            execute(f"Container.Update({items.url})")
        return

    if isinstance(items, Refresh):
        if items.notify:
            gui.Dialog().notification(ADDON_NAME, tr(strings.RELOADING_SHOWS))
        plugin.endOfDirectory(handle, succeeded=False)
        execute("Container.Refresh")
        return

    plugin.setContent(handle, "videos")
    plugin.addDirectoryItems(
        handle, [(i.url, _list_item(gui, i), i.is_folder) for i in items], len(items)
    )
    plugin.endOfDirectory(handle)


def _list_item(gui: Any, item: MenuItem) -> Any:
    li = gui.ListItem(label=item.label, offscreen=True)
    if item.thumbnail_url:
        li.setArt({"thumb": item.thumbnail_url, "icon": item.thumbnail_url})

    tag = li.getVideoInfoTag()
    tag.setTitle(item.label)
    if item.plot:
        tag.setPlot(item.plot)
    if item.genre:
        tag.setGenres([item.genre])
    if item.premiered:
        tag.setPremiered(item.premiered.isoformat())
        tag.setYear(item.premiered.year)
    if item.context_menu:
        li.addContextMenuItems([(label, f"RunPlugin({url})") for label, url in item.context_menu])
    if item.playable:
        li.setProperty("IsPlayable", "true")
        tag.setMediaType("video")
        if item.duration:
            tag.setDuration(item.duration)
    return li
