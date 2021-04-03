# -*- coding: utf-8 -*-
# Copyright: (c) 2019, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
from builtins import str
import re

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib import resolver_proxy, web_utils
from resources.lib.menu_utils import item_post_treatment


# TODO
# Add more button

URL_ROOT = 'https://www.bfmtv.com'

URL_ROOT_REGION = 'https://www.bfmtv.com/%s'

URL_LIVE_BFM_REGION = URL_ROOT_REGION + '/en-direct/'

URL_REPLAY_BFM_REGION = URL_ROOT_REGION + '/videos/?page=%s'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    Build categories listing
    - Tous les programmes
    - Séries
    - Informations
    - ...
    """
    item = Listitem()
    item.label = plugin.localize(30701)
    item.set_callback(list_videos, item_id=item_id, page='1')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos(plugin, item_id, page, **kwargs):

    if 'paris' in item_id:
        resp = urlquick.get(URL_ROOT + '/mediaplayer/videos-bfm-paris/?page=%s' % page,
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    else:
        resp = urlquick.get(URL_REPLAY_BFM_REGION % (item_id.replace('bfm', ''), page),
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    root = resp.parse()

    for video_datas in root.iterfind(
            ".//article[@class='duo_liste content_item content_type content_type_video']"
    ):
        if 'https' not in video_datas.find('.//a').get('href'):
            video_url = URL_ROOT + video_datas.find('.//a').get('href')
        else:
            video_url = video_datas.find('.//a').get('href')
        video_image = ''  # TODO image
        video_title = video_datas.find('.//img').get('alt')

        item = Listitem()
        item.label = video_title
        item.art['thumb'] = item.art['landscape'] = video_image

        item.set_callback(get_video_url,
                          item_id=item_id,
                          video_url=video_url)
        item_post_treatment(item, is_playable=True, is_downloadable=True)
        yield item

    # More videos...
    yield Listitem.next_page(item_id=item_id,
                             page=str(int(page) + 1))


@Resolver.register
def get_video_url(plugin,
                  item_id,
                  video_url,
                  download_mode=False,
                  **kwargs):

    resp = urlquick.get(video_url)

    data_account = re.compile(r'accountid="(.*?)"').findall(resp.text)[0]
    data_video_id = re.compile(r'videoid="(.*?)"').findall(resp.text)[0]
    data_player = re.compile(r'playerid="(.*?)"').findall(resp.text)[0]

    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id,
                                                    download_mode)


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    if 'paris' in item_id:
        resp = urlquick.get(URL_ROOT + '/mediaplayer/live-bfm-paris/',
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)
    else:
        resp = urlquick.get(URL_LIVE_BFM_REGION % item_id.replace('bfm', ''),
                            headers={'User-Agent': web_utils.get_random_ua()},
                            max_age=-1)

    root = resp.parse()
    live_datas = root.find(".//div[@class='video_block']")
    data_account = live_datas.get('accountid')
    data_video_id = live_datas.get('videoid')
    data_player = live_datas.get('playerid')
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)
