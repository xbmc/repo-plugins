# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from enum import Enum


class SUBTITLE_LANGUAGE(Enum):  # pylint: disable=invalid-name
    NONE = 0
    PROMPT = 1
    CURRENT_W_FALLBACK = 2
    CURRENT = 3
    CURRENT_WO_ASR = 4
