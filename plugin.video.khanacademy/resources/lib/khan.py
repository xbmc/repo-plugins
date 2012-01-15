try:
    import json
except ImportError:
    import simplejson as json
import time
import urllib


def api_url():
    '''Returns the API url with a timestamp url paremeter set to
    int(time.time() * 1000)
    '''
    return ('http://www.khanacademy.org/api/v1/playlists/library/compact?v=%d' %
            int(time.time() * 1000))


API_URL = api_url()


def download_playlists_json():
    '''Fetches the playlist JSON from the Khan Academy API and returns the
    parsed JSON object.
    '''
    conn = urllib.urlopen(API_URL)
    resp = json.load(conn)
    conn.close()
    return resp


class Video(object):

    def __init__(self, _json):
        self.key_id = _json['key_id']
        self.title = _json['title']
        self.readable_id = _json['readable_id']

    def to_listitem(self, plugin):
        '''Returns a dict suitable for passing to xbmcswift.plugin.add_items'''
        return {
            'label': self.title,
            'url': plugin.url_for('play_video', video_slug=self.readable_id),
            'is_playable': True,
            'is_folder': False,
        }


class Playlist(object):

    def __init__(self, _json):
        self.slugged_title = _json['slugged_title']
        self.title = _json['title']
        self.videos = [Video(item) for item in _json['videos']]

    def __iter__(self):
        return iter(self.videos)

    def to_listitem(self, plugin):
        '''Returns a dict suitable for passing to xbmcswift.plugin.add_items'''
        return {
            'label': self.title,
            'url': plugin.url_for('show_category', category=self.title),
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
