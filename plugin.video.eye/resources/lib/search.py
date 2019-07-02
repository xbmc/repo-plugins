# -*- coding: utf-8 -*-

"""EYE searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup, SoupStrainer
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

EYE_URI = "https://www.eyefilm.nl/"
EYE_COLLECTIONS_URI = "{}en/collection/film-history/film/all/all" \
                      "?f[0]=field_cm_media_filter%3Awith%20film%20fragment".format(EYE_URI)
EYE_PERIOD_TEMPLATE = "{}en/collection/film-history/film/all/{{}}" \
                      "?f[0]=field_cm_media_filter%3Awith%20film%20fragment".format(EYE_URI)
EYE_SEARCH_TEMPLATE = "{}&searchterm={{}}&page={{}}".format(EYE_COLLECTIONS_URI)

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_TIMEOUT = 60

logger = logging.getLogger(__name__)
searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")


def text_to_int(text):
    # type: (str) -> int
    """Extracts first digits from a string in sequence, defaults to 0"""
    number = re.search(r'\d+', text).group()
    return int(number) if number else 0


def get_next(element, target):
    if target is None:
        return element
    return element.findNext(target) if element else ""


def get_info(token):
    # type: (str) -> dict
    soup = get_html(token)
    originaltitle = soup.find("div", "collection-movie-original-title")
    info = soup.find("div", {"id": "node-collection-movie-full-group-cm-information"}).extract()
    director = info.find("div", string="director")
    category = info.find("div", string="category")
    country = info.find("div", string="country")
    year = info.find("div", string="production year")
    plot = soup.find("div", "group-cm-summary")
    runtime = soup.find("div", string="runtime")
    img = soup.find("img", {"typeof": "foaf:Image"})
    return {
        "title": soup.find("h1").text,
        "art": ku.art(img["src"]) if img else ku.icon("eye.png"),
        "info": {
            "originaltitle": originaltitle.text if originaltitle else "",
            "plot": plot.findNext("p").text if plot else "",
            "country": country.findNext("div").text if country else "",
            "genre": category.findNext("div").text if category else "",
            "year": int(year.findNext("div").text) if year else "",
            "director": director.findNext("div").text if director else "",
            "duration": text_to_int(runtime.findNext("div").text) * 60 if runtime else 0,
            "mediatype": "video"
        },
        "soup": soup
    }


def get_stream_token(data):
    div = data.find("div", "media-youtube-video")
    src = div.find("iframe")["data-src"]
    return re.search(r"embed/(.*)\?", src).group(1)


def get_search_url(query=None, page=1):
    # type: (str, int) -> str
    query = "" if query is None else query
    return EYE_SEARCH_TEMPLATE.format(query, page)


def get_page_url(href):
    # type: (str) -> str
    """Gets a full URL to a EYE html page"""
    return href if href.startswith(EYE_URI) else "{}{}".format(EYE_URI, href.lstrip("/"))


def clear():
    # type: () -> None
    """Clears entire cache"""
    with Cache() as c:
        c.clear()


def get_html(uri):
    # type: (str) -> Union[BeautifulSoup, None]
    """Gets cached or live HTML from the url"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip"
    }
    with Cache() as c:
        cached = c.get(uri)
        if cached:
            headers.update(conditional_headers(cached))
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
        r = requests.get(uri, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            strainer = SoupStrainer("div", {"id": "main-container"})
            soup = BeautifulSoup(r.content, "html.parser", parse_only=strainer)
            c.set(uri, str(soup), r.headers)
            return soup
        if 304 == r.status_code:
            c.touch(uri, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        return None


def date_range(date):
    # type: (str) -> str
    """Creates year range from years in the format 'YYYY - YYYY' end inclusive"""
    start, end = date.split(" - ")
    return "+".join(str(x) for x in list(range(int(start), int(end) + 1)))
