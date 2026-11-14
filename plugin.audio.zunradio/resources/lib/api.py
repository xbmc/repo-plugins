# SPDX-License-Identifier: GPL-2.0-or-later
"""Streams of ZUN radio and the information about what is on air.

Pure Python without Kodi modules, so the logic can be tested outside Kodi.
"""

import json
from collections import namedtuple
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

BASE_URL = 'https://zunradio.cz/'
TRACK_URL = BASE_URL + 'onair/track_for_web.json'
SHOW_URL = BASE_URL + 'onair/actual_show.json'
TIMEOUT = 10

# Hosts that serve ZUN radio streams (stream2 is the backup site)
STREAM_HOSTS = ('stream.zunradio.cz', 'stream2.zunradio.cz')

Stream = namedtuple('Stream', 'id url mimetype label_id')

STREAMS = (
    Stream('zun1', 'https://stream.zunradio.cz/zun1.aac', 'audio/aac', 30001),
    Stream('zun2', 'https://stream.zunradio.cz/zun2.aac', 'audio/aac', 30002),
    Stream('zun3', 'https://stream.zunradio.cz/zun3.mp3', 'audio/mpeg', 30003),
)
DEFAULT_STREAM = STREAMS[0]

NowPlaying = namedtuple('NowPlaying', 'artist title show cover show_image label label_logo')
NowPlaying.__new__.__defaults__ = ('', '', '', '', '', '', '')


def stream_by_id(stream_id):
    """Return the stream with the given id, or the default stream."""
    for stream in STREAMS:
        if stream.id == stream_id:
            return stream
    return DEFAULT_STREAM


def is_zun_stream(url):
    """True when the URL points to a ZUN radio stream."""
    try:
        parts = urlsplit(url or '')
    except ValueError:
        return False
    return parts.scheme in ('http', 'https') and parts.hostname in STREAM_HOSTS


def _image_url(base, name):
    """Absolute URL of an image given as a file name or a path."""
    name = str(name or '').strip()
    if not name:
        return ''
    return urljoin(base, quote(name, safe="/:?=&%~+"))


def parse_track(data):
    """Artist, title, cover and record label from track_for_web.json.

    cover_large (the original cover) is preferred to cover (300 px); label and label_logo
    (white logo of the record label on black) are optional.
    """
    track = data.get('track') if isinstance(data, dict) else None
    if not isinstance(track, dict):
        return None
    cover = track.get('cover_large') or track.get('cover')
    return {
        'artist': str(track.get('artist') or '').strip(),
        'title': str(track.get('title') or '').strip(),
        'cover': _image_url(BASE_URL + 'onair/', cover),
        'label': str(track.get('label') or '').strip(),
        'label_logo': _image_url(BASE_URL + 'onair/', track.get('label_logo')),
    }


def parse_show(data):
    """Name and image of the show from actual_show.json."""
    if not isinstance(data, dict):
        return None
    image = str(data.get('imageUrl') or '').lstrip('/')
    return {
        'show': str(data.get('ShowName') or '').strip(),
        'show_image': _image_url(BASE_URL, image),
    }


def get_json(url, user_agent, timeout=TIMEOUT):
    """Download and decode a JSON document."""
    request = Request(url, headers={'User-Agent': user_agent, 'Accept': 'application/json'})
    with urlopen(request, timeout=timeout) as response:  # nosec: fixed https URLs only
        return json.loads(response.read().decode('utf-8'))


def fetch_now_playing(user_agent, timeout=TIMEOUT, getter=get_json):
    """What is on air now. Returns None when the track information is unavailable.

    The show is optional: when actual_show.json fails, the track is still returned.
    """
    track = parse_track(getter(TRACK_URL, user_agent, timeout))
    if not track:
        return None
    try:
        show = parse_show(getter(SHOW_URL, user_agent, timeout)) or {}
    except (OSError, ValueError):
        show = {}
    return NowPlaying(
        artist=track['artist'],
        title=track['title'],
        show=show.get('show', ''),
        cover=track['cover'],
        show_image=show.get('show_image', ''),
        label=track['label'],
        label_logo=track['label_logo'],
    )
