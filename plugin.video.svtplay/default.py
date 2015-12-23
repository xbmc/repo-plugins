# -*- coding: utf-8 -*-
import re
import json
import sys
import time
import urllib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import CommonFunctions as common
import resources.lib.bestofsvt as bestof
import resources.lib.helper as helper
import resources.lib.svt as svt
import resources.lib.PlaylistManager as PlaylistManager
import resources.lib.FavoritesManager as FavoritesManager
from resources.lib.PlaylistDialog import PlaylistDialog

MODE_CHANNELS = "kanaler"
MODE_A_TO_O = "a-o"
MODE_PROGRAM = "pr"
MODE_CLIPS = "clips"
MODE_LIVE_PROGRAMS = "live"
MODE_LATEST = "senaste"
MODE_LATEST_NEWS = 'news'
MODE_POPULAR = "populara"
MODE_LAST_CHANCE = "sista-chansen"
MODE_VIDEO = "video"
MODE_CATEGORIES = "categories"
MODE_CATEGORY = "ti"
MODE_LETTER = "letter"
MODE_SEARCH = "search"
MODE_BESTOF_CATEGORIES = "bestofcategories"
MODE_BESTOF_CATEGORY = "bestofcategory"
MODE_VIEW_TITLES = "view_titles"
MODE_VIEW_EPISODES = "view_episodes"
MODE_VIEW_CLIPS = "view_clips"
MODE_PLAYLIST_MANAGER = "playlist-manager"
MODE_FAVORITES = "favorites"

S_DEBUG = "debug"
S_HIDE_SIGN_LANGUAGE = "hidesignlanguage"
S_SHOW_SUBTITLES = "showsubtitles"
S_USE_ALPHA_CATEGORIES = "alpha"

PLUGIN_HANDLE = int(sys.argv[1])

addon = xbmcaddon.Addon("plugin.video.svtplay")
localize = addon.getLocalizedString
xbmcplugin.setContent(PLUGIN_HANDLE, "tvshows")

common.plugin = addon.getAddonInfo('name') + ' ' + addon.getAddonInfo('version')
common.dbg = helper.getSetting(S_DEBUG)


def viewStart():

  addDirectoryItem(localize(30009), { "mode": MODE_POPULAR })
  addDirectoryItem(localize(30003), { "mode": MODE_LATEST })
  addDirectoryItem(localize(30010), { "mode": MODE_LAST_CHANCE })
  addDirectoryItem(localize(30002), { "mode": MODE_LIVE_PROGRAMS })
  addDirectoryItem(localize(30008), { "mode": MODE_CHANNELS })
  addDirectoryItem(localize(30000), { "mode": MODE_A_TO_O })
  addDirectoryItem(localize(30001), { "mode": MODE_CATEGORIES })
  addDirectoryItem(localize(30007), { "mode": MODE_BESTOF_CATEGORIES })
  addDirectoryItem(localize(30006), { "mode": MODE_SEARCH })
  addDirectoryItem(localize(30405), { "mode": MODE_FAVORITES })
  addDirectoryItem(localize(30400), { "mode": MODE_PLAYLIST_MANAGER }, folder=False)

def viewFavorites():
  favorites = FavoritesManager.get_all()

  for item in favorites:
    list_item = xbmcgui.ListItem(item["title"])
    fm_script = "special://home/addons/plugin.video.svtplay/resources/lib/FavoritesManager.py"
    fm_action = "remove"
    list_item.addContextMenuItems(
      [
        (
          localize(30407),
          "XBMC.RunScript("+fm_script+", "+fm_action+", "+item["id"]+")"
         )
      ], replaceItems=True)
    params = {}
    params["url"] = item["url"]
    params["mode"] = MODE_PROGRAM
    xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys.argv[0] + '?' + urllib.urlencode(params), list_item, True)


def viewManagePlaylist():
  plm_dialog = PlaylistDialog()
  plm_dialog.doModal()
  del plm_dialog

def viewAtoO():
  programs = svt.getAtoO()

  for program in programs:
    addDirectoryItem(program["title"], { "mode": MODE_PROGRAM, "url": program["url"] })

def viewCategories():
  categories = svt.getCategories()

  for category in categories:
    addDirectoryItem(category["title"], { "mode": MODE_CATEGORY, "url": category["url"] }, thumbnail=category["thumbnail"])

def viewAlphaDirectories():
  alphas = svt.getAlphas()
  if not alphas:
    return
  for alpha in alphas:
    addDirectoryItem(alpha["title"], { "mode": MODE_LETTER, "letter": alpha["char"] })

def viewProgramsByLetter(letter):
  programs = svt.getProgramsByLetter(letter)

  for program in programs:
    addDirectoryItem(program["title"], { "mode": MODE_PROGRAM, "url": program["url"] })

def viewSection(section, page):
  (items, moreItems) = svt.getItems(section, page)
  if not items:
    return
  for item in items:
    createDirItem(item, MODE_VIDEO)
  if moreItems:
    addNextPageItem(page+1, section)

def viewChannels():
  channels = svt.getChannels()
  if not channels:
    return
  for channel in channels:
    createDirItem(channel, MODE_VIDEO)

def viewCategory(url):
  if url == svt.URL_TO_OA:
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT Play", localize(30107))
    viewStart()
    return

  programs = svt.getProgramsForCategory(url)
  if not programs:
    return
  for program in programs:
    addDirectoryItem(program["title"], { "mode" : MODE_PROGRAM, "url" : program["url"] }, thumbnail=program["thumbnail"])

def viewEpisodes(url):
  """
  Displays the episodes for a program with URL 'url'.
  """
  episodes = svt.getEpisodes(url)
  if not episodes:
    helper.errorMsg("No episodes found!")
    return

  for episode in episodes:
    createDirItem(episode, MODE_VIDEO)

def addClipDirItem(url):
  """
  Adds the "Clips" directory item to a program listing.
  """
  params = {}
  params["mode"] = MODE_CLIPS
  params["url"] = url
  addDirectoryItem(localize(30108), params)

def viewClips(url):
  """
  Displays the latest clips for a program
  """
  clips = svt.getClips(url)
  if not clips:
    helper.errorMsg("No clips found!")
    return

  for clip in clips:
    createDirItem(clip, MODE_VIDEO)

def viewSearch():
  keyword = common.getUserInput(localize(30102))
  if keyword == "" or not keyword:
    viewStart()
    return
  keyword = urllib.quote(keyword)
  helper.infoMsg("Search string: " + keyword)

  keyword = re.sub(r" ", "+", keyword)

  url = svt.URL_TO_SEARCH + keyword

  results = svt.getSearchResults(url)
  for result in results:
    mode = MODE_VIDEO
    if result["type"] == "program":
      mode = MODE_PROGRAM
    createDirItem(result["item"], mode)


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
    addDirectoryItem(show["title"], params, show["thumbnail"], False, False, show["info"])


def createDirItem(article, mode):
  """
  Given an article and a mode; create directory item
  for the article.
  """
  if not helper.getSetting(S_HIDE_SIGN_LANGUAGE) or (article["title"].lower().endswith("teckentolkad") == False and article["title"].lower().find("teckenspråk".decode("utf-8")) == -1):

    params = {}
    params["mode"] = mode
    params["url"] = article["url"]
    folder = False

    if mode == MODE_PROGRAM:
      folder = True
    info = None
    if "info" in article.keys():
      info = article["info"]
    addDirectoryItem(article["title"], params, article["thumbnail"], folder, False, info)

def addNextPageItem(nextPage, section):
  addDirectoryItem("Next page",
                   {  "page": nextPage,
                      "mode": section})

def startVideo(url):
  """
  Starts the XBMC player if a valid video URL is
  found for the given page URL.
  """
  if not url.startswith("/"):
    url = "/" + url

  url = svt.BASE_URL + url + svt.JSON_SUFFIX

  show_obj = helper.resolveShowURL(url)
  player = xbmc.Player()
  startTime = time.time()

  if show_obj["videoUrl"]:
    xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(path=show_obj["videoUrl"]))

    if show_obj["subtitleUrl"]:
      while not player.isPlaying() and time.time() - startTime < 10:
        time.sleep(1.)

      player.setSubtitles(show_obj["subtitleUrl"])

      if not helper.getSetting(S_SHOW_SUBTITLES):
        player.showSubtitles(False)
  else:
    # No video URL was found
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT Play", localize(30100))


def addDirectoryItem(title, params, thumbnail = None, folder = True, live = False, info = None):

  li = xbmcgui.ListItem(title)

  if thumbnail:
    li.setThumbnailImage(thumbnail)

  if live:
    li.setProperty("IsLive", "true")

  if not folder:
    if params["mode"] == MODE_VIDEO:
      li.setProperty("IsPlayable", "true")
      # Add context menu item for adding a video to playlist
      plm_script = "special://home/addons/plugin.video.svtplay/resources/lib/PlaylistManager.py"
      plm_action = "add"
      if not thumbnail:
        thumbnail = ""
      li.addContextMenuItems(
        [
          (
            localize(30404),
            "XBMC.RunScript("+plm_script+", "+plm_action+", "+params["url"]+", "+title+", "+thumbnail+")"
           )
        ], replaceItems=True)
  if params["mode"] == MODE_PROGRAM:
    # Add context menu item for adding programs as favorites
    fm_script = "special://home/addons/plugin.video.svtplay/resources/lib/FavoritesManager.py"
    fm_action = "add"
    li.addContextMenuItems(
      [
        (
          localize(30406),
          "XBMC.RunScript("+fm_script+", "+fm_action+", "+title+", "+params["url"]+")"
         )
      ], replaceItems=True)

  if info:
    li.setInfo("Video", info)
    if "fanart" in info.keys() and helper.getSetting("showfanart"):
      li.setArt({"fanart": info["fanart"]})

  xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys.argv[0] + '?' + urllib.urlencode(params), li, folder)

# Main segment of script
ARG_PARAMS = helper.getUrlParameters(sys.argv[2])
common.log(ARG_PARAMS)
ARG_MODE = ARG_PARAMS.get("mode")
ARG_URL = urllib.unquote_plus(ARG_PARAMS.get("url", ""))
ARG_PAGE = ARG_PARAMS.get("page")
if not ARG_PAGE:
  ARG_PAGE = "1"

if not ARG_MODE:
  viewStart()
elif ARG_MODE == MODE_A_TO_O:
  if helper.getSetting(S_USE_ALPHA_CATEGORIES):
    viewAlphaDirectories()
  else:
    viewAtoO()
elif ARG_MODE == MODE_CATEGORIES:
  viewCategories()
elif ARG_MODE == MODE_CATEGORY:
  viewCategory(ARG_URL)
elif ARG_MODE == MODE_PROGRAM:
  viewEpisodes(ARG_URL)
  addClipDirItem(ARG_URL)
elif ARG_MODE == MODE_CLIPS:
  viewClips(ARG_URL)
elif ARG_MODE == MODE_VIDEO:
  startVideo(ARG_URL)
elif ARG_MODE == MODE_POPULAR or \
     ARG_MODE == MODE_LATEST or \
     ARG_MODE == MODE_LAST_CHANCE or \
     ARG_MODE == MODE_LIVE_PROGRAMS:
  viewSection(ARG_MODE, int(ARG_PAGE))
elif ARG_MODE == MODE_CHANNELS:
  viewChannels()
elif ARG_MODE == MODE_LETTER:
  viewProgramsByLetter(ARG_PARAMS.get("letter"))
elif ARG_MODE == MODE_SEARCH:
  viewSearch()
elif ARG_MODE == MODE_BESTOF_CATEGORIES:
  viewBestOfCategories()
elif ARG_MODE == MODE_BESTOF_CATEGORY:
  viewBestOfCategory(ARG_URL)
elif ARG_MODE == MODE_PLAYLIST_MANAGER:
  viewManagePlaylist()
elif ARG_MODE == MODE_FAVORITES:
  viewFavorites()

xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
