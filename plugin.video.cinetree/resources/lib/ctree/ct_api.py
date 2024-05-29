
# ------------------------------------------------------------------------------
#  Copyright (c) 2022 Dimitri Kroon
#
#  SPDX-License-Identifier: GPL-2.0-or-later
#  This file is part of plugin.video.cinetree
# ------------------------------------------------------------------------------

import logging
from enum import Enum

from codequick import Script
from codequick.support import logger_id

from resources.lib import fetch
from resources.lib import errors
from resources.lib import utils
from resources.lib.ctree.ct_data import create_collection_item
from resources.lib import storyblok


STRM_INFO_UNAVAILABLE = 30921

logger = logging.getLogger(logger_id + '.ct_api')
base_url = ''

GENRES = ('Action', 'Adventure', 'Biography', 'Comedy', 'Coming-of-age', 'Crime', 'Drama', 'Documentary',
          'Family', 'Fantasy', 'History', 'Horror', 'Mystery', 'Sci-Fi', 'Romance', 'Thriller')


def get_jsonp_url(slug, force_refresh=False):
    """Append *slug* to the base path for .js requests and return the full url.

    Part of the base url is a unique number (timestamp) that changes every so often. We obtain
    that number from Cinetree's main page and cache it for future requests.

    """
    global base_url

    if not base_url or force_refresh:
        import re

        resp = fetch.get_document('https://cinetree.nl')
        match = re.search(r'href="([\w_/]*?)manifest\.js" as="script">', resp, re.DOTALL)
        base_url = 'https://cinetree.nl' + match.group(1)
        logger.debug("New jsonp base url: %s", base_url)

    url = base_url + slug
    return url


def get_jsonp(path):
    from resources.lib.jsonp import parse, parse_simple

    url = get_jsonp_url(path)
    try:
        resp = fetch.get_document(url)
    except errors.HttpError as err:
        if err.code == 404:
            # Due to reuselanguageinvoker and the timestamp in the path, the path may become
            # invalid if the plugin is active for a long time.
            url = get_jsonp_url(path, force_refresh=True)
            resp = fetch.get_document(url)
            # Although the timestamps are not the same, expect storyblok's cache version to have been updated as well
            storyblok.clear_cache_version()
        else:
            raise

    if '__NUXT_' in resp[:16]:
        resp_dict = parse(resp)
    else:
        resp_dict = parse_simple(resp)
    return resp_dict


def get_recommended():
    """Return the uuids of the hero items on the subscription page"""
    data, _ = storyblok.get_url('stories//films-en-documentaires',
                                params={'from_release': 'undefined', 'resolve_relations': 'menu,selectedBy'})
    page_top = data['story']['content']['top']
    for section in page_top:
        if section['component'] == 'row-featured-films':
            return section['films']
    return []


def get_subscription_films():
    """Return a list of ID's of the current subscription films"""
    resp = fetch.get_json('https://api.cinetree.nl/films/svod')
    return resp


def create_stream_info_url(film_uuid, slug=None):
    """Return the url to the stream info (json) document.

    Create the url from the uuid. If the uuid is not available, obtain the
    uuid from the film's details page.

    """
    import re

    if not film_uuid:
        try:
            data = storyblok.story_by_name(slug)
            film_uuid = data['uuid']
            # url = get_jsonp_url(slug + '/payload.js')
            # js_doc = fetch.get_document(url)
            # match = re.search(r'.uuid="([\w-]{36})";', js_doc)
            # film_uuid = match[1]
        except(errors.FetchError, TypeError, KeyError):
            logger.error("Unable to obtain uuid from film details of '%s'.", slug, exc_info=True)
            raise errors.FetchError(Script.localize(STRM_INFO_UNAVAILABLE))

    url = 'https://api.cinetree.nl/films/' + film_uuid
    return url


def get_stream_info(url):
    """Return a dict containing urls to the m3u8 playlist, subtitles, etc., for a specific
    film or trailer.

    """
    data = fetch.fetch_authenticated(fetch.get_json, url)
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


def get_watched_films(finished=False):
    """Get the list of 'Mijn Films' to continue watching

    """
    # Request the list of 'my films' and use only those that have only partly been played.
    resp = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/watch-history')
    history = {film['assetId']: film for film in resp if 'playtime' in film.keys()}
    my_films, _ = storyblok.stories_by_uuids(history.keys())

    finished_films = []
    watched_films = []

    for film in my_films:
        duration = utils.duration_2_seconds(film['content'].get('duration', 0))
        if duration - history[film['uuid']]['playtime'] < max(20, duration * 0.02):
            finished_films.append(film)
        else:
            watched_films.append(film)
    return finished_films if finished else watched_films


def get_rented_films():
    resp = fetch.fetch_authenticated(fetch.get_json, 'https://api.cinetree.nl/purchased')
    # contrary to watched, this returns a plain list of uuids
    if resp:
        rented_films, _ = storyblok.stories_by_uuids(resp)
        return rented_films
    else:
        return resp


def get_preferred_collections():
    """Get a short list of the currently preferred collection.

    This is a short selection of all available collections that the user gets
    presented on the website when he clicks on 'huur films'
    """
    data = get_jsonp('films/payload.js')['fetch']
    for k, v in data.items():
        if k.startswith('data-v'):
            return (create_collection_item(col_data) for col_data in v['collections'])


def get_collections():
    """Get a list of all available collections
    Which, by the way, are not exactly all collections, but those the website shows as 'all'.
    To get absolutely all collections, request them from storyblok.
    """
    data = get_jsonp('collecties/payload.js')
    return (create_collection_item(col_data) for col_data in data['data'][0]['collections'])


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
