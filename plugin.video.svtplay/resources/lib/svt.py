# -*- coding: utf-8 -*-
# system imports
from __future__ import absolute_import,unicode_literals
import re
import requests
import time
# own imports
from . import logging
from . import helper

try:
  # Python 2
  from HTMLParser import HTMLParser
  from urllib import unquote
  parser = HTMLParser()
  unescape = parser.unescape
except ImportError:
  # Python 3
  from html import unescape
  from urllib.parse import unquote

BASE_URL = "https://www.svtplay.se"
SVT_BASE_URL = "https://api.svt.se/"
API_URL = "/api/"
VIDEO_API_URL="https://api.svt.se/videoplayer-api/video/"
WANTED_AS = "none" # wanted accessibility service


def getAtoO():
  """
  Returns a list of all items, sorted A-Z.
  """
  json_data = __get_json("all_titles_and_singles")
  if json_data is None:
    return None
  items = []
  for title in json_data:
    items.append(__create_item_by_title(title))
  return sorted(items, key=lambda item: item["title"])

def getCategories():
  """
  Returns a list of all categories.
  """
  json_data = __get_json("clusters")
  if json_data is None:
    return None
  categories = []
  for cluster in json_data:
    category = {}
    category["title"] = cluster["name"]
    category["url"] = cluster["contentUrl"]
    category["genre"] = cluster["slug"]
    categories.append(category)
  return categories

def getLatestNews():
  """
  Returns a list of latest news programs.
  """
  json_data = __get_json("cluster_latest?cluster=nyheter")
  if json_data is None:
    return None
  programs = []
  for item in json_data:
    live_str = ""
    thumbnail = item.get("thumbnail", "")
    if item["broadcastedNow"]:
      live_str = " " + "[COLOR red](Live)[/COLOR]"
    versions = item.get("versions", [])
    url = "video/" + item["contentUrl"]
    if versions:
      url = __get_video_version(versions)
    program = {
        "title" : unescape(item["programTitle"] + " " + (item["title"] or "") + live_str),
        "thumbnail" : helper.prepareThumb(thumbnail, baseUrl=BASE_URL),
        "url" : url,
        "info" : { "duration" : item.get("materialLength", 0), "fanart" : helper.prepareFanart(item.get("poster", ""), baseUrl=BASE_URL) }
        }
    programs.append(program)
  return programs

def getProgramsForGenre(genre):
  """
  Returns a list of all programs for a genre.
  """
  json_data = __get_json("cluster_titles_and_episodes?cluster="+genre)
  if json_data is None:
    return None
  programs = []
  for item in json_data:
    versions = item.get("versions", [])
    content_type = "video"
    if versions:
      url = __get_video_version(versions)
    else:
      url = item["contentUrl"]
      content_type = "program"
    title = item["programTitle"]
    plot = item.get("description", "")
    thumbnail = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    if not thumbnail:
      thumbnail = helper.prepareThumb(item.get("poster", ""), BASE_URL)
    info = {"plot": plot, "thumbnail": thumbnail, "fanart": thumbnail}
    programs.append({
      "title": title,
      "url": url,
      "thumbnail": thumbnail,
      "info": info,
      "type" : content_type
    })
  return programs

def getAlphas():
  """
  Returns a list of all letters in the alphabet that has programs.

  Hard coded as the API can't return a list.
  """
  alphas = []
  alphas.append("A")
  alphas.append("B")
  alphas.append("C")
  alphas.append("D")
  alphas.append("E")
  alphas.append("F")
  alphas.append("G")
  alphas.append("H")
  alphas.append("I")
  alphas.append("J")
  alphas.append("K")
  alphas.append("L")
  alphas.append("M")
  alphas.append("N")
  alphas.append("O")
  alphas.append("P")
  alphas.append("Q")
  alphas.append("R")
  alphas.append("S")
  alphas.append("T")
  alphas.append("U")
  alphas.append("V")
  alphas.append("W")
  alphas.append("X")
  alphas.append("Y")
  alphas.append("Z")
  alphas.append("Å")
  alphas.append("Ä")
  alphas.append("Ö")
  alphas.append("0-9")
  return alphas

def getProgramsByLetter(letter):
  """
  Returns a list of all program starting with the supplied letter.
  """
  logging.log("getProgramsByLetter: {}".format(letter))
  json_data = __get_json("all_titles_and_singles")
  if json_data is None:
    return None
  pattern = "^[{}]".format(letter.upper())
  items = []
  for title in json_data:
    if re.search(pattern, title["programTitle"]):
      items.append(__create_item_by_title(title))
  return items

def __create_item_by_title(title):
  item = {}
  item["title"] = title["programTitle"]
  item["url"] = title["contentUrl"]
  item["thumbnail"] = ""
  item["type"] = "program"
  item["onlyAvailableInSweden"] = title.get("onlyAvailableInSweden", False)
  if "/video/" in item["url"]:
    item["type"] = "video"
  return item

def getSearchResults(search_term):
  """
  Returns a list of both clips and programs
  for the supplied search URL.
  """
  search_term = search_term.strip()
  json_data = __get_json("search?q="+search_term)
  if json_data is None:
    return None
  items = []
  for result in json_data["videosAndTitles"]:
    item = {}
    versions = result.get("versions", [])
    result_type = result.get("titleType", "PROGRAM_FOLDER_OR_MOVIE")
    item_type = "video"
    if versions:
      # MOVIE and episode
      item["url"] = __get_video_version(versions)
    else:
      # Folder or clip
      item["url"] = result["contentUrl"]
      item_type = "program"
    if result_type == "CLIP":
      item_type = "video"
      item["url"] = result["id"]
      item["title"] = unescape(result["title"])
      item["thumbnail"] = helper.prepareThumb(result.get("thumbnail", ""), baseUrl=BASE_URL)
    elif result_type == "SERIES_OR_TV_SHOW":
      item["title"] = unescape(result["programTitle"] + " - " + result["title"])
      item["thumbnail"] = helper.prepareThumb(result.get("poster", ""), baseUrl=BASE_URL)
      item["info"] = {}
      item["info"]["plot"] = result.get("description", "")
    else:
      # MOVIE and folder
      item["title"] = unescape(result["programTitle"])
      item["thumbnail"] = helper.prepareThumb(result.get("poster", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = result.get("description", "")
    items.append({"item": item, "type": item_type})
  return items

def getChannels():
  """
  Returns the live channels from the page "Kanaler".
  """
  time_str = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
  url = "program-guide/programs?channel=svt1,svt2,svt24,svtb,svtk&includePartiallyOverlapping=true&from={timestamp}&to={timestamp}".format(timestamp=time_str)
  json_data = __get_svt_json(url)
  if json_data is None:
    return None
  items = []
  for channel in json_data["hits"]:
    item = {}
    program_title = channel["programmeTitle"]
    ch_id = channel["channel"].lower()
    if channel["channel"] == "SVTK":
      ch_id="kunskapskanalen"
    elif channel["channel"] == "SVTB":
      ch_id="barnkanalen"
    item["title"] = ch_id.upper() + " - " + program_title
    if channel["live"]:
      item["title"] = item["title"] + " [COLOR red]Live[/COLOR]"
    item["info"] = {}
    item["info"]["plot"] = channel.get("longDescription", "No description")
    item["info"]["title"] = item["title"]
    item["url"] = "ch-" + ch_id
    item["thumbnail"] = ""
    items.append(item)

  return items

def getEpisodes(slug):
  """
  Returns the episodes for a slug
  """
  title_data = __get_title_for_slug(slug)
  if title_data is None:
    return None
  article_id = title_data["articleId"]
  fanart = helper.prepareFanart(title_data.get("poster", ""), BASE_URL)
  api_action = "title_episodes_by_article_id?articleId={}".format(str(article_id))
  json_data = __get_json(api_action)
  if json_data is None:
    return None
  programs = []
  for item in json_data:
    program = {}
    program["title"] = item["title"]
    try:
      program["title"] = program["title"] + "[COLOR gray] (S{season}E{episode})[/COLOR]".format(season=str(item["season"]), episode=str(item["episodeNumber"]))
    except KeyError:
      # Suppress
      pass
    versions = item.get("versions", [])
    if versions:
      program["url"] = __get_video_version(versions)
    if program["url"] is None or not versions:
      logging.log("No video versions found for {}, skipping item!".format(item["title"]))
      continue
    program["thumbnail"] = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    info = {}
    info["plot"] = item.get("description", "")
    info["poster"] = helper.prepareFanart(item.get("poster", ""), BASE_URL)
    info["fanart"] = fanart
    info["duration"] = item.get("materialLength", "")
    info["tagline"] = item.get("shortDescription", "")
    info["season"] = item.get("season", "")
    info["episode"] = item.get("episode", "")
    info["playcount"] = 0
    info["onlyAvailableInSweden"] = item.get("onlyAvailableInSweden", False)
    program["info"] = info
    programs.append(program)
  return programs

def getClips(slug):
  """
  Returns the clips for a slug.
  """
  title_data = __get_title_for_slug(slug)
  if title_data is None:
    return None
  article_id = title_data["articleId"]
  url = "title_clips_by_title_article_id?articleId={}".format(str(article_id))
  json_data = __get_json(url)
  if json_data is None:
    return None
  clips = []
  for item in json_data:
    clip = {}
    clip["title"] = item["title"]
    clip["url"] = str(item["id"])
    clip["thumbnail"] = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    info = {}
    info["title"] = clip["title"]
    info["plot"] = item.get("description", "")
    clip["info"] = info
    clips.append(clip)
  return clips

def getVideoJSON(video_id):
  video_version_id = video_id
  if video_id.startswith("/video/"):
    # Special case as some listings don't have video versions available.
    # The second part (12345) of video_id is then the episode ID
    # /video/12345/mystring/
    episode_id = video_id.split("/")[2]
    video_version_id = __get_video_id_for_episode_id(episode_id)
  return __get_video_json_for_video_id(video_version_id)

def getItems(section_name, page):
  if not page:
    page = 1
  json_data = __get_json(section_name+"?page="+str(page)+"&excludedTagsString=lokalt")
  if json_data is None:
    return None
  current_page = json_data["currentPage"]
  total_pages = json_data["totalPages"]
  returned_items = []
  for video in json_data["data"]:
    versions = video.get("versions", [])
    item = {}
    item["title"] = video["programTitle"]
    if versions:
      item["url"] = __get_video_version(versions)
      item["type"] = "video"
    else:
      logging.log("No video versions found for {}, skipping item!".format(item["title"]))
      continue
    item["thumbnail"] = helper.prepareThumb(video.get("thumbnail", ""), baseUrl=BASE_URL)
    info = {}
    info["title"] = item["title"]
    info["plot"] = video.get("description", "")
    info["aired"] = video.get("broadcastDate", "")
    info["duration"] = video.get("materialLength", 0)
    try:
      info["fanart"] = helper.prepareFanart(video["poster"], baseUrl=BASE_URL)
    except KeyError:
      pass
    item["info"] = info
    if not item["thumbnail"] and info["fanart"]:
      item["thumbnail"] = info["fanart"]
    if video.get("broadcastedNow", False):
      item["title"] = item["title"] + " [COLOR red](Live)[/COLOR]"
    returned_items.append(item)
  return (returned_items, total_pages > current_page)

def __get_title_for_slug(slug):
  url = "title?slug="+slug
  json_data = __get_json(url)
  if json_data is None:
    return None
  else:
    return json_data

def __get_video_id_for_episode_id(episode_id):
  url = "episode?id=" + episode_id
  json_data = __get_json(url)
  if json_data is None:
    return None
  versions = json_data["versions"]
  return __get_video_version(versions)

def __get_video_version(versions):
  if len(versions) > 0:
    # This logic is mimicking the web player logic
    # 1. Try to get a version matching the accessibility service (AS)
    # 1.1 Since this plugin does not support AS it will look for "none"
    # 2. If no version matching AS is found, fallback to use the first stream
    for version in versions:
      # ungraceful access so we detect API changes
      if version["accessService"] == WANTED_AS:
        return version["id"]
    return versions[0]["id"]
  return None

def __get_video_json_for_video_id(video_id):
  url = VIDEO_API_URL + str(video_id)
  logging.log("Getting video JSON for {}".format(url))
  response = requests.get(url)
  if response.status_code != 200:
    logging.error("Could not fetch video data for {}".format(url))
    return None
  return response.json()

def __get_json(api_action):
  """
  Returns the JSON for 'api_action'.
  BASE_URL + API_URL is assumed to be the prefix of 'api_action'.
  If the server responds with status code != 200
  the function returns None.
  """
  url = BASE_URL+API_URL+api_action
  return __do_api_request(url)

def __get_svt_json(api_action):
  """
  Calls the SVT api endpoint instead of the SVTPlay
  endpoint.
  """
  url = SVT_BASE_URL + api_action
  return __do_api_request(url)

def __do_api_request(url):
  """
  Performs an API request. Returns None if
  HTTP response code is != 200.
  """
  logging.log("Requesting {}".format(url))
  response = requests.get(url)
  if response.status_code != 200:
    logging.error("Failed to reach {url}, response code {code}".format(url=url, code=response.status_code))
    return None
  else:
    return response.json()
