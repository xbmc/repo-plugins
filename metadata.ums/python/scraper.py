from __future__ import annotations

import json
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs

from cache import FileCache
from duplicate_tracker import DuplicateTracker
from logger import Logger
from settings_manager import SettingsManager
from kinopoisk_api import KinopoiskClient
from omdb_client import OmdbClient, parse_rt_rating, parse_mc_rating, parse_award_tags
from nfo_parser import NfoParser
from models import MovieSearchResult, MovieDetails, Rating, ArtworkType, DataSource
from utils import (
    get_params, clean_title, extract_kinopoisk_id,
    extract_imdb_id, search_kp_by_imdb, transliterate_to_cyrillic,
    extract_franchise_name, extract_alt_title, deduplicate_results,
    _has_cyrillic,
)
from nfo_writer import write_movie_nfo


def _perform_dual_search(
    results: list[MovieSearchResult],
    candidate: str,
    search_year: str | None,
    kp_client: KinopoiskClient,
    type_filter: list[str],
    settings: SettingsManager,
    logger: Logger,
) -> list[MovieSearchResult]:
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


def _try_nfo_fallback_movie(
    kp_id: int, file_path: str, logger: Logger
) -> MovieDetails | None:
    logger.info(
        f"_try_nfo_fallback_movie: attempting NFO fallback for kp_id={kp_id}, "
        f"file_path='{file_path}'"
    )

    if not file_path:
        logger.info("_try_nfo_fallback_movie: empty file_path, cannot locate NFO")
        return None

    root, _ = os.path.splitext(file_path)
    nfo_path = root + ".nfo"

    try:
        if not xbmcvfs.exists(nfo_path):
            logger.info(f"_try_nfo_fallback_movie: NFO not found at {nfo_path}")
            return None

        f = xbmcvfs.File(nfo_path)
        try:
            nfo_content = f.read()
        finally:
            f.close()

        if not nfo_content:
            logger.warning(f"_try_nfo_fallback_movie: empty NFO at {nfo_path}")
            return None

        parser = NfoParser(logger)
        details = parser.parse_full_movie(nfo_content)

        if details is None:
            logger.warning(
                f"_try_nfo_fallback_movie: failed to parse NFO at {nfo_path}"
            )
            return None

        if details.kinopoisk_id == 0:
            details.kinopoisk_id = kp_id

        logger.info(
            f"_try_nfo_fallback_movie: success title='{details.title_ru}' from {nfo_path}"
        )
        return details

    except Exception as e:
        logger.warning(
            f"_try_nfo_fallback_movie: unexpected error for {nfo_path}: {e}"
        )
        return None


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


def run() -> None:
    params = get_params()
    action = params.get("action", "")
    handle = params["handle"]

    settings = SettingsManager()
    logger = Logger(debug_enabled=settings.debug_logging)
    logger.info(f"scraper.run: action={action}, handle={handle}")

    if settings.clear_cache:
        try:
            addon_id = xbmcaddon.Addon().getAddonInfo('id')
            cache = FileCache(addon_id, logger)
            cache.clear()
            tracker = DuplicateTracker(addon_id, logger)
            tracker.clear()
            settings.set_clear_cache(False)
            logger.info("scraper.run: cache cleared by user request")
            xbmc.executebuiltin(
                'Notification("Ultimate Movie Scraper", '
                '"Кэш очищен", 3000)'
            )
        except Exception as e:
            logger.error(f"scraper.run: failed to clear cache: {e}")

    enddir = True
    try:
        if action == "find":
            _handle_find(params, handle, settings, logger)
        elif action == "getdetails":
            enddir = not _handle_getdetails(params, handle, settings, logger)
        elif action == "NfoUrl":
            _handle_nfo(params, handle, logger)
        elif action == "getartwork":
            _handle_getartwork(params, handle, settings, logger)
            enddir = False
        else:
            logger.warning(f"scraper.run: unknown action '{action}'")
    except Exception as e:
        logger.error(f"scraper.run: unhandled exception in action={action}: {e}")

    if enddir:
        xbmcplugin.endOfDirectory(handle)


def _handle_find(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> None:
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

    results = []
    successful_candidate = None
    for candidate in candidates:
        results = kp_client.search(candidate, search_year, type_filter=["FILM"])
        if results:
            successful_candidate = candidate
            logger.info(f"_handle_find: found {len(results)} results for candidate '{candidate}'")
            break

    dual_search_done = False
    if results and settings.enable_dual_search:
        results = _perform_dual_search(
            results, successful_candidate, search_year,
            kp_client, ["FILM"], settings, logger
        )
        dual_search_done = True
    elif results:
        logger.info("_handle_find: dual search: disabled by settings")

    if not results and search_year:
        for candidate in candidates:
            results = kp_client.search(candidate, None, type_filter=["FILM"])
            if results:
                successful_candidate = candidate
                logger.info(f"_handle_find: found {len(results)} results for '{candidate}' without year")
                break

    if results and settings.enable_dual_search and not dual_search_done:
        results = _perform_dual_search(
            results, successful_candidate, search_year,
            kp_client, ["FILM"], settings, logger
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
                results = kp_client.search(trans, search_year, type_filter=["FILM"])
                if results:
                    successful_candidate = trans
                    logger.info(f"_handle_find: found {len(results)} results after transliteration: '{trans}'")
                    break
            if not results and search_year:
                for _, trans in trans_pairs:
                    results = kp_client.search(trans, None, type_filter=["FILM"])
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
            'Notification("Ultimate Movie Scraper", '
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
        return False

    if not settings.kinopoisk_api_key:
        logger.error("_handle_getdetails: Kinopoisk API key not configured")
        return False

    video_file_path = xbmc.getInfoLabel("ListItem.FileNameAndPath") or ""
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
                    "Ultimate Movie Scraper",
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
    from_fallback = False

    if cached_raw is not None:
        details = kp_client.parse_details(cached_raw, genre_language=settings.genre_language)
        logger.info(f"_handle_getdetails: loaded details from cache for kp_id={kp_id}")
    else:
        if _kp_unavailable:
            raw = kp_client.fetch_details_raw_degraded(kp_id)
        else:
            raw = kp_client.fetch_details_raw(kp_id)

        if raw:
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
                details = kp_client.parse_details(stale_raw, genre_language=settings.genre_language)
                from_fallback = True
                logger.warning(
                    f"_handle_getdetails: serving stale cache for kp_id={kp_id}"
                )
                if not _stale_cache_notified:
                    xbmc.executebuiltin(
                        'Notification("Ultimate Movie Scraper", '
                        '"Данные из кэша (устаревшие)", 5000)'
                    )
                    _stale_cache_notified = True
            else:
                nfo_details = _try_nfo_fallback_movie(
                    kp_id, video_file_path, logger
                )
                if nfo_details is not None:
                    details = nfo_details
                    from_fallback = True
                    logger.warning(
                        f"_handle_getdetails: serving NFO data for kp_id={kp_id}"
                    )
                    if not _nfo_fallback_notified:
                        xbmc.executebuiltin(
                            'Notification("Ultimate Movie Scraper", '
                            '"Данные из NFO-файла", 5000)'
                        )
                        _nfo_fallback_notified = True
                else:
                    logger.error(
                        f"_handle_getdetails: all fallbacks failed for kp_id={kp_id}"
                    )
                    if not _kp_unavailable_notified:
                        xbmc.executebuiltin(
                            'Notification("Ultimate Movie Scraper", '
                            '"Кинопоиск недоступен", 5000)'
                        )
                        _kp_unavailable_notified = True
                    xbmcplugin.setResolvedUrl(
                        handle, False, xbmcgui.ListItem(offscreen=True)
                    )
                    return False

    if not from_fallback or not hasattr(details, 'directors') or not details.directors:
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
        details.directors = directors
        details.writers = writers
        details.cast = cast
    else:
        logger.info(f"_handle_getdetails: staff from NFO fallback for kp_id={kp_id}")

    # BL-60: premiere date from distributions
    if not details.premiere_date:
        try:
            distributions_cache_key = f"distributions_{kp_id}"
            cached_distributions = cache.get(distributions_cache_key)
            if cached_distributions is not None:
                logger.info(f"_handle_getdetails: distributions from cache for kp_id={kp_id}")
                details.premiere_date = kp_client.parse_premiere_date(cached_distributions)
            elif not from_fallback and not _kp_unavailable:
                distributions_raw = kp_client.fetch_distributions_raw(kp_id)
                if distributions_raw is not None:
                    cache.put(distributions_cache_key, distributions_raw)
                    details.premiere_date = kp_client.parse_premiere_date(distributions_raw)
            elif _kp_unavailable:
                stale_distributions = cache.get_stale(distributions_cache_key)
                if stale_distributions is not None:
                    details.premiere_date = kp_client.parse_premiere_date(stale_distributions)
                    logger.info(f"_handle_getdetails: distributions from stale cache for kp_id={kp_id}")
        except Exception as exc:
            logger.warning(f"_handle_getdetails: distributions error for kp_id={kp_id}: {exc}")
    else:
        logger.info(f"_handle_getdetails: premiere_date already set for kp_id={kp_id}: {details.premiere_date}")

    if settings.enable_collections:
        try:
            cache_key_sequels = f"kp_sequels_{kp_id}"
            cached_sequels = cache.get(cache_key_sequels)
            if cached_sequels is not None:
                sequels = cached_sequels
                logger.info(f"_handle_getdetails: loaded sequels from cache for kp_id={kp_id}")
            else:
                sequels = kp_client.get_sequels(kp_id)
                if sequels:
                    cache.put(cache_key_sequels, sequels)
            sequel_titles = [
                s.get("nameRu") or s.get("nameOriginal") or ""
                for s in sequels
                if s.get("relationType") == "SEQUEL"
            ]
            sequel_titles = [t for t in sequel_titles if t]
            if sequel_titles:
                franchise = extract_franchise_name(details.title_ru, sequel_titles)
                if franchise:
                    details.set_name = franchise
                    logger.info(
                        f"_handle_getdetails: franchise='{franchise}' for kp_id={kp_id}"
                    )
            else:
                logger.info(
                    f"_handle_getdetails: no sequels for kp_id={kp_id}, skipping collection"
                )
        except Exception as e:
            logger.error(f"_handle_getdetails: collections enrichment failed: {e}")

    _resolve_imdb_via_wikidata(details, kp_id, cache, settings, logger)

    _enrich_with_omdb(details, settings, logger, cache)

    # --- BL-09: YouTube trailer ---
    if settings.enable_trailers and not details.trailer_url:
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
            details.trailer_url = trailer_url
            logger.info(f"_handle_getdetails: Trailer set: {trailer_url.split('videoid=')[-1]}")
        else:
            logger.warning(f"_handle_getdetails: No YouTube trailer found for kp_id={kp_id}")
    elif not settings.enable_trailers:
        logger.info("_handle_getdetails: Trailers disabled, skipping")
    # --- end BL-09 ---

    # --- BL-68: FanArt.tv artwork ---
    fanart_art: dict[str, str] = {}
    if settings.use_fanart and settings.fanart_api_key and details.imdb_id:
        try:
            from fanart_client import FanartClient
            fc = FanartClient(settings.fanart_api_key, logger)
            fanart_art = fc.get_movie_art(details.imdb_id)
            if fanart_art:
                art_count = len(fanart_art)
                logger.info(
                    f"_handle_getdetails: FanArt.tv returned {art_count} art types"
                    f" for imdb_id={details.imdb_id}"
                )
        except Exception as exc:
            logger.warning(f"_handle_getdetails: FanArt.tv error: {exc}")
    elif settings.use_fanart and not settings.fanart_api_key:
        logger.debug("_handle_getdetails: FanArt.tv API key not configured")
    elif settings.use_fanart and not details.imdb_id:
        logger.debug("_handle_getdetails: no IMDB ID for FanArt.tv lookup")
    # --- end BL-68 ---

    listitem = xbmcgui.ListItem(offscreen=True)
    _apply_movie_details_to_listitem(details, listitem, settings, logger, fanart_art)

    write_movie_nfo(details, video_file_path, settings, logger)

    xbmcplugin.setResolvedUrl(handle, True, listitem)

    logger.info(f"_handle_getdetails: success for kp_id={kp_id}, title='{details.title_ru}'")
    return True


def _enrich_with_omdb(
    details: MovieDetails, settings: SettingsManager, logger: Logger,
    cache: FileCache | None = None,
) -> None:
    # Block 1: Fetch OMDb (ALWAYS if key + imdb_id available)
    omdb_ratings = None
    if settings.omdb_api_key and details.imdb_id:
        omdb_cache_key = f"omdb_ratings_{details.imdb_id}"
        cached_omdb = cache.get(omdb_cache_key) if cache else None

        if cached_omdb is not None:
            logger.info(f"_enrich_with_omdb: loaded OMDb from cache for imdb_id={details.imdb_id}")
            try:
                omdb = OmdbClient(settings.omdb_api_key, logger)
                omdb_ratings = omdb.parse_ratings(cached_omdb, details.imdb_id)
            except Exception as exc:
                logger.warning(f"_enrich_with_omdb: cache parse error: {exc}")
        else:
            logger.info(f"_enrich_with_omdb: fetching OMDb for imdb_id={details.imdb_id}")
            try:
                omdb = OmdbClient(settings.omdb_api_key, logger)
                raw_omdb = omdb.fetch_ratings_raw(details.imdb_id)
                if raw_omdb is not None:
                    if cache:
                        cache.put(omdb_cache_key, raw_omdb)
                    omdb_ratings = omdb.parse_ratings(raw_omdb, details.imdb_id)
            except Exception as exc:
                logger.warning(f"_enrich_with_omdb: OMDb error: {exc}")

    # Block 2: Add RT/MC to details.ratings (ALWAYS)
    if omdb_ratings:
        existing_sources = {r.source for r in details.ratings}

        rt_value = parse_rt_rating(omdb_ratings.rotten_tomatoes, logger)
        if rt_value is not None and DataSource.ROTTEN_TOMATOES not in existing_sources:
            details.ratings.append(Rating(DataSource.ROTTEN_TOMATOES, rt_value, 0))
            logger.info(f"_enrich_with_omdb: added RT rating: {rt_value}")

        mc_value = parse_mc_rating(omdb_ratings.metacritic, logger)
        if mc_value is not None and DataSource.METACRITIC not in existing_sources:
            details.ratings.append(Rating(DataSource.METACRITIC, mc_value, 0))
            logger.info(f"_enrich_with_omdb: added MC rating: {mc_value}")

    # Block 2.5: Award tags (gated by enable_award_tags)
    if omdb_ratings and settings.enable_award_tags:
        award_tags = parse_award_tags(omdb_ratings.awards, logger)
        if award_tags:
            details.tags.extend(award_tags)
            logger.info(
                f"_enrich_with_omdb: award tags for imdb_id={details.imdb_id}: {award_tags}"
            )
        else:
            logger.info(
                f"_enrich_with_omdb: no award tags for imdb_id={details.imdb_id}"
            )
    elif omdb_ratings and not settings.enable_award_tags:
        logger.debug("_enrich_with_omdb: enable_award_tags disabled, skipping")

    # Block 3: Text in plot (gated by show_ratings_in_plot)
    if not settings.show_ratings_in_plot:
        logger.debug("_enrich_with_omdb: show_ratings_in_plot disabled, skipping plot text")
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
        logger.info(f"_enrich_with_omdb: ratings in plot: {rating_line}")
    else:
        logger.info("_enrich_with_omdb: no ratings to display")


def _apply_movie_details_to_listitem(
    details: MovieDetails,
    listitem: xbmcgui.ListItem,
    settings: SettingsManager,
    logger: Logger,
    fanart_art: dict[str, str] | None = None,
) -> None:
    logger.debug("_apply_movie_details_to_listitem: mapping details to ListItem")

    infotag = listitem.getVideoInfoTag()

    infotag.setTitle(details.title_ru)
    infotag.setOriginalTitle(details.title_original)
    infotag.setPlot(details.plot)

    # BL-61: plot outline (shortDescription from KP)
    if details.plot_outline:
        infotag.setPlotOutline(details.plot_outline)
        logger.info(f"_apply_movie_details: setPlotOutline (len={len(details.plot_outline)})")

    # BL-60: premiered date from distributions
    if details.premiere_date:
        infotag.setPremiered(details.premiere_date)
        logger.info(f"_apply_movie_details: setPremiered={details.premiere_date}")

    infotag.setTagLine(details.tagline)

    infotag.setYear(details.year)
    infotag.setDuration(details.runtime * 60)
    infotag.setMpaa(details.mpaa)

    if details.original_language:
        try:
            infotag.setOriginalLanguage(details.original_language)
            logger.info(f"_apply_movie_details: setOriginalLanguage('{details.original_language}')")
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
            f"_apply_movie_details_to_listitem: setTags({details.tags})"
        )

    if details.set_name:
        infotag.setSet(details.set_name)
        logger.debug(
            f"_apply_movie_details_to_listitem: setSet('{details.set_name}')"
        )

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

    # --- BL-68: FanArt.tv artwork ---
    if fanart_art:
        for art_type, art_url in fanart_art.items():
            infotag.addAvailableArtwork(art_url, art_type)
            logger.debug(f"_apply_movie_details: FanArt.tv addAvailableArtwork({art_type})")
    # --- end BL-68 ---

    if details.trailer_url:
        infotag.setTrailer(details.trailer_url)
        logger.debug(f"_apply_movie_details_to_listitem: setTrailer('{details.trailer_url}')")

    logger.debug(
        f"_apply_movie_details_to_listitem: mapped '{details.title_ru}' "
        f"with {len(details.ratings)} ratings, {len(details.cast)} cast"
    )


def _handle_nfo(params: dict, handle: int, logger: Logger) -> None:
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


def _handle_getartwork(
    params: dict, handle: int, settings: SettingsManager, logger: Logger
) -> None:
    logger.info(f"_handle_getartwork: params={params}")

    kp_id = extract_kinopoisk_id(params, logger)

    if not kp_id:
        logger.warning("_handle_getartwork: no Kinopoisk ID for artwork fetch")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return

    if not settings.kinopoisk_api_key:
        logger.error("_handle_getartwork: Kinopoisk API key not configured")
        xbmcplugin.setResolvedUrl(handle, False, xbmcgui.ListItem(offscreen=True))
        return

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


if __name__ == "__main__":
    run()
