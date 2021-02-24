#!/usr/bin/env python
# encoding: UTF-8
'''
    Long term strategy should probably be to deprecate everything here in favor
    of api.py.
'''
import itertools
from datetime import datetime

from bs4 import BeautifulSoup
import requests
from sarpur import logger  # noqa


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
    apiurl = (
        "http://ruv.is/sites/all/themes/at_ruv/"
        "scripts/ruv-stream.php?format=json"
    )
    try:
        json = requests.get(apiurl + "&channel=" + channel)
    except Exception:
        return -1

    return json.json()['result'][1]


def get_podcast_shows(url):
    """
    Gets the names and rss urls of all the podcasts (shows)

    :param url: The url to the podcast index
    :return A generator of dictionaries
    """
    doc = get_document(url)

    featured = ({
        'url': show.find_all('a')[-1]['href'],
        'img': show.a.img["src"],
        'name': show.a.img["alt"]
    } for show in doc.find_all(class_="podcast-container"))

    rest = ({
        'url': show.a['href'],
        'img': None,
        'name': show.parent.find('strong').a.text.capitalize()
    } for show in doc.find_all('div', 'views-field-views-conditional'))

    return sorted(
        itertools.chain(featured, rest), key=lambda show: show['name']
    )


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
            '%a, %d %b %Y %H:%M:%S +0000',
            '%a, %d %b %Y',
            '%a, %d %b %Y%H:%M:%S +0000',
            '%a, %d %b %Y %H:%M',
            '%a, %d %b %Y %H.%M'
        )
        df_generator = (format for format in date_formats)

        date = None
        while date is None:
            try:
                date = strptime(date_string, df_generator.next())
            except ValueError:
                pass
            except StopIteration:
                date = datetime.fromtimestamp(0)

        return date

    doc = get_document(url)

    return (
        {
            'url': item.select('guid')[0].text,
            'Premiered': parse_pubdate(
                item.select('pubdate')[0].text
            ).strftime("%d.%m.%Y"),
            'title': item.title.text,
            'Plot': item.description.text
        }
        for item in doc.find_all("item")
    )
