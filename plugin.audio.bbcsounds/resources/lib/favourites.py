
# ------------------------------------------------------------------------------
#  Copyright (c) 2026 Dimitri Kroon.
#  This file is part of plugin.audio.bbcsounds.
#  SPDX-License-Identifier: GPL-3.0-or-later
#  See LICENSE.txt or https://www.gnu.org/licenses/gpl-3.0.txt
# ------------------------------------------------------------------------------

from __future__ import annotations
from resources.lib.log import log
from resources.lib.exceptions import AccountError


class _Favourites:
    """A class to maintain a cache of urns of programmes that the user has
    bookmarked or subscribed to.

    """
    def __init__(self):
        self._subscription_urns: set | False | None = None
        self._bookmark_urns: set | False | None = None

    @property
    def subscriptions(self) -> set:
        """A set of urns of programmes that the user has subscribed to."""
        if self. _subscription_urns is None:
            self.refresh()
        return self._subscription_urns if self._subscription_urns else set()

    @property
    def bookmarks(self) -> set:
        """A set of urns of programmes that the user has bookmarked."""
        if self._bookmark_urns is None:
            self.refresh()
        return self._bookmark_urns if self._bookmark_urns else set()

    def refresh(self):
        """Get all subscriptions and bookmarks from the BBC.

        """
        from resources.lib import fetch
        from resources.lib import parse

        try:
            resp = fetch.get(parse.BASE_URL + 'my')
        except AccountError:
            self._bookmark_urns = False
            self._subscription_urns = False
        else:
            data = parse.scrape_json_data(resp.text)
            rails = data['props']['pageProps']['dehydratedState']['queries'][1]['state']['data']['data']
            self.scrape_urns(rails)

    def scrape_urns(self, rail_data: dict):
        """Get all subscription and bookmark urns from the given page data."""
        self._bookmark_urns = False
        self._subscription_urns = False
        for rail in rail_data:
            if rail['id'] == 'favourites':
                try:
                    self._bookmark_urns = set(item['urn'] for item in rail['data'])
                except Exception as err:
                    log("Favourites Error: failed to collect bookmark urns: %r", err)

            elif rail['id'] == 'follows':
                try:
                    self._subscription_urns = set(item['urn'] for item in rail['data'])
                except Exception as err:
                    log("Favourites Error: failed to collect subscription urns: %r", err)

    def clear(self):
        """Clear the cache back to an uninitialised state."""
        self._subscription_urns = None
        self._bookmark_urns = None


favourites = _Favourites()
