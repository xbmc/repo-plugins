"""The guide: 3-hour schedule blocks, kept between exports, and the info pages."""

import functools
import os
import time
from urllib.parse import quote

from resources.lib.provider import errors
from resources.lib.provider import guideblocks
from resources.lib.util import isotime

# As many parallel requests as the web guide makes (measured 2026-10-26).
EPG_WORKERS = 3
# Kept blocks hold only the fields the export uses (see guideblocks for how long they stay good).
GUIDE_FIELDS = (
    "start_time",
    "end_time",
    "description",
    "episode_name",
    "full_description",
    "release_year",
    "genres",
    "season_number",
    "episode_number",
    "image",
    "poster_image_url",
    "program_id",
    "series_id",
    "show_type",
    "ratings",
    "content_flags",
    "has_audio_description",
    "has_sign_language",
)
# Freshness for "what is on" lookups (see _any_block): with guideblocks.BLOCK_FRESH the live stream's
# manifest request kept waiting for a whole block to be refetched.
LOOKUP_FRESH = 2 * 3600
# The guide API serves only these 3-hour UTC blocks.
BLOCK_OFFSETS = range(0, 24, 3)
BLOCK_SECONDS = 3 * 3600


class Guide:
    """The guide and the info pages; the account's guide when logged in, else the public one.

    :param api: the client's core.Api
    :param auth: the client's auth.Auth
    """

    def __init__(self, api, auth):
        self._api = api
        self._auth = auth
        # Blocks fetched and kept by the last epg_blocks, for the export's log.
        self.epg_stats = {"fetched": 0, "cached": 0}

    def _schedule_block(self, day, hour_offset):
        """Return the programmes of all channels for one 3-hour UTC block, keyed by station_id.

        :param day: a "YYYY-MM-DD" UTC date
        :param hour_offset: a UTC hour (0, 3, ... 21)
        """
        params = {"date": day, "hour_offset": str(hour_offset), "hour_range": "3", "filler": "true"}
        params["isFullDescriptionRequired"] = "true"
        if self._auth.authed:
            # Without a login the server answers with the public channel map anyway.
            params["channelMap_id"] = self._auth.channel_map()
        return self._auth.call_as_account("/epg/channel/schedules", "EPG", "EPG_SCHEDULES", params).get("channels") or {}

    def now_and_next(self, cache_dir=None):
        """Return {station_id: (programme on air now, the next one or None)}.

        The next one only if it is in the same 3-hour block. The block is kept in cache_dir.
        """
        now = time.time()
        out = {}
        for station, progs in self._any_block(now, cache_dir).items():
            programme = _at(progs, now)[0]
            if programme:
                later = [p for p in progs if p.get("start_time", "") >= programme["end_time"]]
                out[station] = (programme, min(later, key=lambda p: p["start_time"], default=None))
        return out

    def programme_at(self, station, when, cache_dir=None):
        """Return (programme, its end as a timestamp) on the station at `when`; (None, None) if not known."""
        try:
            channels = self._any_block(when, cache_dir, station)
        except errors.ApiError:
            return None, None
        return _at(channels.get(station) or [], when)

    def _any_block(self, when, cache_dir, station=None):
        """Return the block around `when` (all stations): kept if still good and has `station`, else fetched.

        A block already over is good however old: refetching it was most of a catch-up
        start (2-2.5 s).
        """
        date, offset = time.strftime("%Y-%m-%d", time.gmtime(when)), time.gmtime(when).tm_hour // 3 * 3
        path = guideblocks.block_path(cache_dir, date, offset) if cache_dir else None
        over = (int(when) // BLOCK_SECONDS + 1) * BLOCK_SECONDS <= time.time()
        kept = guideblocks.cached_block(path, None, date, offset, any_stations=True, fresh=float("inf") if over else LOOKUP_FRESH)
        if kept is not None and (station is None or station in kept):
            return kept
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        channels = self._block(date, offset, cache_dir, None)[0]
        if cache_dir:
            guideblocks.drop_old_blocks(cache_dir)
        return channels

    def epg_blocks(self, past_days=1, days_ahead=7, stations=None, cache_dir=None, progress=None):
        """Return the guide from `past_days` before today (UTC) to `days_ahead` after it, block by block.

        Days ahead stop at the first day without programmes (13 days published when
        tried, 2026-10-27). A programme spanning two blocks is in both. Sets epg_stats.

        :param stations: the station ids to keep (every block lists all of them)
        :param cache_dir: where the blocks are kept between calls (see GUIDE_FIELDS)
        :param progress: progress(done, total) is called after each block; what it raises ends the fetch
        :return: [(date, offset, guideblocks.GuideBlock), ...] in time order
        """
        from concurrent.futures import ThreadPoolExecutor

        today = int(time.time()) // 86400 * 86400
        # Login and account first, so the parallel requests below only read them.
        if self._auth.authed:
            self._auth.valid_account()
            self._auth.valid_access_token()
        wanted = None if stations is None else set(stations)
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
        self.epg_stats = {"fetched": 0, "cached": 0}
        kept = set()
        days = range(-past_days, days_ahead + 1)
        total, done = len(days) * 8, 0
        blocks = []
        # A week is ~70 blocks, a minute and a half one by one.
        with ThreadPoolExecutor(max_workers=EPG_WORKERS) as pool:
            for day in days:
                date = time.strftime("%Y-%m-%d", time.gmtime(today + day * 86400))
                kept.update(
                    os.path.basename(guideblocks.block_path(cache_dir, date, offset)) for offset in BLOCK_OFFSETS if cache_dir
                )
                fetch = functools.partial(self._kept_or_fetched, date, cache_dir=cache_dir, stations=wanted)
                found = 0
                for offset, (block, fetched) in zip(BLOCK_OFFSETS, pool.map(fetch, BLOCK_OFFSETS)):
                    self.epg_stats["fetched" if fetched else "cached"] += 1
                    blocks.append((date, offset, block))
                    found += block.programmes
                    done += 1
                    if progress:
                        progress(done, total)
                if day > 0 and not found:
                    del blocks[-len(BLOCK_OFFSETS) :]  # the first day without programmes: none ahead
                    break
        guideblocks.drop_blocks(cache_dir, kept)
        return blocks

    def _block(self, date, offset, cache_dir, stations):
        """Return (programmes by station, whether fetched from the provider)."""
        path = guideblocks.block_path(cache_dir, date, offset) if cache_dir else None
        channels = guideblocks.cached_block(path, stations, date, offset)
        if channels is not None:
            return channels, False
        return self._fetch_block(date, offset, path, stations), True

    def _kept_or_fetched(self, date, offset, cache_dir, stations):
        """Return (guideblocks.GuideBlock, whether fetched) for epg_blocks: a kept block is not read yet."""
        path = guideblocks.block_path(cache_dir, date, offset) if cache_dir else None
        header = guideblocks.block_header(path, stations, date, offset)
        if header is not None:
            return guideblocks.GuideBlock(path, stations, header["programmes"]), False
        channels = self._fetch_block(date, offset, path, stations)
        if path and os.path.exists(path):
            # Backed by its file so the digest matches the next run's.
            return guideblocks.GuideBlock(path, stations, sum(map(len, channels.values()))), True
        return guideblocks.GuideBlock(channels=channels), True

    def _fetch_block(self, date, offset, path, stations):
        """Return a block's programmes by station, fetched (and kept at `path`)."""
        try:
            fetched = self._schedule_block(date, offset)
        except errors.ApiError as e:
            # A day out of range is refused (400), not empty; only today must exist.
            if getattr(e, "status", None) != 400 or date == time.strftime("%Y-%m-%d", time.gmtime()):
                raise
            fetched = {}
        channels = {
            station: [_guide_entry(p) for p in progs if p.get("slot_type") == "schedule" and p.get("start_time")]
            for station, progs in fetched.items()
            if stations is None or station in stations
        }
        if path:
            guideblocks.store_block(path, stations, channels)
        return channels

    def details(self, kind, item_id):
        """Return the info page of a programme ("program") or a series ("series"); public, no login."""
        return self._api.call("/details/%s/%s" % (kind, quote(item_id, safe="")), "DETAILS", "DETAILS")


def _at(progs, when):
    """Return (programme, its end as a timestamp) of these on air at `when`; (None, None) if none."""
    stamp = isotime.iso(when)
    for p in progs:
        if p.get("start_time", "") <= stamp < p.get("end_time", ""):
            return p, isotime.stamp(p["end_time"])
    return None, None


def _guide_entry(p):
    return {k: p[k] for k in GUIDE_FIELDS if k in p}
