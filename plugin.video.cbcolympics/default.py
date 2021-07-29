import sys

try:
    # Try the Python 3 libraries first
    from urllib.parse import urlencode
    from urllib.parse import parse_qsl, urljoin, quote_plus
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    isPython2 = False
except ImportError:
    # Fall-back to Python 2 libraries
    from urllib import urlencode, quote_plus
    from urlparse import parse_qsl, urljoin
    from urllib2 import Request, urlopen, HTTPError
    isPython2 = True

import xml.etree.ElementTree as ET
import datetime
import time
import json
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import urllib
import zlib

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon()

UTF8 = 'utf-8'

class SmilDocumentError(Exception):
    pass

class NoVideoNodeError(SmilDocumentError):
    pass

class NoSrcAttribError(SmilDocumentError):
    pass

# Used for encoding Python 2 strings in UTF-8 while also
# letting Python 3 just work as it normally does with
# built-in unicode strings
def py2utf8(str):
    if isPython2:
        return str.encode(UTF8)
    else:
        # Python3 strings are already unicode
        return str

def py2decodeUtf8(str):
    if isPython2:
        return str.decode(UTF8)
    else:
        # Python3 strings are already unicode
        return str

def strings(id):
    return py2utf8(addon.getLocalizedString(id))

def okDialog(message):
    xbmc.log('Showing OK dialog: ' + message)
    dialog = xbmcgui.Dialog()
    return dialog.ok(strings(30999), message)

SMIL_URL = "https://link.theplatform.com/s/ExhSPC/media/guid/2655402169/{0}/meta.smil?feed=Player%20Selector%20-%20Prod&format=smil&mbr=true&manifest=m3u"

PAGE_SIZE = 36

USERAGENT   = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:90.0) Gecko/20100101 Firefox/90.0'

TIME_FORMAT = '%I:%M %p'

httpHeaders = {
                'User-Agent': USERAGENT,
                'Accept':"application/json, text/javascript, text/html,*/*",
                'Accept-Encoding':'gzip,deflate,sdch',
                'Accept-Language':'en-US,en;q=0.8',
                'Content-Type':'application/json'
            }

SPORTS = [
        { 'title': strings(30000), 'category': 'sports/olympics/summer' },
        { 'title': strings(30001), 'category': 'sports/olympics/summer/aquatics/artistic swimming' },
        { 'title': strings(30002), 'category': 'sports/olympics/summer/archery' },
        { 'title': strings(30003), 'category': 'sports/olympics/summer/badminton' },
        { 'title': strings(30004), 'category': 'sports/olympics/summer/baseball' },
        { 'title': strings(30005), 'category': 'sports/olympics/summer/basketball' },
        { 'title': strings(30006), 'category': 'sports/olympics/summer/volleyball/beach volleyball' },
        { 'title': strings(30007), 'category': 'sports/olympics/summer/boxing' },
        { 'title': strings(30008), 'category': 'sports/olympics/summer/canoe-kayak' },
        { 'title': strings(30009), 'category': 'sports/olympics/summer/cycling' },
        { 'title': strings(30010), 'category': 'sports/olympics/summer/aquatics/diving' },
        { 'title': strings(30011), 'category': 'sports/olympics/summer/equestrian' },
        { 'title': strings(30012), 'category': 'sports/olympics/summer/fencing' },
        { 'title': strings(30013), 'category': 'sports/olympics/summer/field hockey' },
        { 'title': strings(30014), 'category': 'sports/olympics/summer/golf' },
        { 'title': strings(30015), 'category': 'sports/olympics/summer/gymnastics' },
        { 'title': strings(30016), 'category': 'sports/olympics/summer/handball' },
        { 'title': strings(30017), 'category': 'sports/olympics/summer/judo' },
        { 'title': strings(30018), 'category': 'sports/olympics/summer/karate' },
        { 'title': strings(30019), 'category': 'sports/olympics/summer/modern pentathlon' },
        { 'title': strings(30020), 'category': 'sports/olympics/summer/rowing' },
        { 'title': strings(30021), 'category': 'sports/olympics/summer/rugby' },
        { 'title': strings(30022), 'category': 'sports/olympics/summer/sailing' },
        { 'title': strings(30023), 'category': 'sports/olympics/summer/shooting' },
        { 'title': strings(30024), 'category': 'sports/olympics/summer/skateboarding' },
        { 'title': strings(30025), 'category': 'sports/olympics/summer/soccer' },
        { 'title': strings(30026), 'category': 'sports/olympics/summer/softball' },
        { 'title': strings(30027), 'category': 'sports/olympics/summer/sport climbing' },
        { 'title': strings(30028), 'category': 'sports/olympics/summer/surfing' },
        { 'title': strings(30029), 'category': 'sports/olympics/summer/aquatics/swimming' },
        { 'title': strings(30030), 'category': 'sports/olympics/summer/table tennis' },
        { 'title': strings(30031), 'category': 'sports/olympics/summer/taekwondo' },
        { 'title': strings(30032), 'category': 'sports/olympics/summer/tennis' },
        { 'title': strings(30033), 'category': 'sports/olympics/summer/track and field' },
        { 'title': strings(30034), 'category': 'sports/olympics/summer/triathlon' },
        { 'title': strings(30035), 'category': 'sports/olympics/summer/volleyball/volleyball' },
        { 'title': strings(30036), 'category': 'sports/olympics/summer/aquatics/water polo' },
        { 'title': strings(30037), 'category': 'sports/olympics/summer/weightlifting' },
        { 'title': strings(30038), 'category': 'sports/olympics/summer/wrestling' },
    ]

STATIC_ENTRIES = [
        {
            'title': strings(30200),
            'type': 'folder',
            'page': 'live_videos',
            'uri': 'live_videos',
        },
        {
            'title': strings(30201),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'sports/olympics/summer/replays',
        },
        {
            'title': strings(30202),
            'type': 'folder',
            'page': 'sports',
        },
        {
            'title': strings(30203),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'sports/olympics/summer/highlights',
        },
        {
            'title': strings(30204),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'Sports/Olympics/Summer/Team Canada',
        },
        {
            'title': strings(30205),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'Sports/Olympics/Features/Kraft While You Were Sleeping',
        },
        {
            'title': strings(30206),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'sports/olympics/features/Petro Canada The Bond',
        },
        {
            'title': strings(30207),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'sports/olympics/features/RBC Spotlight',
        },
        {
            'title': strings(30208),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'sports/olympics/features/Toyota Breakthrough',
        },
        {
            'title': strings(30209),
            'type': 'folder',
            'page': 'clips_by_category',
            'category': 'sports/olympics/features/VISA Olympic Moments',
        }
    ]

# Lovingly borrowed from t1mlib
def get_url(**kwargs):
    try:
        return '{0}?{1}'.format(_url, urlencode(kwargs))
    except:
        raise ValueError(str(kwargs))

# Lovingly borrowed from t1mlib
def getRequest(url, udata=None, headers = httpHeaders, dopost = False, rmethod = None):
    req = Request(py2utf8(url), udata, headers)

    if dopost == True:
        rmethod = "POST"

    if rmethod is not None:
        req.get_method = lambda: rmethod

    #try:
    response = urlopen(req, timeout=60)
    page = response.read()

    if response.headers.get('Content-Encoding') == 'gzip':
        page = zlib.decompress(page, zlib.MAX_WBITS + 16)
    #except:
    #  page = ""
    return(page.decode(UTF8))        # Decode from UTF-8: Slight change from the library version

def list_entries(folder_title, entries):
    xbmcplugin.setPluginCategory(_handle, folder_title)
    xbmcplugin.setContent(_handle, 'episodes')

    for entry in entries:
        # Set the listing entry's title to either listing_title or title
        list_item = xbmcgui.ListItem(entry.get('listing_title', entry['title']))

        if entry['type'] == 'video':
            list_item.setInfo('video',
                {
                    'title': entry['title'],
                    'plot': entry.get('description', None),
                    'mediatype': 'video'
                })

            # Set the stream duration if it was provided so it shows
            # in the listing
            duration = entry.get('duration')
            if duration is not None:
                list_item.addStreamInfo('video',
                    {
                        'duration': duration
                    })

            list_item.setArt(entry['art'])
            list_item.setProperty('IsPlayable', 'true')

            url = get_url(action='play', title=py2utf8(entry['title']), videoId=entry.get('videoId', ''), isUpcoming=entry.get('isUpcoming', False))

            is_folder = False

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

        elif entry['type'] == 'folder':
            list_item.setProperty('IsPlayable', 'false')

            url = get_url(action='listing', page=entry['page'], title=py2utf8(entry['title']), uri=entry.get('uri'), category=entry.get('category'), pageNo=entry.get('pageNo', 1))

            is_folder = True

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def entries_append_video(entries, video):
    duration = video.get('duration')

    airDate = datetime.datetime.fromtimestamp(video.get('airDate', 0) / 1000)
    isLive = video.get('isLive', False)
    isUpcoming = (airDate > datetime.datetime.now())

    if isLive or isUpcoming:
        # For future scheduled events, include the event start time in the title
        try:
            # Get the event start time string, stripping off leading zeroes because
            # apparently Python doesn't have a format specifier for 12-hour hours
            # without leading zeroes
            airTimeStr = airDate.strftime(TIME_FORMAT).lstrip('0')

            # For events today just include the time but for
            # events on another day, include the date and time
            if datetime.datetime.now().date() == airDate.date():
                airDateStr = airTimeStr
            else:
                monthStr = airDate.strftime('%b')
                dayStr = airDate.strftime('%d').lstrip('0')       # There's that leading zero strip again
                airDateStr = '{0} {1} {2}'.format(airTimeStr, monthStr, dayStr)

            # Build a description of the start date
            if isUpcoming:
                titleState = strings(30303).format(airDateStr)
                descState = strings(30303).format(airDateStr)
            elif isLive:
                titleState = strings(30304).format(airDateStr)
                descState = strings(30304).format(airDateStr)
        except:
            # Something went wrong so just go with the default state string
            pass
    else:
        # Replay (ie. not live or upcoming)
        titleState = strings(30305)
        descState = strings(30305)

    video['title'] = u'{0} ({1})'.format(video['title'].rstrip(), titleState)
    video['description'] = u'{0}\n\n({1})'.format(video['description'], descState)

    thumbnail = video.get('thumbnail')

    entries.append(
        {
            'type': 'video',
            'title': video.get('title'),
            'description': video.get('description'),
            'videoId': video.get('id'),
            'duration': video.get('duration'),
            'isUpcoming': isUpcoming,
            'art':
            {

                'thumb': thumbnail,
                'icon': thumbnail,
                'fanart': thumbnail
            }
        })

    return

def run_graphql(graphql, variables):
    GRAPHQL_URL = 'https://www.cbc.ca/graphql'

    body = {
        'query': graphql,
        'variables': variables
    }

    return json.loads(getRequest(url=GRAPHQL_URL, udata=json.dumps(body).encode(UTF8), dopost=True))

def graphql_category_to_entries(entries, graphql_category):
    if graphql_category:
        for video in graphql_category:
            entries_append_video(entries, video)

def graphql_result_to_entries(graphql_result):
    entries = []
    data = graphql_result.get('data')
    if data:
        categories = data.get('categories')
        for category in categories:
            graphql_category_to_entries(entries, category.get('clips'))

    return entries

def list_live_videos(page_title, pageNo):
    graphql = """
query liveClips($liveFullTitle: String, $clipPageSize: Int, $clipPage: Int) {
        categories: mpxCategories(fullTitle: $liveFullTitle) {
            id
            title
            fullTitle
            clips(pageSize: $clipPageSize, page: $clipPage) {
                ...itemBase
            }
        }

    } fragment itemBase on MediaItem {
    id
    source
    title
    description
    thumbnail
    duration
    airDate
    isLive
    isVideo
}
"""

    variables = {
		"liveFullTitle": "sports/olympics/summer/live",
		"clipPage": pageNo,
		"clipPageSize": PAGE_SIZE
	}

    graphql_result = run_graphql(graphql, variables)

    entries = graphql_result_to_entries(graphql_result)

    # If we have a full page of results, append a "next page" entry
    if len(entries) == PAGE_SIZE:
        nextPageNo = pageNo + 1
        entries.append(
            {
                'title': page_title,
                'listing_title': strings(30306).format(page_title, nextPageNo),
                'type': 'folder',
                'page': 'live_videos',
                'pageNo': nextPageNo,
                'uri': 'live_videos',
            })

    return list_entries(page_title, entries)

def list_clips_by_category(page_title, category, pageNo):
    graphql = """
query clipsByCategory($fullTitle: String, $clipPageSize: Int, $clipPage: Int) {
            categories: mpxCategories(fullTitle: $fullTitle) {
                id
                title
                fullTitle
                clips(pageSize: $clipPageSize, page: $clipPage) {
                    ...itemBase
                }
            }
    } fragment itemBase on MediaItem {
    id
    title
    description
    thumbnail
    duration
    airDate
    isLive
    isVideo
}
"""

    variables = {
		"fullTitle": category,
		"clipPage": pageNo,
		"clipPageSize": PAGE_SIZE
	}

    graphql_result = run_graphql(graphql, variables)

    entries = graphql_result_to_entries(graphql_result)

    # If we have a full page of results, append a "next page" entry
    if len(entries) == PAGE_SIZE:
        nextPageNo = pageNo + 1
        entries.append(
            {
                'title': page_title,
                'listing_title': strings(30306).format(page_title, nextPageNo),
                'type': 'folder',
                'page': 'clips_by_category',
                'pageNo': nextPageNo,
                'category': category,
            })

    return list_entries(page_title, entries)

def list_sports(page_title):
    entries = []
    for sport in SPORTS:
        entries.append(
            {
                'title': sport['title'],
                'type': 'folder',
                'page': 'clips_by_category',
                'category': sport['category']
            })

    list_entries(page_title, entries)

def videoIdToM3u8Url(videoId):
    # Build URL to the video's SMIL document
    smil_url = SMIL_URL.format(videoId)
    xbmc.log('smil_url = ' + smil_url)

    try:
        # Fetch the SMIL
        smil = getRequest(smil_url)

        # Parse the SMIL document as XML
        root = ET.fromstring(smil)

        # Locate the first video element on the page
        ns = {'smil': 'http://www.w3.org/2005/SMIL21/Language'}
        video = root.find('./smil:body//smil:video', ns)
        if not video:
            raise NoVideoNodeError('SMIL document missing a video node')

        # Extract the "src" attribute of the video element
        src = video.attrib.get('src')
        if not src:
            raise NoSrcAttribError('Video node missing a src attribute')

        return src
    except Exception as err:
        xbmc.log('Error loading SMIL: ' + str(err))
        xbmc.log(smil)
        raise

def pickStreamUrlFromM3u8Url(m3u8_url):
    try:
        # Query the video manifest for the highest quality bitrate
        m3u8 = getRequest(m3u8_url)
        stream_urls = re.compile('^hdntl.*$', re.MULTILINE).findall(m3u8)

        # Get the bitrate limit setting, if there is one
        try:
            # Load the kbps bitrate setting and convert to bps
            bitrateLimitKbps = int(xbmcplugin.getSetting(_handle, 'bitrateLimitKbps'))
        except ValueError:
            bitrateLimitKbps = 10000000       # 10 Gbit/sec is essentially unlimited, right?

        # Find the highest bitrate within the setting limit
        selected_bitrateKbps = 0
        for stream_url in stream_urls:
            bitrateKbps = int(re.search('master_(\d*)', stream_url).group(1))
            if (bitrateKbps <= bitrateLimitKbps) and (bitrateKbps > selected_bitrateKbps):
                selected_stream_url = stream_url
                selected_bitrateKbps = bitrateKbps

        selected_stream_url = urljoin(m3u8_url, selected_stream_url)
        return selected_stream_url
    except HTTPError:
        # Let the HTTP errors bubble up so that the caller can handle them
        raise
    except Exception as err:
        # If any of the stream selection code above fails, just return the original m3u8
        # and let Kodi choose the stream. It will default to the first one which has
        # been the 2 Mbit stream. The user can switch streams in Kodi's UI during playback.
        xbmc.log('Error picking stream from M3U8: ' + str(err))
        xbmc.log('Falling back to playing M3U8 directly')
        return m3u8_url

def play_video(videoId, isUpcoming):
    if not videoId or (videoId == ''):
        raise ValueError(strings(30900))

    try:
        # Fetch the video's SMIL document and extract the m3u8 from it.
        # This has failed in the past so re-try to see if the error persists.
        smilAttemptsRemaining = 2
        while (smilAttemptsRemaining > 0):
            try:
                m3u8_url = videoIdToM3u8Url(videoId)

                # Success. No need to re-try.
                smilAttemptsRemaining = 0
                xbmc.log('m3u8_url: ' + m3u8_url)
            except SmilDocumentError as err:
                smilAttemptsRemaining -= 1
                if (smilAttemptsRemaining == 0):
                    # "The server did not return a valid stream. Please try again later."
                    okDialog(strings(30902))
                    return
                else:
                    xbmc.log('Re-trying SMIL fetch')

        # Fetch the video's m3u8 and pick the stream based on the user's bitrate preference
        stream_url = pickStreamUrlFromM3u8Url(m3u8_url)
        xbmc.log('stream_url: ' + stream_url)

        # Append our custom user agent because it needs to match the agent from the m3u8 request,
        # otherwise an HTTP 403 Forbidden is returned
        stream_agent_url = '{0}|User-Agent={1}'.format(stream_url, quote_plus(USERAGENT))

        # Create a playable item with a path to play.
        play_item = xbmcgui.ListItem(path=stream_agent_url)
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
    except HTTPError as err:
        if err.code == 403:
            errorMessage = strings(30903)
        elif err.code == 404:
            if isUpcoming:
                errorMessage = strings(30904)
            else:
                errorMessage = strings(30905)
        else:
            errorMessage = strings(30906).format(err.code, err.reason)

        okDialog(errorMessage)

def router(paramstring):
    # Parse a URL-encoded paramstring to the dictionary of
    # {<parameter>: <value>} elements
    params = dict(parse_qsl(paramstring))
    # Check the parameters passed to the plugin
    if params:
        page_title = py2decodeUtf8(params['title'])

        if params['action'] == 'listing':
            if params['page'] == 'live_videos':
                list_live_videos(page_title, int(params.get('pageNo', 1)))
            if params['page'] == 'clips_by_category':
                list_clips_by_category(page_title, params['category'], int(params.get('pageNo', 1)))
            if params['page'] == 'sports':
                list_sports(page_title)
            else:
                pass
        elif params['action'] == 'play':
            play_video(params.get('videoId',''), params.get('isUpcoming', 'False')=='True')
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
