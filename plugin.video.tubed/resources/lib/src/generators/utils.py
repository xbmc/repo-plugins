# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import re


def get_thumbnail(snippet):
    thumbnails = snippet.get('thumbnails', {})
    thumbnail = thumbnails.get('standard', thumbnails.get('high', {}))

    if not thumbnail:
        thumbnail = thumbnails.get('medium', thumbnails.get('default', {}))

    return thumbnail.get('url', '')


def get_fanart(branding_settings):
    banners = branding_settings.get('image', {})
    banner = banners.get('bannerTvImageUrl', banners.get('bannerTvHighImageUrl', ''))

    if not banner:
        banner = banners.get('bannerTvMediumImageUrl', banners.get('bannerTvLowImageUrl', ''))

    return banner


def get_chapters(description):
    def timestamp_to_seconds(stamp):
        seconds = 0
        stamp = stamp.split(':')

        if len(stamp) == 4:
            seconds = int(stamp[0]) * 24 * 60 * 60
            stamp = stamp[1:]

        return float(seconds + sum(int(value) * 60 ** index for index, value in
                                   enumerate(reversed(stamp))))

    chapter_sequence = re.compile(r"(?P<timestamp>[0-9:]+:[0-9]{2})\s(?P<title>[^\n]+)\n",
                                  re.MULTILINE)

    chapters = []
    for sequence in chapter_sequence.finditer(description):
        timestamp_label = sequence.group('timestamp')
        timestamp_seconds = timestamp_to_seconds(timestamp_label)

        title = sequence.group('title').strip()

        chapters.append((timestamp_seconds, timestamp_label, title))

    return chapters
