# -*- coding: utf-8 -*-

"""EAFA searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodilogging
from . import kodiutils as ku

EAFA_URI = "http://www.eafa.org.uk/"
EAFA_SEARCH_URI = "{}search.aspx".format(EAFA_URI)
EAFA_BROWSE_URI = "{}browse.aspx".format(EAFA_URI)
EAFA_PLAYER_URI = "https://media.eafa.org.uk/media/"
EAFA_LOW_RES_THUMB_TEMPLATE = "{}uploads/images/{{}}.jpg".format(EAFA_URI)

VIDEO_DEFINITION = ku.get_setting("video_definition")
SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
kodilogging.config()
logger = logging.getLogger(__name__)


def query_encode(query):
    # type: (str) -> str
    """Replaces ' ' for  '+'"""
    return query.replace(" ", "+")


def query_decode(query):
    # type: (str) -> str
    """Replaces '+' for  ' '"""
    return query.replace("+", " ")


def text_to_int(text):
    # type: (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def remove_whitespace(text):
    # type: (str) -> str
    """strips all white-space from a string"""
    if text is None:
        return ""
    return "".join(text.split())


def time_to_seconds(time):
    # type: (str) -> int
    """
    Attempts convert a given time string to the number of seconds
    where the format is SS, MM:SS or HH:MM:SS
    """
    return sum(x * int(t) if t.isdigit() else 0 for x, t in zip([1, 60, 3600], reversed(time.strip().split(":"))))


def get_callback_id(text):
    # type: (str) -> str
    """Attempts to extract the callback identifier from the given text"""
    idx = re.search(r"__doPostBack\('(.*)',", text)
    return idx.group(1) if idx else ""


def get_mp4_url(text):
    # type: (str) -> Optional[str]
    """
    Attempts to extract mp4 url from the given text, uses VIDEO_DEFINITION as preference. i.e.
    VIDEO_DEFINITION is High will try High, then fallback to Low if not found
    VIDEO_DEFINITION is Low will try Low, then fallback to High if not found
    """
    mp4 = re.search(r"(http.*{}\.mp4)".format(VIDEO_DEFINITION), text)
    if not mp4:
        logger.debug("get_mp4_url no  mp4: {}".format(VIDEO_DEFINITION))
        swap = "Low" if VIDEO_DEFINITION == "High" else "High"
        mp4 = re.search(r"(http.*{}\.mp4)".format(swap), text)
        if not mp4:
            logger.debug("get_mp4_url no  mp4: {}".format(swap))
            return
    return mp4.group(1)


def get_catalogue_url(number):
    # type: (int) -> str
    """Gets the full catalogue url for a given catalogue number"""
    return "{}catalogue/{}".format(EAFA_URI, number)


def get_year(text):
    # type: (str) -> int
    """Attempts to extract the year from text, default 0"""
    year = re.search(r"\d{4}", text)
    return int(year.group()) if year else 0


def get_genres(soup):
    # type: (BeautifulSoup) -> list
    """Attempts to get a list of genres from the soup"""
    genre = soup.find("h4", string="Genre:")
    if not genre:
        return []
    genres = genre.find_next("p").find_all("a")
    if len(genres):
        return [genre.text for genre in genres]
    return []


def get_info(soup):
    # type: (BeautifulSoup) -> Optional[dict]
    """Get the video information from a catalogue page.
    Returns None if the info can't be parsed"""
    title_right = soup.find("div", "title_right")
    if not title_right:
        logger.debug("get_info error no catalogue number")
    container = soup.find("div", {"id": "video-container"})
    if not container:
        logger.debug("get_info error: no container")
        return
    script = container.find_next_sibling("script")
    if not script:
        logger.debug("get_info error: no script")
        return
    return {
        "title": soup.find("h2").text.strip(),
        "image": get_image_url(script.text, text_to_int(title_right.text)),
        "video": get_mp4_url(script.text),
        "info": {
            "mediatype": "video",
            "plot": soup.find("p", "space").text,
            "duration": time_to_seconds(soup.find("span", "film_icon").text),
            "year": get_year(soup.find("h3").text),
            "genre": get_genres(soup)
        }
    }


def get_image_url(text, catalogue_number):
    # type: (str, int) -> Optional[str]
    """
    Attempts to extract the image url from the given text.
    The url is tested and cached if working (quite a few 404).
    If not 200 and a catalogue_number number is supplied, a low-res thumbnail is used and cached as the response
    """
    image = re.search(r"image: \"(http.*)\"", text)
    url = image.group(1) if image else None
    thumb = EAFA_LOW_RES_THUMB_TEMPLATE.format(catalogue_number)
    if not url and catalogue_number:
        return thumb
    with Cache() as c:
        cached = c.get(url)
        if cached and (cached["fresh"] or cached["immutable"]):
            return cached["blob"]
        r = requests.head(url)
        if 200 == r.status_code:
            c.set(url, url, r.headers)
            return url
        c.set(url, thumb, None)
        return thumb


def get_url(href):
    # type: (str) -> str
    """Gets a full url to an archive resource"""
    return href if href.startswith("http") else "{}{}".format(EAFA_URI, href.lstrip("/"))


def cache_clear():
    # type: () -> None
    """Clears all cached data"""
    with Cache() as c:
        c.clear()


def get_form_data(data):
    # type: (BeautifulSoup) -> Optional[dict]
    """Attempts to extract the form state and validation data"""
    validation = data.find("input", {"id": "__EVENTVALIDATION"})
    if not validation:
        logger.debug("get_form_data error no __EVENTVALIDATION")
        return
    return {
        "state": data.find("input", {"id": "__VIEWSTATE"}).get("value"),
        "action": data.find("form", {"id": "aspnetForm"}).get("action"),
        "validation": validation.get("value")
    }


def do_search(form, page, query):
    # type: (dict, int, str) -> BeautifulSoup
    """Perform a search on the archive"""
    return post_html(EAFA_SEARCH_URI, {
        "__EVENTTARGET": "ctl00$ContentPlaceHolder1$ucSearch$ToolkitScriptManager1",
        "__EVENTARGUMENT": "vonly=1&page={}&psize={}&text={}".format(page, SEARCH_MAX_RESULTS, query),
        "__VIEWSTATE": form.get("state")
    })


def post_html(url, data):
    # type: (str, dict) -> Optional[BeautifulSoup]
    """Gets cached or live HTML from the url with POST data"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip",
        "User-agent": "Mozilla/1.0 (X 0; rv:0.1) Gecko"
    }
    with Cache() as c:
        cached = c.get(url)
        if cached:
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
            headers.update(conditional_headers(cached))
        r = requests.post(url, headers=headers, data=data, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.content, r.headers)
            return BeautifulSoup(r.content, "html.parser")
        elif 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
    logger.debug("post_html error{} {}".format(r.status_code, url))


def get_html(url):
    # type: (str) -> Optional[BeautifulSoup]
    """Gets cached or live HTML from the url"""
    headers = {
        "Accept": "text/html",
        "Accept-encoding": "gzip"
    }
    with Cache() as c:
        cached = c.get(url)
        if cached:
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
            headers.update(conditional_headers(cached))
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            c.set(url, r.content, r.headers)
            return BeautifulSoup(r.content, "html.parser")
        elif 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
    logger.debug("get_html error{} {}".format(r.status_code, url))
