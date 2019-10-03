import cookielib
from datetime import datetime, timedelta
import os, sys
import threading
import time, math
import requests
import random
import urllib
import xbmc, xbmcgui, xbmcaddon, xbmcvfs, xbmcplugin
import _strptime


if not xbmc.getCondVisibility('System.HasAddon(pvr.iptvsimple)'):
    dialog = xbmcgui.Dialog()
    dialog.notification('PS Vue EPG', 'Please enable PVR IPTV Simple Client', xbmcgui.NOTIFICATION_INFO, 5000, False)
    sys.exit()

ADDON = xbmcaddon.Addon()
PS_VUE_ADDON = xbmcaddon.Addon('plugin.video.psvue')
ADDON_PATH_PROFILE = xbmc.translatePath(PS_VUE_ADDON.getAddonInfo('profile'))
UA_ANDROID_TV = 'Mozilla/5.0 (Linux; Android 6.0.1; Hub Build/MHC19J; wv) AppleWebKit/537.36 (KHTML, like Gecko)' \
                ' Version/4.0 Chrome/61.0.3163.98 Safari/537.36'
UA_ADOBE = 'Adobe Primetime/1.4 Dalvik/2.1.0 (Linux; U; Android 6.0.1 Build/MOB31H)'
CHANNEL_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/channel'
EPG_URL = 'https://epg-service.totsuko.tv/epg_service_sony/service/v2'
SHOW_URL = 'https://media-framework.totsuko.tv/media-framework/media/v2.1/stream/airing/'
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
IPTV_SIMPLE_ADDON = xbmcaddon.Addon('pvr.iptvsimple')
SAVE_LOCATION = ADDON_PATH_PROFILE
COPY_LOCATION = xbmc.translatePath(ADDON.getSetting(id='location'))
VERIFY = True


def get_json(url):
    headers = {
        'Accept': '*/*',
        'reqPayload': PS_VUE_ADDON.getSetting(id='EPGreqPayload'),
        'User-Agent': UA_ANDROID_TV,
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'X-Requested-With': 'com.snei.vue.android',
        'Connection': 'keep-alive'
    }

    r = requests.get(url, headers=headers, cookies=load_cookies(), verify=VERIFY)

    if r.status_code != 200:
        dialog = xbmcgui.Dialog()
        msg = 'The request could not be completed.'
        try:
            json_source = r.json()
            msg = json_source['header']['error']['message']
        except:
            pass
        dialog.notification('Error ' + str(r.status_code), msg, xbmcgui.NOTIFICATION_INFO, 9000)
        sys.exit()
    return r.json()


def load_cookies():
    cookie_file = os.path.join(ADDON_PATH_PROFILE, 'cookies.lwp')
    cj = cookielib.LWPCookieJar()
    try:
        cj.load(cookie_file, ignore_discard=True)
    except:
        pass
    return cj


def find(source, start_str, end_str):
    start = source.find(start_str)
    end = source.find(end_str, start + len(start_str))
    if start != -1:
        return source[start + len(start_str):end]
    else:
        return ''


def string_to_date(string, date_format):
    try:
        date = datetime.strptime(str(string), date_format)
    except TypeError:
        date = datetime(*(time.strptime(str(string), date_format)[0:6]))
    return date


def check_iptv_setting(id, value):
    if IPTV_SIMPLE_ADDON.getSetting(id) != value:
        IPTV_SIMPLE_ADDON.setSetting(id=id, value=value)


def sleep(time, units):
    if units == 'm':
        time /= 1000
    elif units == 'M':
        time *= 60

    xbmc.Monitor().waitForAbort(time)


def get_channel_list():
    json_source = get_json(EPG_URL + '/browse/items/channels/filter/all/sort/channeltype/offset/0/size/500')
    channel_list = []
    sort_order = 1
    for channel in json_source['body']['items']:
        title = channel['title']
        if channel['channel_type'] == 'linear':
            channel_id = str(channel['id'])
            logo = None
            for image in channel['urls']:
                if 'width' in image:
                    if image['width'] == 600 or image['width'] == 440:
                        logo = image['src']
                        break

            channel_list.append([channel_id, title, logo, sort_order])
            sort_order += 1

    return channel_list


def build_playlist(channels):
    playlist_path = os.path.join(SAVE_LOCATION, 'playlist.m3u')
    playlist_copy = os.path.join(COPY_LOCATION, 'playlist.m3u')
    m3u_file = open(playlist_path, "w")
    m3u_file.write("#EXTM3U")
    m3u_file.write("\n")

    for channel_id, title, logo in channels:
        url = 'plugin://plugin.video.psvue/?url='
        url += urllib.quote(CHANNEL_URL + '/' + channel_id)
        url += '&mode=900'

        m3u_file.write("\n")
        channel_info = '#EXTINF:-1 tvg-id="' + channel_id + '" tvg-name="' + title + '"'

        if logo is not None:
            channel_info += ' tvg-logo="' + logo + '"'
        channel_info += ' group_title="PS Vue",' + title
        m3u_file.write(channel_info + "\n")
        m3u_file.write(url + "\n")
    m3u_file.close()
    if ADDON.getSetting(id='custom_directory') == 'true':
        xbmc.log("Copying Playlist... ")
        xbmcvfs.copy(playlist_path, playlist_copy)
        xbmc.log("COPIED Playlist!!! ")

    check_iptv_setting('epgPathType', '0')
    check_iptv_setting('epgTSOverride', 'true')
    check_iptv_setting('m3uPathType', '0')
    check_iptv_setting('m3uPath', playlist_path)
    check_iptv_setting('logoFromEpg', '1')
    check_iptv_setting('logoPathType', '1')
