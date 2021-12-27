from resources.lib.globals import *
from resources.lib.stream import *
from adobepass.adobe import ADOBE


def categories():
    headers = {
        'User-Agent': UA_NBCSN
    }

    r = requests.get(CONFIG_URL, headers=headers,
                     verify=VERIFY)
    json_source = r.json()

    for item in json_source['brands']:
        display_name = item['display-name']
        url = item['id']
        icon = item['channelChangerLogo']
        add_dir(display_name, url, 2, icon, FANART)

    # r = requests.get(ROOT_URL + 'apps/NBCSportsGold/configuration-firetv.json', headers=headers, verify=VERIFY)
    # json_source = r.json()
    #
    # for item in json_source['brands']:
    #     display_name = item['display-name']
    #     url = item['id']
    #     icon = item['channelChangerLogo']
    #     add_dir(display_name, url, 2, icon, FANART)


def get_sub_nav(id, icon):
    headers = {
        'User-Agent': UA_NBCSN
    }
    url = CONFIG_URL
    # if id == 'nbc-sports-gold':
    #     url += 'apps/NBCSportsGold/configuration-firetv.json'
    # else:
    #     url += 'apps/NBCSports/configuration-firetv.json'

    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    for brand in json_source['brands']:
        if brand['id'] == id:
            for sub_nav in brand['sub-nav']:
                display_name = sub_nav['display-name']
                url = sub_nav['feed-url']
                add_dir(display_name, url, 4, icon, FANART)
            break


def scrape_videos(url):
    url = 'https://api-leap.nbcsports.com/feeds/assets?application=NBCSports&env=prod&format=v1&platform=androidTV&sections=all&size=35&statuses=Replay'
    headers = {
        'Connection': 'keep-alive',
        'Accept': '*/*',
        'User-Agent': UA_NBCSN,
        'Accept-Language': 'en-us',
    }

    r = requests.get(url, headers=headers, verify=VERIFY)
    json_source = r.json()

    if 'featured' in url:
        json_source = json_source['showCase']

    # if 'live-upcoming' not in url:
    #     json_source = sorted(json_source, key=lambda k: k['start'], reverse=True)
    # else:
    #     json_source = sorted(json_source, key=lambda k: k['start'], reverse=False)

    for item in json_source['results']:
        if 'show-all' in filter_list or item['sport'] in filter_list:
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
        stream_info['drm_asset_id'] = item['videoSources'][0]['drmAssetId']
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
            #add_free_link(name, link_url, iconimage, fanart=None, info=None)
        elif FREE_ONLY == 'false':
            menu_name = '[COLOR=' + LIVE + ']' + menu_name + '[/COLOR]'
            add_premium_link(menu_name, url, imgurl, stream_info, FANART, info)
            #(name, link_url, iconimage, requestor_id, fanart=None, info=None)
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
            # stream_url = get_tokenized_url(media_token, resource_id, stream_url, pid)
            # drm_token = get_drm_token(media_token, resource_id, pid)
            # stream_url += "|User-Agent=" + UA_NBCSN
            # play_stream(stream_url, drm_token)
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


def get_tokenized_url(media_token, resource_id, stream_url, pid):
    #url = 'http://token.playmakerservices.com/cdn'
    url = 'https://tokens.playmakerservices.com'
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en;q=1",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.11.0"
    }

    payload = {
      "application": "NBCSports",
      "authInfo": {
        "authenticationType": "adobe-pass",
        "requestorId": "nbcsports",
        "resourceId": base64.b64encode(codecs.encode(resource_id)).decode("ascii"),
        "token": media_token
      },
      "cdns": [
        {
          "name": "akamai",
          "url": stream_url
        }
      ],
      "pid": pid,
      "platform": "firetv"
    }

    # payload = {
    #     'resourceId': base64.b64encode(codecs.encode(resource_id)).decode("ascii"),
    #     'requestorId': 'nbcsports',
    #     'token': media_token,
    #     'cdn': 'akamai',
    #     'url': stream_url,
    #     'pid': pid,
    #     'application': 'NBCSports',
    #     'version': 'v1',
    #     'platform': 'firetv'
    # }
    xbmc.log(str(payload))
    r = requests.post(url, headers=headers, cookies=load_cookies(), json=payload, verify=VERIFY)
    save_cookies(r.cookies)

    xbmc.log(r.text)

    return r.json()['akamai'][0]['tokenizedUrl']


def get_drm_token(media_token, resource_id, pid):
    url = 'https://tokens.playmakerservices.com'
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en;q=1",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.11.0"
    }

    payload = {
        "application": "NBCSports",
        "pid": pid,
        "platform": "firetv",
        "authInfo": {
            "authenticationType": "adobe-pass",
            "requestorId": "nbcsports",
            "resourceId": base64.b64encode(codecs.encode(resource_id)).decode("ascii"),
            "token": media_token
        },
        "drmInfo":
            {
                "assetId":"0D9978F6344C4646A0CCFFE40B5D106300000000",
                "deviceId":"c577f1f28b8d181d"
            }
        }

    xbmc.log(str(payload))
    r = requests.post(url, headers=headers, cookies=load_cookies(), json=payload, verify=VERIFY)
    save_cookies(r.cookies)
    xbmc.log(r.text)

    return r.json()['drmToken']


def logout():
    adobe = ADOBE(SERVICE_VARS)
    adobe.logout()


def play_stream(stream_url, drm_token):
    xbmc.log('------------------------------------------------------------------------------------------')
    xbmc.log(stream_url)
    xbmc.log(drm_token)
    xbmc.log('------------------------------------------------------------------------------------------')

    if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
        stream = stream_url.split("|")[0]
        headers = stream_url.split("|")[1]

        lic_url = 'https://widevine.license.istreamplanet.com/widevine/api/license/263b65d9-0c1f-4246-9b3f-0b500ed8c794'
        lic_headers = "User-Agent=okhttp/3.12.12"
        lic_headers += '&X-ISP-TOKEN=%s' % drm_token
        license_key = '%s|%s|R{SSM}|' % (lic_url, lic_headers)
        xbmc.log(license_key)

        is_helper = inputstreamhelper.Helper('hls', drm='widevine')
        if not is_helper.check_inputstream():
            sys.exit()

        listitem = xbmcgui.ListItem(path=stream)
        if KODI_VERSION >= 19:
            listitem.setProperty('inputstream', 'inputstream.adaptive')
        else:
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.stream_headers', 'User-Agent=%s' % UA_NBCSN)
        listitem.setProperty('inputstream.adaptive.license_key', license_key)
        listitem.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
    else:
        listitem = xbmcgui.ListItem(path=stream_url)
        listitem.setMimeType("application/x-mpegURL")

    # listitem = xbmcgui.ListItem(path=stream_url)
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem)



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
    # Set quality level based on user settings
    #stream_url = set_stream_quality(url)
    #listitem = xbmcgui.ListItem(path=stream_url)
    stream_url = url + "|User-Agent=" + UA_NBCSN
    play_stream(stream_url)

elif mode == 999:
    logout()

# Don't cache content lists
if mode == 4:
    xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=False)
else:
    xbmcplugin.endOfDirectory(ADDON_HANDLE)
