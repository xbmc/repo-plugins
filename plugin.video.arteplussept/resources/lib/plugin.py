"""Main module for Kodi add-on plugin.video.arteplussept"""

from datetime import date
import xbmcaddon
import xbmcgui
# pylint: disable=import-error
from xbmcswift2 import Plugin
# pylint: disable=import-error
from xbmcswift2 import xbmc
from resources.lib import logger
from resources.lib import user
from resources.lib import view
from resources.lib.mapper.artefavorites import ArteFavorites
from resources.lib.mapper.artehistory import ArteHistory
from resources.lib.mapper.artesearch import ArteSearch
from resources.lib.mapper.artezone import ArteZone
from resources.lib.player import Player
from resources.lib.settings import Settings
from resources.lib import utils
from resources.lib.utils import PlayFrom

DATE_FORMAT = "%Y-%m-%d"

plugin = Plugin()
settings = Settings(plugin)


@plugin.route('/', name='index')
def display_index():
    """
    Display home menu. On every new version, display a dialog box
    to remind users where to donate and report issues.
    """
    addon = xbmcaddon.Addon()
    current_version = addon.getAddonInfo("version")
    last_version = addon.getSetting("last_version_notified")
    last_date = addon.getSetting("last_date_notified")

    if last_version != current_version or days_since(last_date) >= 30:
        xbmcgui.Dialog().ok(
            addon.getLocalizedString(30061).format(version=current_version),
            addon.getLocalizedString(30062).format(version=current_version)
        )
        addon.setSetting("last_version_notified", current_version)
        addon.setSetting("last_date_notified", date.today().strftime(DATE_FORMAT))

    lst_itms = view.build_home_page(
        plugin, settings, plugin.get_storage('cached_categories', TTL=60))
    logger.log_xbmc(lst_itms, 'index')
    return lst_itms


def days_since(date_str):
    """
    date_str: '2026-08-14' or '' (empty)
    Returns number of days between today and date_str.
    If empty → MAX_INT.
    """

    if not date_str:
        return 1000000

    try:
        other = date.fromisoformat(date_str)
    except ValueError:
        # invalid format, not a date
        return 1000000

    today = date.today()
    return (today - other).days


@plugin.route('/category/api/<category_code>', name='api_category')
def display_api_category(category_code):
    """Display the menu for a category that needs an api call"""
    lst_itms = view.build_api_category(plugin, category_code, settings)
    logger.log_xbmc(lst_itms, 'api_category')
    return lst_itms


@plugin.route('/category/cached/<zone_id>', name='cached_category')
def display_cached_category(zone_id):
    """Display the menu for a category that is stored
    in cache from previous api call like home page"""
    lst_itms = view.get_cached_category(
        plugin, settings, zone_id, plugin.get_storage('cached_categories', TTL=60))
    logger.log_xbmc(lst_itms, 'cached_category')
    return lst_itms


@plugin.route('/category/page/<zone_id>/<page>/<page_id>', name='category_page')
def display_category_page(zone_id, page, page_id):
    """Display the menu for a category that needs an api call"""
    lst_itms = ArteZone(plugin, settings, plugin.get_storage('cached_categories', TTL=60)) \
        .build_menu(zone_id, page, page_id)
    logger.log_xbmc(lst_itms, 'category_page')
    return lst_itms


@plugin.route('/raw_page/<category>', name='raw_page')
def display_raw_page(category):
    """Display the menu for a category that needs an api call"""
    lst_itms = view.build_page(plugin, settings, category)
    xbmc.log(f"all my lst_itms {lst_itms}", xbmc.LOGWARNING)
    logger.log_xbmc(lst_itms, 'raw_page')
    return lst_itms


@plugin.route('/favorites', name='favorites_default')
@plugin.route('/favorites/<page>', name='favorites')
def display_favorites(page=1):
    """Display the menu for user favorites"""
    lst_itms = ArteFavorites(plugin, settings).build_menu(page)
    logger.log_xbmc(lst_itms, 'favorites')
    return lst_itms


@plugin.route('/add_favorite/<program_id>/<label>', name='add_favorite')
def add_favorite(program_id, label):
    """Add content program_id to user favorites.
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    ArteFavorites(plugin, settings).add_favorite(program_id, label)


@plugin.route('/remove_favorite/<program_id>/<label>', name='remove_favorite')
def remove_favorite(program_id, label):
    """Remove content program_id from user favorites
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    ArteFavorites(plugin, settings).remove_favorite(program_id, label)


@plugin.route('/purge_favorites', name='purge_favorites')
def purge_favroties():
    """Flush user history and notify about completion status"""
    ArteFavorites(plugin, settings).purge()


@plugin.route('/mark_as_watched/<program_id>/<label>', name='mark_as_watched')
def mark_as_watched(program_id, label):
    """Mark program as watched in Arte
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    view.mark_as_watched(plugin, settings.username, program_id, label)


@plugin.route('/last_viewed', name='last_viewed_default')
@plugin.route('/last_viewed/<page>', name='last_viewed')
def display_last_viewed(page=1):
    """Display the menu of user history"""
    lst_itms = ArteHistory(plugin, settings).build_menu(page)
    logger.log_xbmc(lst_itms, 'last_viewed')
    return lst_itms


@plugin.route('/purge_last_viewed', name='purge_last_viewed')
def purge_last_viewed():
    """Flush user history and notify about completion status"""
    ArteHistory(plugin, settings).purge()


@plugin.route('/collection/<kind>/<program_id>', name='collection')
def display_collection(kind, program_id):
    """Display menu for collection of content"""
    lst_itms = view.build_mixed_collection(plugin, kind, program_id, settings)
    logger.log_xbmc(lst_itms, 'collection')
    return lst_itms


@plugin.route('/streams/<program_id>', name='streams')
def display_streams(program_id):
    """Play a multi language content."""
    lst_itms = view.build_video_streams(plugin, settings, program_id)
    logger.log_xbmc(lst_itms, 'streams')
    return lst_itms


@plugin.route('/play_live/<stream_url>/<mpaa>', name='play_live')
def play_live(stream_url, mpaa):
    """Play live content."""
    utils.warn_if_age_restricted(plugin, mpaa)
    lst_itm = {'path': stream_url}
    logger.log_xbmc(lst_itm, 'play_live')
    return plugin.set_resolved_url(lst_itm)

# Cannot read video new arte tv program API. Blocked by FFMPEG issue #10149
# @plugin.route('/play_artetv/<program_id>', name='play_artetv')
# def play_artetv(program_id):
#     item = api.player_video(settings.language, program_id)
#     attr = item.get('attributes')
#     streamUrl=attr.get('streams')[0].get('url')
#     return plugin.set_resolved_url({'path': streamUrl})


def synch_during_playback(synched_player):
    """Manage timeframe to send synchronization events to Arte TV API"""
    # wait 1s first to give a chance for playback to start
    # otherwise synched_player won't be able to listen
    xbmc.sleep(500)
    # start at 0 to synch progress at start-up
    i = 1
    # keep current method stack up to keep event callbacks up
    while synched_player.is_playback():
        # synch progress to Arte TV every minute, as on website
        if i % 60 == 0:
            synched_player.synch_progress()
        i += 1
        xbmc.sleep(1000)
    synched_player.synch_progress()


@plugin.route('/play/<kind>/<program_id>/<mpaa>', name='play')
@plugin.route('/play/<kind>/<program_id>/<mpaa>/<play_from>', name='play_from')
@plugin.route('/play/<kind>/<program_id>/<mpaa>/<play_from>/<audio_slot>', name='play_specific')
def play(kind, program_id, mpaa, play_from=PlayFrom.ITM, audio_slot='1'):
    """Play content identified with program_id.
    :param str kind: an enum in TODO (e.g. TRAILER, COLLECTION, LINK, CLIP, ...)
    :param str audio_slot: a numeric to identify the audio stream to use e.g. 1 2
    """
    synched_player = Player(user.get_cached_token(plugin, settings.username, True), program_id)
    # try to seek parent collection, when out of the context of playlist creation
    sibling_playlist = None
    if play_from == PlayFrom.LST.value:
        sibling_playlist = view.build_sibling_playlist(plugin, settings, program_id)
    played_item = None
    if sibling_playlist is not None and len(sibling_playlist['collection']) > 1:
        # Empty playlist, otherwise requested video is present twice in the playlist
        xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
        # Start playing with the first playlist item
        played_item = plugin.add_to_playlist(sibling_playlist['collection'])[0]
        logger.log_xbmc(played_item, 'play')
        result = plugin.set_resolved_url()
    else:
        played_item = view.build_stream_url(plugin, settings, kind, program_id, int(audio_slot))
        logger.log_xbmc(played_item, 'play')
        if play_from == PlayFrom.CTX.value:
            result = plugin.play_video(played_item)
        else:
            result = plugin.set_resolved_url(played_item)
    utils.warn_if_age_restricted(plugin, mpaa)

    synch_during_playback(synched_player)
    del synched_player
    return result


@plugin.route('/play_collection/<kind>/<collection_id>/<mpaa>', name='play_collection')
def play_collection(kind, collection_id, mpaa):
    """
    Load a playlist and start playing its first item.
    """
    playlist = view.build_collection_playlist(plugin, settings, kind, collection_id)

    # Empty playlist, otherwise requested video is present twice in the playlist
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    # Start playing with the first playlist item
    synched_player = Player(
        user.get_cached_token(plugin, settings.username, True),
        playlist['start_program_id'])
    # try to seek parent collection, when out of the context of playlist creation
    # Start playing with the first playlist item
    played_item = plugin.add_to_playlist(playlist['collection'])[0]
    logger.log_xbmc(played_item, 'play_collection')
    result = plugin.set_resolved_url(played_item)
    utils.warn_if_age_restricted(plugin, mpaa)
    synch_during_playback(synched_player)
    del synched_player
    return result


@plugin.route('/search', name='init_search')
def init_search():
    """Display the keyboard to search for content.
    Then, display the first page of search results"""
    lst_itms = ArteSearch(plugin, settings).init_search()
    logger.log_xbmc(lst_itms, 'search')
    return lst_itms


@plugin.route('/search/<zone_id>/<page>/<query>', name='search')
def display_search_page(zone_id, page, query):
    """Display a given page of search results"""
    lst_itms = ArteSearch(plugin, settings).get_search_page(zone_id, page, query)
    logger.log_xbmc(lst_itms, 'search')
    return lst_itms


@plugin.route('/user/login', name='user_login')
def user_login():
    """Login user with email already set in settings by creating and persisting a token."""
    return plugin.finish(succeeded=user.login(plugin))


@plugin.route('/user/logout', name='user_logout')
def user_logout():
    """Discard token of user in settings."""
    return plugin.finish(succeeded=user.logout(plugin, settings))


# plugin bootstrap
if __name__ == '__main__':
    plugin.run()
