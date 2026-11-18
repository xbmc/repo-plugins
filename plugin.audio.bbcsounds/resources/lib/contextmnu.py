
# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

import xbmc
import xbmcgui

from resources.lib.route import script
from resources.lib import fetch


TXT_DLG_HEADER = 'BBC Sounds'
ID_MSG_REMOVE_LISTING_CONFIRM = 30323


@script
def handle_subscription(_, urn: str, operation: str):
    """Handles both subscription and bookmarks

    The BBC regards all brands as subscriptions and all episodes as bookmarks.
    """
    from resources.lib.favourites import favourites

    if operation == 'add':
        resp = fetch.post('https://rms.api.bbc.co.uk/v2/my/activities', json={'urn': urn})
    elif operation == 'remove':
        resp = fetch.delete('https://rms.api.bbc.co.uk/v2/my/activities/' + urn)
    else:
        raise ValueError(f"Invalid subscription operation: '{operation}'.")
    resp.raise_for_status()
    favourites.refresh()
    xbmc.executebuiltin('Container.Refresh')


@script
def remove_listening(plugin, urn, brand_title, episode_title):
    urn_parts = urn.split(':')
    full_title = f'{brand_title} - {episode_title}'
    if xbmcgui.Dialog().yesno(
            TXT_DLG_HEADER,
            plugin.translate(ID_MSG_REMOVE_LISTING_CONFIRM).format(title=full_title)):
        fetch.post('https://rms.api.bbc.co.uk/v2/my/programmes/plays/remove',
                   json={"pid": urn_parts[-1], "resource_type": urn_parts[-2]}
                   )
        xbmc.executebuiltin('Container.Refresh')
