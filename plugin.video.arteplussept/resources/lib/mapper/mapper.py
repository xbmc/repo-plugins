"""Map JSON API outputs into playable content and menus for Kodi"""
import xbmc
from resources.lib import api
from resources.lib.extended_program_data import ExtendedProgramData, enrich_program_data
from resources.lib.mapper.arteitem import ArteTvVideoItem
from resources.lib.mapper.artezone import ArteZone
from resources.lib.mapper.artefavorites import ArteFavorites
from resources.lib.mapper.artehistory import ArteHistory
from resources.lib.mapper.arteliveitem import ArteLiveItem
from resources.lib.mapper.artesearch import ArteSearch


def build_video_from_program(plugin, settings, prgm_id, col_id=None):
    """
    Build a full playable video with metadata from a single program.
    """
    path = None
    if prgm_id:
        full_prgm = api.player_video(settings.language, prgm_id)
        if col_id:
            path = build_path_for_menu(plugin, col_id, prgm_id)
        else:
            path = build_path_for_playlist(full_prgm)
    if path:
        prgm_attr = full_prgm.get('attributes', {}).get('metadata', {})
        prgm_attr = enrich_program_data(
            prgm_attr, ExtendedProgramData(plugin, settings).get(prgm_id)
        )
        builder = ArteTvVideoItem(plugin, prgm_attr)
        li = builder.build_item(path, True)
        builder.set_tracking_properties(li, full_prgm.get('attributes', {}).get('stat', {}))
        return li
    return None


def build_path_for_menu(plugin, col_id, prgm_id):
    """Build path to point to playing a program in a collection"""
    return plugin.url_for('play_collection_from', col_id=col_id, prgm_id=prgm_id, mpaa='Unknown')


def build_path_for_playlist(full_prgm):
    """Build path to a playable multi lang video"""
    path = ''
    streams = full_prgm.get('attributes', {}).get('streams', [])
    if len(streams) > 0:
        path = streams[0].get('url', None)
    return path


def map_zone_to_item(plugin, settings, zone):
    """Arte TV API page is split into zones. Map a 'zone' to menu item(s).
    Never use cache, because we cannot store ListItem in it"""
    menu_item = None
    title = zone.get('title')
    if get_authenticated_content_type(zone) == 'sso-favorites':
        menu_item = ArteFavorites(plugin, settings).build_item(title)
    elif get_authenticated_content_type(zone) == 'sso-personalzone':
        menu_item = ArteHistory(plugin, settings).build_item(title)
    elif zone.get('content') and zone.get('content').get('data'):
        menu_item = ArteZone(plugin, settings).build_item(zone)
    else:
        xbmc.log(
            f"Ignore zone \"{title}\". No link. No content. Unknown id.",
            level=xbmc.LOGINFO)

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


def build_home_page(plugin, settings):
    """Display home menu based on fixed entries and then content from API home page"""
    addon_menu = [
        ArteSearch(plugin, settings).build_item()
    ]
    try:
        addon_menu.append(
            ArteLiveItem(plugin, api.player_video(settings.language, 'LIVE'))
            .build_item_live())
    # pylint: disable=broad-exception-caught
    except Exception as error:
        xbmc.log("Unable to build live stream item with " +
                 f"because \"{str(error)}\"",
                 level=xbmc.LOGERROR)

    try:
        arte_home = api.page_content(settings.language)
        for zone in arte_home.get('zones'):
            menu_item = map_zone_to_item(plugin, settings, zone)
            if menu_item:
                addon_menu.append(menu_item)
    # pylint: disable=broad-exception-caught
    except Exception as error:
        xbmc.log("Unable to build home items with " +
                 f"because \"{str(error)}\"",
                 level=xbmc.LOGERROR)

    return addon_menu


def build_page(plugin, settings, category):
    """
    Build a page for a category like SER, CIN, DOR...
    A page is a list of zones.
    To be extended to HOME.
    """
    page = api.page_content(settings.language, category)
    page_menu = []
    for zone in page.get('zones', []):
        page_item = ArteZone(plugin, settings).build_item(zone)
        if page_item:
            page_menu.append(page_item)
    return page_menu


def build_menu_from_collection(plugin, settings, collection_id):
    """
    Build a playlist from artetv playlist api with multi lang streams
    """
    playlist = api.playlist_collection(settings.language, collection_id)
    menu = []
    extended_programs = ExtendedProgramData(plugin, settings).get_all()
    for pl_prgm in playlist.get('attributes', {}).get('items', {}):
        prgm_id = pl_prgm.get('providerId', None)
        if prgm_id:
            path = plugin.url_for('play', program_id=prgm_id, mpaa='Unknown')
            item_data = enrich_program_data(
                pl_prgm, extended_programs.get(prgm_id, {})
            )
            li = ArteTvVideoItem(plugin, item_data).build_item(path, True)
            if li:
                menu.append(li)
    return menu


def build_playlist_from_collection(plugin, settings, collection_id, menu=False):
    """
    Build a playlist from artetv playlist api with multi lang streams
    """
    playlist = api.playlist_collection(settings.language, collection_id)
    collection = []
    prgm_id_to_pos = {}
    pos_to_prgm_id = []
    for pl_prgm in playlist.get('attributes', {}).get('items', {}):
        prgm_id = pl_prgm.get('providerId', None)
        if prgm_id:
            col_id_if_menu = collection_id if menu else None
            prgm_itm = build_video_from_program(plugin, settings, prgm_id, col_id_if_menu)
            if prgm_itm:
                collection.append(prgm_itm)
                pos = len(pos_to_prgm_id)
                if prgm_id_to_pos.get(prgm_id, False):
                    xbmc.log(
                        f"Duplicated program {prgm_id} in playlist {collection_id}",
                        xbmc.LOGWARNING)
                prgm_id_to_pos[prgm_id] = pos
                pos_to_prgm_id.append(prgm_id)
    return {'collection': collection,
            'prgm_id_to_pos': prgm_id_to_pos,
            'pos_to_prgm_id': pos_to_prgm_id
            }


def get_collection_resume_position(
        items, program_id_to_pos, program_id=None, collection_id=None):
    """Choose explicit episode first, otherwise resume the collection history."""
    default_completed_threshold = 0.95
    default_start_position = -1
    if program_id:
        if program_id in program_id_to_pos:
            position = program_id_to_pos[program_id]
            xbmc.log(
                f"Starting collection {collection_id} at requested program "
                f"{program_id}, playlist position {position}.",
                xbmc.LOGDEBUG,
            )
            return position
        xbmc.log(
            f"Unable to find program {program_id} in collection {collection_id}. "
            "Falling back to automatic resume.",
            xbmc.LOGERROR,
        )

    items_progress = []
    for item in items:
        start_offset = item.getProperty('arte_start_offset')
        try:
            progress = float(start_offset) / float(item.getVideoInfoTag().getDuration()) \
                if start_offset else None
        except (TypeError, ValueError, OverflowError):
            progress = None
        # normalize progress, to keep the same number and
        # order between progress_values and items
        if progress is not None:
            progress = max(0.0, min(progress, 1.0))
        else:
            progress = 0.0
        items_progress.append(progress)

    for position, progress in enumerate(items_progress):
        if 0.0 <= progress < default_completed_threshold:
            xbmc.log(
                f"Automatically resuming collection {collection_id} at playlist "
                f"position {position} ({progress * 100:.1f}%).",
                xbmc.LOGDEBUG,
            )
            return position

    xbmc.log(
        f"No program id forced and all items in collection {collection_id} exceed "
        f"{default_completed_threshold * 100:.1f}%; "
        f"keeping default start position {default_start_position}.",
        xbmc.LOGDEBUG,
    )
    return default_start_position


def build_playable_playlist(playlist):
    """
    Convert a list of listitem into a playable video playlist
    """
    # Empty playlist, otherwise requested video is present twice in the playlist
    # xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    for item in playlist or []:
        pl.add(item.getPath(), item)
    return pl
