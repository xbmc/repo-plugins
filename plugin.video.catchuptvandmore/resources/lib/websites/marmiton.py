# -*- coding: utf-8 -*-
'''
    Catch-up TV & More
    Copyright (C) 2017  SylvainCecchetto
    This file is part of Catch-up TV & More.
    Catch-up TV & More is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    Catch-up TV & More is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License along
    with Catch-up TV & More; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from resources.lib.codequick import Route, Resolver, Listitem, youtube

from resources.lib.labels import LABELS
from resources.lib.menu_utils import item_post_treatment


def website_entry(plugin, item_id, **kwargs):
    """
    First executed function after website_bridge
    """
    return root(plugin)


def root(plugin, **kwargs):
    item = Listitem()
    item.label = 'Marmiton (youtube)'
    item.set_callback(list_videos_youtube,
                      channel_youtube='UCmKCpHH5ATFMURHTRC2jLyA')
    item_post_treatment(item)
    yield item


@Route.register
def list_videos_youtube(plugin, channel_youtube, **kwargs):

    yield Listitem.youtube(channel_youtube)
