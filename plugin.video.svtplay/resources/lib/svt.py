# -*- coding: utf-8 -*-
import urllib

import helper
import CommonFunctions as common

BASE_URL = "http://svtplay.se"

URL_A_TO_O = "/program"
URL_TO_SEARCH = "/sok?q="
URL_TO_OA = "/kategorier/oppetarkiv"
URL_TO_CHANNELS = "/kanaler"

JSON_SUFFIX = "?output=json"

SECTION_POPULAR = "popular-videos"
SECTION_LATEST_VIDEOS = "latest-videos"
SECTION_LAST_CHANCE = "last-chance-videos"
SECTION_LATEST_CLIPS = "playJs-more-clips"
SECTION_EPISODES = "playJs-more-episodes"
SECTION_LIVE_PROGRAMS = "live-channels"

SEARCH_LIST_TITLES = "[^\"']*playJs-search-titles[^\"']*"
SEARCH_LIST_EPISODES = "[^\"']*playJs-search-episodes[^\"']*"
SEARCH_LIST_CLIPS = "[^\"']*playJs-search-clips[^\"']*"


def getAtoO():
  """
  Returns a list of all programs, sorted A-Z.
  """
  html = getPage(URL_A_TO_O)

  link_class = "[^\"']*play_alphabetic-link[^\"']*"
  texts = common.parseDOM(html, "a" , attrs = { "class": link_class })
  hrefs = common.parseDOM(html, "a" , attrs = { "class": link_class }, ret = "href")

  programs = []

  for index, text in enumerate(texts):
    program = {}
    program["title"] = common.replaceHTMLCodes(text)
    program["url"] = hrefs[index]
    programs.append(program)

  return programs


def getCategories():
  """
  Returns a list of all categories.
  """
  html = getPage("/")

  container = common.parseDOM(html, "div", attrs = { "id": "[^\"']*playJs-categories[^\"']*" })
  articles = common.parseDOM(container, "article")
  thumbs = common.parseDOM(container, "img", attrs = { "class": "[^\"']*play_videolist__thumbnail[^\"']*" }, ret = "src")
  categories = []

  for index, article in enumerate(articles):
    category = {}
    category["url"] = common.parseDOM(article, "a", ret = "href")[0]
    title = common.parseDOM(article, "h2")[0]

    if category["url"].endswith("oppetarkiv"):
      # Skip the "Oppetarkiv" category
      continue

    category["title"] = common.replaceHTMLCodes(title)
    category["thumbnail"] = BASE_URL + thumbs[index]
    categories.append(category)

  return categories


def getProgramsForCategory(url):
  """
  Returns a list of programs for a specific category URL.
  """
  html = getPage(url)

  container = common.parseDOM(html, "div", attrs = { "id" : "[^\"']*playJs-alphabetic-list[^\"']*" })

  if not container:
    common.log("Could not find container for URL "+url)
    return None

  articles = common.parseDOM(container, "article", attrs = { "class" : "[^\"']*play_videolist-element[^\"']*" })

  if not articles:
    common.log("Could not find program links for URL "+url)
    return None

  programs = []
  for index, article in enumerate(articles):
    url = common.parseDOM(article, "a", ret="href")[0]
    title = common.parseDOM(article, "span", attrs= { "class" : "play-link-sub" })[0]
    title = common.replaceHTMLCodes(title)
    thumbnail = common.parseDOM(article, "img", ret="src")[0]
    program = { "title": title, "url": url, "thumbnail": thumbnail}
    programs.append(program)

  return programs


def getAlphas():
  """
  Returns a list of all letters in the alphabet that has programs.
  """
  html = getPage(URL_A_TO_O)
  container = common.parseDOM(html, "ul", attrs = { "class" : "[^\"']*play_alphabetic-list-titles[^\"']*" })

  if not container:
    common.log("No container found!")
    return None

  letters = common.parseDOM(container[0], "h3", attrs = { "class" : "[^\"']*play_alphabetic-letter--title[^\"']*" })

  if not letters:
    common.log("Could not find any letters!")
    return None

  alphas = []

  for letter in letters:
    alpha = {}
    alpha["title"] = helper.convertChar(letter)
    alpha["char"] =  letter
    alphas.append(alpha)

  return alphas


def getProgramsByLetter(letter):
  """
  Returns a list of all program starting with the supplied letter.
  """
  letter = urllib.unquote(letter)

  html = getPage(URL_A_TO_O)

  letterboxes = common.parseDOM(html, "li", attrs = { "class": "[^\"']*play_alphabetic-letter[^\"']*" })
  if not letterboxes:
    common.log("No containers found for letter '%s'" % letter)
    return None

  letterbox = None

  for letterbox in letterboxes:

    heading = common.parseDOM(letterbox, "h3")[0]

    if heading == letter:
      break

  lis = common.parseDOM(letterbox, "li", attrs = { "class": "[^\"']*play_js-filterable-item[^\"']*" })
  if not lis:
    common.log("No items found for letter '"+letter+"'")
    return None

  programs = []

  for li in lis:
    program = {}
    program["url"] = common.parseDOM(li, "a", ret = "href")[0]
    title = common.parseDOM(li, "a")[0]
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
      common.log("No items in list '"+list_id+"'")
      continue
    results.extend(items)

  return results


def getSearchResultsForList(html, list_id):
  """
  Returns the items in the supplied list.

  Lists are the containers on a program page that contains clips or programs.
  """
  container = common.parseDOM(html, "div", attrs = { "id" : list_id })
  if not container:
    common.log("No container found for list ID '"+list_id+"'")
    return None

  articles = common.parseDOM(container, "article")
  if not articles:
    common.log("No articles found for list ID '"+list_id+"'")
    return None

  titles = common.parseDOM(container, "article", ret = "data-title")

  results = []
  for index, article in enumerate(articles):
    thumbnail = common.parseDOM(article, "img", attrs = { "class" : "[^\"']*play_videolist__thumbnail[^\"']*" }, ret = "src")[0]
    url = common.parseDOM(article, "a", ret = "href")[0]
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
  anchor_class = "[^\"']*play_zapper__menu__item-link[^\"']*"
  html = getPage(URL_TO_CHANNELS)

  container = common.parseDOM(html, "ul", attrs = { "data-tabarea" : "ta-schedule"})
  if not container:
    common.log("No container found for channels")
    return None

  channels = []
  ch_boxes = common.parseDOM(container, "li")
  for box in ch_boxes:
    title = common.parseDOM(box, "a", attrs = {"class" : anchor_class}, ret = "title")[0]
    url = common.parseDOM(box, "a", attrs = {"class" : anchor_class}, ret = "href")[0]
    plot = common.parseDOM(box, "span", attrs = {"class" : "[^\"']*play_zapper__menu__item-title[^\"']*"})[0]
    thumbnail = BASE_URL + common.parseDOM(box, "img", attrs = {"class" : "[^\"']*play_hide--gte-m[^\"']*"}, ret = "src")[0]
    channels.append({
      "title" : title,
      "url" : url,
      "thumbnail" : thumbnail,
      "info" : { "title" : plot, "plot" : plot}
    })

  return channels

def getPopular():
  """
  Returns the 'popular' items.
  """
  return getArticles(SECTION_POPULAR)

def getLatestVideos():
  """
  Returns the latest videos.
  """
  return getArticles(SECTION_LATEST_VIDEOS)

def getLastChance():
  """
  Returns the 'last chance' videos
  """
  return getArticles(SECTION_LAST_CHANCE)

def getLivePrograms():
  """
  Returns the 'live' channels (differs from 'channels')
  """
  return getArticles(SECTION_LIVE_PROGRAMS)

def getEpisodes(url):
  """
  Returns the episodes for a program URL.
  """
  return getArticles(SECTION_EPISODES, url)

def getClips(url):
  """
  Returns the clips for a program URL.
  """
  return getArticles(SECTION_LATEST_CLIPS, url)

def getArticles(section_name, url=None):
  """
  Returns a list of the articles in a section as program items.

  Program items have 'title', 'thumbnail', 'url' and 'info' keys.
  """
  if not url:
    url = "/"
  html = getPage(url)

  video_list_class = "[^\"']*play_videolist[^\"']*"

  container = common.parseDOM(html, "div", attrs = { "class" : video_list_class, "id" : section_name })
  if not container:
    common.log("No container found for section "+section_name+"!")
    return None
  container = container[0]

  article_class = "[^\"']*play_videolist-element[^\"']*"
  articles = common.parseDOM(container, "article", attrs = { "class" : article_class })
  titles = common.parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-title")
  plots = common.parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-description")
  airtimes = common.parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-broadcasted")
  if section_name == SECTION_LATEST_CLIPS:
    airtimes = common.parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-published")
  durations = common.parseDOM(container, "article", attrs = { "class" : article_class }, ret = "data-length")
  new_articles = []

  if not articles:
    common.log("No articles found for section '"+section_name+"' !")
    return None

  for index, article in enumerate(articles):
    info = {}
    new_article = {}
    plot = plots[index]
    aired = airtimes[index]
    duration = durations[index]
    title = titles[index]
    new_article["url"] = common.parseDOM(article, "a",
                            attrs = { "class": "[^\"']*play_videolist-element__link[^\"']*" },
                            ret = "href")[0]
    thumbnail = common.parseDOM(article,
                                "img",
                                attrs = { "class": "[^\"']*play_videolist__thumbnail[^\"']*" },
                                ret = "src")[0]
    new_article["thumbnail"] = helper.prepareThumb(thumbnail, baseUrl=BASE_URL)
    if section_name == SECTION_LIVE_PROGRAMS:
      notlive = common.parseDOM(article, "span", attrs = {"class": "[^\"']*play_graphics-live[^\"']*is-inactive[^\"']*"})
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

  return new_articles


def getPage(url):
  """
  Wrapper, calls helper.getPage with SVT's base URL
  """
  return helper.getPage(BASE_URL + url)
