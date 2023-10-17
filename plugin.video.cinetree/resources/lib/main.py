
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import xbmcplugin
import sys

from xbmcgui import ListItem as XbmcListItem

from codequick import Route, Resolver, Listitem, Script
from codequick import run as cc_run

from resources.lib.addon_log import logger
from resources.lib.ctree import ct_api
from resources.lib.ctree import ct_data
from resources.lib import storyblok, kodi_utils
from resources.lib import errors
from resources.lib import constants


logger.critical('-------------------------------------')


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
TXT_NOTHING_FOUND = 30608
TXT_TOO_MANY_RESULTS = 30609


@Route.register
def root(_):
    yield Listitem.from_dict(list_my_films, Script.localize(TXT_MY_FILMS), params={'_cache_to_disc_': False})
    yield Listitem.from_dict(list_films_and_docus, Script.localize(TXT_RECOMMENDED),
                             params={'category': 'recommended'})
    yield Listitem.from_dict(list_films_and_docus, Script.localize(TXT_MONTH_SELECTION),
                             params={'category': 'subscription'})
    yield Listitem.from_dict(list_rental_collections, Script.localize(TXT_RENTALS_COLLECTIONS))
    yield Listitem.from_dict(list_genres, Script.localize(TXT_RENTALS_GENRES))
    yield Listitem.search(do_search, Script.localize(TXT_SEARCH))


@Route.register(content_type='movies')
def list_my_films(_, subcategory=None):
    """List the films not finished watching. Newly purchased films appear here, so do not cache"""

    if subcategory is None:
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_ALREADY_WATCHED),
                                 params={'subcategory': 'finished', '_cache_to_disc_': False})
        yield Listitem.from_dict(list_my_films,
                                 Script.localize(TXT_RENTED),
                                 params={'subcategory': 'purchased', '_cache_to_disc_': False})

    if subcategory == 'purchased':
        films_list = ct_api.get_rented_films()
    else:
        films_list = ct_api.get_watched_films(subcategory == 'finished')

    if not films_list:
        yield False
        return

    films = (ct_data.create_film_item(film) for film in films_list)
    for film in films:
        if film is not None:
            yield Listitem.from_dict(callback=play_film, **film)


@Route.register(cache_ttl=-1, content_type='movies')
def list_films_and_docus(_, category):
    resp_dict = ct_api.get_jsonp('films-en-documentaires/payload.js')
    films = ct_data.create_films_list(resp_dict, category)
    items = [Listitem.from_dict(callback=play_film, **film) for film in films]
    return items


@Route.register(cache_ttl=480)
def list_rental_collections(_):
    collections = ct_api.get_preferred_collections()
    for coll in collections:
        yield Listitem.from_dict(list_films_by_collection, **coll)
    yield Listitem.from_dict(list_all_collections, 'Alle Collecties')


@Route.register(cache_ttl=480)
def list_all_collections(_):
    collections = ct_api.get_collections()
    for coll in collections:
        yield Listitem.from_dict(list_films_by_collection, **coll)


@Route.register(cache_ttl=480)
def list_genres(_):
    for genre in ct_api.GENRES:
        yield Listitem.from_dict(list_films_by_genre, label=genre, params={'genre': genre})


@Route.register()
def do_search(_, search_query):
    uuids = ct_api.search_films(search_term=search_query)

    if len(uuids) > 100:
        Script.notify('Cinetree - ' + Script.localize(TXT_SEARCH),
                      Script.localize(TXT_TOO_MANY_RESULTS),
                      Script.NOTIFY_INFO, 12000)

    stories, _ = storyblok.stories_by_uuids(uuids[:100])
    films = ct_data.create_films_list(stories, 'storyblok')
    if films:
        return [Listitem.from_dict(play_film, **film) for film in films]
    else:
        Script.notify('Cinetree - ' + Script.localize(TXT_SEARCH),
                      Script.localize(TXT_NOTHING_FOUND),
                      Script.NOTIFY_INFO, 7000)
        return False


@Route.register(cache_ttl=480, content_type='movies')
def list_films_by_collection(_, slug):
    data = ct_api.get_jsonp(slug + '/payload.js')
    films = ct_data.create_films_list(data)
    return [Listitem.from_dict(play_film, **film) for film in films]


@Route.register(cache_ttl=480, content_type='movies')
def list_films_by_genre(_, genre, page=1):
    list_len = 50
    films, num_films = storyblok.search(genre=genre, page=page, items_per_page=list_len)

    for film in films:
        film_item_data = ct_data.create_film_item(film)
        if film_item_data is not None:
            yield Listitem.from_dict(play_film, **film_item_data)
    if num_films > page * list_len:
        yield Listitem.next_page(genre=genre, page=page + 1)


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

    resume_time = stream_info.get('playtime')
    if resume_time and int(resume_time):
        result = kodi_utils.ask_resume_film(resume_time)
        logger.debug("Resume from %s result = %s", resume_time, result)
        if result == -1:
            logger.debug("User canceled resume play dialog")
            return False
        elif result == 0:
            play_item.setInfo('video', {'playcount': 1})
            play_item.setProperties({
                'ResumeTime': str(resume_time),
                'TotalTime': '7200'
            })
            logger.debug("Play from %s", resume_time)
        else:
            logger.debug("Play from start")

    return play_item


@Resolver.register
def play_film(plugin, title, uuid, slug, end_date=None):
    logger.info('play film - title=%s, uuid=%s, slug=%s, end_date=%s', title, uuid, slug, end_date)
    try:
        stream_info = ct_api.get_stream_info(ct_api.create_stream_info_url(uuid, slug))
        logger.debug("play_info = %s", stream_info)
    except errors.NotPaidError:
        kodi_utils.show_rental_msg(slug)
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


def run():
    if isinstance(cc_run(), Exception):
        xbmcplugin.endOfDirectory(int(sys.argv[1]), False)
