# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route, Script
import urlquick

from resources.lib import download, resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TODO
# Replay add emissions

URL_ROOT_FR = 'https://francais.rt.com'

URL_LIVE_FR = URL_ROOT_FR + '/en-direct'

URL_ROOT_EN = 'https://www.rt.com'

URL_LIVE_EN = URL_ROOT_EN + '/on-air/'

URL_LIVE_AR = 'https://arabic.rt.com/live/'

URL_LIVE_ES = 'https://actualidad.rt.com/en_vivo'

DESIRED_LANGUAGE = Script.setting['rt.language']

CATEGORIES_VIDEOS_FR = {
    URL_ROOT_FR + '/magazines': 'Magazines',
    URL_ROOT_FR + '/documentaires': 'Documentaires',
    URL_ROOT_FR + '/videos': 'Vidéos'
}

CATEGORIES_VIDEOS_EN = {URL_ROOT_EN + '/shows/': 'Shows'}


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    CATEGORIES_VIDEOS = eval('CATEGORIES_VIDEOS_%s' % DESIRED_LANGUAGE)
    for category_url, category_title in list(CATEGORIES_VIDEOS.items()):
        if 'magazines' in category_url or 'shows' in category_url:
            item = Listitem()
            item.label = category_title
            item.set_callback(list_programs,
                              item_id=item_id,
                              next_url=category_url)
            item_post_treatment(item)
            yield item
        elif 'documentaires' in category_url:
            item = Listitem()
            item.label = category_title
            item.set_callback(list_videos_documentaries,
                              item_id=item_id,
                              next_url=category_url,
                              page='0')
            item_post_treatment(item)
            yield item
        elif 'videos' in category_url:
            item = Listitem()
            item.label = category_title
            item.set_callback(list_videos, item_id=item_id, page='0')
            item_post_treatment(item)
            yield item


@Route.register
def list_programs(plugin, item_id, next_url, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(next_url)
    if DESIRED_LANGUAGE == 'FR':
        root = resp.parse("ul", attrs={"class": "media-rows"})

        for program_datas in root.iterfind("li"):
            program_title = program_datas.find('.//img').get('alt')
            program_url = program_datas.find('.//a').get('href')
            program_image = program_datas.find('.//img').get('data-src')
            program_plot = program_datas.find('.//p').text

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.info['plot'] = program_plot
            item.set_callback(list_videos_programs,
                              item_id=item_id,
                              next_url=program_url,
                              page='0')
            item_post_treatment(item)
            yield item
    elif DESIRED_LANGUAGE == 'EN':
        root = resp.parse("ul", attrs={"class": "card-rows"})

        for program_datas in root.iterfind("li"):
            program_title = program_datas.find('.//img').get('alt')
            program_url = eval(
                'URL_ROOT_%s' %
                DESIRED_LANGUAGE) + program_datas.find('.//a').get('href')
            program_image = program_datas.find('.//img').get('data-src')

            item = Listitem()
            item.label = program_title
            item.art['thumb'] = item.art['landscape'] = program_image
            item.set_callback(list_videos_programs,
                              item_id=item_id,
                              next_url=program_url,
                              page='0')
            item_post_treatment(item)
            yield item


@Route.register
def list_videos_programs(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url)
    program_id_values = re.compile(r'\/program\.(.*?)\/prepare').findall(
        resp.text)

    if len(program_id_values) > 0:
        if DESIRED_LANGUAGE == 'FR':
            resp2 = urlquick.get(
                eval('URL_ROOT_%s' % DESIRED_LANGUAGE) + '/listing/program.%s/prepare/idi-listing/10/%s' %
                (program_id_values[0], page))
            root = resp2.parse("div", attrs={"data-role": "content"})

            for video_datas in root.iterfind(".//div[@data-role='item']"):
                video_title = video_datas.find(
                    ".//span[@class='st-idi-episode-card__title']").text.strip()
                video_image_datas = video_datas.find(
                    ".//span[@class='st-idi-episode-card__image']").get('style')
                video_image = re.compile(r'url\((.*?)\)').findall(
                    video_image_datas)[0]
                video_url = video_datas.find('.//a').get('href')
                video_plot = video_datas.find(
                    ".//span[@class='st-idi-episode-card__summary']").text.strip()

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info['plot'] = video_plot

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_url=video_url)
                item_post_treatment(item, is_playable=True, is_downloadable=True)
                yield item

        elif DESIRED_LANGUAGE == 'EN':
            resp2 = urlquick.get(
                eval('URL_ROOT_%s' % DESIRED_LANGUAGE) + '/listing/program.%s/prepare/latestepisodes/10/%s' %
                (program_id_values[0], page))

            try:
                root = resp2.parse("ul", attrs={"class": "card-rows js-listing__list"})
            except Exception:
                root = None

            if root is not None:
                for video_datas in root.iterfind(".//li"):
                    video_title = video_datas.find(".//img").get('alt')
                    video_image = video_datas.find(".//img").get('data-src')
                    video_url = eval(
                        'URL_ROOT_%s' %
                        DESIRED_LANGUAGE) + video_datas.find('.//a').get('href')
                    video_plot = video_datas.find(
                        ".//div[@class='card__summary ']").text.strip()

                    item = Listitem()
                    item.label = video_title
                    item.art['thumb'] = item.art['landscape'] = video_image
                    item.info['plot'] = video_plot

                    item.set_callback(get_video_url,
                                      item_id=item_id,
                                      video_url=video_url)
                    item_post_treatment(item, is_playable=True, is_downloadable=True)
                    yield item

        yield Listitem.next_page(item_id=item_id,
                                 next_url=next_url,
                                 page=str(int(page) + 1))

    else:
        if DESIRED_LANGUAGE == 'FR':
            root = resp.parse("ul", attrs={"class": "telecast-list js-listing__list"})
            for video_datas in root.iterfind(".//li"):
                video_title = video_datas.find('.//img').get('alt')
                video_image = video_datas.find('.//img').get('data-src')
                video_url = eval('URL_ROOT_%s' % DESIRED_LANGUAGE) + video_datas.find(
                    './/a').get('href')
                video_plot = video_datas.find(
                    ".//p[@class='card__summary ']").text.strip()

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info['plot'] = video_plot

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_url=video_url)
                item_post_treatment(item, is_playable=True, is_downloadable=True)
                yield item

        elif DESIRED_LANGUAGE == 'EN':
            root = resp.parse("ul", attrs={"class": "card-rows js-listing__list"})
            for video_datas in root.iterfind(".//li"):
                video_title = video_datas.find('.//img').get('alt')
                video_image = video_datas.find('.//img').get('data-src')
                video_url = eval('URL_ROOT_%s' % DESIRED_LANGUAGE) + video_datas.find(
                    './/a').get('href')
                video_plot = video_datas.find(
                    ".//div[@class='card__summary ']").text.strip()

                item = Listitem()
                item.label = video_title
                item.art['thumb'] = item.art['landscape'] = video_image
                item.info['plot'] = video_plot

                item.set_callback(get_video_url,
                                  item_id=item_id,
                                  video_url=video_url)
                item_post_treatment(item, is_playable=True, is_downloadable=True)
                yield item


@Route.register
def list_videos_documentaries(plugin, item_id, next_url, page, **kwargs):

    resp = urlquick.get(next_url)
    program_id = re.compile(r'\/program\.(.*?)\/prepare').findall(resp.text)[0]

    resp2 = urlquick.get(
        eval('URL_ROOT_%s' % DESIRED_LANGUAGE) + '/listing/program.%s/prepare/telecasts/10/%s' % (program_id, page))

    root = resp2.parse("ul", attrs={"class": "telecast-list js-listing__list"})

    for video_datas in root.iterfind(
            ".//div[@class='telecast-list__content']"):
        video_title = video_datas.find(".//img").get('alt')
        video_image = video_datas.find(".//img").get('data-src')
        video_url = eval(
            'URL_ROOT_%s' %
            DESIRED_LANGUAGE) + video_datas.find('.//a').get('href')
        video_plot = video_datas.find(
            ".//p[@class='card__summary ']").text.strip()

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        item.info['plot'] = video_plot

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id,
                             next_url=next_url,
                             page=str(int(page) + 1))


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    resp = urlquick.get(
        eval('URL_ROOT_%s' % DESIRED_LANGUAGE) + '/listing/type.Videoclub.category.videos/noprepare/video-rows/10/%s' %
        (page))

    root = resp.parse("ul", attrs={"class": "media-rows js-listing__list"})

    for video_datas in root.iterfind(".//div[@class='media-rows__content']"):
        video_title = video_datas.find(".//img").get('alt')
        video_image = video_datas.find(".//img").get('data-src')
        video_url = eval(
            'URL_ROOT_%s' %
            DESIRED_LANGUAGE) + video_datas.find('.//a').get('href')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    yield Listitem.next_page(item_id=item_id, page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url, max_age=-1)
    if 'youtube.com/embed' in resp.text:
        video_id = re.compile(r'youtube\.com\/embed\/(.*?)[\?\"]').findall(
            resp.text)[0]
        return resolver_proxy.get_stream_youtube(plugin, video_id,
                                                 download_mode)

    final_url = re.compile(r'file\: \"(.*?)\"').findall(resp.text)
    if download_mode:
        return download.download_video(final_url)

    return final_url


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):
    final_language = kwargs.get('language', DESIRED_LANGUAGE)

    if final_language == 'AR':
        url_live = URL_LIVE_AR
        resp = urlquick.get(url_live, max_age=-1)
        live_id = re.compile(r'youtube\.com\/embed\/(.*?)[\?\"]').findall(resp.text)[0]
        return resolver_proxy.get_stream_youtube(plugin, live_id, False)

    if final_language == 'FR':
        url_live = URL_LIVE_FR
        resp = urlquick.get(url_live, max_age=-1)
        return re.compile(r'file\: \"(.*?)\"').findall(resp.text)[0]

    if final_language == 'ES':
        url_live = URL_LIVE_ES
        resp = urlquick.get(url_live, max_age=-1)
        live_id = re.compile(r'youtube\.com\/embed\/(.*?)[\?\"]').findall(resp.text)[0]
        return resolver_proxy.get_stream_youtube(plugin, live_id, False)

    # Use EN by default
    url_live = URL_LIVE_EN
    resp = urlquick.get(url_live, max_age=-1)
    live_id = re.compile(r'youtube\.com\/embed\/(.*?)[\?\"]').findall(resp.text)[0]
    return resolver_proxy.get_stream_youtube(plugin, live_id, False)
