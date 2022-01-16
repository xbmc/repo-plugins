# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from kodi_six import xbmc  # pylint: disable=import-error
from kodi_six import xbmcgui  # pylint: disable=import-error
from kodi_six import xbmcplugin  # pylint: disable=import-error
from kodi_six import xbmcvfs  # pylint: disable=import-error
from six import PY3
from six.moves import xrange
from six.moves.urllib_parse import unquote

from .common import get_handle
from .common import is_resuming_video
from .constants import CONFIG
from .constants import StreamControl
from .containers import Item
from .items.common import get_banner_image
from .items.common import get_fanart_image
from .items.common import get_thumb_image
from .items.track import create_track_item
from .logger import Logger
from .strings import encode_utf8
from .strings import i18n
from .utils import get_file_type
from .utils import get_xml
from .utils import write_pickled

LOG = Logger()


def monitor_channel_transcode_playback(context, server, session_id):
    # Logic may appear backward, but this does allow for a failed start to be detected
    # First while loop waiting for start
    if context.settings.playback_monitor_disabled():
        return

    count = 0
    monitor = xbmc.Monitor()
    player = xbmc.Player()

    LOG.debug('Not playing yet...sleeping for up to 20 seconds at 2 second intervals')
    while not player.isPlaying() and not monitor.abortRequested():
        count += 1
        if count >= 10:
            # Waited 20 seconds and still no movie playing - assume it isn't going to..
            return
        if monitor.waitForAbort(2.0):
            return

    LOG.debug('Waiting for playback to finish')
    while player.isPlaying() and not monitor.abortRequested():
        if monitor.waitForAbort(0.5):
            break

    LOG.debug('Playback Stopped')
    LOG.debug('Stopping PMS transcode job with session: %s' % session_id)
    server.stop_transcode_session(session_id)


def play_media_id_from_uuid(context, data):
    server = context.plex_network.get_server_from_uuid(data['server_uuid'])
    data['url'] = server.get_formatted_url('/library/metadata/%s' % data['media_id'])
    play_library_media(context, data)


def play_library_media(context, data):
    up_next = True
    if '&upnext=false' in data['url']:
        up_next = False
        data['url'] = data['url'].replace('&upnext=false', '')

    server = context.plex_network.get_server_from_url(data['url'])
    media_id = data['url'].split('?')[0].split('&')[0].split('/')[-1]

    if 'includeMarkers' not in data['url']:
        data['url'] += '&' if '?' in data['url'] else '?'
        data['url'] += 'includeMarkers=1'

    tree = get_xml(context, data['url'])
    if tree is None:
        return

    stream = StreamData(context, server, tree).stream

    stream_data = stream.get('full_data', {})
    stream_media = stream.get('media', {})

    if data.get('force') and stream['type'] == 'music':
        play_playlist(context, server, stream)
        return

    url = MediaSelect(context, server, stream).media_url

    if url is None:
        return

    transcode = is_transcode_required(context, stream.get('details', [{}]), data['transcode'])
    try:
        transcode_profile = int(data['transcode_profile'])
    except ValueError:
        transcode_profile = 0

    url, session = get_playback_url_and_session(server, url, stream, transcode, transcode_profile)

    details = {
        'resume': int(int(stream_media['viewOffset']) / 1000),
        'duration': int(int(stream_media['duration']) / 1000),
    }

    if isinstance(data.get('force'), int):
        if int(data['force']) > 0:
            details['resume'] = int(int(data['force']) / 1000)
        else:
            details['resume'] = data['force']

    if CONFIG['kodi_version'] >= 18:
        details['resuming'] = is_resuming_video()
    else:
        details['resuming'] = int(details.get('resume', 0)) > 0

    LOG.debug('Resume has been set to %s' % details['resume'])

    list_item = create_playback_item(url, stream, stream_data, details)

    if stream['type'] in ['music', 'video']:
        server.settings = None  # can't pickle xbmcaddon.Addon()
        write_pickled('playback_monitor.pickle', {
            'details': details,
            'media_id': media_id,
            'playing_file': url,
            'session': session,
            'server': server,
            'stream': stream,
            'up_next': up_next,
            'callback_args': {
                'transcode': transcode,
                'transcode_profile': transcode_profile
            }
        })

    xbmcplugin.setResolvedUrl(get_handle(), True, list_item)

    set_now_playing_properties(server, media_id)


def create_playback_item(url, streams, data, details):
    if not data:
        data = {}

    stream_art = streams.get('art', {})

    if CONFIG['kodi_version'] >= 18:
        list_item = xbmcgui.ListItem(path=url, offscreen=True)
    else:
        list_item = xbmcgui.ListItem(path=url)

    if data:
        fanart = stream_art.get('fanart', '')
        if not fanart:
            fanart = stream_art.get('section_art', '')

        thumb = stream_art.get('thumb', '')
        if not thumb:
            thumb = stream_art.get('section_art', '')
        if not thumb:
            thumb = stream_art.get('fanart', '')

        poster = ''
        if data.get('mediatype', '') == 'movie':
            poster = thumb
        elif data.get('mediatype', '') == 'episode':
            poster = stream_art.get('season_thumb', '')
            if not poster:
                poster = stream_art.get('show_thumb', '')

        list_item.setArt({
            'icon': thumb,
            'thumb': thumb,
            'poster': poster,
            'fanart': fanart,
            'banner': stream_art.get('banner')
        })

    list_item.setProperty('TotalTime', '%.1f' % details['duration'])
    if details.get('resuming') and details.get('resume'):
        list_item.setProperty('ResumeTime', '%.1f' % details['resume'])
        data['playcount'] = '0'

        LOG.debug('Playback from resume point: %s' % details['resume'])

    list_item.setInfo(type=streams['type'], infoLabels=data)

    if streams['type'] == 'music':
        list_item.setProperty('culrc.source', i18n('Plex powered by LyricFind'))

    return list_item


def set_now_playing_properties(server, media_id):
    window = xbmcgui.Window(10000)
    window.setProperty('plugin.video.composite-nowplaying.server', server.get_location())
    window.setProperty('plugin.video.composite-nowplaying.id', media_id)


def get_playback_url_and_session(server, url, streams, transcode, transcode_profile):
    protocol = url.split(':', 1)[0]

    if protocol == 'file':
        LOG.debug('We are playing a local file')
        return url.split(':', 1)[1], None

    if protocol.startswith('http'):
        LOG.debug('We are playing a stream')
        if transcode:
            LOG.debug('We will be transcoding the stream')
            return server.get_universal_transcode(streams['extra']['path'],
                                                  transcode_profile=transcode_profile)

        return server.get_formatted_url(url), None

    return url, None


def is_transcode_required(context, stream_details, default=False):
    if context.settings.always_transcode():
        return True

    codec = stream_details[0].get('codec')
    resolution = stream_details[0].get('videoResolution')
    try:
        bit_depth = int(stream_details[0].get('bitDepth', 8))
    except ValueError:
        bit_depth = None

    if codec and (context.settings.transcode_hevc() and codec.lower() == 'hevc'):
        return True
    if resolution and (context.settings.transcode_g1080() and resolution.lower() == '4k'):
        return True
    if bit_depth and (context.settings.transcode_g8bit() and bit_depth > 8):
        return True

    return default


class StreamData:

    def __init__(self, context, server, tree):
        self.context = context
        self.server = server
        self.tree = tree

        self._content = None

        self.data = {
            'contents': 'type',  # What type of data we are holding
            'audio': {},  # Audio data held in a dict
            'audio_count': 0,  # Number of audio streams
            'subtitle': {},  # Subtitle data (embedded) held as a dict
            'sub_count': 0,  # Number of subtitle streams
            'parts': [],  # The different media locations
            'parts_count': 0,  # Number of media locations
            'media': {},  # Resume/duration data for media
            'details': [],  # Bitrate, resolution and container for each part
            'sub_offset': -1,  # Stream index for selected subs
            'audio_offset': -1,  # Stream index for select audio
            'full_data': {},  # Full metadata extract if requested
            'type': 'video',  # Type of metadata
            'intro_markers': [],
            'extra': {},
        }

        self.update_data()

    def update_data(self):
        LOG.debug('Gathering stream info')

        if not self._get_content():
            return

        self.data['media']['viewOffset'] = self._content.get('viewOffset', 0)
        self.data['media']['duration'] = self._content.get('duration', 12 * 60 * 60)

        if self.data['type'] == 'video':
            self._get_video_data()

        if self.data['type'] == 'music':
            self._get_track_data()

        self._get_art()

        self._get_media_details()

        if (self.data['type'] == 'video' and
                self.context.settings.stream_control() == StreamControl().PLEX):
            self._get_audio_and_subtitles()
        else:
            LOG.debug('Stream selection is set OFF')

    @property
    def stream(self):
        LOG.debug(self.data)
        return self.data

    def _get_content(self):
        content = self.tree.find('Video')
        if content is not None:
            self.data['type'] = 'video'
            self.data['extra']['path'] = content.get('key')
            self._content = content
            return True

        content = self.tree.find('Track')
        if content is not None:
            self.data['type'] = 'music'
            self.data['extra']['path'] = content.get('key')
            self._content = content
            return True

        content = self.tree.find('Photo')
        if content is not None:
            self.data['type'] = 'picture'
            self.data['extra']['path'] = content.get('key')
            self._content = content
            return True

        LOG.debug('No content data found')
        self._content = None
        return False

    def _get_video_data(self):
        self.data['full_data'] = {
            'plot': encode_utf8(self._content.get('summary', '')),
            'title': encode_utf8(self._content.get('title', i18n('Unknown'))),
            'sorttitle': encode_utf8(
                self._content.get('titleSort', self._content.get('title', i18n('Unknown')))
            ),
            'rating': float(self._content.get('rating', 0)),
            'studio': encode_utf8(self._content.get('studio', '')),
            'mpaa': encode_utf8(self._content.get('contentRating', '')),
            'year': int(self._content.get('year', 0)),
            'tagline': self._content.get('tagline', ''),
            'mediatype': 'video'
        }

        if self._content.get('type') == 'movie':
            self.data['full_data']['mediatype'] = 'movie'
        elif self._content.get('type') == 'episode':
            self.data['full_data']['episode'] = int(self._content.get('index', 0))
            self.data['full_data']['aired'] = self._content.get('originallyAvailableAt', '')
            self.data['full_data']['tvshowtitle'] = encode_utf8(
                self._content.get('grandparentTitle', self.tree.get('grandparentTitle', ''))
            )
            self.data['full_data']['season'] = int(
                self._content.get('parentIndex', self.tree.get('parentIndex', 0))
            )
            self.data['full_data']['mediatype'] = 'episode'

        if not self.context.settings.skip_metadata():
            tree_genres = self._content.findall('Genre')
            if tree_genres is not None:
                self.data['full_data']['genre'] = \
                    list(map(lambda x: encode_utf8(x.get('tag', '')), tree_genres))

        self.data['intro_markers'] = self._get_intro_markers()

    def _get_track_data(self):

        track_title = '%s. %s' % \
                      (str(self._content.get('index', 0)).zfill(2),
                       encode_utf8(self._content.get('title', i18n('Unknown'))))
        lyrics = self._get_lyrics()

        self.data['full_data'] = {
            'TrackNumber': int(self._content.get('index', 0)),
            'discnumber': int(self._content.get('parentIndex', 0)),
            'title': track_title,
            'rating': float(self._content.get('rating', 0)),
            'album': encode_utf8(self._content.get('parentTitle',
                                                   self.tree.get('parentTitle', ''))),
            'artist': encode_utf8(self._content.get('grandparentTitle',
                                                    self.tree.get('grandparentTitle', ''))),
            'duration': int(self._content.get('duration', 0)) / 1000,
            'lyrics': lyrics,
        }

        self.data['extra']['album'] = self._content.get('parentKey')
        self.data['extra']['index'] = self._content.get('index')

    def _get_intro_markers(self):
        for marker in self._content.iter('Marker'):
            if (marker.get('type') == 'intro' and
                    marker.get('startTimeOffset') and marker.get('endTimeOffset')):
                return [marker.get('startTimeOffset'), marker.get('endTimeOffset')]

        return []

    def _get_lyrics(self):
        lyrics = []

        lyric_priorities = self.context.settings.get_lyrics_priorities()
        if not lyric_priorities:
            return ''

        for stream in self._content.iter('Stream'):
            if (stream.get('provider') == 'com.plexapp.agents.lyricfind' and
                    stream.get('streamType') == '4'):
                lyric = {
                    'codec': stream.get('codec', ''),
                    'title': stream.get('displayTitle', ''),
                    'format': stream.get('format', ''),
                    'id': stream.get('id', ''),
                    'key': stream.get('key', ''),
                    'provider': stream.get('provider', 'com.plexapp.agents.lyricfind'),
                    'streamType': stream.get('streamType', '4'),
                }
                lyric['priority'] = lyric_priorities.get(lyric.get('codec', 'none'), 0)
                lyrics.append(lyric)

        if lyrics:
            lyrics = sorted(lyrics, key=lambda l: l['priority'], reverse=True)
            return self.server.get_lyrics(lyrics[0]['id'])

        return ''

    def _get_art(self):
        art = {
            'banner': '',
            'fanart': '',
            'season_thumb': '',
            'section_art': '',
            'show_thumb': '',
            'thumb': '',
        }

        if self.context.settings.skip_images():
            self.data['art'] = art
            return

        art.update({
            'banner': get_banner_image(self.context, self.server, self.tree),
            'fanart': get_fanart_image(self.context, self.server, self._content),
            'season_thumb': '',
            'section_art': get_fanart_image(self.context, self.server, self.tree),
            'show_thumb': '',
            'thumb': get_thumb_image(self.context, self.server, self._content),
        })

        if '/:/resources/show-fanart.jpg' in art['section_art']:
            art['section_art'] = art.get('fanart', '')

        if art['fanart'] == '':
            art['fanart'] = art.get('section_art', '')

        if (self._content.get('grandparentThumb', '') and
                '/:/resources/show.png' not in self._content.get('grandparentThumb', '')):
            art['show_thumb'] = \
                get_thumb_image(self.context, self.server, {
                    'thumb': self._content.get('grandparentThumb', '')
                })

        if (art.get('season_thumb', '') and
                '/:/resources/show.png' not in art.get('season_thumb', '')):
            art['season_thumb'] = get_thumb_image(self.context, self.server, {
                'thumb': art.get('season_thumb')
            })

        # get ALL SEASONS or TVSHOW thumb
        if (not art.get('season_thumb', '') and self._content.get('parentThumb', '') and
                '/:/resources/show.png' not in self._content.get('parentThumb', '')):
            art['season_thumb'] = \
                get_thumb_image(self.context, self.server, {
                    'thumb': self._content.get('parentThumb', '')
                })

        elif not art.get('season_thumb', '') and art['show_thumb']:
            art['season_thumb'] = art['show_thumb']

        self.data['art'] = art

    def _get_media_details(self):
        media = self._content.findall('Media')

        self.data['details'] = []
        self.data['parts'] = []
        self.data['parts_count'] = 0

        for details in media:

            try:
                if details.get('videoResolution') == 'sd':
                    resolution = 'SD'
                elif int(details.get('videoResolution', 0)) > 1088:
                    resolution = '4K'
                elif int(details.get('videoResolution', 0)) >= 1080:
                    resolution = 'HD 1080'
                elif int(details.get('videoResolution', 0)) >= 720:
                    resolution = 'HD 720'
                else:
                    resolution = 'SD'
            except ValueError:
                resolution = ''

            media_details = {
                'bitrate': round(float(details.get('bitrate', 0)) / 1000, 1),
                'bitDepth': details.get('bitDepth', 8),
                'videoResolution': resolution,
                'container': details.get('container', 'unknown'),
                'codec': details.get('videoCodec')
            }

            parts = details.findall('Part')

            # Get the media locations (file and web) for later on
            append_parts = self.data['parts'].append
            append_details = self.data['details'].append
            for part in parts:
                append_parts((part.get('key'), part.get('file')))
                append_details(media_details)
                self.data['parts_count'] += 1

    def _get_audio_and_subtitles(self):
        default_to_forced = self.context.settings.default_forced_subtitles()

        audio_offset = 0
        sub_offset = 0

        self.data['contents'] = 'all'
        self.data['audio_count'] = 0
        self.data['sub_count'] = 0

        if PY3:
            tags = self.tree.iter('Stream')
        else:
            tags = self.tree.getiterator('Stream')

        forced_subtitle = False
        for bits in tags:
            stream = dict(bits.items())

            # Audio Streams
            if stream['streamType'] == '2':
                self.data['audio_count'] += 1
                audio_offset += 1
                if stream.get('selected') == '1':
                    LOG.debug('Found preferred audio id: %s ' % stream['id'])
                    self.data['audio'] = stream
                    self.data['audio_offset'] = audio_offset

            # Subtitle Streams
            elif stream['streamType'] == '3':

                if forced_subtitle:
                    continue

                if sub_offset == -1:
                    sub_offset = int(stream.get('index', -1))
                elif 0 < int(stream.get('index', -1)) < sub_offset:
                    sub_offset = int(stream.get('index', -1))

                forced_subtitle = stream.get('forced') == '1' and default_to_forced
                selected = stream.get('selected') == '1'

                if forced_subtitle or selected:
                    LOG.debug('Found %s subtitles id : %s ' %
                              ('preferred' if not forced_subtitle else 'forced', stream['id']))
                    self.data['sub_count'] += 1
                    self.data['subtitle'] = stream
                    if stream.get('key'):
                        self.data['subtitle']['key'] = self.server.get_formatted_url(stream['key'])
                    else:
                        self.data['sub_offset'] = int(stream.get('index')) - sub_offset


class MediaSelect:
    def __init__(self, context, server, data):
        self.context = context
        self.server = server
        self.data = data

        self.dvd_playback = False

        self._media_index = None
        self._media_url = None

        self.update_selection()

    def update_selection(self):
        self._select_media()
        self._get_media_url()

    @property
    def media_url(self):
        return self._media_url

    @media_url.setter
    def media_url(self, value):
        self._media_url = value

    def _select_media(self):
        force_dvd = self.context.settings.force_dvd()

        count = self.data['parts_count']
        options = self.data['parts']
        details = self.data['details']

        if count > 1:

            dialog_options = []
            dvd_index = []
            append_dialog_options = dialog_options.append
            append_dvd_index = dvd_index.append
            index_count = 0
            for items in options:

                if items[1]:
                    name = items[1].split('/')[-1]
                    # name='%s %s %sMbps' % (items[1].split('/')[-1],
                    # details[index_count]['videoResolution'], details[index_count]['bitrate'])
                else:
                    name = '%s %s %sMbps' % (items[0].split('.')[-1],
                                             details[index_count]['videoResolution'],
                                             details[index_count]['bitrate'])

                if force_dvd:
                    if '.ifo' in name.lower():
                        LOG.debug('Found IFO DVD file in ' + name)
                        name = 'DVD Image'
                        append_dvd_index(index_count)

                append_dialog_options(name)
                index_count += 1

            LOG.debug('Create selection dialog box - we have a decision to make!')
            dialog = xbmcgui.Dialog()
            result = dialog.select(i18n('Select media to play'), dialog_options)
            if result == -1:
                self._media_index = None

            if result in dvd_index:
                LOG.debug('DVD Media selected')
                self.dvd_playback = True

            self._media_index = result

        else:
            if force_dvd:
                if '.ifo' in options[0]:
                    self.dvd_playback = True

            self._media_index = 0

    def _get_media_url(self):
        if self._media_index is None:
            self.media_url = None
            return

        stream = self.data['parts'][self._media_index][0]
        filename = self.data['parts'][self._media_index][1]

        if self._http(filename, stream):
            return

        file_type = get_file_type(filename)

        if self._auto(filename, file_type, stream):
            return

        if self._smb_afp(filename, file_type):
            return

        LOG.debug('No option detected, streaming is safest to choose')
        self.media_url = self.server.get_formatted_url(stream)

    def _http(self, filename, stream):
        if filename is None or self.context.settings.get_stream() == '1':  # http
            LOG.debug('Selecting stream')
            self.media_url = self.server.get_formatted_url(stream)
            return True

        return False

    def _auto(self, filename, file_type, stream):
        if self.context.settings.get_stream() == '0':  # auto
            # check if the file can be found locally
            if file_type in ['NIX', 'WIN']:
                LOG.debug('Checking for local file')
                if xbmcvfs.exists(filename):
                    LOG.debug('Local file exists')
                    self.media_url = 'file:%s' % filename
                    return True

            LOG.debug('No local file')
            if self.dvd_playback:
                LOG.debug('Forcing SMB for DVD playback')
                self.context.settings.set_stream('2')
            else:
                self.media_url = self.server.get_formatted_url(stream)
                return True

        return False

    def _smb_afp(self, filename, file_type):
        if self.context.settings.get_stream() in ['2', '3']:  # smb / AFP

            filename = unquote(filename)
            if self.context.settings.get_stream() == '2':
                protocol = 'smb'
            else:
                protocol = 'afp'

            LOG.debug('Selecting smb/unc')
            if file_type == 'UNC':
                self.media_url = '%s:%s' % (protocol, filename.replace('\\', '/'))
            else:
                # Might be OSX type, in which case, remove Volumes and replace with server
                server = self.server.get_location().split(':')[0]
                login_string = ''
                override_info = self.context.settings.override_info()

                if override_info.get('override'):
                    if override_info.get('ip_address'):
                        server = override_info.get('ip_address')
                        LOG.debug('Overriding server with: %s' % server)

                    if override_info.get('user_id'):
                        login_string = '%s:%s@' % (override_info.get('user_id'),
                                                   override_info.get('password'))
                        LOG.debug('Adding AFP/SMB login info for user: %s' %
                                  override_info.get('user_id'))

                if filename.find('Volumes') > 0:
                    self.media_url = '%s:/%s' % \
                                     (protocol, filename.replace('Volumes', login_string + server))
                else:
                    if file_type == 'WIN':
                        self.media_url = ('%s://%s%s/%s' %
                                          (protocol, login_string, server,
                                           filename[3:].replace('\\', '/')))
                    else:
                        # else assume its a file local to server available over smb/samba.
                        # Add server name to file path.
                        self.media_url = '%s://%s%s%s' % (protocol, login_string, server, filename)

            # nas override
            self._nas_override()

            return self.media_url is not None

        return False

    def _nas_override(self):
        override_info = self.context.settings.override_info()
        if override_info.get('override') and override_info.get('root'):
            # Re-root the file path
            LOG.debug('Altering path %s so root is: %s' %
                      (self.media_url, override_info.get('root')))
            if '/' + override_info.get('root') + '/' in self.media_url:
                components = self.media_url.split('/')
                index = components.index(override_info.get('root'))
                pop = components.pop
                for _ in xrange(3, index):
                    pop(3)
                self.media_url = '/'.join(components)


def play_playlist(context, server, data):
    LOG.debug('Creating new playlist')
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()

    url = server.join_url(server.get_url_location(), data['extra'].get('album'), 'children')
    tree = get_xml(context, url)

    if tree is None:
        return

    track_tags = tree.findall('Track')
    add_to_playlist = playlist.add
    item_constructor = xbmcgui.ListItem

    for track in track_tags:
        LOG.debug('Adding playlist item')
        item = Item(server, None, tree, track)
        track = create_track_item(context, item, listing=False)
        url = track[0]
        details = track[1]
        if CONFIG['kodi_version'] >= 18:
            list_item = item_constructor(details.get('title', i18n('Unknown')), offscreen=True)
        else:
            list_item = item_constructor(details.get('title', i18n('Unknown')))

        thumb = data['full_data'].get('thumbnail', CONFIG['icon'])
        if 'thumbnail' in data['full_data']:
            del data['full_data']['thumbnail']  # not a valid info label

        list_item.setArt({
            'icon': thumb,
            'thumb': thumb
        })
        list_item.setInfo(type='music', infoLabels=details)
        add_to_playlist(url, list_item)

    index = int(data['extra'].get('index', 0)) - 1
    LOG.debug('Playlist complete.  Starting playback from track %s [playlist index %s] ' %
              (data['extra'].get('index', 0), index))
    xbmc.Player().playselected(index)
