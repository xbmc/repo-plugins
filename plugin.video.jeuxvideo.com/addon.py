import urllib2
import contextlib
import collections
import time
import re
import xml.etree.ElementTree as ET
import HTMLParser
import email.utils
from datetime import datetime
from xbmcswift2 import Plugin, xbmcgui

plugin = Plugin()

#########################
##  Resource fetching  ##
#########################
WS_MACHINES = 'https://ws.jeuxvideo.com/00.machines_version.xml'
WS_CATEGORIES = {
    'gaming_live': 'http://www.jeuxvideo.com/rss/itunes.xml',
    'chroniques': 'http://www.jeuxvideo.com/rss/itunes-chroniques.xml',
    'reportage': 'http://www.jeuxvideo.com/rss/itunes_reportage.xml',
}

for platform in [ 'pc', 'ps4', 'xo', 'ps3', '360', 'wiiu', 'wii', '3ds', 'vita', 'ds', 'psp', 'iphone', 'android' ]:
    WS_CATEGORIES[platform] = 'http://www.jeuxvideo.com/rss/itunes-%s.xml' % (platform, )

RESOLUTIONS = [ '270p', '400p', '720p', '1080p' ]

def call_ws(url):
    ''' Returns a XML tree parsed from the result of given WebService url. '''
    plugin.log.info('Calling WS: %s', url)
    request = urllib2.Request(url)
    with contextlib.closing(urllib2.urlopen(request)) as handle:
        return ET.parse(handle)

Machine = collections.namedtuple('Machine', [ 'id', 'name', 'icon' ])
Video = collections.namedtuple('Video', [ 'title', 'desc', 'date', 'length',  'thumbnail', 'urls' ])

def safe_find(element, match, default=None):
    ''' Used to provide a default value for non-essentials elements. '''
    e = element.find(match)
    return e.text if e is not None else default

def parse_length(t):
    ''' str('<min>:<sec>') => int(<seconds>) '''
    splitted = t.split(':')
    return int(splitted[0]) * 60 + int(splitted[1])

def get_thumb(**kwargs):
    if '-' in kwargs['kind'] or '_' in kwargs['kind']:
        kwargs['kind'] = kwargs['kind'].replace('-', '_')
        return 'http://image.jeuxvideo.com/images/videos/{kind}_images/{id}-high.jpg'.format(**kwargs)
    else:
        return 'http://image.jeuxvideo.com/images/videos/{kind}-images/{id}-high.jpg'.format(**kwargs)

def get_video(**kwargs):
    return 'http://{subdomain}.jeuxvideo.com/{path}-{reso}.mp4'.format(**kwargs)

@plugin.cached(5)
def get_videos(category):
    videos = call_ws(WS_CATEGORIES[category]).findall('.//item')
    result = []
    # the text items are CDATA... but still have XML entities...
    unescape = HTMLParser.HTMLParser().unescape

    for v in videos:
        enc = v.find('enclosure')
        data = re.search(r'jeuxvideo.com/(?P<path>(?P<kind>.+?)/(?P<id>.+?))(?:\-\D+)?.mp4', enc.attrib['url']).groupdict()
        plugin.log.info('uri=%s data=%s', enc.attrib['url'], repr(data))
        result.append(Video(
            title     = unescape(v.find('title').text),
            desc      = unescape(safe_find(v, 'description', '')),
            # yay, Python date handling!
            date      = datetime.fromtimestamp(time.mktime(email.utils.parsedate(safe_find(v, 'pubDate', 'Sat, 1 Jan 2000, 00:00:00')))),
            length    = parse_length(enc.attrib['length']),
            thumbnail = get_thumb(**data),
            urls      = [
                enc.attrib['url'],                                   # 270p
                get_video(subdomain='videohd', reso='high', **data), # 400p
                get_video(subdomain='video720', reso='720p', **data),
                get_video(subdomain='video1080', reso='1080p', **data),
            ]
        ))
    return result

##################
##  Item lists  ##
##################

@plugin.route('/')
def index():
    return [ {
        'label': plugin.get_string(30001),
        'path': plugin.url_for('category_index', category='gaming_live'),
    }, {
        'label': plugin.get_string(30002),
        'path': plugin.url_for('category_index', category='chroniques'),
    }, {
        'label': plugin.get_string(30003),
        'path': plugin.url_for('category_index', category='reportage'),
    }, {
        'label': plugin.get_string(30201),
        'path': plugin.url_for('category_index', category='pc'),
    }, {
        'label': plugin.get_string(30202),
        'path': plugin.url_for('category_index', category='ps4'),
    }, {
        'label': plugin.get_string(30203),
        'path': plugin.url_for('category_index', category='xo'),
    }, {
        'label': plugin.get_string(30204),
        'path': plugin.url_for('category_index', category='ps3'),
    }, {
        'label': plugin.get_string(30205),
        'path': plugin.url_for('category_index', category='360'),
    }, {
        'label': plugin.get_string(30206),
        'path': plugin.url_for('category_index', category='wiiu'),
    }, {
        'label': plugin.get_string(30207),
        'path': plugin.url_for('category_index', category='wii'),
    }, {
        'label': plugin.get_string(30208),
        'path': plugin.url_for('category_index', category='3ds'),
    }, {
        'label': plugin.get_string(30209),
        'path': plugin.url_for('category_index', category='vita'),
    }, {
        'label': plugin.get_string(30210),
        'path': plugin.url_for('category_index', category='ds'),
    }, {
        'label': plugin.get_string(30211),
        'path': plugin.url_for('category_index', category='psp'),
    }, {
        'label': plugin.get_string(30212),
        'path': plugin.url_for('category_index', category='iphone'),
    }, {
        'label': plugin.get_string(30013),
        'path': plugin.url_for('category_index', category='android'),
    } ]

def select_url(urls):
    ''' Chose one of the available URLs depending on settings and available resolutions. '''
    best = plugin.get_setting('video_resolution', int)
    try:
        # find the matching item or a lower resolution one
        return next( u for u in reversed(urls[:best+1]) if u )
    except StopIteration:
        # nothing? search in the higher ones
        return next( u for u in urls[best:] if u )

@plugin.route('/categories/<category>/')
def category_index(category):
    videos = get_videos(category)
    return [ {
        'label': v.title,
        'thumbnail': v.thumbnail,
        'stream_info': { 'video': { 'duration': v.length } },
        'info': {
            'date': v.date.strftime('%d.%m.%Y'),
            'plot': v.desc,
        },
        'path': select_url(v.urls),
        'context_menu': [ ( plugin.get_string(30005) % res, 'PlayMedia(%s)' % v.urls[i] )
                          for i, res in enumerate(RESOLUTIONS) if v.urls[i] ],
        'is_playable': True
    } for v in videos ]

@plugin.route('/clear_cache')
def clear_cache():
    plugin.clear_function_cache()
    xbmcgui.Dialog().ok(plugin.get_string(30000), plugin.get_string(30104))

if __name__ == '__main__':
    plugin.run()
