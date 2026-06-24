# -*- coding: utf-8 -*-
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 GaianHelmers
#
# ChannelMe! - "Add to Channel" context menu entry.
#
# Registered via addon.xml (kodi.context.item) on library TV shows, movie sets,
# and real (non-plugin) folders (NOT seasons - channels are built from whole
# shows / sets / folders). Reads the focused item's identity and hands it to the
# addon's addtochannel action, which pops a channel picker and appends it.

import urllib.parse

import xbmc

from resources.lib import contextitem

ADDON_URL = 'plugin://plugin.video.channelme/'


def main():
    params = contextitem.resolve()
    if not params:
        return
    query = urllib.parse.urlencode(dict(params, action='addtochannel'))
    xbmc.executebuiltin('RunPlugin({0}?{1})'.format(ADDON_URL, query))


if __name__ == '__main__':
    main()
