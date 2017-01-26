# -*- coding: utf-8 -*-
import urllib
import re
import requests

import helper
import CommonFunctions as common

BASE_URL = "http://svtplay.se"
API_URL = "/api/"

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
    thumbnail = item.get("poster", "")
    if not thumbnail:
      thumbnail = item.get("thumbnail", "")
    if item["broadcastedNow"]:
      live_str = " " + "[COLOR red](Live)[/COLOR]"
    program = {
        "title" : common.replaceHTMLCodes(item["programTitle"] + " " + (item["title"] or "") + live_str),
        "thumbnail" : helper.prepareThumb(thumbnail, baseUrl=BASE_URL),
        "url" : "video/" + str(item["versions"][0]["articleId"])
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
    url = item["contentUrl"]
    title = item["programTitle"]
    plot = item.get("description", "")
    thumbnail = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    if not thumbnail:
      thumbnail = helper.prepareThumb(item.get("poster", ""), BASE_URL)
    info = {"plot": plot, "thumbnail": thumbnail, "fanart": thumbnail}
    programs.append({"title": title, "url": url, "thumbnail": thumbnail, "info": info})
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
      item["url"] = "/" + title["contentUrl"]
      item["title"] = common.replaceHTMLCodes(title["programTitle"])
      item["thumbnail"] = ""
      items.append(item)

  return items


def getSearchResults(search_term):
  """
  Returns a list of both clips and programs
  for the supplied search URL.
  """
  json_data = __get_json("search_page;q="+search_term)
  if json_data is None:
    return None

  items = []

  for program in json_data["titles"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(program["title"])
    item["url"] = program["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(program.get("imageMedium", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = program.get("description", "")
    items.append({"item": item, "type" : "program"})

  for video in json_data["episodes"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(video["title"])
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
  json_data = __get_json("title_page;title="+title)
  if json_data is None:
    return None

  programs = []
  for item in json_data["relatedVideos"]["episodes"]:
    program = {}
    program["title"] = item["title"]
    try:
      program["title"] = program["title"] + "[COLOR green] (S%sE%s)[/COLOR]" % (str(item["season"]), str(item["episodeNumber"]))
    except KeyError:
      # Supress
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
  json_data = __get_json("title_page;title="+title)
  if json_data is None:
    return None

  clips = []
  for item in json_data["relatedVideos"]["clipsResult"]["entries"]:
    clip = {}
    clip["title"] = item["title"]
    clip["url"] = "klipp/" + str(item["id"])
    clip["thumbnail"] = helper.prepareThumb(item.get("thumbnailMedium", ""), BASE_URL)
    info = {}
    info["plot"] = item.get("description", "")
    clip["info"] = info
    clips.append(clip)
  return clips

def getVideoJSON(video_url):
  return __get_json("title_page;title=" + video_url)

def getItems(section_name, page):
  if not page:
    page = 1
  json_data = __get_json(section_name+"_page?page="+str(page))
  if json_data is None:
    return None

  returned_items = []
  for video in json_data["videos"]:
    item = {}
    item["title"] = video["programTitle"]
    item["url"] = video["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(video.get("thumbnail", ""), baseUrl=BASE_URL)
    info = {}
    info["title"] = item["title"]
    try:
      info["plot"] = video["description"]
    except KeyError:
      # Some videos do not have description (Rapport etc)
      info["plot"] = ""
    info["aired"] = video["broadcastDate"]
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
    returned_items.append(item)

  return (returned_items, json_data["paginationData"]["totalPages"] > json_data["paginationData"]["currentPage"])

def __get_json(api_action):
  """
  Returns the JSON for 'api_action'.
  BASE_URL + API_URL is assumed to be the prefix of 'api_action'.
  If the server responds with status code != 200
  the function returns None.
  """
  url = BASE_URL+API_URL+api_action
  response = requests.get(url)
  if response.status_code != 200:
    common.log("ERROR: Failed to get JSON for "+url)
    return None
  else:
    return response.json()
