import time
import base64

import xbmcplugin

import util
import adobe_activate_api
from globals import defaultlive, defaultfanart, translation, pluginhandle
from addon_util import *
from menu_listing import *
from register_mode import RegisterMode

TAG = 'TVOS: '
PLACE = 'tvos'

HOME = 'HOME'
ANDROID_HOME = 'ANDROID_HOME'
SPORTS = 'SPORTS'
CHANNELS = 'CHANNELS'
BUCKET = 'BUCKET'
URL_MODE = 'URL_MODE'
URL = 'URL'



class TVOS(MenuListing):
    @RegisterMode(PLACE)
    def __init__(self):
        MenuListing.__init__(self, PLACE)

    @RegisterMode(ROOT)
    def root_menu(self, args):
        # TVOS home
        url = base64.b64decode(
            'aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2hvbWU=')
        self.parse_json(args, url)

        addDir(translation(30550), dict(MODE=self.make_mode(SPORTS)), defaultlive)
        addDir(translation(30560), dict(MODE=self.make_mode(CHANNELS)), defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(HOME)
    def home(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2hvbWU=')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(CHANNELS)
    def channels(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2NoYW5uZWxz')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(SPORTS)
    def sports(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL3Nwb3J0cw==')
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(URL_MODE)
    def url_mode(self, args):
        url = args.get(URL)[0]
        self.parse_json(args, url)
        xbmcplugin.endOfDirectory(pluginhandle)

    # Used on the main menu
    def list_live_content(self):
        url = base64.b64decode(
            'aHR0cDovL3dhdGNoLnByb2R1Y3QuYXBpLmVzcG4uY29tL2FwaS9wcm9kdWN0L3YxL3R2b3Mvd2F0Y2hlc3BuL2hvbWU=')
        json_data = util.get_url_as_json_cache(get_url(url))
        if 'buckets' in json_data['page']:
            buckets = json_data['page']['buckets']
            for bucket in buckets:
                if bucket['name'] == 'Live':
                    xbmc.log(TAG + 'Chose bucket %s' % bucket['id'])
                    bucket_arg = str(bucket['id']) + '/'
                    bucket_list = list()
                    bucket_list.append(bucket_arg)
                    self.parse_json(dict(BUCKET=bucket_list), url)

    def process_buckets(self, url, buckets, selected_buckets, current_bucket_path):
        selected_bucket = None if selected_buckets is None or len(selected_buckets) == 0 else selected_buckets[0]
        xbmc.log(TAG + 'Selected buckets: %s Current Path: %s' % (selected_buckets, current_bucket_path), xbmc.LOGDEBUG)
        original_bucket_path = current_bucket_path
        for bucket in buckets:
            current_bucket_path = list(original_bucket_path)
            current_bucket_path.append(str(bucket['id']))
            if selected_bucket is not None and str(bucket['id']) != selected_bucket:
                continue
            if ('contents' in bucket or 'buckets' in bucket) and selected_bucket is None and len(buckets) > 1:
                if bucket['type'] != 'images':
                    bucket_path = '/'.join(current_bucket_path)
                    addDir(bucket['name'],
                           dict(URL=url, MODE=self.make_mode(URL_MODE), BUCKET=bucket_path), defaultlive)
            else:
                if 'buckets' in bucket:
                    if selected_buckets is not None and len(selected_buckets) > 0:
                        self.process_buckets(url, bucket['buckets'], selected_buckets[1:], current_bucket_path)
                    else:
                        self.process_buckets(url, bucket['buckets'], list(), current_bucket_path)
                else:
                    if 'contents' in bucket:
                        bucket['contents'].sort(cmp=compare_tvos)
                        for content in bucket['contents']:
                            content_type = content['type']
                            if content_type == 'network' or content_type == 'subcategory' or content_type == 'category' or content_type == 'program':
                                content_url = content['links']['self']
                                if 'imageHref' in content:
                                    fanart = content['imageHref']
                                else:
                                    fanart = defaultfanart
                                addDir(content['name'], dict(URL=content_url, MODE=self.make_mode(URL_MODE)), fanart)
                            else:
                                self.index_content(content)
                                xbmcplugin.setContent(pluginhandle, 'episodes')

    def parse_json(self, args, url):
        xbmc.log(TAG + 'Looking at url %s %s' % (url, args), xbmc.LOGDEBUG)
        selected_bucket = args.get(BUCKET, None)
        if selected_bucket is not None:
            selected_bucket = selected_bucket[0].split('/')
            xbmc.log(TAG + 'Looking at bucket %s' % selected_bucket, xbmc.LOGDEBUG)
        json_data = util.get_url_as_json_cache(get_url(url))
        if 'buckets' in json_data['page']:
            buckets = json_data['page']['buckets']
            self.process_buckets(url, buckets, selected_bucket, list())

    def index_content(self, content):
        duration = 0
        if 'tracking' in content and 'duration' in content['tracking']:
            duration = int(content['tracking']['duration'])
        starttime = get_time(content)
        if 'date' in content and 'time' in content:
            description = content['date'] + ' ' + content['time']
            if 'tracking' in content:
                description += '\n' + content['tracking']['sport']
        else:
            description = ''
        networkId = ''
        networkName = ''
        if 'adobeRSS' in content:
            networkId = content['tracking']['network'] if 'network' in content['tracking'] else ''
            networkName = content['source']
        league = content['tracking']['league']
        index_item({
            'sport': content['tracking']['sport'],
            'eventName': content['name'] + ' (' + league + ')',
            'subcategory': content['subtitle'] if 'subtitle' in content else content['tracking']['sport'],
            'imageHref': content['imageHref'],
            'parentalRating': 'U',
            'starttime': starttime,
            'duration': duration,
            'type': content['status'] if 'status' in content else 'live',
            'networkId': networkId,
            'networkName': networkName,
            #TODO: Blackout check
            'blackout': False,
            'description': description,
            'eventId': content['id'],
            'sessionUrl': content['airings'][0]['videoHref'],
            'adobeRSS': content['adobeRSS'] if 'adobeRSS' in content else None
        })

def get_time(content):
    starttime = None
    if 'date' in content and 'time' in content:
        now_time = time.localtime(time.time())
        year = time.strftime('%Y', now_time)
        # Correct no zero padding in the time hours
        time_part = content['time']
        if time_part.find(':') == 1:
            time_part = '0' + time_part
        starttime = time.strptime(year + ' ' + content['date'] + ' ' + time_part, '%Y %A, %B %d %I:%M %p')
    return starttime

def compare_tvos(l, r):
    lnetwork = l['source'] if 'source' in l else None
    rnetwork = r['source'] if 'source' in r else None
    ltype = l['status'] if 'status' in l else 'clip'
    rtype = r['status'] if 'status' in r else 'clip'
    return compare(get_time(l), lnetwork, ltype, get_time(r), rnetwork, rtype)
