# -*- coding: utf-8 -*-

"""Searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

NTSV_URI = "https://www.ngataonga.org.nz/"
NTSV_LANDING_URI = "{}search-landing".format(NTSV_URI)
NTSV_DEFAULT_IMAGE_URI = "{}assets/video_offline.jpg".format(NTSV_URI)
NTSV_SEARCH_TEMPLATE = "{}collections/search?i[has_media]=true&i[media_type]=Moving%20image&" \
                       "{{}}{{}}{{}}{{}}{{}}".format(NTSV_URI)
NTSV_PERIODS = [
    "1800 - 1899",
    "1900 - 1909",
    "1910 - 1919",
    "1920 - 1929",
    "1930 - 1939",
    "1940 - 1949",
    "1950 - 1959",
    "1960 - 1969",
    "1970 - 1979",
    "1980 - 1989",
    "1990 - 1999",
    "2000 - 2009",
    "2010 - 2019"
]

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
RECENT_SAVED = ku.get_setting_as_bool("recent_saved")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def get_info(soup):
    # type: (BeautifulSoup) -> dict
    """Gets the video information for the given result data"""
    duration = soup.find("span", string="Duration")
    genre = soup.find("span", string="Genre")
    year = soup.find("span", string="Year")
    return {
        "video": get_m3u8_url(soup.find_all("script")[-1].text),
        "title": soup.find("meta", {"property": "og:title"}).get("content").title(),
        "image": soup.find("meta", {"property": "og:image"}).get("content"),
        "info": {
            "mediatype": "video",
            "duration": time_to_seconds(duration.find_next("strong").text) if duration else "",
            "plot": soup.find("meta", {"property": "og:description"}).get("content"),
            "genre": genre.find_next("strong").text.strip().title() if genre else "",
            "year": int(year.find_next("strong").text) if year else 0
        }
    }


def time_to_seconds(time):
    # type: (str) -> int
    """
    Attempts convert a given time string to the number of seconds
    where the format is SS, MM:SS or HH:MM:SS
    """
    return sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(time.split(":"))))


def text_to_int(text):
    # type (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def get_m3u8_url(text):
    # type: (str) -> Optional[str]
    """Attempts to get the first m3u8 URL from the given text"""
    m3u8 = re.search(r"http.*m3u8[^\"]*", text)
    return m3u8.group() if m3u8 else None


def get_image_url(text):
    # type: (str) -> str
    """Attempts to extract the image url from give text, default NTSV_DEFAULT_IMAGE_URI"""
    image = re.search(r"url\((.*)\)", text)
    return image.group(1) if image else NTSV_DEFAULT_IMAGE_URI


def get_search_url(**kwargs):
    # type: (**str) -> str
    """Constructs a search URL based on the query and page"""
    query = "&text={}".format(kwargs.get("query")) if kwargs.get("query") else ""
    genre = "&i[genre]={}".format(kwargs.get("genre")) if kwargs.get("genre") else ""
    year = "&i[year]=[{}]".format(kwargs.get("year")) if kwargs.get("year") else ""
    place = "&i[place_of_production]={}".format(kwargs.get("place")) if kwargs.get("place") else ""
    page = "&page={}".format(kwargs.get("page")) if kwargs.get("page") else ""
    return NTSV_SEARCH_TEMPLATE.format(query, genre, year, place, page)


def get_url(href):
    # type: (str) -> str
    """Gets a full URL to a resource"""
    return href if href.startswith("http") else "{}{}".format(NTSV_URI, href.lstrip("/"))


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
