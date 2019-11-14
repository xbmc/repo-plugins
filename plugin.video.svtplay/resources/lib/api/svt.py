# -*- coding: utf-8 -*-
# system imports
from __future__ import absolute_import,unicode_literals
import re
import requests
import time
# own imports
from resources.lib import logging
from resources.lib import helper

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

PLAY_BASE_URL = "https://www.svtplay.se"
PLAY_API_URL = PLAY_BASE_URL+"/api/"
SVT_API_BASE_URL = "https://api.svt.se/"
VIDEO_API_URL= SVT_API_BASE_URL+"videoplayer-api/video/"

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
      "thumbnail" : helper.get_thumb_url(thumbnail, baseUrl=PLAY_BASE_URL),
      "url" : url,
      "info" : { 
        "duration" : item.get("materialLength", 0), 
        "fanart" : helper.get_fanart_url(item.get("poster", ""), baseUrl=PLAY_BASE_URL)
      },
      "onlyAvailableInSweden": item.get("onlyAvailableInSweden", False),
      "inappropriateForChildren": item.get("inappropriateForChildren", False),
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
  for json_item in json_data:
    versions = json_item.get("versions", [])
    content_type = "video"
    if versions:
      url = __get_video_version(versions)
    else:
      url = json_item["contentUrl"]
      content_type = "program"
    title = json_item["programTitle"]
    plot = json_item.get("description", "")
    thumbnail = helper.get_thumb_url(json_item.get("thumbnail", ""), PLAY_BASE_URL)
    if not thumbnail:
      thumbnail = helper.get_thumb_url(json_item.get("poster", ""), PLAY_BASE_URL)
    info = {"plot": plot, "thumbnail": thumbnail, "fanart": thumbnail}
    programs.append({
      "title": title,
      "url": url,
      "thumbnail": thumbnail,
      "info": info,
      "type" : content_type,
      "onlyAvailableInSweden" : json_item["onlyAvailableInSweden"],
      "inappropriateForChildren" : json_item.get("inappropriateForChildren", False)
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
      item["thumbnail"] = helper.get_thumb_url(result.get("thumbnail", ""), baseUrl=PLAY_BASE_URL)
    elif result_type == "SERIES_OR_TV_SHOW":
      item["title"] = unescape(result["programTitle"] + " - " + result["title"])
      item["thumbnail"] = helper.get_thumb_url(result.get("poster", ""), baseUrl=PLAY_BASE_URL)
      item["info"] = {}
      item["info"]["plot"] = result.get("description", "")
    else:
      # MOVIE and folder
      item["title"] = unescape(result["programTitle"])
      item["thumbnail"] = helper.get_thumb_url(result.get("poster", ""), baseUrl=PLAY_BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = result.get("description", "")
    item["onlyAvailableInSweden"] = result.get("onlyAvailableInSweden", False)
    item["inappropriateForChildren"] = result.get("inappropriateForChildren", False)
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
    item["onlyAvailableInSweden"] = True # Channels are always geo restricted
    item["inappropriateForChildren"] = True # No way to guarantee otherwise
    items.append(item)

  return items

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
    clip["thumbnail"] = helper.get_thumb_url(item.get("thumbnail", ""), PLAY_BASE_URL)
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

def getSvtVideoJson(svt_id):
  return __get_svt_json("/video/{}".format(svt_id))

def getItems(section_name, page):
  if not page:
    page = 1
  json_data = __get_json(section_name+"?page="+str(page)+"&excludedTagsString=lokalt")
  if json_data is None:
    return None
  current_page = json_data["currentPage"]
  total_pages = json_data["totalPages"]
  returned_items = []
  for json_item in json_data["data"]:
    versions = json_item.get("versions", [])
    if not versions:
      logging.log("No video versions found for {}, skipping item!".format(item["title"]))
      continue
    url = __get_video_version(versions)
    item = __create_item_from_json(json_item)
    item["url"] = url
    item["type"] = "video"
    returned_items.append(item)
  return (returned_items, total_pages > current_page)

def __create_item_from_json(json_item):
  item = {}
  item["title"] = json_item["programTitle"]
  try:
    item["title"] = "{title} [COLOR gray](S{season}E{episode})[/COLOR]".format(title=item["title"], season=str(json_item["season"]), episode=str(json_item["episodeNumber"]))
  except KeyError:
    # Suppress
    pass
  item["thumbnail"] = helper.get_thumb_url(json_item.get("thumbnail", ""), baseUrl=PLAY_BASE_URL)
  info = {}
  info["title"] = item["title"]
  info["poster"] = helper.get_fanart_url(json_item.get("poster", ""), PLAY_BASE_URL)
  info["plot"] = json_item.get("description", "")
  info["duration"] = json_item.get("materialLength", 0)
  info["tagline"] = json_item.get("shortDescription", "")
  info["season"] = json_item.get("season", "")
  info["episode"] = json_item.get("episodeNumber", "")
  info["dateadded"] = json_item.get("validFrom","2009-04-05 23:16:04")[:19]
  info["playcount"] = 0
  item["onlyAvailableInSweden"] = json_item.get("onlyAvailableInSweden", False)
  item["inappropriateForChildren"] = json_item.get("inappropriateForChildren", False)
  try:
    info["fanart"] = helper.get_fanart_url(json_item["poster"], baseUrl=PLAY_BASE_URL)
  except KeyError:
    pass
  item["info"] = info
  if not item["thumbnail"] and info["fanart"]:
    item["thumbnail"] = info["fanart"]
  if json_item.get("broadcastedNow", False):
    item["title"] = item["title"] + " [COLOR red](Live)[/COLOR]"
  return item

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
      if version["accessService"] == "none":
        return version["contentUrl"]
    return versions[0]["contentUrl"]
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
  PLAY_API_URL is assumed to be the prefix of 'api_action'.
  Return None if the server responds with status code != 200.
  """
  url = PLAY_API_URL+api_action
  return __do_api_request(url)

def __get_svt_json(api_action):
  """
  Calls the SVT api endpoint instead of the SVTPlay
  endpoint.
  """
  url = SVT_API_BASE_URL + api_action
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
