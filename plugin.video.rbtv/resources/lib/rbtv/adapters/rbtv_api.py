from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Any, Callable, Iterator
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from rbtv.adapters.rbtv_mapping import episode_page_from_byshow, shows_from_all
from rbtv.domain.episode import EpisodePage
from rbtv.domain.show import Show

BASE_URL = "https://api.rocketbeans.tv/v1"
USER_AGENT = "Kodi-plugin.video.rbtv"
PAGE_SIZE = 50  # API maximum


class RbtvApiError(Exception):
    pass


@contextmanager
def _unexpected_response(payload: dict[str, Any]) -> Iterator[None]:
    """Turn a payload that does not match the expected shape into an RbtvApiError."""
    try:
        yield
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise RbtvApiError(f"Unexpected response from the RBTV API ({exc!r})") from exc


def fetch_json(url: str, timeout: float = 10.0) -> dict[str, Any]:
    if not url.startswith("https://"):
        raise RbtvApiError(f"Refusing to fetch non-https URL: {url}")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:  # nosec B310
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RbtvApiError(f"Unexpected response for {url}")
    return payload


class RbtvApiCatalog:
    def __init__(
        self,
        fetch: Callable[[str], dict[str, Any]] = fetch_json,
        base_url: str = BASE_URL,
        progress: Callable[[int, int], None] | None = None,
    ) -> None:
        self._fetch = fetch
        self._base_url = base_url
        self._progress = progress

    def all_shows(self) -> list[Show]:
        shows: list[Show] = []
        offset = 0
        while True:
            payload = self._get("/media/show/all", limit=PAGE_SIZE, offset=offset)
            with _unexpected_response(payload):
                page = shows_from_all(payload)
                total = int(payload["pagination"]["total"]) if page else 0
            if not page:
                break
            shows.extend(page)
            offset += len(page)
            if self._progress:
                self._progress(offset, total)
            if offset >= total:
                break
        return shows

    def episodes_of_show(self, show_id: int, offset: int = 0) -> EpisodePage:
        payload = self._get(
            f"/media/episode/byshow/{show_id}",
            limit=PAGE_SIZE,
            offset=offset,
            order="DESC",
        )
        with _unexpected_response(payload):
            return episode_page_from_byshow(payload)

    def _get(self, path: str, **params: Any) -> dict[str, Any]:
        url = self._base_url + path
        if params:
            url += "?" + urlencode(params)
        payload = self._fetch(url)
        if payload.get("success") is False:
            raise RbtvApiError(payload.get("message") or f"API call failed: {url}")
        return payload
