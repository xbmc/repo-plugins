# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json
import re
import xml.etree.ElementTree as ET

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

try:
    from html import unescape
except ImportError:
    from six.moves.html_parser import HTMLParser
    HTML_PARSER = HTMLParser()
    unescape = HTML_PARSER.unescape

# TO DO

# Info
# Add date of videos

URL_ROOT = 'https://lcp.fr'
URL_CATEGORIES = URL_ROOT + '/%s'
URL_VIDEO_REPLAY = 'http://play1.qbrick.com/config/avp/v1/player/' \
                   'media/%s/darkmatter/%s/'

URL_API_MOBILE = 'https://api-mobile.yatta.francetv.fr/'

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}

TAG_RE = re.compile(r'<[^>]+>')

# VideoID, AccountId

CATEGORIES = {
    'documentaires': 'Documentaires',
    'emissions': 'Emission A-Z'
}

CORRECT_MONTH = {
    'janvier': '01',
    'février': '02',
    'mars': '03',
    'avril': '04',
    'mai': '05',
    'juin': '06',
    'juillet': '07',
    'août': '08',
    'septembre': '09',
    'octobre': '10',
    'novembre': '11',
    'décembre': '12'
}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    for category_id, category_name in list(CATEGORIES.items()):
        category_url = URL_CATEGORIES % category_id

        item = Listitem()
        item.label = category_name
        if category_id == 'documentaires':
            item.set_callback(list_videos,
                              item_id=item_id,
                              videos_url=category_url,
                              page='0')
        else:
            item.set_callback(list_programs,
                              item_id=item_id,
                              category_url=category_url)
        item_post_treatment(item)
        yield item

    # Search items
    item = Listitem.search(list_videos_search, item_id=item_id, type_de_contenu='episode', page='0')
    item.label = 'Rechercher dans Replay Programme'
    item_post_treatment(item)
    yield item

    # Search items
    item = Listitem.search(list_videos_search, item_id=item_id, type_de_contenu='programme_unitaire', page='0')
    item.label = 'Rechercher dans Replay Documentaire'
    item_post_treatment(item)
    yield item


@Route.register(autosort=False)
def list_videos_search(plugin, search_query, item_id, type_de_contenu, page, **kwargs):
    if search_query is None or len(search_query) == 0:
        return False

    params = {
        'search_api_fulltext': search_query,
        'created': 'All',
        'f[0]': 'type_de_contenu:' + type_de_contenu,
        'page': page
    }
    response = urlquick.get(URL_ROOT + '/recherche', params=params, headers=GENERIC_HEADERS, max_age=-1)
    root = response.parse("div", attrs={"class": "view-content"})

    at_least_one_item = False
    for program_datas in root.iterfind(".//div[@class='views-row']"):
        if program_datas.findall(".//div[@class='views-field views-field-title']")[0].find(".//h2[@class='field-content']") is None:
            break
        program_desc = ''
        program_image = ''
        program_url = URL_ROOT + program_datas.find(".//a").get('href')
        program_label = program_datas.findall(".//div[@class='views-field views-field-title']")[0].find(".//h2[@class='field-content']").text
        program_title = program_datas.find(".//a").text
        if program_label is not None:
            program_title = program_label + program_title

        raw_root = ET.tostring(program_datas, encoding='utf-8').decode()
        list_desc = re.findall(r'<div class="views-field views-field-search-api-excerpt"><span class="field-content">(.*)</span>', raw_root)
        if len(list_desc) > 0:
            program_desc = list_desc[0]

        if program_datas.find(".//img") is not None:
            program_image = URL_ROOT + program_datas.find(".//img").get('src')
        else:
            continue
        program_date = program_datas.findall(".//div[@class='views-field views-field-created']")[0].find(".//span[@class='field-content']").text
        program_date_split = program_date.split(' ')
        if len(program_date_split) == 4:
            day = program_date_split[1]
            month = CORRECT_MONTH[program_date_split[2].lower()]
            year = program_date_split[3]
            date_value = '-'.join((year, month, day))
        else:
            date_value = None

        item = Listitem()
        item.label = program_title
        item.art['thumb'] = item.art['landscape'] = item.art["fanart"] = program_image
        item.info['plot'] = TAG_RE.sub('', unescape(program_desc))
        if date_value:
            item.info.date(date_value, '%Y-%m-%d')
        item.set_callback(get_video_url, item_id=item_id, video_url=program_url)
        item_post_treatment(item)
        at_least_one_item = True
        yield item

    if at_least_one_item:
        yield Listitem.next_page(item_id=item_id,
                                 search_query=search_query,
                                 type_de_contenu=type_de_contenu,
                                 page=str(int(page) + 1))
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    resp = urlquick.get(category_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for program_datas in root.iterfind(".//div[@class='sticky- views-row']"):
        program_label = program_datas.find(".//h2").text
        program_image = URL_ROOT + program_datas.find(".//img").get('src')
        program_url = program_datas.find(".//a").get('href')

        item = Listitem()
        item.label = program_label
        item.art['thumb'] = item.art['landscape'] = program_image
        item.set_callback(list_videos_programs,
                          item_id=item_id,
                          videos_url=program_url,
                          page='0')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos_programs(plugin, item_id, videos_url, page, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    resp = urlquick.get(videos_url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    all_videos_link = URL_ROOT + root.findall(".//div[@class='more-link']")[0].find(".//a").get('href')

    resp2 = urlquick.get(all_videos_link + '?page=%s' % page)
    root2 = resp2.parse("main", attrs={"class": "layout-3col__left-content"})

    for video_datas in root2.iterfind(".//div[@class='views-row']"):
        video_label = video_datas.findall(".//span[@class='field-content']")[1].text
        video_image = URL_ROOT + video_datas.find(".//img").get('src')
        video_url = URL_ROOT + video_datas.find(".//a").get('href')

        item = Listitem()
        item.label = video_label
        item.art['thumb'] = item.art['landscape'] = video_image
        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             videos_url=videos_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, videos_url, page, **kwargs):
    """
    Build programs listing
    - Journal de 20H
    - Cash investigation
    """
    resp = urlquick.get(videos_url + '?page=%s' % page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='views-row']"):
        for a in video_datas.iterfind(".//div[@class='views-field views-field-title-1 views-field-title']"):
            video_label = a.findall(".//span[@class='field-content']")[0].text
            video_image = URL_ROOT + video_datas.find(".//img").get('src')
            video_url = URL_ROOT + video_datas.find(".//a").get('href')

            item = Listitem()
            item.label = video_label
            item.art['thumb'] = item.art['landscape'] = video_image
            item.set_callback(get_video_url, item_id=item_id, video_url=video_url)
            item_post_treatment(item, is_playable=True, is_downloadable=True)
            yield item

    yield Listitem.next_page(item_id=item_id,
                             videos_url=videos_url,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url, headers=GENERIC_HEADERS, max_age=-1)
    if re.compile(r'"embedUrl":"https:.?/.?/www.dailymotion.com.?/video.?\/(.*)[\?\"]').findall(resp.text):
        video_id = re.compile(r'"embedUrl":"https:.?/.?/www.dailymotion.com.?/video.?\/(.*)[\?\"]').findall(resp.text)[0]
        return resolver_proxy.get_stream_dailymotion(plugin, video_id, download_mode)
    else:
        plugin.notify(plugin.localize(30600), plugin.localize(30716))
        return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    params = {'platform': 'apps'}
    resp = urlquick.get(URL_API_MOBILE + '/apps/channels/%s' % item_id, headers=GENERIC_HEADERS, params=params, max_age=-1)
    json_parser = json.loads(resp.text)

    for collection in json_parser['collections']:
        if 'live' == collection['type']:
            items_partner = collection['items'][0].get('partner')
            if items_partner is not None and 'partner_path' in items_partner:
                channel_path = items_partner.get("partner_path")
                if channel_path == item_id:
                    broadcast_id = items_partner.get("si_id")
                    return resolver_proxy.get_francetv_live_stream(plugin, broadcast_id)
