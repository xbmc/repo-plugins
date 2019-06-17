# -*- coding: utf-8 -*-

"""IWM searcher and helpers"""

__author__ = "fraser"

import json
import logging
import re

import requests
from bs4 import BeautifulSoup

from . import kodiutils as ku
from .cache import Cache, datetime_to_httpdate

IWM_URI = "https://film.iwmcollections.org.uk/"
IWM_SEARCH_URI = "https://film.iwmcollections.org.uk/search/performsearch/"
IWM_DATA_URI = "https://film.iwmcollections.org.uk/recordgridview/getdata/"
IWM_INFO_URI = "https://film.iwmcollections.org.uk/record/"
IWM_SEARCH_PAYLOAD = {
    "resultsPerPage": 10,
    "keyword": "*",
    "type": "list",
    "collectionText": "collection",
    "sort": "Relevance",
    "page": 1,
    "filter": "",
    "spellCheck": "true",
    "customPage": []
}
SEARCH_SAVED = ku.get_setting_as_bool("search_saved")
SEARCH_MAX_RESULTS = ku.get_setting_as_int("search_max_results")
SEARCH_TIMEOUT = 60
SEARCH_APP_KEY = "app://saved-searches"

logger = logging.getLogger(__name__)


def text_to_int(text):
    # type: (str) -> int
    """Extracts each digit from a string in sequence, defaults to 0"""
    try:
        return int("".join(x for x in text if x.isdigit()))
    except ValueError:
        return 0


def clean_uri(uri):
    # type: (str) -> str
    """Removes redundant backslashes from a uri"""
    return re.sub(r"\\/", r"/", uri)


def get_image_url(text):
    # type: (str) -> str
    """Attempts to extract an image url from the given text"""
    img = re.search(r"https[^)]*", text)
    return clean_uri(img.group())


def get_preview(text):
    # type: (str) -> str
    """Attempts to extract an preview image url from the given text"""
    img = re.search(r"\"preview\":\"([^\"]*)", text)
    return clean_uri(img.group(1))


def get_info(token):
    # type: (str) -> dict
    soup = get_html(token)
    return {
        "title": clean_title(soup.find("span", string="Title:").findNext("span").text),
        "art": ku.art(get_preview(soup.text)),
        "info": {
            "plot": soup.find("span", string="Description:").findNext("span").text,
            "plotoutline": soup.find("span", string="Summary:").findNext("span").text,
            "country": soup.find("span", string="Production Country:").findNext("span").text,
            "year": int(soup.find("span", string="Production Date:").findNext("span").text.split("-")[0]),
            "director": soup.find("span", string="Production Details:").findNext("span").text
        },
        "soup": soup
    }


def get_m3u8_url(text):
    # type: (str) -> Union[str, None]
    """Attempts to get the first m3u8 url from the given string"""
    m3u8 = re.search(r"https[^\"]*\.m3u8", text)
    sig = re.search(r"(\?sig=[^\"]*)", text)
    if m3u8 and sig:
        return "{}{}".format(clean_uri(m3u8.group()), sig.group())
    return None


def get_recent():
    # type: () -> list
    with Cache() as c:
        data = c.domain(IWM_INFO_URI)
        return [{"uri": item["uri"], "soup": BeautifulSoup(item["blob"], "html.parser")} for item in
                data] if data is not None else []


def time_to_seconds(time):
    # type: (str) -> int
    """
    Attempts convert a given time string to the number of seconds
    where the format is SS, MM:SS or HH:MM:SS
    """
    return sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(time.split(":"))))


def clean_title(title):
    # type: (str) -> str
    return title.replace("[Main Title]", "").replace("[Allocated Title]", "")


def add_cache_headers(headers, cached):
    # type: (dict, dict) -> None
    if cached["etag"] is not None:
        headers["If-None-Match"] = cached["etag"]
    if cached["last_modified"] is not None:
        headers["If-Modified-Since"] = datetime_to_httpdate(cached["last_modified"])


def get_search_url(query="", page=1):
    # type: (str, int) -> str
    return IWM_SEARCH_URI.format(query, page)


def get_page_url(href):
    # type: (str) -> str
    """Gets a full URL to a IWM html page"""
    return href if href.startswith(IWM_URI) else "{}{}".format(IWM_URI, href.lstrip("/"))


def save(searches):
    # type: (list) -> None
    with Cache() as c:
        c.set(SEARCH_APP_KEY, json.dumps(searches, ensure_ascii=False))


def retrieve():
    # type: () -> list
    """Gets list of saved search strings"""
    with Cache() as c:
        data = c.get(SEARCH_APP_KEY)
        return json.loads(data["blob"]) if data else []


def remove(query):
    # type: (str) -> bool
    """Removes a query from the saved search list"""
    if not query or not SEARCH_SAVED:
        return False
    searches = retrieve()
    if query in searches:
        searches.remove(query)
        save(searches)
        return True
    return False


def append(query):
    # type: (str) -> bool
    """
    Adds a query to the saved search list
    unless the query is equal to False or
    SEARCH_SAVED settings is False
    """
    if not query or not SEARCH_SAVED:
        return False
    searches = retrieve()
    if query not in searches:
        searches.append(query)
        save(searches)


def cache_clear():
    # type: () -> None
    with Cache() as c:
        c.clear()


def recent_clear():
    # type: () -> None
    with Cache() as c:
        data = c.domain(IWM_INFO_URI, 999)  # larger than total possible film uris
        for item in data:
            c.delete(item["uri"])


def post_json(payload=None):
    # type: (dict) -> dict
    payload = IWM_SEARCH_PAYLOAD if payload is None else payload
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip",
        "origin": IWM_URI
    }
    r = requests.post(IWM_SEARCH_URI, headers=headers, json=payload)
    if 200 == r.status_code:
        return r.json()
    else:
        ku.notification(ku.localize(32007), "There are no results for \"{}\"".format(payload["keyword"]))
        return {"results": []}


def post_form(data=None):
    r = requests.post(IWM_DATA_URI, data=data)
    if 200 == r.status_code:
        return r.json()
    else:
        return {"cellTokens": []}


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
            add_cache_headers(headers, cached)
            if cached["fresh"] and not uri.startswith(IWM_INFO_URI):
                return BeautifulSoup(cached["blob"], "html.parser")
        r = requests.get(uri, headers=headers, timeout=SEARCH_TIMEOUT)
        if 200 == r.status_code:
            soup = BeautifulSoup(r.content, "html.parser")
            for x in soup(["style"]):
                x.extract()
            headers = None if uri.startswith(IWM_INFO_URI) else r.headers
            c.set(uri, str(soup), headers)
            return soup
        if 304 == r.status_code:
            c.touch(uri, r.headers)
            return BeautifulSoup(cached["blob"], "html.parser")
        return None
