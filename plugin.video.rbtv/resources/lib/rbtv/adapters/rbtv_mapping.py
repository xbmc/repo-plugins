from __future__ import annotations

from datetime import date, datetime
from typing import Any

from rbtv.domain.episode import Episode, EpisodePage, SourceKind, VideoSource
from rbtv.domain.show import Show

_PREFERRED_SIZES = ("large", "medium", "small")


def shows_from_all(payload: dict[str, Any]) -> list[Show]:
    return [
        Show(
            id=item["id"],
            title=item["title"],
            thumbnail_url=_pick_image(item.get("thumbnail") or []),
            description=item.get("description") or "",
            genre=item.get("genre") or "",
            last_episode_date=_last_episode_date(item.get("lastEpisode")),
            episode_count=_episode_count(item),
        )
        for item in payload["data"]
    ]


def _episode_count(item: dict[str, Any]) -> int | None:
    if item.get("hasUnsortedEpisodes"):
        return None
    seasons = item.get("seasons") or []
    counts = [season.get("numEpisodes") for season in seasons]
    # numEpisodes is not in the (2022) API docs: show nothing rather than a wrong sum
    if not counts or not all(isinstance(c, int) for c in counts):
        return None
    return sum(int(c) for c in counts)


def _last_episode_date(last_episode: dict[str, Any] | None) -> date | None:
    episodes = (last_episode or {}).get("episodes") or []
    if not episodes:
        return None
    episode = episodes[0]
    return _parse_date(episode.get("distributionPublishingDate")) or _parse_date(
        episode.get("firstBroadcastdate")
    )


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def episode_page_from_byshow(payload: dict[str, Any]) -> EpisodePage:
    pagination = payload["pagination"]
    return EpisodePage(
        episodes=tuple(_episode(item) for item in payload["data"]["episodes"]),
        offset=pagination["offset"],
        total=pagination["total"],
    )


def _episode(item: dict[str, Any]) -> Episode:
    return Episode(
        id=item["id"],
        title=item["title"],
        show_id=item["showId"],
        duration=item.get("duration") or 0,
        available=bool(item.get("isAvailable")),
        thumbnail_url=_pick_image(item.get("thumbnail") or []),
        sources=tuple(
            VideoSource(SourceKind.parse(t.get("type")), t["token"])
            for t in item.get("tokens") or []
        ),
        published=_parse_date(item.get("distributionPublishingDate"))
        or _parse_date(item.get("firstBroadcastdate")),
        description=item.get("description") or "",
    )


def _pick_image(images: list[dict[str, Any]]) -> str | None:
    by_name = {img.get("name"): img.get("url") for img in images}
    for size in _PREFERRED_SIZES:
        url = by_name.get(size)
        if url:
            return _absolute(url)
    return None


def _absolute(url: str) -> str:
    return "https:" + url if url.startswith("//") else url
