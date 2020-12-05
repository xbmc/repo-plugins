# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from html import unescape
from urllib.parse import parse_qs
from urllib.parse import urlparse

import xbmcgui  # pylint: disable=import-error
import xbmcplugin  # pylint: disable=import-error

from ..constants.media import LOGO_SMALL
from ..generators.channel import channel_generator
from ..generators.data_cache import get_cached
from ..generators.playlist import playlist_generator
from ..generators.video import video_generator
from ..lib.url_utils import extract_urls


def invoke(context, video_id):
    cached_payload = get_cached(context, context.api.videos, [video_id])
    cached_video = cached_payload.get(video_id, {})
    cached_snippet = cached_video.get('snippet', {})

    extracted_urls = []
    items = []
    success = True

    description = unescape(cached_snippet.get('description', ''))
    if not description:
        success = False

    if description:
        extracted_urls = extract_urls(description)
        if not extracted_urls:
            success = False

    if success:
        parsed_urls = parse_urls(context, extracted_urls)

        if parsed_urls.get('channel_ids'):
            payload = context.api.channels(parsed_urls.get('channel_ids'), fields='items(kind,id)')
            items += channel_generator(context, payload.get('items', []))

        if parsed_urls.get('playlist_ids'):
            payload = context.api.playlists(parsed_urls.get('playlist_ids'),
                                            fields='items(kind,id,snippet(title))')
            items += playlist_generator(context, payload.get('items', []))

        if parsed_urls.get('video_ids'):
            payload = context.api.videos(parsed_urls.get('video_ids'), fields='items(kind,id)')
            items += video_generator(context, payload.get('items', []))

        success = len(items) > 0

    if success:
        xbmcplugin.addDirectoryItems(context.handle, items, len(items))

    else:
        xbmcgui.Dialog().notification(
            context.addon.getAddonInfo('name'),
            context.i18n('There were no links found in the description'),
            LOGO_SMALL,
            sound=False
        )

    xbmcplugin.endOfDirectory(context.handle, succeeded=success)


def parse_urls(context, urls):
    channel_ids = []
    playlist_ids = []
    video_ids = []

    for url in urls:
        parsed_url = urlparse(url)
        if parsed_url.netloc.endswith(('youtube.com', 'youtu.be')):

            if parsed_url.path.startswith('/channel/'):
                try:
                    channel_ids.append(parsed_url.path.lstrip('/channel/').split('/')[0])
                except IndexError:
                    pass

            elif parsed_url.path.endswith('/playlist'):
                try:
                    playlist_ids.append(parse_qs(parsed_url.query).get('list', [])[0])
                except IndexError:
                    continue

            elif (parsed_url.path.startswith('/embed/') or
                  parsed_url.path.endswith('/watch') or
                  parsed_url.netloc == 'youtu.be'):

                if parsed_url.path.startswith('/embed/') or parsed_url.netloc == 'youtu.be':
                    try:
                        video_ids.append(parsed_url.path.lstrip('/embed').lstrip('/').split('/')[0])
                    except IndexError:
                        continue

                elif parsed_url.path.endswith('/watch'):
                    try:
                        video_ids.append(parse_qs(parsed_url.query).get('v', [])[0])
                    except IndexError:
                        continue

            elif (parsed_url.path.startswith(('/user/', '/c/')) or
                  len(parsed_url.path.lstrip('/').split('/')) == 1):
                try:
                    username = \
                        parsed_url.path.lstrip('/user').lstrip('/c').lstrip('/').split('/')[0]
                except IndexError:
                    continue

                if not username:
                    continue

                payload = context.api.channel_by_username(username)

                channel_id = payload.get('items', [{}])[0].get('id', '')
                if not channel_id:
                    continue

                channel_ids.append(channel_id)

    return {
        'channel_ids': channel_ids,
        'playlist_ids': playlist_ids,
        'video_ids': video_ids
    }
