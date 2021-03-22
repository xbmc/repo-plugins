# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy
from resources.lib.menu_utils import item_post_treatment


# TO DO
# Add Next Button (More videos to get)
# Readd date without beautiful soup

URL_ROOT = 'https://www.caledonia.nc'


@Route.register
def list_programs(plugin, item_id, **kwargs):
    """
    Build programs listing
    - Les feux de l'amour
    - ...
    """
    resp = urlquick.get(URL_ROOT)
    root = resp.parse()

    for program_datas in root.iterfind(".//a"):
        if program_datas.get('href'):
            if 'emission/' in program_datas.get('href'):
                program_title = program_datas.text
                if URL_ROOT in program_datas.get('href'):
                    program_url = program_datas.get('href')
                else:
                    program_url = URL_ROOT + program_datas.get('href')

                item = Listitem()
                item.label = program_title
                item.set_callback(list_videos,
                                  item_id=item_id,
                                  program_url=program_url)
                item_post_treatment(item)
                yield item


@Route.register
def list_videos(plugin, item_id, program_url, **kwargs):

    resp = urlquick.get(program_url)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//div[@class='block-yt-playlist col-lg-4 col-12 mb-4']"):
        video_title = video_datas.find('.//h3').text.strip()
        video_image = video_datas.find(
            ".//div[@class='wrapper-gdpr-yt block-video-yt']"
        ).get('data-ytthumbnail')
        video_id = video_datas.find(
            ".//div[@class='wrapper-gdpr-yt block-video-yt']"
        ).get('data-ytid')
        # date_value = utils.strip_tags(video_datas.find(".//div[@class='wrap-infos mt-3']")).text

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image
        # try:
        #     item.info.date(date_value, '%d/%m/%Y')
        # except:
        #     pass

        # try:
        #     item.info.date(date_value, '%d-%m-%Y')
        # except:
        #     pass

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_id=video_id)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_id,
                  download_mode=False,
                  **kwargs):

    return resolver_proxy.get_stream_youtube(plugin, video_id, download_mode)
