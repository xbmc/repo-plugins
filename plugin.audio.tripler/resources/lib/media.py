import re

class Media:
    RE_BANDCAMP_ALBUM_ID             = re.compile(r'https://bandcamp.com/EmbeddedPlayer/.*album=(?P<media_id>[^/]+)')
    RE_BANDCAMP_ALBUM_ART            = re.compile(r'"art_id":(\w+)')
    BANDCAMP_ALBUM_PLUGIN_BASE_URL   = 'plugin://plugin.audio.kxmxpxtx.bandcamp/?mode=list_songs'
    BANDCAMP_ALBUM_PLUGIN_FORMAT     = '{}&album_id={}&item_type=a'
    BANDCAMP_ALBUM_ART_URL           = 'https://bandcamp.com/api/mobile/24/tralbum_details?band_id=1&tralbum_type=a&tralbum_id={}'

    RE_BANDCAMP_ALBUM_LINK_ID        = re.compile(r'(?P<media_id>https?://[^/\.]+\.bandcamp.com/album/[\w\-]+)')
    RE_BANDCAMP_BAND_LINK_ID         = re.compile(r'(?P<media_id>https?://[^/\.]+\.bandcamp.com/)$')

    RE_BANDCAMP_TRACK_ID             = re.compile(r'(?P<media_id>https?://[^/\.]+\.bandcamp.com/(track|album)/[\w\-]+)')
    BANDCAMP_TRACK_PLUGIN_BASE_URL   = 'plugin://plugin.audio.kxmxpxtx.bandcamp/?mode=url'
    BANDCAMP_TRACK_PLUGIN_FORMAT     = '{}&url={}'
    RE_BANDCAMP_TRACK_ART            = re.compile(r'art_id&quot;:(?P<art_id>\d+),')
    RE_BANDCAMP_TRACK_BAND_ART       = re.compile(r'data-band="[^"]*image_id&quot;:(?P<band_art_id>\d+)}"')

    RE_BANDCAMP_ART_QUALITY_SEARCH   = r'/img/(?P<art>[^_]+)_(?P<quality>\d+)\.jpg'

    RE_SOUNDCLOUD_PLAYLIST_ID        = re.compile(r'.+soundcloud\.com/playlists/(?P<media_id>[^&]+)')
    SOUNDCLOUD_PLUGIN_BASE_URL       = 'plugin://plugin.audio.soundcloud/'
    SOUNDCLOUD_PLUGIN_FORMAT         = '{}?action=call&call=/playlists/{}'

    RE_YOUTUBE_VIDEO_ID              = re.compile(r'^(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube(?:-nocookie)?\.com|youtu.be)(?:\/(?:[\w\-]+\?v=|embed\/|v\/)?)(?P<media_id>[\w\-]+)(?!.*list)\S*$')
    YOUTUBE_PLUGIN_BASE_URL          = 'plugin://plugin.video.youtube/play/'
    YOUTUBE_VIDEO_PLUGIN_FORMAT      = '{}?video_id={}&play=1'
    YOUTUBE_VIDEO_ART_URL_FORMAT     = 'https://i.ytimg.com/vi/{}/hqdefault.jpg'

    RE_YOUTUBE_PLAYLIST_ID           = re.compile(r'^(?:(?:https?:)?\/\/)?(?:(?:www|m)\.)?(?:youtube(?:-nocookie)?\.com|youtu.be)\/.+\?.*list=(?P<media_id>[\w\-]+)')
    YOUTUBE_PLAYLIST_PLUGIN_FORMAT   = '{}?playlist_id={}&order=default&play=1'
    YOUTUBE_PLAYLIST_ART_URL         = 'https://youtube.com/oembed?url=https%3A//www.youtube.com/playlist%3Flist%3D{}&format=json'

    RE_INDIGITUBE_ALBUM_ID           = re.compile(r'https://www.indigitube.com.au/embed/album/(?P<media_id>[^"]+)')
    INDIGITUBE_ALBUM_PLUGIN_BASE_URL   = 'plugin://plugin.audio.indigitube/?mode=list_songs'
    INDIGITUBE_ALBUM_PLUGIN_FORMAT   = '{}&album_id={}'

    RE_SPOTIFY_ALBUM_ID              = re.compile(r'.+spotify\.com(\/embed)?\/album\/(?P<media_id>[^&?\/]+)')
    RE_SPOTIFY_PLAYLIST_ID           = re.compile(r'.+spotify\.com(\/embed)?\/playlist\/(?P<media_id>[^&]+)')

    RE_APPLE_ALBUM_ID                = re.compile(r'.+music\.apple\.com\/au\/album\/(?P<media_id>.+)')
    APPLE_ALBUM_URL                  = 'https://music.apple.com/au/album/{}'

    EXT_SEARCH_PLUGIN_FORMAT         = 'plugin://plugin.audio.tripler/tracks/ext_search?q={search}'

    RE_MEDIA_URLS = {
        'bandcamp': {
            're':     RE_BANDCAMP_ALBUM_ID,
            'base':   BANDCAMP_ALBUM_PLUGIN_BASE_URL,
            'format': BANDCAMP_ALBUM_PLUGIN_FORMAT,
            'name':   'Bandcamp',
        },
        'bandcamp_track': {
            're':     RE_BANDCAMP_TRACK_ID,
            'base':   BANDCAMP_TRACK_PLUGIN_BASE_URL,
            'format': BANDCAMP_TRACK_PLUGIN_FORMAT,
            'name':   'Bandcamp',
        },
        'bandcamp_link': {
            're':     RE_BANDCAMP_ALBUM_LINK_ID,
            'base':   BANDCAMP_TRACK_PLUGIN_BASE_URL,
            'format': BANDCAMP_TRACK_PLUGIN_FORMAT,
            'name':   'Bandcamp',
        },
        'bandcamp_band_link': {
            're':     RE_BANDCAMP_BAND_LINK_ID,
            'format': EXT_SEARCH_PLUGIN_FORMAT,
            'name':   'Bandcamp Band Search',
        },
        'soundcloud': {
            're':     RE_SOUNDCLOUD_PLAYLIST_ID,
            'base':   SOUNDCLOUD_PLUGIN_BASE_URL,
            'format': SOUNDCLOUD_PLUGIN_FORMAT,
            'name':   'SoundCloud',
        },
        'youtube': {
            're':     RE_YOUTUBE_VIDEO_ID,
            'base':   YOUTUBE_PLUGIN_BASE_URL,
            'format': YOUTUBE_VIDEO_PLUGIN_FORMAT,
            'name':   'YouTube',
        },
        'youtube_playlist': {
            're':     RE_YOUTUBE_PLAYLIST_ID,
            'base':   YOUTUBE_PLUGIN_BASE_URL,
            'format': YOUTUBE_PLAYLIST_PLUGIN_FORMAT,
            'name':   'YouTube',
        },
        'indigitube': {
            're':     RE_INDIGITUBE_ALBUM_ID,
            'base':   INDIGITUBE_ALBUM_PLUGIN_BASE_URL,
            'format': INDIGITUBE_ALBUM_PLUGIN_FORMAT,
            'name':   'indigiTUBE',
        },
        'spotify': {
            're':     RE_SPOTIFY_ALBUM_ID,
            'format': EXT_SEARCH_PLUGIN_FORMAT,
            'name':   'Album Search',
        },
        'spotify_playlist': {
            're':     RE_SPOTIFY_PLAYLIST_ID,
            'format': EXT_SEARCH_PLUGIN_FORMAT,
            'name':   'Playlist Search',
        },
        'apple': {
            're':     RE_APPLE_ALBUM_ID,
            'format': EXT_SEARCH_PLUGIN_FORMAT,
            'name':   'Album Search',
        },
    }

    def __init__(self, quality):
        self.quality = quality

    def parse_media_id(self, plugin, media_id, search=''):
        info = self.RE_MEDIA_URLS.get(plugin, {})
        if info:
            return info.get('format', '').format(info.get('base', ''), media_id, search=search)
        else:
            return ''

    def parse_art(self, art):
        if art and 'f4.bcbits.com' in art:
            band = '/img/a' not in art
            quality = self._bandcamp_band_quality() if band else self._bandcamp_album_quality()
            art = re.sub(self.RE_BANDCAMP_ART_QUALITY_SEARCH, f'/img/\g<art>_{quality}.jpg', art)
        if art and '/600x600bf-60.jpg' in art:
            art = art.replace('/600x600bf-60.jpg', self._apple_album_quality())
        return art

    def _bandcamp_band_quality(self):
        if self.quality == 0:
            return 1 # full resolution
        if self.quality == 1:
            return 10 # 1200px wide
        if self.quality == 2:
            return 25 # 700px wide

    def _bandcamp_album_quality(self):
        if self.quality == 0:
            return 5 # 700px wide
        if self.quality == 1:
            return 2 # 350px wide
        if self.quality == 2:
            return 9 # 210px wide

    def _apple_album_quality(self):
        if self.quality == 0:
            return '/600x600bf.jpg'
        if self.quality == 1:
            return '/600x600bf-60.jpg'
        if self.quality == 2:
            return '/300x300bb-60.jpg'
