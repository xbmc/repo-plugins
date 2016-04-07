# -*- coding: utf-8 -*-
import urllib
import requests

import helper
import CommonFunctions as common

BASE_URL = "http://svtplay.se"
API_URL = "http://svtplay.se/api/"

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

SEARCH_LIST_TITLES = "[^\"']*playJs-search-titles[^\"']*"
SEARCH_LIST_EPISODES = "[^\"']*playJs-search-episodes[^\"']*"
SEARCH_LIST_CLIPS = "[^\"']*playJs-search-clips[^\"']*"

# Using Python magic to create shortcut
parseDOM = common.parseDOM 

def getAtoO():
  """
  Returns a list of all programs, sorted A-Z.
  """
  html = getPage(URL_A_TO_O)

  link_class = "[^\"']*play_link-list__link[^\"']*"
  texts = parseDOM(html, "a" , attrs = { "class": link_class })
  hrefs = parseDOM(html, "a" , attrs = { "class": link_class }, ret = "href")

  programs = []

  for index, text in enumerate(texts):
    program = {}
    if (hrefs[index][0:7] != u'/genre/'):
        program["title"] = common.replaceHTMLCodes(text)
        program["url"] = hrefs[index]
        programs.append(program)

  return programs


def getCategories():
  """
  Returns a list of all categories.
  """
  html = getPage(URL_A_TO_O)

  container = parseDOM(html,
                       "div",
                       attrs = { "class": "[^\"']*play_promotion-grid[^\"']*"})
  if not container:
    helper.errorMsg("Could not find container")
    return None

  titles = parseDOM(container,
                    "span",
                    attrs={"class": "[^\"']*play_promotion-item__caption_inner[^\"']*"})
  if not titles:
    helper.errorMsg("Could not find titles")
    return None

  thumbs = parseDOM(container,
                    "img",
                    attrs = { "class": "[^\"']*play_promotion-item__image[^\"']*" },
                    ret = "src")
  if not thumbs:
    helper.errorMsg("Could not find thumbnails")
    return None

  hrefs = parseDOM(container,
                   "a",
                    attrs={"class": "[^\"']*play_promotion-item__link[^\"']*"},
                    ret="href")
  if not hrefs:
    helper.errorMsg("Could not find hrefs")
    return None

  categories = []

  for index, title in enumerate(titles):
    category = {}
    category["url"] = hrefs[index]

    if category["url"].endswith("oppetarkiv"):
      # Skip the "Oppetarkiv" category
      continue
    elif category["url"].startswith("/genre"):
      # No support for /genre yet TODO: Add support
      continue

    # One ugly hack for the React generated HTML
    title = parseDOM(title, "span")[0]
    category["title"] = common.replaceHTMLCodes(title)
    category["thumbnail"] = helper.prepareThumb(thumbs[index], baseUrl=BASE_URL)
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
  Returns a list of programs for a specific category URL.
  """
  html = getPage(url)

  container = parseDOM(html, "div", attrs = { "id" : "[^\"']*playJs-alphabetic-list[^\"']*" })

  if not container:
    helper.errorMsg("Could not find container for URL "+url)
    return None

  articles = parseDOM(container, "article", attrs = { "class" : "[^\"']*play_videolist-element[^\"']*" })

  if not articles:
    helper.errorMsg("Could not find program links for URL "+url)
    return None

  programs = []
  for index, article in enumerate(articles):
    url = parseDOM(article, "a", ret="href")[0]
    title = parseDOM(article, "span", attrs= { "class" : "play_videolist-element__title-text" })[0]
    title = common.replaceHTMLCodes(title)
    thumbnail = parseDOM(article, "img", ret="src")[0]
    program = { "title": title, "url": url, "thumbnail": helper.prepareThumb(thumbnail, baseUrl=BASE_URL)}
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
  url = API_URL+"programs_page"
 
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
    item["thumbnail"] = helper.prepareThumb(program["thumbnailLarge"], baseUrl=BASE_URL)
    items.append(item)

  return items


def getSearchResults(search_term):
  """
  Returns a list of both clips and programs
  for the supplied search URL.
  """
  url = API_URL+"search_page;q="+search_term
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
    item["thumbnail"] = helper.prepareThumb(program["thumbnailLarge"], baseUrl=BASE_URL)
    item["info"] = {}
    try:
      item["info"]["plot"] = program["description"]
    except KeyError:
      item["info"]["plot"] = ""
    items.append({"item": item, "type" : "program"})

  for video in contents["episodes"]["videoItems"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(video["title"])
    item["url"] = video["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(video["thumbnailLarge"], baseUrl=BASE_URL)
    item["info"] = {}
    try:
      item["info"]["plot"] = video["description"]
    except KeyError:
      item["info"]["plot"] = ""
    items.append({"item": item, "type": "video"})

  for clip in contents["clips"]["videoItems"]:
    item = {}
    item["title"] = common.replaceHTMLCodes(clip["title"])
    item["url"] = clip["contentUrl"]
    item["thumbnail"] = helper.prepareThumb(clip["thumbnailLarge"], baseUrl=BASE_URL)
    item["info"] = {}
    try:
      item["info"]["plot"] = clip["description"]
    except KeyError:
      item["info"]["plot"] = ""
    items.append({"item": item, "type": "video"})

  return items

def getChannels():
  """
  Returns the live channels from the page "Kanaler".
  """
  url = API_URL+"channel_page"
  r = requests.get(url)
  if r.status_code != 200:
    common.log("Could not get response for: "+url)
    return None
  contents = r.json()

  items = []

  for channel in contents["channels"]:
    item = {}
    item["title"] = channel["name"]
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

def getEpisodes(url):
  """
  Returns the episodes for a program URL.
  """
  return getProgramItems(SECTION_EPISODES, url)

def getClips(url):
  """
  Returns the clips for a program URL.
  """
  return getProgramItems(SECTION_LATEST_CLIPS, url)

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
  url = API_URL+section_name+"_page"+";sida="+str(page)
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
    item["thumbnail"] = helper.prepareThumb(video["thumbnailLarge"], baseUrl=BASE_URL)
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
      info["fanart"] = helper.prepareFanart(video["posterXL"], baseUrl=BASE_URL)
    except KeyError:
      # Some programs do not have posters
      info["fanart"] = ""
    item["info"] = info
    returned_items.append(item)

  return (returned_items, contents["hasNextPage"])

def getPage(url):
  """
  Wrapper, calls helper.getPage with SVT's base URL
  """
  return helper.getPage(BASE_URL + url)
