import sys, re, os
import xbmc
import xbmcgui
from urllib.parse import urlencode

class ListItems:
    INDIGITUBE_ACCESS_KEY            = 'access_token=%242a%2410%24x2Zy%2FTgIAOC0UUMi3NPKc.KY49e%2FZLUJFOpBCNYAs8D72UUnlI526'
    INDIGITUBE_ALBUM_URL             = 'https://api.appbooks.com/content/album/{}?' + INDIGITUBE_ACCESS_KEY
    INDIGITUBE_TRACK_URL             = 'https://api.appbooks.com/get/{}?' + INDIGITUBE_ACCESS_KEY
    INDIGITUBE_VIDEO_URL             = 'https://api.appbooks.com/get/{}?variant=720&' + INDIGITUBE_ACCESS_KEY
    INDIGITUBE_ALBUM_ART_URL         = 'https://api.appbooks.com/get/{}/file/file.jpg?w={}&quality=90&' + INDIGITUBE_ACCESS_KEY + '&ext=.jpg'
    QUERY_RADIO = '5b5ac73df6b4d90e6deeabd1'
    NOWHERE = 'plugin://plugin.audio.indigitube/?mode=explicit'

    def __init__(self, addon):
        self.matrix = '19.' in xbmc.getInfoLabel('System.BuildVersion')
        self.addon = addon
        self.allow_explicit = self.addon.getSettingBool('allow_explicit')
        self.allow_deceased = self.addon.getSettingBool('allow_deceased')
        self._respath = os.path.join(self.addon.getAddonInfo('path'), 'resources')
        self.fanart = os.path.join(self._respath, 'fanart.jpg')
        quality = self.addon.getSetting('image_quality')
        self.quality = int(quality) if quality else 1

    def _album_quality(self):
        if self.quality == 0:
            return '700'
        if self.quality == 1:
            return '350'
        if self.quality == 2:
            return '200'

    def _build_url(self, query):
        base_url = sys.argv[0]
        return base_url + '?' + urlencode(query)

    def get_item(self, item_json, args={}):
       definition = item_json.get('definition', item_json.get('file', {}).get('definition'))
       if definition == 'radioStation':
           return self.get_radio_station_item(item_json)
       elif definition == 'channel':
           if item_json.get('_id') == self.QUERY_RADIO:
               return self.get_channel_item(item_json, query=True)
           else:
               return self.get_channel_item(item_json)
       elif definition == 'audioContent':
           return self.get_track_item(item_json, args)
       elif definition == 'videoContent':
           return self.get_video_item(item_json)
       elif definition == 'album':
           return self.get_album_item(item_json)

    def get_radio_station_item(self, item_json):
        item_data = item_json.get('data', {})
        title     = item_json.get('title', '')
        if not self.allow_deceased:
            if item_data.get('deceasedContent', 'no') != "no":
                return
        artist    = item_json.get('realms', [{}])[0].get('title')
        url       = item_data.get('feedSource')
        desc      = item_data.get('description')
        textbody  = re.compile(r'<[^>]+>').sub('', desc)
        art_id    = item_data.get('coverImage', '')
        if not isinstance(art_id, str):
            art_id = art_id.get('_id')
        art_url  = self.INDIGITUBE_ALBUM_ART_URL.format(art_id, self._album_quality())

        if item_data.get('explicit'):
            title += ' (Explicit)'
            if not self.allow_explicit:
                url = self.NOWHERE
        if artist:
            title = title + ' - ' + artist
        li = xbmcgui.ListItem(label=title, offscreen=True)
        if not self.matrix:
            vi = li.getVideoInfoTag()
            vi.setTitle(title)
            vi.setPlot(textbody)
        else: # Matrix v19.0
            vi = {
                'title':     title,
                'plot':      textbody,
            }
            li.setInfo('video', vi)
        li.setArt({'thumb': art_url, 'fanart': self.fanart})
        li.setProperty('IsPlayable', 'true')
        li.setPath(url)
        return (url, li, False)

    def get_channel_item(self, item_json, query=False):
        item_data = item_json.get('data', {})
        title     = item_json.get('title', '')
        if not self.allow_deceased:
            if item_data.get('deceasedContent', 'no') != "no":
                return
        if query:
            mode    = 'list_query'
            key_id  = 'query_id'
            item_id = item_json.get('data', {}).get('query')
        else:
            mode    = 'list_channel'
            key_id  = 'channel_id'
            item_id = item_json.get('_id')
        desc      = item_data.get('description', '')
        textbody  = re.compile(r'<[^>]+>').sub('', desc)
        url       = self._build_url({'mode': mode, key_id: item_id})

        if item_data.get('allExplicit'):
            title += ' (Explicit)'
            if not self.allow_explicit:
                url = self.NOWHERE
        li = xbmcgui.ListItem(label=title, offscreen=True)
        if not self.matrix:
            vi = li.getVideoInfoTag()
            vi.setTitle(title)
            vi.setPlot(textbody)
        else: # Matrix v19.0
            vi = {
                'title':     title,
                'plot':      textbody,
            }
            li.setInfo('video', vi)
        li.setArt({'fanart': self.fanart})
        li.setPath(url)
        return (url, li, True)

    def get_album_item(self, item_json):
        item_data = item_json.get('data', {})
        if not self.allow_deceased:
            if item_data.get('deceasedContent', 'no') != "no":
                return
        title     = item_json.get('title', '')
        artist    = item_data.get('artist', '')
        desc      = item_data.get('description', '')
        textbody  = re.compile(r'<[^>]+>').sub('', desc)
        art_id    = item_data.get('coverImage', '')
        if not isinstance(art_id, str):
            art_id = art_id.get('_id')
        art_url = self.INDIGITUBE_ALBUM_ART_URL.format(art_id, self._album_quality())

        if item_data.get('allExplicit') or item_data.get('explicit'):
            title += ' (Explicit)'
        if artist:
            title = title + ' - ' + artist
        folder = False

        if len(item_data.get('items', [])) > 1:
            url = self._build_url({'mode': 'list_songs', 'album_id': item_json.get('_id')})

            folder = True
            if item_data.get('allExplicit'):
                if not self.allow_explicit:
                    folder = False
                    url = self.NOWHERE
            li = xbmcgui.ListItem(label=title, offscreen=True)
        else:
            item = item_data.get('items', [])[0]
            file = item.get('file', '')
            if not isinstance(file, str):
                file = file.get('_id')
            url = self.INDIGITUBE_TRACK_URL.format(file)
            
            li = xbmcgui.ListItem(label=title, offscreen=True)
            li.setProperty('IsPlayable', 'true')
            if item_data.get('explicit'):
                if not self.allow_explicit:
                    li.setProperty('IsPlayable', 'false')
                    url = self.NOWHERE

        li.setArt({'thumb': art_url, 'fanart': self.fanart})
        if not self.matrix:
            vi = li.getVideoInfoTag()
            vi.setTitle(title)
            vi.setPlot(textbody)
        else: # Matrix v19.0
            vi = {
                'title':     title,
                'plot':      textbody,
            }
            li.setInfo('video', vi)
        li.setPath(url)
        return (url, li, folder)

    def get_track_item(self, item_json, args):
        title   = item_json.get('title', '')
        artist  = item_json.get('artist', '')
        file = item_json.get('file', '')
        if not isinstance(file, str):
            file = file.get('_id')
        url = self.INDIGITUBE_TRACK_URL.format(file)

        if item_json.get('explicit'):
            title += ' (Explicit)'
            if not self.allow_explicit:
                url = self.NOWHERE
        li = xbmcgui.ListItem(label=title, offscreen=True)
        # if not self.matrix:
        if False:
            mi = li.getMusicInfoTag()
            mi.setTitle(title)
            mi.setArtist(artist)
            mi.setMediaType('song')
            if args.get('album'):
                mi.setAlbum(args.get('album'))
            if args.get('album_artist'):
                mi.setAlbumArtist(args.get('album_artist'))
            # setTrack doesn't work in v20. Bypassed
            mi.setTrack(args.get('track_number'))
        else: # Matrix v19.0
            mi = {
                'title':       title,
                'artist':      artist,
                'mediatype':   'song',
                'album':       args.get('album'),
                'albumartist': args.get('album_artist'),
                'tracknumber': args.get('track_number'),
            }
            li.setInfo('music', mi)
        li.setArt({'thumb': args.get('art_url'), 'fanart': self.fanart})
        li.setProperty('IsPlayable', 'true')
        li.setPath(url)
        return (url, li, False)

    def get_video_item(self, item_json):
        item_data = item_json.get('data', {})
        title    = item_json.get('title', '')
        duration = int(item_json.get('duration', 0))
        url      = self.INDIGITUBE_VIDEO_URL.format(item_json.get('_id'))
        desc     = item_data.get('description', '')
        textbody = re.compile(r'<[^>]+>').sub('', desc)
        art_id   = item_json.get('poster', '')
        if not isinstance(art_id, str) and len(art_id) > 0:
            art_id = art_id[0]

        if item_data.get('explicit'):
            title += ' (Explicit)'
            if not self.allow_explicit:
                url = self.NOWHERE
        li = xbmcgui.ListItem(label=title, offscreen=True)
        if not self.matrix:
            vi = li.getVideoInfoTag()
            vi.setTitle(title)
            vi.setDuration(duration)
            if textbody:
                vi.setPlot(textbody)
        else:
            vi = {
                'title':     title,
                'duration':  duration,
                'plot':      textbody,
            }
            li.setInfo('video', vi)
        if art_id:
            art_url = self.INDIGITUBE_ALBUM_ART_URL.format(art_id, self._album_quality())
            li.setArt({'thumb': art_url, 'fanart': self.fanart})
        li.setProperty('IsPlayable', 'true')
        if item_data.get('explicit'):
            if not self.allow_explicit:
                url = self.NOWHERE
                li.setProperty('IsPlayable', 'false')
        li.setPath(url)
        return (url, li, False)
        

    def get_root_items(self, page_json):
        page_data = page_json.get('data', {})
        items = []
        for carousel in page_data.get('carousels', []):
            item = self.get_item(carousel)
            if item:
                items.append(item)
        return items

    def get_query_items(self, query_json):
        items = []
        for station in query_json:
            item = self.get_item(station)
            if item:
                items.append(item)
        # items.sort(key=lambda x: x[1].getLabel())
        return items

    def get_channel_items(self, channel_json):
        channel_data = channel_json.get('data', {})
        channel_items = channel_data.get('items', {})
        items = []
        for channel in channel_items:
            if channel.get('item'):
                item = self.get_item(channel.get('item'))
                if item:
                    items.append(item)
        return items

    def get_track_items(self, album_json):
        items = []
        album_title   = album_json.get('title', '')
        album_artist  = album_json.get('realms', [{}])[0].get('title', '')
        album_data    = album_json.get('data', {})
        art_id        = album_data.get('coverImage', {}).get('_id')
        album_art_url = self.INDIGITUBE_ALBUM_ART_URL.format(art_id, self._album_quality())
        args = {
            'track_number': 1,
            'album': album_title,
            'album_artist': album_artist,
            'art_url': album_art_url,
        }
        for track in album_data.get('items', []):
            items.append(self.get_item(track, args))
            args['track_number'] += 1
        return items
