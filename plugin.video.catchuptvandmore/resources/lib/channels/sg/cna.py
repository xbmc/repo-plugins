# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO
# Add Replay

URL_ROOT = "https://www.channelnewsasia.com"

URL_LIVE = URL_ROOT + "/watch"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)
    root = resp.parse()

    live_datas = root.find(".//video-js")
    data_account = live_datas.get('data-account')
    data_video_id = live_datas.get('data-video-id')
    data_player = live_datas.get('data-player')

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id)
