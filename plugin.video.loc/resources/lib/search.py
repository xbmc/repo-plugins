# -*- coding: utf-8 -*-

"""BP searcher and helpers"""

__author__ = "fraser"

import logging
import re

import requests
from cache import Cache, Store, conditional_headers

from . import kodiutils as ku

LOC_URI = "https://www.loc.gov/"
LOS_MEDIA_TEMPLATE = "https://media.loc.gov/services/v1/media?id={}"
LOC_SEARCH_TEMPLATE = "{}film-and-videos/{{}}" \
                      "?fa=online-format:video&fo=json&q={{}}&dates={{}}&c={{}}&sp={{}}".format(LOC_URI)
LOC_STATIC_IMAGE = "/static/images/original-format/film-video.png"
LOC_DEFAULT_IMAGE_URI = "{}{}".format(LOC_URI, LOC_STATIC_IMAGE.lstrip("/"))

SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_MAX_RESULTS = ku.get_setting("search_max_results")
SEARCH_TIMEOUT = 60

searches = Store("app://saved-searches")
recents = Store("app://recently-viewed")
logger = logging.getLogger(__name__)


def extract_year(text):
    # type: (str) -> int
    """Attempts to extract the first four digits in sequence from a string, defaults to 0"""
    data = re.search(r"\d{4}", text)
    return int(data.group()) if data else 0


def get_art(data):
    # type: (dict) -> dict
    """Gets the art-work for the given result data"""
    image = data.get("resources", [{}])[0].get("image")
    if not image or image == LOC_STATIC_IMAGE:  # default
        return ku.art(LOC_DEFAULT_IMAGE_URI)
    if image.startswith("//"):  # no protocol
        return ku.art("http:{}".format(image))
    return ku.art(image)


def get_info(data):
    # type: (dict) -> dict
    """Gets the video information for the given result data"""
    item = data.get("item", {})
    plot = item.get("summary", data.get("description"))
    if plot and isinstance(plot, list):
        plot = plot[0]
    # TODO : some-kind of duration calculation...
    return {
        "title": item.get("title", "").title(),
        "plot": plot,
        "year": extract_year(item.get("date", "")),
        "genre": item.get("genre")
    }


def get_search_url(index=None, query=None, dates=None, page=0):
    # type: (str, str, str, int) -> str
    """Constructs a search URL based on the query and current search settings"""
    index = "" if index is None else index
    query = "" if query is None else query
    dates = "" if dates is None else dates
    return LOC_SEARCH_TEMPLATE.format(index, query, dates, SEARCH_MAX_RESULTS, page)


def get_mime_property(data, key, mime):
    # type: (list, str, str) -> str
    """Attempts to get key data from a mime-type object"""
    try:
        return [item.get(key) for item in data if item.get("mimetype") == mime][0]
    except (IndexError, KeyError):
        logger.debug("get_mime_property error: {} {}".format(key, mime))
        return ""


def get_video_url(data):
    # type: (dict) -> Optional[str]
    """Attempts to get a playable URL from given response data"""
    resource = data.get("resources", [{}])[0]
    url = resource.get("video_stream")  # try m3u8
    if not url:  # try mp4
        files = resource.get("files")[0]
        mp4 = get_mime_property(files, "url", "video/mp4")
        url = "https:{}".format(mp4) if mp4 and mp4.startswith("//") else mp4
        if not url:  # try x-video
            idx = get_mime_property(files, "mediaObjectId", "application/x-video")
            media = get_json(LOS_MEDIA_TEMPLATE.format(idx))
            derivative = media.get("mediaObject").get("derivatives")[0]
            url = "https://{}/{}".format(
                derivative.get("fqdn"),
                derivative.get("derivativeMediaUrl").replace("mp4:", ""))
    return url


def cache_clear():
    # type: () -> None
    """Clear the cache of all data"""
    with Cache() as c:
        c.clear()


def get_json(url):
    """Gets cached or live JSON from the url"""
    headers = {
        "Accept": "text/html",
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
