#!/usr/bin/env python
# encoding: UTF-8

import re
import requests
from bs4 import BeautifulSoup


def get_document(url):
    """
    .. py:function:: get_document(url)

    Downloads url and returns a BeautifulSoup object

    :param url: An url
    :return BeautifulSoup "document"
    """
    req = requests.get(url)
    doc = BeautifulSoup(req.content, "html.parser")
    return doc

def get_stream_info(page_url):
    """
    .. py:function:: get_stream_info(page_url)

    Get a page url and finds the url of the rtmp stream

    :param page_url: An url to a page with a media player
    :return a 3-tuple of paths useful for playing videos
    """
    doc = get_document(page_url)

    #Get urls for the swf player and playpath
    params = doc.find_all('param')
    swfplayer = 'http://ruv.is{0}'.format(params[0].get('value'))
    details = params[1].get('value')
    playpath = re.search('streamer=(.*?)&(file=.*?)&stre', details).group(2)

    # Get the url of the actual rtmp stream
    source_tags = doc.find_all('source')
    if source_tags and source_tags[0].get('src'): #RÚV
        rtmp_url = source_tags[0].get('src')
    else: #RÁS 1 & 2
        # The ip address of the stream server is returned in another page
        cache_url = doc.select('script[src*="load.cache.is"]')[0].get('src')
        res = requests.get(cache_url)
        cache_ip = re.search('"([^"]+)"', res.content).group(1)

        # Now that we have the ip address we can insert it into the URL
        source_js = doc.find('script', text=re.compile(r'tengipunktur')).text
        source_url = re.search(r"'file': '(http://' \+ tengipunktur \+ '[^']+)", source_js).group(1)

        rtmp_url = source_url.replace("' + tengipunktur + '", cache_ip)

    return (playpath, rtmp_url, swfplayer)

def get_videos(url):
    """
    .. py:function:: get_videos(url)

    Find playable items in a group (like fréttir or barnaefni)

    :param url: The url to the group
    :return A list of of 2-tuples with item name and page url
    """
    doc = get_document(url)
    episodes = []

    #Every tab has a player with the newest/featured item. Get the name of it.
    featured_item = doc.select('.sarpefst div h1')
    if featured_item:
        featured_name = featured_item[0].text
        featured_date = doc.select('.sarpur-date')[0].text.split(' | ')[0]
        title = u"{0} - {1}".format(featured_name, featured_date)
        episodes.append((title, url))

    #Get the listed items
    for item in doc.select('.sarplisti li'):
        item_link = item.find_all("a")[0]
        item_date = item.find_all("em")[0].text
        page_url = u"http://www.ruv.is{0}".format(item_link['href'])
        title = u"{0} - {1}".format(item_link.get('title'), item_date)
        episodes.append((title, page_url))

    return episodes

def get_podcast_shows(url):
    """
    .. py:function:: get_podcast_shows(url)

    Gets the names and rss urls of all the podcasts (shows)

    :param url: The url to the podcast index
    :return A list of 2-tuples with show name and rss url

    """
    doc = get_document(url)
    shows = []

    for show in doc.select("ul .hladvarp-info"):
        title = show.select('li h4')[0].text
        show_url = show.select("li a[href*=http]")[0].get('href')
        shows.append((title, show_url))

    return shows

def get_podcast_episodes(url):
    """
    .. py:function:: get_podcast_episodes(url)

    Gets the items from the rss feed

    :param url: Get all the playable items in podcast rss
    :return a list of 2-tuples with airdate and media url

    """
    doc = get_document(url)
    episodes = []

    for item in doc.find_all("guid"):
        url = item.text
        date = item.select('~ pubdate')[0].text
        episodes.append((date, url))

    return episodes
