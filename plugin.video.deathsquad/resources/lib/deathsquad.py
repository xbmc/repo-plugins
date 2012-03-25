import urllib
import urllib2
import re
import os
import traceback
from BeautifulSoup import BeautifulSoup
from elementtree import ElementTree


class ElementWrapper:
    
    def __init__(self, element, ns=None):
        self._element = element
        self._ns = ns or ""
        
    def __getattr__(self, tag):
        if tag.startswith("__"):
            raise AttributeError(tag)
        return self._element.findtext(self._ns + tag)


class RSSWrapper(ElementWrapper):

    def __init__(self, feed):
        channel = feed.find("channel")
        ElementWrapper.__init__(self, channel)
        self._items = channel.findall("item")

    def __getitem__(self, index):
        return ElementWrapper(self._items[index])


def get_remote_data(url):
    
    """Retrieve and return remote resource as string
    
    Arguments:  url -- A string containing the url of a remote page to retrieve
    Returns:    data -- A string containing the contents to the remote page"""

    # Build the page request including setting the User Agent
    req  = urllib2.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

    # connect to url using urlopen
    client = urllib2.urlopen(req)
    
    # read data from page
    data = client.read()
    
    # close connection to url
    client.close()
    
    # return the retrieved data
    return data


def split_seq(seq,size):
    """ Split up seq in pieces of size """
    return [seq[i:i+size] for i in range(0, len(seq), size)]


def get_video_details(url):
    """
    Gets the list of thumbnails, video URLs and titles from the video site and display the list

    @param string url - Main URL of uStream page (without page number)
    @param int page_no - Page number to get

    @returns dictionary
    """     

    # Create a new soup instance and assign a video list html to a variable
    soup = BeautifulSoup(get_remote_data(url))

    blogentry = soup.find('div', 'entry_content')
    
    if not blogentry:
        
        return ''
    
    video = {}
    
    # Get the title
    video['title'] = soup.find('hgroup', 'post-title').h1.string

    try:
    
        # Get the video URL
        video['url'] = blogentry.p.center.a['href']
    
    except:
    
        return ''
    
    try:
    
        # Get the thumbnail
        video['thumb'] = blogentry.p.center.a.img['src']
    
    except:
    
        video['thumb'] = ''
    
    if re.search(r'vimeo', video['url']):
        
        video['src'] = 'vimeo'
        
        # Extract clip ID from the URL, method varying depending on whether it's player.vimeo.com or vimeo.com/id
        if re.search(r'player.vimeo.com/video', video['url']):
        
            url_section = video['url'].split('/')
            clip_id = url_section[4]
            clip_id = clip_id.split('?')[0]
        
        else:
        
            url_section =  video['url'].split('/')
            clip_id = url_section[3]
        
        video['id'] = clip_id
    
    elif re.search(r'ustream', video['url']):
    
        # get src and id if video is ustream
        video['src'] = 'ustream'
        video['id'] = video['url'].replace('http://www.ustream.tv/recorded/', '')
    
    else:
    
        return ''

    return video


def pull_video_list(page_number = 1, category_url = ''):
    
    URL = 'http://deathsquad.tv/?feed=rss2&%s' % category_url
    
    tree = ElementTree.parse(urllib2.urlopen(URL))

    feed = RSSWrapper(tree.getroot())

    feed_items = []
    
    items_per_page = 15
    
    for item in feed:
        feed_items.append(item.link)
    
    return split_seq(feed_items, items_per_page)[page_number -1]



if __name__ == '__main__':
        
        # Just testing
        print pull_video_list(1)
