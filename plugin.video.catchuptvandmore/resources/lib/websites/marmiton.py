# -*- coding: utf-8 -*-
# Copyright: (c) 2017, SylvainCecchetto
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Listitem, Route

from resources.lib.menu_utils import item_post_treatment


@Route.register
def website_root(plugin, **kwargs):
    item = Listitem()
    item.label = 'Marmiton (youtube)'
    item.set_callback(list_videos_youtube, channel_youtube='UCmKCpHH5ATFMURHTRC2jLyA')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_youtube(plugin, channel_youtube, **kwargs):

    yield Listitem.youtube(channel_youtube)
