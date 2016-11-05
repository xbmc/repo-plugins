# -*- coding: utf-8 -*-
#
#  Copyright (c) 2014 Will Adams (izilly)
#  Distributed under the terms of the Modified BSD License.
#  The full license is in the file LICENSE.txt, distributed with this software.


import sys
import urlparse
import urllib
import urllib2
import json
import re
import os.path
import xbmcgui
import xbmcplugin
import xbmcaddon
from datetime import timedelta

#from pudb.remote import set_trace
#set_trace(term_size=(160, 60))

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.
_HANDLE = int(sys.argv[1])

API_ADDRESS = 'http://phish.in/api/v1'
PLUGIN_NAME = os.path.basename(_URL)
ADDON = xbmcaddon.Addon(PLUGIN_NAME)
FANART = ADDON.getAddonInfo('fanart')
ICON = ADDON.getAddonInfo('icon')
#THUMB = 'https://i.ytimg.com/vi/Kz9oqbpNDKk/maxresdefault.jpg'
THUMB = os.path.join(ADDON.getAddonInfo('path').decode('utf-8'), 'thumb.jpg')

URLOPENER = urllib2.build_opener()
URLOPENER.addheaders = [('Content-Type', 'application/json')]


def localize(string_id):
    return xbmcaddon.Addon().getLocalizedString(string_id).encode('utf-8')


class ListItem(object):
    def __init__(self, label,
                 url_params=None,
                 fanart=None,
                 thumb=None,
                 is_folder=True):
        self.label = label
        self.url_params = url_params
        self.fanart = fanart
        self.thumb = thumb
        self.is_folder = is_folder
        self.add_url()
        self.add_list_item()

    def add_url(self):
        url_parts = list(urlparse.urlparse(_URL))
        query = self.url_params
        url_parts[4] = urllib.urlencode(query)
        self.url = urlparse.urlunparse(url_parts)

    def add_list_item(self):
        li = xbmcgui.ListItem(label=self.label)
        # todo: use different method if possible, not setArt()
        #       (setArt() failed on my oldish xbmc box I tried)
        if self.thumb:
            #li.setThumbnailImage(self.thumb)
            li.setArt({'thumb': self.thumb})
            #li.setArt({'thumb': self.thumb})
        if self.fanart:
            li.setArt({'fanart': self.fanart})
            #li.setProperty('fanart_image', my_addon.getAddonInfo('fanart'))
            #li.setProperty('fanart_image', self.fanart)
        if not self.is_folder:
            li.setProperty('IsPlayable', 'true')
        self.list_item = li

    def get_dir_item(self):
        return (self.url, self.list_item, self.is_folder)

class ListItemTrack(ListItem):
    def add_url(self):
        params = u'item_type=track&path={0}'.format(self.url_params['path'])
        print(_URL)
        self.url = u'{0}?{1}'.format(_URL, params)

class Resp(object):
    def __init__(self, data):
        self.data = data
        self.label = self.get_label()
        self.url_params = self.get_url_params()
        self.fanart, self.thumb = self.get_art()
        self.is_folder = self.get_is_folder()

    def get_art(self):
        return FANART, THUMB

    def get_is_folder(self):
        return True

    def get_dir_item(self):
        li = ListItem(self.label,
                      self.url_params,
                      self.fanart,
                      self.thumb,
                      self.is_folder)
        return li.get_dir_item()

class RespYear(Resp):
    def get_label(self):
        return self.data

    def get_url_params(self):
        return {'endpoint': 'years',
                'endpoint_arg': self.data,
                'item_type': 'year'}

class RespShow(Resp):
    def get_label(self):
        venue = self.data['venue']
        venue_name = venue['name']
        venue_loc = venue['location']
        venue_text = u'{0}, {1}'.format(venue_name, venue_loc)
        date = self.data['date']
        sbd = self.data['sbd']
        label = u'{0} {1}'.format(date, venue_text)
        if sbd:
            label = u'{0} (sbd)'.format(label)
        return label

    def get_url_params(self):
        arg = self.data['id']
        return {'endpoint': 'shows',
                'endpoint_arg': arg,
                'item_type': 'show'}

class RespShowBasic(Resp):
    def get_label(self):
        venue_text = self.data['venue_name']
        date = self.data['date']
        sbd = self.data['sbd']
        label = u'{0} {1}'.format(date, venue_text)
        if sbd:
            label = u'{0} (sbd)'.format(label)
        return label

    def get_url_params(self):
        arg = self.data['id']
        return {'endpoint': 'shows',
                'endpoint_arg': arg,
                'item_type': 'show'}

class RespTrack(Resp):
    def get_label(self):
        self.get_info()
        return '{0:02d}. {1}'.format(self.num, self.title)

    def get_info(self):
        self.title = self.data['title']
        self.album = self.data.get('album')
        self.artist = self.data.get('artist')
        if not self.artist:
            self.artist = 'Phish'
        self.set_num = self.data.get('set')
        self.num = self.data.get('position')
        if self.num:
            self.num = int(self.num)
        self.duration = self.data.get('duration')
        if self.duration:
            self.duration = int(self.duration/1000)
        self.genre = 'Rock'

    def add_info(self):
        # this doesn't work anymore on my system:
        #info = {'title': self.title,
                #'tracknumber': self.num,
                #'duration': self.duration,
                #'album': self.album,
                #'artist': self.artist,
                #'genre': self.genre,}
        #self.li.list_item.setInfo('music', info)

        # this works fine:
        self.li.list_item.setInfo('music', {'title': self.title})
        self.li.list_item.setInfo('music', {'tracknumber': self.num})
        self.li.list_item.setInfo('music', {'duration': self.duration})
        self.li.list_item.setInfo('music', {'album': self.album})
        self.li.list_item.setInfo('music', {'artist': self.artist})
        self.li.list_item.setInfo('music', {'genre': self.genre})

    def get_duration(self, milliseconds):
        td = timedelta(milliseconds=milliseconds)
        h,m,s = td.__str__().split(':')



    def get_url_params(self):
        return {'item_type': 'track',
                'path': self.data['mp3']}

    def get_is_folder(self):
        return False

    def get_dir_item(self):
        self.li = ListItem(self.label,
                      self.url_params,
                      self.fanart,
                      self.thumb,
                      self.is_folder)
        self.add_info()
        return self.li.get_dir_item()


def handle_years(params):
    endpoint = params.get('endpoint')
    resp = get_api_resp(endpoint)
    years = resp['data']
    list_items = []
    for y in years:
        r = RespYear(y)
        di = r.get_dir_item()
        list_items.append(di)
    xbmcplugin.addDirectoryItems(_HANDLE, list_items, len(list_items))
    xbmcplugin.addSortMethod(_HANDLE,
                             xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_HANDLE)

def handle_random(params):
    endpoint = params.get('endpoint')
    resp = get_api_resp(endpoint)
    show = resp['data']
    list_items = []
    r = RespShow(show)
    di = r.get_dir_item()
    list_items.append(di)
    xbmcplugin.addDirectoryItems(_HANDLE, list_items, len(list_items))
    xbmcplugin.addSortMethod(_HANDLE,
                             xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_HANDLE)

def handle_year(params):
    endpoint = params.get('endpoint')
    endpoint_arg = params.get('endpoint_arg')
    resp = get_api_resp(endpoint, endpoint_arg)
    shows = resp['data']
    list_items = []
    for s in shows:
        r = RespShowBasic(s)
        di = r.get_dir_item()
        list_items.append(di)
    xbmcplugin.addDirectoryItems(_HANDLE, list_items, len(list_items))
    xbmcplugin.addSortMethod(_HANDLE,
                             xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_HANDLE)

def handle_show(params):
    endpoint = params.get('endpoint')
    endpoint_arg = params.get('endpoint_arg')
    resp = get_api_resp(endpoint, endpoint_arg)
    show = resp['data']
    showdate = show['date']
    venue = show['venue']['name']
    city = show['venue']['location']
    album = '{0} {1}, {2}'.format(showdate, venue, city)
    tracks = show['tracks']
    list_items = []
    for t in tracks:
        t['album'] = album
        r = RespTrack(t)
        di = r.get_dir_item()
        list_items.append(di)
    xbmcplugin.addDirectoryItems(_HANDLE, list_items, len(list_items))
    xbmcplugin.setContent(_HANDLE, 'songs')
    xbmcplugin.addSortMethod(_HANDLE,
                             xbmcplugin.SORT_METHOD_TRACKNUM)
    xbmcplugin.endOfDirectory(_HANDLE)

def handle_track(params):
    """
    Play an item

    Args:
        params: dict (params['path'] is the path to play)

    Returns:
        None
    """
    # todo inspect params['path'] to see what a value looks like.
    # Create a playable item with a path to play.
    list_item = xbmcgui.ListItem(path=params['path'])
    xbmcplugin.setContent(_HANDLE, 'songs')
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=list_item)


def add_categories():
    categories = []
    categories.append(add_year_cat())
    categories.append(add_random_cat())
    xbmcplugin.addDirectoryItems(_HANDLE, categories, len(categories))
    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_NONE)
    xbmcplugin.endOfDirectory(_HANDLE)

def add_year_cat():
    label = localize(30001)
    url_params = {'endpoint': 'years',
                  'item_type': 'years'}
    li = ListItem(label,
                  url_params)
    di = li.get_dir_item()
    return di

def add_random_cat():
    label = localize(30005)
    url_params = {'endpoint': 'random-show',
                  'item_type': 'random-show'}
    li = ListItem(label,
                  url_params)
    di = li.get_dir_item()
    return di

def router(paramstring):
    """
    Call the appropriate function for the given paramstring.

    Args:
        paramstring: query string passed to the add-on

    Returns:
        None
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(urlparse.parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        if params.get('content_type') and len(params) == 1:
            add_categories()
            return True
        it = params.get('item_type')
        if it == 'years':
            handle_years(params)
        elif it == 'random-show':
            handle_random(params)
        elif it == 'year':
            handle_year(params)
        elif it == 'show':
            handle_show(params)
        elif it == 'track':
            handle_track(params)
        #elif params['action'] == 'listing':
            ## Display the list of items in a given category.
            #list_items(params['category'])
        elif params['action'] == 'play':
            # Play item from a provided URL.
            play_item(params['item'])
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of categories
        add_categories()

def urljoin(parts):
    joined = '/'.join(s.strip('/') for s in parts)
    return joined

def build_url(endpoint_name, *args, **kwargs):
    url = urljoin([API_ADDRESS] + [endpoint_name] + list(args))
    if kwargs:
        url_parts = list(urlparse.urlparse(url))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        query.update(kwargs)
        url_parts[4] = urllib.urlencode(query)
        url = urlparse.urlunparse(url_parts)
    return url

def get_api_resp(endpoint_name, *args, **kwargs):
    url = build_url(endpoint_name, *args, **kwargs)
    resp = URLOPENER.open(url)
    resp = json.loads(resp.read())
    return resp


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])

