# -*- coding: utf-8 -*-
"""

    Copyright (C) 2011-2018 PleXBMC (plugin.video.plexbmc) by hippojay (Dave Hawes-Johnson)
    Copyright (C) 2018-2020 Composite (plugin.video.composite_for_plex)

    This file is part of Composite (plugin.video.composite_for_plex)

    SPDX-License-Identifier: GPL-2.0-or-later
    See LICENSES/GPL-2.0-or-later.txt for more information.
"""

from six.moves.urllib_parse import quote_plus

from ..constants import CONFIG
from ..logger import Logger
from ..strings import encode_utf8

LOG = Logger()


def get_link_url(server, url, path_data):
    path = path_data.get('key', '')

    LOG.debug('Path is %s' % path)

    if path == '':
        LOG.debug('Empty Path')
        return ''

    # If key starts with http, then return it
    if path.startswith('http'):
        LOG.debug('Detected http(s) link')
        return path

    # If key starts with a / then prefix with server address
    if path.startswith('/'):
        LOG.debug('Detected base path link')
        return server.join_url(server.get_url_location(), path)

    # If key starts with plex:// then it requires transcoding
    if path.startswith('plex:'):
        LOG.debug('Detected plex link')
        components = path.split('&')
        append_component = components.append
        for idx in components:
            if 'prefix=' in idx:
                del components[components.index(idx)]
                break
        if path_data.get('identifier') is not None:
            append_component('identifier=' + path_data['identifier'])

        path = '&'.join(components)
        return 'plex://' + server.get_location() + '/' + '/'.join(path.split('/')[3:])

    if path.startswith('rtmp'):
        LOG.debug('Detected RTMP link')
        return path

    # Any thing else is assumed to be a relative path and is built on existing url
    LOG.debug('Detected relative link')
    return server.join_url(url, path)


def get_thumb_image(context, server, data, width=720, height=720):
    """
        Simply take a URL or path and determine how to format for images
        @ input: elementTree element, server name
        @ return formatted URL
    """
    if context.settings.skip_images():
        return ''

    thumbnail = encode_utf8(data.get('thumb', '').split('?t')[0])

    if thumbnail.startswith('http'):
        return thumbnail

    if thumbnail.startswith('/'):
        if context.settings.full_resolution_thumbnails():
            return server.get_kodi_header_formatted_url(thumbnail)

        thumbnail = quote_plus('http://localhost:32400' + thumbnail)
        return server.get_kodi_header_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' %
                                                    (thumbnail, width, height))

    return CONFIG['icon']


def get_banner_image(context, server, data, width=720, height=720):
    """
        Simply take a URL or path and determine how to format for images
        @ input: elementTree element, server name
        @ return formatted URL
    """
    if context.settings.skip_images():
        return ''

    banner = encode_utf8(data.get('banner', '').split('?t')[0])

    if banner.startswith('http'):
        return banner

    if banner.startswith('/'):
        if context.settings.full_resolution_thumbnails():
            return server.get_kodi_header_formatted_url(banner)

        banner = quote_plus('http://localhost:32400' + banner)
        return server.get_kodi_header_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' %
                                                    (banner, width, height))

    return ''


def get_fanart_image(context, server, data, width=1280, height=720):
    """
        Simply take a URL or path and determine how to format for fanart
        @ input: elementTree element, server name
        @ return formatted URL for photo resizing
    """
    if context.settings.skip_images():
        return ''

    fanart = encode_utf8(data.get('art', ''))

    if fanart.startswith('http'):
        return fanart

    if fanart.startswith('/'):
        if context.settings.full_resolution_fanart():
            return server.get_kodi_header_formatted_url(fanart)

        return server.get_kodi_header_formatted_url('/photo/:/transcode?url=%s&width=%s&height=%s' %
                                                    (quote_plus('http://localhost:32400' + fanart),
                                                     width, height))

    return ''


def get_media_data(tag_dict):
    """
        Extra the media info_labels from the XML
        @input: dict of <media /> tag attributes
        @output: dict of required values
    """
    stream_info_video = {
        'codec': tag_dict.get('videoCodec', ''),
        'aspect': float(tag_dict.get('aspectRatio', '1.78')),
        'height': int(tag_dict.get('height', 0)),
        'width': int(tag_dict.get('width', 0)),
        'duration': int(tag_dict.get('duration', 0)) / 1000
    }
    stream_info_audio = {
        'codec': tag_dict.get('audioCodec', ''),
        'channels': int(tag_dict.get('audioChannels', '2'))
    }

    return {
        'VideoResolution': tag_dict.get('videoResolution', ''),
        'VideoCodec': tag_dict.get('videoCodec', ''),
        'AudioCodec': tag_dict.get('audioCodec', ''),
        'AudioChannels': tag_dict.get('audioChannels', ''),
        'VideoAspect': tag_dict.get('aspectRatio', ''),
        'stream_info': {
            'video': stream_info_video,
            'audio': stream_info_audio,
        },
    }


def get_metadata(context, data):
    metadata = {
        'attributes': {},
        'cast': [],
        'collections': [],
        'director': [],
        'genre': [],
        'writer': [],
    }

    media_tag = data.find('Media')
    if media_tag is not None:
        metadata['attributes'] = dict(media_tag.items())

    if not context.settings.skip_metadata():
        append_genre = metadata['genre'].append
        append_writer = metadata['writer'].append
        append_director = metadata['director'].append
        append_cast = metadata['cast'].append
        append_collections = metadata['collections'].append

        for child in data:
            if child.tag == 'Genre':
                append_genre(child.get('tag'))
            elif child.tag == 'Writer':
                append_writer(child.get('tag'))
            elif child.tag == 'Director':
                append_director(child.get('tag'))
            elif child.tag == 'Role':
                append_cast(child.get('tag'))
            elif child.tag == 'Collection':
                append_collections(child.get('tag'))

    return metadata
