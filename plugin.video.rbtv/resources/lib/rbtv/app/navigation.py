from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Callable
from urllib.parse import parse_qs, urlencode, urlsplit

from rbtv.app import strings
from rbtv.app.strings import Translate
from rbtv.domain.episode import Episode, SourceKind
from rbtv.domain.show import Show
from rbtv.ports.catalog import Catalog

DETAIL_MAX_LENGTH = 80
DEFAULT_DATE_FORMAT = "%d.%m.%Y"
YOUTUBE_PLAY_URL = "plugin://plugin.video.youtube/play/?video_id={}"
_SHOW_PATH = re.compile(r"^/shows/(\d+)$")
_FAVORITE_PATH = re.compile(r"^/favorite/(add|remove)/(\d+)$")


class NotFound(Exception):
    pass


@dataclass(frozen=True)
class Refresh:
    """The view must be reloaded. notify=True also shows a message."""

    notify: bool = True


@dataclass(frozen=True)
class Redirect:
    """Leave this listing: open url instead, or stay where we are if url is None."""

    url: str | None = None


@dataclass(frozen=True)
class MenuItem:
    label: str
    url: str
    is_folder: bool
    thumbnail_url: str | None = None
    playable: bool = False
    duration: int = 0
    plot: str = ""
    genre: str = ""
    premiered: date | None = None
    context_menu: tuple[tuple[str, str], ...] = ()


class Navigation:
    def __init__(
        self,
        catalog: Catalog,
        base_url: str,
        tr: Translate,
        prompt: Callable[[], str | None] = lambda: None,
        recent_years: int = 0,
        favorites: set[int] | None = None,
        sort_by_date: bool = False,
        date_format: str = DEFAULT_DATE_FORMAT,
    ) -> None:
        self._catalog = catalog
        self.tr = tr
        self.date_format = date_format
        self._base = base_url.rstrip("/")
        self.prompt = prompt
        self.recent_years = recent_years
        self.favorites = favorites or set()
        self.sort_by_date = sort_by_date
        self.today = date.today
        self.on_favorite_change: Callable[[int, bool], None] = lambda show_id, add: None
        self.on_favorites_replaced: Callable[[set[int]], None] = lambda ids: None
        self.choose_favorites: Callable[[list[tuple[str, str]], list[int]], list[int] | None] = (
            lambda rows, preselected: None
        )

    def dispatch(self, url: str, query: str = "") -> list[MenuItem] | Refresh | Redirect:
        path = urlsplit(url).path.rstrip("/") or "/"
        params = parse_qs(query.lstrip("?"))

        if path == "/":
            return self.root()
        favorite = _FAVORITE_PATH.match(path)
        if favorite:
            action, show_id = favorite.group(1), int(favorite.group(2))
            self.on_favorite_change(show_id, action == "add")
            return Refresh(notify=False)
        if path == "/favorites":
            return self.manage_favorites()
        if path == "/all":
            return self.shows()
        if path == "/refresh":
            return self.refresh()
        if path == "/search":
            return self.search(params.get("q", [""])[0])
        match = _SHOW_PATH.match(path)
        if match:
            offset = int(params.get("offset", ["0"])[0])
            return self.episodes(int(match.group(1)), offset)
        raise NotFound(path)

    def search(self, needle: str) -> list[MenuItem] | Redirect:
        if needle:
            return self.shows(needle)
        entered = self.prompt()
        if not entered:
            return Redirect()
        # Keep the text in the folder URL so Container.Refresh can repeat the search
        return Redirect(f"{self._base}/search?{urlencode({'q': entered})}")

    def refresh(self) -> Refresh:
        invalidate = getattr(self._catalog, "invalidate", None)
        if invalidate:
            invalidate()
        return Refresh()

    def root(self) -> list[MenuItem]:
        items = [
            MenuItem(self._action(strings.SEARCH), f"{self._base}/search", is_folder=True),
            MenuItem(self._action(strings.REFRESH_LIST), f"{self._base}/refresh", is_folder=False),
            MenuItem(
                self._action(strings.MANAGE_FAVORITES), f"{self._base}/favorites", is_folder=False
            ),
        ]
        if self.favorites:
            items.append(
                MenuItem(self._action(strings.ALL_SHOWS), f"{self._base}/all", is_folder=True)
            )
            items.extend(self.shows(only=self.favorites))
        else:
            items.extend(self.shows())
        return items

    def shows(self, query: str | None = None, only: set[int] | None = None) -> list[MenuItem]:
        shows = self._sorted(self._catalog.all_shows())
        if only is not None:
            shows = [s for s in shows if s.id in only]
        elif query:
            needle = query.casefold()
            shows = [s for s in shows if needle in s.title.casefold()]
        elif self.recent_years > 0:
            oldest = self.today().year - self.recent_years + 1
            shows = [s for s in shows if s.last_year and s.last_year >= oldest]
        return [
            MenuItem(
                label=self._show_label(s),
                url=f"{self._base}/shows/{s.id}",
                is_folder=True,
                thumbnail_url=s.thumbnail_url,
                plot=s.description,
                genre=s.genre,
                premiered=s.last_episode_date,
                context_menu=self._favorite_action(s.id),
            )
            for s in shows
        ]

    def manage_favorites(self) -> Refresh:
        shows = self._sorted(self._catalog.all_shows())
        preselected = [i for i, s in enumerate(shows) if s.id in self.favorites]
        rows = [(s.title, _detail_line(s)) for s in shows]
        chosen = self.choose_favorites(rows, preselected)
        if chosen is None:
            return Refresh(notify=False)
        self.on_favorites_replaced({shows[i].id for i in chosen})
        return Refresh(notify=False)

    def _sorted(self, shows: list[Show]) -> list[Show]:
        if not self.sort_by_date:
            return sorted(shows, key=lambda s: s.title.casefold())
        return sorted(
            shows,
            key=lambda s: (
                s.last_episode_date is None,
                -(s.last_episode_date.toordinal() if s.last_episode_date else 0),
                s.title.casefold(),
            ),
        )

    def _favorite_action(self, show_id: int) -> tuple[tuple[str, str], ...]:
        if show_id in self.favorites:
            label, action = self.tr(strings.FAVORITE_REMOVE), "remove"
        else:
            label, action = self.tr(strings.FAVORITE_ADD), "add"
        return ((label, f"{self._base}/favorite/{action}/{show_id}"),)

    def episodes(self, show_id: int, offset: int = 0) -> list[MenuItem]:
        page = self._catalog.episodes_of_show(show_id, offset)
        items = [item for item in map(self._episode_item, page.episodes) if item]
        if page.has_more:
            next_offset = page.offset + len(page.episodes)
            query = urlencode({"offset": next_offset})
            items.append(
                MenuItem(
                    self.tr(strings.NEXT_PAGE),
                    f"{self._base}/shows/{show_id}?{query}",
                    is_folder=True,
                )
            )
        return items

    def _action(self, string_id: int) -> str:
        return f"[{self.tr(string_id)}]"

    def _format_date(self, value: date) -> str:
        try:
            text = value.strftime(self.date_format)
        except ValueError:
            # e.g. "%-d" from Kodi's region settings raises on Windows
            text = ""
        return text.strip() or value.strftime(DEFAULT_DATE_FORMAT)

    def _show_label(self, show: Show) -> str:
        parts = []
        if show.last_year:
            parts.append(str(show.last_year))
        if show.episode_count:
            string_id = (
                strings.EPISODE_COUNT_ONE if show.episode_count == 1 else strings.EPISODE_COUNT_MANY
            )
            parts.append(self.tr(string_id).format(show.episode_count))
        return f"{show.title} ({', '.join(parts)})" if parts else show.title

    def _episode_item(self, episode: Episode) -> MenuItem | None:
        if not episode.available:
            return None
        youtube = episode.source(SourceKind.YOUTUBE)
        if youtube is None:
            return None
        label = episode.title
        if episode.published:
            label = f"{self._format_date(episode.published)} | {label}"
        return MenuItem(
            label=label,
            url=YOUTUBE_PLAY_URL.format(youtube.token),
            is_folder=False,
            thumbnail_url=episode.thumbnail_url,
            playable=True,
            duration=episode.duration,
            premiered=episode.published,
            plot=episode.description,
        )


def _detail_line(show: Show) -> str:
    parts = [str(show.last_year) if show.last_year else "", show.genre, show.description]
    text = " | ".join(part.strip() for part in parts if part and part.strip())
    text = " ".join(text.split())
    if len(text) > DETAIL_MAX_LENGTH:
        text = text[: DETAIL_MAX_LENGTH - 1].rstrip() + "…"
    return text
