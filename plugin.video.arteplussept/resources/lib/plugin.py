"""Main module for Kodi add-on plugin.video.arteplussept"""

from datetime import date
from typing import Final
import traceback
import json

import xbmcaddon
import xbmcgui
import xbmc

from resources.lib import logger
from resources.lib import user
from resources.lib import utils
from resources.lib import api
from resources.lib.mapper import mapper
from resources.lib.mapper.artefavorites import ArteFavorites
from resources.lib.mapper.artehistory import ArteHistory
from resources.lib.mapper.arteliveitem import ArteLiveItem
from resources.lib.mapper.artesearch import ArteSearch
from resources.lib.mapper.artezone import ArteZone
from resources.lib.native_plugin import Plugin
from resources.lib.player import Player
from resources.lib.settings import Settings

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

    lst_itms = mapper.build_home_page(plugin, settings)
    logger.log_xbmc(lst_itms, 'index')
    user.update_login_state_settings(plugin, settings.username)
    return lst_itms


def days_since(date_str):
    """
    date_str: '2026-08-14' or '' (empty)
    Returns number of days between today and date_str.
    """
    try:
        # parse YYYY-MM-DD
        other = date.fromisoformat(date_str)
    except (TypeError, ValueError):
        # invalid format or not a date
        return 1000000

    today = date.today()
    return (today - other).days


@plugin.route('/category/page/<zone_id>/<page>/<page_id>', name='category_page')
def display_category_page(zone_id, page, page_id):
    """Display the menu for a category that needs an api call"""
    lst_itms = ArteZone(plugin, settings) \
        .build_menu(zone_id, page, page_id)
    logger.log_xbmc(lst_itms, 'category_page')
    return lst_itms


@plugin.route('/raw_page/<category>', name='raw_page')
def display_raw_page(category):
    """Display the menu for a category that needs an api call"""
    lst_itms = mapper.build_page(plugin, settings, category)
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


@plugin.route('/mark_as_watched/<program_id>/<label>', name='mark_as_watched')
def mark_as_watched(program_id, label):
    """Mark program as watched in Arte
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    ArteHistory(plugin, settings).mark_as_watched(program_id, label)


@plugin.route('/collection/<program_id>', name='collection')
def display_collection(program_id):
    """Display menu for collection of content"""
    lst_itms = mapper.build_playlist_from_collection(
        plugin, settings, program_id, menu=True)['collection']
    logger.log_xbmc(lst_itms, 'collection')
    return lst_itms


@plugin.route('/play/live/<stream_url>/<mpaa>', name='play_live')
def play_live(stream_url, mpaa):
    """Play live content."""
    if not plugin_operate(plugin, 'inputstream.adaptive'):
        addon = xbmcaddon.Addon()
        plugin.notify(addon.getLocalizedString(30034).format(strm=stream_url), image='error')
        return None
    utils.warn_if_age_restricted(plugin, mpaa)
    live_item = ArteLiveItem(plugin, api.player_video(settings.language, 'LIVE')).build_item_live()
    live_item.setPath(stream_url)
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    xbmc.Player().play(stream_url, live_item)
    return True


@plugin.route('/play/<program_id>/<mpaa>', name='play')
def play(program_id, mpaa):
    """
    Play content identified with program_id.
    """
    if not plugin_operate(plugin, 'inputstream.adaptive'):
        addon = xbmcaddon.Addon()
        plugin.notify(addon.getLocalizedString(30034).format(strm=program_id), image='error')
        return None
    synched_player = Player(user.get_cached_token(plugin, settings.username, True), program_id)
    played_item = None
    try:
        played_item = mapper.build_video_from_program(plugin, settings, program_id)
    # pylint: disable=broad-exception-caught
    except Exception as exp:
        stack_trace = traceback.format_tb(exp.__traceback__)
        xbmc.log(f"Exception during stream resolution {stack_trace}", xbmc.LOGERROR)
    if played_item:
        logger.log_xbmc(played_item, 'play')
        utils.warn_if_age_restricted(plugin, mpaa)
        xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
        xbmc.Player().play(played_item.getPath(), played_item)
        synch_during_playback(synched_player)
    else:
        xbmc.log("Could not resolve stream...", xbmc.LOGERROR)
        addon = xbmcaddon.Addon()
        plugin.notify(addon.getLocalizedString(30029).format(strm=program_id, ln='no'))

    del synched_player
    return True


@plugin.route('/play/collection/<col_id>/<mpaa>', name='play_collection')
@plugin.route('/play/collection/<col_id>/<mpaa>/from/<prgm_id>', name='play_collection_from')
def play_collection(col_id, mpaa, prgm_id=None):
    """
    Load a playlist and start playing its first item.
    """
    if not plugin_operate(plugin, 'inputstream.adaptive'):
        addon = xbmcaddon.Addon()
        plugin.notify(addon.getLocalizedString(30034).format(strm=col_id), image='error')
        return None
    # Empty playlist, otherwise requested video is present twice in the playlist
    xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
    playlist = mapper.build_playlist_from_collection(plugin, settings, col_id)
    # make sure there is a playlist
    if not playlist or not playlist['collection'] or len(playlist['collection']) <= 0:
        xbmc.log(f"Unable to fetch collection {col_id} to play it", xbmc.LOGERROR)
        addon = xbmcaddon.Addon()
        plugin.notify(addon.getLocalizedString(30029).format(strm=col_id, ln='no'))
        return None
    # set start position with or without program id
    # pylint: disable=invalid-name
    DEFAULT_START_POS: Final[int] = -1
    startpos = DEFAULT_START_POS
    if prgm_id:
        startpos = playlist['prgm_id_to_pos'].get(prgm_id, DEFAULT_START_POS)
        if DEFAULT_START_POS == startpos:
            xbmc.log(f"Unable to find program {prgm_id} in collection {col_id}. " +
                     f"Starting from {startpos}", xbmc.LOGERROR)

    # Start playing with the first playlist item
    # Disabling playback synchronization because it is not working
    # ensured that the synched_player is created with the program id of the item being played
    # when playing a collection
    # synched_player = Player(
    #    user.get_cached_token(plugin, settings.username, True), prgm_id)
    # try to seek parent collection, when out of the context of playlist creation
    # Start playing with the first playlist item
    played_item = mapper.build_playable_playlist(playlist['collection'])
    logger.log_xbmc(played_item, 'play_collection')
    utils.warn_if_age_restricted(plugin, mpaa)
    xbmc.Player().play(played_item, startpos=startpos)
    # synch_during_playback(synched_player)
    # del synched_player
    return True


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


def plugin_operate(my_plugin, marking):
    """Enforce inputstream adaptive plugin is installed and activated"""
    addon = xbmcaddon.Addon()
    # pylint: disable=line-too-long
    check_uno = xbmc.executeJSONRPC(f'{{"jsonrpc":"2.0","id":1,"method":"Addons.GetAddonDetails","params":{{"addonid":"{marking}","properties":["enabled"]}}}}') # noqa E501
    answer_uno = json.loads(check_uno)
    answer_due = json.loads(f'{{"error": "{marking} NOT FOUND"}}')
    answer_uno_ok = answer_uno.get('result', {}).get('addon', {}).get('enabled', False) is True
    if "error" not in answer_uno.keys() and not answer_uno_ok:
        try:
            # pylint: disable=line-too-long
            xbmc.executeJSONRPC(f'{{"jsonrpc":"2.0","id":1,"method":"Addons.SetAddonEnabled","params":{{"addonid":"{marking}","enabled":true}}}}') # noqa E501
            xbmc.log("(common.plugin_operate) ERROR - ACTIVATED - ERROR :\n" +
                     f"##### Das benötigte Addon : *{marking}* ist NICHT aktiviert !!! #####\n" +
                     "##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####",
                     xbmc.LOGERROR)
        # pylint: disable=broad-exception-caught
        except Exception:
            pass
        del answer_due
        # pylint: disable=line-too-long
        check_due = xbmc.executeJSONRPC(f'{{"jsonrpc":"2.0","id":1,"method":"Addons.GetAddonDetails","params":{{"addonid":"{marking}","properties":["enabled"]}}}}') # noqa E501
        answer_due = json.loads(check_due)
    answer_due_ok = answer_due.get('result', {}).get('addon', {}).get('enabled', False) is True
    if answer_uno_ok or answer_due_ok:
        return True
    if not answer_due_ok:
        my_plugin.notify(addon.getLocalizedString(30034).format(strm='n/a'))
        xbmc.log("(common.plugin_operate) ERROR - ACTIVATED - ERROR :\n" +
                 f"##### Das benötigte Addon : *{marking}* ist NICHT aktiviert !!! #####\n" +
                 "##### Eine automatische Aktivierung ist leider NICHT möglich !!! #####",
                 xbmc.LOGERROR)
    if "error" in answer_uno.keys() or "error" in answer_due.keys():
        my_plugin.notify(addon.getLocalizedString(30034).format(strm='n/a'))
        xbmc.log("(common.plugin_operate) ERROR - INSTALLED - ERROR :\n" +
                 f"##### Das benötigte Addon : *{marking}* ist NICHT installiert !!! #####",
                 xbmc.LOGERROR)
    return False


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
    return user.login(plugin)


@plugin.route('/user/logout', name='user_logout')
def user_logout():
    """Discard token of user in settings."""
    return user.logout(plugin)


# plugin bootstrap
if __name__ == '__main__':
    plugin.run()
