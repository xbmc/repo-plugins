# -*- coding: utf-8 -*-
import CommonFunctions
import re
import helper
import urllib

common = CommonFunctions

BASE_URL = "http://www.oppetarkiv.se"
SWF_URL = "http://www.oppetarkiv.se/public/swf/video/svtplayer-2013.05.swf"

BANDWIDTH = [300,500,900,1600,2500,5000]

URL_A_TO_O = "/kategori/titel"
URL_CATEGORIES = "/kategori/titel"
URL_TO_LATEST = "?tab=episodes&sida=1"
URL_TO_LATEST_NEWS = "?tab=news&sida=1"
URL_TO_RECOMMENDED = "?tab=recommended&sida=1"
URL_TO_SEARCH = "/sok?q="

JSON_SUFFIX = "?output=json"

CLASS_SHOW_MORE_BTN = "[^\"']*svtoa-button[^\"']*"
DATA_NAME_SHOW_MORE_BTN = "sida"

TAB_TITLES      = "titles"
TAB_EPISODES    = "episodes"
TAB_CLIPS       = "clips"
TAB_NEWS        = "news"
TAB_RECOMMENDED = "recommended"

  
def getAtoO():
  """
  Returns a list of all programs, sorted A-Z.
  """
  html = getPage(URL_A_TO_O)

  texts = common.parseDOM(html, "a" , attrs = { "class": "svt-text-default" })
  hrefs = common.parseDOM(html, "a" , attrs = { "class": "svt-text-default" }, ret = "href")
  
  programs = []

  for index, text in enumerate(texts):
    program = {}
    program["title"] = common.replaceHTMLCodes(text)
    program["url"] = hrefs[index]
    programs.append(program)

  return programs




def getProgramsByLetter(letter):
  """
  Returns a list of all program starting with the supplied letter.
  """
  letter = urllib.unquote(letter)

  html = getPage(URL_A_TO_O)

  letterboxes = common.parseDOM(html, "div", attrs = { "class": "[^\"']*playAlphabeticLetter[^\"']*" })

  for letterbox in letterboxes:

    heading = common.parseDOM(letterbox, "h3")[0]

    if heading == letter:
      break

  lis = common.parseDOM(letterbox, "li", attrs = { "class": "[^\"']*playListItem[^\"']*" })

  programs = []

  for li in lis:
    program = {}
    program["url"] = common.parseDOM(li, "a", ret = "href")[0]
    title = common.parseDOM(li, "a")[0]
    program["title"] = common.replaceHTMLCodes(title)
    programs.append(program)

  return programs


def getAjaxUrl(html,tabname):
  """
  Fetches the Ajax URL from a program page.
  """
  common.log("tabname: " + tabname)

  container = getPlayBox(html,tabname) 

  attrs = { "class": CLASS_SHOW_MORE_BTN, "data-name": DATA_NAME_SHOW_MORE_BTN}
  
  ajaxurl = common.parseDOM(container,
                              "a",
                              attrs = attrs,
                              ret = "data-baseurl")
  if len(ajaxurl) > 0:
    return common.replaceHTMLCodes(ajaxurl[0])
  else:
    return None



def getPlayBox(html,tabname):
  container = common.parseDOM(html,
                              "div",
                              attrs = { "class": "[^\"']*[playBoxBody|playBoxAltBody][^\"']*", "data-tabname": tabname })[0]
  return container


def getArticles(url,page,tabname=None):
  """
  Fetches all "article" DOM elements in a "svtGridBlock" or
  tab and returns a list of article 'objects'.  
  """
  if page:
    pageurl = url + "sida=" + page
  else:
    pageurl = url 
  
  common.log("pageurl: " , pageurl)
  html = getPage(pageurl)

  
  container = common.parseDOM(html,
                "div",
                attrs = { "class": "[^\"']*svtGridBlock[^\"']*" })[0]
  

  articles = common.parseDOM(container, "article")
  newarticles = []
 
  for index,article in enumerate(articles):
    info = {}
    newarticle = {}

    title = common.parseDOM(article,"h3")[0]
    title = common.parseDOM(title,"a")[0]
    newarticle["url"] = common.parseDOM(article, "a",
                            attrs = { "class": "[^\"']*[playLink|playAltLink][^\"']*" },
                            ret = "href")[0]
    thumbnail = common.parseDOM(article,
                                "img",
                                attrs = { "class": "oaImg" },
                                ret = "src")[0]
    newarticle["thumbnail"] = helper.prepareThumb(thumbnail)
    
    title = common.replaceHTMLCodes(title)
    newarticle["title"] = title
    info["title"] = title

    newarticle["info"] = info
    newarticles.append(newarticle)
 
  return newarticles


def getPage(url):
  """
  Wrapper, calls helper.getPage
  """
  common.log(url)
  if url.startswith("/http") or url.startswith("http"):
    return helper.getPage(url)
  else:
    return helper.getPage(BASE_URL + url)

def getHighBw(low):
  """
  Returns the higher bandwidth boundary
  """
  i = BANDWIDTH.index(low)
  return BANDWIDTH[i+1]
