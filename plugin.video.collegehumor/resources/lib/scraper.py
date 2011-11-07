import urllib2
import re
from BeautifulSoup import BeautifulSoup
from urllib import urlencode

IPAD_USERAGENT = ('Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; '
                  'en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Versi'
                  'on/4.0.4 Mobile/7B314 Safari/531.21.10')

MAIN_URL = 'http://m.collegehumor.com/'


def getCategories():
    url = MAIN_URL + 'videos/browse'
    tree = __getTree(url)
    categories = list()
    for element in tree.find('ul', {'data-role': 'listview'}).findAll('a'):
        categories.append({'title': element.string,
                           'link': element['href'][1:]})
    return categories


def getVideos(category, page=1):
    post = {'render_mode': 'ajax'}
    url = MAIN_URL + '%s/page:%s' % (category, page)
    tree = __getTree(url, post)
    videos = list()
    elements = tree.find('ul', {'data-role': 'listview'}).findAll('li')
    for element in elements:
        if element.a and re.search(re.compile('/video/'), element.a['href']):
            videos.append({'title': element.a.h3.string,
                           'link': element.a['href'][1:],
                           'image': element.a.img['src'],
                           'tagline': element.p.string})
    has_next_page = (len(elements) >= 20)
    return videos, has_next_page


def getVideoFile(link):
    url = MAIN_URL + link
    tree = __getTree(url)
    return tree.find('video')['src']


def __getTree(url, data_dict=None):
    if data_dict:
        post_data = urlencode(data_dict)
    else:
        post_data = ' '
    req = urllib2.Request(url, post_data)
    req.add_header('User-Agent', IPAD_USERAGENT)
    req.add_header('Accept', ('text/html,application/xhtml+xml,'
                              'application/xml;q=0.9,*/*;q=0.8'))
    response = urllib2.urlopen(req).read()
    tree = BeautifulSoup(response, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree
