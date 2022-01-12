# -*- coding: utf-8 -*-
"""

    Copyright (C) 2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

import sys

from kodi_six import xbmc  # pylint: disable=import-error


def strip_transcode(url):
    url = url.replace('&transcode=0', '')
    url = url.replace('&transcode=1', '')
    return url


if __name__ == '__main__':
    info_tag = sys.listitem.getVideoInfoTag()

    try:
        plugin_url = info_tag.getFilenameAndPath()
    except AttributeError:
        plugin_url = xbmc.getInfoLabel('ListItem.FileNameAndPath')

    plugin_url = strip_transcode(plugin_url)
    plugin_url += '&transcode=1'
    xbmc.executebuiltin('PlayMedia(%s)' % plugin_url)
