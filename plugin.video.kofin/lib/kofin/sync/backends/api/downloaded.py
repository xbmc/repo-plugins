"""A download's mark on its library row, carried by the pass.

The badge art and the "Kofin Downloads" tag are part of the desired state: a
downloaded movie or episode carries the badge, and so do the season and the
show of a downloaded episode, so that a skin can mark them while browsing
down to the file; a downloaded movie and the show of a downloaded episode
carry the tag, and a downloaded episode a tag of its own where this Kodi
keeps an episode's tags (``episode_tags``). The state joins the inputs token
(metadata.inputs_token), so a change of it re-plans the row
(downloads/nativeport.NativeApi). The badge key has no dot: the setter
accepts a dotted art key and never stores it.
"""

from collections.abc import Iterable

from kofin.core.log import Logger

LOG = Logger(__name__)

BADGE_ART = "kofindownloaded"
BADGE_URL = "special://home/addons/plugin.video.kofin/resources/media/downloaded.png"


def marks() -> tuple[set[str], dict[str, set[str]]]:
    """``(downloaded item ids, series id -> its downloaded episode ids)``,
    read once a pass from kofin's own store."""
    try:
        from kofin.downloads import store

        rows = store.rows(store.DONE)
    except Exception:
        LOG.exception("download rows unavailable to the pass")
        return set(), {}
    done = {row.jellyfin_id for row in rows}
    series: dict[str, set[str]] = {}
    for row in rows:
        if row.media_type == "episode" and row.series_id:
            series.setdefault(row.series_id, set()).add(row.jellyfin_id)
    return done, series


def flag(
    kind: str,
    item_id: str,
    done: set[str],
    series: Iterable[str],
    season: bool = False,
) -> str:
    """What of the download state a row of this kind reads: an input token.
    ``season`` says a season holds a downloaded episode: the catalogue files
    an episode under its show, so the caller finds that through the
    episodes' numbers (patch.Applier.downloaded_seasons)."""
    if kind in ("Movie", "Episode") and item_id in done:
        return "downloaded"
    if kind == "Series" and item_id in series:
        return "downloaded"
    if kind == "Season" and season:
        return "downloaded"
    return ""


def apply(kind: str, desired: dict, mark: str) -> None:
    """Put the badge and the tag into the desired state of a marked row.
    An episode's desired state has tags only on a Kodi that keeps them."""
    from kofin.downloads import EPISODE_TAG, TAG

    if not mark:
        return
    desired.setdefault("art", {})[BADGE_ART] = BADGE_URL
    tag = {"Movie": TAG, "Series": TAG, "Episode": EPISODE_TAG}.get(kind)
    if tag and isinstance(desired.get("tag"), list):
        desired["tag"] = sorted(set(desired["tag"]) | {tag})
