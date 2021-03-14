# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Get informations of replay ?

URL_ROOT = 'https://%s.bfmtv.com'

URL_REPLAY = {
    'rmcstory': URL_ROOT + '/mediaplayer-replay/nouveautes/',
    'rmcdecouverte': URL_ROOT + '/mediaplayer-replay/'
}

URL_LIVE = URL_ROOT + '/mediaplayer-direct/'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """

    resp = urlquick.get(URL_REPLAY[item_id] % item_id)
    root = resp.parse("div", attrs={"class": "list_21XUu"})

    for category_datas in root.iterfind(".//a"):
        category_title = category_datas.text
        category_url = URL_ROOT % item_id + category_datas.get('href')

        item = Listitem()
        item.label = category_title

        item.set_callback(list_videos,
                          item_id=item_id,
                          category_url=category_url)
        item_post_treatment(item)
        yield item


@Route.register
def list_videos(plugin, item_id, category_url, **kwargs):

    resp = urlquick.get(category_url)
    root = resp.parse()

    for video_datas in root.iterfind(".//div[@class='root_qT0Me']"):
        subtitle = video_datas.find(".//p[@class='subtitle_1hI_I']")
        subtitle = subtitle.text if subtitle is not None else None

        title = video_datas.find(".//p[@class='title_1APl2']")
        title = title.text if title is not None else None

        item = Listitem()

        if title is not None and subtitle is not None:
            item.label = title + ' - ' + subtitle
        elif title is not None:
            item.label = title
        else:
            item.label = 'No title'

        video_image = video_datas.find('.//img').get('src')
        video_url = URL_ROOT % item_id + video_datas.find('.//a').get('href')
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()
    video_datas = root.find(".//div[@class='next-player player_2t_e9']")

    data_account = video_datas.get('data-account')
    data_video_id = video_datas.get('data-video-id')
    data_player = video_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE % item_id,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)

    root = resp.parse()
    live_datas = root.find(".//div[@class='next-player player_2t_e9']")

    data_account = live_datas.get('data-account')
    data_video_id = live_datas.get('data-video-id')
    data_player = live_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)
