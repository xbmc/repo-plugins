# -*- coding: utf-8 -*-
"""A small client for the REG-Vault catalogue.

Only one call is needed: look a game up by system and ROM hash. Kodi copies
the manual itself, from the URL handed back to it, so nothing is downloaded
here.

The service publishes a free tier of 1,000 metadata requests a day per address
and asks that it not be scraped in bulk, so requests are paced and a rate
limit response stops the run rather than being retried around.

No Kodi imports here, so it can be tested on its own.
"""

import http.client
import json
import time
import urllib.error
import urllib.request

BASE_URL = "https://api.regvault.org/api/v1"

#: Box art and screenshots are served off the host root, not under the API
ASSET_BASE_URL = "https://api.regvault.org"

#: Identifies the caller, so the service can see what its traffic is
USER_AGENT = "kodi-plugin.game.manuals.regvault/0.5.0 (+https://kodi.tv)"

#: The documented burst allowance is 100 requests a minute. Staying under it
#: by a wide margin keeps a large library scan from looking like a scrape.
MIN_SECONDS_BETWEEN_REQUESTS = 1.0

DEFAULT_TIMEOUT = 30


class RateLimited(Exception):
    """The service asked us to stop. Not something to retry around."""


class Unavailable(Exception):
    """The service could not be reached, or answered with something unusable."""


class Client(object):
    def __init__(self, timeout=DEFAULT_TIMEOUT, pace=MIN_SECONDS_BETWEEN_REQUESTS):
        self._timeout = timeout
        self._pace = pace
        self._last_request = 0.0

    def _wait_turn(self):
        elapsed = time.time() - self._last_request
        if elapsed < self._pace:
            time.sleep(self._pace - elapsed)
        self._last_request = time.time()

    def _open(self, url):
        self._wait_turn()

        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        try:
            return urllib.request.urlopen(request, timeout=self._timeout)
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            if error.code == 429:
                raise RateLimited("the service is rate limiting this address")
            raise Unavailable("HTTP %d" % error.code)
        except (urllib.error.URLError, OSError) as error:
            raise Unavailable(str(error))

    def lookup(self, system, rom_hash):
        """The catalogue entry for a game, or None if it is not known.

        :param system: a REG-Vault system slug
        :param rom_hash: the MD5 of the ROM
        """
        url = "%s/game/%s/%s" % (BASE_URL, system, rom_hash)

        response = self._open(url)
        if response is None:
            return None

        try:
            with response:
                return json.loads(response.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError, OSError, http.client.HTTPException) as error:
            raise Unavailable("unreadable answer: %s" % error)

    def size_of(self, url):
        """How large the document at a URL is, in bytes, or 0 if it will not say.

        Worth one request because a manual can be anything from a few hundred
        kilobytes to a hundred megabytes, and that is most of what decides
        whether the player wants it fetched over their connection.

        There is no cheap way to ask. The service answers HEAD with JSON
        rather than headers, and ignores a Range request. So the download is
        started and abandoned as soon as the header has arrived: nothing past
        what was already in flight is transferred.
        """
        response = self._open(url)
        if response is None:
            return 0

        try:
            with response:
                return int(response.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            return 0
