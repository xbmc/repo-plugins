import CommonFunctions
import helper as helper

BESTOF_BASE_URL = "http://www.bestofsvt.se"
common = CommonFunctions
common.plugin = "SVT Play 3:bestofsvt"


def getCategories():
  """
  Returns all categories in the header menu
  """
  html = helper.getPage(BESTOF_BASE_URL)
  
  menu = common.parseDOM(html, "ul", attrs = { "class": "menu_1"})[0]

  lis = common.parseDOM(menu, "li")

  categories = []

  for li in lis:
    title = common.parseDOM(li, "a")[0]
    href = common.parseDOM(li, "a", ret = "href")[0]
    title = common.replaceHTMLCodes(title)
    categories.append({"title":title,"url":href})
  
  return categories

def getShows(url):
  """
  Returns all shows in a category
  """
  html = helper.getPage(BESTOF_BASE_URL + url)

  container = common.parseDOM(html, "div", attrs = {"class":"[^\"']*content_show_videos[^\"']*"})[0]

  boxes = common.parseDOM(container, "div", attrs = {"class":"show_box"})

  shows = []

  for box in boxes:
    href = common.parseDOM(box, "a", attrs = {"rel":"nofollow"}, ret = "href")[0]
    href = href.replace("http://www.svtplay.se/","")
    thumb = common.parseDOM(box, "img", ret = "src")[0]
    thumb = thumb.replace("/medium/", "/large/")
    title = common.parseDOM(box, "div", attrs = {"class":"image_info_1"})[0]
    shows.append({"title":title,"url":href,"thumbnail":thumb})

  return shows
