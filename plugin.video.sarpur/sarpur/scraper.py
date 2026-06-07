#!/usr/bin/env python
# encoding: UTF-8
"""
    Long term strategy should probably be to deprecate everything here in favor
    of api.py.
"""
from __future__ import absolute_import

from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sarpur import logger  # noqa
from util import strptime


def duration_to_seconds(duration):
    """
    Takes a string in the format hh:mm:ss or hh:mm and converts
    to a number of minutes
    :param duration: String with hours and minutes seperated with a colon
    :return: A number of minutes
    """
    hms = duration.split(":")
    if len(hms) == 3:
        return int(hms[0]) * 60 * 60 + int(hms[1]) * 60 + int(hms[2])
    if len(hms) == 2:
        return int(hms[0]) * 60 + int(hms[1])
    else:
        return 0


def get_document(url):
    """
    Downloads url and returns a BeautifulSoup object

    :param url: Any url
    :return BeautifulSoup "document"
    """
    req = requests.get(url)
    doc = BeautifulSoup(req.content, "html.parser")
    return doc


def get_live_url(channel):
    """
    Finds a live stream url for channel
    :param channel: Slug name of channel
    :return An url
    """
    try:
        json = requests.get(f"https://geo.spilari.ruv.is/channel/{channel}")
    except Exception:
        return -1

    return json.json()["url"]


def get_podcast_episodes(url):
    """
    Gets the items from the rss feed

    :param url: RSS URL
    :return a generator of dictionaries

    """

    def parse_pubdate(date_string):
        """
        Change pubdate string to datetime object. Tries a bunch of
        possible formats, but if none of them is a match, it will
        return a epoch = 0 datetime object

        :param date_string: A string representing a date
        :return: datetime object
        """
        date_formats = (
            "%a, %d %b %Y %H:%M:%S +0000",
            "%a, %d %b %Y",
            "%a, %d %b %Y%H:%M:%S +0000",
            "%a, %d %b %Y %H:%M",
            "%a, %d %b %Y %H.%M",
        )
        df_generator = (format for format in date_formats)

        date = None
        while date is None:
            try:
                date = strptime(date_string, next(df_generator))
            except ValueError:
                pass
            except StopIteration:
                date = datetime.fromtimestamp(0)

        return date

    doc = get_document(url)

    return (
        {
            "url": item.enclosure["url"],  # Beautifulsoup parses <link> wrong
            "Premiered": parse_pubdate(item.select("pubdate")[0].text).strftime(
                "%d.%m.%Y"
            ),
            # 'Duration': duration_to_seconds(item.find('itunes:duration').text),
            "title": item.title.text,
            "Plot": item.description.text,
        }
        for item in doc.find_all("item")
    )
