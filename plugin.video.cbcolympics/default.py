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

import datetime
import json
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import zlib

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

addon = xbmcaddon.Addon()

UTF8 = 'utf-8'

class MedianetDocumentError(Exception):
    pass

class NoUrlElementError(MedianetDocumentError):
    pass

class M3u8DocumentError(Exception):
    pass

# Used for encoding and decoding Python 2 strings in UTF-8 while also
# letting Python 3 just work as it normally does with built-in unicode strings
def py2utf8(str):
    if isPython2:
        # Python2 strings are either ASCII or UTF-8 bytes so encode to UTF-8 to maintain non-ASCII support
        return str.encode(UTF8)
    else:
        # Python3 strings are left unicode
        return str

def py3unicode(str):
    if isPython2:
        # Python2 strings are UTF-8 so leave them be
        return str
    else:
        # Python3 strings are unicode so convert it from UTF-8 bytes
        return str.decode(UTF8)

def strings(id):
    return addon.getLocalizedString(id)

def okDialog(message):
    xbmc.log('Showing OK dialog: ' + message)
    dialog = xbmcgui.Dialog()
    return dialog.ok(strings(30999), message)

PAGE_SIZE = 36

USERAGENT   = 'Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0'

TIME_FORMAT = '%I:%M %p'

httpHeaders = {
                'User-Agent': USERAGENT,
                'Accept':"application/json, text/javascript, text/html,*/*",
                'Accept-Encoding':'gzip,deflate,sdch',
                'Accept-Language':'en-US,en;q=0.8',
                'Content-Type':'application/json'
            }

SPORTS = [
        {
            'title': strings(30000),
            'url': '/sports/olympics/summer/archery',
            'slug': 'summer-olympics-archery',
        },
        {
            'title': strings(30001),
            'url': '/sports/olympics/summer/aquatics/artistic-swimming',
            'slug': 'summer-olympics-artistic-swimming',
        },
        {
            'title': strings(30002),
            'url': '/sports/olympics/summer/athletics',
            'slug': 'track-and-field',
        },
        {
            'title': strings(30003),
            'url': '/sports/olympics/summer/badminton',
            'slug': 'badminton',
        },
        {
            'title': strings(30004),
            'url': '/sports/olympics/summer/basketball',
            'slug': 'summer-olympics-basketball',
        },
        {
            'title': strings(30005),
            'url': '/sports/olympics/summer/basketball/3x3-basketball',
            'slug': '3x3-basketball',
        },
        {
            'title': strings(30006),
            'url': '/sports/olympics/summer/volleyball/beach',
            'slug': 'summer-olympics-beach-volleyball',
        },
        {
            'title': strings(30007),
            'url': '/sports/olympics/summer/boxing',
            'slug': 'summer-olympics-boxing',
        },
        {
            'title': strings(30008),
            'url': '/sports/olympics/summer/breaking',
            'slug': 'olympics-summer-breaking',
        },
        {
            'title': strings(30009),
            'url': '/sports/olympics/summer/canoe-kayak',
            'slug': 'summer-olympics-canoe-kayak',
        },
        {
            'title': strings(30010),
            'url': '/sports/olympics/summer/cycling',
            'slug': 'summer-olympics-cycling',
        },
        {
            'title': strings(30011),
            'url': '/sports/olympics/summer/aquatics/diving',
            'slug': 'summer-olympics-diving',
        },
        {
            'title': strings(30012),
            'url': '/sports/olympics/summer/equestrian',
            'slug': 'summer-olympics-equestrian',
        },
        {
            'title': strings(30013),
            'url': '/sports/olympics/summer/fencing',
            'slug': 'summer-olympics-fencing',
        },
        {
            'title': strings(30014),
            'url': '/sports/olympics/summer/field-hockey',
            'slug': 'summer-olympics-field-hockey',
        },
        {
            'title': strings(30015),
            'url': '/sports/olympics/summer/golf',
            'slug': 'summer-olympics-golf',
        },
        {
            'title': strings(30016),
            'url': '/sports/olympics/summer/gymnastics/artistic',
            'slug': 'artistic',
        },
        {
            'title': strings(30017),
            'url': '/sports/olympics/summer/gymnastics/rhythmic',
            'slug': 'rhythmic',
        },
        {
            'title': strings(30018),
            'url': '/sports/olympics/summer/gymnastics/trampoline',
            'slug': 'trampoline',
        },
        {
            'title': strings(30019),
            'url': '/sports/olympics/summer/handball',
            'slug': 'summer-olympics-handball',
        },
        {
            'title': strings(30020),
            'url': '/sports/olympics/summer/judo',
            'slug': 'summer-olympics-judo',
        },
        {
            'title': strings(30021),
            'url': '/sports/olympics/summer/modern-pentathlon',
            'slug': 'summer-olympics-modern-pentathlon',
        },
        {
            'title': strings(30022),
            'url': '/sports/olympics/summer/rowing',
            'slug': 'summer-olympics-rowing',
        },
        {
            'title': strings(30023),
            'url': '/sports/olympics/summer/rugby',
            'slug': 'summer-olympics-rugby',
        },
        {
            'title': strings(30024),
            'url': '/sports/olympics/summer/sailing',
            'slug': 'summer-olympics-sailing',
        },
        {
            'title': strings(30025),
            'url': '/sports/olympics/summer/shooting',
            'slug': 'summer-olympics-shooting',
        },
        {
            'title': strings(30026),
            'url': '/sports/olympics/summer/skateboarding',
            'slug': 'summer-olympics-skateboarding',
        },
        {
            'title': strings(30027),
            'url': '/sports/olympics/summer/soccer',
            'slug': 'summer-olympics-soccer',
        },
        {
            'title': strings(30028),
            'url': '/sports/olympics/summer/sport-climbing',
            'slug': 'summer-olympics-sport-climbing',
        },
        {
            'title': strings(30029),
            'url': '/sports/olympics/summer/surfing',
            'slug': 'summer-olympics-surfing',
        },
        {
            'title': strings(30030),
            'url': '/sports/olympics/summer/aquatics/swimming',
            'slug': 'summer-olympics-swimming',
        },
        {
            'title': strings(30031),
            'url': '/sports/olympics/summer/table-tennis',
            'slug': 'summer-olympics-table-tennis',
        },
        {
            'title': strings(30032),
            'url': '/sports/olympics/summer/taekwondo',
            'slug': 'summer-olympics-taekwondo',
        },
        {
            'title': strings(30033),
            'url': '/sports/olympics/summer/tennis',
            'slug': 'summer-olympics-tennis',
        },
        {
            'title': strings(30034),
            'url': '/sports/olympics/summer/triathlon',
            'slug': 'summer-olympics-triathlon',
        },
        {
            'title': strings(30035),
            'url': '/sports/olympics/summer/volleyball',
            'slug': 'summer-olympics-volleyball',
        },
        {
            'title': strings(30036),
            'url': '/sports/olympics/summer/aquatics/water-polo',
            'slug': 'summer-olympics-water-polo',
        },
        {
            'title': strings(30037),
            'url': '/sports/olympics/summer/weightlifting',
            'slug': 'summer-olympics-weightlifting',
        },
        {
            'title': strings(30038),
            'url': '/sports/olympics/summer/wrestling',
            'slug': 'summer-olympics-wrestling',
        },
    ]

STATIC_ENTRIES = [
        {
            'title': strings(30200),
            'type': 'folder',
            'page': 'live_videos',
        },
        {
            'title': strings(30201),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-replays',
        },
        {
            'title': strings(30202),
            'type': 'folder',
            'page': 'sports',
        },
        {
            'title': strings(30203),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-highlights',
        },
        {
            'title': strings(30204),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-team-canada',
        },
        {
            'title': strings(30210),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'betrivers-the-game-betcha-didnt-know-olympics-feature',
        },
        {
            'title': strings(30205),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-features-toyota',
        },
        {
            'title': strings(30214),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-canadian-tire-women-in-sports',
        },
        {
            'title': strings(30207),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-features-bell',
        },
        {
            'title': strings(30209),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-sobeys-feed-the-dream',
        },
        {
            'title': strings(30212),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-air-canada-experience-paris',
        },
        {
            'title': strings(30213),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-ozempic-lumieres-sur-paris',
        },
        {
            'title': strings(30206),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'makeorbreak',
        },
        {
            'title': strings(30211),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-petro-medal-moments',
        },
        {
            'title': strings(30216),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-smartwater-paris-tonight',
        },
        {
            'title': strings(30215),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'olympics-coca-cola-real-magic',
        },
        {
            'title': strings(30218),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'road-to-the-olympic-games',
        },
        {
            'title': strings(30208),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-features-rbc',
        },
        {
            'title': strings(30217),
            'type': 'folder',
            'page': 'clips_by_slug',
            'slug': 'summer-olympics-features-kraft',
        },
    ]

# Lovingly borrowed from t1mlib
def get_url(**kwargs):
    try:
        if isPython2:
            return '{0}?{1}'.format(_url, urlencode(dict([unicode(k).encode(UTF8),unicode(v).encode(UTF8)] for k,v in kwargs.items())))
        else:
            return '{0}?{1}'.format(_url, urlencode(kwargs))
    except:
        xbmc.log('get_url kwargs = ' + str(kwargs))
        raise

# Lovingly borrowed from t1mlib
def getRequest(url, udata=None, headers = httpHeaders, dopost = False, rmethod = None):
    req = Request(url, udata, headers)

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

    return py3unicode(page)     # Return as a Python2 UTF-8 str or a Python3 unicode str

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

            url = get_url(
                action='play',
                title=entry['title'],
                videoId=entry.get('videoId', ''),
                medianetUrl=entry.get('medianetUrl', ''),
                isUpcoming=entry.get('isUpcoming', False)
            )

            is_folder = False

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

        elif entry['type'] == 'folder':
            art = entry.get('art')
            if art:
                list_item.setArt(art)

            list_item.setProperty('IsPlayable', 'false')

            url = get_url(
                action='listing',
                page=entry['page'],
                title=entry['title'],
                slug=entry.get('slug'),
                pageNo=entry.get('pageNo', 1)
            )

            is_folder = True

            # Add our item to the Kodi virtual folder listing.
            xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)

    # Add a sort method for the virtual folder items
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_NONE)

    # Finish creating a virtual folder.
    xbmcplugin.endOfDirectory(_handle)

def extractMedianetUrl(contentItem):
    media = contentItem.get('media')
    if media:
        # Extract the medianet URL
        assets = media.get('assets', [])
        for asset in (asset for asset in assets if asset['type'] == 'medianet'):
            return asset.get('key')

    return None

def entries_append_contentItem(entries, contentItem):
    duration = 0
    isLive = False

    medianetUrl = extractMedianetUrl(contentItem)

    try:
        airDate = datetime.datetime.fromtimestamp(int(contentItem.get('publishedAt', 0)) / 1000)
    except ValueError:
        airDate = 0

    media = contentItem.get('media')
    if media:
        isLive = (media.get('streamType') == 'Live')
        duration = int(media.get('duration', ''))

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

    contentItem['title'] = u'{0} ({1})'.format(contentItem['title'].rstrip(), titleState)
    contentItem['description'] = u'{0}\n\n({1})'.format(contentItem['description'], descState)

    thumbnail = contentItem.get('imageLarge')

    entries.append(
        {
            'type': 'video',
            'title': contentItem.get('title'),
            'description': contentItem.get('description'),
            'videoId': contentItem.get('id'),
            'medianetUrl': medianetUrl,
            'duration': duration,
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

    #xbmc.log('GraphQL query: ' + json.dumps(body))
    response = getRequest(url=GRAPHQL_URL, udata=json.dumps(body).encode(UTF8), dopost=True)
    #xbmc.log('GraphQL response: ' + response)
    return json.loads(response)

def graphql_contentItems_to_entries(contentItems):
    entries = []
    for contentItem in contentItems:
        entries_append_contentItem(entries, contentItem)

    return entries

def graphql_allContentItems_result_to_entries(graphql_result):
    data = graphql_result.get('data')
    if not data:
        return []

    allContentItems = data.get('allContentItems')
    if not allContentItems:
        return []

    nodes = allContentItems.get('nodes')
    if not nodes:
        return []

    return graphql_contentItems_to_entries(nodes)

def list_contentItems(page_title, graphql_variables, next_page_entry):
    graphql = """
query contentItemsByItemsQueryFilters(
  $itemsQueryFilters: ItemsQueryFilters
  $page: Int
  $pageSize: Int
  $minPubDate: String
  $maxPubDate: String
  $lineupOnly: Boolean
  $offset: Int
) {
  allContentItems(
    itemsQueryFilters: $itemsQueryFilters
    page: $page
    pageSize: $pageSize
    offset: $offset
    minPubDate: $minPubDate
    maxPubDate: $maxPubDate
    lineupOnly: $lineupOnly
    targets: [WEB, ALL]
  ) {
    nodes {
      id
      title
      description
      flag
      imageLarge
      publishedAt
      updatedAt
      type
      media {
        duration
        hasCaptions
        streamType
        assets {
          type
          key
        }
      }
    }
  }
}
"""

    graphql_result = run_graphql(graphql, graphql_variables)

    entries = graphql_allContentItems_result_to_entries(graphql_result)

    # If we have a full page of results, append a "next page" entry
    if len(entries) == PAGE_SIZE:
        entries.append(next_page_entry)

    return list_entries(page_title, entries)

def list_live_videos(page_title, pageNo):
    variables = {
        "itemsQueryFilters": {
            "categorySlugs": [
                "summer-olympics-live"
            ],
            "mediaStreamType": "Live",
            "sort": "+publishedAt",
            "types": [
                "video"
            ]
        },
        "lineupOnly": False,
        "maxPubDate": "now+35d",
        "page": pageNo,
        "pageSize": PAGE_SIZE
    }

    next_page_entry = {
        'title': page_title,
        'listing_title': strings(30306).format(page_title, pageNo + 1),
        'type': 'folder',
        'page': 'live_videos',
        'pageNo': pageNo + 1,
    }

    return list_contentItems(page_title, variables, next_page_entry)

def list_clips_by_slug(page_title, slug, pageNo):
    variables = {
        "itemsQueryFilters": {
            "categorySlugs": [
                slug
            ],
            "sort": "-updatedAt",
            "types": [
                "video"
            ]
        },
        "lineupOnly": False,
        "minPubDate": "now-365d",
        "maxPubDate": "now+4h",
        "page": pageNo,
        "pageSize": PAGE_SIZE
    }

    next_page_entry = {
        'title': page_title,
        'listing_title': strings(30306).format(page_title, pageNo + 1),
        'type': 'folder',
        'page': 'clips_by_slug',
        'slug': slug,
        'pageNo': pageNo + 1,
    }

    return list_contentItems(page_title, variables, next_page_entry)

def list_sports(page_title):
    entries = []
    for sport in SPORTS:
        entries.append(
            {
                'title': sport['title'],
                'type': 'folder',
                'page': 'clips_by_slug',
                'slug': sport['slug']
            })

    list_entries(page_title, entries)

def medianetUrlToM3u8Url(medianetUrl):
    xbmc.log('medianetUrl = ' + medianetUrl)
    try:
        # Fetch the JSON
        medianetJsonStr = getRequest(medianetUrl)

        # Parse the document as JSON
        medianetJson = json.loads(medianetJsonStr)

        # Return the url element as the video
        medianetUrl =  medianetJson.get('url')
        if not medianetUrl:
            raise NoUrlElementError('medianet document missing a URL element')

        return medianetUrl
    except Exception as err:
        xbmc.log('Error loading medianet JSON: ' + str(err))
        xbmc.log(medianetJsonStr)
        raise

def videoIdToMedianetUrl(videoId):
    graphql = """
query Content($videoId: Int) {
  contentItem(id: $videoId) {
    media {
      assets {
        type
        key
      }
    }
  }
}
"""

    variables = {
        "videoId": int(videoId)
    }

    graphql_result = run_graphql(graphql, variables)

    data = graphql_result.get('data')
    if data:
        return extractMedianetUrl(data.get('contentItem'))
    else:
        return None

def parseM3u8(m3u8):
    streams = {}

    xbmc.log('m3u8 = ' + str(m3u8))
    m3u8Lines = m3u8.split('\n')
    if (len(m3u8Lines) < 1) or (m3u8Lines[0] != '#EXTM3U'):
        raise M3u8DocumentError('Not an M3U document')

    # Start with empty properties in case none are found
    props = {}
    for m3u8Line in m3u8Lines:
        # We're interested in the stream information lines
        if m3u8Line.startswith('#EXT-X-STREAM-INF:'):
            # Parse out the info data
            m3u8StreamInfo = m3u8Line.split(':', 1)[1]

            # Parse properties at the comma. This breaks on quoted properties but it's fine
            # because we're not interested in those anyway.
            for m3u8StreamProp in m3u8StreamInfo.split(','):
                m3u8PropParts = m3u8StreamProp.split('=')
                if len(m3u8PropParts) == 2:
                    props[m3u8PropParts[0]] = m3u8PropParts[1]

        elif m3u8Line.startswith('#'):
            # Skip uninteresting comment lines
            continue

        else:
            # A non-comment line is a URL so store it along with the previously-parsed properties
            streams[m3u8Line] = props
            # Reset properties for next URL
            props = {}

    return streams

def pickStreamUrlFromM3u8Url(m3u8_url):
    try:
        # Fetch and parse the video playlist
        m3u8 = getRequest(m3u8_url)
        streams = parseM3u8(m3u8)

        # Get the bitrate limit setting, if there is one
        try:
            # Load the kbps bitrate setting and convert to bps
            bitrateLimit = int(xbmcplugin.getSetting(_handle, 'bitrateLimitKbps')) * 1000
        except ValueError:
            bitrateLimit = 10000000000       # 10 Gbit/sec is essentially unlimited, right?

        # Find the highest bitrate within the setting limit
        selected_bitrate = 0
        for url, props in streams.items():
            bitrate = int(props.get('BANDWIDTH', 0))
            if (bitrate <= bitrateLimit) and (bitrate > selected_bitrate):
                selected_stream_url = url
                selected_bitrate = bitrate

        xbmc.log('selected_bitrate = ' + str(selected_bitrate))
        xbmc.log('selected_stream_url = ' + selected_stream_url)

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

def play_video(videoId, medianetUrl, isUpcoming):
    if (not medianetUrl or (medianetUrl == '')) and (not videoId or (videoId == '')):
        raise ValueError(strings(30900))

    try:
        if (not medianetUrl or (medianetUrl == '')):
            xbmc.log('Fetching medianetUrl from videoId ' + videoId)
            medianetUrl = videoIdToMedianetUrl(videoId)

        xbmc.log('medianetUrl: ' + medianetUrl)

        # Fetch the video's medianet JSON document and extract the m3u8 URL from it.
        # In case this fails, re-try a few times.
        medianetAttemptsRemaining = 2
        while (medianetAttemptsRemaining > 0):
            try:
                m3u8_url = medianetUrlToM3u8Url(medianetUrl)

                # Success. No need to re-try.
                medianetAttemptsRemaining = 0
                xbmc.log('m3u8_url: ' + m3u8_url)
            except MedianetDocumentError as err:
                medianetAttemptsRemaining -= 1
                if (medianetAttemptsRemaining == 0):
                    # "The server did not return a valid stream. Please try again later."
                    okDialog(strings(30902))
                    return
                else:
                    xbmc.log('Re-trying medianet fetch')

        # For Paris 2024, some streams (not many) are published as separate video and audio streams
        # in the m3u8 which the player can understand and play correctly. However, this plugin was
        # doing its own bitrate selection by parsing the m3u8 and extracting the chosen stream, so
        # for these dual-stream manifests it was only passing the one stream, the video, to the
        # player, causing them to be silent. To resolve this, I could've either continued to parse
        # the m3u8, extracted both the video and audio URLs, built a new manifest with the two
        # streams, and passed that into the player, or I could just forego the custom bitrate
        # selection and instead pass the original m3u8 to Kodi, letting Kodi pick the most
        # appropriate stream. I decided on the latter because the games are already underway and I
        # felt that losing the custom bitrate selection was worth the benefit of passing all
        # responsibility for parsing the m3u8 to Kodi.
        # Added benefit: Kodi's in-player program selection and audio stream selection now work.

        # [No longer] Fetch the video's m3u8 and pick the stream based on the user's bitrate preference
        #stream_url = pickStreamUrlFromM3u8Url(m3u8_url)
        stream_url = m3u8_url
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
        page_title = params['title']

        if params['action'] == 'listing':
            if params['page'] == 'live_videos':
                list_live_videos(page_title, int(params.get('pageNo', 1)))
            if params['page'] == 'clips_by_slug':
                list_clips_by_slug(page_title, params['slug'], int(params.get('pageNo', 1)))
            if params['page'] == 'sports':
                list_sports(page_title)
            else:
                pass
        elif params['action'] == 'play':
            play_video(params.get('videoId',''), params.get('medianetUrl'), params.get('isUpcoming', 'False')=='True')
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
