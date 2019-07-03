# -*- coding: utf-8 -*-

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcaddon
import xbmcgui
import xbmcplugin
import requests
import simplejson as json
import xbmc
import inputstreamhelper

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]

# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])


VIDEOS = [
    {
        'name': 'ViuTV 99台',
        'thumb': 'https://static.viu.tv/public/images/amsUpload/201701/1484127151250_ChannelLogo99.jpg',
        'video': 'https://dummy/viutv99.m3u8',
    },
    {
        'name': '港台電視 RTHK-TV 31',
        'thumb': 'https://www.rthk.hk/assets/rthk/images/tv/player/500x281.jpg',
        'video': 'https://www.rthk.hk/feeds/dtt/rthktv31_https.m3u8',
    },
    {
        'name': '港台電視 RTHK-TV 32',
        'thumb': 'https://www.rthk.hk/assets/rthk/images/tv/player/500x281.jpg',
        'video': 'https://www.rthk.hk/feeds/dtt/rthktv32_https.m3u8',
    },
    {
        'name': '有線新聞台',
        'thumb': 'https://vignette.wikia.nocookie.net/evchk/images/f/f8/Cablelogo.gif/revision/latest',
        'video': 'https://dummy/cabletv.m3u8',
    },
    {
        'name': '香港開電視 77台',
        'thumb': 'http://plib.aastocks.com/aafnnews/image/medialib/20181026093830853_m.jpg',
        'video': 'http://media.fantv.hk/m3u8/archive/channel2.m3u8',
    },
]

facebook_pages = [
    'https://www.facebook.com/hk.nextmedia/videos/',
    'https://www.facebook.com/standnewshk/videos/',
]

def get_cabletv():
    params = {
        "device": "aos_mobile",
        "channel_no": "_9",
        "method": "streamingGenerator2",
        "quality": "m",
        "uuid": "",
        "vlink": "_9",
        "is_premium": "0",
        "network": "wifi",
        "platform": "1",
        "deviceToken": "",
        "appVersion": "6.3.4",
        "market": "G",
        "lang": "zh_TW",
        "version": "6.3.4",
        "osVersion": "23",
        "channel_id": "106",
        "deviceModel": "KODI",
        "type": "live",
    }

    response = requests.get(
        'https://mobileapp.i-cable.com/iCableMobile/API/api.php',
        headers={
            'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 6.0.1; F8132 Build/35.0.A.1.282)',
        },
        params={
            'data': json.dumps(params),
        }
    )

    return response.json()['result']['stream']


def get_viutv():
    response = requests.post(
        'https://api.viu.now.com/p8/2/getLiveURL',
        json={
            'callerReferenceNo': "20190625160500",
            'channelno': "099",
            'deviceId': "7849989bff631f5888",
            'deviceType': "5",
            'format': "HLS",
            'mode': "prod",
        }
    )

    return response.json()['asset']['hls']['adaptive'][0]


def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))


def list_videos():
    """
    Create the list of playable videos in the Kodi interface.

    :param category: Category name
    :type category: str
    """
    # Set plugin category. It is displayed in some skins as the name
    # of the current section.
    # xbmcplugin.setPluginCategory(_handle, category)

    # Set plugin content. It allows Kodi to select appropriate views
    # for this type of content.
    xbmcplugin.setContent(_handle, 'videos')

    # Get the list of videos in the category.
    # videos = get_videos(category)

    # Iterate through videos.
    # for video in videos:
    for video in VIDEOS:
        # Create a list item with a text label and a thumbnail image.
        list_item = xbmcgui.ListItem(label=video['name'])

        # Set additional info for the list item.
        # 'mediatype' is needed for skin to display info for this ListItem correctly.
        list_item.setInfo('video', {
            'title': video['name'],
            'mediatype': 'video',
        })

        # Set graphics (thumbnail, fanart, banner, poster, landscape etc.) for the list item.
        # Here we use the same image for all items for simplicity's sake.
        # In a real-life plugin you need to set each image accordingly.
        list_item.setArt({
            'thumb': video['thumb'],
            'icon': video['thumb'],
            'fanart': video['thumb'],
        })

        # Set 'IsPlayable' property to 'true'.
        # This is mandatory for playable items!
        list_item.setProperty('IsPlayable', 'true')

        # Create a URL for a plugin recursive call.
        # Example: plugin://plugin.video.example/?action=play&video=http://www.vidsplay.com/wp-content/uploads/2017/04/crab.mp4
        url = get_url(
            action='play',
            video=video['video']
        )

        # Add the list item to a virtual Kodi folder.
        # is_folder = False means that this item won't open any sub-list.
        is_folder = False

        # Add our item to the Kodi virtual folder listing.
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    for page in facebook_pages:
        response = requests.get(
            page,
        )

        pos_start = response.text.find('hd_src')
        if pos_start > -1:
            print(pos_start)
            pos_end = response.text.find('",', pos_start)
            print(pos_end)
            if pos_end > -1:
                list_item = xbmcgui.ListItem(label='LIVE')

                list_item.setInfo('video', {
                    'title': 'LIVE',
                    'mediatype': 'video',
                })

                list_item.setArt({
                    'thumb': 'https://static.viu.tv/public/images/amsUpload/201701/1484127151250_ChannelLogo99.jpg',
                    'icon': 'https://static.viu.tv/public/images/amsUpload/201701/1484127151250_ChannelLogo99.jpg',
                    'fanart': 'https://static.viu.tv/public/images/amsUpload/201701/1484127151250_ChannelLogo99.jpg',
                })

                list_item.setProperty('IsPlayable', 'true')

                url = get_url(
                    action='play',
                    video=response.text[pos_start + 9: pos_end].replace('\\', ''),
                )

                is_folder = False

                xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)


def play_video(STREAM_URL):
    if '.mpd' in STREAM_URL:
        PROTOCOL = 'mpd'
        is_helper = inputstreamhelper.Helper(PROTOCOL)
        if is_helper.check_inputstream():
            playitem = xbmcgui.ListItem(path=STREAM_URL)
            playitem.setProperty('inputstreamaddon', is_helper.inputstream_addon)
            playitem.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
            xbmc.Player().play(item=STREAM_URL, listitem=playitem)
    else:
        playitem = xbmcgui.ListItem(path=STREAM_URL)
        xbmc.Player().play(item=STREAM_URL, listitem=playitem)


def router(paramstring):
    """
    Router function that calls other functions
    depending on the provided paramstring

    :param paramstring: URL encoded plugin paramstring
    :type paramstring: str
    """
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))

    # Check the parameters passed to the plugin
    if params:
        if params['action'] == 'play':
            # Play a video from a provided URL.

            if params['video'] == 'https://dummy/viutv99.m3u8':
                url = get_viutv()
            elif params['video'] == 'https://dummy/cabletv.m3u8':
                url = get_cabletv()
            else:
                url = params['video']

            play_video(url)
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters,
        # display the list of video categories
        # list_categories()
        list_videos()


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring

    router(sys.argv[2][1:])
