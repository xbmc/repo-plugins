# TODO: find secure way to pass token

import os
import sys
import pickle
from time import sleep
import requests
from resources.lib import auth
import resources.lib.config as config
from urllib import parse
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import xbmcplugin
import threading


from resources.lib.auth import read_credentials, get_device_code
import resources.lib.utils as utils

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
qs = sys.argv[2][1:]
args = parse.parse_qs(qs)

mode = args.get('mode')
token = None

# Addon dir path
__addon__ = xbmcaddon.Addon()
addon_path = __addon__.getAddonInfo('path')
profile_path = xbmcvfs.translatePath(
    __addon__.getAddonInfo('profile'))
token_path = profile_path + config.token_filename
xbmcplugin.setContent(addon_handle, 'images')


def new_account():
    # try:
    # Get User Code from auth server
    code_json = get_device_code()
    xbmc.log('Executing new_account function', xbmc.LOGDEBUG)
    user_code = code_json["userCode"]
    # except Exception as exec
    #     raise Exception(
    #         "Unable to get code from auth server. Check your server configuration in addon settings")
    login_dialog = xbmcgui.DialogProgress()
    dialog_msg = f'Visit {config.base_url} and enter the code:\n'
    login_dialog.create('Authenticate', dialog_msg + user_code)

    # Update progress dialog indicating time left for complete
    sleep_time = utils.sleep_time(code_json['expires_in'])
    xbmc.log(str(sleep_time), xbmc.LOGDEBUG)
    time = 99
    while time >= 0:
        login_dialog.update(time)
        if login_dialog.iscanceled():
            break
        sleep(sleep_time)
        # TODO: Handle the case of server going down
        status_code = auth.fetch_and_save_token(
            code_json['deviceCode'], token_path)
        # TODO: Time parameter
        if status_code == 200:
            xbmc.executebuiltin(
                'Notification(Success, Account added successfully, time=3000)')
            break
        if status_code == 403:
            sleep(10)
        if time == 0:
            code_json = get_device_code()
            time = 100
            login_dialog.update(time, message=dialog_msg +
                                code_json["userCode"])
            xbmc.executebuiltin('Notification(Code refreshed, ,time=3000)')
        time -= 1

    login_dialog.close()
    # TODO: Test this
    xbmc.executebuiltin('Container.Refresh')
    # account_dialog.addControl(msg)

    # resp = xbmcgui.Dialog().ok(
    #     'Authenticate', f'Visit {config.base_url} and enter the code: {user_code}')
    # win =


def list_options():
    items = []
    modes = [('Search', 'search'), ('All Media', 'list_media', 'all'),
             ('All Albums', 'list_albums'), ('Shared Albums', 'shared_albums')]

    for mode in modes:
        if len(mode) == 2:
            url = utils.build_url(base_url, {'mode': mode[1]})
        else:
            url = utils.build_url(base_url, {'mode': mode[1], 'type': mode[2]})
        li = xbmcgui.ListItem(mode[0])
        items.append((url, li, True))  # (url, listitem[, isFolder])

    xbmcplugin.addDirectoryItems(addon_handle, items)
    xbmcplugin.endOfDirectory(addon_handle)


def search():
    pass


def refresh():
    id = xbmcgui.getCurrentWindowId()
    # pos = xbmc.getInfoLabel(f'ListItem.Label')
    pos = int(xbmc.getInfoLabel(f'Container.CurrentItem'))
    xbmc.executebuiltin('Container.Refresh')
    # get active window
    win = xbmcgui.Window(id)
    cid = win.getFocusId()
    while not xbmc.getCondVisibility(f'Control.IsVisible({cid})'):
        sleep(0.2)
    xbmc.executebuiltin(f'SetFocus({cid},{pos},absolute)')


def get_items(pageToken=None) -> dict:
    # Handle Pagination and other params for request
    params = {'pageSize': 100}
    if pageToken:
        params['pageToken'] = pageToken

    headers = {'Authorization': 'Bearer ' + token}
    # Check type of required listing
    list_type = args.get('type')[0]
    if list_type == 'all':
        error = 'Unable to retrieve media items from Google'
        res = requests.get(config.service_endpoint + f'/mediaItems',
                           headers=headers, params=params)
    elif list_type == 'album':
        error = 'Unable to load album items'
        params['albumId'] = args.get('id')[0]
        res = requests.post(config.service_endpoint + f'/mediaItems:search',
                            headers=headers, data=params)
    if res.status_code != 200:
        dialog = xbmcgui.Dialog()
        dialog.notification(
            'Error', f'{error}. Error Code:{res.status_code}', xbmcgui.NOTIFICATION_ERROR, 3000)
        return None
    return res.json()


def get_items_bg(result, path):
    xbmc.log("Image Loader started.", xbmc.LOGDEBUG)
    if 'nextPageToken' in result[-1]:
        # print(f'lala {result}')
        pageToken = result[-1]["nextPageToken"]
        media = get_items(pageToken)
        if not media:
            return None
        utils.storeData(path, media)


def list_media():
    path = profile_path + config.media_filename
    result = utils.loadData(path)
    if not result:
        media = get_items()
        if not media:
            return
        result = [media]
        utils.storeData(path, media)

    # List for media
    items = []
    for item in result:
        items += create_media_list(item)

    # Add list to directory
    xbmcplugin.addDirectoryItems(
        addon_handle, items, totalItems=len(items))
    if 'nextPageToken' in result[-1]:
        url = utils.build_url(base_url, {'mode': 'refresh'})
        li = xbmcgui.ListItem('Show more...')
        xbmcplugin.addDirectoryItem(addon_handle, url, li)

    xbmcplugin.endOfDirectory(addon_handle)

    if 'nextPageToken' in result[-1]:
        loader = threading.Thread(target=get_items_bg, args=(
            result, path,))
        loader.start()
        loader.join()
        xbmc.log("All Image links fetched.", xbmc.LOGDEBUG)


def create_media_list(media: dict):
    # Creates a list of (url, li) from media dictionary
    items = []
    for item in media["mediaItems"]:
        item_type = item["mimeType"].split('/')[0]
        li = xbmcgui.ListItem(item["filename"])
        url = None
        h = xbmcgui.getScreenHeight()
        w = xbmcgui.getScreenWidth()
        if item_type == 'image':
            # thumb_url = item["baseUrl"] + f'=w{w}-h{h}'
            thumb_url = item["baseUrl"] + f'=w{960}-h{540}'
            img_url = item["baseUrl"] + f'=w{w}-h{h}'

            # url = utils.build_url(
            #     base_url, {'mode': 'show_image', 'path': thumb_url})
            li.setArt(
                {'icon': 'DefaultIconInfo.png'})
            url = img_url
            # li.set
        elif item_type == 'video':
            vid_url = item["baseUrl"] + '=dv'
            thumb_url = item["baseUrl"] + f'=w{w}-h{h}'
            url = utils.build_url(
                base_url, {'mode': 'play_video', 'path': vid_url, 'status': item["mediaMetadata"]["video"]["status"]})
            li.setArt({'thumb': thumb_url, 'icon': thumb_url})
            # li.setInfo()
            li.setProperty('IsPlayable', 'true')
        else:
            continue
        li.setProperty('MimeType', item["mimeType"])
        items.append((url, li))
    return items


def play_video():
    # https://kodi.wiki/view/HOW-TO:Video_addon
    if args.get('status')[0] != 'READY':
        xbmc.executebuiltin(
            'Notification(Error, Video is not ready for viewing yet, time=3000)')
    else:
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=args.get('path')[0])
        # play_item = xbmcgui.ListItem(
        #     path='http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4')
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def list_albums():
    # https://developers.google.com/photos/library/guides/list
    params = {}
    if args.get('pageToken'):
        params['pageToken'] = args.get('pageToken')[0]
    a_num = 1
    headers = {'Authorization': 'Bearer ' + token}
    res = requests.get(config.service_endpoint + '/albums',
                       headers=headers, params=params)
    if res.status_code != 200:
        dialog = xbmcgui.Dialog()
        dialog.notification(
            'Error', f'Unable to retrieve album list. Error Code:{res.status_code}', xbmcgui.NOTIFICATION_ERROR, 3000)
    else:
        album_data = res.json()  # { albums, nextPageToken}
        # Album cover is also available in API. Useful for nameless albums
        items = []
        for album in album_data["albums"]:
            url = utils.build_url(
                base_url, {'mode': 'list_media', 'type': 'album', 'id': album["id"]})
            if 'title' in album:
                li = xbmcgui.ListItem(album["title"])
            else:
                li = xbmcgui.ListItem(f'Nameless album {a_num}')
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
                base_url, {'mode': 'list_albums', 'pageToken': album_data['nextPageToken']})
            li = xbmcgui.ListItem('Next Page')
            # icon = os.path.join(addon_path, 'resources',
            #                     'lib', 'download.png')
            # li.setArt({'thumb': icon, 'icon': icon})
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)

        xbmcplugin.endOfDirectory(addon_handle)


if mode is None:
    # Option for adding New Account
    if os.path.exists(token_path):
        # Get email
        email = 'Email Unknown'
        creds = read_credentials(token_path)
        headers = {'Authorization': 'Bearer ' + creds["token"]}
        res = requests.get(config.email_url, headers=headers)
        if res.status_code == 200:
            res_json = res.json()
            email = res_json["email"]

        url = utils.build_url(
            base_url, {'mode': 'list_options'})
        li = xbmcgui.ListItem(email)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    # Add Account Button
    url = utils.build_url(base_url, {'mode': 'new_account'})
    li = xbmcgui.ListItem('Add New Account')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
else:
    if os.path.exists(token_path):
        creds = read_credentials(token_path)
    token = creds["token"]
    eval(mode[0] + '()')
