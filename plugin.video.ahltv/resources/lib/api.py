from resources.lib.globals import *
import requests
import xbmcgui
import sys
import json
import os
import inputstreamhelper
from .utils import log

def get_request_headers(authorized = False):
    headers = {
        "Accept": "application/json",
        "User-Agent": xbmc.getUserAgent(),
        "product_id": PRODUCT_ID,
        "app_id": APP_ID,
        "app_key": APP_KEY
    }

    if (authorized):
        auth_json = None
        try:
            auth_json = load_auth_info()
        except Exception as e:
            log('Failed to load auth info: '+ str(e), True)
            sys.exit()

        headers["api_key"] = auth_json['api_key']
        headers["app_id"] = auth_json['app_id']

    return headers

def login():
    # Check if username and password are provided
    global USERNAME
    if USERNAME == '""':
        dialog = xbmcgui.Dialog()
        USERNAME = dialog.input(LOCAL_STRING(31000), type=xbmcgui.INPUT_ALPHANUM)
        settings.setSetting(id='username', value=USERNAME)
        USERNAME = json.dumps(USERNAME)
        sys.exit()

    global PASSWORD
    if PASSWORD == '""':
        dialog = xbmcgui.Dialog()
        PASSWORD = dialog.input(LOCAL_STRING(31001), type=xbmcgui.INPUT_ALPHANUM, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        settings.setSetting(id='password', value=PASSWORD)
        PASSWORD = json.dumps(PASSWORD)
        sys.exit()

    if USERNAME != '""' and PASSWORD != '""':
        url = API_URL + '/sessions/api_key'
        headers = get_request_headers(False)

        body = '{"email":' + USERNAME + ', "password":' + PASSWORD + '}'

        r = requests.post(url, headers=headers, data=body, verify=VERIFY)
        if r.status_code == 401:
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(31002), LOCAL_STRING(31003))
            sys.exit()
        elif r.status_code >= 500:
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(31004), LOCAL_STRING(31005))
            sys.exit()

        # get the api key from the response and save it
        json_source = r.json()
        json_source['app_id'] = APP_ID

        save_auth_info(json_source)

        return json_source

def logout(display_msg=None):
    url = API_URL + '/sessions'

    try:
        headers = get_request_headers(True)
        r = requests.delete(url, headers=headers)
        scode = str(r.status_code)
        if r.status_code != 204:
            log('Error logging out user. Error code: '+ str(r.status_code), True)
        else:
            try:
                os.remove(ADDON_PATH_PROFILE + 'auth.json')
            except:
                pass
            dialog = xbmcgui.Dialog()
            dialog.notification(LOCAL_STRING(31006), LOCAL_STRING(31007), ICON, 5000, False)
    except:
        dialog = xbmcgui.Dialog()
        dialog.notification(LOCAL_STRING(31006), LOCAL_STRING(31016), ICON, 5000, False)

    return

def save_auth_info(data):
    with open(ADDON_PATH_PROFILE + 'auth.json', 'w') as f:
        json.dump(data, f, ensure_ascii=False)

def load_auth_info():
    with open(ADDON_PATH_PROFILE + 'auth.json') as f:
        d = json.load(f)
        return d

def get_game_info(game_id):
    auth_json = None
    try:
        auth_json = load_auth_info()
    except:
        pass

    if auth_json is None:
        auth_json = login()

    url = API_URL + '/htv2020/game/' + str(game_id)
    headers = get_request_headers(True)

    r = requests.get(url, headers=headers)
    if r.status_code == 401:
        logout()
        dialog = xbmcgui.Dialog()
        dialog.ok(LOCAL_STRING(31008), LOCAL_STRING(31009))
        sys.exit()

    return r.json()

def get_game_streams(game_id, multiple_audio):
    stream_info = {}
    stream_info["streams"] = []
    stream_info["list_items"] = []
    access_denied_cnt = 0

    headers = get_request_headers(True)

    # Get the home stream info
    url = API_URL + '/htv2020/game/' + str(game_id) + '/stream_info'
    r = requests.get(url, headers=headers)

    if r.status_code == 403:
        access_denied_cnt += 1
    elif r.status_code >= 400:
        log("Error loading stream info - response code: " + str(r.status_code), True)
        dialog = xbmcgui.Dialog()
        dialog.ok(LOCAL_STRING(31010), LOCAL_STRING(31011))
        sys.exit()
    else:
        stream_json = r.json()

        liz = xbmcgui.ListItem(LOCAL_STRING(31012), path=stream_json['stream']['url'])

        helper = inputstreamhelper.Helper('hls')
        if not xbmcaddon.Addon().getSettingBool("ffmpeg") and helper.check_inputstream():
            log("Setting inputstream.adaptive on home list item")
            liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
            liz.setProperty('inputstream.adaptive.manifest_type', 'hls')
        else:
            log("Setting home list item mimeType to application/x-mpegURL")
            liz.setMimeType("application/x-mpegURL")

        stream_info["list_items"].append(liz)
        stream_info["streams"].append(stream_json['stream'])

    if multiple_audio == 1:  # Home and away audio
        url = API_URL + '/htv2020/game/' + str(game_id) + '/stream_info?audio=2'
        r = requests.get(url, headers=headers)

        if r.status_code == 403:
            access_denied_cnt += 1
        elif r.status_code >= 400:
            log("Error loading stream info - response code: " + str(r.status_code), True)
            dialog = xbmcgui.Dialog()
            dialog.ok(LOCAL_STRING(31010), LOCAL_STRING(31011))
            sys.exit()
        else:
            stream_json = r.json()
            liz = xbmcgui.ListItem(LOCAL_STRING(31013), path=stream_json['stream']['url'])

            if not xbmcaddon.Addon().getSettingBool("ffmpeg") and helper.check_inputstream():
                log("Setting inputstream.adaptive on away list item")
                liz.setProperty('inputstreamaddon', 'inputstream.adaptive')
                liz.setProperty('inputstream.adaptive.manifest_type', 'hls')
            else:
                log("Setting away list item mimeType to application/x-mpegURL")
                liz.setMimeType("application/x-mpegURL")

            stream_info["list_items"].append(liz)
            stream_info["streams"].append(stream_json['stream'])

    # check final results
    if (access_denied_cnt == 1 and multiple_audio == 0) or (access_denied_cnt == 2 and multiple_audio == 1):
        dialog = xbmcgui.Dialog()
        dialog.ok(LOCAL_STRING(31014), LOCAL_STRING(31015))
        sys.exit()

    return stream_info

def log_played(game_id, audio_id = 1):
    played_id = None

    auth_json = None
    try:
        auth_json = load_auth_info()
    except:
        pass

    if auth_json is None:
        auth_json = login()

    url = API_URL + '/games/'+ str(game_id) + '/played/' + str(audio_id)
    headers = get_request_headers(True)

    r = requests.post(url, headers=headers, verify=VERIFY)
    if r.status_code == 200:
        played_response = r.json()
        played_id = played_response['id']
    else:
        log("Error logging played - game_id: " + str(game_id) + ', audio_id: ' + str(audio_id), True)

    return played_id

def mark_end_time(played_id):
    success = False

    auth_json = None
    try:
        auth_json = load_auth_info()
    except:
        pass

    if auth_json is None:
        auth_json = login()

    url = API_URL + '/game/mark_end_time/' + str(played_id)
    headers = get_request_headers(True)

    r = requests.put(url, headers=headers, verify=VERIFY)

    if r.status_code == 200:
        success = True
    else:
        log("Error updating end time. played_id: " + str(played_id) + ', status_code: ' + str(r.status_code), True)

    return success
