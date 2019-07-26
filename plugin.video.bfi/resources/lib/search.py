# -*- coding: utf-8 -*-
"""BFI  searcher and helpers"""
__author__ = "fraser"

import json

import requests
from bs4 import BeautifulSoup

from . import kodiutils as ku
from cache import Cache, Store, conditional_headers

BFI_URI = "https://player.bfi.org.uk/"
THE_CUT_URI = "{}the-cut".format(BFI_URI)
SEARCH_URI = "https://search-es.player.bfi.org.uk/prod-films/_search"
PLAYER_URI = "https://player.ooyala.com/hls/player/all/"

STREAM_BANDWIDTH = ku.get_setting("stream_bandwidth")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_DEFAULT_OPERATOR = ku.get_setting("search_default_operator")
SEARCH_LENIENT = ku.get_setting_as_bool("search_lenient")
SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
RECENT_SAVED = ku.get_setting_as_bool("recent_saved")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")


def query_encode(query):
    # type: (str) -> str
    """Replaces " " for "+" in query"""
    return query.replace(" ", "+")


def query_decode(query):
    # type: (str) -> str
    """Replaces "+" for " " in query"""
    return query.replace("+", " ")


def html_to_text(text):
    # type: (str) -> str
    soup = BeautifulSoup(text, "html.parser")
    return '\n'.join(soup.stripped_strings)


def duration_to_seconds(text):
    # type: (str) -> int
    """Attempts to covert string of digits representing minutes to seconds"""
    try:
        seconds = int("".join(x for x in text if x.isdigit())) * 60
        return seconds if seconds else 60
    except ValueError:
        return 0


def parse_meta_info(meta, info):
    # type: (list, dict) -> None
    """Attempts to append year, duration and genre items to given info"""
    info["mediatype"] = "video"
    for item in meta:
        if item.text.isdigit():
            info["year"] = item.text
        elif "mins" in item.text:
            info["duration"] = duration_to_seconds(item.text)
        else:
            info["genre"].append(item.text)


def get_search_url(query, offset):
    # type: (str, int) -> str
    return "{}?q=pillar:free+{}&size={}&from={}&lenient={}&default_operator={}".format(
        SEARCH_URI,
        query_encode(query),
        SEARCH_MAX_RESULTS,
        SEARCH_MAX_RESULTS * offset,
        "true" if SEARCH_LENIENT else "false",
        SEARCH_DEFAULT_OPERATOR)


def get_m3u8_url(video_id):
    # type: (str) -> str
    """Gets a full URL to a m3u8 playlist file"""
    return "{}{}.m3u8?targetBitrate={}&ssl=true".format(PLAYER_URI, video_id, STREAM_BANDWIDTH)


def get_page_url(href):
    # type: (str) -> str
    """Gets a full URL to a BFI html page"""
    return href if href.startswith("http") else "{}{}".format(BFI_URI, href.lstrip("/"))


def cache_clear():
    # type: () -> None
    with Cache() as c:
        c.clear()


def get_html(url):
    # type: (str) -> BeautifulSoup
    """Gets cached or live HTML from the url"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip"
    }
    with Cache() as c:
        cached = c.get(url)
        if cached:
            headers.update(conditional_headers(cached))
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            # pre-cache clean-up
            for x in soup(["script", "style"]):
                x.extract()
            c.set(url, r.content, r.headers)
            return soup
        elif 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")


def get_json(url):
    # type: (str) -> dict
    """Gets cached or live JSON from the url"""
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip"
    }
    with Cache() as c:
        cached = c.get(url)
        if cached:
            headers.update(conditional_headers(cached))
            if cached["fresh"]:
                return json.loads(cached["blob"])
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.json(), r.headers)
            return r.json()
        elif 304 == r.status_code:
            c.touch(url, r.headers)
            return json.loads(cached["blob"])