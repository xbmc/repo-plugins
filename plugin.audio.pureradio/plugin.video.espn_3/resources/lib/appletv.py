import json
import re
import time

import xbmcplugin
import xml.etree.ElementTree as ET

import util
import player_config
import adobe_activate_api
from globals import selfAddon, defaultlive, defaultreplay, defaultupcoming, \
    defaultimage, defaultfanart, translation, pluginhandle
from addon_util import *
from menu_listing import *
from register_mode import RegisterMode

TAG = 'AppleTV: '
PLACE = 'appletv'
FEATURED = 'featured'
CATEGORY_SHOWCASE_MODE = 'CATEGORY_SHOWCASE'
CATEGORY_SHELF_MODE = 'CATEGORY_SHELF'
CATEGORY_SPORTS_MODE = 'CATEGORY_SPORTS'
CATEGORY_CHANNELS_MODE = 'CATEGORY_CHANNELS'

class AppleTV(MenuListing):
    @RegisterMode(PLACE)
    def __init__(self):
        MenuListing.__init__(self, PLACE)

    @RegisterMode(ROOT)
    def root_menu(self, args):
        self.trending_mode(args)
        addDir(translation(30680),
               dict(MODE=self.make_mode(FEATURED)),
               defaultlive)
        addDir(translation(30550),
               dict(MODE=self.make_mode(CATEGORY_SPORTS_MODE)),
               defaultlive)
        addDir(translation(30560),
               dict(MODE=self.make_mode(CATEGORY_CHANNELS_MODE)),
               defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(FEATURED)
    def featured_menu(self, args):
        featured_url = base64.b64decode('aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L2ZlYXR1cmVk')
        et = util.get_url_as_xml_soup_cache(get_url(featured_url))
        for showcase in et.findall('.//showcase/items/showcasePoster'):
            name = showcase.get('accessibilityLabel')
            image = showcase.find('./image').get('src')
            url = util.parse_url_from_method(showcase.get('onPlay'))
            addDir(name,
                   dict(SHOWCASE_URL=url, MODE=self.make_mode(CATEGORY_SHOWCASE_MODE)),
                   image, image)
        collections = et.findall('.//collectionDivider')
        shelfs = et.findall('.//shelf')
        for i in range(0, len(collections)):
            collection_divider = collections[i]
            shelf = shelfs[i]
            title = collection_divider.find('title').text
            name = shelf.get('id')
            addDir(title,
                   dict(SHELF_ID=name, MODE=self.make_mode(CATEGORY_SHELF_MODE)),
                   defaultlive)
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(CATEGORY_SHOWCASE_MODE)
    def categories_showcase(self, args):
        url = args.get(SHOWCASE_URL)[0]
        selected_nav_id = args.get(SHOWCASE_NAV_ID, None)
        et = util.get_url_as_xml_soup_cache(get_url(url))
        navigation_items = et.findall('.//navigation/navigationItem')
        xbmc.log('ESPN3 Found %s items' % len(navigation_items), xbmc.LOGDEBUG)
        if selected_nav_id is None and len(navigation_items) > 0:
            for navigation_item in navigation_items:
                name = navigation_item.find('./title').text
                nav_id = navigation_item.get('id')
                menu_item = navigation_item.find('.//twoLineMenuItem')
                if menu_item is None:
                    menu_item = navigation_item.find('.//twoLineEnhancedMenuItem')
                if menu_item is not None and not menu_item.get('id') == 'no-event':
                    addDir(name,
                           dict(SHOWCASE_URL=url, SHOWCASE_NAV_ID=nav_id, MODE=self.make_mode(CATEGORY_SHOWCASE_MODE)), defaultfanart)
        elif len(navigation_items) > 0:
            for navigation_item in navigation_items:
                if navigation_item.get('id') == selected_nav_id[0]:
                    xbmc.log('ESPN3 Found nav item %s' % selected_nav_id[0], xbmc.LOGDEBUG)
                    self.process_item_list(navigation_item.findall('.//twoLineMenuItem'))
                    self.process_item_list(navigation_item.findall('.//twoLineEnhancedMenuItem'))
                    xbmcplugin.setContent(pluginhandle, 'episodes')
        else: # If there are no navigation items then just dump all of the menu entries
            xbmc.log('ESPN3: Dumping all menu items', xbmc.LOGDEBUG)
            self.process_item_list(et.findall('.//twoLineMenuItem'))
            self.process_item_list(et.findall('.//twoLineEnhancedMenuItem'))
            xbmcplugin.setContent(pluginhandle, 'episodes')
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(CATEGORY_SHELF_MODE)
    def category_shelf(self, args):
        featured_url = base64.b64decode('aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L2ZlYXR1cmVk')
        et = util.get_url_as_xml_soup_cache(get_url(featured_url))
        for shelf in et.findall('.//shelf'):
            name = shelf.get('id')
            if name == args.get(SHELF_ID)[0]:
                self.process_item_list(shelf.findall('.//sixteenByNinePoster'))
        xbmcplugin.setContent(pluginhandle, 'episodes')
        xbmcplugin.endOfDirectory(pluginhandle)

    @RegisterMode(CATEGORY_SPORTS_MODE)
    def category_sports(self, args):
        sports_url = base64.b64decode('aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L3Nwb3J0cw==')
        et = util.get_url_as_xml_soup_cache(get_url(sports_url))
        images = et.findall('.//image')
        sports = et.findall('.//oneLineMenuItem')
        for i in range(0, min(len(images), len(sports))):
            sport = sports[i]
            image = images[i]
            name = sport.get('accessibilityLabel')
            image = image.text
            url = util.parse_url_from_method(sport.get('onSelect'))
            addDir(name,
                   dict(SHOWCASE_URL=url, MODE=self.make_mode(CATEGORY_SHOWCASE_MODE)),
                   image, image)
        xbmcplugin.endOfDirectory(pluginhandle, updateListing=False)

    @RegisterMode(CATEGORY_CHANNELS_MODE)
    def category_channels(self, args):
        channels_url = base64.b64decode('aHR0cDovL2VzcG4uZ28uY29tL3dhdGNoZXNwbi9hcHBsZXR2L2NoYW5uZWxz')
        et = util.get_url_as_xml_soup_cache(get_url(channels_url))
        for channel in et.findall('.//oneLineMenuItem'):
            name = channel.get('accessibilityLabel')
            image = channel.find('.//image').text
            url = util.parse_url_from_method(channel.get('onSelect'))
            addDir(name,
                   dict(SHOWCASE_URL=url, MODE=self.make_mode(CATEGORY_SHOWCASE_MODE)),
                   image, image)
        xbmcplugin.setContent(pluginhandle, 'episodes')
        xbmcplugin.endOfDirectory(pluginhandle, updateListing=False)

    def trending_mode(self, args):
        url = base64.b64decode('aHR0cDovL3dhdGNoLmFwaS5lc3BuLmNvbS92MS90cmVuZGluZw==')
        json_data = util.get_url_as_json_cache(get_url(url))
        for listing in json_data['listings']:
            index_listing(listing)
        for video in json_data['videos']:
            index_video(video)

    # Items can play as is and do not need authentication
    def index_item_shelf(self, stash_json):
        description = stash_json['description']
        item = stash_json['internal_item']
        description = description + '\n\n' + self.get_metadata(item)

        index_item({
            'sport': stash_json['sportName'],
            'eventName': stash_json['name'],
            'imageHref': stash_json['imageHref'],
            'duration': int(stash_json['duration']),
            'description': description,
            'sessionUrl': stash_json['playbackUrl'],
            'type': 'live'
        })

    def index_tv_shelf(self, stash_json, upcoming):
        if 'description' in stash_json:
            description = stash_json['description']
        else:
            description = ''
        item = stash_json['internal_item']
        description = description + '\n\n' + self.get_metadata(item)

        index_item({
            'sport': stash_json['categoryName'],
            'eventName': stash_json['name'],
            'subcategory': stash_json['subcategoryName'],
            'imageHref':stash_json['imageHref'],
            'parentalRating':stash_json['parentalRating'],
            'starttime' : time.localtime(int(stash_json['startTime']) / 1000),
            'duration': int(stash_json['duration']),
            'type' : stash_json['type'],
            'networkId' : stash_json['network'],
            'blackout' : self.check_blackout(item),
            'description' : description,
            'eventId' : stash_json['eventId'],
            'sessionUrl': stash_json['sessionUrl'],
            'guid': stash_json['guid'],
            'channelResourceId': stash_json['channelResourceId']
        })

    def process_item_list(self, item_list):
        stashes = list()
        for item in item_list:
            stash_element = item.find('./stash/json')
            if item.get('id').startswith('loadMore'):
                method_info = util.parse_method_call(item.get('onSelect'))
                if method_info[0] == 'espn.page.loadMore':
                    label = item.find('./label')
                    label2 = item.find('./label2')
                    menu_label = ''
                    if label is not None:
                        menu_label = label.text
                    if label2 is not None:
                        menu_label = menu_label + ' ' + label2.text
                    if label is None and label2 is None:
                        menu_label = translation(30570)
                    url = method_info[3]
                    nav_id = method_info[2]
                    url = url + '&navigationItemId=' + nav_id
                    xbmc.log(TAG + 'Load more url %s' % url, xbmc.LOGDEBUG)
                    addDir(menu_label,
                           dict(SHOWCASE_URL=url, MODE=self.make_mode(CATEGORY_SHOWCASE_MODE)),
                           defaultimage)
            elif not item.get('id') == 'no-event':
                if stash_element is None:
                    # Assume goes to another onPlay with a url
                    name = item.get('accessibilityLabel')
                    image = item.find('./image').get('src')
                    url = util.parse_url_from_method(item.get('onPlay'))
                    addDir(name,
                           dict(SHOWCASE_URL=url, MODE=self.make_mode(CATEGORY_SHOWCASE_MODE)),
                           image, image)
                else:
                    stash = stash_element.text.encode('utf-8')
                    # Some of the json is baddly formatted
                    stash = re.sub(r'\s+"', '"', stash)
                    stash_json = json.loads(stash, 'utf-8')
                    stash_json['internal_item'] = item
                    stashes.append(stash_json)

        xbmc.log(TAG + ' sorting %s items' % len(stashes), xbmc.LOGDEBUG)
        stashes.sort(cmp=compare_appletv)
        for stash_json in stashes:
            if stash_json['type'] == 'upcoming':
                self.index_tv_shelf(stash_json, True)
            elif 'sessionUrl' in stash_json:
                self.index_tv_shelf(stash_json, False)
            else:
                self.index_item_shelf(stash_json)

    def get_metadata(self, item):
        metadataKeysElement = item.find('.//metadataKeys')
        metadataValuesElement = item.find('.//metadataValues')
        description = ''
        if metadataKeysElement is not None and metadataValuesElement is not None:
            keyLabels = metadataKeysElement.findall('.//label')
            valueLabels = metadataValuesElement.findall('.//label')
            for i in range(0, min(len(keyLabels), len(valueLabels))):
                if valueLabels[i].text is not None:
                    description += '%s: %s\n' % (keyLabels[i].text, valueLabels[i].text)
        return description

    def check_blackout(self, item):
        xbmc.log(TAG + 'check blackout %s' % ET.tostring(item), xbmc.LOGDEBUG)
        blackouts = item.findall('.//blackouts/blackoutsItem/detail/detailItem')
        xbmc.log(TAG + '%s' % blackouts, xbmc.LOGDEBUG)
        blackout_type = item.find('.//blackouts/blackoutsItem/type')
        if blackout_type is not None and not blackout_type.text == 'dma':
            return False
        user_dma = player_config.get_dma()
        if blackouts is not None:
            for blackout in blackouts:
                if blackout.text == user_dma:
                    return True
        return False

def get_time(listing):
    return time.localtime(int(listing['startTime']) / 1000) if 'startTime' in listing else None

def compare_appletv(l, r):
    lnetwork = l['network'] if 'network' in l else None
    rnetwork = r['network'] if 'network' in r else None
    ltype = l['type'] if 'type' in l else 'clip'
    rtype = r['type'] if 'type' in r else 'clip'
    return compare(get_time(l), lnetwork, ltype, get_time(r), rnetwork, rtype)
