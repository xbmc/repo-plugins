import urllib2
import re
from BeautifulSoup import BeautifulSoup
from urllib import urlencode

IPAD_USERAGENT = (
    'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) '
    'AppleWebKit/531.21.10 (KHTML, like Gecko) '
    'Version/4.0.4 Mobile/7B334b Safari/531.21.10'
)

MOBILE_URL = 'http://m.collegehumor.com/'
MAIN_URL = 'http://www.collegehumor.com/'


def getCategories():
    url = MOBILE_URL + 'videos/browse'
    tree = __getTree(url)
    categories = []
    for a in tree.find('ul', {'data-role': 'listview'}).findAll('a'):
        if 'playlist' in a['href']:
            print 'Skipping Playlist'
            continue
        categories.append({
            'title': a.string,
            'link': a['href'][1:]
        })
    return categories


def getVideos(category, page=1):
    post = {'render_mode': 'ajax'}
    url = MOBILE_URL + '%s/page:%s' % (category, page)
    tree = __getTree(url, post)
    videos = []
    elements = tree.find('ul', {'data-role': 'listview'}).findAll('a')
    for a in elements:
        if 'playlist' in a['href']:
            print 'Skipping Playlist'
            continue
        videos.append({
            'title': a.h3.string,
            'link': a['href'][1:],
            'image': a.img['src']
        })
    has_next_page = len(elements) == 24
    return videos, has_next_page


def getVideoFile(link):
    url = MAIN_URL + link
    tree = __getTree(url)

    print 'Simple, we used IPAD UA - so maybe we have luck'
    video_object = tree.find('video')
    if video_object and video_object.get('src'):
        return video_object['src']

    print 'No luck. Ok, maybe it\'s youtube?'
    re_youtube = re.compile('http://www.youtube.com/embed/(\w+)')
    youtube_iframe = tree.find('iframe', {'src': re_youtube})
    if youtube_iframe:
        yotube_id = re.search(re_youtube, youtube_iframe['src']).group(1)
        return ('plugin://plugin.video.youtube/'
                '?action=play_video&videoid=%s' % yotube_id)

    print 'Still no luck. But there could also be some ugly JS HTML5'
    re_flv = re.compile("flvSourceUrl: '([^']+)',")
    js_code = tree.find('script', {'type': 'text/javascript'},
                        text=re_flv)
    if js_code:
        flv_url = re.search(re_flv, js_code).group(1)
        return flv_url

    print 'Nope. We don\'t like multiple HTTP request, but...'
    url = MAIN_URL + 'moogaloop/video/%s' % link.split('/')[1]
    moogaloop_tree = __getTree(url)
    video_file = moogaloop_tree.video.file.string
    if 'manifest' not in video_file:
        return video_file

    print 'Noooo. OK, now we like HTTP requests, take another one!'
    re_content = re.compile("content: '([^']+)',")
    re_video_id = re.compile("videoId: '([^']+)',")
    re_video_url = re.compile('"adUrl":"([^"]+)"')
    js_code = tree.find('script', {'type': 'text/javascript'},
                        text=re_content)
    if js_code:
        content = re.search(re_content, js_code).group(1)
        video_id = re.search(re_video_id, js_code).group(1)
        url = (
            'http://ads.rnmd.net/getAds?delivery=jsonp&adType=videosrc'
            '&adDiv=%s&url=%s&appId=college_humor_web&v=1'
        ) % (video_id, content)
        tree = __getTree(url)
        json_code = tree.contents[0]
        video_url = re.search(re_video_url, json_code)
        if video_url:
            return video_url.group(1).replace('\/', '/')

    print 'Game Over - nothing to see here, move along...'
    raise NotImplementedError


def __getTree(url, data_dict=None):
    print 'Opening url: %s' % url
    if data_dict:
        post_data = urlencode(data_dict)
    else:
        post_data = ' '
    req = urllib2.Request(url, post_data)
    req.add_header('User-Agent', IPAD_USERAGENT)
    req.add_header('X-Requested-With', 'XMLHttpRequest')
    response = urllib2.urlopen(req).read()
    tree = BeautifulSoup(response, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree
