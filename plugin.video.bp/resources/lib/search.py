# -*- coding: utf-8 -*-

"""BP searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

BP_ARCHIVE = "Reuters"
BP_URI = "https://www.britishpathe.com/"
BP_COLLECTIONS_URI = "{}pages/collections/".format(BP_URI)
BP_ARCHIVE_URI = "{}pages/in-the-news/".format(BP_URI)
BP_SEARCH_URI = "{}search/query/".format(BP_URI)
BP_INFO_URI = "{}video/".format(BP_URI)
BP_SEARCH_TEMPLATE = "{}{{}}/start/{{}}/end/{{}}/archive/{{}}/colour/{{}}/limit/{{}}/page/{{}}".format(
    BP_SEARCH_URI)

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_ARCHIVE = ku.get_setting("search_archive")
SEARCH_COLOUR = ku.get_setting("search_colour")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def text_to_int(text):
    # type: (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def extract_year(text):
    # type: (str) -> int
    """Attempts to extract the first four digits from a string, defaults to 0"""
    data = re.search(r"\d{4}", text)
    return int(data.group()) if data else 0


def get_info(href):
    # type: (str) -> dict
    """Attempts to extract footage data from a video page"""
    soup = get_html(href)
    # head data
    head = soup.find("head").extract()
    title = head.find("meta", {"property": "og:title"})
    outline = head.find("meta", {"name": "description"})
    img = head.find("meta", {"property": "og:image"})
    # details data
    details = soup.find("ul", "details").extract()
    plot = details.find("h3", string="Description")
    group = details.find("dt", string="Group:")
    issue_date = details.find("dt", string="Issue Date:")
    duration = details.find("dt", string="Duration:")
    # urn = soup.find("dt", string="Media URN:").findNext("dd").text
    return {
        "title": title["content"] if title else "",
        "art": ku.art(img["content"] if img else ""),
        "info": {
            "plot": plot.findNext("div", "entry-content").text.strip().replace("\n", " ") if plot else "",
            "plotoutline": outline["content"] if outline else "",
            "genre": group.findNext("dd").text.strip() if group else "",
            "year": extract_year(issue_date.findNext("dd").text) if issue_date else 0,
            "duration": time_to_seconds(duration.findNext("dd").text) if duration else 0
        },
        "m3u8": get_m3u8_url(str(soup))
    }


def get_uri(href):
    # type: (str) -> str
    """Gets a full URI to a British Path Pathé resource"""
    return "{}{}".format(BP_URI, href.lstrip("/"))


def get_m3u8_url(text):
    # type: (str) -> Optional[str]
    """Attempts to get the first m3u8 url from the given string"""
    m3u8 = re.search(r"https[^\"]*\.m3u8", text)
    return m3u8.group() if m3u8 else None


def time_to_seconds(time):
    # type: (str) -> int
    """Attempts convert a given time string to the number of seconds, where the format is HH:MM:SS:MS"""
    if not time:
        return 0
    return sum(x * int(t) for x, t in zip([3600, 60, 1, 0], time.split(":")))


def get_search_url(query=None, start=None, end=None, page=None):
    # type: (str, int, int, int) -> str
    """Constructs a search URL based on the given parameters"""
    query = "+" if query is None else query
    start = "+" if start is None else start
    end = "+" if end is None else end
    page = 1 if page is None else page
    archive = "+" if SEARCH_ARCHIVE == "All" else SEARCH_ARCHIVE
    colour = "+" if SEARCH_COLOUR == "All" else SEARCH_COLOUR
    return BP_SEARCH_TEMPLATE.format(query, start, end, archive, colour, SEARCH_MAX_RESULTS, page)


def cache_clear():
    # type: () -> None
    """Clear the cache of all data"""
    with Cache() as c:
        c.clear()


def get_html(uri):
    # type: (str) -> Optional[BeautifulSoup]
    """Gets cached or live HTML from the url"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip"
    }
    is_info = uri.startswith(BP_INFO_URI)
    if is_info:
        uri = uri.split("/query")[0]
    with Cache() as c:
        cached = c.get(uri)
        if cached:
            # Always return cached info pages...
            if cached["fresh"] or is_info:
                return BeautifulSoup(cached["blob"], "html.parser")
            headers.update(conditional_headers(cached))
        r = requests.get(uri, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            # Always cache info pages...
            headers = None if is_info else r.headers
            c.set(uri, r.content, headers)
            return soup
        if 304 == r.status_code:
            c.touch(uri, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        logger.debug("get_html error: {} {}".format(r.status_code, uri))
        return None


def get_collection_data():
    # type: () -> dict
    """Rationalises the collection menu data"""
    soup = get_html(BP_COLLECTIONS_URI)
    images = soup.select("a > img")
    data = dict()
    for image in images:
        action = image.parent.findNext("a")
        heading = action.findPrevious("h2")
        if heading.text == u"British Pathé Programming":
            # skip programmes as they have a different structure to all other collections
            continue
        item = {action.text: [action["href"], image["src"]]}
        if heading.text in data:
            data[heading.text].update(item)
        else:
            data[heading.text] = item
    return data
