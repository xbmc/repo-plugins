import json
import sys
import requests
from pathlib import Path
from resources.lib import auth
import resources.lib.config as config
from urllib import parse
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin
import threading
import traceback
import time

from resources.lib.auth import read_credentials, get_device_code
import resources.lib.dialogs as dialogs
# from resources.lib.ui.custom_filter_dialog import FilterDialog
import resources.lib.utils as utils

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
qs = sys.argv[2][1:]
args = parse.parse_qs(qs)

mode = args.get('mode')
token = None  # Access token

# Addon dir path
__addon__ = xbmcaddon.Addon()
# addon_path = __addon__.getAddonInfo('path')
profile_path = xbmcvfs.translatePath(
    __addon__.getAddonInfo('profile'))
token_folder = Path(profile_path + config.token_folder)
token_path = None
if args.get('token_filename'):
    token_path = Path(token_folder / args.get('token_filename')[0])
xbmcplugin.setContent(addon_handle, 'images')


def new_account():
    xbmc.log('Executing new_account function', xbmc.LOGDEBUG)

    # Open dialog
    baseUrl = __addon__.getSettingString('baseUrl')
    login_dialog = dialogs.QRDialogProgress.create()
    login_dialog.show()
    # Gives enough time for window to initialize before sending the device code request
    xbmc.sleep(10)
    # Get User Code from auth server
    code_json = get_device_code()
    expires_at = time.time() + 0.99 * float(code_json["expires_in"])
    login_dialog.update(
        int(code_json["expires_in"]), code=code_json["userCode"])
    last_req_time = time.time()

    # Update progress dialog indicating time left for complete
    while not login_dialog.iscanceled():
        time_left = round(expires_at - time.time())
        login_dialog.update(time_left=time_left)
        xbmc.sleep(1000)

        status_code = -1  # Indicates no request sent
        # Check if last request is sufficiently old
        if (time_left > 0) and (time.time() - last_req_time >= code_json["interval"]):
            status_code = auth.fetch_and_save_token(
                code_json['deviceCode'], token_folder)
            last_req_time = time.time()
            if status_code == 200:
                xbmcgui.Dialog().notification(__addon__.getLocalizedString(30424),
                                              __addon__.getLocalizedString(30402), xbmcgui.NOTIFICATION_INFO, 3000)
                break

            if status_code == 403:      # 403 indicates rate limiting
                xbmc.sleep(1000)

        # Refresh Code if time is over
        if (time_left < 0) or (status_code and (status_code == 400)):
            code_json = get_device_code()
            expires_at = time.time() + 0.99 * float(code_json["expires_in"])
            login_dialog.update(
                int(code_json["expires_in"]), code_json["userCode"])
            xbmcgui.Dialog().notification(__addon__.getLocalizedString(30424),
                                          __addon__.getLocalizedString(30403), xbmcgui.NOTIFICATION_INFO, 3000)
    login_dialog.close()
    xbmc.executebuiltin('Container.Refresh')


def remove_account():
    xbmcvfs.delete(str(token_path))
    xbmc.executebuiltin('Container.Refresh')


def remove_all_accounts():
    token_folder.mkdir(parents=True, exist_ok=True)
    for file in token_folder.iterdir():
        xbmcvfs.delete(str(file))


def list_options():
    items = []

    # Third string in the tuples are API endpoint's route
    modes = [(__addon__.getLocalizedString(30404), 'list_media', 'all'),
             (__addon__.getLocalizedString(30405), 'list_albums', 'albums'),
             (__addon__.getLocalizedString(30406), 'list_albums', 'sharedAlbums'),
             (__addon__.getLocalizedString(30407), 'custom_filter')]

    for mode in modes:
        if len(mode) == 2:
            url = utils.build_url(
                base_url, {'mode': mode[1], 'token_filename': token_path.name})
        else:
            url = utils.build_url(
                base_url, {'mode': mode[1], 'type': mode[2], 'token_filename': token_path.name})
        li = xbmcgui.ListItem(mode[0])
        items.append((url, li, True))  # (url, listitem[, isFolder])

    xbmcplugin.addDirectoryItems(addon_handle, items)
    xbmcplugin.endOfDirectory(addon_handle)


def refresh():
    '''
    Refreshes the current window
    IMP: Pass previous query string as argument in the url with key prev_q
    '''
    id = xbmcgui.getCurrentWindowId()
    pos = int(xbmc.getInfoLabel(f'Container.CurrentItem'))
    cont_path = utils.build_url(
        base_url, {'call_type': 1}, args.get('prev_q')[0])
    xbmc.executebuiltin(f'Container.Update({cont_path})')

    # get active window
    win = xbmcgui.Window(id)
    cid = win.getFocusId()
    # Check if window is fully loaded
    while not xbmc.getCondVisibility(f'Control.IsVisible({cid})'):
        xbmc.sleep(150)
    # Focus on the last focused position
    xbmc.executebuiltin(f'SetFocus({cid},{pos},absolute)')


def get_items(pageToken=None) -> dict:

    # Prepare request
    params = {'pageSize': 100}
    if pageToken:
        params['pageToken'] = pageToken
    headers = {'Authorization': 'Bearer ' + token}

    # Check type of required listing
    list_type = args.get('type')[0]
    if list_type == 'all':
        error = __addon__.getLocalizedString(30408)
        res = requests.get(config.service_endpoint + '/mediaItems',
                           headers=headers, params=params)
    elif list_type == 'album':
        error = __addon__.getLocalizedString(30409)
        params['albumId'] = args.get('id')[0]
        res = requests.post(config.service_endpoint + '/mediaItems:search',
                            headers=headers, data=params)
    elif list_type == 'filter':
        # params
        params['filters'] = utils.buildFilter(__addon__)
        if not bool(params['filters']):
            return None
        error = __addon__.getLocalizedString(30410)
        res = requests.post(config.service_endpoint + '/mediaItems:search',
                            headers=headers, json=params)
    if res.status_code != 200:
        dialog = xbmcgui.Dialog()
        dialog.notification(
            __addon__.getLocalizedString(30411), f'{error}. {__addon__.getLocalizedString(30412)}:{res.status_code}', xbmcgui.NOTIFICATION_ERROR, 3000)
        return None
    return res.json()


def get_items_bg(result, path):
    if 'nextPageToken' in result[-1]:
        pageToken = result[-1]["nextPageToken"]
        media = get_items(pageToken)
        if not media:
            return None
        utils.storeData(path, media)


def list_media():
    # For all photo directories

    path = profile_path + config.media_filename
    if not args.get('call_type'):
        xbmcvfs.delete(path)

    result = utils.loadData(path)
    if not result:
        media = get_items()
        if media:
            utils.storeData(path, media)
            result = [media]
        else:
            xbmcgui.Dialog().notification(__addon__.getLocalizedString(30425),
                                          __addon__.getLocalizedString(30413), xbmcgui.NOTIFICATION_INFO, 3000)
            return
    # List for media
    items = []
    for item in result:
        items += create_media_list(item)

    # Add list to directory
    xbmcplugin.addDirectoryItems(
        addon_handle, items, totalItems=len(items))

    if 'nextPageToken' in result[-1]:
        url = utils.build_url(base_url, {'mode': 'refresh', 'prev_q': qs})
        li = xbmcgui.ListItem(__addon__.getLocalizedString(30414))
        li.setProperty('IsPlayable', 'false')
        xbmcplugin.addDirectoryItem(addon_handle, url, li)
    if args.get('call_type'):
        updateListing = True
    else:
        updateListing = False
    xbmcplugin.endOfDirectory(
        addon_handle, updateListing=updateListing, cacheToDisc=False)

    if 'nextPageToken' in result[-1]:
        loader = threading.Thread(target=get_items_bg, args=(
            result, path,))
        loader.start()
        loader.join()


def create_media_list(media: dict):
    # Creates a list of (url, li) from media dictionary
    items = []
    for item in media.get("mediaItems", {}):
        item_type = item["mimeType"].split('/')[0]
        li = xbmcgui.ListItem(item["filename"])
        url = None
        h = xbmcgui.getScreenHeight()
        w = xbmcgui.getScreenWidth()
        if item_type == 'image':
            # thumb_url = item["baseUrl"] + f'=w{w}-h{h}'
            thumb_url = item["baseUrl"] + f'=w{960}-h{540}'
            img_url = item["baseUrl"] + f'=w{w}-h{h}'
            li.setArt(
                {'icon': 'DefaultIconInfo.png'})
            url = img_url
        elif item_type == 'video':
            vid_url = item["baseUrl"] + '=dv'
            thumb_url = item["baseUrl"] + f'=w{w}-h{h}'
            url = utils.build_url(
                base_url, {'mode': 'play_video', 'path': vid_url,
                           'status': item["mediaMetadata"]["video"]["status"], 'token_filename': token_path.name})
            li.setArt({'thumb': thumb_url, 'icon': thumb_url})
            li.setProperty('IsPlayable', 'true')
        else:
            continue
        li.setProperty('MimeType', item["mimeType"])
        items.append((url, li))
    return items


def play_video():
    # https://kodi.wiki/view/HOW-TO:Video_addon
    if args.get('status')[0] != 'READY':
        xbmcgui.Dialog().notification(__addon__.getLocalizedString(30411),
                                      __addon__.getLocalizedString(30415), xbmcgui.NOTIFICATION_ERROR, 3000)
    else:
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=args.get('path')[0])
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def custom_filter():
    __addon__.openSettings()
    url = utils.build_url(
        base_url, {'mode': 'list_media', 'type': 'filter'}, qs)
    li = xbmcgui.ListItem(__addon__.getLocalizedString(30416))
    li.setProperty('isPlayable', 'false')
    xbmcplugin.addDirectoryItem(addon_handle, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)


def list_albums():
    # For shared albums and regular albums
    # https://developers.google.com/photos/library/guides/list

    request_type = args.get('type')[0]
    # Request for listing albums or sharedAlbums
    params = {}
    if args.get('pageToken'):
        params['pageToken'] = args.get('pageToken')[0]
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.get(config.service_endpoint + f'/{request_type}',
                       headers=headers, params=params)

    # Parse response
    a_num = 1    # For albums without name TODO: a_num should be in nextPage URL
    if res.status_code != 200:
        dialog = xbmcgui.Dialog()
        dialog.notification(
            'Error', f'{__addon__.getLocalizedString(30417)}{res.status_code}', xbmcgui.NOTIFICATION_ERROR, 3000)
    else:
        album_data = res.json()  # { albums, nextPageToken}
        items = []
        if album_data:
            for album in album_data[request_type]:
                url = utils.build_url(
                    base_url, {'mode': 'list_media', 'type': 'album', 'id': album["id"], 'token_filename': token_path.name})
                if 'title' in album:
                    li = xbmcgui.ListItem(album["title"])
                else:
                    li = xbmcgui.ListItem(
                        f'{__addon__.getLocalizedString(30418)} {a_num}')
                    a_num += 1
                thumb_url = album["coverPhotoBaseUrl"] + \
                    f'=w{xbmcgui.getScreenWidth()}-h{xbmcgui.getScreenHeight()}'
                li.setArt(
                    {'thumb': thumb_url})
                items.append((url, li, True))

        xbmcplugin.addDirectoryItems(
            addon_handle, items, totalItems=len(items))

        # Pagination
        if 'nextPageToken' in album_data:
            url = utils.build_url(
                base_url, {'mode': 'list_albums', 'pageToken': album_data['nextPageToken'], 'token_filename': token_path.name, 'type': request_type})
            li = xbmcgui.ListItem(__addon__.getLocalizedString(30419))
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)

        xbmcplugin.endOfDirectory(addon_handle)

# Modify this function to force changes after update


def make_changes():
    version_file = profile_path + 'info'
    xbmcvfs.mkdirs(profile_path)
    with open(version_file, 'w+') as file:
        try:
            past_info = json.load(file)
        except:
            past_info = {}

    if bool(past_info) or past_info.get('version') != __addon__.getAddonInfo('version'):
        past_info['version'] = __addon__.getAddonInfo('version')
        __addon__.setSettingString(
            "baseUrl", "https://photos-kodi-addon.onrender.com")
        with open(version_file, 'w') as file:
            json.dump(past_info, file, default=str)


def display_page_content():
    if mode is None:
        # Display logged in accounts
        token_folder.mkdir(parents=True, exist_ok=True)
        for file in token_folder.iterdir():
            try:
                creds = read_credentials(file)
            except:
                xbmc.log(str(traceback.format_exc()), xbmc.LOGDEBUG)
                err_dialog = xbmcgui.Dialog()
                err_dialog.notification(__addon__.getLocalizedString(30411),
                                        __addon__.getLocalizedString(30422),
                                        xbmcgui.NOTIFICATION_ERROR, 3000)
                exit()
            email = creds["email"]
            url = utils.build_url(
                base_url, {'mode': 'list_options', 'token_filename': file.name})
            li = xbmcgui.ListItem(email)
            removePath = utils.build_url(
                base_url, {'mode': 'remove_account', 'email': email, 'token_filename': file.name})
            contextItems = [(__addon__.getLocalizedString(
                30420), f'RunPlugin({removePath})')]
            li.addContextMenuItems(contextItems)
            xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                        listitem=li, isFolder=True)
        # Add Account Button
        url = utils.build_url(base_url, {'mode': 'new_account'})
        li = xbmcgui.ListItem(__addon__.getLocalizedString(30421))
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li)
        xbmcplugin.endOfDirectory(addon_handle)
    else:
        # Read account credentials if present
        if token_path and mode[0] != 'remove_account':
            try:
                creds = read_credentials(token_path)
            except:
                err_dialog = xbmcgui.Dialog()
                err_dialog.notification(__addon__.getLocalizedString(30411),
                                        __addon__.getLocalizedString(30422),
                                        xbmcgui.NOTIFICATION_ERROR, 3000)
                exit()
            global token
            token = creds["token"]
        eval(mode[0] + '()')  # Fire up the actual function


make_changes()
# check for credentials
if not __addon__.getSettingString('client_id') or not __addon__.getSettingString('client_secret'):
    open_settings_dialog = xbmcgui.Dialog().ok(__addon__.getLocalizedString(30428),
                                               __addon__.getLocalizedString(30429))
    remove_all_accounts()
    __addon__.openSettings()
else:
    display_page_content()
    # Updates:
    # Slideshow

    # Not on list
    # Video seeking - Not possible due to API limitations
