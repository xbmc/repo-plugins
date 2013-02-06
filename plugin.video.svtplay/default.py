# -*- coding: utf-8 -*-
import re
import json
import time
import urllib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import CommonFunctions
import os
import resources.lib.bestofsvt as bestof
import resources.lib.helper as helper
import resources.lib.svt as svt

MODE_CHANNELS = "kanaler"
MODE_A_TO_O = "a-o"
MODE_PROGRAM = "pr"
MODE_LIVE = "live"
MODE_LATEST = "ep"
MODE_LATEST_NEWS = "en"
MODE_VIDEO = "video"
MODE_CATEGORIES = "categories"
MODE_CATEGORY = "ti"
MODE_LETTER = "letter"
MODE_RECOMMENDED = "rp"
MODE_SEARCH = "search"
MODE_BESTOF_CATEGORIES = "bestofcategories"
MODE_BESTOF_CATEGORY = "bestofcategory"
MODE_VIEW_TITLES = "view_titles"
MODE_VIEW_EPISODES = "view_episodes"
MODE_VIEW_CLIPS = "view_clips"

BASE_URL = "http://www.svtplay.se"
SWF_URL = "http://www.svtplay.se/public/swf/video/svtplayer-2013.02.swf" 
JSON_SUFFIX = "?output=json"

URL_A_TO_O = "/program"
URL_CATEGORIES = "/kategorier"
URL_CHANNELS = "/kanaler"
URL_TO_LATEST = "?tab=episodes&sida=1"
URL_TO_LATEST_NEWS = "?tab=news&sida=1"
URL_TO_RECOMMENDED = "?tab=recommended&sida=1"
URL_TO_SEARCH = "/sok?q="

VIDEO_PATH_RE = "/(klipp|video|live)/\d+"
VIDEO_PATH_SUFFIX = "?type=embed"

TAB_TITLES      = "titles"
TAB_EPISODES    = "episodes"
TAB_CLIPS       = "clips"
TAB_NEWS        = "news"
TAB_RECOMMENDED = "recommended"

MAX_NUM_GRID_ITEMS = 12
CURR_DIR_ITEMS = 0

pluginHandle = int(sys.argv[1])

settings = xbmcaddon.Addon()
localize = settings.getLocalizedString

common = CommonFunctions
common.plugin = "SVT Play 3"

# Get and set settings
common.dbg = False
if settings.getSetting('debug') == "true":
  common.dbg = True

HLS_STRIP = False
if settings.getSetting("hlsstrip") == "true":
    HLS_STRIP = True

FULL_PROGRAM_PARSE = False
if settings.getSetting("fullparse") == "true":
  FULL_PROGRAM_PARSE = True

HIDE_SIGN_LANGUAGE = False
if settings.getSetting("hidesignlanguage") == "true":
  HIDE_SIGN_LANGUAGE = True

SHOW_SUBTITLES = False
if settings.getSetting("showsubtitles") == "true":
  SHOW_SUBTITLES = True

USE_ALPHA_CATEGORIES = False
if settings.getSetting("alpha") == "true":
  USE_ALPHA_CATEGORIES = True

MAX_DIR_ITEMS = int(float(settings.getSetting("diritems")))


def viewStart():

  addDirectoryItem(localize(30008), { "mode": MODE_CHANNELS })
  addDirectoryItem(localize(30000), { "mode": MODE_A_TO_O })
  addDirectoryItem(localize(30001), { "mode": MODE_CATEGORIES })
  addDirectoryItem(localize(30005), { "mode": MODE_RECOMMENDED, "page": 1 })
  addDirectoryItem(localize(30002), { "mode": MODE_LIVE })
  addDirectoryItem(localize(30003), { "mode": MODE_LATEST, "page": 1 })
  addDirectoryItem(localize(30004), { "mode": MODE_LATEST_NEWS, "page": 1 })
  addDirectoryItem(localize(30006), { "mode": MODE_SEARCH })
  addDirectoryItem(localize(30007), { "mode": MODE_BESTOF_CATEGORIES })


def viewChannels():
  channels = svt.getChannels(BASE_URL + URL_CHANNELS)
  
  params = {}
  params["mode"] = MODE_VIDEO

  for channel in channels:
    params["url"] = channel["url"]
    addDirectoryItem(channel["title"],params,channel["thumbnail"],False,True)
    
  

def viewAtoO():
  html = helper.getPage(BASE_URL + URL_A_TO_O)

  texts = common.parseDOM(html, "a" , attrs = { "class": "playAlphabeticLetterLink" })
  hrefs = common.parseDOM(html, "a" , attrs = { "class": "playAlphabeticLetterLink" }, ret = "href")

  for index, text in enumerate(texts):
    addDirectoryItem(common.replaceHTMLCodes(text), { "mode": MODE_PROGRAM, "url": hrefs[index], "page": 1 })

def viewLive():
  html = helper.getPage(BASE_URL)

  tabId = common.parseDOM(html, "a", attrs = { "class": "[^\"']*playButton-TabLive[^\"']*" }, ret = "data-tab")

  if len(tabId) > 0:

    tabId = tabId[0]

    container = common.parseDOM(html, "div", attrs = { "class": "[^\"']*svtTab-" + tabId + "[^\"']*" })

    lis = common.parseDOM(container, "li", attrs = { "class": "[^\"']*svtMediaBlock[^\"']*" })

    for li in lis:

      liveIcon = common.parseDOM(li, "img", attrs = { "class": "[^\"']*playBroadcastLiveIcon[^\"']*"})

      if len(liveIcon) > 0:

        text = common.parseDOM(li, "h5")[0]
        href = common.parseDOM(li, "a", ret = "href")[0]

        match = re.match(VIDEO_PATH_RE, href)

        if match:

          url = match.group()

          addDirectoryItem(common.replaceHTMLCodes(text), { "mode": MODE_VIDEO, "url": url }, None, False, True)

def viewCategories():
  html = helper.getPage(BASE_URL + URL_CATEGORIES)

  container = common.parseDOM(html, "ul", attrs = { "class": "[^\"']*svtGridBlock[^\"']*" })

  lis = common.parseDOM(container, "li" , attrs = { "class": "[^\"']*svtMediaBlock[^\"']*" })

  for li in lis:

    href = common.parseDOM(li, "a", ret = "href")[0]
    text = common.parseDOM(li, "h2")[0]

    addDirectoryItem(common.replaceHTMLCodes(text), { "mode": MODE_CATEGORY, "url": href, "page": 1})

def viewAlphaDirectories():
  """
  Used to create the alphabetical A-Ö directory items.
  Addon setting has to be enabled for this to trigger.
  """
  html = helper.getPage(BASE_URL + URL_A_TO_O)

  container = common.parseDOM(html, "div", attrs = { "id" : "playAlphabeticLetterList" })

  letters = common.parseDOM(container, "h3", attrs = { "class" : "playAlphabeticLetterHeading " })

  for letter in letters:
    url = letter
    addDirectoryItem(helper.convertChar(letter), { "mode": MODE_LETTER, "letter": url })

def viewProgramsByLetter(letter):

  letter = urllib.unquote(letter)

  html = helper.getPage(BASE_URL + URL_A_TO_O)

  container = common.parseDOM(html, "div", attrs = { "id": "playAlphabeticLetterList" })

  letterboxes = common.parseDOM(container, "div", attrs = { "class": "playAlphabeticLetter" })

  for letterbox in letterboxes:

    heading = common.parseDOM(letterbox, "h3")[0]

    if heading == letter:
      break

  lis = common.parseDOM(letterbox, "li", attrs = { "class": "[^\"']*playListItem[^\"']*" })

  for li in lis:

    href = common.parseDOM(li, "a", ret = "href")[0]
    text = common.parseDOM(li, "a")[0]

    addDirectoryItem(common.replaceHTMLCodes(text), { "mode": MODE_PROGRAM, "url": href, "page": 1 })


def viewLatest(mode,page,index):

  dirtype = MODE_VIDEO

  if mode == MODE_LATEST_NEWS:
    url = URL_TO_LATEST_NEWS
  elif mode == MODE_RECOMMENDED:
    url = URL_TO_RECOMMENDED
  elif mode == MODE_LATEST:
    url = URL_TO_LATEST

  createDirectory(url,page,index,mode,dirtype)


def viewCategory(url,page,index):
  createDirectory(url,page,index,MODE_CATEGORY,MODE_PROGRAM)

def viewProgram(url,page,index):
  if FULL_PROGRAM_PARSE:
    createTabIndex(url)
  else:
    createDirectory(url,page,index,MODE_PROGRAM,MODE_VIDEO)

def viewSearch():

  keyword = common.getUserInput(localize(30102))
  if not keyword:
    viewStart()
    return
  keyword = urllib.quote(keyword)
  common.log("Search string: " + keyword)

  if keyword == "" or not keyword:
    viewStart()
    return 

  keyword = re.sub(r" ","+",keyword) 

  url = URL_TO_SEARCH + keyword
  
  createTabIndex(url)

def createTabIndex(url):
  """
  Creates a directory item for each available tab; Klipp, Hela program, Programtitlar
  """
  html = helper.getPage(BASE_URL + url)
  foundTab = False
 
  # Search for the "titles" tab. If it exists; create link to result directory   
  foundTab = tabExists(url,TAB_TITLES)
  if foundTab:
    addDirectoryItem(localize(30104), { 
                    "mode": MODE_VIEW_TITLES,
                    "url": url,
                    "page": 1,
                    "index": 0 })
  else:
    # Do nothing
    common.log("No titles found")


  # Search for the "episodes" tab. If it exists; create link to result directory   
  foundTab = tabExists(url,TAB_EPISODES)
  if foundTab:
    addDirectoryItem(localize(30105), { 
                    "mode": MODE_VIEW_EPISODES,
                    "url": url,
                    "page": 1,
                    "index": 0 })
  else:
    # Do nothing
    common.log("No episodes found")


  # Search for the "clips" tab. If it exists; create link to result directory   
  foundTab = tabExists(url,TAB_CLIPS)
  if foundTab:
    addDirectoryItem(localize(30106), { 
                    "mode": MODE_VIEW_CLIPS,
                    "url": url,
                    "page": 1,
                    "index": 0 })
  else:
    # Do nothing 
    common.log("No clips found")

  if not foundTab:
    # Raise dialog with a "No results found" message
    common.log("No search result") 
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT Play",localize(30103))
    viewSearch()
    return

def tabExists(url,tabname):
  """
  Check if a specific tab exists in the DOM.
  """
  html = helper.getPage(BASE_URL + url)
  return elementExists(html,"div",{ "data-tabname": tabname})

def elementExists(html,etype,attrs):
  """
  Check if a specific element exists in the DOM.

  Returns True if the element exists and False if not.
  """

  htmlelement = common.parseDOM(html,etype, attrs = attrs)

  return len(htmlelement) > 0


def viewPageResults(url,mode,page,index):
  """
  Creates a directory for the search results from
  the tab specified by the mode parameter.
  """ 
  common.log("url: " + url + " mode: " + mode)
  dirtype = None

  if MODE_VIEW_TITLES == mode:
    dirtype = MODE_PROGRAM
  elif MODE_VIEW_EPISODES == mode:
    dirtype = MODE_VIDEO
  elif MODE_VIEW_CLIPS == mode:
    dirtype = MODE_VIDEO
  else:
    common.log("Undefined mode")
    viewStart()
    return

  createDirectory(url,page,index,mode,dirtype)

def viewBestOfCategories():
  """
  Creates a directory displaying each of the
  categories from the bestofsvt page
  """
  categories = bestof.getCategories()
  params = {}
  params["mode"] = MODE_BESTOF_CATEGORY

  for category in categories:
    params["url"] = category["url"]
    addDirectoryItem(category["title"], params)

def viewBestOfCategory(url):
  """
  Creates a directory containing all shows displayed
  for a category
  """
  shows = bestof.getShows(url)
  params = {}
  params["mode"] = MODE_VIDEO

  for show in shows:
    params["url"] = show["url"]
    addDirectoryItem(show["title"], params, show["thumbnail"], False)

def createDirectory(url,page,index,callertype,dirtype):
  """
  Parses Ajax URL and last page number from the argument url and
  then calls populateDir to populate a directory with
  video/program items.
  """

  if not url.startswith("/"):
    url = "/" + url

  tabname = TAB_EPISODES
  if MODE_RECOMMENDED == callertype:
    tabname = TAB_RECOMMENDED
  elif MODE_LATEST_NEWS == callertype:
    tabname = TAB_NEWS
  elif MODE_VIEW_CLIPS == callertype:
    tabname = TAB_CLIPS
  elif MODE_CATEGORY == callertype or MODE_VIEW_TITLES == callertype:
    tabname = TAB_TITLES

  if not tabExists(url,tabname) and tabname == TAB_EPISODES:
    tabname = TAB_CLIPS # In case there are no episodes for a show, get the clips instead
  elif not tabExists(url,tabname):
    common.log("Could not find tab "+tabname+" on page. Aborting!")
    return 

  (foundUrl,ajaxurl,lastpage) = parseAjaxUrlAndLastPage(url,tabname)

  if not foundUrl:
    populateDirNoPaging(url,dirtype,tabname)
    return

  fetchitems = True
  pastlastpage = False

  page = int(page)
  index = int(index)
  lastpage = int(lastpage)

  while fetchitems:

    if page > lastpage:
      pastlastpage = True
      break

    (fetchitems,lastindex) = populateDir(ajaxurl,dirtype,str(page),index)
    page += 1

  if not pastlastpage:
    page = page - 1
    addDirectoryItem(localize(30101),
             { "mode": callertype,
               "url": url,
               "page": str(page),
               "index": lastindex})


def parseAjaxUrlAndLastPage(url,tabname):
  """
  Fetches the Ajax URL and the the last page number
  from a program page.
  """
  common.log("url: " + url + ", tabname: " + tabname)
  classexp = "[^\"']*playShowMoreButton[^\"']*"
  dataname = "sida"
  html = helper.getPage(BASE_URL + url)

  container = common.parseDOM(html,
                              "div",
                              attrs = { "class": "[^\"']*[playBoxBody|playBoxAltBody][^\"']*", "data-tabname": tabname })[0]

  attrs = { "class": classexp, "data-name": dataname}
  
  if elementExists(container,"a", attrs):
    ajaxurl = common.parseDOM(container,
                              "a",
                              attrs = attrs,
                              ret = "data-baseurl")[0]
  else:
    return (False,"","")

  lastpage = common.parseDOM(container,
                 "a",
                 attrs = { "class": classexp, "data-name": dataname },
                 ret = "data-lastpage")[0]

  ajaxurl = common.replaceHTMLCodes(ajaxurl)
  return (True,ajaxurl,lastpage)

def populateDir(ajaxurl,mode,page,index):
  """
  Populates a directory with items from a "Ajax" page.

  index is used as a starting reference if the not
  all items on a page were used to populate the previous
  directory.
  """
  common.log("ajaxurl: " + ajaxurl + ", mode: " + mode + ", page: " + page + ", index: " + str(index))

  global CURR_DIR_ITEMS

  articles = getArticles(ajaxurl,page)
  articles = articles[index:]
  index = 0

  for article in articles:

    if CURR_DIR_ITEMS >= MAX_DIR_ITEMS:
      CURR_DIR_ITEMS = 0
      return (False,index)
      
    createDirItem(article,mode)      

    index += 1

  return (True,0)

def populateDirNoPaging(url,mode,tabname):
  """
  Program pages that have less than 8 videos
  does not have a way to fetch the Ajax URL.
  Therefore we need a separate parse function
  for these programs.
  """
  common.log("url: " + url + ", mode: " + mode + ", tabname: " + tabname)

  articles = getArticles(url,None,tabname)
  
  for article in articles:
    createDirItem(article,mode)

def createDirItem(article,mode):
  """
  Given an article and a mode; create directory item
  for the article.
  """
  global CURR_DIR_ITEMS

  (title,url,thumbnail,info) = article

  if (not HIDE_SIGN_LANGUAGE) or title.lower().endswith("teckentolkad") == False:

    params = {}
    params["mode"] = mode
    params["url"] = url
    folder = False

    if(mode == MODE_VIDEO):
      params["url"] = url
    elif mode == MODE_PROGRAM:
      folder = True
      params["page"] = 1

    addDirectoryItem(title, params, thumbnail, folder, False, info)
    CURR_DIR_ITEMS += 1

def getArticles(ajaxurl,page,tabname=None):
  """
  Fetches all "article" DOM elements in a "svtGridBlock" and
  returns a list of quadruples containing:  
  title - the title of the article
  href - the URL of the article
  thumbnail - the thumbnail of the article
  info - metadata of the article
  """
  if page:
    pageurl = BASE_URL + ajaxurl + "sida=" + page
  else:
    pageurl = BASE_URL + ajaxurl 
  
  html = helper.getPage(pageurl)

  if not tabname:
    container = common.parseDOM(html,
                  "div",
                  attrs = { "class": "[^\"']*svtGridBlock[^\"']*" })[0]
  else:
    container = common.parseDOM(html,
                  "div",
                  attrs = { "data-tabname": tabname })[0]

  articles = common.parseDOM(container, "article")
  plots = common.parseDOM(container, "article", ret = "data-description")
  airtimes = common.parseDOM(container, "article", ret = "data-broadcasted")
  durations = common.parseDOM(container, "article", ret = "data-length")
  newarticles = []
  i = 0
 
  for article in articles:
    info = {}
    plot = plots[i]
    aired = airtimes[i]
    duration = durations[i]
    title = common.parseDOM(article,"h5")[0]
    href = common.parseDOM(article, "a",
                            attrs = { "class": "[^\"']*[playLink|playAltLink][^\"']*" },
                            ret = "href")[0]
    thumbnail = common.parseDOM(article,
                                "img",
                                attrs = { "class": "playGridThumbnail" },
                                ret = "src")[0]
    thumbnail = thumbnail.replace("/medium/", "/large/")
    
    title = common.replaceHTMLCodes(title)
    plot = common.replaceHTMLCodes(plot)
    aired = common.replaceHTMLCodes(aired) 
    info["title"] = title
    info["plot"] = plot
    info["aired"] = aired
    info["duration"] = helper.convertDuration(duration)
    newarticles.append((title,href,thumbnail,info))
    i += 1
 
  return newarticles


def startVideo(url):

  if not url.startswith("/"):
    url = "/" + url

  url = url + JSON_SUFFIX
  common.log("url: " + url)
  html = helper.getPage(BASE_URL + url)

  jsonString = common.replaceHTMLCodes(html)
  jsonObj = json.loads(jsonString)
  common.log(jsonString)

  subtitle = None
  player = xbmc.Player()
  startTime = time.time()
  videoUrl = None
  extension = "None"
  args = ""

  for video in jsonObj["video"]["videoReferences"]:
    """
    Determine which file extension that will be used
    m3u8 is preferred, hence the break.
    Order: m3u8, f4m, mp4, flv
    """
    tmpurl = video["url"]
    argpos = tmpurl.rfind("?")
    if argpos > 0:
      args = tmpurl[argpos:]
      tmpurl = tmpurl[:argpos]

    if tmpurl.endswith(".m3u8"):
      extension = "HLS"
      videoUrl = tmpurl
      break
    if tmpurl.endswith(".f4m"):
      extension = "F4M"
      videoUrl = tmpurl
      continue
    if tmpurl.endswith(".mp4"):
      extension = "MP4"
      videoUrl = tmpurl
      continue
    if tmpurl.endswith(".flv"):
      extension = "FLV"
      videoUrl = tmpurl
      continue
    videoUrl = tmpurl

  for sub in jsonObj["video"]["subtitleReferences"]:
    if sub["url"].endswith(".wsrt"):
      subtitle = sub["url"]
    else:
      if len(sub["url"]) > 0:
        common.log("Skipping unknown subtitle: " + sub["url"])

  if extension == "HLS" and HLS_STRIP:
    videoUrl = hlsStrip(videoUrl)

  if extension == "F4M":
    videoUrl = videoUrl.replace("/z/", "/i/").replace("manifest.f4m","master.m3u8")

  if extension == "MP4":
    videoUrl = mp4Handler(jsonObj)

  if extension == "None" and videoUrl:
    # No supported video was found
    common.log("No supported video extension found for URL: " + videoUrl)
    videoUrl = None

  if videoUrl:
    
    if args and not HLS_STRIP:
      common.log("Appending arguments: "+args)
      videoUrl = videoUrl + args

    if extension == "MP4" and videoUrl.startswith("rtmp://"):
      videoUrl = videoUrl + " swfUrl="+SWF_URL+" swfVfy=1"
 
    xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path=videoUrl))

    if subtitle:

      while not player.isPlaying() and time.time() - startTime < 10:
        time.sleep(1.)

      player.setSubtitles(subtitle)

      if not SHOW_SUBTITLES:
        player.showSubtitles(False)
  else:
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT PLAY", localize(30100))

def mp4Handler(jsonObj):
  """
  If there are several mp4 streams in the json object:
  pick the one with the highest bandwidth.

  Some programs are available with multiple mp4 streams
  for different bitrates. This function ensures that the one
  with the highest bitrate is chosen.

  Can possibly be extended to support some kind of quality
  setting in the plugin.
  """
  videos = []

  # Find all mp4 videos
  for video in jsonObj["video"]["videoReferences"]:
    if video["url"].endswith(".mp4"):
      videos.append(video)
  
  if len(videos) == 1:
    return videos[0]["url"]

  bitrate = 0
  url = ""

  # Find the video with the highest bitrate
  for video in videos:
    if video["bitrate"] > bitrate:
      bitrate = video["bitrate"]
      url = video["url"]          

  common.log("mp4 handler info: bitrate="+str(bitrate)+" url="+url)
  return url

def hlsStrip(videoUrl):
    """
    Extracts the stream that supports the
    highest bandwidth and is not using the avc1.77.30 codec.
    Returns the path to a m3u8 file on the local disk with a
    reference to the extracted stream.
    """
    common.log("Stripping file: " + videoUrl)

    ufile = urllib.urlopen(videoUrl)
    lines = ufile.readlines()

    newplaylist = "#EXTM3U\n"
    header = ""
    hlsurl = ""
    bandwidth = 0
    foundhigherquality = False

    for line in lines:
      if foundhigherquality:
        foundhigherquality = False
        hlsurl = line
      if "EXT-X-STREAM-INF" in line:
        if not "avc1.77.30" in line:
          match = re.match(r'.*BANDWIDTH=(\d+),.*CODECS=\"(.+?),.+',line)
          if match:
            if bandwidth < int(match.group(1)):
              foundhigherquality = True
              header = line
              bandwidth = int(match.group(1))
          continue

    if bandwidth == 0:
      return None

    ufile.close()
    newpath = os.path.join(xbmc.translatePath("special://temp"),"svt.m3u8")
    newfile = open(newpath, 'w')
    newplaylist += header + hlsurl

    try:
        newfile.write(newplaylist)
    finally:
        newfile.close()

    return newpath


def addDirectoryItem(title, params, thumbnail = None, folder = True, live = False, info = None):

  li = xbmcgui.ListItem(title)

  if thumbnail:
    li.setThumbnailImage(thumbnail)

  if live:
    li.setProperty("IsLive", "true")

  if not folder:
    li.setProperty("IsPlayable", "true")

  if info:
    li.setInfo("Video", info)

  xbmcplugin.addDirectoryItem(pluginHandle, sys.argv[0] + '?' + urllib.urlencode(params), li, folder)


params = helper.getUrlParameters(sys.argv[2])

mode = params.get("mode")
url = urllib.unquote_plus(params.get("url", ""))
page = params.get("page")
letter = params.get("letter")
index = params.get("index")

if not index:
  index = "0"

if not mode:
  viewStart()
elif mode == MODE_A_TO_O:
  if USE_ALPHA_CATEGORIES:
    viewAlphaDirectories()
  else:
    viewAtoO()
elif mode == MODE_LIVE:
  viewLive()
elif mode == MODE_CATEGORIES:
  viewCategories()
elif mode == MODE_CATEGORY:
  viewCategory(url,page,index)
elif mode == MODE_PROGRAM:
  viewProgram(url,page,index)
elif mode == MODE_VIDEO:
  startVideo(url)
elif mode == MODE_LATEST:
  viewLatest(mode,page,index)
elif mode == MODE_LATEST_NEWS:
  viewLatest(mode,page,index)
elif mode == MODE_LETTER:
  viewProgramsByLetter(letter)
elif mode == MODE_RECOMMENDED:
  viewLatest(mode,page,index)
elif mode == MODE_SEARCH:
  viewSearch()
elif mode == MODE_VIEW_TITLES or \
     mode == MODE_VIEW_EPISODES or \
     mode == MODE_VIEW_CLIPS:
  viewPageResults(url,mode,page,index)
elif mode == MODE_BESTOF_CATEGORIES:
  viewBestOfCategories()
elif mode == MODE_BESTOF_CATEGORY:
  viewBestOfCategory(url)
elif mode == MODE_CHANNELS:
  viewChannels()

xbmcplugin.endOfDirectory(pluginHandle)
