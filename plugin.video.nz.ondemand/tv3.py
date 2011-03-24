# 3 News
# mms://content.mediaworks.co.nz/tv/News/TOPSTORIES.300k


import tools, urllib, string, re, sys, time, xbmcaddon
from BeautifulSoup import BeautifulSoup, SoupStrainer

addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])
localize = addon.getLocalizedString


# Setup a dictionary of useful URLs

tv3_urls = dict()
tv3_urls["TV3"] = 'http://www.tv3.co.nz'
tv3_urls["BASE1"] = 'http://ondemand'
tv3_urls["BASE2"] = 'co.nz'
tv3_urls["RTMP1"] = 'rtmpe://nzcontent.mediaworks.co.nz'
tv3_urls["RTMP2"] = '_definst_/mp4:'
tv3_urls["HTTP1"] = 'http://flash.mediaworks.co.nz'
tv3_urls["HTTP2"] = 'streams/_definst_//'
tv3_urls["VIDEO1"] = 'tabid'
tv3_urls["VIDEO2"] = 'articleID'
tv3_urls["VIDEO3"] = 'MCat'
tv3_urls["VIDEO4"] = 'Default.aspx'
tv3_urls["FEEDBURNER_RE"] = '//feedproxy\.google\.com/'
tv3_urls["CAT"] = '/default404.aspx?tabid='
tv3_urls["CAT_RE"] = '/default404\.aspx\?tabid='
tv3_urls["IMG_RE"] = '\.ondemand\.tv3\.co\.nz/Portals/0/AM/'
tv3_urls["IMG_RE2"] = '\.ondemand\.tv3\.co\.nz/Portals/0-Articles/'
tv3_urls["Fanart"] = 'resources/images/TV3.jpg'






def seasonepisode(se): #Search a tag for season and episode numbers. If there's an episode and no season, assume that it's season 1
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

def dateduration(ad): #Search a tag for aired date and video duration
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


def base_url(provider): #Build a base website URL for a given site (c4tv or tv3)
 #return "%s.%s.%s" % (tv3_urls["BASE1"], provider, tv3_urls["BASE2"])
 return "%s.%s.%s" % (tv3_urls["BASE1"], 'tv3', tv3_urls["BASE2"])

def rtmp(provider): #Build an RTMP URL for a given site (c4tv or tv3)
 if provider == "c4tv":
  return "%s/%s/%s" % (tv3_urls["RTMP1"], "c4", tv3_urls["RTMP2"])
 else:
  return "%s/%s/%s" % (tv3_urls["RTMP1"], provider, tv3_urls["RTMP2"])

def http(provider): #Build an RTMP URL for a given site (c4tv or tv3)
 if provider == "c4tv":
  return "%s/%s/%s" % (tv3_urls["HTTP1"], "c4", tv3_urls["HTTP2"])
 else:
  return "%s/%s/%s" % (tv3_urls["HTTP1"], provider, tv3_urls["HTTP2"])



#Create pages of folders (for categories, etc)

def INDEX_FOLDERS(): #Create a list of top level folders for the hierarchy view
 folders = dict()
 folders["0"] = localize(30052) # "Categories"
 folders["1"] = localize(30053) # "Channels"
 folders["2"] = localize(30054) # "Genres"
 #folders["3"] = localize(30055) # "Shows"
 folders["4"] = localize(30065) # "Search"
 count = len(folders)
 for index in folders:
  info = tools.defaultinfo(1)
  info["Title"] = folders[index]
  info["Count"] = int(index)
  info["FileName"] = "%s?ch=TV3&folder=%s" % (sys.argv[0], folders[index])
  tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 1, count)

def INDEX_FOLDER(folder): #Create second level folder for the hierarchy view, only showing items for the selected top level folder
 infopages = dict()
 infopages["0"]  = ("63", localize(30052), "tv3", localize(30056)) # Latest
 infopages["1"]  = ("61", localize(30052), "tv3", localize(30057)) # Most Watched
 infopages["2"]  = ("64", localize(30052), "tv3", localize(30058)) # Expiring soon
 infopages["3"]  = ("70", localize(30052), "atoz", "A - Z")
 infopages["4"]  = ("71", localize(30053), "tv3", "TV3")
 infopages["5"]  = ("72", localize(30053), "c4tv", "FOUR")
 infopages["6"]  = ("65", localize(30054), "tv3", localize(30059)) # Comedy
 infopages["7"]  = ("66", localize(30054), "tv3", localize(30060)) # Drama
 infopages["8"]  = ("67", localize(30054), "tv3", localize(30061)) # News/Current affairs
 infopages["9"]  = ("68", localize(30054), "tv3", localize(30062)) # Reality
 infopages["10"] = ("82", localize(30054), "tv3", localize(30063)) # Sports
 infopages["11"] = ("80", localize(30052), "tv3", localize(30064)) # All
 #infopages["12"] = ("74", "RSS", "tv3", "RSS Feeds")
 #infopages["13"] = ("81", "Categories", "tv3", "C4 Highlights")
 #infopages["13"] = ("73", "Categories", "tv3", "All (Small)")
 for index in infopages:
  if infopages[index][1] == folder:
   info = tools.defaultinfo(1)
   info["Title"] = infopages[index][3]
   info["Count"] = int(index)
   info["FileName"] = "%s?ch=TV3&cat=%s&catid=%s" % (sys.argv[0], infopages[index][2], infopages[index][0])
   tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 1)
 if folder == "Shows":
  INDEX_SHOWS("tv3")
 elif folder == "Search":
  INDEX_SEARCH()

def INDEX(provider): #Create a list of top level folders as scraped from TV3's website
 doc = tools.gethtmlpage("%s/tabid/56/default.aspx" % (base_url(provider))) #Get our HTML page with a list of video categories
 if doc:
  a_tag = SoupStrainer('a')
  html_atag = BeautifulSoup(doc, parseOnlyThese = a_tag)
  links = html_atag.findAll(attrs={"rel": "nofollow", "href": re.compile(tv3_urls["CAT_RE"])}) #, "title": True
  if len(links) > 0:
   count = 0
   for link in links:
    info = tools.defaultinfo(1)
    info["Title"] = link.string
    caturl = link['href']
    catid = re.search('%s([0-9]+)' % (tv3_urls["CAT_RE"]), caturl).group(1)
    if info["Title"] == "Title (A - Z)":
     cat = "atoz"
    elif info["Title"] == "TV3 Shows":
     cat = "tv3"
    #elif info["Title"] == "C4TV Shows":
    elif info["Title"] == "FOUR Shows":
     cat = "c4tv"
    else:
     cat = "tv"
    if catid:
     info["Count"] = count
     count += 1
     info["FileName"] = "%s?ch=TV3&cat=%s&catid=%s" % (sys.argv[0], cat, catid)
     tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 1)
  else:
   sys.stderr.write("Couldn't find any categories")
 else:
  sys.stderr.write("Couldn't get index webpage")

def INDEX_SEARCH():
 import xbmc
 keyboard = xbmc.Keyboard("Away", "Search for a Video")
 #keyboard.setHiddenInput(False)
 keyboard.doModal()
 if keyboard.isConfirmed():
  SHOW_SEARCH("58", keyboard.getText())

def INDEX_SHOWS(provider): #Create a second level list of TV Shows from a TV3 webpage
 #doc = tools.gethtmlpage("%s/Shows/tabid/64/Default.aspx" % ("http://www.tv3.co.nz")) #Get our HTML page with a list of video categories
 doc = tools.gethtmlpage("%s/Shows.aspx" % ("http://www.tv3.co.nz")) #Get our HTML page with a list of video categories
 if doc:
  html_divtag = BeautifulSoup(doc)
  linksdiv = html_divtag.find('div', attrs = {"id": "pw_8171"})
  if linksdiv:
   links = linksdiv.findAll('a')
   if len(links) > 0:
    count = 0
    for link in links:
     info = tools.defaultinfo(1)
     info["Title"] = link.string.strip()
     catid = link['href']
     if info["Title"] == "60 Minutes": #The URL on the next line has more videos
      info["FileName"] = "%s?ch=TV3&cat=%s&title=%s&catid=%s" % (sys.argv[0], "shows", urllib.quote(info["Title"]), urllib.quote(catid)) #"http://ondemand.tv3.co.nz/Default.aspx?TabId=80&cat=22"
     else:
      info["FileName"] = "%s?ch=TV3&cat=%s&title=%s&catid=%s" % (sys.argv[0], "shows", urllib.quote(info["Title"]), urllib.quote(catid))
     info["Count"] = count
     count += 1
     tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 1)
   else:
    sys.stderr.write("Couldn't find any videos in list")
  else:
   sys.stderr.write("Couldn't find video list")
 else:
  sys.stderr.write("Couldn't get index webpage")








# HTML Scrapers for different page styles

def add_item_div(soup, provider, count): #Scrape items from a div-style HTML page
 baseurl = base_url(provider)
 info = tools.defaultinfo()
 info["Studio"] = provider
 sys.stderr.write(baseurl)
 link = soup.find("a", attrs={"href": re.compile(baseurl)})
 if link:
  href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, tv3_urls["VIDEO1"], tv3_urls["VIDEO2"], tv3_urls["VIDEO3"]), link['href'])
  if href:
   if link.string:
    title = link.string.strip()
    if title <> "":
     info["TVShowTitle"] = title
     image = soup.find("img", attrs={"src": re.compile(tv3_urls["IMG_RE"]), "title": True})
     if image:
      info.update(tools.imageinfo(image))
     se = soup.find("span", attrs={"class": "title"})
     if se:
      info.update(seasonepisode(se))
     date = soup.find("span", attrs={"class": "dateAdded"})
     if date:
      info.update(dateduration(date))
     info["Title"] = tools.itemtitle(info["TVShowTitle"], info["PlotOutline"])
     info["Count"] = count
     plot = soup.find("div", attrs={"class": "left"}).string
     if plot:
      if plot.strip() <> "":
       info["Plot"] = tools.unescape(plot.strip())
     info["FileName"] = "%s?ch=TV3&id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
     tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 0)

def add_item_show(soup, provider, count, title): #Scrape items from a show-style HTML page
 info = tools.defaultinfo()
 info["Studio"] = provider
 bold = soup.find('b')
 if bold:
  link = bold.find("a", attrs={"href": re.compile(tv3_urls["FEEDBURNER_RE"])})
  if link:
   urltype = "other"
  else:
   link = bold.find("a", attrs={"href": re.compile(base_url("tv3"))})
   if link:
    urltype = "tv3"
  if link:
   if link.string:
    plot = link.string.strip()
    if plot <> "":
     info["PlotOutline"] = plot
     info["TVShowTitle"] = title
     image = soup.find("img", attrs={"src": re.compile(tv3_urls["IMG_RE"])})
     if image:
      info.update(tools.imageinfo(image))
     info.update(seasonepisode(link))
     info["Title"] = tools.itemtitle(info["TVShowTitle"], info["PlotOutline"])
     info["Count"] = count
     if urltype == "tv3":
      href = re.search("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (base_url("tv3"), tv3_urls["VIDEO1"], tv3_urls["VIDEO2"], tv3_urls["VIDEO3"]), link['href'])
      if href:
       info["FileName"] = "%s?ch=TV3&id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
     elif urltype == "other":
      info["FileName"] = "%s?ch=TV3&id=%s&info=%s" % (sys.argv[0], urllib.quote(link["href"]), urllib.quote(str(info)))
     tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 0)

def add_item_table(soup, provider, count, title): #Scrape items from a table-style HTML page
 info = tools.defaultinfo()
 info["Studio"] = provider
 link = soup.find('a')
 if link:
  if link.string:
   plot = link.string.strip()
   if plot <> "":
    info["PlotOutline"] = plot
    info["TVShowTitle"] = title
    info.update(seasonepisode(link))
    info["Title"] = tools.itemtitle(info["TVShowTitle"], info["PlotOutline"])
    info["Count"] = count
    href = re.search("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (base_url("tv3"), tv3_urls["VIDEO1"], tv3_urls["VIDEO2"], tv3_urls["VIDEO3"]), link['href'])
    if href:
     info["FileName"] = "%s?ch=TV3&id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
    tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 0)

def add_item_atoz(soup, provider, count): #Scrape items from an AtoZ-style HTML page
 baseurl = base_url(provider)
 info = tools.defaultinfo()
 info["Studio"] = provider
 if soup.find('h5'):
  link = soup.h5.find("a", attrs={"href": re.compile(baseurl)})
  if link:
   infoitems = {}
   href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, tv3_urls["VIDEO1"], tv3_urls["VIDEO2"], tv3_urls["VIDEO3"]), link['href'])
   if href:
    if link.string:
     title = link.string.strip()
     if title <> "":
      info["TVShowTitle"] = title
      image = soup.find("img", attrs={"src": re.compile(tv3_urls["IMG_RE2"]), "title": True})
      if image:
       info.update(tools.imageinfo(image))
      info.update(seasonepisode(soup.contents[4]))
      info["Title"] = tools.itemtitle(info["TVShowTitle"], info["PlotOutline"])
      plot = soup.find("span", attrs={"class": "lite"})
      if plot.string:
       cleanedplot = plot.string.strip()
       if cleanedplot:
        info["Plot"] = tools.unescape(cleanedplot)
      info["Count"] = count
      info["FileName"] = "%s?ch=TV3&id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
      infoitems[info["Title"]] = info
      #tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 0)
   tools.addlistitems(infoitems, tv3_urls["Fanart"], 0)

def add_item_search(soup, provider, count): #Scrape items from a table-style HTML page
 baseurl = base_url(provider)
 info = tools.defaultinfo()
 info["Studio"] = provider
 title = soup.find("div", attrs={"class": 'catTitle'})
 if title:
  info["TVShowTitle"] = title.a.string.strip()
  href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, tv3_urls["VIDEO1"], tv3_urls["VIDEO2"], tv3_urls["VIDEO3"]), title.a['href'])
  image = soup.find("img")
  if image:
   info.update(tools.imageinfo(image))
  ep = soup.find("div", attrs={"class": 'epTitle'})
  if ep:
   if ep.a:
    info.update(seasonepisode(ep.a))
  date = soup.find("div", attrs={"class": 'epDate'})
#  if date:
#   sys.stderr.write(date.span[1].string.strip())
  info["Title"] = tools.itemtitle(info["TVShowTitle"], info["PlotOutline"])
  info["Count"] = count
  info["FileName"] = "%s?ch=TV3&id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
  tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 0)











# Create pages listing Episodes that can be played

def SHOW_EPISODES(catid, provider): #Show video items from a normal TV3 webpage
 doc = tools.gethtmlpage("%s%s%s" % (base_url("tv3"), tv3_urls["CAT"], catid))
 if doc:
  a_tag=SoupStrainer('div')
  html_atag = BeautifulSoup(doc, parseOnlyThese = a_tag)
  programs = html_atag.findAll(attrs={"class": "latestArticle "})
  if len(programs) > 0:
   count = 0
   for soup in programs:
    add_item_div(soup, provider, count)
    count += 1
  else:
   sys.stderr.write("Couldn't find any videos")
 else:
  sys.stderr.write("Couldn't get videos webpage")

def SHOW_SEARCH(catid, searchterm): #Show video items from a normal TV3 webpage
 doc = tools.gethtmlpage("%s/search/tabid/%s/Default.aspx?amq=%s" % (base_url("tv3"), catid, searchterm.replace(" ", "+")))
 if doc:
  a_tag=SoupStrainer('div')
  html_atag = BeautifulSoup(doc, parseOnlyThese = a_tag)
  programs = html_atag.findAll(attrs={"class": "results"})
  if len(programs) > 0:
   count = 0
   for soup in programs:
    provider = "tv3"
    add_item_search(soup, "tv3", count)
    count += 1
  else:
   sys.stderr.write("Couldn't find any videos")
 else:
  sys.stderr.write("Couldn't get videos webpage")

def SHOW_SHOW(catid, title, provider): #Show video items from a TV Show style TV3 webpage
 baseurl = ""
 if catid[:4] <> "http":
  baseurl = tv3_urls["TV3"]
 geturl = "%s%s" % (baseurl, catid)
 doc = tools.gethtmlpage(geturl)
 if doc:
  div_tag=SoupStrainer('div')
  html_divtag = BeautifulSoup(doc, parseOnlyThese = div_tag)
  tables = html_divtag.find(attrs={"xmlns:msxsl": "urn:schemas-microsoft-com:xslt"})
  if tables:
   programs = tables.findAll('table')
   if len(programs) > 0:
    count = 0
    for soup in programs:
     add_item_show(soup, provider, count, title)
     count += 1
   else:
    programs = tables.findAll('tr')
    if len(programs) > 0:
     count = -1
     for soup in programs:
      count += 1
      if count > 0:
       add_item_table(soup, provider, count, title)
    else:
     sys.stderr.write("Couldn't find any videos in list")
  else:
   sys.stderr.write("Couldn't find video list")
 else:
  sys.stderr.write("Couldn't get index webpage")

def SHOW_ATOZ(catid, provider): #Show video items from an AtoZ style TV3 webpage
 doc = tools.gethtmlpage("%s%s%s" % (base_url("tv3"), tv3_urls["CAT"], catid))
 if doc:
  a_tag=SoupStrainer('div')
  html_atag = BeautifulSoup(doc, parseOnlyThese = a_tag)
  programs = html_atag.findAll(attrs={"class": "wideArticles"})
  if len(programs) > 0:
   count = 0
   for soup in programs:
    add_item_atoz(soup, provider, count)
    count += 1
  else:
   sys.stderr.write("Couldn't find any videos")
 else:
  sys.stderr.write("Couldn't get videos webpage")







# Play a given media file grabbed from a URL

def RESOLVE(id, info): #Scrape a page for a given OnDemand video and build an RTMP URL from the info in the page, then play the URL
 ids = id.split(",")
 if len(ids) == 4:
  pageUrl = "%s/%s/%s/%s/%s/%s/%s/%s/%s" % (base_url(info["Studio"]), ids[0], tv3_urls["VIDEO1"], ids[1], tv3_urls["VIDEO2"], ids[2], tv3_urls["VIDEO3"], ids[3], tv3_urls["VIDEO4"])
  doc = tools.gethtmlpage(pageUrl)
 else:
  doc = tools.gethtmlpage("id")
 if doc:
  #videoid = re.search('var video ="/\*transfer\*([0-9]+)\*([0-9A-Z]+)";', doc)
  videoid = re.search('var video ="\*(.*?)\*([0-9]+)\*(.*?)";', doc)
  if videoid:
   #videoplayer = re.search('var fo = new FlashObject\("(http://static.mediaworks.co.nz/(.*?).swf)', doc)
   videoplayer = re.search('swfobject.embedSWF\("(http://static.mediaworks.co.nz/(.*?).swf)', doc)
   if videoplayer:
    auth = re.search('random_num = "([0-9]+)";', doc)
    realstudio = 'tv3'
    site = re.search("var pageloc='TV-(FOUR|TV3)-Video(Extras)?-OnDemand-", doc)
    if site:
     if site.group(1) <> 'TV3':
      realstudio = 'c4'
    playlist=list()
    #if addon.getSetting('TV3_showads') == 'true':
     #playlist.append(ad)
    fifteen = re.search('flashvars.fifteenHundred = "yes";', doc)
    seven = re.search('flashvars.sevenHundred = "yes";', doc)
    if fifteen and seven:
     LowQuality = "330K"
     MediumQuality = "700K"
     HighQuality = "1500K"
    elif fifteen:
     LowQuality = "128K"
     MediumQuality = "330K"
     HighQuality = "1500K"
    elif seven:
     LowQuality = "128K"
     MediumQuality = "330K"
     HighQuality = "700K"
    else:
     LowQuality = "128K"
     MediumQuality = "330K"
     HighQuality = "330K"
    #elif re.search('flashvars.highEnd = "true";', doc):
    quality = HighQuality
    quality2 = MediumQuality
    quality3 = LowQuality
    if addon.getSetting('TV3_quality') == "Low":
     quality = LowQuality
     quality3 = HighQuality
    elif addon.getSetting('TV3_quality') == "Medium":
     quality = MediumQuality
     quality2 = HighQuality
    geo = re.search('var geo= "(no|geo)";', doc)
    if (geo.group(1) == 'no'):
     url = '%s%s/%s/%s_%s.%s' % (http(realstudio), videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality, "mp4")
    else:
     #swfverify = ' swfUrl=%s swfVfy=true' % (videoplayer.group(1))
     #rtmpurl = '%s%s/%s/%s_%s' % (rtmp(info["Studio"]), videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality)
     url = '%s%s/%s/%s_%s' % (rtmp(realstudio), videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality)
     if auth:
      swfverify = ' swfUrl=%s?rnd=%s pageUrl=%s swfVfy=true' % (videoplayer.group(1), auth.group(1), pageUrl)
     else:
      swfverify = ' swfUrl=%s pageUrl=%s swfVfy=true' % (videoplayer.group(1), pageUrl)
     url += swfverify
    sys.stderr.write("URL: %s" % (url))
    #sys.stderr.write("Flash Player: %s" % (videoplayer.group(1)))
    playlist.append(url)
    if len(playlist) > 1:
     uri = constructStackURL(playlist)
    elif len(playlist) == 1:
     uri = playlist[0]
    #liz = xbmcgui.ListItem(id, iconImage = info["Icon"], thumbnailImage = info["Thumb"])
    #liz.setInfo( type = "Video", infoLabels = info)
    #liz.setProperty("IsPlayable", "true")
    #liz.setPath(uri)
    #xbmcplugin.setResolvedUrl(handle = int(sys.argv[1]), succeeded = True, listitem = liz)
    info["FileName"] = url
    tools.addlistitem(int(sys.argv[1]), info, tv3_urls["Fanart"], 0, 1, uri)
   else:
    sys.stderr.write("Couldn't get video player URL")
  else:
   sys.stderr.write("Couldn't get video RTMP URL")
 else:
  sys.stderr.write("Couldn't get video webpage")
