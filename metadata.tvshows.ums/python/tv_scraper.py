from __future__ import annotations

import json
import os
import threading
import time
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

from dataclasses import dataclass
from typing import Optional

from cache import FileCache
from duplicate_tracker import DuplicateTracker
from logger import Logger
from settings_manager import SettingsManager
from kinopoisk_api import KinopoiskClient, map_production_status
from omdb_client import OmdbClient, parse_rt_rating, parse_mc_rating, parse_award_tags
from tvmaze_client import TvmazeClient
from fanart_client import FanartClient
from nfo_parser import NfoParser
from models import (
    TVShowDetails, Season, Episode,
    ArtworkType, DataSource, Rating
)
from utils import (
    get_params, clean_title, extract_kinopoisk_id,
    extract_imdb_id, search_kp_by_imdb, transliterate_to_cyrillic,
    extract_alt_title, deduplicate_results, _has_cyrillic,
)
from nfo_writer import write_tvshow_nfo


def _perform_dual_search(
    results: list,
    candidate: str,
    search_year: str | None,
    kp_client: KinopoiskClient,
    type_filter: list[str],
    settings: SettingsManager,
    logger: Logger,
) -> list:
    alt_title = extract_alt_title(results[0], candidate, logger)

    if not alt_title:
        logger.info("_perform_dual_search: dual search: skipped, no valid alt_title")
        return results

    logger.info(
        f"_perform_dual_search: dual search: alt_title='{alt_title}', "
        f"source='{'title_original' if _has_cyrillic(candidate) else 'title_ru'}'"
    )

    secondary_results = kp_client.search(alt_title, search_year, type_filter=type_filter)

    if not secondary_results:
        logger.info("_perform_dual_search: dual search: secondary search returned 0 results")
        return results

    merged = deduplicate_results(results, secondary_results, search_year, logger)
    logger.info(
        f"_perform_dual_search: dual search complete: "
        f"primary={len(results)}, secondary={len(secondary_results)}, merged={len(merged)}"
    )
    return merged


_kp_unavailable = False
_kp_unavailable_notified = False
_stale_cache_notified = False
_nfo_fallback_notified = False
_wikidata_errors = 0
_WIKIDATA_MAX_ERRORS = 3
_wikidata_degraded_notified = False

# In-memory season cache (thread-safe)
@dataclass
class _CacheEntry:
    seasons: list[Season]
    timestamp: float
    access_order: int


_season_cache: dict[int, _CacheEntry] = {}
_season_cache_lock = threading.Lock()
_CACHE_MAX_SIZE = 10
_cache_access_counter = 0


def _resolve_imdb_via_wikidata(details, kp_id, cache, settings, logger):
    """Попытка получить IMDB ID из Wikidata если KP API не вернул его."""
    global _wikidata_errors, _wikidata_degraded_notified

    if details.imdb_id:
        return

    if not settings.use_wikidata_fallback:
        return

    if _wikidata_errors >= _WIKIDATA_MAX_ERRORS:
        if not _wikidata_degraded_notified:
            logger.warning("_resolve_imdb_via_wikidata: degraded mode, skipping Wikidata fallback")
            _wikidata_degraded_notified = True
        return

    wikidata_cache_key = f"wikidata_imdb_{kp_id}"

    # 1. Fresh cache
    cached = cache.get(wikidata_cache_key)
    if cached is not None:
        imdb_id = cached.get("imdb_id", "")
        if imdb_id:
            details.imdb_id = imdb_id
            logger.info(f"_resolve_imdb_via_wikidata: cache hit kp_id={kp_id} -> {imdb_id}")
        else:
            logger.debug(f"_resolve_imdb_via_wikidata: cache hit (empty) kp_id={kp_id}")
        return

    # 2. Stale cache
    stale = cache.get_stale(wikidata_cache_key)
    if stale is not None:
        imdb_id = stale.get("imdb_id", "")
        if imdb_id:
            details.imdb_id = imdb_id
            logger.info(f"_resolve_imdb_via_wikidata: stale cache hit kp_id={kp_id} -> {imdb_id}")
        return

    # 3. SPARQL request
    from wikidata_client import WikidataClient
    client = WikidataClient(logger)
    imdb_id = client.get_imdb_id_by_kp_id(kp_id)

    if imdb_id is None:
        _wikidata_errors += 1
        if _wikidata_errors >= _WIKIDATA_MAX_ERRORS:
            logger.warning(
                f"_resolve_imdb_via_wikidata: {_wikidata_errors} errors, entering degraded mode"
            )
        return

    # 4. Cache result (including empty)
    cache.put(wikidata_cache_key, {"imdb_id": imdb_id})

    if imdb_id:
        details.imdb_id = imdb_id
        logger.info(f"_resolve_imdb_via_wikidata: resolved kp_id={kp_id} -> {imdb_id}")
    else:
        logger.info(f"_resolve_imdb_via_wikidata: no IMDB ID found for kp_id={kp_id}")


def _try_nfo_fallback_tvshow(
    kp_id: int, dir_path: str, logger: Logger
) -> TVShowDetails | None:
    logger.info(
        f"_try_nfo_fallback_tvshow: attempting NFO fallback for kp_id={kp_id}, "
        f"dir_path='{dir_path}'"
    )

    if not dir_path:
        logger.info("_try_nfo_fallback_tvshow: empty dir_path, cannot locate NFO")
        return None

    if dir_path.endswith("/") or dir_path.endswith("\\"):
        nfo_path = dir_path + "tvshow.nfo"
    else:
        _, ext = os.path.splitext(dir_path)
        if ext:
            nfo_path = os.path.dirname(dir_path) + "/tvshow.nfo"
        else:
            nfo_path = dir_path + "/tvshow.nfo"

    try:
        if not xbmcvfs.exists(nfo_path):
            logger.info(f"_try_nfo_fallback_tvshow: NFO not found at {nfo_path}")
            return None

        f = xbmcvfs.File(nfo_path)
        try:
            nfo_content = f.read()
        finally:
            f.close()

        if not nfo_content:
            logger.warning(f"_try_nfo_fallback_tvshow: empty NFO at {nfo_path}")
            return None

        parser = NfoParser(logger)
        details = parser.parse_full_tvshow(nfo_content)

        if details is None:
            logger.warning(
                f"_try_nfo_fallback_tvshow: failed to parse NFO at {nfo_path}"
            )
            return None

        if details.kinopoisk_id == 0:
            details.kinopoisk_id = kp_id

        logger.info(
            f"_try_nfo_fallback_tvshow: success title='{details.title_ru}' from {nfo_path}"
        )
        return details

    except Exception as e:
        logger.warning(
            f"_try_nfo_fallback_tvshow: unexpected error for {nfo_path}: {e}"
        )
        return None


def run() -> None:
    """Entry point for the TV Shows scraper."""
    params = get_params()
    action = params.get("action", "")
    handle = params["handle"]

    settings = SettingsManager()
    logger = Logger(debug_enabled=settings.debug_logging)
    logger.info(f"tv_scraper.run: action={action}, handle={handle}")

    if settings.clear_cache:
        try:
            addon_id = xbmcaddon.Addon().getAddonInfo('id')
            cache = FileCache(addon_id, logger)
            cache.clear()
            tracker = DuplicateTracker(addon_id, logger)
            tracker.clear()
            settings.set_clear_cache(False)
            logger.info("tv_scraper.run: cache cleared by user request")
            xbmc.executebuiltin(
                'Notification("TV Scraper", '
                '"Кэш очищен", 3000)'
            )
        except Exception as e:
            logger.error(f"tv_scraper.run: failed to clear cache: {e}")

    enddir = True
    try:
        if action == "find":
            _handle_find(params, handle, settings, logger)
        elif action == "getdetails":
            enddir = not _handle_getdetails(params, handle, settings, logger)
        elif action == "getepisodelist":
            _handle_getepisodelist(params, handle, settings, logger)
        elif action == "getepisodedetails":
            enddir = not _handle_getepisodedetails(params, handle, settings, logger)
        elif action == "getartwork":
            enddir = not _handle_getartwork(params, handle, settings, logger)
        elif action == "NfoUrl":
            _handle_nfo(params, handle, logger)
        else:
            logger.warning(f"tv_scraper.run: unknown action '{action}'")
    except Exception as e:
        logger.error(f"tv_scraper.run: unhandled exception in action={action}: {e}")

    if enddir:
        xbmcplugin.endOfDirectory(handle)


def _handle_find(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> None:
    """Search for TV shows on Kinopoisk with TV type filter."""
    global _kp_unavailable
    title = params.get("title", "")
    year = params.get("year")

    logger.info(f"_handle_find: title='{title}', year={year}")

    if not title:
        logger.warning("_handle_find: empty title")
        return

    if not settings.kinopoisk_api_key:
        logger.error("_handle_find: Kinopoisk API key not configured")
        xbmc.executebuiltin(
            'Notification("Ultimate Movie Scraper", '
            '"Укажите API-ключ Кинопоиска в настройках дополнения", 5000)'
        )
        return

    kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)

    search_year = year if year and year != "0" else None
    candidates, extracted_year = clean_title(title, logger)
    if not search_year and extracted_year:
        search_year = extracted_year

    tv_type_filter = ["TV_SERIES", "MINI_SERIES", "TV_SHOW"]

    results = []
    successful_candidate = None
    for candidate in candidates:
        results = kp_client.search(candidate, search_year, type_filter=tv_type_filter)
        if results:
            successful_candidate = candidate
            logger.info(f"_handle_find: found {len(results)} results for candidate '{candidate}'")
            break

    dual_search_done = False
    if results and settings.enable_dual_search:
        results = _perform_dual_search(
            results, successful_candidate, search_year,
            kp_client, tv_type_filter, settings, logger
        )
        dual_search_done = True
    elif results:
        logger.info("_handle_find: dual search: disabled by settings")

    if not results and search_year:
        for candidate in candidates:
            results = kp_client.search(candidate, None, type_filter=tv_type_filter)
            if results:
                successful_candidate = candidate
                logger.info(f"_handle_find: found {len(results)} results for '{candidate}' without year")
                break

    if results and settings.enable_dual_search and not dual_search_done:
        results = _perform_dual_search(
            results, successful_candidate, search_year,
            kp_client, tv_type_filter, settings, logger
        )
    elif results and not dual_search_done:
        logger.info("_handle_find: dual search: disabled by settings")

    if not results:
        trans_pairs = [
            (c, transliterate_to_cyrillic(c)) for c in candidates if transliterate_to_cyrillic(c) != c
        ]
        if trans_pairs:
            for original, trans in trans_pairs:
                logger.info(f"_handle_find: transliteration fallback: '{original}' -> '{trans}'")
            for _, trans in trans_pairs:
                results = kp_client.search(trans, search_year, type_filter=tv_type_filter)
                if results:
                    successful_candidate = trans
                    logger.info(f"_handle_find: found {len(results)} results after transliteration: '{trans}'")
                    break
            if not results and search_year:
                for _, trans in trans_pairs:
                    results = kp_client.search(trans, None, type_filter=tv_type_filter)
                    if results:
                        successful_candidate = trans
                        logger.info(
                            f"_handle_find: found {len(results)} results after transliteration (no year): '{trans}'"
                        )
                        break

    if (
        settings.auto_select_exact_match
        and len(results) == 1
        and search_year is not None
        and successful_candidate is not None
        and results[0].title_ru is not None
        and results[0].title_ru.lower() == successful_candidate.lower()
        and results[0].year is not None
        and str(results[0].year) == str(search_year)
    ):
        logger.info(f"_handle_find: auto-selected exact match: kp_id={results[0].kinopoisk_id}")

    if not results and _kp_unavailable:
        logger.error(
            f"_handle_find: API unavailable during find for title='{title}'"
        )
        xbmc.executebuiltin(
            'Notification("TV Scraper", '
            '"Кинопоиск недоступен, поиск невозможен", 5000)'
        )

    for result in results:
        label = f"{result.title_ru} ({result.year})" if result.year else result.title_ru
        listitem = xbmcgui.ListItem(label, offscreen=True)
        infotag = listitem.getVideoInfoTag()
        infotag.setTitle(result.title_ru)
        infotag.setOriginalTitle(result.title_original)
        infotag.setYear(result.year)

        if result.poster_url:
            listitem.setArt({"thumb": result.poster_url})

        uniqueids = {}
        if result.kinopoisk_id:
            uniqueids["kinopoisk"] = str(result.kinopoisk_id)
        if result.imdb_id:
            uniqueids["imdb"] = result.imdb_id

        url = json.dumps(uniqueids)
        xbmcplugin.addDirectoryItem(
            handle=handle,
            url=url,
            listitem=listitem,
            isFolder=True
        )

    logger.info(f"_handle_find: added {len(results)} results to directory")


def _handle_getdetails(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> bool:
    """Fetch TV show details from Kinopoisk and enrich with OMDb ratings."""
    global _kp_unavailable, _kp_unavailable_notified, _stale_cache_notified, _nfo_fallback_notified

    logger.info(f"_handle_getdetails: params keys={list(params.keys())}")

    kp_id = extract_kinopoisk_id(params, logger)

    if not kp_id:
        imdb_id = extract_imdb_id(params, logger)
        if imdb_id:
            logger.info(f"_handle_getdetails: no kp_id, trying IMDB lookup: {imdb_id}")
            kp_id = search_kp_by_imdb(imdb_id, settings, logger)

    if not kp_id:
        logger.error("_handle_getdetails: no Kinopoisk ID available")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return False

    if not settings.kinopoisk_api_key:
        logger.error("_handle_getdetails: Kinopoisk API key not configured")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return False

    video_file_path = xbmc.getInfoLabel("ListItem.Path") or ""
    if video_file_path:
        logger.info(f"_handle_getdetails: video_file_path='{video_file_path}'")
    else:
        logger.info("_handle_getdetails: video_file_path is empty")

    if settings.enable_duplicate_detection:
        path_settings = video_file_path
        if path_settings:
            dup_addon_id = xbmcaddon.Addon().getAddonInfo('id')
            tracker = DuplicateTracker(dup_addon_id, logger)
            existing_path = tracker.check_and_update(kp_id, path_settings)
            if existing_path:
                basename = os.path.basename(existing_path.rstrip("/\\")) or existing_path
                xbmcgui.Dialog().notification(
                    "TV Scraper",
                    f"Дубль KP {kp_id}: уже у {basename}",
                    xbmcgui.NOTIFICATION_WARNING,
                    7000,
                )
        else:
            logger.info("_handle_getdetails: duplicate tracking skipped: empty path")

    kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
    addon_id = xbmcaddon.Addon().getAddonInfo('id')
    cache = FileCache(addon_id, logger)

    cache_key_details = f"kp_details_{kp_id}"
    cached_raw = cache.get(cache_key_details)
    details_raw = None  # type: Optional[dict]
    from_fallback = False
    nfo_tvshow = None  # type: Optional[TVShowDetails]

    if cached_raw is not None:
        details_raw = cached_raw
        details = kp_client.parse_details(cached_raw, genre_language=settings.genre_language)
        logger.info(f"_handle_getdetails: loaded details from cache for kp_id={kp_id}")
    else:
        if _kp_unavailable:
            raw = kp_client.fetch_details_raw_degraded(kp_id)
        else:
            raw = kp_client.fetch_details_raw(kp_id)

        if raw:
            details_raw = raw
            cache.put(cache_key_details, raw)
            details = kp_client.parse_details(raw, genre_language=settings.genre_language)
            _kp_unavailable = False
        else:
            _kp_unavailable = True
            logger.warning(
                f"_handle_getdetails: API unavailable for kp_id={kp_id}, trying fallbacks"
            )

            stale_raw = cache.get_stale(cache_key_details)
            if stale_raw is not None:
                details_raw = stale_raw
                details = kp_client.parse_details(stale_raw, genre_language=settings.genre_language)
                from_fallback = True
                logger.warning(
                    f"_handle_getdetails: serving stale cache for kp_id={kp_id}"
                )
                if not _stale_cache_notified:
                    xbmc.executebuiltin(
                        'Notification("TV Scraper", '
                        '"Данные из кэша (устаревшие)", 5000)'
                    )
                    _stale_cache_notified = True
            else:
                nfo_tvshow = _try_nfo_fallback_tvshow(
                    kp_id, video_file_path, logger
                )
                if nfo_tvshow is not None:
                    details = None
                    from_fallback = True
                    logger.warning(
                        f"_handle_getdetails: serving NFO data for kp_id={kp_id}"
                    )
                    if not _nfo_fallback_notified:
                        xbmc.executebuiltin(
                            'Notification("TV Scraper", '
                            '"Данные из NFO-файла", 5000)'
                        )
                        _nfo_fallback_notified = True
                else:
                    logger.error(
                        f"_handle_getdetails: all fallbacks failed for kp_id={kp_id}"
                    )
                    if not _kp_unavailable_notified:
                        xbmc.executebuiltin(
                            'Notification("TV Scraper", '
                            '"Кинопоиск недоступен", 5000)'
                        )
                        _kp_unavailable_notified = True
                    xbmcplugin.setResolvedUrl(
                        handle, False, xbmcgui.ListItem(offscreen=True)
                    )
                    return False

    # BL-60: premiere date from distributions
    premiere_date = ""
    if not from_fallback and details is not None:
        try:
            distributions_cache_key = f"kp_distributions_{kp_id}"
            cached_distributions = cache.get(distributions_cache_key)
            if cached_distributions is not None:
                logger.info(f"_handle_getdetails: distributions from cache for kp_id={kp_id}")
                premiere_date = kp_client.parse_premiere_date(cached_distributions)
            else:
                distributions_raw = kp_client.fetch_distributions_raw(kp_id)
                if distributions_raw is not None:
                    cache.put(distributions_cache_key, distributions_raw)
                    premiere_date = kp_client.parse_premiere_date(distributions_raw)
                else:
                    logger.info(f"_handle_getdetails: no distributions data for kp_id={kp_id}")
        except Exception as exc:
            logger.warning(f"_handle_getdetails: distributions error for kp_id={kp_id}: {exc}")

    # Map MovieDetails -> TVShowDetails (or use NFO fallback directly)
    if nfo_tvshow is not None:
        tvshow = nfo_tvshow
    else:
        tvshow = TVShowDetails(
            kinopoisk_id=details.kinopoisk_id,
            imdb_id=details.imdb_id,
            title_ru=details.title_ru,
            title_original=details.title_original,
            tagline=details.tagline,
            year=details.year,
            plot=details.plot,
            plot_outline=details.plot_outline,
            runtime=details.runtime,
            mpaa=details.mpaa,
            genres=details.genres,
            countries=details.countries,
            studios=details.studios,
            ratings=details.ratings,
            artwork=details.artwork,
            premiere_date=premiere_date,
        )

    if not from_fallback or not tvshow.directors:
        cache_key_staff = f"kp_staff_{kp_id}"
        cached_staff = cache.get(cache_key_staff)
        if cached_staff is not None:
            directors, writers, cast = kp_client.parse_staff(cached_staff)
            logger.info(f"_handle_getdetails: loaded staff from cache for kp_id={kp_id}")
        elif not from_fallback:
            raw_staff = kp_client.fetch_staff_raw(kp_id)
            if raw_staff is not None:
                cache.put(cache_key_staff, raw_staff)
                directors, writers, cast = kp_client.parse_staff(raw_staff)
            else:
                directors, writers, cast = [], [], []
        elif _kp_unavailable:
            stale_staff = cache.get_stale(cache_key_staff)
            if stale_staff is not None:
                directors, writers, cast = kp_client.parse_staff(stale_staff)
                logger.info(f"_handle_getdetails: loaded staff from stale cache for kp_id={kp_id}")
            else:
                directors, writers, cast = [], [], []
        else:
            raw_staff = kp_client.fetch_staff_raw_degraded(kp_id)
            if raw_staff is not None:
                cache.put(cache_key_staff, raw_staff)
                directors, writers, cast = kp_client.parse_staff(raw_staff)
            else:
                stale_staff = cache.get_stale(cache_key_staff)
                if stale_staff is not None:
                    directors, writers, cast = kp_client.parse_staff(stale_staff)
                else:
                    directors, writers, cast = [], [], []
        tvshow.directors = directors
        tvshow.writers = writers
        tvshow.cast = cast
    else:
        logger.info(f"_handle_getdetails: staff from NFO fallback for kp_id={kp_id}")

    _resolve_imdb_via_wikidata(tvshow, kp_id, cache, settings, logger)

    _enrich_tvshow_with_omdb(tvshow, settings, logger, cache)

    # BL-18: Mini-series detection
    content_type = (details_raw or {}).get("type", "")
    tvshow.is_miniseries = (content_type == "MINI_SERIES")
    if tvshow.is_miniseries:
        tag = "Мини-сериал" if settings.genre_language == "ru" else "Mini-Series"
        if tag not in tvshow.tags:
            tvshow.tags.append(tag)
        logger.info(f"_handle_getdetails: mini-series detected, tag='{tag}'")
    else:
        logger.debug(f"_handle_getdetails: content_type='{content_type}', not mini-series")

    # --- BL-38: TV show status ---
    show_status = ""
    if settings.use_tvmaze and (tvshow.imdb_id or tvshow.title_original):
        try:
            tvmaze_status = TvmazeClient(logger)
            show_status = tvmaze_status.get_show_status(
                tvshow.imdb_id, title_original=tvshow.title_original
            )
            if show_status:
                logger.info(f"_handle_getdetails: status from TVMaze: '{show_status}'")
        except Exception as exc:
            logger.warning(f"_handle_getdetails: TVMaze status error: {exc}")

    if not show_status:
        show_status = map_production_status(details_raw or {}, logger)
        if show_status:
            logger.info(f"_handle_getdetails: status from KP fallback: '{show_status}'")

    if show_status:
        tvshow.status = show_status
    else:
        logger.debug(f"_handle_getdetails: no status resolved for kp_id={kp_id}")
    # --- end BL-38 ---

    # --- BL-09: YouTube trailer ---
    if settings.enable_trailers and not tvshow.trailer_url:
        cache_key_videos = f"kp_videos_{kp_id}"
        cached_videos = cache.get(cache_key_videos)

        if cached_videos is not None:
            trailer_url = kp_client.parse_trailer_url(cached_videos)
            logger.info(f"_handle_getdetails: loaded videos from cache for kp_id={kp_id}")
        elif from_fallback and _kp_unavailable:
            stale_videos = cache.get_stale(cache_key_videos)
            if stale_videos is not None:
                trailer_url = kp_client.parse_trailer_url(stale_videos)
                logger.info(f"_handle_getdetails: loaded videos from stale cache for kp_id={kp_id}")
            else:
                trailer_url = ""
                logger.info(f"_handle_getdetails: no cached videos for kp_id={kp_id}")
        else:
            if _kp_unavailable:
                raw_videos = kp_client.fetch_videos_raw_degraded(kp_id)
            else:
                raw_videos = kp_client.fetch_videos_raw(kp_id)

            if raw_videos is not None:
                cache.put(cache_key_videos, raw_videos)
                trailer_url = kp_client.parse_trailer_url(raw_videos)
            else:
                stale_videos = cache.get_stale(cache_key_videos)
                if stale_videos is not None:
                    trailer_url = kp_client.parse_trailer_url(stale_videos)
                    logger.info(f"_handle_getdetails: videos from stale cache for kp_id={kp_id}")
                else:
                    trailer_url = ""

        if trailer_url:
            tvshow.trailer_url = trailer_url
            logger.info(f"_handle_getdetails: Trailer set: {trailer_url.split('videoid=')[-1]}")
        else:
            logger.warning(f"_handle_getdetails: No YouTube trailer found for kp_id={kp_id}")
    elif not settings.enable_trailers:
        logger.info("_handle_getdetails: Trailers disabled, skipping")
    # --- end BL-09 ---

    # --- BL-69: FanArt.tv artwork for TV shows ---
    fanart_show_art: dict[str, str] = {}
    fanart_season_art: dict[int, dict[str, str]] = {}
    if settings.use_fanart and settings.fanart_api_key:
        if not settings.use_tvmaze:
            logger.debug("_handle_getdetails: TVMaze disabled, skipping FanArt.tv")
        elif not tvshow.imdb_id and not tvshow.title_original:
            logger.debug("_handle_getdetails: no IMDB ID or title for FanArt.tv")
        else:
            try:
                tvmaze_fa = TvmazeClient(logger)
                tvdb_id = tvmaze_fa.get_tvdb_id(tvshow.imdb_id, tvshow.title_original)
                if tvdb_id:
                    fc = FanartClient(settings.fanart_api_key, logger)
                    fanart_show_art, fanart_season_art = fc.get_tv_art(tvdb_id)
                    if fanart_show_art or fanart_season_art:
                        logger.info(
                            f"_handle_getdetails: FanArt.tv returned {len(fanart_show_art)} show types + "
                            f"{len(fanart_season_art)} seasons for tvdb_id={tvdb_id}"
                        )
                else:
                    logger.debug("_handle_getdetails: no TVDB ID from TVMaze")
            except Exception as exc:
                logger.warning(f"_handle_getdetails: FanArt.tv error: {exc}")
    elif settings.use_fanart and not settings.fanart_api_key:
        logger.debug("_handle_getdetails: FanArt.tv API key not configured")
    # --- end BL-69 ---

    # Build episodeguide JSON
    episodeguide = json.dumps({
        "kinopoisk_id": tvshow.kinopoisk_id,
        "imdb_id": tvshow.imdb_id,
        "title_original": tvshow.title_original,
    })

    listitem = xbmcgui.ListItem(offscreen=True)
    _apply_tvshow_details_to_listitem(tvshow, listitem, settings, logger, fanart_show_art)

    infotag = listitem.getVideoInfoTag()

    # --- BL-40/63: Season artwork and names ---
    _apply_season_art(tvshow.imdb_id, infotag, settings, logger)
    # --- end BL-40/63 ---

    # --- BL-69: FanArt.tv season-level artwork ---
    for season_num, season_arts in fanart_season_art.items():
        for art_type, art_url in season_arts.items():
            infotag.addAvailableArtwork(art_url, art_type, season=season_num)
            logger.debug(f"_handle_getdetails: FanArt.tv season {season_num} addAvailableArtwork({art_type})")
    # --- end BL-69 ---

    infotag.setEpisodeGuide(episodeguide)

    write_tvshow_nfo(tvshow, video_file_path, settings, logger)

    xbmcplugin.setResolvedUrl(handle, True, listitem)

    logger.info(
        f"_handle_getdetails: success for kp_id={kp_id}, title='{tvshow.title_ru}', "
        f"episodeguide set"
    )
    return True


def _handle_getepisodelist(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> None:
    """Return list of all episodes so Kodi knows what exists."""
    url_str = params.get("url", "")
    logger.info(f"_handle_getepisodelist: url={url_str[:100]}")

    try:
        guide = json.loads(url_str)
    except (json.JSONDecodeError, TypeError):
        try:
            guide = {"kinopoisk_id": int(url_str)}
            logger.info(f"_handle_getepisodelist: plain kp_id from url: {url_str}")
        except (ValueError, TypeError):
            logger.error("_handle_getepisodelist: invalid episodeguide JSON")
            return

    if isinstance(guide, (int, float)):
        guide = {"kinopoisk_id": int(guide)}
        logger.info(f"_handle_getepisodelist: legacy episodeguide, kp_id={guide['kinopoisk_id']}")
    elif isinstance(guide, str):
        try:
            guide = {"kinopoisk_id": int(guide)}
            logger.info(f"_handle_getepisodelist: legacy episodeguide (str), kp_id={guide['kinopoisk_id']}")
        except ValueError:
            logger.error(f"_handle_getepisodelist: unrecognized episodeguide format: {url_str[:100]}")
            return

    kp_id = int(guide.get("kinopoisk_id", 0))
    if not kp_id:
        imdb_id = guide.get("imdb_id") or guide.get("imdb") or ""
        if imdb_id:
            logger.info(f"_handle_getepisodelist: no kinopoisk_id, resolving from imdb_id={imdb_id}")
            kp_id = search_kp_by_imdb(imdb_id, settings, logger)
        if not kp_id:
            logger.error(
                f"_handle_getepisodelist: no kinopoisk_id in guide and IMDB resolve failed (imdb_id='{imdb_id}')"
            )
            return
        logger.info(f"_handle_getepisodelist: resolved kp_id={kp_id} from imdb_id={imdb_id}")

    kp_client = None
    cache = None
    seasons = _cache_get(kp_id, logger)
    if seasons is None:
        if not settings.kinopoisk_api_key:
            logger.error("_handle_getepisodelist: Kinopoisk API key not configured")
            return

        addon_id = xbmcaddon.Addon().getAddonInfo('id')
        cache = FileCache(addon_id, logger)
        file_cache_key = f"kp_seasons_{kp_id}"
        cached_raw = cache.get(file_cache_key)

        kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
        if cached_raw is not None:
            seasons = kp_client.parse_seasons(cached_raw)
            if seasons:
                logger.info(f"_handle_getepisodelist: loaded seasons from file cache for kp_id={kp_id}")
            else:
                cache.delete(file_cache_key)
                logger.info(f"_handle_getepisodelist: deleted empty seasons cache for kp_id={kp_id}")
        else:
            raw = kp_client.fetch_seasons_raw(kp_id)
            if raw is not None:
                seasons = kp_client.parse_seasons(raw)
                if seasons:
                    cache.put(file_cache_key, raw)
            else:
                seasons = []
        _cache_put(kp_id, seasons, logger)

    if not seasons:
        if not kp_client and settings.kinopoisk_api_key:
            kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
        if not cache:
            addon_id = xbmcaddon.Addon().getAddonInfo('id')
            cache = FileCache(addon_id, logger)
        if kp_client:
            kp_id, seasons = _fallback_seasons_search(
                kp_id, guide, kp_client, settings, logger, cache
            )

    imdb_id = guide.get("imdb_id") or guide.get("imdb") or ""
    title_original = guide.get("title_original", "")
    total_episodes = 0
    for season in seasons:
        for ep in season.episodes:
            listitem = xbmcgui.ListItem(offscreen=True)
            infotag = listitem.getVideoInfoTag()
            infotag.setSeason(season.number)
            infotag.setEpisode(ep.episode_number)
            if ep.release_date:
                infotag.setFirstAired(ep.release_date)
            ep_url = json.dumps({
                "kinopoisk_id": kp_id,
                "imdb_id": imdb_id,
                "title_original": title_original,
                "season": season.number,
                "episode": ep.episode_number,
            })
            xbmcplugin.addDirectoryItem(
                handle=handle, url=ep_url, listitem=listitem, isFolder=False
            )
            total_episodes += 1

    logger.info(
        f"_handle_getepisodelist: added {total_episodes} episodes "
        f"across {len(seasons)} seasons for kp_id={kp_id}"
    )


def _handle_getepisodedetails(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> bool:
    """Fetch individual episode details from Kinopoisk seasons data with caching."""
    url_str = params.get("url", "")

    try:
        guide = json.loads(url_str)
    except (json.JSONDecodeError, TypeError):
        try:
            guide = {"kinopoisk_id": int(url_str)}
            logger.info(f"_handle_getepisodedetails: plain kp_id from url: {url_str}")
        except (ValueError, TypeError):
            logger.error("_handle_getepisodedetails: invalid episodeguide JSON")
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
            return False

    if isinstance(guide, (int, float)):
        guide = {"kinopoisk_id": int(guide)}
        logger.info(f"_handle_getepisodedetails: legacy episodeguide, kp_id={guide['kinopoisk_id']}")
    elif isinstance(guide, str):
        try:
            guide = {"kinopoisk_id": int(guide)}
            logger.info(f"_handle_getepisodedetails: legacy episodeguide (str), kp_id={guide['kinopoisk_id']}")
        except ValueError:
            logger.error(f"_handle_getepisodedetails: unrecognized episodeguide format: {url_str[:100]}")
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
            return False

    kp_id = int(guide.get("kinopoisk_id", 0))
    imdb_id = guide.get("imdb_id", "")
    title_original = guide.get("title_original", "")
    season_num = int(guide.get("season", 0))
    episode_num = int(guide.get("episode", 0))

    # Backward compat: old episodeguides lack title_original and imdb_id
    if not title_original and not imdb_id and settings.use_tvmaze and kp_id:
        if settings.kinopoisk_api_key:
            try:
                kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
                details = kp_client.get_details(kp_id)
                if details:
                    title_original = details.title_original or ""
                    imdb_id = details.imdb_id or ""
                    logger.info(
                        f"_handle_getepisodedetails: resolved from KP: "
                        f"title_original='{title_original}', imdb_id='{imdb_id}'"
                    )
            except Exception as exc:
                logger.warning(f"_handle_getepisodedetails: KP details fallback error: {exc}")

    logger.info(f"_handle_getepisodedetails: S{season_num:02d}E{episode_num:02d}, kp_id={kp_id}")

    if not kp_id:
        logger.error("_handle_getepisodedetails: no kinopoisk_id in guide")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return False

    kp_client = None
    cache = None
    seasons = _cache_get(kp_id, logger)
    if seasons is None:
        if not settings.kinopoisk_api_key:
            logger.error("_handle_getepisodedetails: Kinopoisk API key not configured")
            xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
            return False

        addon_id = xbmcaddon.Addon().getAddonInfo('id')
        cache = FileCache(addon_id, logger)
        file_cache_key = f"kp_seasons_{kp_id}"
        cached_raw = cache.get(file_cache_key)

        kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
        if cached_raw is not None:
            seasons = kp_client.parse_seasons(cached_raw)
            if seasons:
                logger.info(f"_handle_getepisodedetails: loaded seasons from file cache for kp_id={kp_id}")
            else:
                cache.delete(file_cache_key)
                logger.info(f"_handle_getepisodedetails: deleted empty seasons cache for kp_id={kp_id}")
        else:
            raw = kp_client.fetch_seasons_raw(kp_id)
            if raw is not None:
                seasons = kp_client.parse_seasons(raw)
                if seasons:
                    cache.put(file_cache_key, raw)
            else:
                seasons = []
        _cache_put(kp_id, seasons, logger)

    if not seasons:
        if not kp_client and settings.kinopoisk_api_key:
            kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
        if not cache:
            addon_id = xbmcaddon.Addon().getAddonInfo('id')
            cache = FileCache(addon_id, logger)
        if kp_client:
            kp_id, seasons = _fallback_seasons_search(
                kp_id, guide, kp_client, settings, logger, cache
            )

    episode = _find_episode(seasons, season_num, episode_num)
    if episode is None:
        logger.warning(
            f"_handle_getepisodedetails: episode S{season_num:02d}E{episode_num:02d} "
            f"not found for kp_id={kp_id}"
        )
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return False

    # OMDb episode rating (optional)
    imdb_rating = None
    imdb_votes = 0
    if settings.omdb_api_key and imdb_id:
        try:
            omdb = OmdbClient(settings.omdb_api_key, logger)
            omdb_result = omdb.get_episode_rating(imdb_id, season_num, episode_num)
            if omdb_result is not None:
                imdb_rating, imdb_votes = omdb_result
        except Exception as exc:
            logger.warning(f"_handle_getepisodedetails: OMDb error: {exc}")

    tvmaze: Optional[TvmazeClient] = None
    if settings.use_tvmaze and (imdb_id or title_original):
        tvmaze = TvmazeClient(logger)

    tvmaze_plot = None
    if tvmaze and not episode.synopsis:
        try:
            tvmaze_plot = tvmaze.get_episode_plot(imdb_id, season_num, episode_num, title_original=title_original)
            if tvmaze_plot:
                logger.info(
                    f"_handle_getepisodedetails: TVMaze plot for "
                    f"S{season_num:02d}E{episode_num:02d}, len={len(tvmaze_plot)}"
                )
        except Exception as exc:
            logger.warning(f"_handle_getepisodedetails: TVMaze error: {exc}")

    tvmaze_directors: list[str] = []
    tvmaze_writers: list[str] = []
    if tvmaze:
        try:
            tvmaze_directors, tvmaze_writers = tvmaze.get_episode_crew(
                imdb_id, season_num, episode_num, title_original=title_original
            )
            if tvmaze_directors or tvmaze_writers:
                logger.info(
                    f"_handle_getepisodedetails: TVMaze crew for "
                    f"S{season_num:02d}E{episode_num:02d}, "
                    f"directors={len(tvmaze_directors)}, writers={len(tvmaze_writers)}"
                )
        except Exception as exc:
            logger.warning(f"_handle_getepisodedetails: TVMaze crew error: {exc}")

    tvmaze_thumb_url = ""
    tvmaze_thumb_preview = ""
    if tvmaze:
        try:
            tvmaze_thumb_url, tvmaze_thumb_preview = tvmaze.get_episode_image(
                imdb_id, season_num, episode_num, title_original=title_original
            )
            if tvmaze_thumb_url:
                logger.info(
                    f"_handle_getepisodedetails: TVMaze thumbnail for "
                    f"S{season_num:02d}E{episode_num:02d}"
                )
        except Exception as exc:
            logger.warning(f"_handle_getepisodedetails: TVMaze image error: {exc}")

    listitem = xbmcgui.ListItem(offscreen=True)
    _apply_episode_to_listitem(
        episode, season_num, episode_num, imdb_rating, listitem, settings, logger,
        tvmaze_plot=tvmaze_plot, imdb_votes=imdb_votes,
        tvmaze_directors=tvmaze_directors, tvmaze_writers=tvmaze_writers,
        tvmaze_thumb_url=tvmaze_thumb_url, tvmaze_thumb_preview=tvmaze_thumb_preview,
    )
    xbmcplugin.setResolvedUrl(handle, True, listitem)

    logger.info(f"_handle_getepisodedetails: success S{season_num:02d}E{episode_num:02d} title='{episode.title_ru}'")
    return True


def _handle_nfo(params: dict, handle: int, logger: Logger) -> None:
    """Parse NFO content and extract Kinopoisk/IMDB IDs."""
    nfo_content = params.get("nfo", "")
    logger.info(f"_handle_nfo: received NFO content, length={len(nfo_content)}")

    if not nfo_content:
        logger.warning("_handle_nfo: empty NFO content")
        return

    parser = NfoParser(logger)
    result = parser.parse(nfo_content)

    if result.kinopoisk_id:
        logger.info(f"_handle_nfo: found kinopoisk_id={result.kinopoisk_id}")
        listitem = xbmcgui.ListItem(offscreen=True)
        infotag = listitem.getVideoInfoTag()
        infotag.setUniqueIDs({"kinopoisk": str(result.kinopoisk_id)}, "kinopoisk")
        url = json.dumps({"kinopoisk": str(result.kinopoisk_id)})
        xbmcplugin.addDirectoryItem(
            handle=handle, url=url, listitem=listitem, isFolder=True
        )
    elif result.imdb_id:
        logger.info(f"_handle_nfo: found imdb_id={result.imdb_id}")
        listitem = xbmcgui.ListItem(offscreen=True)
        infotag = listitem.getVideoInfoTag()
        infotag.setUniqueIDs({"imdb": result.imdb_id}, "imdb")
        url = json.dumps({"imdb": result.imdb_id})
        xbmcplugin.addDirectoryItem(
            handle=handle, url=url, listitem=listitem, isFolder=True
        )
    else:
        logger.info("_handle_nfo: no recognized IDs in NFO")


# ---------------------------------------------------------------------------
# Season cache helpers (thread-safe, LRU-like eviction)
# ---------------------------------------------------------------------------

def _cache_get(kp_id: int, logger: Logger) -> Optional[list[Season]]:
    """Retrieve cached seasons for a given kp_id. Returns None on cache miss."""
    global _cache_access_counter
    with _season_cache_lock:
        entry = _season_cache.get(kp_id)
        if entry is not None:
            _cache_access_counter += 1
            entry.access_order = _cache_access_counter
            logger.info(f"season_cache: cache hit for kp_id={kp_id}")
            return entry.seasons
    logger.info(f"season_cache: cache miss for kp_id={kp_id}")
    return None


def _fallback_seasons_search(
    kp_id: int,
    guide: dict,
    kp_client: KinopoiskClient,
    settings: SettingsManager,
    logger: Logger,
    cache: Optional[FileCache] = None,
) -> tuple:
    logger.info(f"_fallback_seasons_search: starting for kp_id={kp_id}")

    imdb_id = guide.get("imdb_id", "")
    if imdb_id:
        new_kp_id = search_kp_by_imdb(imdb_id, settings, logger)
        if new_kp_id and new_kp_id != kp_id:
            raw = kp_client.fetch_seasons_raw(new_kp_id)
            if raw is not None:
                if cache:
                    cache.put(f"kp_seasons_{new_kp_id}", raw)
                new_seasons = kp_client.parse_seasons(raw)
                if new_seasons:
                    _cache_put(new_kp_id, new_seasons, logger)
                    logger.info(
                        f"_fallback_seasons_search: strategy=imdb_lookup, "
                        f"imdb_id='{imdb_id}', found kp_id={new_kp_id}"
                    )
                    return new_kp_id, new_seasons

    title = guide.get("title_original", "")
    if title:
        tv_type_filter = ["TV_SERIES", "MINI_SERIES", "TV_SHOW"]
        results = kp_client.search(title, None, type_filter=tv_type_filter)
        if results and results[0].kinopoisk_id != kp_id:
            new_kp_id = results[0].kinopoisk_id
            raw = kp_client.fetch_seasons_raw(new_kp_id)
            if raw is not None:
                if cache:
                    cache.put(f"kp_seasons_{new_kp_id}", raw)
                new_seasons = kp_client.parse_seasons(raw)
                if new_seasons:
                    _cache_put(new_kp_id, new_seasons, logger)
                    logger.info(
                        f"_fallback_seasons_search: strategy=title_search, "
                        f"title='{title}', found kp_id={new_kp_id}"
                    )
                    return new_kp_id, new_seasons

    if not title and not imdb_id:
        fallback_cache_key = f"kp_type_{kp_id}"
        if cache:
            cached_type = cache.get(fallback_cache_key)
            if cached_type is not None:
                film_type = cached_type.get("type", "")
                logger.info(
                    f"_fallback_seasons_search: kp_id={kp_id} cached as type='{film_type}'"
                )
                if film_type not in ("TV_SERIES", "MINI_SERIES", "TV_SHOW"):
                    return kp_id, []
                else:
                    logger.info(
                        f"_fallback_seasons_search: kp_id={kp_id} is type='{film_type}' "
                        f"but API has no season data"
                    )
                    return kp_id, []

        data = kp_client.fetch_details_raw(kp_id)
        if data:
            film_type = data.get("type", "")
            if cache:
                cache.put(fallback_cache_key, {"type": film_type})
            if film_type not in ("TV_SERIES", "MINI_SERIES", "TV_SHOW"):
                logger.warning(
                    f"_fallback_seasons_search: kp_id={kp_id} is type='{film_type}', "
                    f"not a TV series. Rescan required."
                )
                xbmc.executebuiltin(
                    f'Notification("TV Scraper", '
                    f'"ID {kp_id} — не сериал. Пересканируйте.", 7000)'
                )
                if cache:
                    cache.delete(f"kp_seasons_{kp_id}")
            else:
                logger.info(
                    f"_fallback_seasons_search: kp_id={kp_id} is type='{film_type}' "
                    f"but API has no season data"
                )

    logger.info(f"_fallback_seasons_search: all strategies failed for kp_id={kp_id}")
    return kp_id, []


def _cache_put(kp_id: int, seasons: list[Season], logger: Logger) -> None:
    """Store seasons in cache with LRU eviction when cache exceeds max size."""
    global _cache_access_counter
    with _season_cache_lock:
        _cache_access_counter += 1
        _season_cache[kp_id] = _CacheEntry(
            seasons=seasons,
            timestamp=time.monotonic(),
            access_order=_cache_access_counter,
        )
        if len(_season_cache) > _CACHE_MAX_SIZE:
            oldest_key = min(_season_cache, key=lambda k: _season_cache[k].access_order)
            del _season_cache[oldest_key]
            logger.debug(f"season_cache: evicted kp_id={oldest_key} (cache size exceeded {_CACHE_MAX_SIZE})")
    total_eps = sum(len(s.episodes) for s in seasons)
    logger.info(f"season_cache: stored kp_id={kp_id}, {len(seasons)} seasons, {total_eps} episodes")


# ---------------------------------------------------------------------------
# Episode lookup
# ---------------------------------------------------------------------------

def _find_episode(seasons: list[Season], season_num: int, episode_num: int) -> Optional[Episode]:
    """Find a specific episode by season and episode number."""
    for season in seasons:
        if season.number == season_num:
            for ep in season.episodes:
                if ep.episode_number == episode_num:
                    return ep
    return None


# ---------------------------------------------------------------------------
# ListItem mapping helpers
# ---------------------------------------------------------------------------

def _apply_tvshow_details_to_listitem(
    details: TVShowDetails,
    listitem: xbmcgui.ListItem,
    settings: SettingsManager,
    logger: Logger,
    fanart_art: dict[str, str] | None = None,
) -> None:
    """Map TVShowDetails fields onto a Kodi ListItem via VideoInfoTag."""
    logger.debug("_apply_tvshow_details_to_listitem: mapping details to ListItem")

    infotag = listitem.getVideoInfoTag()

    infotag.setTitle(details.title_ru)
    infotag.setOriginalTitle(details.title_original)
    infotag.setPlot(details.plot)
    infotag.setTagLine(details.tagline)

    # BL-61: plot outline (shortDescription from KP)
    if details.plot_outline:
        infotag.setPlotOutline(details.plot_outline)
        logger.info(f"_apply_tvshow_details_to_listitem: setPlotOutline (len={len(details.plot_outline)})")

    # BL-60: premiere date from distributions
    if details.premiere_date:
        infotag.setPremiered(details.premiere_date)
        logger.info(f"_apply_tvshow_details_to_listitem: setPremiered={details.premiere_date}")

    infotag.setYear(details.year)
    infotag.setDuration(details.runtime * 60)
    infotag.setMpaa(details.mpaa)

    if details.original_language:
        try:
            infotag.setOriginalLanguage(details.original_language)
            logger.info(f"_apply_tvshow_details: setOriginalLanguage('{details.original_language}')")
        except AttributeError:
            logger.debug(
                f"setOriginalLanguage not available (Kodi < v22), "
                f"original_language='{details.original_language}' skipped"
            )

    infotag.setGenres(details.genres)
    infotag.setCountries(details.countries)
    infotag.setStudios(details.studios)

    if details.tags:
        infotag.setTags(details.tags)
        logger.debug(
            f"_apply_tvshow_details_to_listitem: setTags({details.tags})"
        )

    if details.status:
        infotag.setTvShowStatus(details.status)
        logger.info(f"_apply_tvshow_details_to_listitem: setTvShowStatus='{details.status}'")

    uniqueids = {}
    default_id = "kinopoisk"
    if details.kinopoisk_id:
        uniqueids["kinopoisk"] = str(details.kinopoisk_id)
    if details.imdb_id:
        uniqueids["imdb"] = details.imdb_id
        infotag.setIMDBNumber(details.imdb_id)
    infotag.setUniqueIDs(uniqueids, default_id)

    preferred_source = settings.preferred_rating_source
    kodi_ratings = {}
    for r in details.ratings:
        kodi_ratings[r.source.value] = (r.value, r.votes)
    infotag.setRatings(kodi_ratings, preferred_source.value)

    actor_lang = settings.actor_name_language

    infotag.setDirectors([p.display_name(actor_lang) for p in details.directors])
    infotag.setWriters([p.display_name(actor_lang) for p in details.writers])

    kodi_cast = []
    for person in details.cast:
        kodi_cast.append(xbmc.Actor(
            person.display_name(actor_lang),
            person.role,
            person.order,
            person.photo_url
        ))
    infotag.setCast(kodi_cast)

    if actor_lang == "en":
        no_en = [p for p in details.cast if not p.name_en]
        if no_en:
            logger.debug(
                f"_handle_getdetails: {len(no_en)} actors without English name, "
                f"fallback to Russian"
            )

    for art in details.artwork:
        if art.artwork_type == ArtworkType.POSTER:
            infotag.addAvailableArtwork(art.url, "poster")

    fanart_list = []
    for art in details.artwork:
        if art.artwork_type == ArtworkType.FANART:
            fanart_list.append({
                "image": art.url,
                "preview": art.preview_url or art.url
            })
    if fanart_list:
        listitem.setAvailableFanart(fanart_list)

    # --- BL-69: FanArt.tv show-level artwork ---
    if fanart_art:
        for art_type, art_url in fanart_art.items():
            infotag.addAvailableArtwork(art_url, art_type)
            logger.debug(f"_apply_tvshow_details: FanArt.tv addAvailableArtwork({art_type})")
    # --- end BL-69 ---

    if details.trailer_url:
        infotag.setTrailer(details.trailer_url)
        logger.debug(f"_apply_tvshow_details_to_listitem: setTrailer('{details.trailer_url}')")

    logger.debug(
        f"_apply_tvshow_details_to_listitem: mapped '{details.title_ru}' "
        f"with {len(details.ratings)} ratings, {len(details.cast)} cast"
    )


def _apply_season_art(
    imdb_id: str,
    infotag,
    settings: SettingsManager,
    logger: Logger,
) -> None:
    if not settings.use_tvmaze:
        logger.debug("_apply_season_art: use_tvmaze=false, skipping")
        return
    if not settings.use_season_art:
        logger.debug("_apply_season_art: use_season_art=false, skipping")
        return
    if not imdb_id:
        logger.warning("_apply_season_art: no IMDB ID, cannot fetch season art")
        return

    logger.info(f"_apply_season_art: fetching season art for imdb_id={imdb_id}")

    tvmaze = TvmazeClient(logger)

    show_id = tvmaze.lookup_show(imdb_id)
    if show_id is None:
        logger.warning(f"_apply_season_art: TVMaze show not found for imdb_id={imdb_id}")
        return

    seasons = tvmaze.get_seasons(show_id)
    if seasons is None:
        logger.warning(f"_apply_season_art: failed to fetch seasons for show_id={show_id}")
        return
    if not seasons:
        logger.info(f"_apply_season_art: no seasons returned for show_id={show_id}")
        return

    art_count = 0
    for s in seasons:
        infotag.addSeason(s.number, s.name)
        if s.poster_url:
            infotag.addAvailableArtwork(
                s.poster_url,
                arttype="poster",
                preview=s.poster_preview_url,
                season=s.number,
            )
            art_count += 1

    logger.info(
        f"_apply_season_art: applied {len(seasons)} seasons, "
        f"{art_count} posters for imdb_id={imdb_id}"
    )


def _apply_episode_to_listitem(
    episode: Episode,
    season_num: int,
    ep_num: int,
    imdb_rating: Optional[float],
    listitem: xbmcgui.ListItem,
    settings: SettingsManager,
    logger: Logger,
    tvmaze_plot: Optional[str] = None,
    imdb_votes: int = 0,
    tvmaze_directors: Optional[list[str]] = None,
    tvmaze_writers: Optional[list[str]] = None,
    tvmaze_thumb_url: str = "",
    tvmaze_thumb_preview: str = "",
) -> None:
    """Map Episode fields onto a Kodi ListItem via VideoInfoTag."""
    infotag = listitem.getVideoInfoTag()
    title = episode.title_ru or episode.title_en or f"Episode {ep_num}"
    infotag.setTitle(title)
    infotag.setSeason(season_num)
    infotag.setEpisode(ep_num)
    if episode.synopsis:
        infotag.setPlot(episode.synopsis)
    elif tvmaze_plot:
        infotag.setPlot(tvmaze_plot)
    if episode.release_date:
        infotag.setFirstAired(episode.release_date)
    ratings: dict[str, tuple[float, int]] = {}
    if episode.rating and episode.rating > 0:
        ratings["kinopoisk"] = (episode.rating, 0)
    if imdb_rating is not None and imdb_rating > 0:
        ratings["imdb"] = (imdb_rating, imdb_votes or 0)
    if ratings:
        default_source = settings.preferred_rating_source.value
        if default_source not in ratings:
            default_source = next(iter(ratings))
        infotag.setRatings(ratings, default_source)

    directors = tvmaze_directors or []
    if directors:
        infotag.setDirectors(directors)
        logger.debug(
            f"_apply_episode_to_listitem: set {len(directors)} directors "
            f"for S{season_num:02d}E{ep_num:02d}"
        )

    writers = tvmaze_writers or []
    if writers:
        infotag.setWriters(writers)
        logger.debug(
            f"_apply_episode_to_listitem: set {len(writers)} writers "
            f"for S{season_num:02d}E{ep_num:02d}"
        )

    if tvmaze_thumb_url:
        infotag.addAvailableArtwork(tvmaze_thumb_url, "thumb", tvmaze_thumb_preview)
        logger.info(
            f"_apply_episode_to_listitem: addAvailableArtwork(thumb) for "
            f"S{season_num:02d}E{ep_num:02d}"
        )

    logger.debug(
        f"_apply_episode_to_listitem: S{season_num:02d}E{ep_num:02d} "
        f"title='{title}', kp_rating={episode.rating}, imdb_rating={imdb_rating}, "
        f"plot_source={'kp' if episode.synopsis else ('tvmaze' if tvmaze_plot else 'none')}, "
        f"directors={len(directors)}, writers={len(writers)}, "
        f"thumb={'yes' if tvmaze_thumb_url else 'no'}"
    )


# ---------------------------------------------------------------------------
# Artwork fetching
# ---------------------------------------------------------------------------

def _handle_getartwork(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> bool:
    """Fetch additional artwork (posters, fanart) for a TV show."""
    logger.info(f"_handle_getartwork: params keys={list(params.keys())}")

    kp_id = extract_kinopoisk_id(params, logger)

    if not kp_id:
        logger.warning("_handle_getartwork: no Kinopoisk ID for artwork fetch")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return False

    if not settings.kinopoisk_api_key:
        logger.error("_handle_getartwork: Kinopoisk API key not configured")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return False

    kp_client = KinopoiskClient(settings.kinopoisk_api_key, logger)
    artworks = kp_client.get_images(kp_id, ["POSTER", "STILL"])

    listitem = xbmcgui.ListItem(offscreen=True)
    infotag = listitem.getVideoInfoTag()

    poster_count = 0
    for art in artworks:
        if art.artwork_type == ArtworkType.POSTER:
            infotag.addAvailableArtwork(art.url, "poster")
            poster_count += 1

    fanart_list = [
        {"image": art.url, "preview": art.preview_url or art.url}
        for art in artworks
        if art.artwork_type == ArtworkType.FANART
    ]
    if fanart_list:
        listitem.setAvailableFanart(fanart_list)

    xbmcplugin.setResolvedUrl(handle, True, listitem)
    logger.info(
        f"_handle_getartwork: added {poster_count} posters, "
        f"{len(fanart_list)} fanart for kp_id={kp_id}"
    )
    return True


# ---------------------------------------------------------------------------
# OMDb enrichment for TV shows
# ---------------------------------------------------------------------------

def _enrich_tvshow_with_omdb(
    details: TVShowDetails, settings: SettingsManager, logger: Logger,
    cache: Optional[FileCache] = None
) -> None:
    """Enrich TVShowDetails with OMDb ratings and optionally append rating line to plot."""
    # Block 0: Resolve IMDB ID via TVMaze if missing
    if not details.imdb_id and details.title_original and settings.omdb_api_key:
        logger.info(
            f"_enrich_tvshow_with_omdb: imdb_id empty, trying TVMaze for "
            f"title_original='{details.title_original}'"
        )
        try:
            tvmaze = TvmazeClient(logger)
            resolved_imdb = tvmaze.search_imdb_id(details.title_original)
            if resolved_imdb:
                details.imdb_id = resolved_imdb
                logger.info(
                    f"_enrich_tvshow_with_omdb: resolved imdb_id={resolved_imdb} "
                    f"via TVMaze"
                )
        except Exception as exc:
            logger.warning(f"_enrich_tvshow_with_omdb: TVMaze IMDB lookup error: {exc}")

    # Block 1: Fetch OMDb (ALWAYS if key + imdb_id available)
    omdb_ratings = None
    if settings.omdb_api_key and details.imdb_id:
        omdb_cache_key = f"omdb_ratings_{details.imdb_id}"
        cached_omdb = cache.get(omdb_cache_key) if cache else None

        if cached_omdb is not None:
            logger.info(f"_enrich_tvshow_with_omdb: loaded OMDb from cache for imdb_id={details.imdb_id}")
            try:
                omdb = OmdbClient(settings.omdb_api_key, logger)
                omdb_ratings = omdb.parse_ratings(cached_omdb, details.imdb_id)
            except Exception as exc:
                logger.warning(f"_enrich_tvshow_with_omdb: cache parse error: {exc}")
        else:
            logger.info(f"_enrich_tvshow_with_omdb: fetching OMDb for imdb_id={details.imdb_id}")
            try:
                omdb = OmdbClient(settings.omdb_api_key, logger)
                raw_omdb = omdb.fetch_ratings_raw(details.imdb_id)
                if raw_omdb is not None:
                    if cache:
                        cache.put(omdb_cache_key, raw_omdb)
                    omdb_ratings = omdb.parse_ratings(raw_omdb, details.imdb_id)
            except Exception as exc:
                logger.warning(f"_enrich_tvshow_with_omdb: OMDb error: {exc}")

    # Block 2: Add RT/MC to details.ratings (ALWAYS)
    if omdb_ratings:
        existing_sources = {r.source for r in details.ratings}

        rt_value = parse_rt_rating(omdb_ratings.rotten_tomatoes, logger)
        if rt_value is not None and DataSource.ROTTEN_TOMATOES not in existing_sources:
            details.ratings.append(Rating(DataSource.ROTTEN_TOMATOES, rt_value, 0))
            logger.info(f"_enrich_tvshow_with_omdb: added RT rating: {rt_value}")

        mc_value = parse_mc_rating(omdb_ratings.metacritic, logger)
        if mc_value is not None and DataSource.METACRITIC not in existing_sources:
            details.ratings.append(Rating(DataSource.METACRITIC, mc_value, 0))
            logger.info(f"_enrich_tvshow_with_omdb: added MC rating: {mc_value}")

    # Block 2.5: Award tags (gated by enable_award_tags)
    if omdb_ratings and settings.enable_award_tags:
        award_tags = parse_award_tags(omdb_ratings.awards, logger)
        if award_tags:
            details.tags.extend(award_tags)
            logger.info(
                f"_enrich_tvshow_with_omdb: award tags for imdb_id={details.imdb_id}: {award_tags}"
            )
        else:
            logger.info(
                f"_enrich_tvshow_with_omdb: no award tags for imdb_id={details.imdb_id}"
            )
    elif omdb_ratings and not settings.enable_award_tags:
        logger.debug("_enrich_tvshow_with_omdb: enable_award_tags disabled, skipping")

    # Block 3: Text in plot (gated by show_ratings_in_plot)
    if not settings.show_ratings_in_plot:
        logger.debug("_enrich_tvshow_with_omdb: show_ratings_in_plot disabled, skipping plot text")
        return

    parts = []
    for r in details.ratings:
        if r.source == DataSource.KINOPOISK and r.value:
            parts.append(f"KP: {r.value}")
        elif r.source == DataSource.IMDB and r.value:
            parts.append(f"IMDb: {r.value}")

    if omdb_ratings:
        if omdb_ratings.imdb_rating and omdb_ratings.imdb_rating != "N/A":
            parts = [p for p in parts if not p.startswith("IMDb:")]
            parts.append(f"IMDb: {omdb_ratings.imdb_rating}")
        if omdb_ratings.rotten_tomatoes:
            parts.append(f"RT: {omdb_ratings.rotten_tomatoes}")
        if omdb_ratings.metacritic:
            parts.append(f"MC: {omdb_ratings.metacritic}")

    if parts:
        rating_line = " | ".join(parts)
        if details.plot:
            details.plot = f"{details.plot}\n\n{rating_line}"
        else:
            details.plot = rating_line
        logger.info(f"_enrich_tvshow_with_omdb: ratings in plot: {rating_line}")
    else:
        logger.info("_enrich_tvshow_with_omdb: no ratings to display")


if __name__ == "__main__":
    run()
