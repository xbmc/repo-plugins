import time
import base64

import xbmcplugin

import util
import adobe_activate_api
from globals import defaultlive, defaultfanart, translation, pluginhandle
from addon_util import *
from menu_listing import *
from register_mode import RegisterMode


TAG = 'ROKU: '
PLACE = 'roku'
URL_MODE = 'URL_MODE'
URL = 'URL'
ID = 'ID'

MIN_THUMBNAIL_WIDTH = 500


class Roku(MenuListing):
    @RegisterMode(PLACE)
    def __init__(self):
        MenuListing.__init__(self, PLACE)

    @RegisterMode(ROOT)
    def root_menu(self, args):
        # Roku config
        url = base64.b64decode(
            'aHR0cDovL2Fzc2V0cy5lc3BuLmdvLmNvbS9wcm9kL2Fzc2V0cy93YXRjaGVzcG4vcm9rdS9jb25maWcuanNvbg==')
        json_data = util.get_url_as_json_cache(get_url(url))
        for group in json_data['config']['featured']['groups']:
            if group['visibility'] == 'not authenticated':
                # This represents the duplicate Browse by Sport
                continue
            extra = ''
            if group['visibility'] == 'authenticated':
                if not adobe_activate_api.is_authenticated():
                    extra = '*'
            if len(group['contents']) > 1:
                extra += group['name'] + ' - '
            for content in group['contents']:
                addDir(extra + content['name'],
                       dict(URL=content['href'], MODE=self.make_mode(URL_MODE)), defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    def get_thumbnail(self, category):
        max_width = 0
        href = ''
        key = 'thumbnails'
        if 'thumbnails' not in category:
            key = 'images'
        if key in category:
            for thumbnail_key in category[key]:
                thumbnail = category[key][thumbnail_key]
                if 'slates' == thumbnail_key:
                    return thumbnail['large']['href']
                width = thumbnail['width']
                if width >= MIN_THUMBNAIL_WIDTH:
                    return thumbnail['href']
                elif width > max_width:
                    max_width = width
                    href = thumbnail['href']
        return href

    @RegisterMode(URL_MODE)
    def url_mode(self, args):
        url = args.get(URL)[0]
        category_id = args.get(ID)
        if category_id:
            category_id = category_id[0]
        json_data = util.get_url_as_json_cache(get_url(url))
        if 'listings' in json_data:
            json_data['listings'].sort(cmp=compare_roku)
            for listing in json_data['listings']:
                index_listing(listing)
            xbmcplugin.setContent(pluginhandle, 'episodes')
        if 'videos' in json_data:
            for video in json_data['videos']:
                index_video(video)
            xbmcplugin.setContent(pluginhandle, 'episodes')
        if 'categories' in json_data:
            for category in json_data['categories']:
                if category_id is None:
                    if 'api' in category['links'] and 'subcategories' not in category:
                        addDir(category['name'],
                               dict(URL=category['links']['api']['video']['href'], MODE=self.make_mode(URL_MODE)),
                               self.get_thumbnail(category))
                    elif 'subcategories' in category:
                        # Collapse sub categories
                        for subcategory in category['subcategories']:
                            if 'api' in subcategory['links']:
                                addDir(category['name'] + ' - ' + subcategory['name'],
                                       dict(URL=subcategory['links']['api']['video']['href'],
                                            MODE=self.make_mode(URL_MODE)),
                                       self.get_thumbnail(category))
                elif category_id == str(category['id']):
                    if 'api' in category['links']:
                        addDir(category['name'] + ' - Clips',
                               dict(URL=category['links']['api']['video']['href'], MODE=self.make_mode(URL_MODE)),
                               self.get_thumbnail(category))
                    if 'subcategories' in category:
                        for subcategory in category['subcategories']:
                            if 'api' in subcategory['links']:
                                addDir(subcategory['name'],
                                       dict(URL=subcategory['links']['api']['video']['href'],
                                            MODE=self.make_mode(URL_MODE)),
                                       self.get_thumbnail(category))
        if 'clients' in json_data:
            for client in json_data['clients']:
                for channel in client['channels']:
                    addDir(channel['name'],
                           dict(URL=channel['links']['api']['listings']['href'], MODE=self.make_mode(URL_MODE)),
                           self.get_thumbnail(channel))
        xbmcplugin.endOfDirectory(pluginhandle)


def get_time(listing):
    if 'startTime' in listing:
        time_format = '%Y-%m-%dT%H:%M:%S'
        return time.strptime(listing['startTime'][:-3], time_format)
    return None


def compare_roku(l, r):
    lnetwork = l['broadcasts'][0]['name'] if 'broadcasts' in l else None
    rnetwork = r['broadcasts'][0]['name'] if 'broadcasts' in r else None
    ltype = l['type']
    rtype = r['type']
    return compare(get_time(l), lnetwork, ltype, get_time(r), rnetwork, rtype)
