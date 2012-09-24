# 3 News
# mms://content.mediaworks.co.nz/tv/News/TOPSTORIES.300k

import urllib, re, sys, time

from BeautifulSoup import BeautifulSoup, SoupStrainer

import resources.tools as tools
import resources.config as config
settings = config.__settings__
from resources.tools import webpage

class tv3:
 def __init__(self):
  self.base = sys.argv[0]
  self.channel = "TV3"
  self.urls = dict()
  self.urls['base'] = 'http://www.tv3.co.nz'
  self.urls['base1'] = 'http://ondemand'
  self.urls['base2'] = 'co.nz'
  self.urls['rtmp1'] = 'rtmpe://nzcontent.mediaworks.co.nz:80'
  self.urls['rtmp2'] = '_definst_/mp4:'
  self.urls['flash1'] = 'rtmpe://flashcontent.mediaworks.co.nz:80'
  self.urls['flash2'] = 'mp4:'
  self.urls['http1'] = 'http://flash.mediaworks.co.nz'
  self.urls['http2'] = 'streams/_definst_//'
  self.urls['video1'] = 'tabid'
  self.urls['video2'] = 'articleID'
  self.urls['video3'] = 'MCat'
  self.urls['video4'] = 'Default.aspx'
  self.urls['feedburner_re'] = '//feedproxy\.google\.com/'
  self.urls['cat'] = '/default404.aspx?tabid='
  self.urls['cat_re'] = '/default404\.aspx\?tabid='
  self.urls['img_re'] = '\.ondemand\.tv3\.co\.nz/ondemand/AM/'
  self.urls['img_re2'] = '\.ondemand\.tv3\.co\.nz/Portals/0-Articles/'
  self.xbmcitems = tools.xbmcItems(self.channel)
  self.prefetch = False
  if settings.getSetting('%s_prefetch' % self.channel) == 'true':
   self.prefetch = True

 def index(self, fake = True):
  if fake:
   self._indexfake()
  else:
   self._indexreal()
  self.xbmcitems.addall()


 def _indexfake(self): #Create a list of top level folders for the hierarchy view
  folders = list()
  folders.append(config.__language__(30052)) # "Categories"
  folders.append(config.__language__(30053)) # "Channels"
  folders.append(config.__language__(30054)) # "Genres"
  #folders.append(config.__language__(30055)) # "Shows"
  folders.append(config.__language__(30065)) # "Search"
  count = len(folders)
  for folder in folders:
   item = tools.xbmcItem()
   info = item.info
   info["Title"] = folder
   info["FileName"] = "%s?ch=TV3&folder=%s" % (self.base, folder)
   self.xbmcitems.items.append(item)

 def _indexreal(provider): #Create a list of top level folders as scraped from TV3's website
  page = webpage("%s/tabid/56/default.aspx" % (self._base_url(provider)))
  if page.doc:
   a_tag = SoupStrainer('a')
   html_atag = BeautifulSoup(page.doc, parseOnlyThese = a_tag)
   links = html_atag.findAll(attrs={"rel": "nofollow", "href": re.compile(self.urls["cat_re"])}) #, "title": True
   if len(links) > 0:
    for link in links:
     item = tools.xbmcItem()
     info = item.info
     info["Title"] = link.string
     caturl = link['href']
     cat = "tv"
     if info["Title"] in {"Title (A - Z)": "atoz", "TV3 Shows": "tv3", "FOUR Shows": "four"}:
      cat = cats[info["Title"]]
     catid = re.search('%s([0-9]+)' % (self.urls["cat_re"]), caturl).group(1)
     if catid:
      info["FileName"] = "%s?ch=TV3&cat=%s&catid=%s" % (self.base, cat, catid)
      self.xbmcitems.items.append(item)
   else:
    sys.stderr.write("Couldn't find any categories")
  else:
   sys.stderr.write("Couldn't get index webpage")

 def folderindex(self, folder): #Create second level folder for the hierarchy view, only showing items for the selected top level folder
  infopages = list()
  infopages.append(("63", config.__language__(30052), "tv3", config.__language__(30056))) # Latest
  infopages.append(("61", config.__language__(30052), "tv3", config.__language__(30057))) # Most Watched
  infopages.append(("64", config.__language__(30052), "tv3", config.__language__(30058))) # Expiring soon
  #infopages.append(("70", config.__language__(30052), "atoz", "A - Z")) # Now empty
  infopages.append(("71", config.__language__(30053), "tv3", "TV3"))
  infopages.append(("72", config.__language__(30053), "four", "FOUR"))
  infopages.append(("65", config.__language__(30054), "tv3", config.__language__(30059))) # Comedy
  infopages.append(("66", config.__language__(30054), "tv3", config.__language__(30060))) # Drama
  infopages.append(("67", config.__language__(30054), "tv3", config.__language__(30061))) # News/Current affairs
  infopages.append(("68", config.__language__(30054), "tv3", config.__language__(30062))) # Reality
  infopages.append(("82", config.__language__(30054), "tv3", config.__language__(30063))) # Sports
  infopages.append(("80", config.__language__(30052), "tv3", config.__language__(30064))) # All
  #infopages.append(("74", "RSS", "tv3", "RSS Feeds"))
  #infopages.append(("81", "Categories", "tv3", "FOUR Highlights"))
  #infopages.append(("73", "Categories", "tv3", "All (Small)"))
  for page in infopages:
   if page[1] == folder:
    item = tools.xbmcItem()
    info = item.info
    info["Title"] = page[3]
    info["FileName"] = "%s?ch=TV3&cat=%s&catid=%s" % (self.base, page[2], page[0])
    self.xbmcitems.items.append(item)
  if folder == "Shows":
   self.shows("tv3")
  elif folder == "Search":
   self.search()
  self.xbmcitems.addall()

 def showsindex(provider): #Create a second level list of TV Shows from a TV3 webpage
  #doc = resources.tools.gethtmlpage("%s/Shows/tabid/64/Default.aspx" % ("http://www.tv3.co.nz")) #Get our HTML page with a list of video categories
  #doc = resources.tools.gethtmlpage("%s/Shows.aspx" % ("http://www.tv3.co.nz")) #Get our HTML page with a list of video categories
  page = webpage("%s/Shows.aspx" % ("http://www.tv3.co.nz"))
  if page.doc:
   html_divtag = BeautifulSoup(page.doc)
   linksdiv = html_divtag.find('div', attrs = {"id": "pw_8171"})
   if linksdiv:
    links = linksdiv.findAll('a')
    if len(links) > 0:
     count = 0
     for link in links:
      item = tools.xbmcItem()
      info = item.info
      info["Title"] = link.string.strip()
      catid = link['href']
      if info["Title"] == "60 Minutes": #The URL on the next line has more videos
       info["FileName"] = "%s?ch=TV3&cat=%s&title=%s&catid=%s" % (self.base, "shows", urllib.quote(info["Title"]), urllib.quote(catid)) #"http://ondemand.tv3.co.nz/Default.aspx?TabId=80&cat=22"
      else:
       info["FileName"] = "%s?ch=TV3&cat=%s&title=%s&catid=%s" % (self.base, "shows", urllib.quote(info["Title"]), urllib.quote(catid))
      self.xbmcitems.items.append(item)
     self.xbmcitems.addall()
    else:
     sys.stderr.write("showsindex: Couldn't find any videos in list")
   else:
    sys.stderr.write("showsindex: Couldn't find video list")
  else:
   sys.stderr.write("showsindex: Couldn't get index webpage")


 def episodes(self, catid, provider): #Show video items from a normal TV3 webpage
  page = webpage("%s%s%s" % (self._base_url("tv3"), self.urls['cat'], catid))
  if page.doc:
   a_tag=SoupStrainer('div')
   html_atag = BeautifulSoup(page.doc, parseOnlyThese = a_tag)
   programs = html_atag.findAll(attrs={"class": "latestArticle "})
   if len(programs) > 0:
    for soup in programs:
     item = self._itemdiv(soup, provider)
     if item:
      self.xbmcitems.items.append(item)
      if len(item.urls) > 0:
       if self.prefetch:
        self.xbmcitems.add(len(programs))
    if self.prefetch:
     self.xbmcitems.sort()
    else:
     self.xbmcitems.addall()
   else:
    sys.stderr.write("episodes: Couldn't find any videos")
  else:
   sys.stderr.write("episodes: Couldn't get videos webpage")

 def show(self, catid, title, provider): #Show video items from a TV Show style TV3 webpage
  baseurl = ""
  if catid[:4] != "http":
   baseurl = self.urls["base"]
  geturl = "%s%s" % (baseurl, catid)
  page = webpage(geturl)
  if page.doc:
   div_tag = SoupStrainer('div')
   html_divtag = BeautifulSoup(page.doc, parseOnlyThese = div_tag)
   tables = html_divtag.find(attrs={"xmlns:msxsl": "urn:schemas-microsoft-com:xslt"})
   if tables:
    programs = tables.findAll('table')
    if len(programs) > 0:
     count = 0
     for soup in programs:
      self.xbmcitems.items.append(self._itemshow(soup, provider, title))
      count += 1
     self.xbmcitems.addall()
    else:
     programs = tables.findAll('tr')
     if len(programs) > 0:
      count = -1
      for soup in programs:
       count += 1
       if count > 0:
        self.xbmcitems.items.append(self._itemtable(soup, provider, title))
      self.xbmcitems.addall()
     else:
      sys.stderr.write("show: Couldn't find any videos in list")
   else:
    sys.stderr.write("show: Couldn't find video list")
  else:
   sys.stderr.write("show: Couldn't get index webpage")

 def atoz(self, catid, provider): #Show video items from an AtoZ style TV3 webpage
  page = webpage("%s%s%s" % (self._base_url("tv3"), self.urls["cat"], catid))
  if page.doc:
   a_tag=SoupStrainer('div')
   html_atag = BeautifulSoup(page.doc, parseOnlyThese = a_tag)
   programs = html_atag.findAll(attrs={"class": "wideArticles"})
   if len(programs) > 0:
    for soup in programs:
     item = self._itematoz(soup, provider)
     self.xbmcitems.items.append(item)
     if len(item.urls) > 0:
      if self.prefetch:
       self.xbmcitems.add()
    if self.prefetch:
     self.xbmcitems.sort()
    else:
     self.xbmcitems.addall()
   else:
    sys.stderr.write("atoz: Couldn't find any videos")
  else:
   sys.stderr.write("atoz: Couldn't get videos webpage")

 def search(self):
  results = self.xbmcitems.search()
  if results:
   self._search(results, "58")

 def _search(self, searchterm, catid): #Show video items from a normal TV3 webpage
  page = webpage("%s/search/tabid/%s/Default.aspx?amq=%s" % (self._base_url('tv3'), catid, searchterm.replace(" ", "+")))
  if page.doc:
   a_tag=SoupStrainer('div')
   html_atag = BeautifulSoup(page.doc, parseOnlyThese = a_tag)
   programs = html_atag.findAll(attrs={"class": "results"})
   if len(programs) > 0:
    for soup in programs:
     self.xbmcitems.items.append(self._itemsearch(soup, "tv3"))
     self.xbmcitems.items.append(self._itemsearch(soup, "four"))
    self.xbmcitems.addall()
   else:
    sys.stderr.write("_search: Couldn't find any videos")
  else:
   sys.stderr.write("_search: Couldn't get videos webpage")

 def _itemsearch(self, soup, provider): # Scrape items from a table-style HTML page
  baseurl = self._base_url(provider)
  item = tools.xbmcItem()
  info = item.info
  title = soup.find("div", attrs={"class": 'catTitle'})
  if title:
   info["TVShowTitle"] = title.a.string.strip()
   href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, self.urls["video1"], self.urls["video2"], self.urls["video3"]), title.a['href'])
   if href:
    image = soup.find("img")
    if image:
     info["Thumb"] = image['src']
    ep = soup.find("div", attrs={"class": 'epTitle'})
    if ep:
     if ep.a:
      info.update(self._seasonepisode(ep.a))
    date = soup.find("div", attrs={"class": 'epDate'})
  #  if date:
  #   sys.stderr.write(date.span[1].string.strip())
    item.titleplot()
    if self.prefetch:
     item.urls = self._geturls("%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider)
    else:
     item.playable = True
     info["FileName"] = "%s?ch=TV3&id=%s&provider=%s&info=%s" % (self.base, "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider, item.infoencode())
    return item
   else:
    sys.stderr.write("_itemsearch: No href")
  else:
   sys.stderr.write("_itemsearch: No title")

 def _itemdiv(self, soup, provider): #Scrape items from a div-style HTML page
  baseurl = self._base_url(provider)
  item = tools.xbmcItem()
  info = item.info
  #info["Studio"] = provider
  link = soup.find("a", attrs={"href": re.compile(baseurl)})
  if link:
   href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, self.urls["video1"], self.urls["video2"], self.urls["video3"]), link['href'])
   if href:
    if link.string:
     title = link.string.strip()
     if title != "" and title[0:7] != "rotator":
      info["TVShowTitle"] = title
      image = soup.find("img", attrs={"src": re.compile(self.urls["img_re"]), "title": True})
      if image:
       info["Thumb"] = image['src']
      se = soup.find("span", attrs={"class": "title"})
      if se:
       info.update(self._seasonepisode(se))
      date = soup.find("span", attrs={"class": "dateAdded"})
      if date:
       info.update(self._dateduration(date))
      item.titleplot()
      plot = soup.find("div", attrs={"class": "left"}).string
      if plot:
       if plot.strip() != "":
        info["Plot"] = item.unescape(plot.strip())
      if self.prefetch:
       item.urls = self._geturls("%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider)
      else:
       item.playable = True
       info["FileName"] = "%s?ch=TV3&id=%s&provider=%s&info=%s" % (self.base, "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider, item.infoencode())
      return item
     else:
      sys.stderr.write("_itemdiv: No title")
    else:
     sys.stderr.write("_itemdiv: No link.string")
   else:
    sys.stderr.write("_itemdiv: No href")
  else:
   sys.stderr.write("_itemdiv: No link")

 def _itemshow(self, soup, provider, title): #Scrape items from a show-style HTML page
  item = tools.xbmcItem()
  info = item.info
  bold = soup.find('b')
  if bold:
   link = bold.find("a", attrs={"href": re.compile(self.urls["feedburner_re"])})
   if link:
    urltype = "other"
   else:
    link = bold.find("a", attrs={"href": re.compile(self._base_url("tv3"))})
    if link:
     urltype = "tv3"
   if link:
    if link.string:
     plot = link.string.strip()
     if plot != "":
      info["PlotOutline"] = plot
      info["TVShowTitle"] = title
      image = soup.find("img", attrs={"src": re.compile(self.urls["img_re"])})
      if image:
       info["Thumb"] = image['src']
      info.update(self._seasonepisode(link))
      item.titleplot()
      if urltype == "tv3":
       href = re.search("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (self._base_url("tv3"), self.urls["video1"], self.urls["video2"], self.urls["video3"]), link['href'])
       if href:
        if self.prefetch:
         item.urls = self._geturls("%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider)
        else:
         item.playable = True
         info["FileName"] = "%s?ch=TV3&id=%s&provider=%s&info=%s" % (self.base, "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider, item.infoencode())
      elif urltype == "other":
       if self.prefetch:
        item.urls = self._geturls(link["href"], provider)
       else:
        item.playable = True
        info["FileName"] = "%s?ch=TV3&id=%s&provider=%s&info=%s" % (self.base, urllib.quote(link["href"]), provider, item.infoencode())
      return item
     else:
      sys.stderr.write("_itemshow: No plot")
    else:
     sys.stderr.write("_itemshow: No link.string")
   else:
    sys.stderr.write("_itemshow: No link")
  else:
   sys.stderr.write("_itemshow: No bold")

 def _itemtable(self, soup, provider, title): #Scrape items from a table-style HTML page
  item = tools.xbmcItem()
  info = item.info
  link = soup.find('a')
  if link:
   if link.string:
    plot = link.string.strip()
    if plot != "":
     info["PlotOutline"] = plot
     info["TVShowTitle"] = title
     info.update(self._seasonepisode(link))
     item.titleplot()
     href = re.search("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (self._base_url("tv3"), self.urls["video1"], self.urls["video2"], self.urls["video3"]), link['href'])
     if href:
      if self.prefetch:
       item.urls = self._geturls("%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider)
      else:
       item.playable = True
       info["FileName"] = "%s?ch=TV3&id=%s&provider=%s&info=%s" % (self.base, "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider, item.infoencode())
     return item
    else:
     sys.stderr.write("_itemtable: No plot")
   else:
    sys.stderr.write("_itemtable: No link.string")
  else:
   sys.stderr.write("_itemtable: No link")

 def _itematoz(self, soup, provider): #Scrape items from an AtoZ-style HTML page
  baseurl = self._base_url(provider)
  item = tools.xbmcItem()
  if soup.find('h5'):
   link = soup.h5.find("a", attrs={"href": re.compile(baseurl)})
   if link:
    infoitems = {}
    href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, self.urls["video1"], self.urls["video2"], self.urls["video3"]), link['href'])
    if href:
     if link.string:
      title = link.string.strip()
      if title != "":
       item.info["TVShowTitle"] = title
       image = soup.find("img", attrs={"src": re.compile(self.urls["IMG_RE2"]), "title": True})
       if image:
        item.info["Thumb"] = image['src']
       item.info.update(self._seasonepisode(soup.contents[4]))
       item.titleplot()
       plot = soup.find("span", attrs={"class": "lite"})
       if plot.string:
        cleanedplot = plot.string.strip()
        if cleanedplot:
         item.info["Plot"] = item.unescape(cleanedplot)
       if self.prefetch:
        item.urls = self._geturls("%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider)
       else:
        item.playable = True
        item.info["FileName"] = "%s?ch=%s&id=%s&provider=%s&info=%s" % (self.base, self.channel, "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), provider, item.infoencode())
       if "FileName" in item.info or len(item.urls) > 0:
        return item
      else:
       sys.stderr.write("_itematoz: No title")
     else:
      sys.stderr.write("_itematoz: No link.string")
    else:
     sys.stderr.write("_itematoz: No href")
   else:
    sys.stderr.write("_itematoz: No link")
  else:
   sys.stderr.write("_itematoz: No h5")

 def play(self, id, studio, encodedinfo):
  item = tools.xbmcItem()
  item.infodecode(encodedinfo)
  item.fanart = self.xbmcitems.fanart
  item.urls = self._geturls(id, studio)
  self.xbmcitems.resolve(item, self.channel)

 def _geturls(self, id, studio): #Scrape a page for a given OnDemand video and build an RTMP URL from the info in the page, then play the URL
  urls = dict()
  ids = id.split(",")
  if len(ids) == 4:
   pageUrl = "%s/%s/%s/%s/%s/%s/%s/%s/%s" % (self._base_url(studio), ids[0], self.urls["video1"], ids[1], self.urls["video2"], ids[2], self.urls["video3"], ids[3], self.urls["video4"])
   #sys.stderr.write(pageUrl)
   page = webpage(pageUrl)
  else:
   #doc = resources.tools.gethtmlpage("id")
   #sys.stderr.write(id)
   page = webpage(id) # Huh? - I guess this is feeding a full URL via the id variable
  if page.doc:
   #videoid = re.search('var video ="/\*transfer\*([0-9]+)\*([0-9A-Z]+)";', doc)
   #videoid = re.search('var video ="\*(.*?)\*([0-9]+)\*(.*?)";', page.doc)
   videoid = re.search('var video ="\*(.*?)\*([0-9A-Z\-]+)\*(.*?)";', page.doc)
   #videoid = re.search('var video ="\*(.*?)";', page.doc)
   if videoid:
    #videoplayer = re.search('var fo = new FlashObject\("(http://static.mediaworks.co.nz/(.*?).swf)', doc)
    videoplayer = re.search('swfobject.embedSWF\("(http://static.mediaworks.co.nz/(.*?).swf)', page.doc)
    if videoplayer:
     rnd = ""
     auth = re.search('random_num = "([0-9]+)";', page.doc)
     if auth:
      rnd = "?rnd=" + auth.group(1)
     swfverify = ' swfUrl=%s%s pageUrl=%s swfVfy=true' % (videoplayer.group(1), rnd, pageUrl)
     #swfverify = ' swfUrl=%s%s' % (videoplayer.group(1), rnd)
     realstudio = 'tv3'
     site = re.search("var pageloc='(TV-)?(.*?)-", page.doc)
     if site:
      #if site.group(2) == 'FOUR':
       #realstudio = 'four'
      realstudio = site.group(2).lower()
     playlist = list()
     qualities = [330]
     if re.search('flashvars.sevenHundred = "yes";', page.doc):
      qualities.append(700)
     if re.search('flashvars.fifteenHundred = "yes";', page.doc):
      qualities.append(1500)
     if not re.search('flashvars.highEnd = "true";', page.doc): # flashvars.highEnd = "true";//true removes 56K option
      qualities.append(56)
     geo = re.search('var geo= "(.*?)";', page.doc)
     if geo:
      if geo.group(1) == 'geo':
       for quality in qualities:
        urls[quality] = '%s/%s/%s%s/%s/%s_%sK' % (self.urls["rtmp1"], self._rtmpchannel(realstudio), self.urls["rtmp2"], videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality) + swfverify
      elif geo.group(1) == 'str':
       for quality in qualities:
        urls[quality] = '%s/%s/%s%s/%s/%s_%sK' % (self.urls["flash1"], self._rtmpchannel(realstudio), self.urls["flash2"], videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality) + swfverify
      elif geo.group(1) == 'no':
       for quality in qualities:
        urls[quality] = '%s/%s/%s%s/%s/%s_%s.%s' % (self.urls["http1"], "four", self.urls["http2"], videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality, "mp4")
    else:
     sys.stderr.write("_geturls: No page.doc")
   else:
    sys.stderr.write("_geturls: No videoid")
  else:
   sys.stderr.write("_geturls: No videoplayer")
  return urls

 def _seasonepisode(self, se): #Search a tag for season and episode numbers. If there's an episode and no season, assume that it's season 1
  if se:
   info = dict()
   info["PlotOutline"] = se.string.strip()
   season = re.search("(Cycle|Season) ([0-9]+)", se.string)
   seasonfound = 0
   if season:
    info["Season"] = int(season.group(2))
    seasonfound = 1
   episode = re.search("Ep(|isode) ([0-9]+)", se.string)
   if episode:
    info["Episode"] = int(episode.group(2))
    if not seasonfound:
     info["Season"] = 1
   return info

 def _dateduration(self, ad): #Search a tag for aired date and video duration
  if ad:
   info = dict()
   aired = re.search("([0-9]{2}/[0-9]{2}/[0-9]{2})", ad.contents[1])
   if aired:
    #info["Premiered"] = time.strftime("%Y-%m-%d", time.strptime(aired.group(1),"%d/%m/%y"))
    info["Premiered"] = tools.xbmcdate(aired.group(1))
    info["Date"] = info["Premiered"]
    #info["Year"] = int(time.strftime("%Y", info["Aired"]))
   duration = re.search("\(([0-9]+:[0-9]{2})\)", ad.contents[1])
   if duration:
    #info["Duration"] = duration.group(2)
    info["Duration"] = time.strftime("%M", time.strptime(duration.group(1), "%M:%S"))
   return info

 def _base_url(self, provider): #Build a base website URL for a given site (four or tv3)
  return "%s.%s.%s" % (self.urls['base1'], provider, self.urls['base2'])
  #return "%s.%s.%s" % (self.urls['base1'], 'tv3', self.urls['base2'])

 def _rtmpchannel(self, provider):
  if provider == "four":
   return "c4"
  return provider