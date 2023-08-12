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
        'path': plugin.url_for('favorites'),
        'context_menu': [
            (plugin.addon.getLocalizedString(30040),
                actions.background(plugin.url_for('purge_favorites')))
        ]
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
        item = map_collection_as_menu_item(item)
        #item = map_video_as_playlist_item(item)
    elif show_video_streams is True:
        item = map_video_streams_as_menu(item)
    else:
        item = map_video_as_item(item)
    return item

def map_collection_as_playlist(arte_collection, req_start_program_id = None):
    """
    Map a collection from arte API to a list of items ready to build a playlist.
    Playlist item will be in the same order as arte_collection, if start_program_id
    is None, otherwise it starts from item with program id equals to start_program_id
    (and the same order).
    Return an empty list, if arte_collection is None or empty.
    """
    items_before_start = []
    items_after_start = []
    before_start = True
    # assume arte_collection[0] will be mapped successfully with map_video_as_playlist_item
    start_program_id = arte_collection[0].get('programId')
    for arte_item in arte_collection or []:
        xbmc_item = map_video_as_playlist_item(arte_item)
        if xbmc_item is None:
            break

        # search for the start item until it is found once
        if before_start:
            if req_start_program_id is None:
                # start from the first element not fully viewed
                if utils.get_progress(arte_item) < 0.95:
                    before_start = False
                    start_program_id = arte_item.get('programId')
            else:
                # start from the requested element
                if req_start_program_id == arte_item.get('programId'):
                    before_start = False
                    start_program_id = req_start_program_id

        if before_start:
            items_before_start.append(xbmc_item)
        else:
            items_after_start.append(xbmc_item)
    return { 'collection': items_after_start + items_before_start,
        'start_program_id': start_program_id}

def map_video_as_playlist_item(item):
    """
    Create a video menu item without recursiveness to fetch parent collection
    from a json returned by Arte HBBTV or ArteTV API
    """
    program_id = item.get('programId')
    is_hbbtv_content = True
    kind = item.get('kind')
    if isinstance(kind, dict) and kind.get('code', False):
        kind = kind.get('code')
        is_hbbtv_content = False
    if isinstance(item.get('lastviewed'), dict):
        is_hbbtv_content = False

    path = plugin.url_for(
        'play_siblings', kind=kind, program_id=program_id, audio_slot='1', from_playlist='1')
    result = map_generic_video(item, path, True) if is_hbbtv_content \
        else map_artetv_item_new(item, path, True)
    return result

def map_video_streams_as_menu(item):
    """Create a menu item for video streams from a json returned by Arte HBBTV API"""
    program_id = item.get('programId')
    path = plugin.url_for('streams', program_id=program_id)
    return map_generic_video(item, path, False)

def map_video_as_item(item):
    """Create a playable video menu item from a json returned by Arte HBBTV API"""
    program_id = item.get('programId')
    kind = item.get('kind')
    path = plugin.url_for('play', kind=kind, program_id=program_id)
    return map_generic_video(item, path, True)

def map_generic_video(item, path, is_playable):
    """Create a video menu item from a json returned by Arte HBBTV API"""
    program_id = item.get('programId')
    label = utils.format_title_and_subtitle(item.get('title'), item.get('subtitle'))
    duration = item.get('durationSeconds')
    if duration is None:
        duration = item.get('duration', None)
        if isinstance(duration, dict):
            duration = duration.get('seconds', None)
    airdate = item.get('broadcastBegin')
    if airdate is not None:
        airdate = str(utils.parse_date_hbbtv(airdate))

    return {
        'label': label,
        'path': path,
        'thumbnail': item.get('imageUrl'),
        'is_playable': is_playable,
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
            (plugin.addon.getLocalizedString(30035),
                actions.background(plugin.url_for(
                    'mark_as_watched', program_id=program_id, label=label))),
        ],
    }

PREFERED_KINDS = ['TV_SERIES', 'MAGAZINE']

def map_artetv_item(item):
    """
    Return video menu item to show content from Arte TV API.
    Manage specificities of various types : playlist, menu or video items
    """
    program_id = item.get('programId')
    kind = item.get('kind')
    if isinstance(kind, dict) and kind.get('code', False):
        kind = kind.get('code')
    if kind == 'EXTERNAL':
        return None

    additional_context_menu = []
    if utils.is_playlist(program_id):
        if kind in PREFERED_KINDS:
            #content_type = Content.PLAYLIST
            path = plugin.url_for('play_collection', kind=kind, collection_id=program_id)
            is_playable = True
            additional_context_menu = [
                (plugin.addon.getLocalizedString(30011),
                actions.update_view(plugin.url_for(
                    'display_collection', program_id=program_id, kind=kind)))]
        else:
            #content_type = Content.MENU_ITEM
            path = plugin.url_for('display_collection', kind=kind, program_id=program_id)
            is_playable = False
    else:
        #content_type = Content.VIDEO
        path = plugin.url_for('play', kind=kind, program_id=program_id)
        is_playable = True

    xbmc_item = map_artetv_item_new(item, path, is_playable)
    if xbmc_item is not None:
        xbmc_item['context_menu'].extend(additional_context_menu)
    return xbmc_item


def map_artetv_item_new(item, path, is_playable):
    """
    Return video menu item to show content from Arte TV API.
    Generic method that tqke variables mapping in inputs.
    :rtype dict[str, Any] | None: To be used in
    https://romanvm.github.io/Kodistubs/_autosummary/xbmcgui.html#xbmcgui.ListItem.setInfo
    """
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

    progress = utils.get_progress(item)
    time_offset = item.get('lastviewed') and item.get('lastviewed').get('timecode') or 0

    if isinstance(kind, dict) and kind.get('code', False):
        kind = kind.get('code')
    if kind == 'EXTERNAL':
        return None

    return {
        'label': label,
        'path': path,
        'thumbnail': thumbnail_url,
        'is_playable': is_playable, # item.get('playable') # not show_video_streams
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
            #'StartPercent': str(progress * 100),
            'StartPercent': '0' if duration is None else str(
                float(time_offset if isinstance(time_offset, int) else 0) * 100.0
                / float(duration)),
        },
        'context_menu': [
            (plugin.addon.getLocalizedString(30023),
                actions.background(plugin.url_for(
                    'add_favorite', program_id=program_id, label=label))),
            (plugin.addon.getLocalizedString(30024),
                actions.background(plugin.url_for(
                    'remove_favorite', program_id=program_id, label=label))),
            (plugin.addon.getLocalizedString(30035),
                actions.background(plugin.url_for(
                    'mark_as_watched', program_id=program_id, label=label))),
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


def map_collection_as_menu_item(item):
    """Map JSON item to menu entry to access playlist content"""
    program_id = item.get('programId')
    kind = item.get('kind')

    return {
        'label': utils.format_title_and_subtitle(item.get('title'), item.get('subtitle')),
        'path': plugin.url_for('display_collection', kind=kind, collection_id=program_id),
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

    video_item = map_video_as_item(item)

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
    if get_authenticated_content_type(zone) == 'sso-favorites':
        menu_item = create_favorites_item(title)
    elif get_authenticated_content_type(zone) == 'sso-personalzone':
        menu_item = create_last_viewed_item(title)
    elif zone.get('content') and zone.get('content').get('data'):
        cached_category = map_collection_as_menu(zone)
        if cached_category:
            category_code = zone.get('code')
            cached_categories[category_code] = cached_category
            menu_item = map_categories_item(zone, 'cached_category')
    elif zone.get('link'):
        menu_item = map_categories_item(zone, 'api_category', zone.get('link').get('page'))
    else:
        xbmc.log(f"Zone \"{title}\" will be ignored. No link. No content. id unknown.")

    return menu_item


def get_authenticated_content_type(artetv_zone):
    """
    Return the value of artetv_zone.authenticatedContent.contentId or None.
    Known values are sso-personalzone and sso-favorites
    """
    if not isinstance(artetv_zone, dict):
        return None
    if not isinstance(artetv_zone.get('authenticatedContent'), dict):
        return None
    return artetv_zone.get('authenticatedContent', {}).get('contentId', None)


def map_collection_as_menu(zone):
    """Map JSON node zone from Arte TV API to a list of menu items."""
    cached_category = []
    for item in zone.get('content').get('data'):
        menu_video = map_artetv_item(item)
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
