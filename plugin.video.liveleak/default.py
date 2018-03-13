# -*- coding: utf-8 -*-

# Standard libraries - Python 2 & 3
import re, requests, json
from os import path
from bs4 import BeautifulSoup as bs

# Fallback if multiprocessing module is not available
slow_mode = False
try:
    from multiprocessing.dummy import Pool
except:
    slow_mode = True

try: # Python 3
    from html import unescape
    from urllib.parse import quote_plus, unquote_plus, urlencode
    from urllib.parse import parse_qsl, urlparse, urlunparse
except: # Python 2
    from HTMLParser import HTMLParser
    from urllib import quote_plus, unquote_plus, urlencode
    from urlparse import parse_qsl, urlparse, urlunparse

# Standardize Python 2/3
try: # Python 3
    unescape
except: # Python 2
    unescape = HTMLParser().unescape

#TODO: Implement unicode conversion functions for both Python 2 & 3

# Kodi libraries
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

# Identifiers
BASE_URL = sys.argv[0].encode('utf-8')
ADDON_HANDLE = int(sys.argv[1])
addon         = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo('name')
ADDON_PROFILE = addon.getAddonInfo('profile')

# Per profile preference
userProfilePath = xbmc.translatePath(ADDON_PROFILE)
leakPostersFile = u'leakposters.json'
leakPostersFileLocation = path.join(userProfilePath, leakPostersFile)

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

http_timeout = 10

# Where our targets live
domain_home = "https://www.liveleak.com/"


# -----------------
# --- Functions ---
# -----------------

# --- Helper functions ---

def log(txt, level='debug'):
    #Write text to Kodi log file.
    levels = {
        'debug': xbmc.LOGDEBUG,
        'error': xbmc.LOGERROR,
        'notice': xbmc.LOGNOTICE
        }
    logLevel = levels.get(level, xbmc.LOGDEBUG)

    message = '%s: %s' % (ADDON_NAME, txt)
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
    for vid in liveleak_vids:
        media.append(vid['src'])

    youtubes = []
    youtube_vids = block.select('iframe[src*="youtube.com/embed/"]')
    for vid in youtube_vids:
        # Extract youtube video id and append to list
        youtubes.append(re.search(r'youtube.com/embed/(.+?)\?rel=0.*$', vid['src']).group(1))
    youtubes = list(set(youtubes)) # remove duplicates

    media.extend(youtubes) #concatenate liveleak & youtube media references

    return media

def fetchItemDetails((url, meta)):
    page = requests.get(url)

    if page.status_code != requests.codes.ok: # Uh-oh!
        log("Error: %s: %s" % (page.status_code, url))
        return

    # Reduce page to video information block
    soup = bs(page.text, 'html.parser')
    vid_block = soup.find('div', class_='step_outer')
    for script in vid_block("script"):
        script.decompose()
    for style in vid_block("style"):
        style.decompose()

    # Get post description
    meta['description'] = vid_block.get_text().strip()

    media = findAllMediaItems(vid_block)
    if media:
        if len(media) > 1: # More than one media item on page
            mediaList = []
            for medium in media:
                mediaList.append((url, medium, meta))
            return mediaList
        else:
            return ((url, media[0], meta)) # single item

def buildListItem((url, medium, meta)):
    #Extract meta info
    title = meta['title']
    thumbnail = meta['thumbnail']
    credit = meta['credit']
    description = meta['description']
    mpaa = meta['mpaa']
    rating = meta['rating']

    leakPosters = loadLeakPosters() # Preferences for coloring titles

    if 'cdn.liveleak.com' in medium:
        # Capture source of this medium
        src = url.replace(domain_home, '')
        url = buildUrl({'mode': 'play', 'url': medium, 'src': src})
    else:
        url = 'plugin://plugin.video.youtube/play/?video_id=%s' % medium
        url = url.encode('utf-8')

    # Build list item
    user_mod = leakPosters.get(credit, 0)
    if user_mod == 1:
        title = "[COLOR limegreen]%s[/COLOR]" % title
    elif user_mod == 2:
        title = "[COLOR dimgray]%s[/COLOR]" % title
    liz = xbmcgui.ListItem(label=title, thumbnailImage=thumbnail)
    info = {"title":title,"credits":credit,"plot":description}
    info.update({'mpaa':mpaa,'tagline':rating})
    liz.setInfo("Video", info)
    liz.addStreamInfo('video', {'codec': 'h264'}) #Helps prevent multiple fetch
    liz.setArt( {'thumb': thumbnail} )
    liz.setProperty('IsPlayable', 'true')
    cmd = "XBMC.RunPlugin({})"
    cmd = cmd.format( buildUrl( {'mode': 'mod_user', 'user': credit.encode('utf-8')} ) )
    liz.addContextMenuItems([('Moderate user: %s' % credit, cmd)])

    return (url, liz)

def saveLeakPosters(leakPosters):
    # Kludge to force auto-creation of the required userdata folder
    addon.setSetting('user_prefs', 'enabled')
    try:
        with open(leakPostersFileLocation, 'w') as f:
            f.write(json.dumps(leakPosters))
        return True
    except Exception as e:
        log(e)
        return False

def loadLeakPosters():
    try:
        with open(leakPostersFileLocation, 'r') as f:
            return json.loads(f.read())
    except:
        saveLeakPosters({})
        return {}

def getSearchString():
    keyboard = xbmc.Keyboard(searchStr, 'Search')
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
    addDir('Featured', 'in_bookmark_folder_id', '1')
    addDir('News & Politics', 'tag_string', 'news, politics')
    addDir('Yoursay', 'tag_string', 'yoursay,your say')
    addDir('Must See', 'in_bookmark_folder_id', '2')
    addDir('Ukraine', 'tag_string', 'ukraine')
    addDir('Middle East', 'tag_string', 'syria,afghanistan,iraq')
    addDir('Entertainment', 'by_user_token', '9ee5fbcb8e0b7990d586')
    addDir('WTF', 'tag_string', 'wtf')
    addDir('Russia', 'tag_string', 'russia')
    addDir('Search', 'q', '')

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
    page = requests.get(url, headers=http_headers, timeout=http_timeout).text
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
        pool = Pool(8)
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
        play_item = xbmcgui.ListItem(path=item.encode('utf-8'))
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
            url = match.group(1).encode('utf-8')
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
        try: params[key] = unquote_plus(params[key]).decode('utf-8')
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

elif mode == 'mod_user':
    leakPosters = loadLeakPosters()

    user = params.get('user', '???').decode('utf-8')

    select_title = "For items posted by %s:" % user
    select_list = ['reset to normal', 'highlight', 'subdue']
    choice = xbmcgui.Dialog().select(select_title, select_list)

    if choice >= 0:
        if leakPosters.get(user, 0) == choice:
            message = "Setting not changed."
        else:
            if choice == 0:
                message = "... will be displayed normally on next page load."
            elif choice == 1:
                message = "... will be highlighted on next page load."
            elif choice == 2:
                message = "... will be subdued on next page load."

            leakPosters[user] = choice
            if not saveLeakPosters(leakPosters):
                message = "Error saving setting."

        xbmcgui.Dialog().ok("Postings by %s ..." % user, message)
