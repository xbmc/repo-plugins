from string import *
import urllib, re

'''
    RaiClick for XBMC 1.1.0
    Copyright (C) 2005-2011 Angelo Conforti <angeloxx@angeloxx.it>
    http://www.angeloxx.it
    
    Lo script è un semplice browser del sito rai.tv, tutti i diritti
    sono di proprietà della RAI    
'''

urlBase = "http://www.rai.tv/%s"
urlBaseThemes = "http://www.rai.tv/dl/RaiTV/cerca_tematiche.html?%s"
urlListItems = "http://www.rai.tv/dl/RaiTV/programmi/liste/%s-V-%s.html"

''' 
  There are three level of contents:
  
  Themes (Musica,Spettacoli) -> listThemes\urlBaseThemes
    ThemeItems (Sanremo,XFactor) -> listThemeItems\urlBaseThemes?Theme
      ListItems (Extra,Sintesi Giornalierei) -> listSubItems\urlBase + ThemeItem
        VideoList (Videos) -> listItems\urlListItems + SubItem + ? + ?
'''


''' Return a list with <description> (and GET argument) of each theme '''
def listThemes():
  items = []
  data = urllib.urlopen(urlBaseThemes % ("Nope")).read()
  result = re.findall("<a title=\".*?\" href=\"\?(.*?)\">.*</a>", data)
  for item in result:
    items.append(item)
    
  return items
  
  
''' Return a list with <url> and <description> of each section '''
def listThemeItems(theme):
  items = []
  print("listThemeItems: Theme %s" % (theme))
  data = urllib.urlopen(urlBaseThemes % theme).read()
  
  ''' Remove newline char and simplify the regexp'''
  data = data.replace("\n","")
  result = re.findall("<a href=\"(\/dl.*?)\">.*?<div class=\"internal\">(.*?)</div>", data)
  for item in result:
    items.append(item)
  return items

''' Return a list with <list-url> and <description> of each sub-section '''
def listSubItems(startURL):
  items = []
  startURL = startURL.replace(".html","-page.html?LOAD_CONTENTS")
  print("listSubItems: startURL %s" % (startURL))
  data = urllib.urlopen(urlBase % startURL).read()
  result = re.findall("<a target=\"_top\" href=\"#\" id=\"(ContentSet.*?)\">(.*?)</a>", data)
  for item in result:
    items.append(item)
  return items
  
''' Return a list with <url> and <description> of each video '''
def listItems(startURL):
  items = []
  print("listItems: startURL %s" % (startURL))
  page = 0
  while(True):
    data = urllib.urlopen(urlListItems % (startURL,page)).read()
    if data.find("404 Not Found") > 0:
      print("listItems: startURL %s stopped at page %s" % (startURL,page))
      return items
      
    data = data.replace("\n","")
    result = re.findall("<a .*?href=\"(/dl/RaiTV/programmi/media/ContentItem.*?)\".*?><h2>(.*?)</h2>", data)
    for item in result:
      items.append(item)
    page += 1
  
def openMovie(url):
    print("openMovie: URL " + url)
    data = urllib.urlopen(url).read()
    result = re.findall("videoURL = \"(.*?)\"", data, re.DOTALL)
    return result[0]
