# -*- coding: utf-8 -*-
import urllib

import helper
import CommonFunctions as common

BASE_URL = "http://svtplay.se"

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

  html = getPage(URL_A_TO_O)

  letterboxes = parseDOM(html, "div", attrs = { "class": "[^\"']*play_alphabetic-list__letter-container[^\"']*" })
  if not letterboxes:
    helper.errorMsg("No containers found for letter '%s'" % letter)
    return None

  letterbox = None

  for letterbox in letterboxes:

    heading = parseDOM(letterbox, "a", attrs = { "class": "[^\"']*play_alphabetic-list__letter[^\"']*"})[0]

    if heading.encode("utf-8") == letter:
      break

  lis = parseDOM(letterbox, "li", attrs = { "class": "[^\"']*play_alphabetic-list__item[^\"']*" })
  if not lis:
    helper.errorMsg("No items found for letter '"+letter+"'")
    return None

  programs = []

  for li in lis:
    program = {}
    program["url"] = parseDOM(li, "a", ret = "href")[0]
    title = parseDOM(li, "a")[0]
    program["title"] = common.replaceHTMLCodes(title)
    programs.append(program)

  return programs


def getSearchResults(url):
  """
  Returns a list of both clips and programs
  for the supplied search URL.
  """
  html = getPage(url)

  results = []

  for list_id in [SEARCH_LIST_TITLES, SEARCH_LIST_EPISODES, SEARCH_LIST_CLIPS]:
    items = getSearchResultsForList(html, list_id)
    if not items:
      helper.errorMsg("No items in list '"+list_id+"'")
      continue
    results.extend(items)

  return results


def getSearchResultsForList(html, list_id):
  """
  Returns the items in the supplied list.

  Lists are the containers on a program page that contains clips or programs.
  """
  container = parseDOM(html, "div", attrs = { "id" : list_id })
  if not container:
    helper.errorMsg("No container found for list ID '"+list_id+"'")
    return None

  articles = parseDOM(container, "article")
  if not articles:
    helper.errorMsg("No articles found for list ID '"+list_id+"'")
    return None

  titles = parseDOM(container, "article", ret = "data-title")

  results = []
  for index, article in enumerate(articles):
    thumbnail = parseDOM(article, "img", attrs = { "class" : "[^\"']*play_videolist-element__thumbnail-image[^\"']*" }, ret = "src")[0]
    url = parseDOM(article, "a", ret = "href")[0]
    title = common.replaceHTMLCodes(titles[index])
    thumbnail = helper.prepareThumb(thumbnail, baseUrl=BASE_URL)

    item_type = "video"
    if list_id == SEARCH_LIST_TITLES:
      item_type = "program"
    results.append({"item": { "title" : title, "thumbnail" : thumbnail, "url" : url  }, "type" : item_type })

  return results

def getChannels():
  """
  Returns the live channels from the page "Kanaler".
  """
  # Parsing this since React is way too complicated.
  # Results are hard coded instead
  channels = [
    {"title" : "SVT1", "url" : "/kanaler/svt1", "thumbnail" : ""},
    {"title" : "SVT2", "url" : "/kanaler/svt2", "thumbnail" : ""},
    {"title" : "Barnkanalen", "url" : "/kanaler/barnkanalen", "thumbnail" : ""},
    {"title" : "SVT24", "url" : "/kanaler/svt24", "thumbnail" : ""},
    {"title" : "Kunskapskanalen", "url" : "/kanaler/kunskapskanalen", "thumbnail" : ""},
  ]
  return channels

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

def getItems(section, page):
  """
  TODO Update py-doc!
  """
  if not section:
    print "Missing parameter section!"
    return None

  container = getPage("/"+section+"?embed=true"+"&sida="+str(page))

  article_class = "[^\"']*play_videolist-element[^\"']*"
  articles = parseDOM(container, "article", attrs = { "class" : article_class })
  titles = parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-title")
  plots = parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-description")
  airtimes = parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-broadcasted")
  if section == SECTION_LATEST_CLIPS:
    airtimes = parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-published")
  durations = parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-length")

  if not articles:
    helper.errorMsg("No articles found for section '"+section+"' !")
    return None
  
  # Check if "Nästa sida" exists, assume it is
  next_page_exists = True
  next_page_elem = parseDOM( container, 
                          "div",
                          attrs={ "class" : "[^\"']*play_gridpage__pagination[^\"']*"})
  if not next_page_elem:
    next_page_exists = False

  new_articles = []
  for index, article in enumerate(articles):
    info = {}
    new_article = {}
    plot = plots[index]
    aired = airtimes[index]
    duration = durations[index]
    title = titles[index]
    new_article["url"] = parseDOM(article, "a",
                            attrs = { "class": "[^\"']*play_videolist-element__link[^\"']*" },
                            ret = "href")[0]
    thumbnail = parseDOM(article,
                                "img",
                                attrs = { "class": "[^\"']*play_videolist-element__thumbnail-image[^\"']*" },
                                ret = "data-imagename")[0]
    new_article["thumbnail"] = helper.prepareThumb(thumbnail, baseUrl=None)
    if section == SECTION_LIVE_PROGRAMS:
      notlive = parseDOM(article,
                                "span",
                                attrs = {"class": "[^\"']*play_graphics-live[^\"']*is-inactive[^\"']*"})
      if notlive:
        new_article["live"] = False
      else:
        new_article["live"] = True
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

  return (new_articles, next_page_exists)

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


def getPage(url):
  """
  Wrapper, calls helper.getPage with SVT's base URL
  """
  return helper.getPage(BASE_URL + url)
