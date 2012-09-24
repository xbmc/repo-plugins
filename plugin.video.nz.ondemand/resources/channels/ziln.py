import urllib, re, sys
from BeautifulSoup import BeautifulSoup, SoupStrainer, BeautifulStoneSoup

import resources.tools as tools
import resources.config as config
settings = config.__settings__
from resources.tools import webpage

class ziln:
 def __init__(self):
  self.base = sys.argv[0]
  self.channel = "Ziln"
  self.urls = dict()
  self.urls['base'] = 'http://www.ziln.co.nz'
  self.urls["rtmp1"] = 'rtmp://flash1.e-cast.co.nz'
  self.urls["rtmp2"] = 'ecast'
  self.urls["rtmp3"] = 'mp4:/ziln'
  self.xbmcitems = tools.xbmcItems(self.channel)
  self.prefetch = False
  if settings.getSetting('%s_prefetch' % self.channel) == 'true':
   self.prefetch = True


 def index(self):
  item = tools.xbmcItem()
  info = item.info
  info["Title"] = config.__language__(30053)
  info["Count"] = 1
  info["FileName"] = "%s?ch=Ziln&folder=channels" % sys.argv[0]
  self.xbmcitems.items.append(item)
  item = tools.xbmcItem()
  info = item.info
  info["Title"] = config.__language__(30065)
  info["Count"] = 2
  info["Thumb"] = "DefaultVideoPlaylists.png"
  info["FileName"] = "%s?ch=Ziln&folder=search" % sys.argv[0]
  self.xbmcitems.items.append(item)
  self.xbmcitems.addall()

 def programmes(self, type, urlext):
  if type == "channel":
   folder = 1
   url = self.urls['base']
  elif type == "video":
   folder = 0
   url = "%s/assets/php/slider.php?channel=%s" % (self.urls['base'], urlext)
  elif type == "search":
   folder = 0
   url = "%s/search?search_keyword=%s" % (self.urls['base'], urlext.replace(" ", "+"))
  page = webpage(url)
  if page.doc:
   if type == "channel" or type == "search":
    div_tag = SoupStrainer('div')
    html_divtag = BeautifulSoup(page.doc, parseOnlyThese = div_tag)
    programmes = html_divtag.findAll(attrs={'class' : 'programmes'})
   elif type == "video":
    div_tag = SoupStrainer('body')
    html_divtag = BeautifulSoup(page.doc, parseOnlyThese = div_tag)
    programmes = html_divtag.findAll(attrs={'class' : 'slider slider-small'})
   if type == "search":
    type = "video"
   if len(programmes) > 0:
    for programme in programmes:
     list = programme.find('ul')
     if list:
      listitems = list.findAll('li')
      count = len(listitems)
      if count > 0:
       for listitem in listitems:
        link = listitem.find('a', attrs={'href' : re.compile("^/%s/" % type)})
        if link.img:
         if re.search("assets/images/%ss/" % type, link.img["src"]):
          #item = tools.xbmcItem()
          item = tools.xbmcItem()
          if listitem.p.string:
           item.info["Title"] = listitem.p.string.strip()
          else:
           item.info["Title"] = link.img["alt"]
          item.info["Thumb"] = "%s/%s" % (self.urls['base'], link.img["src"])
          index = re.search("assets/images/%ss/([0-9]*?)-mini.jpg" % type, link.img["src"]).group(1)
          item.info["FileName"] = "%s?ch=%s&%s=%s" % (self.base, self.channel, type, urllib.quote(index))
          if type == "video":
           if self.prefetch:
            item.info["FileName"] = self._geturl(index)
           else:
            item.playable = True
          self.xbmcitems.items.append(item)
          if self.prefetch:
           self.xbmcitems.add(count)
       if self.prefetch:
        self.xbmcitems.sort()
       else:
        self.xbmcitems.addall()
     else:
      sys.stderr.write("Search returned no results")
   else:
    sys.stderr.write("Couldn't find any programs")
  else:
   sys.stderr.write("Couldn't get page")

 def search(self):
  results = self.xbmcitems.search()
  if results:
   self.programmes("search", results)

 def play(self, index):
  self.xbmcitems.play(self._geturl(index))

 def _geturl(self, index):
  page = webpage("%s/playlist/null/%s" % (self.urls['base'], index))
  if page.doc:
   soup = BeautifulStoneSoup(page.doc)
   #return "%s%s" % (self.urls['base'], soup.find('media:content')["url"])
   return "%s%s" % (self.urls['base'], urllib.quote(soup.find('media:content')["url"]))