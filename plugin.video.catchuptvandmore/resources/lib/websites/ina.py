# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto; 2024, darodi
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

import re
import xml.etree.ElementTree as ET

import urlquick
# noinspection PyUnresolvedReferences
from codequick import Listitem, Resolver, Route, utils
# noinspection PyUnresolvedReferences
from codequick.utils import urljoin_partial, strip_tags

from resources.lib.menu_utils import item_post_treatment
from resources.lib.web_utils import html_parser


URL_ROOT = 'http://www.ina.fr'
url_constructor = urljoin_partial(URL_ROOT)

ASSET_URL_PATTERN = re.compile(r'asset-details-url=\"(.*?)\"')


def find_element_with_class_name(parent_element, class_name, text_only=False):
    element = None
    for e in parent_element.iterfind(".//div[@class]"):
        if class_name not in e.get('class').split(' '):
            continue
        element = e
        break
    if not text_only:
        return element
    return '' if element is None else element.text


@Route.register
def website_root(plugin, **kwargs):
    item = Listitem.search(list_search)
    item_post_treatment(item)
    yield item

    categories = [
        ('Homepage', homepage),
        ("L'INA éclaire l'actu", ina_eclaire_actu),
        ('Madelen', madelen)
    ]

    for category in categories:
        item = Listitem()
        item.label = category[0]
        item.set_callback(category[1])
        item_post_treatment(item)
        yield item


@Route.register
def homepage(plugin, **kwargs):
    resp = urlquick.get(URL_ROOT)
    root_elem = resp.parse("div", attrs={"id": "block-hub-content"})
    for url_tag in root_elem.iterfind(".//div[@class]"):
        if "block-hub" not in url_tag.get('class').split(' '):
            continue

        title = url_tag.find(".//h2[@class='title-bloc']")
        if title is None:
            continue
        item = Listitem()
        item.label = strip_tags(ET.tostring(title, encoding='unicode', method='html'))
        bloc_thematique = find_element_with_class_name(url_tag, "blocThematique")
        if bloc_thematique is None:
            continue

        item.set_callback(list_bloc_thematique, bloc_thematique=bloc_thematique)
        yield item


@Route.register
def ina_eclaire_actu(plugin, **kwargs):
    resp = urlquick.get(url_constructor("/ina-eclaire-actu"))
    root_elem = resp.parse("div", attrs={"id": "block-hub-content"})
    for url_tag in root_elem.iterfind(".//div[@class='gtm-print-list']"):
        item = Listitem()
        title = url_tag.findtext(".//h2[@class='title-bloc']")
        if title is None:
            continue
        item.label = re.sub(r'^\s*|\s*$', '', title)
        carrousel = url_tag.find(".//div[@d-role='carrousel']")
        item.set_callback(list_carousel, carrousel=carrousel)
        yield item


@Route.register
def madelen(plugin, **kwargs):
    # TODO Add Premium Account INA Madelen (purchase an account to test)
    # https://github.com/Catch-up-TV-and-More/plugin.video.catchuptvandmore/issues/287
    plugin.notify(plugin.localize(30600), plugin.localize(30721))
    yield False


@Route.register
def list_search(plugin, search_query, **kwargs):
    url_search = url_constructor("/ajax/recherche?q={search_query}&modified=term".format(search_query=search_query))
    resp = urlquick.get(url_search, max_age=-1)

    root_elem = None
    try:
        root_elem = resp.parse("div", attrs={"id": "search-result"})
    except RuntimeError:
        yield False

    if root_elem is not None:
        for link in root_elem.iterfind('.//a'):
            item = Listitem()
            video_url = url_constructor(link.get('href'))
            title = link.findtext(".//div[@class='title-bloc-small mt-3']")
            if title is None:
                continue
            item.label = re.sub(r'^\s*|\s*$', '', title)
            image = link.find(".//img")
            if image is not None:
                item.art["thumb"] = image.get("data-src")
            item.set_callback(play_video, url=video_url)
            yield item


@Route.register
def list_carousel(plugin, carrousel, **kwargs):
    for link in carrousel.iterfind('.//a'):
        item = Listitem()
        video_url = url_constructor(link.get('href'))
        item.label = link.findtext(".//div[@class='title-bloc-small']")
        image = link.find(".//img")
        if image is not None:
            item.art["thumb"] = image.get("data-src")
        item.set_callback(play_video, url=video_url)
        yield item


@Route.register
def list_bloc_thematique(plugin, bloc_thematique, **kwargs):
    for link in bloc_thematique.iterfind('.//a'):
        item = Listitem()
        video_url = url_constructor(link.get('href'))
        item.label = find_element_with_class_name(link, "title-bloc-small", True)
        item.info['plot'] = find_element_with_class_name(link, "texte-bloc", True)
        image = link.find(".//img")
        if image is not None:
            item.art["thumb"] = image.get("data-src")
        item.set_callback(play_video, url=video_url)
        yield item


@Resolver.register
def play_video(plugin, url):
    resp = urlquick.get(url, max_age=-1)
    asset_url_array = ASSET_URL_PATTERN.findall(resp.text)
    if len(asset_url_array) == 0:
        return False
    asset_url = asset_url_array[0]
    asset_url_escaped = html_parser.unescape(asset_url)
    json_resp_api = urlquick.get(asset_url_escaped, max_age=-1).json()
    if "resourceUrl" in json_resp_api:
        resource_url = json_resp_api["resourceUrl"]
        # TODO use resolver_proxy.get_stream_with_quality
        return resource_url
    return False
