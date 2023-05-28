"""Map JSON API outputs into playable content and meanus for Kodi"""
# pylint: disable=import-error
from xbmcswift2 import xbmc
# pylint: disable=import-error
from xbmcswift2 import actions
# pylint: disable=cyclic-import
from addon import plugin
from . import hof
from . import utils


def create_favorites_item(label):
    """Return menu entry to access user favorites"""
    return {
        'label': label,
        'path': plugin.url_for('favorites')
    }


def create_last_viewed_item(label):
    """Return menu entry to access user history
    with an additional command to flush user history"""
    return {
        'label': label,
        'path': plugin.url_for('last_viewed'),
        'context_menu': [
            (plugin.addon.getLocalizedString(30030),
                actions.background(plugin.url_for('purge_last_viewed')))
        ]
    }


def create_search_item():
    """Return menu entry to search content"""
    return {
        'label': plugin.addon.getLocalizedString(30012),
        'path': plugin.url_for('search')
    }


def map_category_item(item, category_code):
    """Return menu entry to access a category content"""
    title = item.get('title')
    path = plugin.url_for(
        'sub_category_by_title',
        category_code=category_code,
        sub_category_title=utils.encode_string(title))

    return {
        'label': title,
        'path': path
    }


def map_generic_item(item, show_video_streams):
    """Return entry menu for video or playlist"""
    program_id = item.get('programId')

    if utils.is_playlist(program_id):
        item = map_playlist(item)
    else:
        item = map_video(item, show_video_streams)
    return item


def map_video(item, show_video_streams):
    """Create a video menu item from a json returned by Arte HBBTV API"""
    program_id = item.get('programId')
    label = utils.format_title_and_subtitle(item.get('title'), item.get('subtitle'))
    kind = item.get('kind')
    duration = item.get('durationSeconds')
    airdate = item.get('broadcastBegin')
    if airdate is not None:
        airdate = str(utils.parse_date_hbbtv(airdate))
    if show_video_streams:
        path = plugin.url_for('streams', program_id=program_id)
    else:
        path = plugin.url_for('play', kind=kind, program_id=program_id)

    return {
        'label': label,
        'path': path,
        'thumbnail': item.get('imageUrl'),
        'is_playable': not show_video_streams,
        'info_type': 'video',
        'info': {
            'title': item.get('title'),
            'duration': duration,
            'genre': item.get('genrePresse'),
            'plot': item.get('shortDescription') or item.get('fullDescription'),
            'plotoutline': item.get('teaserText'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            # 'year': int(config.get('productionYear')),
            'country': [country.get('label') for country in item.get('productionCountries', [])],
            'director': item.get('director'),
            'aired': airdate
        },
        'properties': {
            'fanart_image': item.get('imageUrl'),
        },
        'context_menu': [
            (plugin.addon.getLocalizedString(30023),
                actions.background(plugin.url_for(
                    'add_favorite', program_id=program_id, label=label))),
            (plugin.addon.getLocalizedString(30024),
                actions.background(plugin.url_for(
                    'remove_favorite', program_id=program_id, label=label))),
        ],
    }

def map_artetv_video(item):
    """Return video menu item to show content from Arte TV API
    :rtype dict[str, Any] | None: To be used in
    https://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo"""
    program_id = item.get('programId')
    label = utils.format_title_and_subtitle(item.get('title'), item.get('subtitle'))
    kind = item.get('kind')
    duration = item.get('durationSeconds')
    airdate = item.get('beginsAt') # broadcastBegin
    if airdate is not None:
        airdate = str(utils.parse_date_artetv(airdate))

    fanart_url = ""
    thumbnail_url = ""
    if item.get('images') and item.get('images')[0] and item.get('images')[0].get('url'):
        # Remove query param type=TEXT to avoid title embeded in image
        fanart_url = item.get('images')[0].get('url').replace('?type=TEXT', '')
        # Set same image for fanart and thumbnail to spare network bandwidth
        # and business logic easier to maintain
        #if item.get('images')[0].get('alternateResolutions'):
        #    smallerImage = item.get('images')[0].get('alternateResolutions')[3]
        #    if smallerImage and smallerImage.get('url'):
        #        thumbnailUrl = smallerImage.get('url').replace('?type=TEXT', '')
    if not fanart_url:
        fanart_url = item.get('mainImage').get('url').replace('__SIZE__', '1920x1080')
    thumbnail_url = fanart_url

    progress = item.get('lastviewed') and item.get('lastviewed').get('progress') or 0
    time_offset = item.get('lastviewed') and item.get('lastviewed').get('timecode') or 0

    if not isinstance(kind, str) and kind is not None:
        kind = kind.get('code')
    if kind == 'EXTERNAL':
        return None

    is_playlist = utils.is_playlist(program_id)
    path = plugin.url_for('collection' if is_playlist else 'play', kind=kind, program_id=program_id)

    return {
        'label': label,
        'path': path,
        'thumbnail': thumbnail_url,
        'is_playable': not is_playlist, # item.get('playable') # not show_video_streams
        'info_type': 'video',
        'info': {
            'title': item.get('title'),
            'duration': duration,
            #'genre': item.get('genrePresse'),
            'plot': item.get('description'),
            'plotoutline': item.get('shortDescription'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            # 'year': int(config.get('productionYear')),
            #'country': [country.get('label') for country in item.get('productionCountries', [])],
            #'director': item.get('director'),
            #'aired': airdate
            'playcount': '1' if progress >= 0.95 else '0',
        },
        'properties': {
            'fanart_image': fanart_url,
            # ResumeTime and TotalTime deprecated. Use InfoTagVideo.setResumePoint() instead.
            'ResumeTime': str(time_offset),
            'TotalTime': str(duration),
            'StartPercent': str(progress * 100)
        },
        'context_menu': [
            (plugin.addon.getLocalizedString(30023),
                actions.background(plugin.url_for(
                    'add_favorite', program_id=program_id, label=label))),
            (plugin.addon.getLocalizedString(30024),
                actions.background(plugin.url_for(
                    'remove_favorite', program_id=program_id, label=label))),
        ],
    }


def map_live_video(item, quality, audio_slot):
    """Return menu entry to watch live content from Arte TV API"""
    # program_id = item.get('id')
    attr = item.get('attributes')
    meta = attr.get('metadata')

    duration = meta.get('duration').get('seconds')

    fanart_url = ""
    thumbnail_url = ""
    if meta.get('images') and meta.get('images')[0] and meta.get('images')[0].get('url'):
        # Remove query param type=TEXT to avoid title embeded in image
        fanart_url = meta.get('images')[0].get('url').replace('?type=TEXT', '')
        thumbnail_url = fanart_url
        # Set same image for fanart and thumbnail to spare network bandwidth
        # and business logic easier to maintain
        #if item.get('images')[0].get('alternateResolutions'):
        #    smallerImage = item.get('images')[0].get('alternateResolutions')[3]
        #    if smallerImage and smallerImage.get('url'):
        #        thumbnailUrl = smallerImage.get('url').replace('?type=TEXT', '')
    stream_url=map_playable(attr.get('streams'), quality, audio_slot, match_artetv).get('path')

    return {
        'label': utils.format_live_title_and_subtitle(meta.get('title'), meta.get('subtitle')),
        'path': plugin.url_for('play_live', stream_url=stream_url),
        # playing the stream from program id makes the live starts from the beginning of the video
        # while it starts the video like the live tv, with the above
        #  'path': plugin.url_for('play', kind='SHOW', program_id=programId.replace('_fr', '')),
        'thumbnail': thumbnail_url,
        'is_playable': True, # not show_video_streams
        'info_type': 'video',
        'info': {
            'title': meta.get('title'),
            'duration': duration,
            #'genre': item.get('genrePresse'),
            'plot': meta.get('description'),
            #'plotoutline': meta.get('shortDescription'),
            # year is not correctly used by kodi :(
            # the aired year will be used by kodi for production year :(
            # 'year': int(config.get('productionYear')),
            #'country': [country.get('label') for country in item.get('productionCountries', [])],
            #'director': item.get('director'),
            #'aired': airdate
            'playcount': '0',
        },
        'properties': {
            'fanart_image': fanart_url,
        }
    }


def map_playlist(item):
    """Map JSON item to menu entry to access playlist content"""
    program_id = item.get('programId')
    kind = item.get('kind')

    return {
        'label': utils.format_title_and_subtitle(item.get('title'), item.get('subtitle')),
        'path': plugin.url_for('collection', kind=kind, collection_id=program_id),
        'thumbnail': item.get('imageUrl'),
        'info': {
            'title': item.get('title'),
            'plotoutline': item.get('teaserText')
        }
    }


def map_streams(item, streams, quality):
    """Map JSON item and list of audio streams into a menu."""
    program_id = item.get('programId')
    kind = item.get('kind')

    video_item = map_video(item, False)

    filtered_streams = None
    for qlt in [quality] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality]:
        filtered_streams = [s for s in streams if s.get('quality') == qlt]
        if len(filtered_streams) > 0:
            break

    if filtered_streams is None or len(filtered_streams) == 0:
        raise RuntimeError('Could not resolve stream...')

    sorted_filtered_streams = sorted(
        filtered_streams, key=lambda s: s.get('audioSlot'))

    def map_stream(video_item, stream):
        audio_slot = stream.get('audioSlot')
        audio_label = stream.get('audioLabel')

        video_item['label'] = audio_label
        video_item['is_playable'] = True
        video_item['path'] = plugin.url_for(
            'play_specific', kind=kind, program_id=program_id, audio_slot=str(audio_slot))

        return video_item

    return [map_stream(dict(video_item), stream) for stream in sorted_filtered_streams]


def map_playable(streams, quality, audio_slot, match):
    """Select the stream best matching quality and audio slot criteria in streams
    and map to a menu entry"""
    stream = None
    for qlt in [quality] + [i for i in ['SQ', 'EQ', 'HQ', 'MQ'] if i is not quality]:
        # pylint: disable=cell-var-from-loop
        stream = hof.find(lambda s: match(s, qlt, audio_slot), streams)
        if stream:
            break

    if stream is None:
        raise RuntimeError('Could not resolve stream...')

    return {
        'info_type': 'video',
        'path': stream.get('url'),
    }

def match_hbbtv(item, quality, audio_slot):
    """Return True if item from HHB TV API matches quality and audio_slot constraints,
    False otherwise"""
    return item.get('quality') == quality and item.get('audioSlot') == audio_slot

def match_artetv(item, quality, audio_slot):
    """Return True if item from Arte TV API matches quality and audio_slot constraints,
    False otherwise"""
    return item.get('mainQuality').get('code') == quality and str(item.get('slot')) == audio_slot


def map_zone_to_item(zone, cached_categories):
    """Arte TV API page is split into zones. Map a 'zone' to menu item(s).
    Populate cached_categories for zones with videos available in child 'content'"""
    menu_item = None
    title = zone.get('title')
    if zone.get('id') == 'b1dfd8e0-4757-4236-9dab-6f6331cb5ea4':
        menu_item = create_favorites_item(title)
    elif zone.get('id') == '823d6af6-fedd-4b54-8049-ddb7158eee64':
        menu_item = create_last_viewed_item(title)
    elif zone.get('content') and zone.get('content').get('data'):
        cached_category = map_cached_categories(zone)
        if cached_category:
            category_code = zone.get('code')
            cached_categories[category_code] = cached_category
            menu_item = map_categories_item(zone, 'cached_category')
    elif zone.get('link'):
        menu_item = map_categories_item(zone, 'api_category', zone.get('link').get('page'))
    else:
        xbmc.log(f"Zone \"{title}\" will be ignored. No link. No content. id unknown.")

    return menu_item


def map_cached_categories(zone):
    """Map JSON node zone from Arte TV API to a list of menu items."""
    cached_category = []
    for item in zone.get('content').get('data'):
        menu_video = map_artetv_video(item)
        if menu_video:
            cached_category.append(menu_video)
    return cached_category

def map_categories_item(item, category_rule, category_code=None):
    """Return a menu entry to access content of category item.
    :param dict item: JSON node item
    :param str category_rule: value is either cached_category, either api_category.
    :param str category_code: if None, use item code.
    """
    if not category_code:
        category_code = item.get('code')
    return {
        'label': utils.colorize(item.get('title'), item.get('color')),
        'path': plugin.url_for(category_rule, category_code=category_code)
    }
