from resources.globals import *
from adobepass.adobe import ADOBE


def categories():
    headers = {
        'User-Agent': UA_NBCSN
    }

    r = requests.get(ROOT_URL + 'apps/NBCSports/configuration-firetv.json?version=5.12.4', headers=headers,
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
    url = ROOT_URL
    url += 'apps/NBCSports/configuration-firetv.json?version=5.12.4'
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

    if 'live-upcoming' not in url:
        json_source = sorted(json_source, key=lambda k: k['start'], reverse=True)
    else:
        json_source = sorted(json_source, key=lambda k: k['start'], reverse=False)

    for item in json_source:
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
        'channel': channel
    }

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


def sign_stream(stream_url, stream_name, stream_icon, pid):
    SERVICE_VARS['requestor_id'] = 'nbcsports'
    resource_id = get_resource_id()
    SERVICE_VARS['resource_id'] = urllib.quote(resource_id)
    adobe = ADOBE(SERVICE_VARS)
    if adobe.check_authn():
        if adobe.authorize():
            media_token = adobe.media_token()
            stream_url = get_tokenized_url(media_token, resource_id, stream_url, pid)
            stream_url += "|User-Agent=" + UA_NBCSN
            play_stream(stream_url)
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
    url = 'https://token.playmakerservices.com/cdn'
    headers = {
        "Accept": "*/*",
        "Accept-Language": "en;q=1",
        "Content-Type": "application/json",
        "User-Agent": "okhttp/3.11.0"
    }

    payload = {
        'resourceId': base64.b64encode(codecs.encode(resource_id)).decode("ascii"),
        'requestorId': 'nbcsports',
        'token': media_token,
        'cdn': 'akamai',
        'url': stream_url,
        'pid': pid,
        'application': 'NBCSports',
        'version': 'v1',
        'platform': 'desktop'
    }

    r = requests.post(url, headers=headers, cookies=load_cookies(), json=payload, verify=VERIFY)
    save_cookies(r.cookies)
    return r.json()['tokenizedUrl']


def logout():
    adobe = ADOBE(SERVICE_VARS)
    adobe.logout()


def play_stream(stream_url):
    xbmc.log('------------------------------------------------------------------------------------------')
    xbmc.log(stream_url)
    xbmc.log('------------------------------------------------------------------------------------------')

    if xbmc.getCondVisibility('System.HasAddon(inputstream.adaptive)'):
        stream = stream_url.split("|")[0]
        headers = stream_url.split("|")[1]
        listitem = xbmcgui.ListItem(path=stream)
        if KODI_VERSION >= 19:
            listitem.setProperty('inputstream', 'inputstream.adaptive')
        else:
            listitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        listitem.setProperty('inputstream.adaptive.manifest_type', 'hls')
        listitem.setProperty('inputstream.adaptive.stream_headers', headers)
        listitem.setProperty('inputstream.adaptive.license_key', "|" + headers)
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

if 'url' in params: url = urllib.unquote_plus(params["url"])
if 'name' in params: name = urllib.unquote_plus(params["name"])
if 'mode' in params: mode = int(params["mode"])
if 'icon_image' in params: icon_image = urllib.unquote_plus(params["icon_image"])
if 'requestor_id' in params: requestor_id = urllib.unquote_plus(params['requestor_id'])
if 'channel' in params: channel = urllib.unquote_plus(params['channel'])
if 'pid' in params: pid = urllib.unquote_plus(params['pid'])

if mode is None or url is None or len(url) < 1:
    categories()

elif mode == 2:
    get_sub_nav(url, icon_image)

elif mode == 4:
    scrape_videos(url)

elif mode == 5:
    sign_stream(url, name, icon_image, pid)

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
