import datetime
import os
import sys
import uuid
from urllib.parse import urlencode, parse_qsl
import requests

import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs
import xbmcaddon
from xbmcaddon import Addon
from xbmcvfs import translatePath

# Get the plugin url in plugin:// notation.
URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
# Get addon base path
ADDON_PATH = translatePath(Addon().getAddonInfo('path'))
ICONS_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'icons')
FANART_DIR = os.path.join(ADDON_PATH, 'resources', 'images', 'fanart')
__addon__ = xbmcaddon.Addon(id='plugin.video.opentakserver')
__addondir__ = xbmcvfs.translatePath( __addon__.getAddonInfo('profile'))

csrf_token = None


def get_auth_token_from_file():
    f = xbmcvfs.File(os.path.join(__addondir__, "auth_token"), 'r')
    auth_token = f.read()
    f.close()
    return auth_token


def get(url):
    auth_token = get_auth_token_from_file()

    r = requests.get(url, params={'auth_token': auth_token}, verify=bool(xbmcplugin.getSetting(HANDLE, "verify_certificates")))
    if r.status_code != 200:
        xbmc.log(f"Failed to get {url}: {r.text}", xbmc.LOGERROR)
    return r


def login():
    r = requests.post(xbmcplugin.getSetting(HANDLE, "server_url") + "/api/login?include_auth_token",
               json={'username': xbmcplugin.getSetting(HANDLE, "username"),
                     'password': xbmcplugin.getSetting(HANDLE, "password")})
    if r.status_code == 200:
        auth_token = r.json()['response']['user']['authentication_token']
        xbmc.log(f"login() {auth_token}", xbmc.LOGINFO)
        f = xbmcvfs.File(os.path.join(__addondir__, 'auth_token'), 'w')
        f.write(auth_token)
        f.close()
    else:
        dialog = xbmcgui.Dialog()
        dialog.notification('Login Failed', 'Check the settings and try again', xbmcgui.NOTIFICATION_INFO, 5000)


def format_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :return: plugin call URL
    :rtype: str
    """
    return '{}?{}'.format(URL, urlencode(kwargs))


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    params = dict(parse_qsl(paramstring))
    xbmc.log("paramstring " + str(paramstring), xbmc.LOGINFO)
    xbmcplugin.setPluginCategory(HANDLE, "OpenTAKServer")
    xbmcplugin.setContent(HANDLE, 'videos')
    auth_token = get_auth_token_from_file()

    window = xbmcgui.Window(10000)

    # Check the parameters passed to the plugin
    if not params:
        login()
        xbmcplugin.addDirectoryItem(HANDLE, format_url(choice="streams", page="1"), xbmcgui.ListItem(label="Streams"), True)
        xbmcplugin.addDirectoryItem(HANDLE, format_url(choice="recordings", page="1"), xbmcgui.ListItem(label="Recordings"), True)
        xbmcplugin.endOfDirectory(HANDLE)

    elif params['choice'] == "streams":
        page = params["page"]
        if not page:
            page = 1
        else:
            page = int(page)

        if page > 1:
            list_item = xbmcgui.ListItem(label="Previous Page")
            xbmcplugin.addDirectoryItem(HANDLE, format_url(choice="streams", page=str(page - 1)), list_item, isFolder=True)

        streams = get(xbmcplugin.getSetting(HANDLE, "server_url") + "/api/video_streams").json()
        for stream in streams['results']:
            list_item = xbmcgui.ListItem(label=stream['path'])

            # The random UUID prevents Kodi from pulling the thumbnail from cache. The server ignores it
            thumbnail = xbmcplugin.getSetting(HANDLE, "server_url") + '/api/videos/thumbnail?path={}&random={}&auth_token={} '.format(stream['path'], str(uuid.uuid4()), auth_token)
            list_item.setArt({'thumb': thumbnail, 'fanart': thumbnail})

            xbmcplugin.addDirectoryItem(HANDLE, f"{stream['rtsp_link']}?jwt={auth_token}", list_item, False)

        if page < streams['total_pages']:
            list_item = xbmcgui.ListItem(label="Next Page")
            xbmcplugin.addDirectoryItem(HANDLE, format_url(choice="streams", page=str(page + 1)), list_item, isFolder=True)
        xbmcplugin.endOfDirectory(HANDLE)

    elif params['choice'] == 'recordings':
        page = params["page"]
        if not page:
            page = 1
        else:
            page = int(page)

        if page > 1:
            list_item = xbmcgui.ListItem(label="Previous Page")
            xbmcplugin.addDirectoryItem(HANDLE, format_url(choice="recordings", page=str(page - 1)), list_item, isFolder=True)

        server_url = xbmcplugin.getSetting(HANDLE, "server_url")
        recordings = get("{}/api/videos/recordings?page={}".format(server_url, page))
        xbmc.log(recordings.text, xbmc.LOGINFO)
        for recording in recordings.json()['results']:
            url = "{}/api/videos/recording?id={}&auth_token={}|Cookie=Cookie: ".format(server_url, recording['id'], auth_token)
            thumbnail = '{}/api/videos/thumbnail?path={}&recording={}&random={}&auth_token={}'.format(server_url, recording['path'], recording['filename'], str(uuid.uuid4()), auth_token)
            list_item = xbmcgui.ListItem(label=recording['path'] + " - " + recording['start_time'])
            list_item.setArt({'thumb': thumbnail})
            try:
                start_time = datetime.datetime.strptime(recording['start_time'], "%Y-%m-%dT%H:%M:%SZ")
            except:
                start_time = datetime.datetime.now()

            tag = list_item.getVideoInfoTag()
            tag.setDateAdded(start_time.strftime("%Y-%m-%d %H:%M:%S"))
            tag.setPremiered(start_time.strftime("%Y-%m-%d %H:%M:%S"))
            if recording['duration']:
                tag.setDuration(recording['duration'])
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item)

        if page < recordings.json()['total_pages']:
            list_item = xbmcgui.ListItem(label="Next Page")
            xbmcplugin.addDirectoryItem(HANDLE, format_url(choice="recordings", page=str(page + 1)), list_item, isFolder=True)

        xbmcplugin.endOfDirectory(HANDLE)
    else:
        raise ValueError(f'Invalid paramstring: {paramstring}!')


if __name__ == '__main__':
    if not xbmcplugin.getSetting(HANDLE, "server_url") or not xbmcplugin.getSetting(HANDLE, "username") or not xbmcplugin.getSetting(HANDLE, "password"):
        xbmcaddon.Addon().openSettings()
    router(sys.argv[2][1:])
