from urllib2 import urlopen, Request, HTTPError, URLError
import re
from BeautifulSoup import BeautifulSoup

MAIN_URL = 'http://www.myzen.tv'


class NetworkError(Exception):
    pass


def get_free_videos():
    url = MAIN_URL + '/index.php/en/live-tv'
    tree = __get_tree(url)
    videos = []
    for li in tree.findAll('li', {'class': re.compile('ul-videos-li')}):
        videos.append({
            'label': li.img['title'],
            'thumbnail': __resize_icon(MAIN_URL + li.img['src']),
            'info': {'duration': li.span.string.strip()},
            'path': li.div.a['href'],
        })
    return videos


def get_rtmp_params(path):
    video_page_url = MAIN_URL + path
    html = __get_url(video_page_url)

    r_swf_url = re.compile("src: '(.*?)'")
    r_rtmp_url = re.compile("streamer: '(.*?)'")
    r_playpath = re.compile("file: '(.*?)'")
    r_app = re.compile("rtmp://.*?/(.*)")

    rtmp_url = re.search(r_rtmp_url, html).group(1)
    playpath = re.search(r_playpath, html).group(1)
    swf_url = re.search(r_swf_url, html).group(1)
    app = re.search(r_app, rtmp_url).group(1)

    rtmp_params = {
        'rtmp_url': rtmp_url,
        'playpath': 'mp4:%s' % playpath,
        'app': app,
        'swf_url': swf_url,
        'video_page_url': video_page_url,
    }
    return rtmp_params

def __resize_icon(url):
    return url.strip().replace('180_y', '590_y')


def __get_tree(url):
    log('__get_tree opening url: %s' % url)
    req = Request(url)
    req.add_header('Accept', ('text/html,application/xhtml+xml,'
                              'application/xml;q=0.9,*/*;q=0.8'))
    req.add_header('User-Agent', ('Mozilla/5.0 (X11; Linux i686) '
                                  'AppleWebKit/535.21 (KHTML, like Gecko) '
                                  'Chrome/19.0.1041.0 Safari/535.21'))
    html = __get_url(req)
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def __get_url(req):
    try:
        html = urlopen(req).read()
    except HTTPError, error:
        log('__urlopen HTTPError: %s' % error)
        raise NetworkError('HTTPError: %s' % error)
    except URLError, error:
        log('__urlopen URLError: %s' % error)
        raise NetworkError('URLError: %s' % error)
    return html


def log(msg):
    print('%s scraper: %s' % (MAIN_URL, msg))
