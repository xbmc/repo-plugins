
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------
from __future__ import annotations

import xbmc
import xbmcplugin
import sys
from collections.abc import Iterable

from xbmc import executebuiltin
from xbmcgui import ListItem as XbmcListItem

from codequick import Route, Resolver, Listitem, Script
from codequick import run as cc_run
from codequick.storage import PersistentDict

from resources.lib.addon_log import logger
from resources.lib.ctree import ct_api
from resources.lib.ctree import ct_data
from resources.lib import storyblok, kodi_utils
from resources.lib import errors
from resources.lib import constants
from resources.lib import utils


logger.critical('-------------------------------------')

TXT_SORT_BY = 30106
TXT_SORT_ORDER = 30107
MSG_FILM_NOT_AVAILABLE = 30606
MSG_ONLY_WITH_SUBSCRIPTION = 30607
TXT_MY_FILMS = 30801
TXT_RECOMMENDED = 30802
TXT_MONTH_SELECTION = 30803
TXT_RENTALS_COLLECTIONS = 30805
TXT_RENTALS_GENRES = 30806
TXT_SEARCH = 30807
TXT_ALREADY_WATCHED = 30808
TXT_RENTED = 30809
TXT_ALL_COLLECTIONS = 30810
TXT_CONTINUE_WATCHING = 30811
TXT_MY_LIST = 30812
TXT_ORIGINALS = 30813
TXT_SHORT = 30814
TXT_ALL_SHORT_FILMS = 30815
TXT_REMOVE_FROM_LIST = 30859
TXT_NOTHING_FOUND = 30608
TXT_TOO_MANY_RESULTS = 30609
MSG_PAYMENT_FAIL = 30625
MSG_REMOVE_CONFIRM = 30626

TXT_ADD_TO_WATCHLIST = Script.localize(30860)
TXT_REMOVE_FROM_WATCHLIST = Script.localize(30861)


@Route.register
def root(_):
    yield Listitem.from_dict(list_my_films, Script.localize(TXT_MY_FILMS), params={'_cache_to_disc_': False})
    yield Listitem.from_dict(list_films_and_docus, Script.localize(TXT_RECOMMENDED),
                             params={'category': 'recommended'})
    yield Listitem.from_dict(list_films_and_docus, Script.localize(TXT_MONTH_SELECTION),
                             params={'category': 'subscription'})
    yield Listitem.from_dict(list_originals, Script.localize(TXT_ORIGINALS))
    yield Listitem.from_dict(list_shorts, Script.localize(TXT_SHORT))
    yield Listitem.from_dict(list_rental_collections, Script.localize(TXT_RENTALS_COLLECTIONS))
    yield Listitem.from_dict(list_genres, Script.localize(TXT_RENTALS_GENRES))
    yield Listitem.search(do_search, Script.localize(TXT_SEARCH))
    sync_watched_state()


@Route.register(content_type='movies')
def list_my_films(addon, subcategory=None):
    """List the films not finished watching. Newly purchased films appear here, so do not cache"""

    if subcategory is None:
        yield Listitem.from_dict(list_watchlist,
                                 Script.localize(TXT_MY_LIST),
                                 params={'_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_CONTINUE_WATCHING),
                                 params={'subcategory': 'continue', '_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_ALREADY_WATCHED),
                                 params={'subcategory': 'finished', '_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_RENTED),
                                 params={'subcategory': 'purchased', '_cache_to_disc_': False})
        return

    if subcategory == 'purchased':
        films = ct_data.create_films_list(ct_api.get_rented_films(), 'storyblok')
        yield from _create_playables(addon, films)
        return
    else:
        watched_films = ct_api.get_watched_films()
        if subcategory == 'finished':
            films = (film for film in watched_films if film.playtime == 0)
        else:
            films = (film for film in watched_films if film.playtime > 0)

    if not films:
        # yield False
        return

    for film in films:
        uuid = film.uuid
        li = Listitem.from_dict(callback=play_film, **film.data)
        li.context.script(remove_from_list,
                          addon.localize(TXT_REMOVE_FROM_LIST),
                          film_uuid=uuid,
                          title=film.data['info']['title'])
        yield li


def _create_playables(addon, films: Iterable[ct_data.FilmItem]):
    """Create playable Codequick.Listitems from FilmItems with a
    context menu items to add or remove from Watch List.

    """
    if addon:
        addon.add_sort_methods(xbmcplugin.SORT_METHOD_UNSORTED,
                               xbmcplugin.SORT_METHOD_DATEADDED)
    favourites = ct_api.get_favourites()

    for film_item in films:
        if film_item:
            uuid = film_item.uuid
            is_on_watchlist = uuid in favourites
            li = Listitem.from_dict(callback=play_film, **film_item.data)
            li.context.script(
                edit_watchlist,
                TXT_REMOVE_FROM_WATCHLIST if is_on_watchlist else TXT_ADD_TO_WATCHLIST,
                film_uuid=uuid,
                action='remove' if is_on_watchlist else 'add')
            yield li
        else:
            logger.debug("film item is Empty")


@Route.register(content_type='movies')
def list_watchlist(addon):
    favourites = ct_api.get_favourites(refresh=True)
    films_list, _ = storyblok.stories_by_uuids(favourites.keys())
    films = []
    for film in films_list:
        film_item = ct_data.FilmItem(film)
        if not film_item:
            continue
        time_added = utils.reformat_date(favourites[film_item.uuid], '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%d %H:%M:%S')
        film_item.data['info']['dateadded'] = time_added
        films.append(film_item)
    if not films:
        return False
    return _create_playables(addon, films)


@Script.register()
def edit_watchlist(_, film_uuid, action):
    ct_api.edit_favourites(film_uuid, action)
    xbmc.executebuiltin('Container.Refresh')


@Route.register(content_type='movies')
def list_films_and_docus(addon, category):
    """List subscription films"""
    if category == 'subscription':
        film_ids = ct_api.get_subscription_films()
    elif category == 'recommended':
        film_ids = ct_api.get_recommended()
    else:
        return None
    stories, _ = storyblok.stories_by_uuids(film_ids)
    films = ct_data.create_films_list(stories, 'storyblok', add_price=False)
    return list(_create_playables(addon, films))


@Route.register()
def list_rental_collections(addon):
    collections = ct_api.get_preferred_collections(page='films')
    for coll in collections:
        yield Listitem.from_dict(list_films_by_collection, **coll)
    yield Listitem.from_dict(list_all_collections, addon.localize(TXT_ALL_COLLECTIONS))


@Route.register()
def list_all_collections(_):
    collections = ct_api.get_collections()
    for coll in collections:
        yield Listitem.from_dict(list_films_by_collection, **coll)


@Route.register()
def list_genres(_):
    for genre in ct_api.GENRES:
        yield Listitem.from_dict(list_films_by_genre, label=genre, params={'genre': genre})


@Route.register()
def do_search(addon, search_query):
    uuids = ct_api.search_films(search_term=search_query)

    if len(uuids) > 100:
        Script.notify('Cinetree - ' + Script.localize(TXT_SEARCH),
                      Script.localize(TXT_TOO_MANY_RESULTS),
                      Script.NOTIFY_INFO, 12000)

    stories, _ = storyblok.stories_by_uuids(uuids[:100])

    if stories:
        films = ct_data.create_films_list(stories, 'storyblok')
        return list(_create_playables(addon, films))
    else:
        Script.notify('Cinetree - ' + Script.localize(TXT_SEARCH),
                      Script.localize(TXT_NOTHING_FOUND),
                      Script.NOTIFY_INFO, 7000)
        return False


@Route.register(content_type='movies')
def list_originals(addon):
    data = ct_api.get_originals()
    films = ct_data.create_films_list(data, 'storyblok')
    yield from _create_playables(addon, films)


@Route.register(content_type='movies')
def list_shorts(addon, list_films=False):
    if not list_films:
        # List a submenu of collections of short films
        collections = ct_api.get_preferred_collections(page='kort')
        for coll in collections:
            yield Listitem.from_dict(list_films_by_collection, **coll)
        yield Listitem.from_dict(list_shorts, addon.localize(TXT_ALL_SHORT_FILMS), params={'list_films': True})
    else:
        # List all short films
        stories, _ = storyblok._get_url_page('stories', params={'starts_with': 'shorts/'})
        yield from _create_playables(addon, ct_data.create_films_list(stories, 'storyblok'))


@Route.register(content_type='movies')
def list_films_by_collection(addon, slug):
    data = ct_api.get_jsonp(slug + '/payload.js')
    yield from _create_playables(addon, ct_data.create_films_list(data))


@Route.register(content_type='movies')
def list_films_by_genre(addon, genre, page=1):
    sort_by = addon.setting.get_int('genre-sort-method')
    sort_order = addon.setting.get_int('genre-sort-order')
    logger.debug("*** Genre %s, pag %s, sorted by %s:%r", genre, page, sort_by, repr(sort_order))
    addon.add_sort_methods(xbmcplugin.SORT_METHOD_NONE, disable_autosort=True)
    list_len = 50
    films, num_films = storyblok.search(genre=genre,
                                        page=page,
                                        items_per_page=list_len,
                                        sort_method=sort_by,
                                        sort_order=sort_order)
    # Context menu item to set the sort method and sort order for all genres.
    ctx_sort_by = (
        addon.localize(TXT_SORT_BY) + '    >>',
        ''.join(('RunPlugin(plugin://',
                 utils.addon_info['id'],
                 '/resources/lib/settings/genre_sort_method)'))
    )
    for li in _create_playables(None, (ct_data.FilmItem(film) for film in films)):
        li.context.insert(0, ctx_sort_by)
        yield li
    if num_films > page * list_len:
        yield Listitem.next_page(genre=genre, page=page + 1)


@Script.register()
def remove_from_list(addon, film_uuid, title):
    """Remove a film from the 'Continue Watching' or 'Already Watched' list."""
    if kodi_utils.yes_no_dialog(addon.localize(MSG_REMOVE_CONFIRM).format(title=title)):
        ct_api.remove_watched_film(film_uuid)
        logger.info("Removed film '%s' from the watched list", title)
        executebuiltin('Container.Refresh')
    else:
        logger.debug("Remove film '%s' canceled by user.", title)


def monitor_progress(watch_id):
    """Pushes playtime to Cinetree when playing starts and when playing ends.

    Is being run after a playable item has been returned to Kodi.
    """
    player = kodi_utils.PlayTimeMonitor()
    if player.wait_until_playing(10) is False:
        return
    ct_api.set_resume_time(watch_id, player.playtime)
    player.wait_while_playing()
    ct_api.set_resume_time(watch_id, player.playtime)


def sync_watched_state():
    """Sync the play progress to Kodi for every film that has changed
    since the last time it was checked.

    """
    history = list(ct_api.get_watched_films())
    logger.debug("[sync_watched] History has %s items", len(history))
    with PersistentDict(constants.HISTORY_CACHE) as prev_watched:
        changed = {film for film in history if prev_watched.get(film.uuid) != film.playtime}
        if not changed:
            return
        logger.info("[sync_watched] %s items changed", len(changed))
        for film in changed:
            kodi_utils.sync_play_state(play_film, film)
        prev_watched.clear()
        prev_watched.update((film.uuid, film.playtime) for film in history)


def create_hls_item(url, title):
    # noinspection PyImport,PyUnresolvedReferences
    import inputstreamhelper

    PROTOCOL = 'hls'

    is_helper = inputstreamhelper.Helper(PROTOCOL)
    if not is_helper.check_inputstream():
        logger.warning('No support for protocol %s', PROTOCOL)
        return False

    play_item = XbmcListItem(title, offscreen=True)
    if title:
        play_item.setInfo('video', {'title': title})

    play_item.setPath(url)
    play_item.setContentLookup(False)

    stream_headers = ''.join((
            'User-Agent=',
            constants.USER_AGENT,
            '&Referer=https://www.cinetree.nl/&'
            'Origin=https://www.cinetree.nl&'
            'Sec-Fetch-Dest=empty&'
            'Sec-Fetch-Mode=cors&'
            'Sec-Fetch-Site=same-site'))

    play_item.setProperties({
        'IsPlayable': 'true',
        'inputstream': 'inputstream.adaptive',
        'inputstream.adaptive.manifest_type': PROTOCOL,
        'inputstream.adaptive.stream_headers': stream_headers
    })

    return play_item


def play_ct_video(stream_info: dict, title: str = ''):
    """ From the info provided in *stream_info*, prepare subtitles and build
    a playable xbmc.ListItem to play a film, short film, or trailer
    from Cinetree.

    """
    try:
        subtitles = [ct_api.get_subtitles(url, lang) for lang, url in stream_info['subtitles'].items()]
        logger.debug("using subtitles '%s'", subtitles)
    except KeyError:
        logger.debug("No subtitels available for video '%s'", title)
        subtitles = None
    except errors.FetchError as e:
        logger.error("Failed to fetch subtitles: %r", e)
        subtitles = None

    play_item = create_hls_item(stream_info.get('url'), title)
    if play_item is False:
        return False

    if subtitles:
        play_item.setSubtitles(subtitles)
    return play_item


@Resolver.register
def play_film(plugin, title, uuid, slug):
    logger.info('play film - title=%s, uuid=%s, slug=%s', title, uuid, slug)
    try:
        stream_info = ct_api.get_stream_info(ct_api.create_stream_info_url(uuid, slug))
        logger.debug("play_info = %s", stream_info)
    except errors.NotPaidError:
        if pay_from_ct_credit(title, uuid):
            return play_film(plugin, title, uuid, slug)
        else:
            return False
    except errors.NoSubscriptionError:
        Script.notify('Cinetree', Script.localize(MSG_ONLY_WITH_SUBSCRIPTION), Script.NOTIFY_INFO, 6500)
        return False
    except errors.FetchError as err:
        status_code = getattr(err, 'code', None)
        if status_code == 404:
            Script.notify('Cinetree', Script.localize(MSG_FILM_NOT_AVAILABLE), Script.NOTIFY_INFO, 6500)
        else:
            logger.error('Error retrieving film urls: %r' % err)
            Script.notify('Cinetree', str(err), Script.NOTIFY_ERROR, 6500)
        return False
    except Exception as e:
        logger.error('Error playing film: %r' % e, exc_info=True)
        return False

    play_item = play_ct_video(stream_info, title)
    if play_item:
        plugin.register_delayed(monitor_progress, watch_id=stream_info.get('watchHistoryId'))
    return play_item


@Resolver.register
def play_trailer(plugin, url):
    if 'youtube' in url:
        logger.info("Play youtube trailer: '%s'", url)
        return plugin.extract_source(url)

    if 'vimeo' in url:
        from resources.lib.vimeo import get_steam_url
        url_type, stream_url = get_steam_url(url)
        if url_type == 'file':
            logger.info("Play vimeo file trailer: '%s'", stream_url)
            return stream_url
        elif url_type == 'hls':
            logger.info("Play vimeo HLS trailer: '%s'", stream_url)
            return create_hls_item(stream_url, 'trailer')

    if 'cinetree' in url:
        stream_info = ct_api.get_stream_info(url)
        logger.info("Play cinetree trailer: '%s'", stream_info.get('url'))
        return play_ct_video(stream_info, 'trailer')

    logger.warning("Cannot play trailer from unknown source: '%s'.", url)
    return False


def pay_from_ct_credit(title, uuid):
    from concurrent import futures
    executor = futures.ThreadPoolExecutor()
    future_objs = [executor.submit(ct_api.get_payment_info, uuid),
                   executor.submit(ct_api.get_ct_credits)]
    futures.wait(future_objs)
    amount, trans_id = future_objs[0].result()
    ct_credits = future_objs[1].result()
    if amount > ct_credits:
        kodi_utils.show_low_credit_msg(amount, ct_credits)
    elif kodi_utils.confirm_rent_from_credit(title, amount, ct_credits):
        if ct_api.pay_film(uuid, title, trans_id, amount):
            return True
        else:
            kodi_utils.ok_dialog(MSG_PAYMENT_FAIL)
    return False


def run():
    if isinstance(cc_run(), Exception):
        xbmcplugin.endOfDirectory(int(sys.argv[1]), False)
