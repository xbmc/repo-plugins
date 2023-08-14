"""Main module for Kodi add-on plugin.video.arteplussept"""
# coding=utf-8
# -*- coding: utf-8 -*-
#
# plugin.video.arteplussept, Kodi add-on to watch videos from http://www.arte.tv/guide/fr/plus7/
# Copyright (C) 2015  known-as-bmf
# Copyright (C) 2023  thomas-ernest
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# https://xbmcswift2.readthedocs.io/en/latest/api.html
# https://github.com/XBMC-Addons/script.module.xbmcswift2
# pylint: disable=import-error
from xbmcswift2 import Plugin
# pylint: disable=import-error
from xbmcswift2 import xbmc
from resources.lib import user
from resources.lib import view
from resources.lib.player import Player
from resources.lib.settings import Settings

# global declarations
# plugin stuff
plugin = Plugin()

settings = Settings(plugin)


@plugin.route('/', name='index')
def index():
    """Display home menu"""
    return view.build_home_page(plugin.get_storage('cached_categories', TTL=60), settings)


@plugin.route('/api_category/<category_code>', name='api_category')
def api_category(category_code):
    """Display the menu for a category that needs an api call"""
    return view.build_api_category(category_code, settings)


@plugin.route('/cached_category/<category_code>', name='cached_category')
def cached_category(category_code):
    """Display the menu for a category that is stored
    in cache from previous api call like home page"""
    return view.get_cached_category(category_code, plugin.get_storage('cached_categories', TTL=60))


@plugin.route('/play_collection/<kind>/<collection_id>', name='play_collection')
def play_collection(kind, collection_id):
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
    result = plugin.set_resolved_url(plugin.add_to_playlist(playlist['collection'])[0])
    synch_during_playback(synched_player)
    del synched_player
    return result


@plugin.route('/favorites', name='favorites')
def favorites():
    """Display the menu for user favorites"""
    plugin.set_content('tvshows')
    return plugin.finish(view.build_favorites(plugin, settings))

@plugin.route('/add_favorite/<program_id>/<label>', name='add_favorite')
def add_favorite(program_id, label):
    """Add content program_id to user favorites.
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    view.add_favorite(plugin, settings.username, program_id, label)

@plugin.route('/remove_favorite/<program_id>/<label>', name='remove_favorite')
def remove_favorite(program_id, label):
    """Remove content program_id from user favorites
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    view.remove_favorite(plugin, settings.username, program_id, label)

@plugin.route('/purge_favorites', name='purge_favorites')
def purge_favroties():
    """Flush user history and notify about completion status"""
    view.purge_favorites(plugin, settings.username)


@plugin.route('/mark_as_watched/<program_id>/<label>', name='mark_as_watched')
def mark_as_watched(program_id, label):
    """Mark program as watched in Arte
    Notify about completion status with label,
    useful when several operations are requested in parallel."""
    view.mark_as_watched(plugin, settings.username, program_id, label)


@plugin.route('/last_viewed', name='last_viewed')
def last_viewed():
    """Display the menu of user history"""
    plugin.set_content('tvshows')
    return plugin.finish(view.build_last_viewed(plugin, settings))

@plugin.route('/purge_last_viewed', name='purge_last_viewed')
def purge_last_viewed():
    """Flush user history and notify about completion status"""
    view.purge_last_viewed(plugin, settings.username)


@plugin.route('/display_collection/<kind>/<program_id>', name='display_collection')
def display_collection(kind, program_id):
    """Display menu for collection of content"""
    plugin.set_content('tvshows')
    return plugin.finish(view.build_mixed_collection(kind, program_id, settings))


@plugin.route('/streams/<program_id>', name='streams')
def streams(program_id):
    """Play a multi language content."""
    return plugin.finish(view.build_video_streams(program_id, settings))

@plugin.route('/play_live/<stream_url>', name='play_live')
def play_live(stream_url):
    """Play live content."""
    return plugin.set_resolved_url({'path': stream_url})

# Cannot read video new arte tv program API. Blocked by FFMPEG issue #10149
# @plugin.route('/play_artetv/<program_id>', name='play_artetv')
# def play_artetv(program_id):
#     item = api.player_video(settings.language, program_id)
#     attr = item.get('attributes')
#     streamUrl=attr.get('streams')[0].get('url')
#     return plugin.set_resolved_url({'path': streamUrl})


@plugin.route('/play/<kind>/<program_id>', name='play')
@plugin.route('/play/<kind>/<program_id>/<audio_slot>', name='play_specific')
@plugin.route('/play/<kind>/<program_id>/<audio_slot>/<from_playlist>', name='play_siblings')
def play(kind, program_id, audio_slot='1', from_playlist='0'):
    """Play content identified with program_id.
    :param str kind: an enum in TODO (e.g. TRAILER, COLLECTION, LINK, CLIP, ...)
    :param str audio_slot: a numeric to identify the audio stream to use e.g. 1 2
    """
    synched_player = Player(user.get_cached_token(plugin, settings.username, True), program_id)
    # try to seek parent collection, when out of the context of playlist creation
    sibling_playlist = None
    if from_playlist == '0':
        sibling_playlist = view.build_sibling_playlist(plugin, settings, program_id)
    if sibling_playlist is not None and len(sibling_playlist['collection']) > 1:
        # Empty playlist, otherwise requested video is present twice in the playlist
        xbmc.PlayList(xbmc.PLAYLIST_VIDEO).clear()
        # Start playing with the first playlist item
        result = plugin.set_resolved_url(plugin.add_to_playlist(sibling_playlist['collection'])[0])
    else:
        item = view.build_stream_url(plugin, kind, program_id, int(audio_slot), settings)
        result = plugin.set_resolved_url(item)
    synch_during_playback(synched_player)
    del synched_player
    return result


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


@plugin.route('/search', name='search')
def search():
    """Display the keyboard to search for content. Then, display the menu of search results"""
    plugin.set_content('tvshows')
    return plugin.finish(view.search(plugin, settings))


@plugin.route('/user/login', name='user_login')
def user_login():
    """Login user with email already set in settings by creating and persisting a token."""
    return plugin.finish(succeeded=user.login(plugin, settings))

@plugin.route('/user/logout', name='user_logout')
def user_logout():
    """Discard token of user in settings."""
    return plugin.finish(succeeded=user.logout(plugin, settings))

# plugin bootstrap
if __name__ == '__main__':
    plugin.run()
