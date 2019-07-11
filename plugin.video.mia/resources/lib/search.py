# -*- coding: utf-8 -*-

"""BP searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

MIA_URI = "https://movingimage.nls.uk/"
MIA_INFO_URI = "{}film/".format(MIA_URI)
MIA_SEARCH_TEMPLATE = "{}search?search_term={{}}&colour={{}}&sound={{}}&fiction={{}}&videoAccess=r".format(MIA_URI)

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_COLOUR = ku.get_setting("search_colour")
SEARCH_SOUND = ku.get_setting("search_sound")
SEARCH_FICTION = ku.get_setting("search_fiction")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def get_info(href):
    # type: (str) -> dict
    """Attempts to extract footage data from a video page"""
    soup = get_html(href)
    catalogue = soup.find("div", {"id": "catalogueInfo"})
    if not catalogue:
        logger.debug("No catalogue data: {}".format(href))
        return
    info = catalogue.extract()
    title = info.find("span", string="Title:")
    date = info.find("span", string="Date:")
    description = info.find("span", string="Description:")
    director = info.find("span", string="Director:")
    time = info.find("span", string="Running time:")
    return {
        "title": title.findNext("span").text.title() if title else "",
        "art": ku.art(get_image_url(str(soup))),
        "info": {
            "year": date.findNext("span").text if date else "",
            "plot": description.findNext("span").text if description else "",
            "duration": time_to_seconds(time.text) if time else 0,
            "director": director.findNext("span").text if director else ""
        },
        "m3u8": get_m3u8_url(str(soup))
    }


def time_to_seconds(text):
    # type: (str) -> int
    """Converts a time in the format mm.ss to seconds"""
    duration = re.search(r"[\d.]+", text)
    return int(duration.group().split('.')[0]) if duration else 0


def get_url(href):
    # type: (str) -> str
    """Gets a full URL to a British Path Pathé resource"""
    return "{}{}".format(MIA_URI, href.lstrip("/"))


def get_m3u8_url(text):
    # type: (str) -> Optional[str]
    """Attempts to get the first m3u8 URL from the given string"""
    m3u8 = re.search(r"https[^\"]*\.m3u8", text)
    return m3u8.group() if m3u8 else None


def get_image_url(text):
    # type: (str) -> Optional[str]
    """Attempts to get the fist jpg URL from the given string"""
    jpg = re.search(r"https[^\"]*\.11\.jpg", text)
    return jpg.group() if jpg else None


def get_search_url(query=None):
    # type: (str) -> str
    """Constructs a URL based on the query and current search settings"""
    query = "" if query is None else query
    colour = "" if SEARCH_COLOUR == "all" else SEARCH_COLOUR
    sound = "" if SEARCH_SOUND == "all" else SEARCH_SOUND
    fiction = "" if SEARCH_FICTION == "all" else SEARCH_FICTION
    return MIA_SEARCH_TEMPLATE.format(query, colour, sound, fiction)


def update_offset(url, offset):
    # type: (str, int) -> str
    """Updates or appends the 'from_row' offset to a URI"""
    offset = "" if offset is None else (int(offset) * 50) - 49
    regex = r"from_row=(\d+)"
    if re.search(regex, url):
        return re.sub(r"from_row=(\d+)", "from_row={}".format(offset), url)
    else:
        return "{}&from_row={}".format(url, offset)


def cache_clear():
    # type: () -> None
    """Clear the cache of all data"""
    with Cache() as c:
        c.clear()


def get_html(url):
    # type: (str) -> Optional[BeautifulSoup]
    """Gets cached or live HTML from the url"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip"
    }
    with Cache() as c:
        cached = c.get(url)
        is_info = url.startswith(MIA_INFO_URI)
        if cached:
            # Always return cached info pages...
            if cached["fresh"] or is_info:
                return BeautifulSoup(cached["blob"], "html.parser")
            headers.update(conditional_headers(cached))
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            # Always cache info pages without any query string
            headers = None if is_info else r.headers
            url = url.split("?")[0] if is_info else url
            soup = BeautifulSoup(r.content, "html.parser")
            c.set(url, r.content, headers)
            return soup
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        logger.debug("get_html error: {} {}".format(r.status_code, url))
        return None
