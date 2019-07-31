# -*- coding: utf-8 -*-

"""Searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

NFPF_URI = "https://www.filmpreservation.org/"
NFPF_SCREENING_ROOM_URI = "{}preserved-films/screening-room".format(NFPF_URI)
NFPF_MERCURY_URI = "{}preserved-films/lost-and-found-mercury-theater-films".format(NFPF_URI)
NFPF_VIDEOS_URI = "{}videos.js".format(NFPF_URI)

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
RECENT_SAVED = ku.get_setting_as_bool("recent_saved")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def get_info(soup):
    # type: (BeautifulSoup) -> dict
    """Gets the video information for the given result data"""
    title = soup.find("h3", "video").text
    return {
        "title": title,
        "video": soup.find("div", "film-player").get("data-file"),
        "image": soup.find("div", "film-player").get("data-image"),
        "info": {
            "mediatype": "video",
            "plot": soup.find("div", {"id": "film-notes"}).find_all("p")[1].text,
            "year": get_year(title)
        }
    }


def get_year(text):
    year = re.match(r"\((\d+)\)", text)
    return year.group(1) if year else 0


def text_to_soup(text):
    return BeautifulSoup(text, "html.parser")


def get_url(href):
    # type: (str) -> str
    """Gets a full URL to a resource"""
    return href if href.startswith("http") else "{}{}".format(NFPF_URI, href.lstrip("/"))


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
                return cached["blob"]
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.json(), r.headers)
            return r.json()
        elif 304 == r.status_code:
            c.touch(url, r.headers)
            return cached["blob"]
        logger.debug("get_json error: {} {}".format(r.status_code, url))
