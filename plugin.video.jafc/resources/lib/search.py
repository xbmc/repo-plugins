# -*- coding: utf-8 -*-

"""JAFC searcher and helpers"""
__author__ = "fraser"

import json
import logging

import requests
import xbmcaddon
from bs4 import BeautifulSoup

from . import kodiutils as ku
from .cache import Cache, datetime_to_httpdate

logger = logging.getLogger(__name__)

JAFC_URI = "https://animation.filmarchives.jp/"
JAFC_SEARCH_URI = "{}en/works/".format(JAFC_URI)
JAFC_INFO_URI = "{}en/works/view/".format(JAFC_URI)

JAFC_STREAM_URI = "https://h10.cs.nii.ac.jp/stream/nfc/"
JAFC_MPD_TEMPLATE = "{}{{}}_{{}}/dash/auto/master.mpd".format(JAFC_STREAM_URI)

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
ENGLISH_SUBTITLES = ku.get_setting_as_bool("english_subtitles")
SEARCH_TIMEOUT = 60

SETTINGS_LOCATION = xbmcaddon.Addon().getAddonInfo("profile")
APP_SAVED_SEARCHES = "app://saved-searches"


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


def get_table_data(soup, text, default=None):
    # type (BeautifulSoup.tag, str) -> str
    """Attempts to retrieve text data from a table based on the header value"""
    if default is None:
        default = ""
    if soup is None:
        return default
    if text is None:
        return default
    head = soup.find("th", text=text)
    if head is None:
        return default
    data = head.findNext("td").text
    return default if data is None or not data else data


def pluck(text, start, end, default=None):
    # type (str, str, str, Any) -> Any
    """Attempts to extract string between start and end from text"""
    if default is None:
        default = ""
    index = text.find(start) + len(start)
    try:
        return text[index:text.find(end, index)]
    except IndexError:
        return default


def get_search_url(query, page=1):
    # type: (str, int) -> str
    """Gets a full URL to a JAFC search result page"""
    return "{}?orderby=default&sound=all&num={}&page={}&keyword={}".format(
        JAFC_SEARCH_URI, SEARCH_MAX_RESULTS, page, query)


def get_mpd_url(token):
    """Gets a full URL to a playable object"""
    english = JAFC_MPD_TEMPLATE.format(token, "en")
    japanese = JAFC_MPD_TEMPLATE.format(token, "jp")
    if not ENGLISH_SUBTITLES:
        return japanese
    with Cache() as c:
        cached = c.get(english)
        if cached and cached["immutable"]:
            return cached["blob"]
        r = requests.head(english, timeout=SEARCH_TIMEOUT)
        if r.status_code == 200:
            c.set(english, english)
            return english
        else:
            c.set(english, japanese)
            return japanese


def get_url(href):
    # type: (str) -> str
    """Create a full URL to a JAFC resource"""
    return "{}{}".format(JAFC_URI, href.lstrip("/"))


def save(searches):
    # type: (list) -> None
    """Saves a list of search strings"""
    with Cache() as c:
        c.set(APP_SAVED_SEARCHES, json.dumps(searches, ensure_ascii=False))


def retrieve():
    # type: () -> list
    """Gets list of saved search strings"""
    with Cache() as c:
        data = c.get(APP_SAVED_SEARCHES)
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
    with Cache() as c:
        c.clear()


def recent_clear():
    # type: () -> None
    with Cache() as c:
        data = c.domain(JAFC_STREAM_URI, 999)  # larger than total possible film uris
        for item in data:
            c.delete(item["uri"])


def get_recent():
    # type: () -> list
    with Cache() as c:
        data = c.domain(JAFC_STREAM_URI)
        return data if data is not None else []


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
            add_cache_headers(headers, cached)
            if cached["fresh"] or cached["immutable"]:
                return BeautifulSoup(cached["blob"], "html.parser")
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            # pre-cache clean-up
            for x in soup(["script", "style"]):
                x.extract()
            # immutable info
            headers = None if url.startswith(JAFC_INFO_URI) else r.headers
            c.set(url, str(soup), headers)
            return soup
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")


def get_image(token):
    # type: (str) -> str
    data = get_html("{}{}".format(JAFC_INFO_URI, text_to_int(token)))  # cached
    return data.find("img", "thumbnail")["src"]


def get_info(token):
    # type: (str) -> object
    data = get_html("{}{}".format(JAFC_INFO_URI, text_to_int(token)))  # cached
    return {
        "plot": get_table_data(data, "Plot", get_table_data(data, "Description")),  # fallback to description
        "title": get_table_data(data, "English Title"),
        "originaltitle": get_table_data(data, "Japanese kana Rendering"),
        "year": text_to_int(get_table_data(data, "Production Date")),
        "director": get_table_data(data, "Credits: Director"),
        "duration": text_to_int(get_table_data(data, "Duration (minutes)")) * 60
    }
