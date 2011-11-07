import urllib2
import re
from BeautifulSoup import BeautifulSoup
from urllib import urlencode

IPAD_USERAGENT = (u'Mozilla/5.0 (iPad; U; CPU OS OS 3_2 like '
                  u'Mac OS X; en-us) AppleWebKit/531.21.10 (K'
                  u'HTML, like Gecko) Version/4.0.4 Mobile/7B'
                  u'367 Safari/531.21.10')

CATEGORIES = ('Alle', 'TopViews', 'TopRated', 'CDROM',
              'PlayStation2', 'PlayStation3', 'Wii', '360', 'NDS',
              'PSP', 'Video-Fazit')

URL_PREFIX = 'http://www.4players.de/4players.php/tvplayer/4PlayersTV/'


def getVideos(filter=None, page=1):
    if filter not in CATEGORIES:
        filter = CATEGORIES[0]
    post = {'currentpage': str(int(page) - 1),
            'filter': filter,
            'funcname': 'aktuellevideos',
            'numcols': 5,
            'numshown': 20,
            'refreshskims': 1}
    url = 'http://www.4players.de/ajax/paginatecontent.php'
    html = __getAjaxContent(url, post)
    tree = BeautifulSoup(html)
    # last_page_num
    page_links = tree.findAll('a', {'class': 'pagenavi'})
    last_page_num = max([page_num.contents[0] for page_num in page_links \
                        if page_num.contents[0].isdigit()])
    # videos
    video_frames = tree.findAll('div', {'class':
                                        re.compile('^videoitemframe')})
    videos = list()
    for frame in video_frames:
        video_item, video_info = frame.findAll('div', recursive=False)
        link = video_info.find('div', {'class': re.compile('^title')}).a
        # title
        title = link['title'].replace('[Video] ', '')
        # url
        video_page = link['href']
        url = video_page.replace(URL_PREFIX, '').replace('.html', '')
        # rating
        rating_div = video_info.find('div', {'class':
                                             re.compile('^rating stars')})
        if rating_div['class'][-1:] in str(range(1, 6)):
            rating = int(rating_div['class'][-1:])
        else:
            rating = 0
        # views
        r = 'Views: (?P<views>[0-9]+)'
        m = re.search(r, unicode(rating_div))
        if m:
            views = int(m.groupdict()['views'])
        else:
            views = 0
         # image
        r = 'skimimageurl="(?P<img_url>[^"]+)"'
        m = re.search(r, unicode(video_item))
        if m:
            image = m.groupdict()['img_url']
        else:
            image = None
        # date
        r = '(?P<day>[0-9]+)\.(?P<month>[0-9]+)\.(?P<year>20[0-9]+)'
        m = re.search(r, unicode(rating_div))
        if m:
            date_dict = m.groupdict()
            date = '%s.%s.%s' % (date_dict['day'],
                                 date_dict['month'],
                                 date_dict['year'])
        else:
            date = ''
        # length
        r = '(?P<min>[0-9]+):(?P<sec>[0-9]+) (Min\.|min|MIn\.)'
        m = re.search(r, unicode(rating_div))
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
    req.add_header('User-Agent', IPAD_USERAGENT)
    req.add_header('Accept', 'text/javascript, */*')
    req.add_header('Content-Type',
                   'application/x-www-form-urlencoded; charset=UTF-8')
    req.add_header('X-Requested-With', 'XMLHttpRequest')
    response = urllib2.urlopen(req).read()
    return response


def getVideoFile(page_url):
    video_page = URL_PREFIX + page_url + '.html'
    html = __getAjaxContent(video_page)
    tree = BeautifulSoup(html)
    link = tree.find('script', text=re.compile('video src'))
    r = '<video src="(?P<url>[^"]+)"'
    m = re.search(r, unicode(link))
    url = m.groupdict()['url']
    return url


def getCategories():
    return CATEGORIES
