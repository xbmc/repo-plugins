import urllib, re, sys
from BeautifulSoup import BeautifulSoup, SoupStrainer, BeautifulStoneSoup

import resources.tools as tools
import resources.config as config
settings = config.__settings__
from resources.tools import webpage

class nzonscreen:
 def __init__(self):
  self.base = sys.argv[0]
  self.channel = "NZOnScreen"
  self.urls = dict()
  self.urls['base'] = 'http://www.nzonscreen.com'
  self.urls['json'] = '/html5/video_data/'
  self.xbmcitems = tools.xbmcItems(self.channel)
  self.prefetch = False
  if settings.getSetting('%s_prefetch' % self.channel) == 'true':
   self.prefetch = True

 def url(self, folder):
  u = self.urls
  return "/".join((u['base'], u['content'], folder, u['page']))

 def _xml(self, doc):
  try:
   document = minidom.parseString(doc)
  except:
   pass
  else:
   if document:
    return document.documentElement
  sys.stderr.write("No XML Data")
  return False

 def index(self, filter = "/explore/"):
  filterarray = filter.strip('/').split('/')
  filterlevel = len(filterarray)
  print filter
  print filter.strip('/')
  print str(filterlevel)
  url = self.urls['base'] + filter
  #sys.stderr.write("URL: " + url)
  #sys.stderr.write('explore_filter_%s' % str(filterlevel))
  page = webpage(url, 'chrome', 'nzos_html5=true')
  #page = webpage(self.urls['base'])
  if page.doc:
   #resources.tools.gethtmlpage("http://www.nzonscreen.com/html5/opt_in", "chrome", 1) # Get a cookie for this session to enable the HTML5 video tag
   div_tag = SoupStrainer('div')
   html_divtag = BeautifulSoup(page.doc, parseOnlyThese = div_tag)
   sections = html_divtag.find(attrs={'id' : 'explore_filter_%s' % str(filterlevel)})
   if not sections:
    sections = html_divtag.find(attrs={'id' : 'explore_listview'})
   if sections:
    links = sections.findAll('a')
    if len(links) > 0:
     for link in links:
 #     if link.string:
 #     sys.stderr.write(link.contents[0].string)
      item = tools.xbmcItem()
      info = item.info
      info["FileName"] = "%s?ch=%s&filter=%s" % (self.base, self.channel, urllib.quote(link["href"]))
      #info["Title"] = link.contents[0].string.strip()
      if link.string:
       info["Title"] = link.string.strip()
      else:
       filterarray = link["href"].split('/')
       info["Title"] = filterarray[len(filterarray) - 1].capitalize()
 #     info["Thumb"] =
      self.xbmcitems.items.append(item)
     if filterlevel == 1:
      item = tools.xbmcItem()
      info = item.info
      info["FileName"] = "%s?ch=%s&filter=search" % (self.base, self.channel)
      info["Title"] = "Search"
      self.xbmcitems.items.append(item)
    else:
 #    if filterarray[filterlevel] ==
     nav = html_divtag.find(attrs={'class' : 'nav_pagination'})
     if nav:
      pages = nav.findAll('a')
      if pages:
       for page in pages:
        if page.string:
         lastpage = page.string.strip()
         #url = page['href']
       for i in range(1, int(lastpage)):
        item = tools.xbmcItem()
        info = item.info
        info["FileName"] = "%s?ch=%s&filter=%s&page=%s" % (self.base, self.channel, urllib.quote(filter), str(i))
        info["Title"] = 'Page %s' % str(i)
        self.xbmcitems.items.append(item)
    self.xbmcitems.addall()
   else:
    sys.stderr.write("index: No sections")
  else:
   sys.stderr.write("index: No page.doc")

 def page(self, filter, page):
  url = "%s%s?page=%s" % (self.urls['base'], filter, page)
  page = webpage(url, 'chrome', 'nzos_html5=true')
  if page.doc:
   div_tag = SoupStrainer('div')
   html_divtag = BeautifulSoup(page.doc, parseOnlyThese = div_tag)
   results = html_divtag.find(attrs={'id' : 'filter_result_set'})
   if results:
    rows = results.findAll('tr')
    if len(rows) > 0:
     for row in rows:
      cells = row.findAll('td')
      count = len(cells)
      if count > 0:
       item = tools.xbmcItem()
       for cell in cells:
        if cell['class'] == 'image':
         item.info['Thumb'] = "%s%s" % (self.urls['base'], cell.div.div.a.img['src'])
         title = re.search("/title/(.*)", cell.a['href'])
         if not title:
          title = re.search("/interviews/(.*)", cell.a['href'])
        #elif cell['class'] == 'title_link title':
        elif cell['class'].startswith('title_link'):
         item.info['Title'] = item.unescape(cell.a.contents[0])
        #elif cell['class'] == 'year':
        # pass
        #elif cell['class'] == 'category':
        # pass
        #elif cell['class'] == 'director':
        # pass
        elif cell['class'] == 'added':
         item.info["Date"] = tools.xbmcdate(cell.contents[0], ".")
       if title:
        if self.prefetch:
         item.urls = self._videourls(title.group(1))
         item.units = "MB"
        else:
         item.info["FileName"] = "%s?ch=%s&title=%s&info=%s" % (self.base, self.channel, title.group(1), item.infoencode())
         item.playable = True
        self.xbmcitems.items.append(item)
        if self.prefetch:
         self.xbmcitems.add(count)
     if self.prefetch:
      self.xbmcitems.sort()
     else:
      self.xbmcitems.addall()
    else:
     sys.stderr.write("page: No rows")
   else:
    sys.stderr.write("page: No results")
  else:
   sys.stderr.write("page: No page.doc")

 def search(self):
  import xbmc
  keyboard = xbmc.Keyboard("", "Search for a Video")
  #keyboard.setHiddenInput(False)
  keyboard.doModal()
  if keyboard.isConfirmed():
   self.page("search", keyboard.getText())

 def play(self, title, encodedinfo):
  item = tools.xbmcItem()
  item.infodecode(encodedinfo)
  item.units = "MB"
  item.fanart = self.xbmcitems.fanart
  item.urls = self._geturls(title)
  self.xbmcitems.resolve(item, self.channel)

 def _geturls(self, title):
  url = "%s%s%s" % (self.urls['base'], self.urls['json'], title)
  page = webpage(url)
  if page.doc:
   import json
   videos = json.loads(page.doc)
   allurls = dict()
   returnurls = dict()
   filesizes = dict()
   for name, value in videos[0].iteritems():
    if name[-4:] == '_res':
     bitrate = name[:-4]
     allurls[bitrate] = list()
     filesizes[bitrate] = 0
   for video in videos:
    for bitrate, temp in allurls.iteritems():
     allurls[bitrate].append(video[bitrate + '_res'])
     filesizes[bitrate] = filesizes[bitrate] + video[bitrate + '_res_mb']
   for bitrate, urls in allurls.iteritems():
    returnurls[filesizes[bitrate]] = urls
   return returnurls
