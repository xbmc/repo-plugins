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

# Using Python magic to create shortcut
parseDOM = common.parseDOM 

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
  html = getPage("/nyheter")

  container = parseDOM(html, "section", attrs = { "class" : "[^\"']*play_category__latest-list[^\"']*" })
  if not container:
    helper.errorMsg("Could not find container!")
    return None

  articles = parseDOM(container, "article")
  if not articles:
    helper.errorMsg("Could not find articles!")
    return None

  titles = parseDOM(container, "article", ret = "data-title")
  airtimes = parseDOM(container, "article", ret = "data-broadcasted")
  durations = parseDOM(container, "article", ret = "data-length")
  urls = parseDOM(container, "a", attrs = { "class" : "[^\"']*play_js-videolist-element-link[^\"']*"}, ret = "href")
  thumbnails = parseDOM(container, "img", attrs = { "class" : "[^\"']*play_videolist-element__thumbnail-image[^\"']*"}, ret = "src")

  items = []
  for index, article in enumerate(articles):
     item = {
        "title" : common.replaceHTMLCodes(titles[index]),
        "thumbnail" : helper.prepareThumb(thumbnails[index], baseUrl=BASE_URL),
        "url" : urls[index]
        }
     items.append(item)

  return items

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
  html = getPage(URL_A_TO_O)
  container = parseDOM(html, "ul", attrs = { "class" : "[^\"']*play_alphabetic-skiplinks[^\"']*" })

  if not container:
    helper.errorMsg("No container found!")
    return None

  letters = parseDOM(container[0], "a", attrs = { "class" : "[^\"']*play_alphabetic-skiplinks__link[^\"']*" })

  if not letters:
    helper.errorMsg("Could not find any letters!")
    return None

  alphas = []

  for letter in letters:
    alpha = {}
    alpha["title"] = common.replaceHTMLCodes(letter).encode("utf-8")
    alpha["char"] =  letter.encode("utf-8")
    alphas.append(alpha)

  return alphas

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

def getProgramItems(section_name, url=None):
  """
  Returns a list of program items for a show.
  Program items have 'title', 'thumbnail', 'url' and 'info' keys.
  """
  if not url:
    url = "/"
  html = getPage(url + "?sida=2")

  video_list_class = "[^\"']*play_videolist[^\"']*"

  container = parseDOM(html, "div", attrs = { "id" : section_name })
  if not container:
    helper.errorMsg("No container found for section "+section_name+"!")
    return None
  container = container[0]

  item_class = "[^\"']*play_vertical-list__item[^\"']*"
  items = parseDOM(container, "li", attrs = { "class" : item_class })
  if not items:
    helper.errorMsg("No items found in container \""+section_name+"\"")
    return None
  new_articles = []


  for index, item in enumerate(items):
    live_item = False
    if "play_live-countdown" in item:
      live_item = True
      helper.infoMsg("Skipping live item!")
      continue
    info = {}
    new_article = {}
    title = parseDOM(item, "a",
                            attrs = { "class" : "[^\"']*play_vertical-list__header-link[^\"']*" })[0]
    plot = parseDOM(item, "p",
                            attrs = { "class" : "[^\"']*play_vertical-list__description-text[^\"']*" })[0]
    new_article["url"] = parseDOM(item, "a",
                            attrs = { "class": "[^\"']*play_vertical-list__header-link[^\"']*" },
                            ret = "href")[0]
    thumbnail = parseDOM(item,
                                "img",
                                attrs = { "class": "[^\"']*play_vertical-list__image[^\"']*" },
                                ret = "src")[0]
    new_article["thumbnail"] = helper.prepareThumb(thumbnail, baseUrl=BASE_URL)
    duration = parseDOM(item, "time", attrs = {}, )[0]
    aired = parseDOM(item, "p", attrs = { "class" : "[^\"']*play_vertical-list__meta-info[^\"']*" })
    if aired:
      aired = aired[0].replace("Publicerades ", "")
    else:
      # Some items do not contain this meta data
      aired = ""

    title = common.replaceHTMLCodes(title)
    plot = common.replaceHTMLCodes(plot)
    new_article["title"] = title
    info["title"] = title
    info["plot"] = plot
    info["aired"] = helper.convertDate(aired) 
    info["duration"] = helper.convertDuration(duration)
    info["fanart"] = helper.prepareFanart(thumbnail, baseUrl=BASE_URL)
    new_article["info"] = info
    new_articles.append(new_article)

  return new_articles

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
