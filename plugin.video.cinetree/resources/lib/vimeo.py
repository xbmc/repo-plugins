
# ------------------------------------------------------------------------------
#  Copyright (c) 2022-2023 Dimitri Kroon.
#  This file is part of plugin.video.cinetree.
#  SPDX-License-Identifier: GPL-2.0-or-later.
#  See LICENSE.txt
# ------------------------------------------------------------------------------

import xbmcgui

from .fetch import get_json


def get_steam_url(video_url, max_resolution=None):
    """Return a direct url to a stream of the specified video.

    Cinetree returns a trailer url like "https://vimeo.com/334256156"
    The config, however, is obtained from https://player.vimeo.com/video

    """
    if video_url.endswith('/'):
        video_url = video_url[:-1]

    video_id = video_url.split('/')[-1]
    config_url = ''.join(('https://player.vimeo.com/video/', video_id, '/config'))
    config = get_json(config_url)

    stream_config = config['request']['files']['progressive']
    if stream_config:
        return 'file', get_progressive_url(stream_config, max_resolution)

    stream_config = config['request']['files']['hls']
    if stream_config:
        return 'hls', get_hls_url(stream_config)

    return None, None


def get_progressive_url(stream_config, max_resolution):
        max_video_height = get_height(max_resolution)
        best_match = {}
        matched_h = 0

        for stream in stream_config:
            h = stream['height']
            if matched_h < h <= max_video_height:
                best_match = stream
                matched_h = h

        return best_match.get('url', '')


def get_hls_url(stream_config):
    def_cdn = stream_config.get('default_cdn')
    urls = stream_config['cdns'].get(def_cdn)
    return urls['url']


def get_height(resolution):
    if resolution is None:
        return xbmcgui.getScreenHeight() or 9999
    if isinstance(resolution, (str, bytes)):
        resolution = resolution.split('x', 1)[-1]
    return int(resolution)
