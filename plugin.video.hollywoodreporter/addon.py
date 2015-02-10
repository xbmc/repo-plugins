from urllib2 import urlopen, Request
import re
from BeautifulSoup import BeautifulSoup
from xbmcswift import Plugin
import pyamf.remoting.client as AMF
import pyamf

__ADDON_NAME__ = 'HollywoodReporter'
__ADDON_ID__ = 'plugin.video.hollywoodreporter'


UA = ('Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) '
      'AppleWebKit/535.1 (KHTML, like Gecko) '
      'Chrome/13.0.782.6 Safari/535.1')

MAIN_URL = 'http://www.hollywoodreporter.com'

plugin = Plugin(__ADDON_NAME__, __ADDON_ID__, __file__)


@plugin.route('/', default=True)
def show_categories():
    log('show_categories started')
    tree = __get_tree('%s/video' % MAIN_URL)
    items = []
    for div in tree.findAll('div', {'class': 'thr-subtitle-link'}):
        items.append({
            'label': div.a.string.replace('See All ', ''),
            'is_folder': True,
            'is_playable': False,
            'url': plugin.url_for(
                'show_videos',
                path=div.a['href'].replace('/videos/', ''),
                page='0'
            ),
        })
    items.append({
        'label': plugin.get_string(30001),
        'url': plugin.url_for('video_search'),
    })
    return plugin.add_items(items)


@plugin.route('/search/')
def video_search():
    log('search start')
    keyboard = xbmc.Keyboard('', plugin.get_string(30001))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        log('search gots a string: "%s"' % search_string)
        url = plugin.url_for('video_search_result',
                             search_string=search_string)
        plugin.redirect(url)


@plugin.route('/search/<search_string>/')
def video_search_result(search_string):
    log('video_search_result started with string=%s' % search_string)
    url = '%s/search?filters=type:video&keys=%s' % (MAIN_URL, search_string)
    tree = __get_tree(url)
    items = []
    for div in tree.findAll('div', {'class': 'search-result-item clearfix'}):
        dt = div.find('dt', {'class': 'title'})
        if not dt:
            continue
        items.append({
            'label': dt.a.string,
            'iconImage': div.find('img')['src'],
            'is_folder': False,
            'is_playable': True,
            'url': plugin.url_for(
                'play_video', path=dt.a['href'].replace('/video/', ''),
            ),
        })
    return plugin.add_items(items)


@plugin.route('/videos/<path>/<page>')
def show_videos(path, page='0'):
    log('show_videos started with path:"%s" page=%s' % (path, page))
    url = '%s/videos/%s' % (MAIN_URL, path)
    if int(page) > 0:
        url += '?page=%s' % page
    tree = __get_tree(url)
    items = []

    def parse_li(li):
        a = li.find('h4').a
        title = a.string
        thumb = li.find('img')['src']
        url = plugin.url_for(
            'play_video',
            path=a['href'].replace('/video/', ''),
        )
        return {'label': title,
                'iconImage': thumb,
                'is_folder': False,
                'is_playable': True,
                'url': url}

    div = tree.find('div', {'class': re.compile('thr-video-main')})
    for li in div.findAll('li'):
        items.append(parse_li(li))

    div = tree.find('div', {'class': re.compile('thr-video-most-recent')})
    for li in div.findAll('li', {'class': re.compile('module_wrap')}):
        items.append(parse_li(li))

    if tree.find('a', text='More Videos'):
        items.append({
            'label': plugin.get_string(30020),
            'is_folder': True,
            'is_playable': False,
            'url': plugin.url_for('show_videos', path=path,
                                  page=str(int(page) + 1)),
        })

    return plugin.add_items(items)


@plugin.route('/video/<path>')
def play_video(path):
    log('play_video started with path:"%s"' % path)
    video_page_url = '%s/video/%s' % (MAIN_URL, path)
    tree = __get_tree(video_page_url)
    player = tree.find('object', {'class': 'BrightcoveExperience'})
    if not player:
        log('play_video could not find brightcove player')
        re_class = re.compile('emvideo-youtube')
        youtube_video = tree.find('div', {'class': re_class})
        if youtube_video:
            log('play_video found embed youtube video')
            re_youtube_id = re.compile('http://www.youtube.com/v/(.*?)&')
            video_obj = youtube_video.find('object')
            video_id = re_youtube_id.search(video_obj['data']).group(1)
            playback_url = ('plugin://plugin.video.youtube/'
                            '?action=play_video&videoid=%s' % video_id)
            return plugin.set_resolved_url(playback_url)
    else:
        log('play_video found brightcove player')
        player_params = {
            'video_page_url': video_page_url,
            'player_id': str(player.find('param', {'name': 'playerID'})['value']),
            'video_id': str(player.find('param', {'name': 'videoID'})['value']),
            'player_key': str(player.find('param', {'name': 'playerKey'})['value']),
        }
        log('play_video got player_params: "%s"' % player_params)

        data = amf_request(**player_params)
        flv_url = data['FLVFullLengthURL']
        if flv_url.endswith('mp4'):
            log('play_video found plain mp4')
            return plugin.set_resolved_url(flv_url)
        else:
            re_app = re.compile('rtmp://.+?/(.+)')
            qualities = sorted(data['renditions'],
                               key=lambda k: k['frameWidth'],
                               reverse=True)
            best_quality = qualities[0]
            rtmp_url, playpath_full = best_quality['defaultURL'].split('&', 1)
            app = re_app.search(rtmp_url).group(1)
            clip = playpath_full.split('&')[0]
            app_full = '%s?%s' % (app, playpath_full.split('&', 1)[1])
            swf_url = ('http://admin.brightcove.com/viewer/'
                       'us20120810.1250/BrightcoveBootloader.swf')
            rtmp_params = {
                'rtmp_url': rtmp_url,
                'clip': clip,
                'app': app,
                'swf_url': swf_url,
                'playpath_full': playpath_full,
                'video_page_url': player_params['video_page_url'],
                'player_id': player_params['player_id'],
                'player_key': player_params['player_key'],
                'video_id': player_params['video_id'],
                'app_full': app_full,
            }

        def rtmpdump_output(rtmp_params):
            if 'brightcove' in rtmp_params['rtmp_url']:
                return (
                    'rtmpdump '
                    '--rtmp "%(rtmp_url)s" '
                    '--app "%(app)s?videoId=%(video_id)s&playerId=%(player_id)s" '
                    '--swfVfy "%(swf_url)s" '
                    '--pageUrl "%(video_page_url)s" '
                    '--conn "B:0" '
                    '--conn "S:%(playpath_full)s" '
                    '--playpath "%(clip)s" '
                    '-o test.flv'
                ) % rtmp_params
            else:
                return (
                    'rtmpdump '
                    '--rtmp "%(rtmp_url)s" '
                    '--app "%(app_full)s" '
                    '--swfUrl "%(swf_url)s" '
                    '--playpath "%(clip)s" '
                    '-o test.flv'
                ) % rtmp_params

        def xbmc_output(rtmp_params):
            if 'brightcove' in rtmp_params['rtmp_url']:
                return (
                    '%(rtmp_url)s '
                    'playpath=%(clip)s '
                    'tcUrl=%(rtmp_url)s '
                    'app=%(app)s '
                    'swfUrl=%(swf_url)s '
                    'pageUrl=%(video_page_url)s '
                    'conn=B:0 '
                    'conn=S:%(playpath_full)s '
                ) % rtmp_params
            else:
                return (
                    '%(rtmp_url)s '
                    'playpath=%(clip)s '
                    'app=%(app_full)s '
                    'swfUrl=%(swf_url)s '
                ) % rtmp_params

        if plugin._mode is 'xbmc':
            playback_url = xbmc_output(rtmp_params)
        else:
            playback_url = rtmpdump_output(rtmp_params)
        return plugin.set_resolved_url(playback_url)


def amf_request(video_page_url, player_id, player_key, video_id):
    video_page_url = 'http://c.brightcove.com/services/messagebroker/amf'
    service_id = 'com.brightcove.experience.ExperienceRuntimeFacade'

    if player_key:
        video_page_url += '?playerKey=%s' % player_key

    client = AMF.RemotingService(
        url=video_page_url,
        user_agent='',
        amf_version=3,
    )
    service = client.getService(service_id)

    class ContentOverride(object):
        def __init__(self, video_id=None):
            self.contentType = int(0)
            self.contentIds = None
            self.target = 'videoPlayer'
            self.contentId = int(video_id)
            self.featuredRefId = None
            self.contentRefIds = None
            self.featuredId = float('nan')
            self.contentRefId = None

    class ViewerExperienceRequest(object):
        def __init__(self, url=None, playerID=None,
                     playerKey=None, video_obj=None):
            self.experienceId = int(playerID)
            self.playerKey = playerKey
            self.contentOverrides = []
            self.contentOverrides.append(video_obj)
            self.TTLToken = ''
            self.URL = url
            self.deliveryType = float('nan')

    pyamf.register_class(
        ContentOverride,
        'com.brightcove.experience.ContentOverride',
    )
    pyamf.register_class(
        ViewerExperienceRequest,
        'com.brightcove.experience.ViewerExperienceRequest',
    )

    video_obj = ContentOverride(video_id)
    experience = ViewerExperienceRequest(
        video_page_url,
        player_id,
        player_key,
        video_obj,
    )
    result = service.getDataForExperience('', experience)
    log('amf_request debug: "%s"' % result)
    data = result['programmedContent']['videoPlayer']['mediaDTO']
    return data


def __get_tree(url, referer=None):
    html = __get_url(url, referer)
    tree = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    return tree


def __get_url(url, referer=None):
    log('__get_url opening url: %s' % url)
    req = Request(url)
    if referer:
        req.add_header('Referer', referer)
    req.add_header('Accept', ('text/html,application/xhtml+xml,'
                              'application/xml;q=0.9,*/*;q=0.8'))
    req.add_header('User-Agent', UA)
    html = urlopen(req).read()
    log('__get_url got %d bytes' % len(html))
    return html


def log(msg):
    xbmc.log(u'%s addon: %s' % (__ADDON_NAME__, msg))


if __name__ == '__main__':
    plugin.run()
