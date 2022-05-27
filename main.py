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


from resources.lib.auth import read_credentials, get_device_code
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
addon_path = __addon__.getAddonInfo('path')
profile_path = xbmcvfs.translatePath(
    __addon__.getAddonInfo('profile'))
token_folder = Path(profile_path + config.token_folder)
token_path = None
if args.get('token_filename'):
    token_path = Path(token_folder / args.get('token_filename')[0])
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
    baseUrl = __addon__.getSettingString('baseUrl')
    dialog_msg = f'Visit {baseUrl} and enter the code:\n'
    login_dialog.create('Authenticate', dialog_msg + user_code)

    # Update progress dialog indicating time left for complete
    sleep_time = utils.sleep_time(code_json['expires_in'])
    xbmc.log(str(sleep_time), xbmc.LOGDEBUG)
    time = 99
    while time >= 0:
        login_dialog.update(time)
        if login_dialog.iscanceled():
            break
        xbmc.sleep(sleep_time)
        # TODO: Handle the case of server going down
        status_code = auth.fetch_and_save_token(
            code_json['deviceCode'], token_folder)
        # TODO: Time parameter
        if status_code == 200:
            xbmc.executebuiltin(
                'Notification(Success, Account added successfully, time=3000)')
            break
        if status_code == 403:
            xbmc.sleep(10000)
        elif status_code != 202:
            xbmc.log(status_code, xbmc.LOGDEBUG)
        if time == 0:
            code_json = get_device_code()
            time = 100
            login_dialog.update(time, message=dialog_msg +
                                code_json["userCode"])
            xbmc.executebuiltin('Notification(Code refreshed, ,time=3000)')
        time -= 1

    login_dialog.close()
    xbmc.executebuiltin('Container.Refresh')


def remove_account():
    xbmcvfs.delete(str(token_path))
    xbmc.executebuiltin('Container.Refresh')


def list_options():
    items = []

    # Third string in the tuples are API endpoint's route
    modes = [('All Media', 'list_media', 'all'),
             ('All Albums', 'list_albums', 'albums'), ('Shared Albums',
                                                       'list_albums', 'sharedAlbums'),
             ('Custom Filter', 'custom_filter')]

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
        error = 'Unable to retrieve media items from Google'
        res = requests.get(config.service_endpoint + '/mediaItems',
                           headers=headers, params=params)
    elif list_type == 'album':
        error = 'Unable to load album items'
        params['albumId'] = args.get('id')[0]
        res = requests.post(config.service_endpoint + '/mediaItems:search',
                            headers=headers, data=params)
    elif list_type == 'filter':
        # params
        params['filters'] = utils.buildFilter(__addon__)
        if not bool(params['filters']):
            return None
        error = 'Error in filtering photos'
        res = requests.post(config.service_endpoint + '/mediaItems:search',
                            headers=headers, json=params)
    if res.status_code != 200:
        dialog = xbmcgui.Dialog()
        dialog.notification(
            'Error', f'{error}. Error Code:{res.status_code}', xbmcgui.NOTIFICATION_ERROR, 3000)
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
            xbmc.executebuiltin(
                'Notification(No items, No Media Item to load, time=3000)')
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
        li = xbmcgui.ListItem('Show more...')
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
        xbmc.executebuiltin(
            'Notification(Error, Video is not ready for viewing yet, time=3000)')
    else:
        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=args.get('path')[0])
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)


def custom_filter():
    __addon__.openSettings()
    url = utils.build_url(
        base_url, {'mode': 'list_media', 'type': 'filter'}, qs)
    li = xbmcgui.ListItem('Display Filtered Results')
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
            'Error', f'Unable to retrieve album list. Error Code:{res.status_code}', xbmcgui.NOTIFICATION_ERROR, 3000)
    else:
        album_data = res.json()  # { albums, nextPageToken}
        # Album cover is also available in API. Useful for nameless albums
        items = []
        if album_data:
            for album in album_data[request_type]:
                url = utils.build_url(
                    base_url, {'mode': 'list_media', 'type': 'album', 'id': album["id"], 'token_filename': token_path.name})
                if 'title' in album:
                    li = xbmcgui.ListItem(album["title"])
                else:
                    li = xbmcgui.ListItem(f'Nameless album {a_num}')
                    a_num += 1
                thumb_url = album["coverPhotoBaseUrl"] + \
                    f'=w{xbmcgui.getScreenWidth()}-h{xbmcgui.getScreenHeight()}'
                li.setArt(
                    {'thumb': thumb_url})
                # Better way must be there
                items.append((url, li, True))

        xbmcplugin.addDirectoryItems(
            addon_handle, items, totalItems=len(items))

        # Pagination
        if 'nextPageToken' in album_data:
            url = utils.build_url(
                base_url, {'mode': 'list_albums', 'pageToken': album_data['nextPageToken'], 'token_filename': token_path.name, 'type': request_type})
            li = xbmcgui.ListItem('Next Page')
            # icon = os.path.join(addon_path, 'resources',
            #                     'lib', 'download.png')
            # li.setArt({'thumb': icon, 'icon': icon})
            xbmcplugin.addDirectoryItem(addon_handle, url, li, True)

        xbmcplugin.endOfDirectory(addon_handle)


if mode is None:
    # Display logged in accounts
    token_folder.mkdir(parents=True, exist_ok=True)
    for file in token_folder.iterdir():
        creds = read_credentials(file)
        email = creds["email"]
        url = utils.build_url(
            base_url, {'mode': 'list_options', 'token_filename': file.name})
        li = xbmcgui.ListItem(email)
        removePath = utils.build_url(
            base_url, {'mode': 'remove_account', 'email': email, 'token_filename': file.name})
        contextItems = [('Remove Account', f'RunPlugin({removePath})')]
        li.addContextMenuItems(contextItems)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                    listitem=li, isFolder=True)
    # Add Account Button
    url = utils.build_url(base_url, {'mode': 'new_account'})
    li = xbmcgui.ListItem('Add New Account')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,
                                listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
else:
    # Read account credentials if present
    if token_path:
        creds = read_credentials(token_path)
        token = creds["token"]
    eval(mode[0] + '()')  # Fire up the actual function


# Updates:
    # Slideshow

# Not on list
    # Video seeking - Not possible due to API limitations
