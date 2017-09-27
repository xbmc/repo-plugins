#!/usr/bin/env python
# encoding: UTF-8

import requests
import itertools
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
from sarpur import logger


def strptime(date_string, format):
    """
    Wrapper for datetime.strptime() because of an odd bug.
    See: http://forum.kodi.tv/showthread.php?tid=112916

    :param date_string: A string representing a date
    :param format: The format of the date
    :return: A datetime object
    """
    try:
        return datetime.strptime(date_string, format)
    except TypeError:
        return datetime(*(time.strptime(date_string, format)[0:6]))

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


def get_media_url(page_url):
    """
    Find the url to the MP4/MP3 on a page

    :param page_url: Page to find the url on
    :return: url
    """

    doc = get_document(page_url)
    sources = [tag['jw-src']
               for tag in doc.find_all('source')
               if tag.has_attr('jw-src')]

    if len(sources) == 0:
        return -1

    return u"http://smooth.ruv.cache.is/{0}".format(sources[0][4:])

def get_live_url(channel):
    """
    Finds a live stream url for channel
    :param channel: Slug name of channel
    :return An url
    """
    apiurl = "http://ruv.is/sites/all/themes/at_ruv/scripts/ruv-stream.php?format=json"    
    try:
        json = requests.get(apiurl + "&channel=" + channel)      
    except:
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
        'url': show.parent.find_all('li')[1].a['href'],
        'img': show.a.img["src"],
        'name': show.a.span.text.capitalize()
    } for show in doc.find_all("h4"))

    rest = ({
        'url': show.a['href'],
        'img': None,
        'name': show.parent.find('strong').a.text.capitalize()
    } for show in doc.find_all('div', 'views-field-views-conditional'))

    return sorted(itertools.chain(featured, rest), key=lambda show: show['name'])

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
        while date == None:
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
            'Premiered': parse_pubdate(item.select('pubdate')[0].text).strftime("%d.%m.%Y"),
            'Duration': duration_to_seconds(item.find('itunes:duration').text),
            'title': item.title.text,
            'Plot': item.description.text
        }
        for item in doc.find_all("item")
    )

def search(query):
    """
    Search for media

    :param query: Query string
    :return: A list of dicts (or empty list)
    """

    query_url = u"http://ruv.is/slisti/ruv?title={0}".format(query)
    doc = get_document(query_url)

    items = []
    pat = re.compile(r'\d{2}.\d{2}.\d{4}')

    for show in doc.find_all("div", class_="views-field views-field-views-conditional"):
        (img_div, desc_div, info_div) = (tag
                                         for tag
                                         in show.find("div", class_="clearfix").children
                                         if tag.name)

        img = img_div.find("img", title=u"Mynd með færslu")

        try:
            (episode, total_episodes) =  desc_div.strong.text.split(u' þáttur af ')
        except (AttributeError, ValueError):
            episode = total_episodes = None

        items.append({
            'img':  img and img.get('srcset') or None,
            'name': desc_div.h3.a.text,
            'url': u"http://ruv.is{0}".format(desc_div.h3.a['href']),
            'Episode': episode,
            'Premiered': pat.search(info_div.text).group(0),
            'TotalEpisodes': total_episodes,
            'Plot': desc_div.text.strip()
        })

    return items