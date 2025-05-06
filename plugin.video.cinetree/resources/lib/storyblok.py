
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import os
import time
import logging

import urlquick
import xbmcplugin
from codequick.support import logger_id

from resources.lib.utils import CacheMgr


logger = logging.getLogger('.'.join((logger_id, __name__)))

token = 'srRWSyWpIEzPm4IzGFBrkAtt'
base_url = 'https://api.storyblok.com/v2/cdn/'

# Since their revisions change independently,
# cache Storyblok requests separately from Cinetree.
st_cache_dir = os.path.join(urlquick.CACHE_LOCATION, 'sbcache')
st_cache_mgr = CacheMgr(st_cache_dir)
st_cache_mgr.revalidate()


def get_url(path, **kwargs):
    cache_version = st_cache_mgr.version or 'undefined'

    headers = {
        'Referer': 'https://www.cintree.nl/',
        'Origin': 'https://www.cintree.nl',
        'Accept': 'application/json',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    }
    params = {'token': token, 'version': 'published', 'cv': cache_version}
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))

    p = kwargs.pop('params', None)
    if p:
        params.update(p)

    kwargs['raise_for_status'] = False
    if cache_version == 'undefined':
        # Requests with a Storyblok cache version of 'undefined' will only be sent once anyway.
        kwargs['max_age'] = -1
    with urlquick.Session(st_cache_dir) as s:
        resp = s.request('get', base_url + path, headers=headers, params=params, **kwargs)
    if resp.status_code == 429:
        # too many requests, wait a second and try once again
        logger.warning("Too many requests per second to storyblok")
        time.sleep(1)
        resp = urlquick.get(base_url + path, headers=headers, params=params, **kwargs)

    resp.raise_for_status()
    data = resp.json()
    st_cache_mgr.version = str(data.get('cv', ''))
    return data, resp.headers


def _get_url_page(path, page=None, items_per_page=None, **kwargs):
    """Make a webrequest to url `path`. Optionally return only a subset of the available
    items by passing in `page` and `items_per_page`.

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
    else:
        uuids = list(uuids)

    stories, total = _get_url_page(
            'stories',
            page,
            items_per_page,
            params={'by_uuids_ordered': ','.join(uuids)})
    if len(uuids) != len(stories):
        logger.warning("%s stories requested by uuid, only %s returned.", len(uuids), len(stories))
    return stories, total


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
    data, _ = get_url(path, params=params, max_age=-1)
    return data['story']


def search(search_term=None, genre=None, duration_min=None, duration_max=None,
           country=None, page=None, items_per_page=None, sort_method=0, sort_order=0):

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

    sort_field = {
        xbmcplugin.SORT_METHOD_DURATION: 'content.duration',
        xbmcplugin.SORT_METHOD_DATEADDED: 'content.startDate',
        xbmcplugin.SORT_METHOD_TITLE: 'content.title',
        xbmcplugin.SORT_METHOD_VIDEO_YEAR: 'content.productionYear'
    }.get(sort_method)
    if sort_field is not None:
        order = 'asc' if sort_order == 0 else 'desc'
        if sort_method == xbmcplugin.SORT_METHOD_DURATION:
            query_str['sort_by'] = ':'.join((sort_field, order, 'float'))
        else:
            query_str['sort_by'] = ':'.join((sort_field, order))

    return _get_url_page('stories', page, items_per_page, params=query_str)
