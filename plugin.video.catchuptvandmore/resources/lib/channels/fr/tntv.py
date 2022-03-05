# -*- coding: utf-8 -*-
# Copyright: (c) 2022, Joaopa
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils
import re

# TODO
# Add Replay

URL_ROOT = "https://www.tntv.pf/"

URL_LIVE = URL_ROOT + "/direct"


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE, headers={'User-Agent': web_utils.get_random_ua()}, max_age=-1)

    data_account_player = re.search('//players\.brightcove\.net/([0-9]+)/([A-Za-z0-9]+)_default/index\.html\?videoId=([0-9]+)', resp.text)
    data_account = data_account_player.group(1)
    data_player = data_account_player.group(2)
    data_video_id = data_account_player.group(3)

    return resolver_proxy.get_brightcove_video_json(plugin, data_account, data_player, data_video_id)
