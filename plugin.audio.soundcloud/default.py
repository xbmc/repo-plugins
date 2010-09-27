'''
Created on Sep 4, 2010
@author: Zsolt Török

Copyright (C) 2010 Zsolt Török
 
This file is part of XBMC SoundCloud Plugin.

XBMC SoundCloud Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

XBMC SoundCloud Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with XBMC SoundCloud Plugin.  If not, see <http://www.gnu.org/licenses/>.

'''
import sys
import xbmc, xbmcgui, xbmcplugin
import xbmcsc.client as client
import urllib
from xbmcsc.client import SoundCloudClient

# plugin related constants
PLUGIN_URL = 'plugin://music/SoundCloud/'

# XBMC plugin modes
MODE_GROUPS = 0
MODE_GROUPS_MENU = 1
MODE_GROUPS_FAVORITES = 2
MODE_GROUPS_SEARCH = 3
MODE_GROUPS_HOTTEST = 4
MODE_GROUPS_TRACKS = 5

MODE_TRACKS = 10
MODE_TRACKS_MENU = 11
MODE_TRACKS_FAVORITES = 12
MODE_TRACKS_SEARCH = 13
MODE_TRACKS_HOTTEST = 14
MODE_TRACK_PLAY = 15

MODE_USERS = 20
MODE_USERS_MENU = 21
MODE_USERS_FAVORITES = 22
MODE_USERS_SEARCH = 23
MODE_USERS_HOTTEST = 24
MODE_USERS_TRACKS = 25

# Parameter keys
PARAMETER_KEY_OFFSET = u'offset'
PARAMETER_KEY_LIMIT = u'limit'
PARAMETER_KEY_MODE = u'mode'
PARAMETER_KEY_URL = u'url'
PARAMETER_KEY_PERMALINK = u'permalink'

handle = int(sys.argv[1])
soundcloud_client = SoundCloudClient()

def addDirectoryItem(name, label2='', infoType="Music", infoLabels={}, isFolder=True, parameters={}):
    ''' Add a list item to the XBMC UI.'''
    li = xbmcgui.ListItem(name, label2)
    if not infoLabels:
        infoLabels = {"Title": name }

    li.setInfo(infoType, infoLabels)
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

def show_tracks_menu():
    ''' Show the Tracks menu. '''
    addDirectoryItem(name="Hottest", parameters={PARAMETER_KEY_URL: PLUGIN_URL + "tracks/hottest", PARAMETER_KEY_MODE: MODE_TRACKS_HOTTEST}, isFolder=True)
    addDirectoryItem(name="Search", parameters={PARAMETER_KEY_URL: PLUGIN_URL + "tracks/search", PARAMETER_KEY_MODE: MODE_TRACKS_SEARCH}, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_users_menu():
    ''' Show the Users menu. '''
    addDirectoryItem(name="Hottest", parameters={PARAMETER_KEY_URL: PLUGIN_URL + "users/hottest", PARAMETER_KEY_MODE: MODE_USERS_HOTTEST}, isFolder=True)
    addDirectoryItem(name="Search", parameters={PARAMETER_KEY_URL: PLUGIN_URL + "users/search", PARAMETER_KEY_MODE: MODE_USERS_SEARCH}, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_groups_menu():
    ''' Show the Groups menu. '''
    addDirectoryItem(name="Hottest", parameters={PARAMETER_KEY_URL: PLUGIN_URL + "groups/hottest", PARAMETER_KEY_MODE: MODE_GROUPS_HOTTEST}, isFolder=True)
    addDirectoryItem(name="Search", parameters={PARAMETER_KEY_URL: PLUGIN_URL + "groups/search", PARAMETER_KEY_MODE: MODE_GROUPS_SEARCH}, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_tracks(tracks, parameters={}):
    ''' Show a list of tracks. A 'More...' item is added, 
        if there are more items available, then what is currently listed. '''
    xbmcplugin.setContent(handle, "songs")
    for track in tracks:
        li = xbmcgui.ListItem(label=track[client.TRACK_TITLE], thumbnailImage=track[client.TRACK_ARTWORK_URL])
        li.setInfo("music", { "title": track[client.TRACK_TITLE], "genre": track.get(client.TRACK_GENRE, "") })
        li.setProperty("mimetype", 'audio/mpeg')
        li.setProperty("IsPlayable", "true")
        track_parameters = { PARAMETER_KEY_MODE: MODE_TRACK_PLAY, PARAMETER_KEY_URL: PLUGIN_URL + "tracks/" + track[client.TRACK_PERMALINK], "permalink": track[client.TRACK_PERMALINK] }
        url = sys.argv[0] + '?' + urllib.urlencode(track_parameters)
        ok = xbmcplugin.addDirectoryItem(handle, url=url, listitem=li, isFolder=False)
    if not len(tracks) < parameters[PARAMETER_KEY_LIMIT]:
        modified_parameters = parameters.copy()
        modified_parameters[PARAMETER_KEY_OFFSET] = str(int(parameters[PARAMETER_KEY_OFFSET]) + int(parameters[PARAMETER_KEY_LIMIT]))
        addDirectoryItem(name="More...", parameters=modified_parameters, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def play_track(id):
    ''' Start to stream the track with the given id. '''
    track = soundcloud_client.get_track(id)
    li = xbmcgui.ListItem(label=track[client.TRACK_TITLE], thumbnailImage=track.get(client.TRACK_ARTWORK_URL, ""), path=track[client.TRACK_STREAM_URL])
    li.setInfo("music", { "title": track[client.TRACK_TITLE], "genre": track.get(client.TRACK_GENRE, "") })
    xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=li)

def show_users(users, parameters):
    ''' Show a list of users. A 'More...' item is added, 
        if there are more items available, then what is currently listed. '''
    for user in users:
        li = xbmcgui.ListItem(label=user.get(client.USER_NAME, ""), thumbnailImage=user.get(client.USER_AVATAR_URL, ""))
        user_parameters = {PARAMETER_KEY_MODE: MODE_USERS_TRACKS, PARAMETER_KEY_URL: PLUGIN_URL + "users/" + user[client.USER_PERMALINK], "user_permalink": user[client.USER_PERMALINK]}
        url = sys.argv[0] + '?' + urllib.urlencode(user_parameters)
        ok = xbmcplugin.addDirectoryItem(handle, url=url, listitem=li, isFolder=True)
    if not len(users) < parameters[PARAMETER_KEY_LIMIT]:
        more_item_parameters = parameters.copy()
        more_item_parameters[PARAMETER_KEY_OFFSET] = str(int(parameters[PARAMETER_KEY_OFFSET]) + int(parameters[PARAMETER_KEY_LIMIT]))
        addDirectoryItem(name="More...", parameters=more_item_parameters, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def show_groups(groups, parameters):
    ''' Show a list of groups. A 'More...' item is added, 
        if there are more items available, then what is currently listed. '''
    for group in groups:
        li = xbmcgui.ListItem(label=group.get(client.GROUP_NAME, ""), thumbnailImage=group.get(client.GROUP_ARTWORK_URL, ""))
        group_parameters = {PARAMETER_KEY_MODE: MODE_GROUPS_TRACKS, PARAMETER_KEY_URL: PLUGIN_URL + "groups/" + group[client.GROUP_PERMALINK], "group_id": group[client.GROUP_ID]}
        url = sys.argv[0] + '?' + urllib.urlencode(group_parameters)
        ok = xbmcplugin.addDirectoryItem(handle, url=url, listitem=li, isFolder=True)
    if not len(groups) < parameters[PARAMETER_KEY_LIMIT]:
        more_item_parameters = parameters.copy()
        more_item_parameters[PARAMETER_KEY_OFFSET] = str(int(parameters[PARAMETER_KEY_OFFSET]) + int(parameters[PARAMETER_KEY_LIMIT]))
        addDirectoryItem(name="More...", parameters=more_item_parameters, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict

def _show_keyboard(default="", heading="", hidden=False):
    ''' Show the keyboard and return the text entered. '''
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        return unicode(keyboard.getText(), "utf-8")
    return default

def show_root_menu():
    ''' Show the plugin root menu. '''
    addDirectoryItem(name='Groups', parameters={ PARAMETER_KEY_URL: PLUGIN_URL + 'groups', PARAMETER_KEY_MODE: MODE_GROUPS}, isFolder=True)
    addDirectoryItem(name='Tracks', parameters={PARAMETER_KEY_URL: PLUGIN_URL + 'tracks', PARAMETER_KEY_MODE: MODE_TRACKS}, isFolder=True)
    addDirectoryItem(name='Users', parameters={PARAMETER_KEY_URL: PLUGIN_URL + 'users', PARAMETER_KEY_MODE: MODE_USERS}, isFolder=True)
    xbmcplugin.endOfDirectory(handle=handle, succeeded=True)

##################################################################

params = parameters_string_to_dict(sys.argv[2])
url = urllib.unquote_plus(params.get(PARAMETER_KEY_URL, ""))
name = urllib.unquote_plus(params.get("name", ""))
mode = int(params.get(PARAMETER_KEY_MODE, "0"))
query = urllib.unquote_plus(params.get("q", ""))
print "##########################################################"
print("Mode: %s" % mode)
print("URL: %s" % url)
print("Name: %s" % name)
print "##########################################################"

# Depending on the mode, call the appropriate function to build the UI.
if not sys.argv[ 2 ] or not url:
    # new start
    ok = show_root_menu()
elif mode == MODE_GROUPS:
    ok = show_groups_menu()
elif mode == MODE_TRACKS:
    ok = show_tracks_menu()
elif mode == MODE_USERS:
    ok = show_users_menu()
elif mode == MODE_TRACKS_SEARCH:
    if (not query):
        query = _show_keyboard()
    tracks = soundcloud_client.get_tracks(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url, query)
    ok = show_tracks(parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL:url, "q":query}, tracks=tracks)
elif mode == MODE_TRACKS_HOTTEST:
    tracks = soundcloud_client.get_tracks(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url)
    ok = show_tracks(parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL:url}, tracks=tracks)
elif mode == MODE_GROUPS_SEARCH:
    if (not query):
        query = _show_keyboard()
    groups = soundcloud_client.get_groups(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url, query)
    ok = show_groups(groups=groups, parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL:url, "q":query})
elif mode == MODE_GROUPS_HOTTEST:
    groups = soundcloud_client.get_groups(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url)
    ok = show_groups(parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL:url}, groups=groups)
elif mode == MODE_GROUPS_TRACKS:
    tracks = soundcloud_client.get_group_tracks(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url, int(params.get("group_id", "1")))
    ok = show_tracks(parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL: url}, tracks=tracks)
elif mode == MODE_USERS_SEARCH:
    if (not query):
        query = _show_keyboard()
    users = soundcloud_client.get_users(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url, query)
    ok = show_users(users=users, parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL:url, "q":query})
elif mode == MODE_USERS_HOTTEST:
    users = soundcloud_client.get_users(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url)
    ok = show_users(parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL:url}, users=users)
elif mode == MODE_USERS_TRACKS:
    tracks = soundcloud_client.get_user_tracks(int(params.get(PARAMETER_KEY_OFFSET, "0")), int(params.get(PARAMETER_KEY_LIMIT, "50")), mode, url, params.get("user_permalink"))
    ok = show_tracks(parameters={PARAMETER_KEY_OFFSET: int(params.get(PARAMETER_KEY_OFFSET, "0")), PARAMETER_KEY_LIMIT: int(params.get(PARAMETER_KEY_LIMIT, "50")), PARAMETER_KEY_MODE: mode, PARAMETER_KEY_URL: url}, tracks=tracks)
elif mode == MODE_TRACK_PLAY:
    play_track(params.get(PARAMETER_KEY_PERMALINK, "1"))
