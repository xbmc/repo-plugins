# -*- coding: utf-8 -*-
"""BFI  searcher and helpers"""
__author__ = "fraser"

import json

import requests
from bs4 import BeautifulSoup

from . import kodiutils as ku
from .cache import Cache, datetime_to_httpdate

BFI_URI = "https://player.bfi.org.uk/"
SEARCH_URI = "https://search-es.player.bfi.org.uk/prod-films/_search"
PLAYER_URI = "https://player.ooyala.com/hls/player/all/"
RECENT_URI = "https://player.bfi.org.uk/free/film/watch"

STREAM_BANDWIDTH = ku.get_setting_as_int("stream_bandwidth")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_DEFAULT_OPERATOR = ku.get_setting("search_default_operator")
SEARCH_LENIENT = ku.get_setting_as_bool("search_lenient")
SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_TIMEOUT = 60

CACHE_URI = ku.translate_path("special://profile/addon_data/plugin.video.bfi/cache.sqlite")
SAVED_SEARCH = "app://saved-searches"


def query_encode(query):
    # type (str) -> str
    return query.replace(" ", "+")


def query_decode(query):
    # type (str) -> str
    return query.replace("+", " ")


def html_to_text(text):
    # type (str) -> str
    soup = BeautifulSoup(text, "html.parser", from_encoding="utf-8")
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


def get_search_url(query, offset):
    # type: (str, int) -> str
    return "{}?q=pillar:free+{}&size={}&from={}&lenient={}&default_operator={}".format(
        SEARCH_URI,
        query_encode(query),
        SEARCH_MAX_RESULTS,
        SEARCH_MAX_RESULTS * offset,
        "true" if SEARCH_LENIENT else "false",
        SEARCH_DEFAULT_OPERATOR)


def get_video_url(video_id):
    # type: (str) -> str
    """Gets a full URL to a m3u8 playlist file"""
    return "{}{}.m3u8?targetBitrate={}&ssl=true".format(PLAYER_URI, video_id, STREAM_BANDWIDTH)


def get_page_url(href):
    # type: (str) -> str
    """Gets a full URL to a BFI html page"""
    return "{}{}".format(BFI_URI, href.lstrip("/"))


def save(searches):
    # type: (list) -> None
    with Cache(CACHE_URI) as c:
        c.set(SAVED_SEARCH, json.dumps(searches, ensure_ascii=False), None)


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
        return True
    return False


def get_recent():
    # type: () -> list
    with Cache(CACHE_URI) as c:
        data = c.domain(RECENT_URI)
        return data if data is not None else []


def cache_clear():
    # type: () -> None
    with Cache(CACHE_URI) as c:
        c.clear()


def recent_clear():
    # type: () -> None
    with Cache(CACHE_URI) as c:
        data = c.domain(RECENT_URI, 99999)
        for item in data:
            c.delete(item["uri"])


def get_m3u8(url):
    # type: (str) -> str
    """
    Gets the cached m3u8 URL from a live video URL
    NB: returns URL rather than playlist data
    """
    headers = {
        "Accept": "application/x-mpegURL",
        "Accept-encoding": "gzip"
    }
    with Cache(CACHE_URI) as c:
        cached = c.get(url)
        if cached:
            add_cache_headers(headers, cached)
            if cached["fresh"]:
                return url
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.content, r.headers)
            return url
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return url


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


def get_json(url):
    # type: (str) -> dict
    """Gets cached or live JSON from the url"""
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip"
    }
    with Cache(CACHE_URI) as c:
        cached = c.get(url)
        if cached:
            add_cache_headers(headers, cached)
            if cached["fresh"]:
                return json.loads(cached["blob"])
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.json(), r.headers)
            return r.json()
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return json.loads(cached["blob"])
