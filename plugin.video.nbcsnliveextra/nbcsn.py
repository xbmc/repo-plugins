from resources.lib.globals import *
from resources.lib.stream import *
from adobepass.adobe import ADOBE


def categories():
    headers = {'User-Agent': UA_NBCSN}
    r = requests.get(CONFIG_URL, headers=headers, verify=VERIFY)
    json_source = r.json()

    for item in json_source['channelChanger']:
        display_name = item['displayName']
        url = item['id']
        icon = item['channelChangerLogo']
        if url != 'nbc-sports-gold' and url != 'sports-talk' and url != 'scores' and url != 'rotoworld':
            add_dir(display_name, url, 2, icon, FANART)

def get_sub_nav(id, icon):
    headers = {'User-Agent': UA_NBCSN}

    r = requests.get(CONFIG_URL, headers=headers, verify=VERIFY)
    json_source = r.json()

    for brand in json_source['channelChanger']:
        if brand['id'] == id:
            #app_name = brand['chromecastApplicationName']
            for sub_nav in brand['subNav']:
                display_name = sub_nav['displayName']
                url = sub_nav['feedUrl']
                url = url.replace('[PLATFORM]', 'android')
                if '/feeds/' in url:
                    add_dir(display_name, url, 4, icon, FANART)
            break

def scrape_videos(url):
    headers = {
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'User-Agent': UA_NBCSN,
        'Accept-Language': 'en-us',
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'results' in json_source:
        json_source = json_source['results']
    elif 'showCase' in json_source:
        json_source = json_source['showCase']

    for item in json_source:
        # if 'show-all' in filter_list or item['sport'] in filter_list:
        #     build_video_link(item)
        if 'show-all' in filter_list or any(x in item['tags'] for x in filter_list):
            build_video_link(item)


def build_video_link(item):
    url = ''
    if 'ottStreamUrl' in item:
        url = item['ottStreamUrl']
    elif 'iosStreamUrl' in item:
        url = item['iosStreamUrl']
    elif 'videoSources' in item:
        if 'ottStreamUrl' in item['videoSources'][0]:
            url = item['videoSources'][0]['ottStreamUrl']
        elif 'iosStreamUrl' in item['videoSources'][0]:
            url = item['videoSources'][0]['iosStreamUrl']

    if 'pid' in item:
        pid = item['pid']
    else:
        pid = ""
    menu_name = item['title']
    title = menu_name
    desc = item['info']
    free = int(item['free'])
    tv_title = title
    if 'channel' in item:
        tv_title = item['channel']

    # Highlight active streams
    start_time = item['start']

    aired = start_time[0:4] + '-' + start_time[4:6] + '-' + start_time[6:8]
    genre = item['sportName']

    length = 0
    if 'length' in item:
        length = int(item['length'])

    info = {
        'plot': desc,
        'tvshowtitle': tv_title,
        'title': title,
        'originaltitle': title,
        'duration': length,
        'aired': aired,
        'genre': genre
    }

    requestor_id = 'nbcsports'
    channel = ''

    # if 'requestorId' in item and item['requestorId'] != 'nbcentertainment':
    #     requestor_id = item['requestorId']
    # if 'channel' in item:
    #     channel = item['channel']
    #
    stream_info = {
        'pid': pid,
        'requestor_id': requestor_id,
        'channel': channel,
    }
    try:
        stream_info['drm_type'] = item['videoSources'][0]['drmType']
        stream_info['drm_asset_id'] = item['videoSources'][0]['drmAssetId'].ljust(40, '0')
    except:
        pass

    imgurl = "http://hdliveextra-pmd.edgesuite.net/HD/image_sports/mobile/%s_m50.jpg" % item['image']
    # menu_name = filter(lambda x: x in string.printable, menu_name)

    start_date = stringToDate(start_time, "%Y%m%d-%H%M")
    start_date = datetime.strftime(utc_to_local(start_date), xbmc.getRegion('dateshort')
                                   + ' ' + xbmc.getRegion('time').replace('%H%H', '%H').replace(':%S', ''))
    info['plot'] = 'Starting at: ' + start_date + '\n\n' + info['plot']
    status = 3
    if 'status' in item:
        status = item['status']
    if url != '' and status != 1:
        if free:
            menu_name = '[COLOR=' + FREE + ']' + menu_name + '[/COLOR]'
            add_free_link(menu_name, url, imgurl, FANART, info)
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR=' + LIVE + ']' + menu_name + '[/COLOR]'
            add_premium_link(menu_name, url, imgurl, stream_info, FANART, info)
    else:
        if free:
            menu_name = '[COLOR=' + FREE_UPCOMING + ']' + menu_name + '[/COLOR]'
            add_dir(menu_name + ' ' + start_date, '/disabled', 0, imgurl, FANART, False, info)
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR=' + UPCOMING + ']' + menu_name + '[/COLOR]'
            add_dir(menu_name + ' ' + start_date, '/disabled', 0, imgurl, FANART, False, info)


def sign_stream(stream_url, stream_name, stream_icon, pid, drm_type, drm_asset_id):
    SERVICE_VARS['requestor_id'] = 'nbcsports'
    resource_id = get_resource_id()
    SERVICE_VARS['resource_id'] = urllib.quote(resource_id)
    adobe = ADOBE(SERVICE_VARS)
    if adobe.check_authn():
        if adobe.authorize():
            media_token = adobe.media_token()
            stream_vars = {
                'drm_asset_id': drm_asset_id,
                'drm_type': drm_type,
                'manifest_url': stream_url,
                'media_token': media_token,
                'resource_id': resource_id,
                'pid': pid
            }
            stream = Stream(stream_vars)
            xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, stream.create_listitem())
        else:
            sys.exit()
    else:
        dialog = xbmcgui.Dialog()
        answer = dialog.yesno(LOCAL_STRING(30010), LOCAL_STRING(30011))
        if answer:
            adobe.register_device()
            sign_stream(stream_url, stream_name, stream_icon, pid)
        else:
            sys.exit()


def logout():
    adobe = ADOBE(SERVICE_VARS)
    adobe.logout()


params = get_params()
url = None
name = ''
mode = None
icon_image = None
requestor_id = ''
channel = ''
pid = ''
drm_asset_id = ''
drm_type = ''

if 'url' in params: url = urllib.unquote_plus(params["url"])
if 'name' in params: name = urllib.unquote_plus(params["name"])
if 'mode' in params: mode = int(params["mode"])
if 'icon_image' in params: icon_image = urllib.unquote_plus(params["icon_image"])
if 'requestor_id' in params: requestor_id = urllib.unquote_plus(params['requestor_id'])
if 'channel' in params: channel = urllib.unquote_plus(params['channel'])
if 'pid' in params: pid = urllib.unquote_plus(params['pid'])
if 'drm_asset_id' in params: drm_asset_id = urllib.unquote_plus(params['drm_asset_id'])
if 'drm_type' in params: drm_type = urllib.unquote_plus(params['drm_type'])

if mode is None or url is None or len(url) < 1:
    categories()

elif mode == 2:
    get_sub_nav(url, icon_image)

elif mode == 4:
    scrape_videos(url)

elif mode == 5:
    sign_stream(url, name, icon_image, pid, drm_type, drm_asset_id)

elif mode == 6:
    stream_vars = {
        'drm_asset_id': drm_asset_id,
        'drm_type': drm_type,
        'manifest_url': url,
        'pid': pid
    }
    stream = Stream(stream_vars)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, stream.create_listitem())

elif mode == 999:
    logout()

# Don't cache content lists
if mode and mode > 4:
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
else:
    xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=False)