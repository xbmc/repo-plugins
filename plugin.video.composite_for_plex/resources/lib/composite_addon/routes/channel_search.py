# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2019 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from six.moves.urllib_parse import quote
from six.moves.urllib_parse import unquote

from ..addon.logger import Logger
from ..addon.processing.plex_plugins import process_plex_plugins
from ..addon.strings import i18n
from ..plex import plex

LOG = Logger()


def run(context, url, prompt):
    """
        When we encounter a search request, branch off to this function to generate the keyboard
        and accept the terms.  This URL is then fed back into the correct function for
        onward processing.
    """
    context.plex_network = plex.Plex(context.settings, load=True)

    if prompt:
        prompt = unquote(prompt)
    else:
        prompt = i18n('Enter search term')

    keyboard = xbmc.Keyboard('', i18n('Search...'))
    keyboard.setHeading(prompt)
    keyboard.doModal()
    if keyboard.isConfirmed():
        text = keyboard.getText()
        LOG.debug('Search term input: %s' % text)
        url = url + '&query=' + quote(text)
        process_plex_plugins(context, url)
