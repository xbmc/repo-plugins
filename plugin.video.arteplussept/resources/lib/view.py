"""Manage views like home menu, dynamic menus, search, favorites..."""
# pylint: disable=import-error
from xbmcswift2 import xbmc

from . import api
from . import mapper


def build_home_page(cached_categories, settings):
    """Display home menu based on fixed entries and then content from API home page"""
    addon_menu = [
        mapper.create_search_item(),
    ]
    try:
        live_stream_data = api.program_video(settings.language, 'LIVE')
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
    return [mapper.map_artetv_video(item) for item in
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


def build_last_viewed(plugin, settings):
    """Build the menu of user history"""
    return [mapper.map_artetv_video(item) for item in
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


def build_stream_url(plugin, kind, program_id, audio_slot, settings):
    """Return URL to stream content"""
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
    return mapper.map_cached_categories(
        api.search(settings.language, query))


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
