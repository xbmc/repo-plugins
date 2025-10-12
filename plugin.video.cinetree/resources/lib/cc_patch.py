
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2025 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-2.0.txt.
# ------------------------------------------------------------------------------

import xbmcgui


def patch_listitem():
    """Setting parameter `offscreen` to true when creating `ListItems`
    can significantly speed up the creation long lists.

    Since codequick doesn't use this parameter, this function monkey
    patches `xmbcgui.Listitem` with an alternative class that sets
    `offscreen` to True by default.

    .. note ::
        To make sure that everything references this patched ListItem apply
        this patch before codequick is imported, or any other module that
        uses xbmcgui.ListItem.
    """
    class PatchedListItem(xbmcgui.ListItem):
        def __init__(self,
                     label: str = '',
                     label2: str = '',
                     path: str = '',
                     offscreen: bool = True):
            # print("**** Using patched Listitem ****")
            super().__init__(label, label2, path, offscreen)

    xbmcgui.ListItem = PatchedListItem


patch_listitem()


from codequick import Route, Listitem
# noinspection PyProtectedMember
from codequick.listing import strip_formatting


def patch_cc_route():
    """
    Fixes a bug in codequick v1.0.2. by monkey patching
    ``codequick.route.Route.__call__(...)``.

    The problem is that decorating a callback with ``@Route.Register(cache_ttl=60)``
    does not lead to the items the callback returns being cached.

    This will be fixed if you call ``patch_cc_route()`` in the addon before
    ``codequick.run()`` is called.

    """
    original_call = Route.__call__

    def patched_call(self, route, args, kwargs):
        self.__dict__.update(route.parameters)
        original_call(self, route, args, kwargs)

    Route.__call__ = patched_call


def patch_label_prop():
    """Addresses an annoyance in codequick v1.0.2. by monkey patching
    ``codequick.listing.Listitem.label`` property.

    The problem is that setting label on a codequick Listitem will always
    set info['title'] as well, overwriting any existing value.
    It is very nice that codequick ensures that relevant values are set, but
    a more appropriate approach would be to only set those the addon has not
    already set.

    This will be fixed if you call ``patch_label_prop()`` in the addon before
    ``codequick.run()`` is being called.

    """
    def label_setter(self, label):
        """Set label and only copy to fields that do not have a value"""
        self.listitem.setLabel(label)
        unformatted_label = strip_formatting("", label)
        self.params.setdefault("_title_", unformatted_label)
        self.info.setdefault("title", unformatted_label)

    Listitem.label = Listitem.label.setter(label_setter)
