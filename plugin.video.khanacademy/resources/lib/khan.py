try:
    import json
except ImportError:
    import simplejson as json
import time
import urllib


# Hierarchical list
API_URL = 'http://www.khanacademy.org/api/v1/playlists/library'
YOUTUBE_PLUGIN_PTN = 'plugin://plugin.video.youtube/?action=play_video&videoid=%s'


def download_playlists_json():
    '''Fetches the playlist JSON from the Khan Academy API and returns the
    parsed JSON object.
    '''
    conn = urllib.urlopen(API_URL)
    resp = json.load(conn)
    conn.close()
    return resp


def _try_parse(_json, *args):
    '''Returns the parsed value or None if doesn't exist. The provided args
    correspond to dictionary keys.

    >>> _json = {'foo': {'bar': 'baz'}}
    >>> _try_parse(_json, 'foo', 'bar')
    baz
    >>> _try_parse(_json, 'foo', 'missingkey')
    None
    '''
    try:
        for key in args:
            _json = _json[key]
        return _json
    except TypeError:
        return None


class Video(object):

    def __init__(self, _json):
        #self.key_id = _json['key_id']
        self.title = _json['title']
        self.readable_id = _json['readable_id']
        self.youtube_url = YOUTUBE_PLUGIN_PTN % _json['youtube_id']
        self.mp4_url = _try_parse(_json, 'download_urls', 'mp4')
        self.thumbnail = _try_parse(_json, 'download_urls', 'png')


    def to_listitem(self, plugin):
        '''Returns a dict suitable for passing to xbmcswift.plugin.add_items'''
        item = {
            'label': self.title,
            'url': self.mp4_url or self.youtube_url,
            'is_playable': True,
            'is_folder': False,
        }
        if self.thumbnail:
            item['thumbnail'] = self.thumbnail
        return item


class Playlist(object):

    def __init__(self, _json):
        self.title = _json['title']
        self.description = _json['description']
        self.videos = [Video(item) for item in _json['videos']]

    def __iter__(self):
        return iter(self.videos)

    def to_listitem(self, plugin):
        '''Returns a dict suitable for passing to xbmcswift.plugin.add_items'''
        return {
            'label': self.title,
            'url': plugin.url_for('show_category', category=self.title),
            'info': {'plot': self.description},
        }


class Category(object):

    def __init__(self, _json):
        self.name = _json['name']

    def to_listitem(self, plugin):
        '''Returns a dict suitable for passing to xbmcswift.plugin.add_items'''
        return {
            'label': self.name,
            'url': plugin.url_for('show_category', category=self.name),
        }


class KhanData(object):
    '''This class repurposes the Khan Academy playlist JSON into more
    convenient data structures.
    '''

    def __init__(self, _json):
        self._items = {}
        self._parse(_json, '_root')

    def _is_playlist(self, item):
        return 'playlist' in item.keys()

    def _create_keys(self, key):
        if key not in self._items.keys():
            self._items[key] = []

    def _parse(self, _json, current_key):
        '''Recursive parsing function to format the _json input in a single
        dict keyable on item['name']
        '''
        self._create_keys(current_key)

        for item in _json:
            if self._is_playlist(item):
                playlist = Playlist(item['playlist'])
                self._items[current_key].append(playlist)
                self._items[item['name']] = playlist
            else:
                category = Category(item)
                self._items[current_key].append(category)
                self._parse(item['items'], item['name'])

    def get_items(self, key):
        '''For a given key, returns a list of items (Category or Playlist) or
        if the key is a playlist name, returns a Playlist object.
        '''
        return self._items[key]
