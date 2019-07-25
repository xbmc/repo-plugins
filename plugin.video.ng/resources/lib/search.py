# -*- coding: utf-8 -*-

"""Searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

NG_URI = "https://video.nationalgeographic.com/"
NG_SHOWS_TEMPLATE = "{}video/ngs?gs=all&gp={{}}".format(NG_URI)
NG_SEARCH_TEMPLATE = "{}search?q={{}}&gp={{}}".format(NG_URI)
NG_VIDEO_TEMPLATE = "https://link.theplatform.com/s/ngs/media/guid/{}/{}?MBR=true&format=smil&width=1080&height=1920"

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
RECENT_SAVED = ku.get_setting_as_bool("recent_saved")
SEARCH_MAX_RESULTS = 75  # fixed by site
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def get_info(soup):
    # type: (BeautifulSoup) -> dict
    """Gets the video information for the given result data"""
    return {
        "video": get_mp4_url(soup.find("div", {"id": "videoPlayer"})),
        "title": soup.find("meta", {"property": "og:title"}).get("content"),
        "image": soup.find("meta", {"property": "og:image"}).get("content"),
        "info": {
            "mediatype": "video",
            "duration": time_to_seconds(soup.find("div", "timestamp").text),
            "plot": soup.find("meta", {"property": "og:description"}).get("content"),
            "genre": [x.text for x in soup.find("ul", "categories").find_all("a")]
        }
    }


def get_playable_item_count(href):
    soup = get_html(get_url(href))
    if not soup:
        return 0
    items = soup.find_all("div", "media-module")
    return len(items) if items else 0


def time_to_seconds(text):
    # type: (str) -> int
    """Converts a time in the format mm:ss to seconds, defaults to 0"""
    if text == 0:
        return 0
    duration = re.search(r"[\d:]+", text)
    if duration:
        minutes, seconds = duration.group().split(':')
        return int(minutes) * 60 + int(seconds)
    return 0


def text_to_int(text):
    # type (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def get_mp4_url(player):
    # type: (bs4.element.Tag) -> Optional[str]
    """Attempts to get a valid mp4 url from the given video player element"""
    if not player:
        return
    player = player.extract()
    data = get_html(NG_VIDEO_TEMPLATE.format(player.get("data-account"), player.get("data-guid")))
    return data.find("video").get("src")


def get_gp(url):
    # type: (str) -> int
    """Attempts to extract the 'gp' parameter value from a given URL, default 0"""
    gp = re.search(r"gp=(\d+)", url)
    return int(gp.group(1)) if gp else 0


def get_show_url(page=0):
    return NG_SHOWS_TEMPLATE.format(page)


def get_search_url(query=None, page=0):
    # type: (str, int) -> str
    """Constructs a search URL based on the query and page"""
    return NG_SEARCH_TEMPLATE.format(query, page)


def get_url(href):
    # type: (str) -> str
    """Gets a full URL to a resource"""
    return href if href.startswith("http") else "{}{}".format(NG_URI, href.lstrip("/"))


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
    with Cache() as c:
        cached = c.get(uri)
        if cached:
            # Always return cached info pages...
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
            headers.update(conditional_headers(cached))
        r = requests.get(uri, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            c.set(uri, r.content, r.headers)
            return soup
        elif 304 == r.status_code:
            c.touch(uri, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        logger.debug("get_html error: {} {}".format(r.status_code, uri))
