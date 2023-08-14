"""Manage views like home menu, dynamic menus, search, favorites..."""
# pylint: disable=import-error
from xbmcswift2 import xbmc

from . import api
from . import hof
from . import mapper
from . import settings as stg


def build_home_page(cached_categories, settings):
    """Display home menu based on fixed entries and then content from API home page"""
    addon_menu = [
        mapper.create_search_item(),
    ]
    try:
        live_stream_data = api.player_video(settings.language, 'LIVE')
        live_stream_item = mapper.map_live_video(
            live_stream_data, settings.quality, '1')
        addon_menu.append(live_stream_item)
    # pylint: disable=broad-exception-caught
    # Could be improve. possible exceptions are limited to auth. errors
    except Exception:
        xbmc.log("Unable to build live stream item with " +
                 f"lang:{settings.language} quality:{settings.quality}")

    arte_home = api.page_content(settings.language)
    for zone in arte_home.get('zones'):
        menu_item = mapper.map_zone_to_item(zone, cached_categories)
        if menu_item:
            addon_menu.append(menu_item)
    return addon_menu


def build_api_category(category_code, settings):
    """Build the menu for a category that needs an api call"""
    category = [mapper.map_category_item(item, category_code) for item in
                api.category(category_code, settings.language)]

    return category


def get_cached_category(category_title, most_viewed_categories):
    """Return the menu for a category that is stored
    in cache from previous api call like home page"""
    return most_viewed_categories[category_title]


def build_favorites(plugin, settings):
    """Build the menu for user favorites thanks to API call"""
    return [mapper.map_artetv_item(item) for item in
            api.get_favorites(plugin, settings.language, settings.username, settings.password) or
            # display an empty list in case of error. error should be display in a notification
            []]


def add_favorite(plugin, usr, pwd, program_id, label):
    """Add content program_id to user favorites.
    Notify about completion success or failure with label."""
    if 200 == api.add_favorite(plugin, usr, pwd, program_id):
        msg = plugin.addon.getLocalizedString(30025).format(label=label)
        plugin.notify(msg=msg, image='info')
    else:
        msg = plugin.addon.getLocalizedString(30026).format(label=label)
        plugin.notify(msg=msg, image='error')


def remove_favorite(plugin, usr, pwd, program_id, label):
    """Remove content program_id from user favorites.
    Notify about completion success or failure with label."""
    if 200 == api.remove_favorite(plugin, usr, pwd, program_id):
        msg = plugin.addon.getLocalizedString(30027).format(label=label)
        plugin.notify(msg=msg, image='info')
    else:
        msg = plugin.addon.getLocalizedString(30028).format(label=label)
        plugin.notify(msg=msg, image='error')


def purge_favorites(plugin, usr, pwd):
    """Flush user favorites and notify about success or failure"""
    if 200 == api.purge_favorites(plugin, usr, pwd):
        plugin.notify(msg=plugin.addon.getLocalizedString(30037), image='info')
    else:
        plugin.notify(msg=plugin.addon.getLocalizedString(30038), image='error')


def mark_as_watched(plugin, usr, pwd, program_id, label):
    """
    Get program duration and synch progress with total duration
    in order to mark a program as watched
    """
    status = -1
    try:
        program_info = api.player_video(stg.languages[0], program_id)
        total_time = program_info.get('attributes').get('metadata').get('duration').get('seconds')
        status = api.sync_last_viewed(plugin, usr, pwd, program_id, total_time)
    # pylint: disable=broad-exception-caught
    except Exception as excp:
        xbmc.log(f" exception caught :{str(excp)}")

    if 200 == status:
        msg = plugin.addon.getLocalizedString(30034).format(label=label)
        plugin.notify(msg=msg, image='info')
    else:
        msg = plugin.addon.getLocalizedString(30035).format(label=label)
        plugin.notify(msg=msg, image='error')


def build_last_viewed(plugin, settings):
    """Build the menu of user history"""
    return [mapper.map_artetv_item(item) for item in
            api.get_last_viewed(plugin, settings.language, settings.username, settings.password) or
            # display an empty list in case of error. error should be display in a notification
            []]


def purge_last_viewed(plugin, usr, pwd):
    """Flush user history and notify about success or failure"""
    if 200 == api.purge_last_viewed(plugin, usr, pwd):
        plugin.notify(msg=plugin.addon.getLocalizedString(30031), image='info')
    else:
        plugin.notify(msg=plugin.addon.getLocalizedString(30032), image='error')


def build_mixed_collection(kind, collection_id, settings):
    """Build menu of content available in collection collection_id thanks to HBB TV API"""
    return [mapper.map_generic_item(item, settings.show_video_streams) for item in
            api.collection(kind, collection_id, settings.language)]


def build_video_streams(program_id, settings):
    """Build the menu with the audio streams available for content program_id"""
    item = api.video(program_id, settings.language)

    if item is None:
        raise RuntimeError('Video not found...')

    program_id = item.get('programId')
    kind = item.get('kind')

    return mapper.map_streams(
        item, api.streams(kind, program_id, settings.language), settings.quality)


def build_sibling_playlist(plugin, settings, program_id):
    """
    Return a pair with videos belonging to the same parent as program id
    e.g. other episodes of a same serie, videos around the same topic
    and the start program id of this collection i.e. program_id
    """
    parent_program = None
    # get parent of prefered kind first. for the moment TV_SERIES only
    for prefered_kind in mapper.PREFERED_KINDS:
        # pylint: disable=cell-var-from-loop
        parent_program = hof.find(
            lambda parent: api.is_of_kind(parent, prefered_kind),
            api.get_parent_collection(settings.language, program_id))
        if parent_program:
            break
    # if a parent was found, then return the list of kodi playable dict.
    if parent_program:
        sibling_arte_items = api.collection_with_last_viewed(
            plugin, settings.language, settings.username, settings.password,
            parent_program.get('kind'), parent_program.get('programId'))
        return mapper.map_collection_as_playlist(sibling_arte_items, program_id)
    return None

def build_collection_playlist(plugin, settings, kind, collection_id):
    """
    Return a pair with collection with collection_id
    and program id of the first element in the collection
    """
    return mapper.map_collection_as_playlist(api.collection_with_last_viewed(
        plugin, settings.language, settings.username, settings.password, kind, collection_id))

def build_stream_url(plugin, kind, program_id, audio_slot, settings):
    """
    Return URL to stream content.
    If the content is not available, it tries to return a related trailer or teaser.
    """
    # first try with content
    program_stream = api.streams(kind, program_id, settings.language)
    if program_stream:
        return mapper.map_playable(program_stream, settings.quality, audio_slot, mapper.match_hbbtv)
    # second try to fallback clip. It allows to display a trailer,
    # when a documentary is not available anymore like on arte tv website
    clip_stream = api.streams('CLIP', program_id, settings.language)
    if clip_stream:
        return mapper.map_playable(clip_stream, settings.quality, audio_slot, mapper.match_hbbtv)
    # otherwise raise the error
    msg = plugin.addon.getLocalizedString(30029)
    plugin.notify(msg=msg.format(strm=program_id, ln=settings.language), image='error')
    return None


def search(plugin, settings):
    """Display the keyboard to search for content. Then, display the menu of search results.
    Do not display an empty, if search is aborted or search for empty string"""
    query = get_search_query(plugin)
    if not query:
        plugin.end_of_directory(succeeded=False)
    return mapper.map_collection_as_menu(api.search(settings.language, query))


def get_search_query(plugin):
    """Display the keyboard to enter the search query and return it"""
    search_query = ''
    keyboard = xbmc.Keyboard(search_query, plugin.addon.getLocalizedString(30012))
    keyboard.doModal()
    if keyboard.isConfirmed() is False:
        return None
    search_query = keyboard.getText()
    if len(search_query) == 0:
        return None
    return search_query
