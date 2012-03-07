import urllib2
import re
from datetime import datetime
from base64 import b64decode
from BeautifulSoup import BeautifulSoup

MAIN_URL = 'http://m.wimp.com/'

MONTHS = {'Jan': 1,
          'Feb': 2,
          'Mar': 3,
          'Apr': 4,
          'May': 5,
          'Jun': 6,
          'Jul': 7,
          'Aug': 8,
          'Sep': 9,
          'Oct': 10,
          'Nov': 11,
          'Dec': 12}


def get_current_videos():
    tree = __get_tree(MAIN_URL)
    return __get_videos(tree)


def get_archive_dates():
    url = MAIN_URL + 'archives'
    tree = __get_tree(url)
    archive_dates = []
    for entry in tree.findAll('a', {'class': 'b'}):
        title = entry.string.strip()
        archive_id = entry['href'].replace('/archives/', '').strip()
        archive_dates.append({'title': title,
                              'archive_id': archive_id})
    return archive_dates


def get_videos_by_archive_date(date):
    url = MAIN_URL + 'archives/%s' % date
    tree = __get_tree(url)
    return __get_videos(tree)


def get_search_result(query):
    url = MAIN_URL + 'search?query=%s' % query
    tree = __get_tree(url)
    return __get_videos(tree)


def get_random_video_url(mobile=False):
    return get_video_url('random', mobile)


def get_video_url(video_id, mobile=False):
    log('get_video_url started with video_id=%s mobile: %s' % (video_id,
                                                               mobile))
    url = MAIN_URL + video_id

    def _mobile(url):
        log('get_video_url mobile mode')
        tree = __get_tree(url, mobile=True)
        title = tree.head.title.string.replace('[VIDEO]', '').strip()
        video_url = tree.find('a', {'id': 'video'})['href']
        return video_url, title

    def _flv(url):
        log('get_video_url flv mode')
        tree = __get_tree(url, mobile=False)
        title = tree.head.title.string.replace('[VIDEO]', '').strip()
        r_js = re.compile('lxUTILsign')
        r_gc = re.compile('var googleCode = \'(.+?)\';')  # funny idea :-)
        r_vurl = re.compile('"file","(.+?)"')
        try:
            js_code = tree.find('script', text=r_js).string.strip()
            js_params = b64decode(re.search(r_gc, js_code).group(1))
            video_url = re.search(r_vurl, js_params).group(1)
        except AttributeError:
            log('get_video_url flv mode FAILED')
            video_url = None
        return video_url, title

    if not mobile:
        video_url, title = _flv(url) or _mobile(url)
    else:
        video_url, title = _mobile(url)
    return video_url, title


def __get_videos(tree):
    videos = []
    page_title = tree.head.title.string
    year = None
    if page_title:
        year = filter(lambda s: s.isdigit(), page_title)
    if not year:
        year = datetime.now().year
    for video in tree.findAll('div', {'class': 'video-item'}):
        title = video.find('a').string.strip()
        video_id = video.find('a')['href'].replace(MAIN_URL, '').strip('/')
        date_str = video.find('span', {'class': 'video_date'}).string
        month_str, day_str = date_str.split()
        month = MONTHS.get(month_str)
        date = '%02i.%02i.%s' % (int(day_str), month, year)
        videos.append({'title': title,
                       'video_id': video_id,
                       'date': date})
    return videos


def __get_tree(url, mobile=True):
    if mobile:
        if '?' in url:
            url = url + '&nord'
        else:
            url = url + '?nord'
    log('__get_tree opening url: %s' % url)
    req = urllib2.Request(url)
    req.add_header('Accept', ('text/html,application/xhtml+xml,'
                              'application/xml;q=0.9,*/*;q=0.8'))
    req.add_header('User-Agent', ('Mozilla/5.0 (X11; Linux i686) '
                                  'AppleWebKit/535.21 (KHTML, like Gecko) '
                                  'Chrome/19.0.1041.0 Safari/535.21'))
    html = urllib2.urlopen(req).read()
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def log(msg):
    print('%s scraper: %s' % ('wimp.com', msg))
