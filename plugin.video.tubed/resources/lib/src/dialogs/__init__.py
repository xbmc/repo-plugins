# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""


class DialogActiveException(Exception):
    pass


__all__ = ['DialogActiveException', 'autoplay_related', 'common', 'sign_in', 'utils']
