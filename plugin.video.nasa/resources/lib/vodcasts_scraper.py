from urllib2 import urlopen
from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup
import re

MAIN_URL = 'http://www.nasa.gov/rss/'


def get_vodcasts():
    log('get_vodcasts started')
    url = 'http://www.nasa.gov/multimedia/index.html'
    html = urlopen(url).read()
    e = BeautifulStoneSoup.HTML_ENTITIES
    tree = BeautifulSoup(html, convertEntities=e)
    vodcasts = []
    for section in tree.findAll('div', {'class': 'box_230_cap'}):
        if section.find('h2', text='Video Podcasts'):
            for row in section.findAll('tr'):
                cells = row.findAll('td')
                if len(cells) == 2:
                    title = cells[0].b.string
                    link = cells[1].a['href']
                    if '/rss/' in link:
                        vodcasts.append({'title': title[1:],
                                         'rss_file': link[5:]})
            break
    log('get_vodcasts finished with %d vodcasts' % len(vodcasts))
    return vodcasts


def show_vodcast_videos(rss_file):
    log('get_vodcasts started with rss_file=%s' % rss_file)
    r_media = re.compile('^media')
    url = MAIN_URL + rss_file
    rss = urlopen(url).read()
    e = BeautifulStoneSoup.XML_ENTITIES
    tree = BeautifulStoneSoup(rss, convertEntities=e)
    videos = []
    for item in tree.findAll('item'):
        if item.find(r_media):
            thumbnail = item.find(r_media)['url']
        else:
            thumbnail = 'DefaultVideo.png'
        videos.append({'title': item.title.string,
                       'thumbnail': thumbnail,
                       'url': item.enclosure['url'],
                       'description': item.description.string})
    log('show_vodcast_videos finished with %d videos' % len(videos))
    return videos


def log(text):
    print 'Nasa vodcasts scraper: %s' % text
