import sys
from urllib import urlencode
from urlparse import urlparse, parse_qsl
import json
import re
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import urllib2
import zlib

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon()

UTF8 = 'utf-8'

def strings(id):
    return addon.getLocalizedString(id).encode(UTF8)

CBC_HOST = 'https://olympics.cbc.ca'

USERAGENT   = 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'

httpHeaders = {'User-Agent': USERAGENT,
                'Accept':"application/json, text/javascript, text/html,*/*",
                'Accept-Encoding':'gzip,deflate,sdch',
                'Accept-Language':'en-US,en;q=0.8'
                }

DISCIPLINES = [
    {'code': 'as', 'name': strings(30001)},
    {'code': 'bt', 'name': strings(30002)},
    {'code': 'bs', 'name': strings(30003)},
    {'code': 'cu', 'name': strings(30004)},
    {'code': 'cc', 'name': strings(30005)},
    {'code': 'fs', 'name': strings(30006)},
    {'code': 'fr', 'name': strings(30007)},
    {'code': 'ih', 'name': strings(30008)},
    {'code': 'lg', 'name': strings(30009)},
    {'code': 'nc', 'name': strings(30010)},
    {'code': 'sb', 'name': strings(30011)},
    {'code': 'sj', 'name': strings(30012)},
    {'code': 'sn', 'name': strings(30013)},
    {'code': 'ss', 'name': strings(30014)},
    {'code': 'st', 'name': strings(30015)},
]

EVENT_DATES = [
    {'name': strings(30099), 'offset': '-1'},
    {'name': strings(30100), 'offset': '1'},      # CBC skipped zero for some reason
    {'name': strings(30101), 'offset': '2'},
    {'name': strings(30102), 'offset': '3'},
    {'name': strings(30103), 'offset': '4'},
    {'name': strings(30104), 'offset': '5'},
    {'name': strings(30105), 'offset': '6'},
    {'name': strings(30106), 'offset': '7'},
    {'name': strings(30107), 'offset': '8'},
    {'name': strings(30108), 'offset': '9'},
    {'name': strings(30109), 'offset': '10'},
    {'name': strings(30110), 'offset': '11'},
    {'name': strings(30111), 'offset': '12'},
    {'name': strings(30112), 'offset': '13'},
    {'name': strings(30113), 'offset': '14'},
    {'name': strings(30114), 'offset': '15'},
    {'name': strings(30115), 'offset': '16'},
    {'name': strings(30116), 'offset': '17'},
]

STATIC_ENTRIES = [
            {
                'type': 'folder',
                'page': 'json_videos_bysport',
                'title': strings(30200),
                'uri': 'condensed-events',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bydate',
                'title': strings(30201),
                'uri': 'condensed-events',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bysport',
                'title': strings(30202),
                'uri': 'replays',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bydate',
                'title': strings(30203),
                'uri': 'replays',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bysport',
                'title': strings(30204),
                'uri': 'highlights',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bydate',
                'title': strings(30205),
                'uri': 'highlights',
            },
            {
                'type': 'folder',
                'page': 'json_videos',
                'title': strings(30206),
                'uri': 'https://olympics.cbc.ca/api-live/online-listing/must-see/list.json',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bysport',
                'title': strings(30207),
                'uri': 'schedule',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bydate',
                'title': strings(30208),
                'uri': 'schedule',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bysport',
                'title': strings(30209),
                'uri': 'whats-on-tv',
            },
            {
                'type': 'folder',
                'page': 'json_videos_bydate',
                'title': strings(30210),
                'uri': 'whats-on-tv',
            },
        ]

# Lovingly borrowed from t1mlib
def get_url(**kwargs):
    try:
        return '{0}?{1}'.format(_url, urlencode(kwargs))
    except:
        raise ValueError(str(kwargs))

# Lovingly borrowed from t1mlib
def getRequest(url, udata=None, headers = httpHeaders, dopost = False, rmethod = None):
    req = urllib2.Request(url.encode(UTF8), udata, headers)  

    if dopost == True:
       rmethod = "POST"

    if rmethod is not None:
        req.get_method = lambda: rmethod

    try:
      response = urllib2.urlopen(req, timeout=60)
      page = response.read()
      if response.info().getheader('Content-Encoding') == 'gzip':
         page = zlib.decompress(page, zlib.MAX_WBITS + 16)
    except:
      page = ""
    return(page.decode(UTF8))        # Decode from UTF-8: Slight change from the library version

def list_entries(folder_title, entries):
    xbmcplugin.setPluginCategory(_handle, folder_title)
    xbmcplugin.setContent(_handle, 'episodes')

    for entry in entries:
        list_item = xbmcgui.ListItem(entry['title'])

        if entry['type'] == 'video':
            list_item.setInfo('video',
                {
                    'title': entry['title'],
                    'plot': entry.get('description', None),
                    'mediatype': 'video'
                })

            list_item.setArt(entry['art'])
            list_item.setProperty('IsPlayable', 'true')

            url = get_url(action='play', title=entry['title'].encode(UTF8), url=entry.get('url', ''), videoId=entry.get('videoId', ''))

            is_folder = False

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

        elif entry['type'] == 'folder':
            list_item.setProperty('IsPlayable', 'false')

            url = get_url(action='listing', page=entry['page'], title=entry['title'].encode(UTF8), uri=entry.get('uri', None))

            is_folder = True

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def get_video_json_url(category, filter_name, filter_value):
    return CBC_HOST + '/api-live/online-listing/{0}/{1}={2}/list.json'.format(category, filter_name, filter_value)

# category: replays, highlights
def list_json_videos_bysport(folder_title, category):
    entries = []
    for discipline in DISCIPLINES:
        entries.append(
            {
                'type': 'folder',
                'page': 'json_videos',
                'title': discipline['name'],
                'uri': get_video_json_url(category, 'discipline', discipline['code']),
            })

    return list_entries(folder_title, entries)

# category: replays, highlights
def list_json_videos_bydate(folder_title, category):
    entries = []
    for event_date in EVENT_DATES:
        entries.append(
            {
                'type': 'folder',
                'page': 'json_videos',
                'title': event_date['name'],
                'uri': get_video_json_url(category, 'day', event_date['offset']),
            })

    return list_entries(folder_title, entries)

def list_json_append_video(entries, video):
    try:
        if ('state' in video) and (video['state'] != ''):
            video['description'] = u'{0}\n\n({1})'.format(video['description'], video['state'].title())
            video['title'] = u'{0} ({1})'.format(video['title'].rstrip(), video['state'])
    except:
        raise ValueError(str(video))

    entries.append(
        {
            'type': 'video',
            'title': video['title'],
            'description': video['description'],
            'videoId': video['key'],
            'art':
            {

                'thumb': CBC_HOST + video['thumb'],
                'icon': CBC_HOST + video['thumb'],
                'fanart': CBC_HOST + video['thumb']
            }
        })

    return

def list_json_videos(folder_title, url):
    # URL: https://olympics.cbc.ca/api-live/online-listing/replays/discipline=cu/list.json

    json_response = json.loads(getRequest(url))

    entries = []
    if 'sports' in json_response:
        for sport in json_response['sports']:
            for video in sport['videos']:
                list_json_append_video(entries, video)
    elif 'videos' in json_response:
        for video in json_response['videos']:
            list_json_append_video(entries, video)

    return list_entries(folder_title, entries)

def videoIdToIsmUrl(videoId):
    # Build URL to the video's XML document
    xml_url = 'https://olympics.cbc.ca/videodata/{0}.xml'

    # Fetch the XML
    xml = getRequest(xml_url.format(videoId))

    # Isolate the HLS videoSource tag content
    xml = re.compile('<videoSource format="HLS"(.+?)</videoSource>', re.DOTALL).search(xml).group(1)

    # Get the URL for the video player's source
    # Example: https://dvr-i-cbc.akamaized.net/dvr/358abd65-c827-4e6f-ac3d-751c445eba59/358abd65-c827-4e6f-ac3d-751c445eba59.ism/manifest(format=m3u8-aapl-v3,audioTrack=english,filter=hls)
    # We can't use this as the actual video URL as it requires some kind of handshake
    videosource_url = re.compile('<uri>(.+?)</uri>', re.DOTALL).search(xml).group(1)

    # Get the videoSource's .ism URL
    return videosource_url.split('.ism')[0] + '.ism'

def videoPageUrlToIsmUrl(videoUrl):
    # Get the video page's HTML
    html = getRequest(videoUrl)

    # Parse the video id from the tag <input name="videoId" value="44267" type="hidden">
    videoId = re.compile('<input type="hidden" name="videoId" value="(.+?)"', re.DOTALL).search(html).group(1)

    return videoIdToIsmUrl(videoId)

def videoIsmUrlToMpegUrl(video_ism_url):
    # Works
    # https://vod-i-cbc.akamaized.net/vod/48dd5257-cbb1-425e-a499-a7293b55d4f4/Social-Who-Is-Tongas-Flag-Bearer.ism/QualityLevels(3257373)/Manifest(video,format=m3u8-aapl-v3,audiotrack=aac_UND_1_56,filter=hls)

    # Error
    # https://vod-i-cbc.akamaized.net/vod/48dd5257-cbb1-425e-a499-a7293b55d4f4/Social-Who-Is-Tongas-Flag-Bearer.ism/QualityLevels(3257373)/Manifest(video,format=m3u8-aapl-v3,audiotrack=english,filter=hls)

    user_agent = 'Mozilla%2F5.0%20%28Windows%20NT%2010.0%3B%20Win64%3B%20x64%3B%20rv%3A58.0%29%20Gecko%2F20100101%20Firefox%2F58.0'

    # Query the video manifest for the highest quality bitrate
    xml = getRequest(video_ism_url + '/manifest')
    xml_streams = re.compile('<StreamIndex (.+)>(.+?)</StreamIndex>', re.DOTALL).search(xml).group(1)
    quality_levels = re.compile('<QualityLevel Index="(.+?)" Bitrate="(.+?)"', re.DOTALL).findall(xml_streams)

    # Find the highest quality level
    highest_quality = 0
    for quality_level in quality_levels:
        if int(quality_level[1]) > highest_quality:
            highest_quality = int(quality_level[1])

    # Default to the most popular highest quality level
    if highest_quality == 0:
        highest_quality = 3449984

    # Get the audio track format
    # Find all stream tags
    xml_stream_tags = re.compile('<StreamIndex (.+?)>', re.DOTALL).findall(xml)

    # Find all stream tags that have type="audio" in them
    xml_audio_tags = [xml_stream_tag for xml_stream_tag in xml_stream_tags if xml_stream_tag.lower().find('type="audio"') != -1]

    # Prepare the name regex
    name_regex = re.compile('name="(.+?)"', re.DOTALL)

    # Get the first stream's audio track as default
    audiotrack = name_regex.search(xml_audio_tags[0].lower()).group(1)

    # If the first stream is not english, look for any other streams that say "eng"
    if audiotrack.find('eng') == -1:
        for xml_audio_tag in xml_audio_tags:
            audiotrack_eng = name_regex.search(xml_audio_tag.lower()).group(1)
            if audiotrack_eng.find('eng') != -1:
                audiotrack = audiotrack_eng

    url = video_ism_url + '/QualityLevels({0})/Manifest(video,format=m3u8-aapl-v3,audiotrack={1},filter=hls)|User-Agent={2}'.format(highest_quality, audiotrack, user_agent)

    return url

def play_video(page_url, videoId):
    if videoId != '':
        ism_url = videoIdToIsmUrl(videoId)
    elif page_url != '':
        ism_url = videoPageUrlToIsmUrl(page_url)
    else:
        raise ValueError(strings(30900))

    # Create a playable item with a path to play.
    play_item = xbmcgui.ListItem(path=videoIsmUrlToMpegUrl(ism_url))
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def router(paramstring):
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        page_title = params['title'].decode(UTF8)

        if params['action'] == 'listing':
            if params['page'] == 'json_videos_bysport':
                list_json_videos_bysport(page_title, params['uri'])
            if params['page'] == 'json_videos_bydate':
                list_json_videos_bydate(page_title, params['uri'])
            if params['page'] == 'json_videos':
                list_json_videos(page_title, params['uri'])
            else:
                pass
        elif params['action'] == 'play':
            play_video(params.get('url', ''), params.get('videoId',''))
        else:
            # If the provided paramstring does not contain a supported action
            # we raise an exception. This helps to catch coding errors,
            # e.g. typos in action names.
            raise ValueError(strings(30901).format(paramstring))
    else:
        # If the plugin is called from Kodi UI without any parameters
        list_entries(strings(30300), STATIC_ENTRIES)


if __name__ == '__main__':
    # Call the router function and pass the plugin call parameters to it.
    # We use string slicing to trim the leading '?' from the plugin call paramstring
    router(sys.argv[2][1:])
