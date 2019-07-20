# -*- coding: utf-8 -*-

"""Searcher and helpers"""

__author__ = "fraser"

import logging

import re
import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

PA_URI = "https://archive.org/"
PA_LIST_TEMPLATE = "{}details/prelinger?headless=1&output=json&morf={{}}".format(PA_URI)
PA_SECTION_TEMPLATE = "{}details/prelinger?scroll=1&headless=1&and[]={{}}:\"{{}}\"&page={{}}".format(PA_URI)
PA_SEARCH_TEMPLATE = "{}details/prelinger?headless=1&and[]={{}}&page={{}}".format(PA_URI)

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
    year = soup.find("dd", {"itemprop": "datePublished"})
    keywords = soup.find("dd", {"itemprop": "keywords"})
    return {
        "title": soup.find("span", {"itemprop": "name"}).text,
        "image": soup.find("meta", {"property": "og:image"}).get("content"),
        "video": soup.find("meta", {"property": "og:video"}).get("content"),
        "info": {
                "plot": soup.find("meta", {"property": "og:description"}).get("content"),
                "plotoutline": soup.find("meta", {"property": "og:title"}).get("content"),
                "year": int(year.text) if year else 0,
                "genre": [item.text for item in keywords.find_all("a")] if keywords else "",
                "duration": int(soup.find("meta", {"property": "video:duration"}).get("content"))
            }
    }


def text_to_int(text):
    # type (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def get_search_url(query=None, page=1):
    # type: (str, int) -> str
    """Constructs a search URL based on the query and page"""
    return PA_SEARCH_TEMPLATE.format(query, page)


def get_list_url(section):
    # type: (str) -> str
    """Constructs a section list URL based on the category"""
    return PA_LIST_TEMPLATE.format(section)


def get_section_url(category, section, page=1):
    """Constructs a section URL based on the category, section and page"""
    try:
        return PA_SECTION_TEMPLATE.format(category, section, page)
    except UnicodeEncodeError:
        return PA_SECTION_TEMPLATE.format(category, section.encode("utf-8"), page)


def get_url(href):
    # type: (str) -> str
    """Gets a full URL to a resource"""
    return href if href.startswith("http") else "{}{}".format(PA_URI, href.lstrip("/"))


def get_page_number(url):
    # type: (str) -> int
    """Attempts to extract the 'page' parameter value from a given URL, default 0"""
    page = re.search(r"page=(\d+)", url)
    return int(page.group(1)) if page else 0


def update_page_number(url, page=1):
    # type: (str, int) -> str
    """Updates or appends the 'page' parameter for a URL"""
    pattern = r"page=(\d+)"
    return re.sub(pattern, "page={}".format(page), url) \
        if re.search(pattern, url) \
        else "{}&page={}".format(url, page)


def cache_clear():
    # type: () -> None
    """Clear the cache of all data"""
    with Cache() as c:
        c.clear()


def get_json(url):
    # type: (str) -> Optional[dict]
    """Gets cached or live JSON from the url"""
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip"
    }
    with Cache() as c:
        cached = c.get(url)
        if cached:
            if cached["fresh"]:
                return cached["blob"]
            headers.update(conditional_headers(cached))
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.json(), r.headers)
            return r.json()
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return cached["blob"]
        logger.debug("get_json error: {} {}".format(r.status_code, url))
        return None


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
        if 304 == r.status_code:
            c.touch(uri, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        logger.debug("get_html error: {} {}".format(r.status_code, uri))
        return None
