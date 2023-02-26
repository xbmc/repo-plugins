# -*- coding: utf-8 -*-
"""

    Copyright (C) 2012-2018 Twitch-on-Kodi

    This file is part of Twitch-on-Kodi (plugin.video.twitch)

    SPDX-License-Identifier: GPL-3.0-only
    See LICENSES/GPL-3.0-only for more information.
"""

from ..addon import utils
from ..addon.common import kodi
from ..addon.constants import ADAPTIVE_SOURCE_TEMPLATE, LINE_LENGTH
from ..addon.converter import JsonListItemConverter
from ..addon.utils import i18n


def route(api, content_type, target_id=None, name=None, video_id=None, remove=False, clip_id=None):
    converter = JsonListItemConverter(LINE_LENGTH)
    if not remove:
        videos = None
        if not target_id or not name:
            return
        if content_type == 'video' and video_id:
            videos = api.get_vod(video_id)
        elif content_type == 'clip' and clip_id:
            videos = api.get_clip(clip_id)
        elif content_type == 'stream':
            videos = api.get_live(name)
        if videos:
            use_ia = utils.use_inputstream_adaptive()
            if use_ia and not any(v['name'] == 'Adaptive' for v in videos) and (content_type != 'clip'):
                videos.append(ADAPTIVE_SOURCE_TEMPLATE)
            result = converter.select_video_for_quality(videos)
            if result:
                quality = result['name']
                result = utils.add_default_quality(content_type, target_id, name, quality)
                if result:
                    kodi.notify(msg=i18n('default_quality_set') % (content_type, quality, name), sound=False)
    else:
        result = utils.remove_default_quality(content_type)
        if result:
            name = result[result.keys()[0]]['name']
            kodi.notify(msg=i18n('removed_default_quality') % (content_type, name), sound=False)
