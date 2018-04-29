import sys

import xbmcplugin
import xbmcaddon
import xbmcgui
import xbmc

import json
import time
import os.path

import requests
import urllib
import urlparse

API_URL = 'https://www.seedr.cc/api'
DEVICE_CODE_URL = 'https://www.seedr.cc/api/device/code'
AUTHENTICATION_URL = 'https://www.seedr.cc/api/device/authorize'
CLIENT_ID = 'seedr_xbmc'

__settings__ = xbmcaddon.Addon(id='plugin.video.seedr')
__language__ = __settings__.getLocalizedString

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def fetch_json_dictionary(url, post_params=None):
    if post_params is not None:
        r = requests.post(url, data=post_params)
    else:
        r = requests.get(url)
    return r.json()


def get_device_code():
    return fetch_json_dictionary(DEVICE_CODE_URL + '?client_id=' + CLIENT_ID)


def get_token(device_code, client_id):
    return fetch_json_dictionary(AUTHENTICATION_URL + '?device_code=' + device_code + '&client_id=' + client_id)


def call_api(func, access_token, params=None):
    return fetch_json_dictionary(API_URL + func + '?access_token=' + access_token, params)


def save_dict(data, filename):
    try:
        f = open(filename, 'w')
    except IOError as e:
        xbmcgui.Dialog().ok(addonname, e.strerror)

    json.dump(data, f)
    f.close()
    return


def load_dict(filename):
    if os.path.isfile(filename):
        f = open(filename, 'r')
        data = json.load(f)
        f.close()
        return data
    else:
        return {}


def get_access_token():
    device_code_dict = get_device_code()
    settings['device_code'] = device_code_dict['device_code']
    settings['device_code_dict'] = device_code_dict  

    line1 = __language__(id=32000) + ' '  + device_code_dict['verification_url'] + ' ' +  __language__(id=32001) + ' ' + device_code_dict['user_code'][0:4] + ' ' + device_code_dict['user_code'][4:]
    line2 = __language__(id=32002) 

    xbmcgui.Dialog().ok(addonname, line1, line2)

    token_dict = None
    access_token = None
    while access_token is None:
        token_dict = get_token(settings['device_code'], CLIENT_ID)
        if 'error' in token_dict:
            if token_dict['error'] == 'authorization_pending':
                xbmc.log(__language__(id=32003));
            else:
                xbmc.log(__language__(id=32004) + ' ' + token_dict['error'])
                sys.exit(0)

            time.sleep(device_code_dict['interval'])
        else:
            access_token = token_dict['access_token']

    xbmc.log(__language__(id=32005))

    settings['access_token'] = access_token

    save_dict(settings, data_file)


addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')

__profile__ = xbmc.translatePath(addon.getAddonInfo('profile')).decode("utf-8")
if not os.path.isdir(__profile__):
    os.makedirs(__profile__)

data_file = xbmc.translatePath(os.path.join(__profile__, 'settings.json')).decode("utf-8")

settings = load_dict(data_file)

args = urlparse.parse_qs(sys.argv[2][1:])
mode = args.get('mode', None)

addon_handle = int(sys.argv[1])
base_url = sys.argv[0]

if 'access_token' not in settings:
    get_access_token()

if 'access_token' in settings:
    if mode is None:
        data = call_api('/folder', settings['access_token'])
    elif mode[0] == 'folder':
        folder_id = args['folder_id'][0]
        data = call_api('/folder/' + folder_id, settings['access_token'])

    if 'error' in data:
        get_access_token()
        if mode is None:
            data = call_api('/folder', settings['access_token'])
        elif mode[0] == 'folder':
            folder_id = args['folder_id'][0]
            data = call_api('/folder/' + folder_id, settings['access_token'])

    folders = data['folders']
    files = data['files']

    for folder in folders:
        url = build_url({'mode': 'folder', 'folder_id': folder['id']})

        li = xbmcgui.ListItem(folder['name'], iconImage='DefaultFolder.png')
        li.addContextMenuItems([(__language__(id=32006), 'Container.Refresh'),
                                (__language__(id=32007), 'Action(ParentDir)')])
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)

    for f in files:
        if f['play_video'] is True:
            url = API_URL + '/media/hls/' + str(f['folder_file_id']) + '?access_token=' + settings['access_token']
            thumbnail = API_URL + '/media/image/320/' + str(f['folder_file_id']) + '?access_token=' + settings['access_token']
            icon = API_URL + '/thumbnail/' + str(f['folder_file_id']) + '?access_token=' + settings['access_token']

            li = xbmcgui.ListItem(f['name'], iconImage=icon, thumbnailImage=thumbnail)
            li.addContextMenuItems([(__language__(id=32006), 'Container.Refresh'),
                                    (__language__(id=32007), 'Action(ParentDir)')])

            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        elif f['play_audio'] is True:
            url = API_URL + '/media/mp3/' + str(f['folder_file_id']) + '?access_token=' + settings['access_token']

            li = xbmcgui.ListItem(f['name'])
            li.addContextMenuItems([(__language__(id=32006), 'Container.Refresh'),
                                    (__language__(id=32007), 'Action(ParentDir)')])

            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)

    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_FILE)
    xbmcplugin.endOfDirectory(addon_handle)

