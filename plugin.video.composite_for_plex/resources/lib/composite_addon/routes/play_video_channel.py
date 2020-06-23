# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmcgui  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error

from ..addon.common import get_handle
from ..addon.constants import CONFIG
from ..addon.data_cache import DATA_CACHE
from ..addon.logger import Logger
from ..addon.playback import monitor_channel_transcode_playback
from ..addon.utils import get_master_server
from ..addon.utils import get_xml
from ..plex import plex

LOG = Logger()


def run(context, url, prefix=None, indirect=None, transcode=False):
    context.plex_network = plex.Plex(context.settings, load=True)

    server = context.plex_network.get_server_from_url(url)
    if 'node.plexapp.com' in url:
        server = get_master_server(context)

    session = None

    if indirect:
        # Probably should transcode this
        if url.startswith('http'):
            url = '/' + url.split('/', 3)[3]
            transcode = True

        url, session = server.get_universal_transcode(url)

    # if we have a plex URL, then this is a transcoding URL
    if 'plex://' in url:
        LOG.debug('found webkit video, pass to transcoder')
        if not prefix:
            prefix = 'system'
            url, session = server.get_universal_transcode(url)

        # Workaround for Kodi HLS request limit of 1024 byts
        if len(url) > 1000:
            LOG.debug('Kodi HLS limit detected, will pre-fetch m3u8 playlist')

            playlist = get_xml(context, url)

            if not playlist or '# EXTM3U' not in playlist:
                LOG.debug('Unable to get valid m3u8 playlist from transcoder')
                return

            server = context.plex_network.get_server_from_url(url)
            session = playlist.split()[-1]
            url = server.join_url(server.get_url_location(),
                                  'video/:/transcode/segmented/%s?t=1' % session)

    LOG.debug('URL to Play: %s ' % url)
    LOG.debug('Prefix is: %s' % prefix)

    # If this is an Apple movie trailer, add User Agent to allow access
    if 'trailers.apple.com' in url:
        url = url + '|User-Agent=QuickTime/7.6.9 (qtver=7.6.9;os=Windows NT 6.1Service Pack 1)'

    LOG.debug('Final URL is: %s' % url)
    xbmcplugin.setResolvedUrl(get_handle(), True, _list_item(url))

    _monitor_transcode(context, server, session, transcode)
    DATA_CACHE.delete_cache(True)


def _list_item(url):
    if CONFIG['kodi_version'] >= 18:
        return xbmcgui.ListItem(path=url, offscreen=True)
    return xbmcgui.ListItem(path=url)


def _monitor_transcode(context, server, session, transcode):
    if session and transcode:
        try:
            monitor_channel_transcode_playback(context, server, session)
        except:  # pylint: disable=bare-except
            LOG.debug('Unable to start transcode monitor')
    else:
        LOG.debug('Not starting monitor')
