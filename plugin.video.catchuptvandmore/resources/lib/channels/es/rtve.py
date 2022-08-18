# -*- coding: utf-8 -*-
# Copyright: (c) 2016-2020, Team Catch-up TV & More
# GNU General Public License v2.0+ (see LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt)

# This file is part of Catch-up TV & More

from __future__ import unicode_literals

from codequick import Listitem, Resolver, Route
import urlquick

from resources.lib.menu_utils import item_post_treatment


# TO DO

URL_ROOT = 'https://www.rtve.es'

URL_LIVE_STREAM = 'https://rtvelivestream-lvlt.rtve.es/{0}/{0}_main.m3u8'
# Live Id

URL_CATEGORIES = URL_ROOT + '/alacarta/categorieslist.shtml?ctx=tve'


@Route.register
def list_categories(plugin, item_id, **kwargs):
    """
    - ...
    """
    resp = urlquick.get(URL_CATEGORIES)
    root = resp.parse()

    for category_datas in root.iterfind(".//h2"):
        category_title = category_datas.find('.//a').get('title').replace('ver todos los programas de ', '')
        category_url = category_datas.find('.//a').get('href').replace('/1/', '/\%/')

        item = Listitem()
        item.label = category_title
        item.set_callback(list_programs,
                          item_id=item_id,
                          category_url=category_url,
                          page='1')
        item_post_treatment(item)
        yield item


@Route.register
def list_programs(plugin, item_id, category_url, **kwargs):
    """
    - ...
    """
    return False


@Resolver.register
def get_live_url(plugin, item_id, **kwargs):

    return URL_LIVE_STREAM.format(item_id)
