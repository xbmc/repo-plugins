# -*- coding: utf-8 -*-
"""
    Copyright (C) 2020 Tubed (plugin.video.tubed)

    This file is part of plugin.video.tubed

    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

import arrow
import xbmcgui  # pylint: disable=import-error

from ..lib.txt_fmt import bold
from ..lib.url_utils import unquote


def invoke(context, title, timestamp):
    if title and '%' in title:
        title = unquote(title)

    humanized = arrow.get(timestamp).to('local').humanize()
    if humanized.startswith('in'):
        message = context.i18n('%s is scheduled to start %s') % (bold(title), humanized)

    else:
        message = context.i18n('%s was scheduled to start %s') % (bold(title), humanized)

    xbmcgui.Dialog().ok(context.i18n('Upcoming'), message)
