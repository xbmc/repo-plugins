"""Map JSON API outputs into playable content and meanus for Kodi"""
# pylint: disable=import-error
from xbmcswift2 import xbmc
from resources.lib import hof
from resources.lib import utils
from resources.lib.mapper.arteitem import ArteVideoItem
from resources.lib.mapper.arteitem import ArteTvVideoItem
from resources.lib.mapper.arteitem import ArteHbbTvVideoItem
from resources.lib.mapper.arteitem import ArteCollectionItem
from resources.lib.mapper.artezone import ArteZone
from resources.lib.mapper.artefavorites import ArteFavorites
from resources.lib.mapper.artehistory import ArteHistory


def map_category_item(plugin, item, category_code):
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


def map_generic_item(plugin, item, show_video_streams):
    """Return entry menu for video or playlist"""
    if ArteVideoItem(plugin, item).is_playlist():
        item = ArteCollectionItem(plugin, item).map_collection_as_menu_item()
    elif show_video_streams is True:
        item = map_video_streams_as_menu(plugin, item)
    else:
        item = map_video_as_item(plugin, item)
    return item


def map_collection_as_playlist(plugin, arte_collection, req_start_program_id=None):
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
        xbmc_item = map_video_as_playlist_item(plugin, arte_item)
        if xbmc_item is None:
            break

        # search for the start item until it is found once
        if before_start:
            if req_start_program_id is None:
                # start from the first element not fully viewed
                if ArteTvVideoItem(plugin, arte_item).get_progress() < 0.95:
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
    return {
        'collection': items_after_start + items_before_start,
        'start_program_id': start_program_id
    }


def map_video_as_playlist_item(plugin, item):
    """
    Create a video menu item without recursiveness to fetch parent collection
    from a json returned by Arte HBBTV or ArteTV API
    """
    program_id = item.get('programId')
    kind = item.get('kind')
    if isinstance(kind, dict) and kind.get('code', False):
        kind = kind.get('code')

    path = plugin.url_for(
        'play_siblings', kind=kind, program_id=program_id, audio_slot='1', from_playlist='1')
    result = ArteVideoItem(plugin, item).build_item(path, True)
    return result


def map_video_streams_as_menu(plugin, item):
    """Create a menu item for video streams from a json returned by Arte HBBTV API"""
    program_id = item.get('programId')
    path = plugin.url_for('streams', program_id=program_id)
    return ArteHbbTvVideoItem(plugin, item).build_item(path, False)


def map_video_as_item(plugin, item):
    """Create a playable video menu item from a json returned by Arte HBBTV API"""
    program_id = item.get('programId')
    kind = item.get('kind')
    path = plugin.url_for('play', kind=kind, program_id=program_id)
    return ArteHbbTvVideoItem(plugin, item).build_item(path, True)


def map_streams(plugin, item, streams, quality):
    """Map JSON item and list of audio streams into a menu."""
    program_id = item.get('programId')
    kind = item.get('kind')

    video_item = map_video_as_item(plugin, item)

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


def map_zone_to_item(plugin, settings, zone, cached_categories):
    """Arte TV API page is split into zones. Map a 'zone' to menu item(s).
    Populate cached_categories for zones with videos available in child 'content'"""
    menu_item = None
    title = zone.get('title')
    if get_authenticated_content_type(zone) == 'sso-favorites':
        menu_item = ArteFavorites(plugin, settings).build_item(title)
    elif get_authenticated_content_type(zone) == 'sso-personalzone':
        menu_item = ArteHistory(plugin, settings).build_item(title)
    elif zone.get('content') and zone.get('content').get('data'):
        menu_item = ArteZone(plugin, settings, cached_categories).build_item(zone)
    elif zone.get('link'):
        menu_item = map_api_categories_item(plugin, zone)
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


def map_api_categories_item(plugin, item):
    """Return a menu entry to access content of category item.
    :param dict item: JSON node item
    """
    return {
        'label': item.get('title'),
        'path': plugin.url_for('api_category', category_code=item.get('link').get('page'))
    }


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


def match_hbbtv(stream, quality, audio_slot):
    """Return True if item from HHB TV API matches quality and audio_slot constraints,
    False otherwise"""
    return stream.get('quality') == quality and stream.get('audioSlot') == audio_slot


def match_artetv(stream, quality, audio_slot):
    """Return True if item from Arte TV API matches quality and audio_slot constraints,
    False otherwise"""
    return stream.get('mainQuality').get('code') == quality \
        and str(stream.get('slot')) == audio_slot
