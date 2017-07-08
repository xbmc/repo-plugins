# Standard libraries
import urllib, urllib2, urlparse, re
from HTMLParser import HTMLParser

# Kodi libraries
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

# Identifiers
BASE_URL = sys.argv[0]
ADDON_HANDLE = int(sys.argv[1])
addon         = xbmcaddon.Addon()
ADDON_NAME = addon.getAddonInfo('name')

# Convenience
h = HTMLParser()
qp = urllib.quote_plus
uqp = urllib.unquote_plus

domain_home = "https://www.liveleak.com/"

# -----------------
# --- Functions ---
# -----------------

# --- Helper functions ---

def log(txt, level='debug'):
    """
    Write text to Kodi log file.
    :param txt: text to write
    :type txt: str
    """
    levels = {
        'notice': xbmc.LOGNOTICE,
        'error': xbmc.LOGERROR
        }
    logLevel = levels.get(level, xbmc.LOGDEBUG)
    
    message = '%s: %s' % (ADDON_NAME, txt.encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=logLevel)

def notify(message):
    """
    Execute built-in GUI Notification
    :param message: message to display
    :type message: str
    """
    command = 'XBMC.Notification("%s", "%s", %s)' % (ADDON_NAME, message , 5000)
    xbmc.executebuiltin(command)

def httpRequest(url, method = 'get'):
    """
    Request a web page or head info from url.
    :param url: Fully-qualified URL of resource
    :type url: str
    :param method: currently, 'head' or 'get' (default)
    :type method: str
    """
    #log("httpRequest URL: %s" % str(url), 'notice' )

    user_agent = ['Mozilla/5.0 (Windows NT 6.1; Win64; x64)',
                  'AppleWebKit/537.36 (KHTML, like Gecko)',
                  'Chrome/55.0.2883.87',
                  'Safari/537.36']
    user_agent = ' '.join(user_agent)
    headers = {'User-Agent':user_agent, 
               'Accept':"text/html", 
               'Accept-Encoding':'gzip,deflate,sdch', 
               'Accept-Language':'en-US,en;q=0.8'
                } 

    req = urllib2.Request(url.encode('utf-8'), None, headers)
    if method is 'head': req.get_method = lambda : 'HEAD'
    try:
        response = urllib2.urlopen(req)
        if method is 'head':
            text = response.info()
        else:
            text = response.read()
        response.close()
    except:
        text = None

    return(text)

def addSearch():
    searchStr = ''
    keyboard = xbmc.Keyboard(searchStr, 'Search')
    keyboard.doModal()
    if (keyboard.isConfirmed()==False):
        return
    searchStr=keyboard.getText()
    if len(searchStr) == 0:
        return
    else:
        return searchStr

def addDir(name, queryString):
    if 'browse?' not in queryString:
        queryString = 'browse?' + queryString
    u="%s?mode=indx&url=%s" % (BASE_URL, qp(queryString))
    liz=xbmcgui.ListItem(name)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=u,listitem=liz,isFolder=True)

def findAllMediaItems(url):
    page = httpRequest(url)
    if page is None:
        notify("The server is not cooperating")
        return False
        
    # Consolidate liveleak and Youtube video sources
    liveleakRegexp = r'<source src="(.+?)".*$'
    youtubeRegexp = r'src="//www.youtube.com/embed/(.+?)\?rel=0.*$'
    Regexp = r'%s|%s' % (liveleakRegexp, youtubeRegexp)

    return re.findall(Regexp, page, re.MULTILINE)


# --- GUI director (Main Event) functions ---

def categories():
    addDir('Popular', 'popular')
    addDir('Featured', 'featured=1')
    addDir('News & Politics', 'channel_token=04c_1302956196')
    addDir('Yoursay', 'channel_token=1b3_1302956579')
    addDir('Must See', 'channel_token=9ee_1303244161')
    addDir('Syria', 'channel_token=cf3_1304149308')
    addDir('Iraq', 'channel_token=e8a_1302956438')
    addDir('Afghanistan', 'channel_token=79f_1302956483')
    addDir('Entertainment', 'channel_token=51a_1302956523')
    addDir('Search', 'q=')
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def index(url):
    if url=="browse?q=":
        searchString = addSearch()
        url="browse?q="+searchString

    # Flesh out paging
    try:
        appdg = url.split('&')[1] # 'page=X'
        before = url.split('&')[0] # original category path
        nextPageNumber = str(int(appdg.split('=')[1]) + 1) # increment page number
        pagedURL = before + "&page=" + nextPageNumber # reassemble paged url
    except:
        nextPageNumber = '2'
        pagedURL = url + "&page=" + nextPageNumber

    url = domain_home + url
    page = httpRequest(url)
    match=re.findall('<a href="(.+?)"><img class="thumbnail_image" src="(.+?)" alt="(.+?)"', page)
    iList = []
    for url,thumbnail,name in match:
        # For 'name': handle unicode, strip dangling whitespace,
        # decode (possibly double-stacked) html entities, and revert to utf-8
        name = unicode(name, 'utf-8', errors='ignore')
        name = h.unescape(h.unescape(name.strip()))
        name = name.encode('utf-8')
        
        match = findAllMediaItems(url) # findall match object
        if match:
            for idx, item in enumerate(match):
                videoNum = ""
                if len(match) > 1:
                    videoNum = " (%s)" % str(idx + 1)
                item = reduce( (lambda x, y: x + y), item) # Discard unmatched RE
                if 'cdn.liveleak.com' in item:
                    # Capture source of this item
                    src = url.replace(domain_home, '').encode('utf-8')
                    item = '%s?mode=play&url=%s&src=%s' % (BASE_URL, qp(item), qp(src))
                else:
                    item = 'plugin://plugin.video.youtube/play/?video_id=%s' % item
                
                # Build list item
                liz=xbmcgui.ListItem(name + videoNum)
                liz.setInfo(type="Video", infoLabels={"Title": name + videoNum})
                liz.addStreamInfo('video', {'codec': 'h264'})
                liz.setArt( {'thumb': thumbnail, 'icon': thumbnail} )
                liz.setProperty('IsPlayable', 'true')
                iList.append((item, liz, False))

    xbmcplugin.addDirectoryItems(ADDON_HANDLE, iList, len(iList))
    addDir("Go To Page " + nextPageNumber, pagedURL)
    liz=xbmcgui.ListItem("Back To Categories")
    xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE,url=BASE_URL,listitem=liz,isFolder=True)

    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def viewPlay(url):
    url = uqp(url) # Decode html quoted/encoded url
    
    # Acceptable URL patterns
    url_patterns = [r'liveleak.com/view?', r'liveleak.com/ll_embed?']

    # Verify it's actually a "view" page
    if not any(x in url for x in url_patterns):
        notify("Invalid URL format")
        return

    match = findAllMediaItems(url) # findall match object
    if match:
        # Play first matching media item
        item = match[0]
        item = reduce( (lambda x, y: x + y), item) # Discard unmatched RE
        if not 'cdn.liveleak.com' in item:
            item = 'plugin://plugin.video.youtube/play/?video_id=%s' % item
        play_item = xbmcgui.ListItem(path=item)
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
    info = httpRequest(url, 'head')
    
    if info is None or 'Content-Type' not in info:
        notify("The server is not cooperating")
        return False
        
    if 'text/html' in info['Content-Type']:
        # Re-fetch time-based link
        regexp = r'src="(%s\?.+?)"' % url.split('?')[0]
        page = httpRequest(domain_home + src)
        match = re.search(regexp, page)
        if match:
            url = match.group(1)
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
    params = urlparse.parse_qs(sys.argv[2][1:])
    for key in params:
        params[key] = params[key][0] # Reduce one-item list to string
        try: params[key] = uqp(params[key]).decode('utf-8')
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

