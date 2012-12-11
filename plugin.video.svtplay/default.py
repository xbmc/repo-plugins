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
MODE_SEARCH_TITLES = "search_titles"
MODE_SEARCH_EPISODES = "search_episodes"
MODE_SEARCH_CLIPS = "search_clips"

BASE_URL = "http://www.svtplay.se"

URL_A_TO_O = "/program"
URL_CATEGORIES = "/kategorier"
URL_TO_LATEST = "?tab=episodes&sida=1"
URL_TO_LATEST_NEWS = "?tab=news&sida=1"
URL_TO_RECOMMENDED = "?tab=recommended&sida=1"
URL_TO_SEARCH = "/sok?q="

VIDEO_PATH_RE = "/(klipp|video|live)/\d+"
VIDEO_PATH_SUFFIX = "?type=embed"

MAX_NUM_GRID_ITEMS = 12
CURR_DIR_ITEMS = 0

pluginHandle = int(sys.argv[1])

settings = xbmcaddon.Addon()
localize = settings.getLocalizedString

common = CommonFunctions
common.plugin = "SVT Play 3"

if settings.getSetting('debug') == "true":
  common.dbg = True
else:
  common.dbg = False

if settings.getSetting("hlsstrip") == "true":
    HLS_STRIP = True
else:
    HLS_STRIP = False

MAX_DIR_ITEMS = int(float(settings.getSetting("diritems")))

def viewStart():

  addDirectoryItem(localize(30000), { "mode": MODE_A_TO_O })
  addDirectoryItem(localize(30001), { "mode": MODE_CATEGORIES })
  addDirectoryItem(localize(30005), { "mode": MODE_RECOMMENDED, "page": 1 })
  addDirectoryItem(localize(30002), { "mode": MODE_LIVE })
  addDirectoryItem(localize(30003), { "mode": MODE_LATEST, "page": 1 })
  addDirectoryItem(localize(30004), { "mode": MODE_LATEST_NEWS, "page": 1 })
  addDirectoryItem(localize(30006), { "mode": MODE_SEARCH })


def viewAtoO():
  html = getPage(BASE_URL + URL_A_TO_O)

  texts = common.parseDOM(html, "a" , attrs = { "class": "playAlphabeticLetterLink" })
  hrefs = common.parseDOM(html, "a" , attrs = { "class": "playAlphabeticLetterLink" }, ret = "href")

  for index, text in enumerate(texts):
    addDirectoryItem(common.replaceHTMLCodes(text), { "mode": MODE_PROGRAM, "url": hrefs[index], "page": 1 })

def viewLive():
  html = getPage(BASE_URL)

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

          url = match.group() + VIDEO_PATH_SUFFIX

          addDirectoryItem(common.replaceHTMLCodes(text), { "mode": MODE_VIDEO, "url": url }, None, False, True)

def viewCategories():
  html = getPage(BASE_URL + URL_CATEGORIES)

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
  html = getPage(BASE_URL + URL_A_TO_O)

  container = common.parseDOM(html, "div", attrs = { "id" : "playAlphabeticLetterList" })

  letters = common.parseDOM(container, "h2", attrs = { "class" : "playAlphabeticLetterHeading " })

  for letter in letters:
    url = letter
    addDirectoryItem(convertChar(letter), { "mode": MODE_LETTER, "letter": url })

def viewProgramsByLetter(letter):

  letter = urllib.unquote(letter)

  html = getPage(BASE_URL + URL_A_TO_O)

  container = common.parseDOM(html, "div", attrs = { "id": "playAlphabeticLetterList" })

  letterboxes = common.parseDOM(container, "div", attrs = { "class": "playAlphabeticLetter" })

  for letterbox in letterboxes:

    heading = common.parseDOM(letterbox, "h2")[0]

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
  createDirectory(url,page,index,MODE_PROGRAM,MODE_VIDEO)

def viewSearch():

  keyword = common.getUserInput(localize(30102))
  keyword = urllib.quote(keyword)
  common.log("Search string: " + keyword)

  if keyword == "" or not keyword:
    viewStart()
    return 

  keyword = re.sub(r" ","+",keyword) 

  url = URL_TO_SEARCH + keyword
  html = getPage(BASE_URL + url)
  foundTab = False
 
  # Try fetching the "titles" tab. If it exists; create link to result directory   
  try:
    common.parseDOM(html, "div", attrs = { "data-tabname": "titles" })[0]
    foundTab = True
  except:
    # Do nothing
    common.log("No titles found")
  else:
    addDirectoryItem(localize(30104), { 
                    "mode": MODE_SEARCH_TITLES,
                    "url": url,
                    "page": 1,
                    "index": 0 })

  # Try fetching the "episodes" tab. If it exists; create link to result directory   
  try:
    common.parseDOM(html, "div", attrs = { "data-tabname": "episodes" })[0]
    foundTab = True
  except:
    # Do nothing
    common.log("No episodes found")
  else:
    addDirectoryItem(localize(30105), { 
                    "mode": MODE_SEARCH_EPISODES,
                    "url": url,
                    "page": 1,
                    "index": 0 })

  # Try fetching the "clips" tab. If it exists; create link to result directory   
  try:
    common.parseDOM(html, "div", attrs = { "data-tabname": "clips" })[0]
    foundTab = True
  except:
    # Do nothing 
    common.log("No clips found")
  else:
    addDirectoryItem(localize(30106), { 
                    "mode": MODE_SEARCH_CLIPS,
                    "url": url,
                    "page": 1,
                    "index": 0 })
 
  if not foundTab:
    # Raise dialog with a "No results found" message
    common.log("No search result") 
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT Play",localize(30103))
    viewSearch()
    return

def viewSearchResults(url,mode,page,index):
  """
  Creates a directory for the search results from
  the tab specified by the mode parameter.
  """ 
  common.log("url: " + url + " mode: " + mode)
  dirtype = None

  if MODE_SEARCH_TITLES == mode:
    dirtype = MODE_PROGRAM
  elif MODE_SEARCH_EPISODES == mode:
    dirtype = MODE_VIDEO
  elif MODE_SEARCH_CLIPS == mode:
    dirtype = MODE_VIDEO
  else:
    common.log("Undefined mode")
    viewStart()
    return

  createDirectory(url,page,index,mode,dirtype)

def createDirectory(url,page,index,callertype,dirtype):
  """
  Parses Ajax URL and last page number from the argument url and
  then calls populateDir to populate a directory with
  video/program items.
  """

  if not url.startswith("/"):
    url = "/" + url

  tabname = "episodes"
  if MODE_RECOMMENDED == callertype:
    tabname = "recommended"
  elif MODE_LATEST_NEWS == callertype:
    tabname = "news"
  elif MODE_SEARCH_CLIPS == callertype:
    tabname = "clips"
  elif MODE_CATEGORY == callertype or MODE_SEARCH_TITLES == callertype:
    tabname = "titles"

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
  html = getPage(BASE_URL + url)

  container = common.parseDOM(html,
                              "div",
                              attrs = { "class": "[^\"']*[playBoxBody|playBoxAltBody][^\"']*", "data-tabname": tabname })[0]
  try:
    ajaxurl = common.parseDOM(container,
                                "a",
                                attrs = { "class": classexp, "data-name": dataname },
                                ret = "data-baseurl")[0]
  except:
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

  if settings.getSetting("hidesignlanguage") == "false" or \
     title.lower().endswith("teckentolkad") == False:

    params = {}
    params["mode"] = mode
    params["url"] = url
    folder = False

    if(mode == MODE_VIDEO):
      params["url"] = url + VIDEO_PATH_SUFFIX
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
  
  html = getPage(pageurl)

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
    info["duration"] = convertDuration(duration)
    newarticles.append((title,href,thumbnail,info))
    i += 1
 
  return newarticles

def convertDuration(duration):
  """
  Converts SVT's duration format to XBMC friendly format (minutes).

  SVT has the following format on their duration strings:
  1 h 30 min
  1 min 30 sek
  1 min
  """

  match = re.match(r'(^(\d+)\sh)*(\s*(\d+)\smin)*(\s*(\d+)\ssek)*',duration)

  dhours = 0
  dminutes = 0
  dseconds = 0

  if match.group(1):
    dhours = int(match.group(2)) * 60

  if match.group(3):
    dminutes = int(match.group(4))
 
  if match.group(5):
    dseconds = int(match.group(6)) / 60

  return str(dhours + dminutes + dseconds) 

def startVideo(url):

  if not url.startswith("/"):
    url = "/" + url

  html = getPage(BASE_URL + url)

  jsonString = common.parseDOM(html, "param", attrs = { "name": "flashvars" }, ret = "value")[0]

  jsonString = jsonString.lstrip("json=")
  jsonString = common.replaceHTMLCodes(jsonString)

  jsonObj = json.loads(jsonString)

  common.log(jsonString)

  subtitle = None
  player = xbmc.Player()
  startTime = time.time()
  videoUrl = None
  hlsvideo = False

  for video in jsonObj["video"]["videoReferences"]:
    if video["url"].find(".m3u8") > 0:
      videoUrl = video["url"]
      hlsvideo = True
      break
    if video["url"].endswith(".flv"):
      videoUrl = video["url"]
      break
    if video["url"].endswith(".mp4"):
      videoUrl = video["url"]
      break
    else:
      if video["url"].endswith("/manifest.f4m"):
        videoUrl = video["url"].replace("/z/", "/i/").replace("/manifest.f4m", "/master.m3u8")
        hlsvideo = True
      else:
        common.log("Skipping unknown filetype: " + video["url"])

  for sub in jsonObj["video"]["subtitleReferences"]:
    if sub["url"].endswith(".wsrt"):
      subtitle = sub["url"]
    else:
      if len(sub["url"]) > 0:
        common.log("Skipping unknown subtitle: " + sub["url"])

  if hlsvideo and HLS_STRIP:
      videoUrl = hlsStrip(videoUrl)

  if videoUrl:

    xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path=videoUrl))

    if subtitle:

      while not player.isPlaying() and time.time() - startTime < 10:
        time.sleep(1.)

      player.setSubtitles(subtitle)

      if settings.getSetting("showsubtitles") == "false":
        player.showSubtitles(False)
  else:
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT PLAY", localize(30100))

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


def getPage(url):

  result = common.fetchPage({ "link": url })

  if result["status"] == 200:
    	return result["content"]

  if result["status"] == 500:
    common.log("redirect url: %s" %result["new_url"])
    common.log("header: %s" %result["header"])
    common.log("content: %s" %result["content"])


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


def convertChar(char):
  if char == "&Aring;":
    return "Å"
  elif char == "&Auml;":
    return "Ä"
  elif char == "&Ouml;":
    return "Ö"
  else:
    return char

def getUrlParameters(arguments):

  params = {}

  if arguments:
    
      start = arguments.find("?") + 1
      pairs = arguments[start:].split("&")

      for pair in pairs:

        split = pair.split("=")

        if len(split) == 2:
          params[split[0]] = split[1]
  
  return params

params = getUrlParameters(sys.argv[2])

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
  if settings.getSetting("alpha") == "true":
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
elif mode == MODE_SEARCH_TITLES or \
     mode == MODE_SEARCH_EPISODES or \
     mode == MODE_SEARCH_CLIPS:
  viewSearchResults(url,mode,page,index)

xbmcplugin.endOfDirectory(pluginHandle)
