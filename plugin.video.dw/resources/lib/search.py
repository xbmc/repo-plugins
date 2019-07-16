# -*- coding: utf-8 -*-

"""BP searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from bs4 import BeautifulSoup
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

DW_URI = "https://www.dw.com/"
DW_MEDIA_URL = "{}en/media-center/".format(DW_URI)
DW_MEDIA_LIVE_URI = "{}live-tv/s-100825".format(DW_MEDIA_URL)
DW_MEDIA_ALL_URL = "{}all-media-content/s-100826".format(DW_MEDIA_URL)
DW_PROGRAMME_URI = "{}en/tv/tv-programs/s-9103".format(DW_URI)

DW_SEARCH_TEMPLATE = "{}mediafilter/research?" \
                     "lang={{}}&type=18&results=0&showteasers=t&first={{}}{{}}{{}}{{}}".format(DW_URI)
DW_VIDEO_TEMPLATE = "https://dwhlsondemand-vh.akamaihd.net/i/dwtv_video/flv/{},sor,avc,.mp4.csmil/master.m3u8"

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_LANGUAGE = ku.get_setting("search_language")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def get_info(href):
    # type: (str) -> dict
    """Gets the info for playable item; title, image, path, etc"""
    soup = get_html(href)
    item = soup.find("div", "mediaItem").extract()
    plot = soup.find("p", "intro")
    title = item.find("input", {"name": "media_title"}).get("value")
    video = soup.find("meta", {"property": "og:video"})
    file_name = item.find("input", {"name": "file_name"})
    duration = item.find("input", {"name": "file_duration"})
    preview_image = item.find("input", {"name": "preview_image"})
    path = None
    if video:
        path = video.get("content")
    elif file_name:
        flv = file_name.get("value")
        path = get_m3u8_url(flv)
        if not path:  # fallback to the low-res flv if no mp4 or mu38...
            path = flv
    return {
        "path": path,
        "image": get_url(preview_image.get("value")) if preview_image else "",
        "info": {
            "title": title,
            "plot": plot.text if plot else title,
            "duration": int(duration.get("value")) if duration else 0
        }
    }


def get_program_id(url):
    # type: (str) -> str
    """Attempts to extract a programme id from a given url"""
    search = re.search(r"programs=(\d+)", url)
    return search.group(1) if search else ""


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


def get_date_time(text):
    # type: (str) -> tuple
    """Attempts to parse date and time from text in the format 'dd.mm.yyyy | mm:ss'"""
    try:
        date, time = text.split("|")
    except ValueError:
        date, time = (text, 0)
    return date, time_to_seconds(time)


def get_url(href):
    # type: (str) -> str
    """Gets a full URL to a resource"""
    return href \
        if href.startswith("http") \
        else "{}{}".format(DW_URI, href.strip().lstrip("/"))


def get_m3u8_url(flv):
    # type: (str) -> Optional[str]
    """Attempts to generate a m3u8 URL from the given flv URL"""
    try:
        return DW_VIDEO_TEMPLATE.format(flv.split("flv/")[1].split("vp6")[0])
    except IndexError:
        return None


def get_search_url(query=None, tid=None, pid=None):
    """Gets a full URL for a search page"""
    language = "en" if tid or pid else SEARCH_LANGUAGE
    query = "" if query is None else "&filter={}".format(query)
    tid = "" if tid is None else "&themes={}".format(tid)
    pid = "" if pid is None else "&programs={}".format(pid)
    return DW_SEARCH_TEMPLATE.format(language, SEARCH_MAX_RESULTS, tid, pid, query)


def get_hidden(url):
    # type: (str) -> int
    """Attempts to extract the hide parameter value from a given URL"""
    hidden = re.search(r"hide=(\d+)", url)
    return int(hidden.group(1)) if hidden else 0


def update_hidden(url, hidden=0):
    # type: (str, int) -> str
    """Updates or appends the 'hide' parameter for a URL"""
    pattern = r"hide=(\d+)"
    return re.sub(pattern, "hide={}".format(hidden), url) \
        if re.search(pattern, url) \
        else "{}&hide={}".format(url, hidden)


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
        if cached:
            if cached["fresh"]:
                return BeautifulSoup(cached["blob"], "html.parser")
            headers.update(conditional_headers(cached))
        r = requests.get(url, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            c.set(url, r.content, r.headers)
            return soup
        if 304 == r.status_code:
            c.touch(url, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        logger.debug("get_html error: {} {}".format(r.status_code, url))
        return None
