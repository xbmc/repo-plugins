# -*- encoding: utf-8 -*-

# import os
import urllib
import httplib
from urlparse import urlparse
from xml.dom.minidom import parse
from bs4 import BeautifulSoup
import re


RTS_PODCAST_URL = u'http://www.rts.ch/services/podcasts/'
RTS_BASE_URL = u'http://www.rts.ch'
RTS_URL_RSS_FORMAT = u'?format=rss/podcast'


class tvEpisode:
    """Class about one tv episode."""
    def __init__(
            self, title=u'', info=u'', image=u'', pubDate=u'', videoUrl=u''):
        self.title = title
        self.info = info
        self.image = image
        self.pubDate = pubDate
        self.videoUrl = videoUrl


class tvShow:
    """Class about one tv show. Build an object for each tv show of the TSR.
    Please, use the function 'get_tv_show()' of this python module for that"""
    def __init__(self, title=u'', info=u'', imgUrl=u'', podcastUrl=u''):
        self.title = title
        self.info = info
        self.imgUrl = imgUrl
        self.podcastUrl = podcastUrl
        self.listOfEpisodes = []

    def getEpisodes(self, delta=0, number=0):
        """Get Episodes informations from the rss feed of the podcast"""
        tvShowDom = parse(urllib.urlopen(self.podcastUrl))
        for item in tvShowDom.getElementsByTagName('item'):
            epTitle = item.getElementsByTagName('title')[0].childNodes[0].data
            epInfo = re.sub(
                '</?p>',
                '',
                item.getElementsByTagName('itunes:summary')[0].childNodes[0].data
            )
            epImage = BeautifulSoup(
                item.getElementsByTagName('description')[0].childNodes[0].nodeValue
            ).img[u'src'].replace('w=80&h=57','w=260&h=227')
            epPubDate = item.getElementsByTagName('pubDate')[0].childNodes[0].data
            epVidUrl = item.getElementsByTagName('enclosure')[0].attributes['url'].childNodes[0].data
            self.listOfEpisodes.append(
                tvEpisode(
                    epTitle,
                    epInfo,
                    epImage,
                    epPubDate,
                    epVidUrl))


def get_tv_shows():
    """Function to get a list of all tv shows by RTS"""
    listOfTvShows = []
    podcastsParser = BeautifulSoup(urllib.urlopen(RTS_PODCAST_URL))
    for podcast in podcastsParser.find_all('li', 'item'):
        title = podcast.a[u'title']
        info = u''
        imgUrlOrigin = RTS_BASE_URL + podcast.img[u'src']
        imgUrl = imgUrlOrigin.replace('w=149&h=149','w=249&h=249')
        podcastUrl = RTS_BASE_URL + podcast.a[u'href'] + RTS_URL_RSS_FORMAT
        listOfTvShows.append(tvShow(title, info, imgUrl, podcastUrl))
    return listOfTvShows


def get_tv_show_from_podast_url(url):
    return tvShow(podcastUrl=url)

def get_HD_video_url_from(urlStr):
    """
    Get the url to the HD version of a video.
    If the HD version don't exist, it return the
    url given in input.
    """
    urlStrHD = urlStr.replace('1201k', '2201k')
    url = urlparse(urlStrHD)
    conn = httplib.HTTPConnection(url.netloc)
    conn.request('HEAD', url.path)
    result = conn.getresponse()
    if result.status == 200:
        return urlStrHD
    else:
        return urlStr
        
