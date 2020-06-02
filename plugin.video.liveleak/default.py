# -*- coding: utf-8 -*-

from __future__ import unicode_literals

# Standard libraries - Python 2 & 3
import sys, io, re, requests, json
from os import path
from bs4 import BeautifulSoup as bs

if sys.platform.startswith('win'): # For file function argument discrimination
    WIN = True
else:
    WIN = False

# Do LBYL version identity instead of idiomatic EAFP
if sys.version_info.major > 2: # Python 3
    PY2 = False
    from html import unescape
    from urllib.parse import quote_plus, unquote_plus, urlencode
    from urllib.parse import parse_qsl, urlparse, urlunparse
else: # Python 2
    PY2 = True
    from HTMLParser import HTMLParser
    from urllib import quote_plus, unquote_plus, urlencode
    from urlparse import parse_qsl, urlparse, urlunparse
    unescape = HTMLParser().unescape # Standardize unescape function name

# Universal unicode conversion functions for Python 2/3. Defined here for early use.
def py23_encode(s, encoding='utf-8'):
   if PY2 and isinstance(s, unicode):
       s = s.encode(encoding)
   return s


def py23_decode(s, encoding='utf-8'):
   if PY2 and isinstance(s, str):
       s = s.decode(encoding)
   return s


# Fallback if multiprocessing module is not available
slow_mode = False
try:
    from multiprocessing.dummy import Pool, cpu_count
except:
    slow_mode = True

# Kodi libraries
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, xbmcvfs

# Identifiers
BASE_URL = py23_decode(sys.argv[0])
ADDON_HANDLE = int(sys.argv[1])
addon         = xbmcaddon.Addon()
ADDON_NAME = py23_decode(addon.getAddonInfo('name'))
ADDON_PROFILE = addon.getAddonInfo('profile') # Unicode decoding not needed for this
_localString = addon.getLocalizedString
#addon.setSetting('user_prefs', 'enabled')

# Per profile preference
userProfilePath = py23_decode(xbmc.translatePath(ADDON_PROFILE))
leakPostersFile = 'leakposters.json'
leakPostersFileLocation = path.join(userProfilePath, leakPostersFile)
# Try to ensure userdata folder is available
if not xbmcvfs.exists(userProfilePath):
    try:
        _ = xbmcvfs.mkdirs(userProfilePath)
    except:
        try:
            os.makedirs(userProfilePath)
        except:
            pass

# HTTP constants
user_agent = ['Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
                'AppleWebKit/537.36 (KHTML, like Gecko)',
                'Chrome/55.0.2883.87',
                'Safari/537.36']
user_agent = ' '.join(user_agent)
http_headers = {'User-Agent':user_agent,
            'Accept':"text/html",
            'Accept-Encoding':'identity',
            'Accept-Language':'en-US,en;q=0.8',
            'Accept-Charset':'utf-8'
            }

http_timeout = 15

monitor = xbmc.Monitor() # For abort-aware sleep

# Where our targets live
domain_home = "https://www.liveleak.com/"


# -----------------
# --- Functions ---
# -----------------

# --- Helper functions ---

def log(txt, level='debug'): # Default must be 'debug' for production use
    #Write text to Kodi log file.
    levels = {
        'debug': xbmc.LOGDEBUG,
        'error': xbmc.LOGERROR,
        'notice': xbmc.LOGNOTICE
        }
    logLevel = levels.get(level, xbmc.LOGDEBUG)

    message = py23_encode('%s: %s' % (ADDON_NAME, txt))
    xbmc.log(msg=message, level=logLevel)

def notify(message):
    #Execute built-in GUI Notification
    command = 'XBMC.Notification("%s","%s",%s)' % (ADDON_NAME, message, 5000)
    xbmc.executebuiltin(command)

def buildUrl(query):
    return BASE_URL + '?' + urlencode(query)

def findAllMediaItems(block):
    media = []
    # Consolidate liveleak and Youtube video sources
    liveleak_vids = block.select('video > source')
    # Select 'default' video if more than one
    if len(liveleak_vids) > 1:
      for vid in liveleak_vids:
        # Select 'default' video and exclude duplicates retaining original order
        if vid.has_attr('default') and vid['src'] not in media:
          media.append(vid['src'])
    elif len(liveleak_vids) == 1:
      media.append(liveleak_vids[0]['src'])

    youtubes = []
    youtube_vids = block.select('iframe[src*="youtube.com/embed/"]')
    for vid in youtube_vids:
        # Extract youtube video id
        vid_id = re.search(r'youtube.com/embed/(.+?)\?.*$', vid['src']).group(1)
        if vid_id not in youtubes: # exclude duplicates retaining original order
          youtubes.append(vid_id)

    media.extend(youtubes) #concatenate liveleak & youtube media references

    return media

def fetchItemDetails(url_meta):
    (url, meta) = url_meta
    page = requests.get(url)

    if page.status_code == 503: #Service temporarily unavailable, try one more time
        monitor.waitForAbort(2)
        if not monitor.abortRequested():
            page = requests.get(url)

    if page.status_code != requests.codes.ok: # Uh-oh!
        log("Error: %s: %s" % (page.status_code, url))
        return

    # Reduce page to video information block
    soup = bs(page.text, 'html.parser')
    vid_block = soup.find('div', class_='step_outer')

    # Prevent errors caused by 'ghost' threads
    if not vid_block:
        return None

    for script in vid_block("script"):
        script.decompose()
    for style in vid_block("style"):
        style.decompose()

    # Get post description
    description = vid_block.get_text().strip()
    # Strip extraneous lines
    description = re.sub(r'(?m)^\.\r?\n?$', '\n', description) # single period on line
    description = re.sub(r'(?m) +\r?\n?$', '\n', description) # line with only blanks
    meta['description'] = re.sub(r'\n{3,}', '\n\n', description) # multiple blank lines


    media = findAllMediaItems(vid_block)
    if media:
        if len(media) > 1: # More than one media item on page
            mediaList = []
            for medium in media:
                mediaList.append((url, medium, meta))
            return mediaList
        else:
            return ((url, media[0], meta)) # single item

def buildListItem(url_medium_meta):
    (url, medium, meta) = url_medium_meta
    #Extract meta info
    title = meta['title']
    thumbnail = meta['thumbnail']
    credit = meta['credit']
    description = meta['description']
    mpaa = meta['mpaa']
    rating = "Rating: " + meta['rating']

    leakPosters = loadLeakPosters() # Preferences for coloring titles

    if 'cdn.liveleak.com' in medium:
        # Capture source of this medium
        src = url.replace(domain_home, '')
        url = buildUrl({'mode': 'play', 'url': medium, 'src': src})
    else:
        url = 'plugin://plugin.video.youtube/play/?video_id=%s' % medium
    url = py23_encode(url)

    # Build list item
    user_label = leakPosters.get(credit, 0)
    if user_label == 1:
        title = "[COLOR limegreen]%s[/COLOR]" % title
    elif user_label == 2:
        title = "[COLOR dimgray]%s[/COLOR]" % title
    elif user_label == 3:
        title = "[COLOR dodgerblue]%s[/COLOR]" % title
    liz = xbmcgui.ListItem(label=title)
    info = {"title":title,"credits":credit,"plot":description}
    info.update({'mpaa':mpaa,'tagline':rating})
    liz.setInfo("Video", info)
    liz.addStreamInfo('video', {'codec': 'h264'}) #Helps prevent multiple fetch
    liz.setArt( {'thumb': thumbnail} )
    liz.setProperty('IsPlayable', 'true')
    cmd = "XBMC.RunPlugin({})"
    cmd = cmd.format( buildUrl( {'mode': 'label_user', 'user': credit} ) )
    liz.addContextMenuItems([('Label user: %s' % credit, cmd)])

    return (url, liz)

def saveLeakPosters(leakPosters):
    if WIN: # Use unicode
        myEncoding = None
    else:
        myEncoding = 'utf-8'
    try:
        with io.open(leakPostersFileLocation, 'w', encoding=myEncoding) as f:
            j_string = json.dumps(leakPosters, ensure_ascii=False)
            if isinstance(j_string, str):
                j_string = py23_decode(j_string)
            f.write(j_string)
        return True
    except Exception as e:
        log(e)
        return False

def loadLeakPosters():
    if WIN: # Use unicode
        myEncoding = None
    else:
        myEncoding = 'utf-8'
    try:
        with io.open(leakPostersFileLocation, 'r', encoding=myEncoding) as f:
            return json.loads(f.read())
    except:
        saveLeakPosters({})
        return {}

def getSearchString():
    keyboard = xbmc.Keyboard('', 'Search')
    keyboard.doModal()
    if (keyboard.isConfirmed()==False):
        return ''
    return keyboard.getText()

def addDir(title, qKey, qVal, pVal='1'):
    url = 'browse?a=list&' + qKey + '=' + qVal + '&page=' + pVal
    url = buildUrl({'mode': 'indx', 'url': url})
    liz = xbmcgui.ListItem(title)
    liz.setInfo(type="Video", infoLabels={"Title": title})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=url,listitem=liz,isFolder=True)


# --- GUI director (Main Event) functions ---

def categories():
    #TODO Update for newly rearranged categories
    addDir(_localString(30000), 'in_bookmark_folder_id', '1')
    addDir(_localString(30001), 'tag_string', 'news, politics, trump')
    addDir(_localString(30002), 'tag_string', 'yoursay,your say')
    addDir(_localString(30003), 'in_bookmark_folder_id', '2')
    addDir(_localString(30004), 'tag_string', 'ukraine')
    addDir(_localString(30005), 'tag_string', 'syria,afghanistan,iraq')
    addDir(_localString(30006), 'by_user_token', '9ee5fbcb8e0b7990d586')
    addDir(_localString(30007), 'tag_string', 'wtf')
    addDir(_localString(30008), 'tag_string', 'russia')
    addDir(_localString(30009), 'q', '')

    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def index(url):
    url_parts = urlparse(url) # Disassemble url
    # Get query parts
    queries = dict(parse_qsl(url_parts.query, keep_blank_values=True))

    # Get and add search string to query if needed
    if 'q' in queries and not queries['q']:
        queries['q'] = getSearchString()

    # Reassemble url
    realUrl = urlunparse(('', '', url_parts.path, '', urlencode(queries), ''))

    # Flesh out paging for next page
    nextPageNumber = str(int(queries['page']) + 1)
    queries['page'] = nextPageNumber
    pagedUrl = urlunparse(('', '', url_parts.path, '', urlencode(queries), ''))
    pagedUrl = buildUrl({'mode': 'indx', 'url': pagedUrl})

    url = domain_home + realUrl # full working url

    page = requests.get(url, headers=http_headers, timeout=http_timeout)
    if page.status_code == 503: #Service temporarily unavailable, try one more time
        monitor.waitForAbort(1)
        if not monitor.abortRequested():
            page = requests.get(url, headers=http_headers, timeout=http_timeout)

    page = page.text
    if page is None:
        notify("The server is not cooperating at the moment")
        return

    # Get list of individual posts from indexing page
    listing = bs(page, 'html.parser')
    posts = []
    for item in listing.find_all('div', class_='featured_items_outer'):
        meta = {}
        url = item.a['href'] # item page url
        meta['thumbnail'] = item.a.div.img['src'] # thumbnail image
        title = item.a.div.img['alt']
        # Handle possibly multiple-coded html entities in title
        meta['title'] = unescape(unescape(title.strip()))
        # Parental Guide rating
        meta['mpaa'] = item.a.div.div.get_text()
        # user rating
        meta['rating'] = item.find('samp', class_='thing_score').get_text()
        # ID of user that posted item
        meta['credit'] = item.find('div', class_='featured_text_con').a.get_text()
        posts.append((url, meta))

    # Fallback to slow mode?
    if slow_mode:
        # Fetch post details via loop
        items = []
        for post in posts:
            items.append(fetchItemDetails(post))
    else:
        # Fetch post details via multiple threads
        pool = Pool(cpu_count() * 2)
        items = pool.map(fetchItemDetails, posts)
        pool.close()
        pool.join()

    if items:
        iList = []
        for item in items: #(url, medium, meta)
            if isinstance(item, list): # Multiple media on the page
                for idx, atom in enumerate(item):
                    # Rebuild tuple with video number appended to title
                    (url, medium, meta) = atom
                    tmp_meta = meta.copy()
                    tmp_meta['title'] = "%s (%d)" % (tmp_meta['title'], (idx + 1)) # Add vidNum
                    atom = (url, medium, tmp_meta)
                    (url, liz) = buildListItem(atom)
                    iList.append((url, liz, False))
            else: # Single media item on the page
                if item:
                    (url, liz) = buildListItem(item)
                    iList.append((url, liz, False))

        xbmcplugin.addDirectoryItems(ADDON_HANDLE, iList, len(iList))
        liz=xbmcgui.ListItem("Go To Page " + nextPageNumber)
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=pagedUrl,listitem=liz,isFolder=True)
        liz=xbmcgui.ListItem("Back To Categories")
        xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=BASE_URL,listitem=liz,isFolder=True)

        xbmcplugin.endOfDirectory(ADDON_HANDLE)

def viewPlay(url):
    url = unquote_plus(url) # Decode html quoted/encoded url

    # Acceptable URL patterns
    url_patterns = [r'liveleak.com/view?', r'liveleak.com/ll_embed?']

    # Verify it's actually a "view" page
    if not any(x in url for x in url_patterns):
        notify("Invalid URL format")
        return

    match = fetchItemDetails((url, '')) # (url, media, meta)
    if isinstance(match, list): # Multiple media on the page
        match = match[0] #Take first one
    if match:
        # Play first matching media item
        item = match[1]
        if not 'cdn.liveleak.com' in item:
            item = 'plugin://plugin.video.youtube/play/?video_id=%s' % item
        play_item = xbmcgui.ListItem(path=py23_encode(item))
        # Pass the item to the Kodi player.
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=play_item)
    else:
        notify("Sorry, no playable media found.")
        return

def playVideo(url, src):
    """
    Play a video by the provided time-based url,
    or fetch new, time-based url from src.
    :param url: Fully-qualified video URL
    :type url: str
    :param src: path of page at domain_home containing video URL
    :type src: str
    """
    # Check if time-based video URL has not expired
    response = requests.head(url, headers=http_headers, timeout=http_timeout)
    content_type = response.headers.get('content-type')

    if content_type is None:
        notify("The server is not cooperating at the moment")
        return False

    if 'text/html' in content_type: # Link has expired else would be video type
        # Re-fetch time-based link
        regexp = r'src="(%s\?.+?)"' % url.split('?')[0]
        page = requests.get(domain_home + src, headers=http_headers, timeout=http_timeout).text
        match = re.search(regexp, page)
        if match:
            url = py23_encode(match.group(1))
        else:
            notify("Video has disappeared")
            return False

    # Create a playable item with a url to play.
    play_item = xbmcgui.ListItem(path=url)
    # Pass the item to the Kodi player.
    xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, listitem=play_item)


# ------------------
# --- Main Event ---
# ------------------

# Parse query string into dictionary
try:
    params = dict(parse_qsl(sys.argv[2][1:]))
    for key in params:
        try: params[key] = py23_decode(unquote_plus(params[key]))
        except: pass
except:
    params = {}

# What do to?
mode = params.get('mode', None)

if mode is None: categories()

elif mode == 'indx':
    url = params.get('url', None) # URL of index folder
    if url: index(url)

elif mode == 'view':
    url = params.get('url', None) # URL of index folder
    if url: viewPlay(url)

elif mode == 'play':
    url = params.get('url', None) # URL of video source
    src = params.get('src', None) # path of page containing video URL
    if url and src: playVideo(url, src)

elif mode == 'label_user':
    leakPosters = loadLeakPosters()

    user = py23_decode(params.get('user', '???'))

    select_title = "Label items posted by %s:" % user
    select_list = ['Remove label', 'Like', 'Dislike', 'Known, Neutral-ish']
    # Remove the user's current label from choice list
    choice = xbmcgui.Dialog().select(select_title, select_list, preselect=leakPosters.get(user, 0))

    if choice >= 0:
        if choice == 0:
            message = "normally"
        elif choice == 1:
            message = "in green"
        elif choice == 2:
            message = "in grey"
        elif choice == 3:
            message = "in blue"

        caption = "Success"
        message = "Postings by %s will be displayed %s on subsequent page loads." % (user, message)

        leakPosters[user] = choice
        if not saveLeakPosters(leakPosters):
            caption = "ERROR"
            message = "Setting could not be saved."

        xbmcgui.Dialog().ok(caption, message)
