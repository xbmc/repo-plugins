import urllib2
import re
from BeautifulSoup import BeautifulSoup
from urllib import urlencode

USER_AGENT = 'XBMC addon plugin.video.4players'

CATEGORIES = ('Alle', 'TopRated', 'TopViews', 'Video-Fazit', 'PC-CDROM',
              'PlayStation3', '360', 'Wii', 'Handhelds')

URL_PREFIX = 'http://www.4players.de/4players.php/tvplayer/'


def getVideos(filter=None, page=1):
    if filter not in CATEGORIES:
        filter = CATEGORIES[0]
    post = {'currentpage': str(int(page) - 1),
            'singlefilter': filter,
            'funcname': 'aktuellevideos',
            'numcols': 5,
            'numshown': 20,
            'refreshskims': 1}
    url = 'http://www.4players.de/paginatecontent.php'
    html = __getAjaxContent(url, post)
    tree = BeautifulSoup(html)
    # last_page_num
    page_links = tree.findAll('a', {'class': 'pagenavi'})
    last_page_num = max([page_num.contents[0] for page_num in page_links \
                        if page_num.contents[0].isdigit()])
    # videos
    section = tree.find('div', {'class': re.compile('tv-weitere-container')})
    video_frames = section.findAll('li')
    videos = list()
    for frame in video_frames:
        link = frame.find('a', {'class': re.compile('tv-weiter-link')})
        # title
        title = link['title']
        # url
        video_page = link['href']
        url = video_page.replace(URL_PREFIX, '').replace('.html', '')
        # rating
        rating_div = frame.find('div', {'class':
                                        re.compile('^tv-weitere-rating')})
        if rating_div['class'][-7:-6] in str(range(1, 6)):
            rating = int(rating_div['class'][-7:-6])
        else:
            rating = 0
        # views
        views_div = frame.find('div', {'class':
                                        re.compile('^tv-weitere-views')})
        r = 'Views: (?P<views>[0-9]+)'
        m = re.search(r, unicode(views_div))
        if m:
            views = int(m.groupdict()['views'])
        else:
            views = 0
        # image
        skim_div = frame.find('div', {'class': 'skim'})
        if skim_div:
            image = skim_div['data-skimimageurl'].replace('skimimage', 'thumb160x90')
            # try to guess the thumb
        # date
        date_div = frame.find('div', {'class':
                                      re.compile('^tv-weitere-datum')})
        r = '(?P<day>[0-9]+)\.(?P<month>[0-9]+)\.(?P<year>20[0-9]+)'
        m = re.search(r, unicode(date_div))
        if m:
            date_dict = m.groupdict()
            date = '%s.%s.%s' % (date_dict['day'],
                                 date_dict['month'],
                                 date_dict['year'])
        else:
            date = ''
        # length
        len_div = frame.find('div', {'class':
                                     re.compile('^tv-weitere-laufzeit')})
        r = '(?P<min>[0-9]+):(?P<sec>[0-9]+) (Min\.|min|MIn\.)'
        m = re.search(r, unicode(len_div))
        if m:
            length_dict = m.groupdict()
            length = '%s:%s' % (length_dict['min'], length_dict['sec'])
        else:
            length = '0:00'
        # finalize
        videos.append({'title': title,
                       'image': image,
                       'url': url,
                       'rating': rating,
                       'views': views,
                       'date': date,
                       'length': length})
    return videos, last_page_num


def __getAjaxContent(url, data_dict=None):
    if data_dict:
        post_data = urlencode(data_dict)
    else:
        post_data = ' '
    req = urllib2.Request(url, post_data)
    req.add_header('User-Agent', USER_AGENT)
    req.add_header('Accept', 'text/javascript, */*')
    req.add_header('Content-Type',
                   'application/x-www-form-urlencoded; charset=UTF-8')
    req.add_header('X-Requested-With', 'XMLHttpRequest')
    response = urllib2.urlopen(req).read()
    return response


def getVideoFile(page_url):
    video_page = URL_PREFIX + page_url + '.html'
    html = __getAjaxContent(video_page)
    r = 'https://login.4players.de/flash/jw5/player.swf\?file=(?P<url>.+?)&amp;'
    m = re.search(r, html)
    url = m.groupdict()['url']
    return url


def getCategories():
    return CATEGORIES
