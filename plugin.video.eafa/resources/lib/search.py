# -*- coding: utf-8 -*-

"""EAFA searcher and helpers"""
__author__ = "fraser"

import json

import requests
from bs4 import BeautifulSoup

from . import kodiutils as ku
from .cache import Cache, datetime_to_httpdate

EAFA_URI = "http://www.eafa.org.uk/"
EAFA_SEARCH_URI = EAFA_URI + "search.aspx"
EAFA_BROWSE_URI = EAFA_URI + "browse.aspx"
PLAYER_URI = "https://media.eafa.org.uk/media/"

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_TIMEOUT = 60

CACHE_URI = ku.translate_path("special://profile/addon_data/plugin.video.eafa/cache.sqlite")
SAVED_SEARCH = "app://saved-searches"


def query_encode(query):
    # type (str) -> str
    return query.replace(" ", "+")


def query_decode(query):
    # type (str) -> str
    return query.replace("+", " ")


def html_to_text(text):
    # type (str) -> str
    """Extracts plain text content from HTML"""
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
    """Appends the cache validation headers if present"""
    if cached["etag"] is not None:
        headers["If-None-Match"] = cached["etag"]
    if cached["last_modified"] is not None:
        headers["If-Modified-Since"] = datetime_to_httpdate(cached["last_modified"])


def remove_whitespace(text):
    # type (str) -> str
    """strips all white-space from a string"""
    if text is None:
        return ""
    return "".join(text.split())


def pluck(text, start, end, default=None):
    # type (str, str, str, Any) -> Any
    """Attempts to extract string between start and end from text"""
    if default is None:
        default = ""
    idx = text.find(start) + len(start)
    try:
        return text[idx:text.find(end, idx)]
    except IndexError:
        return default


def get_search_params(query, page=1):
    # type: (str, int, int) -> str
    """Builds the query parameters fro an EAFA search argument"""
    return "page={}&vonly=1&psize={}&text={}".format(page, SEARCH_MAX_RESULTS, query)


def get_page_url(href):
    # type: (str) -> str
    """Gets a full URL to a EAFA html page"""
    return "{}{}".format(EAFA_URI, href.lstrip("/"))


def save(searches):
    # type: (list) -> None
    """Saves a list of search strings"""
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
    """Clears all cached data"""
    with Cache(CACHE_URI) as c:
        c.clear()


def post_html(url, data):
    # type: (str) -> BeautifulSoup
    """Gets cached or live HTML from the url with POST data"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip",
        "User-agent": "Mozilla/1.0 (X 0; rv:0.1) Gecko"
    }
    with Cache(CACHE_URI) as c:
        cached = c.get(url)
        if cached:
            add_cache_headers(headers, cached)
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
        r = requests.post(url, headers=headers, data=data, timeout=SEARCH_TIMEOUT)
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
            # pre-cache clean-up (NB: need scripts)
            for x in soup(["style"]):
                x.extract()
            c.set(url, str(soup), r.headers)
            return soup
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
