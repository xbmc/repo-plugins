
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import time
import logging
import requests

from codequick.support import logger_id


logger = logging.getLogger('.'.join((logger_id, __name__)))

token = 'srRWSyWpIEzPm4IzGFBrkAtt'
base_url = 'https://api.storyblok.com/v2/cdn/'
cache_version = 'undefined'


def clear_cache_version():
    global cache_version
    cache_version = 'undefined'


def get_url(path, **kwargs):
    global cache_version

    headers = {
        'Referer': 'https://www.cintree.nl/',
        'Origin': 'https://www.cintree.nl',
        'Accept': 'application/json',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
    }
    params = {'token': token, 'version': 'published', 'cv': cache_version}
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))

    p = kwargs.pop('params', None)

    if isinstance(p, dict):
        params.update(p)
    elif isinstance(p, str):
        params = '{}&token={}&version=published&cv={}'.format(p, token, cache_version)
    elif p is not None:
        raise TypeError("Keyword argument 'params' must be of type dict or string")

    resp = requests.get(base_url + path, headers=headers, params=params, **kwargs)
    if resp.status_code == 429:
        # too many requests, wait a second and try once again
        logger.warning("Too many requests per second to storyblok")
        time.sleep(1)
        resp = requests.get(base_url + path, headers=headers, params=params, **kwargs)

    resp.raise_for_status()
    data = resp.json()
    cv = data.get('cv')
    if cv:
        cache_version = cv
    return data, resp.headers


def _get_url_page(path, page=None, items_per_page=None, **kwargs):
    """Make a webrequest to url `path`. Optionally return only a subset of the available
    items by passing in 'page` and 'items_per_page`.

    Returns a tuple of 2 elements. The first is the list of items, second is the
    total number of available items.
    """
    if items_per_page is not None and not 0 < items_per_page <= 100:
        raise ValueError("items_per_page must be 1 - 100.")

    if page is not None and page < 1:
        raise ValueError("page number < 1.")

    # noinspection PyTypeChecker
    num_to_fetch = min(100, items_per_page) if items_per_page and page else 100
    cur_page = int(page) if page else 1
    stories = []

    params = kwargs.get('params', {})

    while True:
        params.update({'page': cur_page, 'per_page': num_to_fetch})
        data, headers = get_url(path, **kwargs)
        new_stories = data.get('stories')
        stories.extend(new_stories)
        total = int(headers.get('total', 0))
        if page or len(stories) >= total or not new_stories:
            break
        cur_page += 1

    logger.info(" {} storyblok stories retrieved".format(len(stories)))
    return stories, total


def stories_by_uuids(uuids, page=None, items_per_page=None):
    """Return the list of stories defined by the uuid in uuids.

    :param uuids: A single uuid as string or an iterable of uuid's referring
        to a stories on Storyblok
    :param page: Return the items of page number *page*. If None, return all items.
    :param items_per_page: Number of items to return per page.
    :return: A tuple of a list of stories end the total number of available stories.

    """
    # Storyblok returns ALL stories when no uuid's are passed, which is not the desired result at all.
    if not uuids:
        return [], 0

    if isinstance(uuids, str):
        uuids = (uuids, )

    query_str = {'token': token,
                 'by_uuids': ','.join(uuids),
                 }

    stories = _get_url_page('stories', page, items_per_page, params=query_str)
    # print(" {} stories retrieved".format(len(stories[0])))
    return stories


def story_by_name(slug: str):
    """Return a single story by its path.

    :param slug: The so-called 'full slug' - path to the story without base path.
        like 'films/kapsalon-romy'

    """
    path = 'stories/' + slug.lstrip('/')
    params = {
        'resolve_relations': 'selectedBy',
        'from_release': 'undefined'
    }
    data, _ = get_url(path, params=params)
    return data['story']


def search(search_term=None, genre=None, duration_min=None, duration_max=None,
           country=None, page=None, items_per_page=None):

    # query_str = {'starts_with': 'films/'}
    query_str = {'filter_query[component][in]': 'film'}

    if not any((search_term, genre, duration_min, duration_max, country)):
        raise ValueError("No filter defined; at least one parameter must have a value")

    # search_term hits every match in each and every field; returns a lot of results.
    # if search_term is not None:
    #     query_str['search_term'] = search_term
    if search_term is not None:
        query_str['filter_query[title][like]'] = '*' + search_term + '*'
    if genre is not None:
        query_str['filter_query[genre][like]'] = '*' + genre + '*'
    if country is not None:
        query_str['filter_query[country][in]'] = country
    if duration_max is not None or duration_min is not None:
        duration_max = duration_max or 500
        duration_min = duration_min or 0
        if not 0 <= duration_min < duration_max:
            raise ValueError("Invalid duration")
        query_str['filter_query[duration][gt_int]'] = duration_min,
        query_str['filter_query[duration][lt_int]'] = duration_max

    return _get_url_page('stories', page, items_per_page, params=query_str)
