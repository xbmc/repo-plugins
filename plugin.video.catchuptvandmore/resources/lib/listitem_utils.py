# -*- coding: utf-8 -*-
"""
    Catch-up TV & More
    Copyright (C) 2016  SylvainCecchetto

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
"""

# The unicode_literals import only has
# an effect on Python 2.
# It makes string literals as unicode like in Python 3
from __future__ import unicode_literals

from codequick import Script

from resources.lib.favourites import add_fav_context
from resources.lib.labels import LABELS


def get_item_label(item_id):
    label = item_id
    if item_id in LABELS:
        label = LABELS[item_id]
        if isinstance(label, int):
            label = Script.localize(label)
    return label


def item2dict(item):
    # Need to use same keywords as
    # https://scriptmodulecodequick.readthedocs.io/en/latest/_modules/codequick/listing.html#Listitem.from_dict
    # in order to be able to directly use `Listitem.from_dict` later
    item_dict = {}
    item_dict['subtitles'] = item.subtitles
    item_dict['art'] = dict(item.art)
    item_dict['info'] = dict(item.info)
    item_dict['stream'] = dict(item.stream)
    item_dict['context'] = list(item.context)
    item_dict['properties'] = dict(item.property)
    item_dict['params'] = item.params
    item_dict['label'] = item.label
    return item_dict


def item_post_treatment(item, **kwargs):
    """
    Optional keyworded arguments:
    - is_playable (bool) (default: False)
    - is_downloadable (bool) (default: False)
    """

    # Add `Download` context menu to the item
    # if is_downloadable is given and True
    if kwargs.get('is_downloadable', False):
        item.context.script(item.path,
                            Script.localize(LABELS['Download']),
                            download_mode=True,
                            **item.params)

    # Add `Add to favourites` context menu to the item
    add_fav_context(item, item2dict(item), **kwargs)

    return
