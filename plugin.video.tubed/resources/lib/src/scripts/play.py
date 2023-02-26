# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from ..routes import play


def invoke(context, video_id, playlist_id='', prompt_subtitles=False, start_offset=None):
    play.invoke(context, video_id, playlist_id, prompt_subtitles, start_offset)
