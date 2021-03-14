# -*- coding: utf-8 -*-
# Copyright: (c) 2018, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals
import re

from codequick import Resolver
import urlquick

from resources.lib import resolver_proxy, web_utils


# TODO
# Add Videos, Replays ?

URL_ROOT = 'http://www.japanet.co.jp'

URL_LIVE = URL_ROOT + '/shopping/movie/movie_player_dx.html'


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    resp = urlquick.get(URL_LIVE,
                        headers={'User-Agent': web_utils.get_random_ua()},
                        max_age=-1)
    data_account = re.compile(r'data-account\'\,\'(.*?)\'').findall(
        resp.text)[0]
    data_player = re.compile(r'data-player\'\,\'(.*?)\'').findall(resp.text)[0]
    data_video_id = re.compile(r'data-video-id\'\,\'(.*?)\'').findall(
        resp.text)[0]
    return resolver_proxy.get_brightcove_video_json(plugin, data_account,
                                                    data_player, data_video_id)
