# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import json

from codequick import Listitem, Resolver, Route, Script
import urlquick
from kodi_six import xbmcgui
from resources.lib.addon_utils import Quality

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = "https://www.tv7.fr"

GENERIC_HEADERS = {"User-Agent": web_utils.get_random_ua()}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse('nav', attrs={"class": "main-menu"})

    for category in root.iterfind('.//li'):
        titre = category.find('.//span[@class="lib"]').text
        if 'Le direct' != titre:
            url = URL_ROOT + category.find('.//a').get('href')
            item = Listitem()
            item.label = titre
            item.set_callback(list_contents, url=url, page='0')
            item_post_treatment(item)
            yield item


@Route.register
def list_contents(plugin, url, page, **kwargs):
    resp = urlquick.get(url + '?page=%s' % page, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse()
    root_emission = root.find('.//ul[@class="listing_vids"]')

    for program_datas in root_emission.iterfind(".//li"):
        item = Listitem()
        item.label = program_datas.find(".//h3").text
        item.art['thumb'] = item.art['landscape'] = URL_ROOT + program_datas.find(".//img").get('src')
        video_url = URL_ROOT + program_datas.find('.//a').get('href')
        item.set_callback(get_video_url, url=video_url)
        item_post_treatment(item)
        yield item

    for pagination in root.iterfind('.//div'):
        if pagination.get('class') is not None and 'pagination' in pagination.get('class'):
            for npage in pagination.iterfind('.//a'):
                if npage.text == '>>':
                    if npage.get('class') is None:
                        yield Listitem.next_page(url=url, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin, url, **kwargs):
    resp = urlquick.get(url, headers=GENERIC_HEADERS, max_age=-1)
    root = resp.parse("div", attrs={"class": "HDR_VISIO"})
    url = URL_ROOT + root.get('data-url') + '&mode=html'
    resp = urlquick.get(url, headers=GENERIC_HEADERS, max_age=-1)
    datas = json.loads(resp.text)

    video_url = datas['files']['auto']

    urls = []
    definition = ['auto', '3072p', '1536p', '768p', '384p']
    for source in datas['files']:
        urls.append(datas['files'][source])

    quality = Script.setting.get_string('quality')
    if quality == Quality['WORST']:
        video_url = urls[len(urls) - 1]
    elif quality == Quality['BEST']:
        video_url = urls[1]
    elif quality == Quality['DEFAULT']:
        video_url = urls[0]
    else:
        video_url = urls[xbmcgui.Dialog().select(Script.localize(30180), definition)]

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="mpd")


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    resp = urlquick.get(URL_ROOT, headers={"User-Agent": web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse("div", attrs={"class": "HDR_VISIO"})
    live_url = URL_ROOT + root.get('data-url') + '&mode=html'

    resp = urlquick.get(live_url, headers=GENERIC_HEADERS, max_age=-1)
    datas = json.loads(resp.text)
    video_url = datas['files']['auto']

    return resolver_proxy.get_stream_with_quality(plugin, video_url, manifest_type="mpd")
