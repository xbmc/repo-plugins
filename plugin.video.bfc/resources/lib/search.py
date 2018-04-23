# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""BFI  searcher and helpers"""
__author__ = "fraser"

import json

import requests
from bs4 import BeautifulSoup

from . import kodiutils as ku
from .cache import Cache, datetime_to_httpdate

BCF_URI = "http://film.britishcouncil.org/"
BCF_SEARCH_URI = "http://film.britishcouncil.org/british-council-film-collection"
PLAYER_URI = "https://player.vimeo.com"

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_TIMEOUT = 60

CACHE_URI = ku.translate_path("special://profile/addon_data/plugin.video.bcf/cache.sqlite")
SAVED_SEARCH = "app://saved-searches"


def query_encode(query):
    # type (str) -> str
    return query.replace(" ", "+")


def query_decode(query):
    # type (str) -> str
    return query.replace("+", " ")


def html_to_text(text):
    # type (str) -> str
    soup = BeautifulSoup(text, "html.parser")
    return '\n'.join(soup.stripped_strings)


def text_to_int(text):
    # type (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def add_cache_headers(headers, cached):
    # type: (dict, dict) -> None
    if cached["etag"] is not None:
        headers["If-None-Match"] = cached["etag"]
    if cached["last_modified"] is not None:
        headers["If-Modified-Since"] = datetime_to_httpdate(cached["last_modified"])


def get_search_url(query="", year="Any", series="Any", genre=""):
    # type: (str, str, str, str) -> str
    return "{}?film_query={}&year={}&series={}&genre[]={}".format(
        BCF_SEARCH_URI,
        query,
        year,
        series,
        genre)


def get_page_url(href):
    # type: (str) -> str
    """Gets a full URL to a BCF html page"""
    return "{}{}".format(BCF_URI, href.lstrip("/"))


def save(searches):
    # type: (list) -> None
    with Cache(CACHE_URI) as c:
        c.set(SAVED_SEARCH, json.dumps(searches, ensure_ascii=False))


def retrieve():
    # type: () -> list
    """Gets list of saved search strings"""
    with Cache(CACHE_URI) as c:
        data = c.get(SAVED_SEARCH)
        return json.loads(data["blob"]) if data else []


def remove(query):
    # type: (str) -> bool
    """Removes a query from the saved search list"""
    if not query or not SEARCH_SAVED:
        return False
    searches = retrieve()
    if query in searches:
        searches.remove(query)
        save(searches)
        return True
    return False


def append(query):
    # type: (str) -> bool
    """
    Adds a query to the saved search list
    unless the query is equal to False or
    SEARCH_SAVED settings is False
    """
    if not query or not SEARCH_SAVED:
        return False
    searches = retrieve()
    if query not in searches:
        searches.append(query)
        save(searches)


def cache_clear():
    # type: () -> None
    with Cache(CACHE_URI) as c:
        c.clear()


def get_html(url):
    # type: (str) -> BeautifulSoup
    """Gets cached or live HTML from the url"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip"
    }
    with Cache(CACHE_URI) as c:
        cached = c.get(url)
        if cached:
            add_cache_headers(headers, cached)
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            # pre-cache clean-up
            for x in soup(["script", "style"]):
                x.extract()
            c.set(url, str(soup), r.headers)
            return soup
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
