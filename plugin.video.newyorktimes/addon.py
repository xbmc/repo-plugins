#!/usr/bin/env python
'''
    New York Times XBMC Addon
    -------------------------

    Watch video from The New York Times.
    http://video.on.nytimes.com/

'''
import re
from urlparse import urljoin
from BeautifulSoup import BeautifulSoup as BS
from brightcove.api import Brightcove
from xbmcswift import Plugin, download_page
from resources.lib.brightcove import item_from_video

__author__ = 'Jonathan Beluch (jbel)'
__license__ = 'GPLv3'
__version__ = '0.1'

PLUGIN_NAME = 'New York Times'
PLUGIN_ID = 'plugin.video.newyorktimes'
plugin = Plugin(PLUGIN_NAME, PLUGIN_ID, __file__)

# NYT Brightcove read-only api token
TOKEN = 'cE97ArV7TzqBzkmeRVVhJ8O6GWME2iG_bRvjBTlNb4o.'
BASE_URL = 'http://video.nytimes.com/'
VIDEO_URL = 'http://video.nytimes.com/video'


def full_url(path):
    '''Returns a full url for a given path.'''
    return urljoin(BASE_URL, path)


def htmlify(url):
    '''Returns a BeautifulSoup object for a given url.'''
    return BS(download_page(url))


def parse_reference_id(url):
    '''Returns the reference id for a give topic URL on the NYT
    website.

    Returns the first match of a string of digits between two forward
    slashes.

    >>> parse_reference_id('foo/23bar/456/789/')
    456

    '''
    ptn = re.compile(r'/(\d+)/')
    match = ptn.search(url)
    if match:
        return match.group(1)
    return None


@plugin.route('/')
def show_topics():
    '''Shows all topics found on the New York Times video page. This
    includes subtopics.  Subtopic lables will be prefixed with the
    parent topic.

    For example, if 'Asia' is a subtopic underneath 'World News', the
    label will read 'World News: Asia'.

    '''
    def get_child_items(parent, sibling):
        '''Return items for child topics.'''

        def make_label(label, prefix):
            '''Some subtopics already contain the parent label so in
            this case just return as is.

            '''
            if label.startswith(prefix):
                return label
            return '%s: %s' % (prefix, label)

        parent_label = parent.a.string
        topics = sibling.findAll('li')
        items = [{
            'label': make_label(topic.a.string, parent_label),
            'url': plugin.url_for('show_videos',
                   reference_id=parse_reference_id(topic.a['href'])),
        } for topic in topics]

        return items

    html = htmlify(VIDEO_URL)
    nav = html.find('td', {'id': 'leftNav'})
    topics = nav.findAll('li', {'id': lambda _id: _id and
                                      _id.startswith('leftNavParent')})

    # Create items for all the parent topics
    items = [{
        'label': topic.a.string,
        'url': plugin.url_for('show_videos',
                              reference_id=parse_reference_id(
                                  topic.a['href'])),
    } for topic in topics]

    # In the NYT source, each of the child topics is not located inside
    # the parent tag, instead it is the next sibling tag
    for topic in topics:
        if topic.findNextSibling('li')['id'].startswith('leftNavChild'):
            items.extend(get_child_items(topic, topic.findNextSibling('li')))

    # Sort the items alphabetically so the sub topics appear clustered
    # with the parent topic
    sorted_items = sorted(items, key=lambda i: i['label'])
    return plugin.add_items(sorted_items)


@plugin.route('/videos/<reference_id>/')
def show_videos(reference_id):
    '''Displays all videos available for a given playlist. The order is
    the default order returned by the Brightcove API.
    '''
    brightcove = Brightcove(TOKEN)
    playlist = brightcove.find_playlist_by_reference_id(reference_id)
    items = [item_from_video(video) for video in playlist.videos]
    return plugin.add_items(items)


if __name__ == '__main__':
    plugin.run()
