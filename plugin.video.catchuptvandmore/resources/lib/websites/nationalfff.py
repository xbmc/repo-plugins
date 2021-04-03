# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Route, Resolver, Listitem
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment

URL_ROOT = 'https://ffftv.fff.fr'

URL_REPLAY = URL_ROOT + '/playback/loadmore/national/%s'

# TODO Add Live


@Route.register
def website_root(plugin, item_id, **kwargs):
    """Add modes in the listing"""
    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(list_videos, item_id=item_id, page='0')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):
    """Build videos listing"""

    resp = urlquick.get(URL_REPLAY % page)
    root = resp.parse()

    for video_datas in root.iterfind(".//a"):
        if video_datas.get('href') is not None:
            video_title = video_datas.find('.//h3').text
            video_image = video_datas.find('.//img').get('src')
            video_url = URL_ROOT + video_datas.get('href')

            item = Listitem()
            item.label = video_title
            item.art['thumb'] = item.art['landscape'] = video_image

            if 'overlayDescription' in video_datas:
                date_value = video_datas['overlayDescription'].split('|')[0]
                item.info.date(date_value, '%d/%m/%Y')

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
    """Get video URL and start video player"""

    resp = urlquick.get(video_url,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    root = resp.parse()
    video_datas = root.find(".//video[@class='player-fff vjs-fluid video-js margin_b16 resp_iframe']")

    data_account = video_datas.get('data-account')
    data_video_id = video_datas.get('data-video-id')
    data_player = video_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)
