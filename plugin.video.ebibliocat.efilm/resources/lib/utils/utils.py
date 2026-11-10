"""Kodi URL construction. Request handling lives in ebibliocat.HTTP."""

from urllib.parse import urlencode


def buildUrl(query, base_url):
    return base_url + "?" + urlencode(query)
