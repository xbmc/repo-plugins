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

CURR_DIR_ITEMS = 0

pluginHandle = int(sys.argv[1])

settings = xbmcaddon.Addon()
localize = settings.getLocalizedString

common = CommonFunctions
common.plugin = "SVTOA Play 3"

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

BW_SELECT = False
if settings.getSetting("bwselect") == "true":
  BW_SELECT = True

LOW_BANDWIDTH  = int(float(settings.getSetting("bandwidth")))
HIGH_BANDWIDTH = svt.getHighBw(LOW_BANDWIDTH)
LOW_BANDWIDH   = LOW_BANDWIDTH

def viewStart():

  addDirectoryItem(localize(30000), { "mode": MODE_A_TO_O })
  addDirectoryItem(localize(30006), { "mode": MODE_SEARCH })
  
def viewAtoO():
  programs = svt.getAtoO()
  
  for program in programs:
    addDirectoryItem(program["title"], { "mode": MODE_PROGRAM, "url": program["url"], "page": 1 })


def viewAlphaDirectories():
  alphas = svt.getAlphas() 

  for alpha in alphas:
    addDirectoryItem(alpha["title"], { "mode": MODE_LETTER, "letter": alpha["char"] })


def viewProgramsByLetter(letter):
  programs = svt.getProgramsByLetter(letter)

  for program in programs:
    addDirectoryItem(program["title"], { "mode": MODE_PROGRAM, "url": program["url"], "page": 1 })


def viewProgram(url,page,index):
  if FULL_PROGRAM_PARSE:
    createTabIndex(url)
  else:
    createDirectory(url,page,index,MODE_PROGRAM,MODE_VIDEO)


def viewSearch():
  query = common.getUserInput(localize(30102))
  if query == "" or not query:
    viewStart()
    return
  query = urllib.quote(query)
  common.log("Search string: " + query)

  query = re.sub(r" ", "+", query)
  page = 1
  results = True

  while results:
    results = viewSearchPageResult(query, page)
    if not results:
      break

    if svt.hasMoreResults(query, page):
      page = page + 1
    else:
      results = False 

def viewSearchPageResult(query, page):
  programs = svt.getSearchResult(query, page)

  if not programs:
    return False  

  for program in programs:
    addDirectoryItem(program["title"], { "mode": MODE_VIDEO, "url": program["url"] }, False, False, program["info"])
  return True


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


def createDirectory(url,page,index,callertype,dirtype):
  """
  Creates a directory with list items from the supplied program
  page (url).
  """

  #if not url.startswith("/"):
  #  url = "/" + url

  tabname = svt.TAB_EPISODES
  if MODE_RECOMMENDED == callertype:
    tabname = svt.TAB_RECOMMENDED
  elif MODE_LATEST_NEWS == callertype:
    tabname = svt.TAB_NEWS
  elif MODE_VIEW_CLIPS == callertype:
    tabname = svt.TAB_CLIPS
  elif MODE_CATEGORY == callertype or MODE_VIEW_TITLES == callertype:
    tabname = svt.TAB_TITLES

  html = svt.getPage(url)

  visafler = common.parseDOM(html, "a", attrs = { "class": "[^\"']*svtCenterUnknown[^\"']*" }, ret = "href")

  if len(visafler) == 1:
    kolla = True
    populateDirNoPaging(url,dirtype,tabname)
    url = visafler[0]

    while (kolla):
      html = svt.getPage(url)
      visafler = common.parseDOM(html, "a", attrs = { "class": "[^\"']*svtCenterUnknown[^\"']*" }, ret = "href")
      populateDirNoPaging(url,dirtype,tabname)
      
      if len(visafler) == 2:
        url = visafler[1]
      else:
        kolla = False
        
    return
  else:
    populateDirNoPaging(url,dirtype,tabname)
    return    


def populateDirNoPaging(url,mode,tabname):
  """
  Program pages that have less than 8 videos
  does not have a way to fetch the Ajax URL.
  Use the normal page URL to populate the
  directory.
  """
  common.log("url: " + url + ", mode: " + mode + ", tabname: " + tabname)

  articles = svt.getArticles(url,None,tabname)
  
  for article in articles:
    createDirItem(article,mode)


def createDirItem(article,mode):
  """
  Given an article and a mode; create directory item
  for the article.
  """
  global CURR_DIR_ITEMS

  if (not HIDE_SIGN_LANGUAGE) or (article["title"].lower().endswith("teckentolkad") == False and article["title"].lower().find("teckenspråk".decode("utf-8")) == -1):

    params = {}
    params["mode"] = mode
    params["url"] = article["url"]
    folder = False

    if mode == MODE_PROGRAM:
      folder = True
      params["page"] = 1

    addDirectoryItem(article["title"], params, article["thumbnail"], folder, False, article["info"])
    CURR_DIR_ITEMS += 1


def startVideo(url):
  """
  Starts the XBMC player if a valid video url is 
  found for the given page url.
  """
  #if not url.startswith("/"):
  #  url = "/" + url

  url = url + svt.JSON_SUFFIX
  common.log("url: " + url)
  html = svt.getPage(url)

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
  elif extension == "HLS" and BW_SELECT: 
    videoUrl = getStream(videoUrl)

  if extension == "F4M":
    videoUrl = videoUrl.replace("/z/", "/i/").replace("manifest.f4m","master.m3u8")

  if extension == "MP4":
    videoUrl = mp4Handler(jsonObj)

  if extension == "None" and videoUrl:
    # No supported video was found
    common.log("No supported video extension found for URL: " + videoUrl)
    videoUrl = None

  if videoUrl:
    
    if args and not (HLS_STRIP or BW_SELECT):
      common.log("Appending arguments: "+args)
      videoUrl = videoUrl + args

    if extension == "MP4" and videoUrl.startswith("rtmp://"):
      videoUrl = videoUrl + " swfUrl="+svt.SWF_URL+" swfVfy=1"
 
    xbmcplugin.setResolvedUrl(pluginHandle, True, xbmcgui.ListItem(path=videoUrl))

    if subtitle:

      while not player.isPlaying() and time.time() - startTime < 10:
        time.sleep(1.)

      player.setSubtitles(subtitle)

      if not SHOW_SUBTITLES:
        player.showSubtitles(False)
  else:
    # No video URL was found
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT PLAY", localize(30100))


def mp4Handler(jsonObj):
  """
  If there are several mp4 streams in the JSON object:
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
    hlsurl = ""
    bandwidth = 0
    foundhigherquality = False

    for line in lines:
      if foundhigherquality:
        # The stream url is on the line proceeding the header
        foundhigherquality = False
        hlsurl = line
      if "EXT-X-STREAM-INF" in line: # The header
        if not "avc1.77.30" in line:
          match = re.match(r'.*BANDWIDTH=(\d+).+',line)
          if match:
            if bandwidth < int(match.group(1)):
              foundhigherquality = True
              bandwidth = int(match.group(1))
          continue

    if bandwidth == 0:
      return None

    ufile.close()
    hlsurl = hlsurl.rstrip()
    common.log("Returned stream url : " + hlsurl)
    return hlsurl


def getStream(url):
  """
  Returns a stream matching the set bandwidth
  """
  
  f = urllib.urlopen(url)
  lines = f.readlines()
  
  marker = "#EXT-X-STREAM-INF"
  found = False

  for line in lines:
    if found:
      # The stream url is on the line proceeding the header
      hlsurl = line
      break
    if marker in line: # The header
      match = re.match(r'.*BANDWIDTH=(\d+)000.+',line)
      if match:
        if LOW_BANDWIDTH < int(match.group(1)) < HIGH_BANDWIDTH:
          common.log("Found stream with bandwidth " + match.group(1) + " for selected bandwidth " + str(LOW_BANDWIDTH))
          found = True
  
  f.close()
  hlsurl = hlsurl.rstrip()
  common.log("Returned stream url: " + hlsurl)
  return hlsurl


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
