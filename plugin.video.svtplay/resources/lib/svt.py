# -*- coding: utf-8 -*-
import urllib
import requests

import helper
import CommonFunctions as common

BASE_URL = "http://svtplay.se"
API_URL = "/api/"
JSON_URL = "/ajax/sok/forslag.json"

URL_A_TO_O = "/program"
URL_TO_SEARCH = "/sok?q="
URL_TO_OA = "/kategorier/oppetarkiv"
URL_TO_CHANNELS = "/kanaler"
URL_TO_NEWS = "/nyheter"

JSON_SUFFIX = "?output=json"

SECTION_POPULAR = "popular-videos"
SECTION_LATEST_VIDEOS = "latest-videos"
SECTION_LAST_CHANCE = "last-chance-videos"
SECTION_LATEST_CLIPS = "play_js-tabpanel-more-clips"
SECTION_EPISODES = "play_js-tabpanel-more-episodes"
SECTION_LIVE_PROGRAMS = "live-channels"

def getAtoO():
  """
  Returns a list of all programs, sorted A-Z.
  """
  r = requests.get(BASE_URL+JSON_URL)
  if r.status_code != 200:
    common.log("Could not fetch forslag JSON!")
    return None
  
  items = []
  programs = []
  for json_item in r.json():
    if json_item["isGenre"] != "genre":
      programs.append(json_item)

  programs = sorted(programs, key=lambda program: program["title"])

  for program in programs:
    item = {}
    item["title"] = common.replaceHTMLCodes(program["title"])
    item["thumbnail"] = helper.prepareThumb(program.get("thumbnail", ""), baseUrl=BASE_URL)
    item["url"] = program["url"].replace("/senaste","")
    items.append(item)

  return items

def getCategories():
  """
  Returns a list of all categories.
  """
  r = requests.get(BASE_URL+API_URL+"programs_page")
  if r.status_code != 200:
    common.log("Could not fetch JSON!")
    return None

  categories = []

  for item in r.json()["categories"]:
    category = {}
    category["url"] = item["url"]

    if category["url"].endswith("oppetarkiv") or category["url"].endswith("barn"):
      # Skip the "Oppetarkiv" and "Barn" category
      continue

    if not category["url"].startswith("genre"):
      category["url"] = "genre/" + category["url"]

    category["title"] = item["name"]
    category["thumbnail"] = item.get("posterImageUrl", "")
    categories.append(category)

  return categories

def getLatestNews():
  """
  Returns a list of latest news programs.
  """
  url = BASE_URL+API_URL+"cluster_latest;cluster=nyheter"
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get JSON for url: "+url)
    return None

  programs = []
  for item in r.json()["data"]:
    item = item["attributes"]
    live_str = ""
    thumbnail = ""
    if item["images"]["thumbnail"]:
      thumbnail = item["images"]["thumbnail"]["attributes"]["alternates"]["small"]["href"]
    if item["images"]["poster"]:
      thumbnail = item["images"]["poster"]["attributes"]["alternates"]["small"]["href"]
    if item["live"]["liveNow"]:
      live_str = " " + "[COLOR red](Live)[/COLOR]"
    program = {
        "title" : common.replaceHTMLCodes(item["officialProgramTitle"] + " " + item["legacyEpisodeTitle"] + live_str),
        "thumbnail" : helper.prepareThumb(thumbnail, baseUrl=BASE_URL),
        "url" : "video/" + str(item["articleId"])
        }
    programs.append(program)
  return programs

def getProgramsForCategory(url):
  """
  Returns a list of programs for a specific category.
  """
  if url.startswith("genre/"):
    return getProgramsForGenre(url.split("/")[1])
  else:
    return None

def getProgramsForGenre(genre):
  url = BASE_URL+API_URL+"cluster_page;cluster="+genre
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get JSON for url: "+url)
    return None

  programs = []
  for item in r.json()["contents"]:
    url = item["contentUrl"]
    title = item["title"]
    plot = item.get("description", "")
    info = {"plot": plot}
    thumbnail = helper.prepareThumb(item.get("thumbnail", ""), BASE_URL)
    program = { "title": title, "url": url, "thumbnail": thumbnail, "info": info}
    programs.append(program)
  return programs

def getAlphas():
  """
  Returns a list of all letters in the alphabet that has programs.
  """
  url = BASE_URL+API_URL+"programs_page"
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get JSON for url: "+url)
    return None

  alphas = []
  for letter in r.json()["letters"]:
    alpha = {}
    alpha["title"] = common.replaceHTMLCodes(letter).encode("utf-8")
    alpha["char"] =  letter.encode("utf-8")
    alphas.append(alpha)

  return sorted(alphas, key=lambda letter: letter["char"])

def getProgramsByLetter(letter):
  """
  Returns a list of all program starting with the supplied letter.
  """
  letter = urllib.unquote(letter)
  url = BASE_URL+API_URL+"programs_page"
 
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Did not get any response for: "+url)
    return None

  contents = r.json()
  items = []
  
  programs = []
  try:
    programs = contents["letters"][letter]
  except KeyError:
    common.log("Could not find letter \""+letter+"\"")
    return None

  for program in programs:
    item = {}
    item["url"] = "/"+program["urlFriendlyTitle"]
    item["title"] = common.replaceHTMLCodes(program["title"])
    item["thumbnail"] = helper.prepareThumb(program.get("thumbnail", ""), baseUrl=BASE_URL)
    items.append(item)

  return items


def getSearchResults(search_term):
  """
  Returns a list of both clips and programs
  for the supplied search URL.
  """
  url = BASE_URL+API_URL+"search_page;q="+search_term
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Did not get any response for: "+url)
    return None

  items = []
  contents = r.json()

  for program in contents["titles"]["videoItems"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(program["title"])
    item["url"] = program["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(program.get("thumbnail", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = program.get("description", "")
    items.append({"item": item, "type" : "program"})

  for video in contents["episodes"]["videoItems"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(video["title"])
    item["url"] = video["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(video.get("thumbnail", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = video.get("description", "")
    items.append({"item": item, "type": "video"})

  for clip in contents["clips"]["videoItems"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(clip["title"])
    item["url"] = clip["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(clip.get("thumbnail", ""), baseUrl=BASE_URL)
    item["info"] = {}
    item["info"]["plot"] = clip.get("description", "")
    items.append({"item": item, "type": "video"})

  return items

def getChannels():
  """
  Returns the live channels from the page "Kanaler".
  """
  url = BASE_URL+API_URL+"channel_page"
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get response for: "+url)
    return None
  contents = r.json()

  items = []

  for channel in contents["channels"]:
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
    except KeyError as e:
      # Some items are missing titlePage, skip them
      pass
    for videoRef in channel["videoReferences"]:
      if videoRef["playerType"] == "ios":
        item["url"] = videoRef["url"]
    items.append(item)

  return items

def getEpisodes(title):
  """
  Returns the episodes for a program URL.
  """
  url = BASE_URL+API_URL+"video_title_page;title="+title
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get JSON for "+url)
    return None
  programs = []
  for item in r.json()["relatedVideos"]["episodes"]:
    program = {}
    program["title"] = item["title"]
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
  url = BASE_URL+API_URL+"video_title_page;title="+title
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get JSON for "+url)
    return None
  clips = []
  for item in r.json()["relatedVideos"]["clipsResult"]["entries"]:
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
  url = BASE_URL + API_URL + "title_page;title=" + video_url
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Failed to get JSON for "+url)
    return None
  return r.json()

def getItems(section_name, page):
  if not page:
    page = 1
  url = BASE_URL+API_URL+section_name+"_page?page="+str(page)
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Did not get any response for: "+url)
    return None

  returned_items = []
  contents = r.json()
  for video in contents["videos"]:
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

  return (returned_items, contents["hasNextPage"])

def getPage(url):
  """
  Wrapper, calls helper.getPage with SVT's base URL
  """
  return helper.getPage(BASE_URL + url)
