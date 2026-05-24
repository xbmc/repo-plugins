
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2026 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt.
# ------------------------------------------------------------------------------

import logging
from datetime import datetime, timezone
from enum import Enum

from codequick import Script
from codequick.support import logger_id

from resources.lib import fetch
from resources.lib import errors
from resources.lib import utils
from resources.lib.ctree.ct_data import create_collection_item, FilmItem
from resources.lib import storyblok


STRM_INFO_UNAVAILABLE = 30921

logger = logging.getLogger(logger_id + '.ct_api')
cache_mgr = utils.CacheMgr(fetch.cache_location)

GENRES = ('Action', 'Adventure', 'Biography', 'Comedy', 'Coming-of-age', 'Crime', 'Drama', 'Documentary',
          'Family', 'Fantasy', 'History', 'Horror', 'Mystery', 'Sci-Fi', 'Romance', 'Thriller')

favourites = None


def get_nuxt_json_url(slug):
    """Append *slug* to the base path for .js requests and return the full url.

    Part of the base url is a timestamp that changes every so often. We obtain
    that number from Cinetree's main page and cache it for future requests.

    """
    nuxt_revision = cache_mgr.version
    if nuxt_revision is None:
        import re

        resp = fetch.web_request('get', 'https://cinetree.nl', max_age=-1)
        page_data = resp.content.decode('utf8')
        match = re.search(r'buildId:"([\w-]*?)"', page_data, re.DOTALL)
        nuxt_revision = match.group(1)
        cache_mgr.version = nuxt_revision
    url = ''.join(('https://cinetree.nl/', slug, '/_payload.json?', nuxt_revision))
    return url


def get_nuxt_json(path):
    from resources.lib.nuxt3 import parse

    url = get_nuxt_json_url(path)
    try:
        resp = fetch.get_document(url)
    except errors.HttpError as err:
        if err.code == 404:
            # Cinetree's revision timestamp may have changed.
            cache_mgr.revalidate()
            storyblok.st_cache_mgr.revalidate()
            url = get_nuxt_json_url(path)
            resp = fetch.get_document(url)
        else:
            raise

    resp_dict = parse(resp)
    return resp_dict


def get_recommended():
    """Return the uuids of the hero items on the subscription page"""
    data, _ = storyblok.get_url('stories//films-en-documentaires',
                                params={'from_release': 'undefined'})
    page_top = data['story']['content']['top']
    for section in page_top:
        if section['component'] == 'row-featured-films':
            return section['films']
    return []


def get_subscription_films():
    """Return a list of ID's of the current subscription films"""
    resp = fetch.get_json('https://api.cinetree.nl/films/svod')
    return resp


def get_originals():
    """Return the list of Cinetree Originals"""
    data = get_nuxt_json('originals')
    # Data has several fields, of which 2 are a list of films. One has only a few highlights,
    # while the other is the full list. Currently, the list we need has a title starting with 'svod-films'
    film_list = []
    for k, v in data.items():
        if k.startswith('svod-films'):
            film_list = v
    return film_list


def create_stream_info_url(film_uuid, slug=None):
    """Return the url to the stream info (json) document.

    Create the url from the uuid. If the uuid is not available, obtain the
    uuid from the film's details page.

    """
    if not film_uuid:
        try:
            data = storyblok.story_by_name(slug)
            film_uuid = data['uuid']
        except (errors.FetchError, TypeError, KeyError):
            logger.error("Unable to obtain uuid from film details of '%s'.", slug, exc_info=True)
            raise errors.FetchError(Script.localize(STRM_INFO_UNAVAILABLE))

    url = 'https://api.cinetree.nl/films/' + film_uuid
    return url


def get_stream_info(url):
    """Return a dict containing urls to the m3u8 playlist, subtitles, etc., for a specific
    film or trailer.

    """
    data = fetch.fetch_authenticated(fetch.get_json, url, max_age=-1)
    return data


def get_subtitles(url: str, lang: str) -> str:
    """Download vtt subtitles file, convert it to srt and save it locally.
    Return the full path to the local file.

    """
    if not url:
        return ''

    vtt_titles = fetch.get_document(url)
    # with open(utils.get_subtitles_temp_file().rsplit('.', 1)[0] + '.vtt', 'w', encoding='utf8') as f:
    #     f.write(vtt_titles)
    srt_titles = utils.vtt_to_srt(vtt_titles)
    logger.debug("VTT subtitles of length %s converted to SRT of length=%s.", len(vtt_titles), len(srt_titles))
    subt_file = utils.get_subtitles_temp_file(lang)
    with open(subt_file, 'w', encoding='utf8') as f:
        f.write(srt_titles)
    return subt_file


def get_watched_films(ask_login: bool = True):
    """Get the list of 'Mijn Films'.

    :param ask_login: Whether to show a dialog asking the user to login when
        the currently not logged in. If False, an AuthenticationError is raised
        without asking the user to sign in.

    """
    history = fetch.fetch_authenticated(
            fetch.get_json,
            url='https://api.cinetree.nl/watch-history',
            ask_login=ask_login,
            max_age=10)
    sb_films, _ = storyblok.stories_by_uuids(film['assetId'] for film in history)
    sb_films = {film['uuid']: film for film in sb_films}

    for item in history:
        try:
            film = sb_films[item['assetId']]
            film['playtime'] = item['playtime']
            fi = FilmItem(film)
            if fi:
                yield fi
        except KeyError:
            # Field playtime may be absent. These items are also disregarded by a regular web browser.
            # And protect against the odd occurrence that a watched film is no longer in the storyblok database.
            logger.debug('Error ct_api.get_watched_films:\n', exc_info=True)
            continue


def remove_watched_film(film_uuid):
    """Remove a film from the watched list.

    It seems that after removing a film will not be added when watched again.

    At the time of testing every request, either with existing, or non-existing
    UUID, or existing films not on the list, return without error.

    """
    resp = fetch.fetch_authenticated(fetch.web_request,
                                     method='delete',
                                     url='https://api.cinetree.nl/watch-history/by-asset/' + film_uuid)
    return resp.status_code == 200


def get_favourites(refresh=False, ask_login=True):
    """Films saved to the personal watch list at Cinetreee.

    :param refresh: Whether to force requesting data from Cinetree, or just
        return already stored data when available.
    :param ask_login: Whether to show a dialog asking the user to login when
        the currently not logged in. If False, an AuthenticationError is raised
        without asking the user to sign in.

"""
    global favourites
    if refresh or favourites is None:
        resp = fetch.fetch_authenticated(
                fetch.get_json,
                url='https://api.cinetree.nl/favorites/',
                ask_login=ask_login,
                max_age=0)

        favourites = {item['uuid']: item['createdAt'] for item in resp}
    return favourites


def edit_favourites(film_uuid: str, action: str):
    """Add or remove a film to/from the personal watch list."""
    method = {
        'remove': 'delete',
        'add': 'put'
    }[action]
    resp = fetch.fetch_authenticated(
            fetch.web_request,
            method=method,
            url='https://api.cinetree.nl/favorites/' + film_uuid)
    if resp.status_code != 200:
        return False

    if action == 'remove':
        del favourites[film_uuid]
    else:
        favourites[film_uuid] = datetime.now(timezone.utc).isoformat()
    return True


def get_rented_films():
    resp = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/purchased', max_age=3)
    # contrary to watched, this returns a plain list of uuids
    if resp:
        rented_films, _ = storyblok.stories_by_uuids(resp)
        return rented_films
    else:
        return resp


def get_preferred_collections(page):
    """Get a short list of the preferred collection.

    This is a short selection of all available collections that the user gets
    presented on the website when he clicks on pages like 'huur films', or 'kort'.
    """
    data = get_nuxt_json(page)
    return (create_collection_item(col_data) for col_data in data['collections'])


def get_collections():
    """Get a list of all available collections
    Which, by the way, are not exactly all collections, but those the website shows as 'all'.
    To get absolutely all collections, request them from storyblok.
    """
    data = get_nuxt_json('collecties')
    return (create_collection_item(col_data) for col_data in data['collections-/collecties'])


class DurationFilter(Enum):
    MAX_1_HR = 60
    BETWEEN_1_TO_2_HRS = 120
    MORE_THAN_2_HRS = 500


def search_films(search_term='', genre=None, country=None, duration=None):
    """Perform a search using the Cinetree api

    Search_term searches on multiple fields, like title, cast, etc.

    """
    # Without args Cinetree returns a lot of items, probably all films, which is not
    # what we want.
    if not any((search_term, genre, country, duration)):
        return []

    query = {'q': search_term, 'startsWith': 'films/,kids/,shorts/'}
    if genre:
        query['genre'] = genre.lower()
    if country:
        query['country'] = country
    if duration:
        query['duration[]'] = {60: ['0', '59'],
                               120: ['60', '120'],
                               500: ['121', '500']}[duration]
    return fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/films', params=query)


def set_resume_time(watch_history_id: str, play_time: float):
    """Report the play position back to Cinetree.

    """
    url = 'https://api.cinetree.nl/watch-history/{}/playtime'.format(watch_history_id)
    play_time = round(play_time, 3)
    data = {"playtime": play_time}
    try:
        fetch.fetch_authenticated(fetch.put_json, url, data=data)
    except Exception as e:
        logger.warning('Failed to report resume time to Cinetree: %r', e)
        return
    logger.debug("Playtime %s reported to Cinetree", play_time)


def get_payment_info(film_uid: str):
    """Return a tuple of the transaction id and amount to be paid to
    rent a film.

    """
    url = 'https://api.cinetree.nl/payments/info/rental/' + film_uid
    payment_data = fetch.fetch_authenticated(fetch.post_json, url, data=None, max_age=-1)
    return float(payment_data['amount']), payment_data['transaction']


def get_ct_credits():
    """Return the current balance of pre-paid credit

    """
    my_data = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/me', max_age=0)
    return float(my_data['credit'])


# noinspection PyBroadException
def pay_film(film_uid: str, film_title: str, transaction_id: str, price: float):
    """Pay for a film by charging the rental amount to the user's prepaid credit.

    """
    try:
        payment_data = {
            'context': {
                'trackEvents': [
                    {
                        'event': 'purchase',
                        'params': {
                            'ecommerce': {
                                'currency': 'EUR',
                                'items': [
                                    {
                                        'item_category': 'TVOD',
                                        'item_id': film_uid,
                                        'item_name': film_title,
                                        'price': price,
                                        'quantity': 1
                                    }
                                ],
                                'tax': price - price / 1.21,
                                'transaction_id': transaction_id,
                                'value': price
                            }
                        }
                    }
                ]
            },
            'transaction': transaction_id
        }
        resp = fetch.fetch_authenticated(
            fetch.web_request,
            'https://api.cinetree.nl/payments/credit',
            method='post',
            headers={'Accept': 'application/json, text/plain, */*'},
            data=payment_data,
            max_age=-1
        )
        content = resp.content.decode('utf8')
        if content:
            logger.warning("[pay_film] - Unexpected response content: '%s'", content)
        # On success cinetree returns 200 OK without content.
        if resp.status_code == 200:
            logger.info("[pay_film] Paid %0.2f from cinetree credit for film '%s'", price, film_title)
            return True
        else:
            logger.error("[pay_film] - Unexpected response status code: '%s'", resp.status_code)
            return False
    except Exception:
        logger.error("[pay_film] paying failed: film_uid=%s, film_title=%s, trans_id=%s, price=%s\n",
                     film_uid, film_title, transaction_id, price, exc_info=True)
        return False
