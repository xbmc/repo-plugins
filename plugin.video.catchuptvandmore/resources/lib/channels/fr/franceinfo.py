# -*- coding: utf-8 -*-
# Copyright: (c) JUL1EN094, SPM, SylvainCecchetto
# Copyright: (c) 2016, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import time

from codequick import Listitem, Resolver, Route, Script, utils
from kodi_six import xbmcgui
import urlquick

from resources.lib import download, resolver_proxy, web_utils
from resources.lib.addon_utils import Quality
from resources.lib.menu_utils import item_post_treatment

# Channels:
#     * Franceinfo

URL_API = utils.urljoin_partial('http://api-front.yatta.francetv.fr')

URL_LIVE_JSON = URL_API('standard/edito/directs')

URL_JT_ROOT = 'https://stream.francetvinfo.fr/stream/program/list.json/origin/jt/support/long/page/1/nb/1000'

URL_MAGAZINES_ROOT = 'https://stream.francetvinfo.fr/stream/program/list.json/origin/magazine/support/long/page/1/nb/1000'

URL_AUDIO_ROOT = 'https://stream.francetvinfo.fr/stream/program/list.json/origin/audio/support/long/page/1/nb/1000'

URL_STREAM_ROOT = 'https://stream.francetvinfo.fr'

URL_VIDEOS_ROOT = 'https://stream.francetvinfo.fr/stream/contents/list/videos.json/support/long'

URL_MODULES_ROOT = 'https://stream.francetvinfo.fr/stream/contents/list/videos-selection.json/support/long'

URL_INFO_OEUVRE = 'https://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/?idDiffusion=%s&catalogue=Info-web'
# Param : id_diffusion

DESIRED_QUALITY = Script.setting['quality']


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    category_title = 'Videos'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos,
                      item_id=item_id,
                      next_url=URL_VIDEOS_ROOT,
                      page='1')
    item_post_treatment(item)
    yield item

    category_title = 'Audio'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs, item_id=item_id, next_url=URL_AUDIO_ROOT)
    item_post_treatment(item)
    yield item

    category_title = 'JT'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs, item_id=item_id, next_url=URL_JT_ROOT)
    item_post_treatment(item)
    yield item

    category_title = 'Magazines'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_programs,
                      item_id=item_id,
                      next_url=URL_MAGAZINES_ROOT)
    item_post_treatment(item)
    yield item

    category_title = 'Modules'
    item = Listitem()
    item.label = category_title
    item.set_callback(list_videos,
                      item_id=item_id,
                      next_url=URL_MODULES_ROOT,
                      page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_programs(plugin, item_id, next_url, **kwargs):

    json_parser = urlquick.get(next_url).json()

    for program_datas in json_parser['programs']:
        program_title = program_datas['label']
        program_url = URL_STREAM_ROOT + program_datas['url']
        program_plot = program_datas['description']

        item = Listitem()
        item.label = program_title
        item.info['plot'] = program_plot
        item.set_callback(list_videos,
                          item_id=item_id,
                          next_url=program_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, next_url, page, **kwargs):

    json_parser = urlquick.get(next_url + '/page/' + page).json()
    if 'videos' in json_parser:
        list_id = 'videos'
    elif 'contents' in json_parser:
        list_id = 'contents'

    at_least_one_item = False
    for video_datas in json_parser[list_id]:
        at_least_one_item = True
        video_title = video_datas['title']
        video_plot = video_datas['description']
        date_epoch = video_datas['firstPublicationDate']
        date_value = time.strftime('%Y-%m-%d', time.localtime(date_epoch))
        video_url = URL_STREAM_ROOT + video_datas['url']
        video_image = ''
        for media_datas in video_datas['medias']:
            if 'urlThumbnail' in media_datas:
                video_image = URL_STREAM_ROOT + media_datas['urlThumbnail']
                break

        item = Listitem()
        item.label = video_title
        item.info['plot'] = video_plot
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info.date(date_value, '%Y-%m-%d')

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    if at_least_one_item:
        yield Listitem.next_page(item_id=item_id,
                                 next_url=next_url,
                                 page=str(int(page) + 1))
    else:
        plugin.notify(plugin.localize(30718), '')
        yield False


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    json_parser = urlquick.get(video_url).json()

    method = None
    id_diffusion = ''
    urls = []
    for media in json_parser['content']['medias']:
        if 'catchupId' in media:
            method = 'id_diffusion'
            id_diffusion = media['catchupId']
            break

        if 'streams' in media:
            method = 'stream_videos'
            for stream in media['streams']:
                urls.append((stream['format'], stream['url']))
            break

        if 'sourceUrl' in media:
            return media['sourceUrl']

    if method == 'id_diffusion':
        return resolver_proxy.get_francetv_video_stream(plugin, id_diffusion, download_mode)

    if method == 'stream_videos':
        url_hd = ''
        url_default = ''
        for url in urls:
            if 'hd' in url[0]:
                url_hd = url[1]
            url_default = url[1]

        if DESIRED_QUALITY == Quality['DIALOG']:
            items = []
            for url in urls:
                items.append(url[0])
            seleted_item = xbmcgui.Dialog().select(
                plugin.localize(30709), items)

            if seleted_item == -1:
                return False
            url_selected = items[seleted_item][1]
            if url_hd != '':
                url_selected = url_hd
            else:
                url_selected = url_default
        else:
            if url_hd != '':
                url_selected = url_hd
            else:
                url_selected = url_default
        if download_mode:
            return download.download_video(url_selected)
        return url_selected

    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    json_parser = urlquick.get(URL_LIVE_JSON,
                               headers={'User-Agent': web_utils.get_random_ua()},
                               max_age=-1).json()

    for live in json_parser["result"]:
        if live["channel"] == item_id:
            live_datas = live["collection"][0]["content_has_medias"]
            liveId = ''
            for live_data in live_datas:
                if "si_direct_id" in live_data["media"]:
                    liveId = live_data["media"]["si_direct_id"]
            return resolver_proxy.get_francetv_live_stream(plugin, liveId)
