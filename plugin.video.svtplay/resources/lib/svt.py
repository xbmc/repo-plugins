# -*- coding: utf-8 -*-
import urllib
import re
import requests

import helper
import CommonFunctions as common

BASE_URL = "http://svtplay.se"
API_URL = "/api/"
VIDEO_API_URL="http://api.svt.se/videoplayer-api/video/"

JSON_SUFFIX = "?output=json"

def getAtoO():
  """
  Returns a list of all items, sorted A-Z.
  """
  json_data = __get_json("all_titles_and_singles")
  if json_data is None:
    return None

  items = []

  for program in json_data:
    item = {}
    item["title"] = common.replaceHTMLCodes(program["programTitle"])
    item["thumbnail"] = ""
    item["url"] = program["contentUrl"]
    items.append(item)

  return sorted(items, key=lambda item: item["title"])

def getCategories():
  """
  Returns a list of all categories.
  """
  json_data = __get_json("active_clusters")
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
  json_data = __get_json("cluster_latest;cluster=nyheter")
  if json_data is None:
    return None

  programs = []
  for item in json_data:
    live_str = ""
    thumbnail = item.get("thumbnail", "")
    if item["broadcastedNow"]:
      live_str = " " + "[COLOR red](Live)[/COLOR]"
    program = {
        "title" : common.replaceHTMLCodes(item["programTitle"] + " " + (item["title"] or "") + live_str),
        "thumbnail" : helper.prepareThumb(thumbnail, baseUrl=BASE_URL),
        "url" : "video/" + item["id"],
        "info" : { "duration" : item.get("materialLength", 0), "fanart" : helper.prepareFanart(item.get("poster", ""), baseUrl=BASE_URL) }
        }
    programs.append(program)
  return programs

def getProgramsForGenre(genre):
  """
  Returns a list of all programs for a genre.
  """
  json_data = __get_json("cluster_titles_and_episodes/?cluster="+genre)
  if json_data is None:
    return None

  programs = []
  for item in json_data:
    if item.get("titleType", "") == "MOVIE":
      url = "video/" + item["id"]
      content_type = "video"
    else:
      url = item["contentUrl"]
      content_type = "program"
    title = item["programTitle"]
    plot = item.get("description", "")
    thumbnail = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    if not thumbnail:
      thumbnail = helper.prepareThumb(item.get("poster", ""), BASE_URL)
    info = {"plot": plot, "thumbnail": thumbnail, "fanart": thumbnail}
    programs.append({"title": title, "url": url, "thumbnail": thumbnail, "info": info, "type" : content_type})
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
  letter = urllib.unquote(letter)
  json_data = __get_json("all_titles_and_singles")
  if json_data is None:
    return None

  letter = letter.decode("utf-8")
  pattern = "[%s]" % letter.upper()

  items = []
  for title in json_data:
    if re.search(pattern, title["programTitle"][0].upper()):
      item = {}
      item["url"] = title["contentUrl"]
      item["title"] = common.replaceHTMLCodes(title["programTitle"])
      item["thumbnail"] = ""
      items.append(item)

  return items


def getSearchResults(search_term):
  """
  Returns a list of both clips and programs
  for the supplied search URL.
  """
  json_data = __get_json("search?q="+search_term)
  if json_data is None:
    return None

  items = []

  for program in json_data["titles"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(program["programTitle"])
    item["url"] = program["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(program.get("imageMedium", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = program.get("description", "")
    items.append({"item": item, "type" : "program"})

  for video in json_data["episodes"]:
    item = {}
    item["title"] = video["programTitle"] + " - " + common.replaceHTMLCodes(video["title"])
    item["url"] = video["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(video.get("imageMedium", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = video.get("description", "")
    items.append({"item": item, "type": "video"})

  for clip in json_data["clips"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(clip["title"])
    item["url"] = clip["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(clip.get("imageMedium", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = clip.get("description", "")
    items.append({"item": item, "type": "video"})

  return items

def getChannels():
  """
  Returns the live channels from the page "Kanaler".
  """
  json_data = __get_json("channel_page")
  if json_data is None:
    return None

  items = []
  for channel in json_data["channels"]:
    item = {}
    program_title = channel["schedule"][0]["title"]
    item["title"] = channel["name"]+" - "+program_title
    item["thumbnail"] = \
      "http://svtplay.se//public/images/channels/posters/%s.png" % channel["title"]
    item["info"] = {}
    try:
      item["info"]["plot"] = channel["schedule"][0]["titlePage"]["description"]
      item["info"]["fanart"] = channel["schedule"][0]["titlePage"]["thumbnailLarge"]
      item["info"]["title"] = channel["schedule"][0]["titlePage"]["title"]
    except KeyError:
      # Some items are missing titlePage, skip them
      pass
    for video_ref in channel["videoReferences"]:
      if video_ref["playerType"] == "ios":
        item["url"] = video_ref["url"]
    items.append(item)

  return items

def getEpisodes(title):
  """
  Returns the episodes for a program URL.
  """
  article_id = __get_article_id_for_title(title)
  if article_id is None:
    return None

  json_data = __get_json("title_episodes_by_article_id?articleId=%s" % (str(article_id)))
  if json_data is None:
    return None

  programs = []
  for item in json_data:
    program = {}
    program["title"] = item["title"]
    try:
      program["title"] = program["title"] + "[COLOR gray] (S%sE%s)[/COLOR]" % (str(item["season"]), str(item["episodeNumber"]))
    except KeyError:
      # Suppress
      pass
    program["url"] = "video/" + str(item["id"])
    program["thumbnail"] = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    info = {}
    info["plot"] = item.get("description", "")
    info["fanart"] = helper.prepareFanart(item.get("poster", ""), BASE_URL)
    program["info"] = info
    programs.append(program)
  return programs

def getClips(title):
  """
  Returns the clips for a program URL.
  """
  article_id = __get_article_id_for_title(title)
  if article_id is None:
    return None

  json_data = __get_json("title_clips_by_title_article_id?articleId=%s" % (str(article_id)))
  if json_data is None:
    return None

  clips = []
  for item in json_data:
    clip = {}
    clip["title"] = item["title"]
    clip["url"] = "klipp/" + str(item["id"])
    clip["thumbnail"] = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    info = {}
    info["title"] = clip["title"]
    info["plot"] = item.get("description", "")
    clip["info"] = info
    clips.append(clip)
  return clips

def getVideoJSON(video_url):
  video_id = ""
  if "video" in video_url:
    # ID should end with "A" for primary video source.
    # That is, not texted or sign interpreted.
    if not video_url.endswith("A"):
      video_url = video_url + "A"
    video_id = video_url.replace("video/", "")
  if "klipp" in video_url:
    video_id = video_url.replace("klipp/", "")
  return __get_video_json_for_video_id(video_id)

def getItems(section_name, page):
  if not page:
    page = 1
  json_data = __get_json(section_name+"?page="+str(page))
  if json_data is None:
    return None

  current_page = json_data["currentPage"]
  total_pages = json_data["totalPages"]

  returned_items = []
  for video in json_data["data"]:
    is_program = video.get("hasEpisodes", False)
    item = {}
    item["title"] = video["programTitle"]
    if is_program:
      item["url"] = video["contentUrl"]
      item["type"] = "program"
    else:
      item["url"] = video["id"]
      item["type"] = "video"
    item["thumbnail"] = helper.prepareThumb(video.get("thumbnail", ""), baseUrl=BASE_URL)
    info = {}
    info["title"] = item["title"]
    try:
      info["plot"] = video["description"]
    except KeyError:
      # Some videos do not have description (Rapport etc)
      info["plot"] = ""
    info["aired"] = video.get("broadcastDate", "")
    try:
      info["duration"] = video["materialLength"]
    except KeyError:
      # Some programs are missing duration, default to 0
      info["duration"] = 0
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

def __get_article_id_for_title(title):
  # Convert contentUrl to slug
  title = title.strip("/")
  url = "title?slug="+title
  json_data = __get_json(url)
  if json_data is None:
    return None
  else:
    return json_data["articleId"]

def __get_video_json_for_video_id(video_id):
  url = VIDEO_API_URL + str(video_id)
  common.log("Fetching video data for URL %s" % url)
  response = requests.get(url)
  if response.status_code != 200:
    common.log("ERROR: Could not fetch video data for URL %s" % url)
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
  # For debug purposes
  #common.log("Request for %s" % url)
  response = requests.get(url)
  if response.status_code != 200:
    common.log("ERROR: Failed to get JSON for "+url)
    return None
  else:
    return response.json()
