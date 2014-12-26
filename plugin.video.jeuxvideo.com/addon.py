import urllib2
import contextlib
import collections
import operator
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from xbmcswift2 import Plugin

plugin = Plugin()

#########################
##  Resource fetching  ##
#########################
# this addon uses the webservice API used by mobile apps, URLs and credentials have been found by MITM.

# authentication handing with urllib2 is so munch messy that it is quicker to do it directly
# the identifiers seems to be hard-coded in apps, they will probably be revoked one day...
WS_AUTH = 'Basic YXBwX2FuZF9tczpEOSFtVlI0Yw=='
WS_MACHINES = 'https://ws.jeuxvideo.com/00.machines_version.xml'
WS_CATEGORIES = {
    'gaming_live': 'https://ws.jeuxvideo.com/04.flux_videos_gaming.xml',
    'chroniques': 'https://ws.jeuxvideo.com/04.flux_videos_chroniques.xml',
    'autres': 'https://ws.jeuxvideo.com/04.flux_videos_autres.xml',
}
RESOLUTIONS = [ '270p', '400p', '720p', '1080p' ]

def call_ws(url):
    ''' Returns a XML tree parsed from the result of given WebService url. '''
    plugin.log.info('Calling WS: %s', url)
    request = urllib2.Request(url, headers={ 'Authorization': WS_AUTH })
    with contextlib.closing(urllib2.urlopen(request)) as handle:
        return ET.parse(handle)

Machine = collections.namedtuple('Machine', [ 'id', 'name', 'icon' ])
Video = collections.namedtuple('Video', [ 'title', 'type', 'desc', 'date', 'length', 'machines', 'thumbnail', 'urls' ])

def safe_find(element, match, default=None):
    ''' Used to provide a default value for non-essentials elements. '''
    e = element.find(match)
    return e.text if e is not None else default

def parse_length(t):
    ''' str('<min>:<sec>') => int(<seconds>) '''
    splitted = t.split(':')
    return int(splitted[0]) * 60 + int(splitted[1])

def safe_strptime(date_string, format):
    ''' WTF?? See http://forum.kodi.tv/showthread.php?tid=112916 '''
    try: return datetime.strptime(date_string, format)
    except TypeError: return datetime(*(time.strptime(date_string, format)[0:6]))

@plugin.cached(24*60)
def get_machines():
    machines = call_ws(WS_MACHINES).findall('./machine')
    return [ Machine(m.find('id').text, m.find('nom').text, safe_find(m, 'url_icone')) for m in machines ]

@plugin.cached(30)
def get_videos(category):
    videos = call_ws(WS_CATEGORIES[category]).findall('./video')

    return [ Video(
        title     = v.find('titre').text,
        type      = safe_find(v, 'type'),
        desc      = safe_find(v, 'resume'),
        date      = safe_strptime(safe_find(v, 'date', '01/01/2000'), '%d/%m/%Y'),
        length    = parse_length(safe_find(v, 'duree', '0:00')),
        machines  = set( m.text for m in v.findall('./id_machine') ),
        thumbnail = safe_find(v, 'url_image'),
        urls      = [
            safe_find(v, 'url_expanded'),
            safe_find(v, 'url_expanded400'),
            safe_find(v, 'url_expanded720'),
            safe_find(v, 'url_expanded1080'),
        ]
    ) for v in videos ]

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
        'path': plugin.url_for('category_index', category='autres'),
    } ]

@plugin.route('/categories/<category>/')
def category_index(category):
    result = [ {
        'label': plugin.get_string(30004),
        'path': plugin.url_for('video_list', category=category, machine='all')
    } ]

    # display only machines that actually contain videos
    existing_machines = reduce(operator.ior, ( v.machines for v in get_videos(category) ), set())

    for m in get_machines():
        if m.id not in existing_machines: continue
        result.append({
            'label': m.name,
            'path': plugin.url_for('video_list', category=category, machine=m.id),
            'icon': m.icon
        })

    return result

def select_url(urls):
    ''' Chose one of the available URLs depending on settings and available resolutions. '''
    best = plugin.get_setting('video_resolution', int)
    try:
        # find the matching item or a lower resolution one
        return next( u for u in reversed(urls[:best+1]) if u )
    except StopIteration:
        # nothing? search in the higher ones
        return next( u for u in urls[best:] if u )

@plugin.route('/categories/<category>/<machine>/')
def video_list(category, machine):
    videos = get_videos(category)
    if machine != 'all':
        videos = filter(lambda v: machine in v.machines, videos)
    return [ {
        'label': '[%s] %s' % (v.type, v.title) if v.type else v.title,
        'thumbnail': v.thumbnail,
        'stream_info': { 'video': { 'duration': v.length } },
        'info': {
            'date': v.date.strftime('%d.%m.%Y'),
            'plot': v.desc,
        },
        'path': select_url(v.urls),
        'context_menu': [ ( plugin.get_string(30005) % res, 'PlayMedia(%s)' % v.urls[i] ) for i, res in enumerate(RESOLUTIONS) ],
        'is_playable': True
    } for v in videos ]

if __name__ == '__main__':
    plugin.run()
