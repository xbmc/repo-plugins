'''
    This module contains functions for scraping video links from
    http://new-stadium.tottenhamhotspur.com
'''

from urlparse import urljoin, urlparse
import json
import re
import os
from collections import namedtuple

from bs4 import BeautifulSoup as BS
import requests

URL_ROOT = "http://new-stadium.tottenhamhotspur.com/"

RE_EMBED = re.compile(r'kWidget\.embed\((.*)\)')

Video = namedtuple('Video', ['title', 'id'])


def get_soup(path):
    '''Return a BeautifulSoup tree for the provided new stadium path'''
    response = requests.get(urljoin(URL_ROOT, path))
    return BS(response.text, 'html.parser')


def get_cams():
    '''Generator for live stadium cameras'''
    soup = get_soup("interact")
    for stream_num, iframe in enumerate(soup('iframe', 'video-class'), start=1):
        yield Video(title='Live Stream {}'.format(stream_num),
                    id=os.path.basename(urlparse(iframe['src']).path))


def get_video_gallery():
    '''Generator for the new stadium video gallery videos'''
    soup = get_soup("video-gallery")
    for video in soup('div', 'video-new'):
        video_vars = json.loads(RE_EMBED.search(video.find(text=RE_EMBED)).group(1))
        yield Video(title=video.find_next_sibling('p').get_text().strip(),
                    id=video_vars['entry_id'])
