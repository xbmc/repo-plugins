# -*- coding: utf-8 -*-
# Copyright: (c) 2022, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, Script
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial

from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://www.sonuma.be'
url_constructor = urljoin_partial(URL_ROOT)

MAIN_PAGE_API = url_constructor('/Web2Store/service/pages/main')
ASSETS_API = url_constructor('/Web2Store/service/assets?links=true')
THESAURUS_API = url_constructor('/Web2Store/service/thesaurus')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "referrer": url_constructor('/homepage')
}


@Route.register
def website_root(plugin, item_id, **kwargs):
    #  Homepage / Accueil
    item = Listitem()
    item.label = plugin.localize(30731)
    item.set_callback(website_homepage, item_id)
    item_post_treatment(item)
    yield item

    # Recently added, les derniers ajouts
    item = Listitem()
    item.label = plugin.localize(30728)
    item.set_callback(latest, item_id)
    item_post_treatment(item)
    yield item

    # Search programs
    item = Listitem.search(list_search, item_id=item_id)
    item.label = plugin.localize(30715)
    item_post_treatment(item)
    yield item

    for i in yield_thematique(item_id):
        yield i


@Route.register
def website_homepage(plugin, item_id, **kwargs):
    resp = urlquick.get(MAIN_PAGE_API, headers=HEADERS, max_age=-1)
    json_parser = resp.json()
    for media_block in json_parser["mediaBlocks"]:
        item = Listitem()
        item.label = media_block["title"]
        item.set_callback(list_mediablock,
                          item_id=item_id,
                          mediablock=media_block)
        item_post_treatment(item)
        yield item


@Route.register(autosort=False, content_type="videos")
def list_search(plugin, search_query, item_id, start=0, **kwargs):
    if search_query is None or len(search_query) == 0:
        yield False

    rows = 50

    query = {
        "queryStr": "",
        "start": start,
        "rows": rows,
        "filter": None,
        "fields": [],
        "sortArr": [],
        "qform": {
            "fields": [
                {
                    "name": "text",
                    "type": "S",
                    "lines": [
                        {
                            "plus": "",
                            "values": [
                                "*%s*" % search_query
                            ]
                        },
                        {
                            "plus": "",
                            "values": [
                                "%s" % re.sub(r'\s+', '*', search_query)
                            ]
                        }
                    ]
                }
            ]
        }
    }

    resp = urlquick.post(ASSETS_API, json=query, headers=HEADERS, max_age=-1)
    json_parser = resp.json()

    num_found = json_parser["numFound"]
    if int(num_found) == 0:
        plugin.notify(plugin.localize(30718), '')
        yield False

    for i in yield_assets(json_parser):
        yield i

    new_start = (start + rows)
    if num_found is not None and int(num_found) > rows and new_start < num_found:
        yield Listitem.next_page(search_query=search_query, item_id=item_id, start=new_start, callback=list_search)


def yield_thematique(item_id):
    set_thematique = set(range(1, 13))
    set_thematique.add("divertissement")

    for i in set_thematique:
        thematique = "/thematique-"
        if isinstance(i, int) and i < 10:
            thematique += '0'
        thematique += str(i)

        resp = urlquick.get(THESAURUS_API + thematique, headers=HEADERS, max_age=-1)
        json_parser = resp.json()

        item = Listitem()
        item.label = json_parser["niceName"]
        item.set_callback(list_thematique,
                          item_id=item_id,
                          thematique_id=json_parser["id"])
        item_post_treatment(item)
        yield item


@Route.register(autosort=False, content_type="videos")
def list_thematique(plugin, item_id, thematique_id, start=0, **kwargs):
    rows = 25

    query = {
        "queryStr": "",
        "start": start,
        "rows": rows,
        "filter": None,
        "fields": [],
        "sortArr": [],
        "qform": {
            "fields": [
                {
                    "name": "thematiquesId",
                    "type": "S",
                    "lines": [
                        {
                            "plus": "",
                            "values": [
                                "%s" % thematique_id
                            ]
                        }
                    ]
                }
            ]
        }
    }

    resp = urlquick.post(ASSETS_API, json=query, headers=HEADERS, max_age=-1)
    json_parser = resp.json()

    num_found = json_parser["numFound"]
    if int(num_found) == 0:
        plugin.notify(plugin.localize(30718), '')
        yield False

    for i in yield_assets(json_parser):
        yield i

    new_start = (start + rows)
    if num_found is not None and int(num_found) > rows and new_start < num_found:
        yield Listitem.next_page(item_id=item_id,
                                 thematique_id=thematique_id,
                                 start=new_start,
                                 callback=list_thematique)


@Route.register(autosort=False, content_type="videos")
def latest(plugin, item_id, start=0, **kwargs):
    rows = 50

    query = {
        "queryStr": "*:*",
        "start": start,
        "rows": rows,
        "filter": None,
        "fields": [],
        "sortArr": [["datePublication", "desc"]],
        "qform": None
    }

    resp = urlquick.post(ASSETS_API, json=query, headers=HEADERS, max_age=-1)
    json_parser = resp.json()

    num_found = json_parser["numFound"]
    if int(num_found) == 0:
        plugin.notify(plugin.localize(30718), '')
        yield False

    for i in yield_assets(json_parser):
        yield i

    new_start = (start + rows)
    if num_found is not None and int(num_found) > rows and new_start < num_found:
        yield Listitem.next_page(item_id=item_id, start=new_start, callback=latest)


@Route.register(autosort=False, content_type="videos")
def list_mediablock(plugin, item_id, mediablock, start=0, **kwargs):
    query = mediablock['query']
    query['start'] = start
    query['rows'] = rows = 20

    resp = urlquick.post(ASSETS_API, json=query, headers=HEADERS, max_age=-1)
    json_parser = resp.json()

    num_found = json_parser["numFound"]
    if int(num_found) == 0:
        plugin.notify(plugin.localize(30718), '')
        yield False

    for i in yield_assets(json_parser):
        yield i

    new_start = (start + rows)
    if num_found is not None and int(num_found) > rows and new_start < int(num_found):
        yield Listitem.next_page(item_id=item_id, mediablock=mediablock, start=new_start, callback=list_mediablock)


def yield_assets(json_parser):
    for asset in json_parser["assets"]:
        item = Listitem()

        date = asset.get('date')
        if date is not None:
            trimmed_date = re.sub(r'\s', '', date)
            item.info.date(trimmed_date, "%Y-%m-%d")  # 1983-05-26

        video_url = asset['mediaURL']
        item.label = asset['titre']

        plot = asset.get('texteDoc')
        if plot is not None:
            item.info['plot'] = plot

        duration = asset.get('duration')
        if duration is not None:
            item.info['duration'] = int(float(duration))

        # https://www.sonuma.be/pictures/320px_85HDVMKB-376V-LPGU-GB5M-4U85LAS6P5D8.jpg
        item.art["thumb"] = url_constructor('/pictures/320px_' + asset['idSonuma'] + '.jpg')

        item.set_callback(play_video, url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def play_video(plugin, url, **kwargs):
    return url  # mp4, do not use resolver_proxy.get_stream_with_quality
