import json
import urllib.parse

import xbmcaddon
from resources.lib.rssaddon.http_client import http_request


class Fyyd:

    _FYYD_API = {
        "search": "https://api.fyyd.de/0.2/search/podcast?term=%s"
    }

    _addon = None

    def __init__(self, addon: xbmcaddon.Addon) -> None:

        self._addon = addon

    def search_podcasts(self, term: str) -> dict:

        response, cookies = http_request(self._addon,
                                         self._FYYD_API["search"] % urllib.parse.quote(term))

        return json.loads(response)
