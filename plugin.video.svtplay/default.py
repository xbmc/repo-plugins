# -*- coding: utf-8 -*-
# system imports
import re
import os
import sys
import time
import urllib
import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
# own imports
import CommonFunctions as common
import resources.lib.helper as helper
import resources.lib.svt as svt

MODE_CHANNELS = "kanaler"
MODE_A_TO_O = "a-o"
MODE_PROGRAM = "pr"
MODE_CLIPS = "clips"
MODE_LIVE_PROGRAMS = "live"
MODE_LATEST = "latest"
MODE_LATEST_NEWS = 'news'
MODE_POPULAR = "popular"
MODE_LAST_CHANCE = "last_chance"
MODE_VIDEO = "video"
MODE_CATEGORIES = "categories"
MODE_CATEGORY = "ti"
MODE_LETTER = "letter"
MODE_SEARCH = "search"
MODE_VIEW_TITLES = "view_titles"
MODE_VIEW_EPISODES = "view_episodes"
MODE_VIEW_CLIPS = "view_clips"

# settings keys
S_DEBUG = "debug"
S_HIDE_SIGN_LANGUAGE = "hidesignlanguage"
S_SHOW_SUBTITLES = "showsubtitles"
S_USE_ALPHA_CATEGORIES = "alpha"
S_HIDE_RESTRICTED_TO_SWEDEN = "hideonlysweden"

# plugin setup
PLUGIN_HANDLE = int(sys.argv[1])
addon = xbmcaddon.Addon("plugin.video.svtplay")
localize = addon.getLocalizedString
xbmcplugin.setContent(PLUGIN_HANDLE, "tvshows")
xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(PLUGIN_HANDLE, xbmcplugin.SORT_METHOD_LABEL)

DEFAULT_FANART = os.path.join(
  xbmc.translatePath(addon.getAddonInfo("path")+"/resources/images/").decode("utf-8"),
  "background.png")

common.plugin = "%s %s" % (addon.getAddonInfo('name'), addon.getAddonInfo('version'))
common.dbg = helper.getSetting(S_DEBUG)

def view_start():
  __add_directory_item(localize(30009), {"mode": MODE_POPULAR})
  __add_directory_item(localize(30003), {"mode": MODE_LATEST})
  __add_directory_item(localize(30004), {"mode": MODE_LATEST_NEWS})
  __add_directory_item(localize(30010), {"mode": MODE_LAST_CHANCE})
  __add_directory_item(localize(30002), {"mode": MODE_LIVE_PROGRAMS})
  __add_directory_item(localize(30008), {"mode": MODE_CHANNELS})
  __add_directory_item(localize(30000), {"mode": MODE_A_TO_O})
  __add_directory_item(localize(30001), {"mode": MODE_CATEGORIES})
  __add_directory_item(localize(30006), {"mode": MODE_SEARCH})

def view_a_to_z():
  programs = svt.getAtoO()
  __program_listing(programs)

def view_alpha_directories():
  alphas = svt.getAlphas()
  if not alphas:
    return
  for alpha in alphas:
    __add_directory_item(alpha, {"mode": MODE_LETTER, "letter": alpha})

def view_programs_by_letter(letter):
  programs = svt.getProgramsByLetter(letter)
  __program_listing(programs)

def __program_listing(programs):
  for program in programs:
    if program["onlyAvailableInSweden"] and \
        helper.getSetting(S_HIDE_RESTRICTED_TO_SWEDEN):
      continue
    folder = True
    mode = MODE_PROGRAM
    if program["type"] == "video":
      mode = MODE_VIDEO
      folder = False
    __add_directory_item(program["title"],
                {"mode": mode, "url": program["url"]},
                thumbnail=program["thumbnail"], folder=folder)

def view_categories():
  categories = svt.getCategories()
  for category in categories:
    __add_directory_item(category["title"],
                {"mode": MODE_CATEGORY, "url": category["genre"]})

def view_section(section, page):
  (items, more_items) = svt.getItems(section, page)
  if not items:
    return
  for item in items:
    mode = MODE_VIDEO
    if item["type"] == "program":
      mode = MODE_PROGRAM
    __create_dir_item(item, mode)
  if more_items:
    __add_next_page_item(page+1, section)

def view_channels():
  channels = svt.getChannels()
  if not channels:
    return
  for channel in channels:
    __create_dir_item(channel, MODE_VIDEO)

def view_latest_news():
    items = svt.getLatestNews()
    if not items:
      return
    for item in items:
      __create_dir_item(item, MODE_VIDEO)

def view_category(genre):
  programs = svt.getProgramsForGenre(genre)
  if not programs:
    return
  for program in programs:
    mode = MODE_PROGRAM
    if program["type"] == "video":
      mode = MODE_VIDEO
    __create_dir_item(program, mode)

def view_episodes(url):
  """
  Displays the episodes for a program
  """
  common.log("View episodes for %s" % url)
  episodes = svt.getEpisodes(url.split("/")[-1])
  if episodes is None:
    helper.errorMsg("No episodes found!")
    return
  for episode in episodes:
    __create_dir_item(episode, MODE_VIDEO)

def __add_clip_dir_item(url):
  """
  Adds the "Clips" directory item to a program listing.
  """
  params = {}
  params["mode"] = MODE_CLIPS
  params["url"] = url
  __add_directory_item(localize(30108), params)

def view_clips(url):
  """
  Displays the latest clips for a program
  """
  common.log("View clips for %s" % url)
  clips = svt.getClips(url.split("/")[-1])
  if not clips:
    helper.errorMsg("No clips found!")
    return
  for clip in clips:
    __create_dir_item(clip, MODE_VIDEO)

def view_search():
  keyword = common.getUserInput(localize(30102))
  if keyword == "" or not keyword:
    view_start()
    return
  keyword = urllib.quote(keyword)
  helper.infoMsg("Search string: " + keyword)
  keyword = re.sub(r" ", "+", keyword)
  keyword = keyword.strip()
  results = svt.getSearchResults(keyword)
  for result in results:
    mode = MODE_VIDEO
    if result["type"] == "program":
      mode = MODE_PROGRAM
    __create_dir_item(result["item"], mode)

def __create_dir_item(article, mode):
  """
  Given an article and a mode; create directory item
  for the article.
  """
  if not helper.getSetting(S_HIDE_SIGN_LANGUAGE) \
      or (not article["title"].lower().endswith("teckentolkad") \
      and article["title"].lower().find("teckenspråk".decode("utf-8")) == -1):
    params = {}
    params["mode"] = mode
    params["url"] = article["url"]
    folder = False
    if mode == MODE_PROGRAM:
      folder = True
    info = None
    if "info" in article.keys():
      if "onlyAvailableInSweden" in article["info"] and \
          article["info"]["onlyAvailableInSweden"] and \
          helper.getSetting(S_HIDE_RESTRICTED_TO_SWEDEN):
        # Do not show geo restricted items
        return
      info = article["info"]
    __add_directory_item(article["title"], params, article["thumbnail"], folder, False, info)

def __add_next_page_item(next_page, section):
  __add_directory_item("Next page",
                   {"page": next_page,
                    "mode": section})

def start_video(video_id):
  video_json = svt.getVideoJSON(video_id)
  if video_json is None:
    common.log("ERROR: Could not get video JSON")
    return
  try:
    show_obj = helper.resolveShowJSON(video_json)
  except ValueError:
    common.log("Could not decode JSON for "+video_id)
    return
  if show_obj["videoUrl"]:
    play_video(show_obj)
  else:
    dialog = xbmcgui.Dialog()
    dialog.ok("SVT Play", localize(30100))

def play_video(show_obj):
  player = xbmc.Player()
  start_time = time.time()
  xbmcplugin.setResolvedUrl(PLUGIN_HANDLE, True, xbmcgui.ListItem(path=show_obj["videoUrl"]))
  if show_obj["subtitleUrl"]:
    while not player.isPlaying() and time.time() - start_time < 10:
      time.sleep(1.)
    player.setSubtitles(show_obj["subtitleUrl"])
    if not helper.getSetting(S_SHOW_SUBTITLES):
      player.showSubtitles(False)

def __add_directory_item(title, params, thumbnail="", folder=True, live=False, info=None):
  list_item = xbmcgui.ListItem(title)
  if thumbnail:
    list_item.setThumbnailImage(thumbnail)
  if live:
    list_item.setProperty("IsLive", "true")
  if not folder and params["mode"] == MODE_VIDEO:
      list_item.setProperty("IsPlayable", "true")
  fanart = info.get("fanart", "") if info else DEFAULT_FANART
  poster = info.get("poster", "") if info else ""
  if info:
    list_item.setInfo("Video", info)
  list_item.setArt({
    "fanart": fanart,
    "poster": poster,
    "thumbnail": thumbnail
  })
  xbmcplugin.addDirectoryItem(PLUGIN_HANDLE, sys.argv[0] + '?' + urllib.urlencode(params), list_item, folder)

# Main segment of script
ARG_PARAMS = helper.getUrlParameters(sys.argv[2])
common.log("params: " + str(ARG_PARAMS))
ARG_MODE = ARG_PARAMS.get("mode")
ARG_URL = urllib.unquote_plus(ARG_PARAMS.get("url", ""))
ARG_PAGE = ARG_PARAMS.get("page")
if not ARG_PAGE:
  ARG_PAGE = "1"

if not ARG_MODE:
  view_start()
elif ARG_MODE == MODE_A_TO_O:
  if helper.getSetting(S_USE_ALPHA_CATEGORIES):
    view_alpha_directories()
  else:
    view_a_to_z()
elif ARG_MODE == MODE_CATEGORIES:
  view_categories()
elif ARG_MODE == MODE_CATEGORY:
  view_category(ARG_URL)
elif ARG_MODE == MODE_PROGRAM:
  view_episodes(ARG_URL)
  __add_clip_dir_item(ARG_URL)
elif ARG_MODE == MODE_CLIPS:
  view_clips(ARG_URL)
elif ARG_MODE == MODE_VIDEO:
  start_video(ARG_URL)
elif ARG_MODE == MODE_POPULAR or \
     ARG_MODE == MODE_LATEST or \
     ARG_MODE == MODE_LAST_CHANCE or \
     ARG_MODE == MODE_LIVE_PROGRAMS:
  view_section(ARG_MODE, int(ARG_PAGE))
elif ARG_MODE == MODE_LATEST_NEWS:
  view_latest_news()
elif ARG_MODE == MODE_CHANNELS:
  view_channels()
elif ARG_MODE == MODE_LETTER:
  view_programs_by_letter(ARG_PARAMS.get("letter"))
elif ARG_MODE == MODE_SEARCH:
  view_search()

xbmcplugin.endOfDirectory(PLUGIN_HANDLE)
