#/*
# *   Copyright (C) 2010 Mark Honeychurch
# *   based on the TVNZ Addon by JMarshall
# *
# *
# * This Program is free software; you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation; either version 2, or (at your option)
# * any later version.
# *
# * This Program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program; see the file COPYING. If not, write to
# * the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# * http://www.gnu.org/copyleft/gpl.html
# *
# */

#ToDo:
# Fix sorting methods (they don't all seem to work properly)
# Scan HTML data for broadcast dates (in AtoZ, table view, etc)
# Find somewhere to add expiry dates?
# Add an option to show an advert before the program (I can't find the URLs for adverts at the moment)

#Useful list of categories
# http://ondemand.tv3.co.nz/Host/SQL/tabid/21/ctl/Login/portalid/0/Default.aspx

#XBMC Forum Thread
# http://forum.xbmc.org/showthread.php?t=37014






# Import external libraries

import urllib, urllib2, htmllib, string, unicodedata, re, time, urlparse, cgi, xbmcgui, xbmcplugin, xbmcaddon
from htmlentitydefs import name2codepoint
from xml.dom import minidom
from BeautifulSoup import BeautifulSoup, SoupStrainer









# Setup a dictionary of useful URLs

urls = dict()
urls["TV3"] = 'http://www.tv3.co.nz'
urls["BASE1"] = 'http://ondemand'
urls["BASE2"] = 'co.nz'
urls["RTMP1"] = 'rtmpe://nzcontent.mediaworks.co.nz'
urls["RTMP2"] = '_definst_/mp4:'
urls["VIDEO1"] = 'tabid'
urls["VIDEO2"] = 'articleID'
urls["VIDEO3"] = 'MCat'
urls["VIDEO4"] = 'Default.aspx'
urls["FEEDBURNER_RE"] = '//feedproxy\.google\.com/'
urls["CAT"] = '/default404.aspx?tabid='
urls["CAT_RE"] = '/default404\.aspx\?tabid='
urls["IMG_RE"] = '\.ondemand\.tv3\.co\.nz/Portals/0-Articles/'

__addon__ = xbmcaddon.Addon(id='plugin.video.tv3.ondemand')
localize  = __addon__.getLocalizedString









# Generic functions

def message(message, title = "Warning"): #Show an on-screen message (useful for debugging)
 dialog = xbmcgui.Dialog()
 if message:
  if message <> "":
   dialog.ok(title, message)
  else:
   dialog.ok("Message", "Empty message text")
 else:
  dialog.ok("Message", "No message text")

def gethtmlpage(url): #Grab an HTML page
 sys.stderr.write("Requesting page: %s" % (url))
 req = urllib2.Request(url)
 response = urllib2.urlopen(req)
 doc = response.read()
 response.close()
 return doc

def unescape(s): #Convert escaped HTML characters back to native unicode, e.g. &gt; to > and &quot; to "
 return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

def checkdict(info, items): #Check that all of the list "items" are in the dictionary "info"
 for item in items:
  if info.get(item, "##unlikelyphrase##") == "##unlikelyphrase##":
   sys.stderr.write("Dictionary missing item: %s" % (item))
   return 0
 return 1






# Metadata

def defaultinfo(folder = 0): #Set the default info for folders (1) and videos (0). Most options have been hashed out as they don't show up in the list and are grabbed from the media by the player
 info = dict()
 if folder:
  info["Icon"] = "DefaultFolder.png"
 else:
  info["Icon"] = "DefaultVideo.png"
  #info["VideoCodec"] = "flv"
  #info["VideoCodec"] = "avc1"
  #info["VideoCodec"] = "h264"
  #info["VideoResolution"] = "480" #actually 360 (640x360)
  #info["VideoAspect"] = "1.78"
  #info["AudioCodec"] = "aac"
  #info["AudioChannels"] = "2"
  #info["AudioLanguage"] = "eng"
 info["Thumb"] = ""
 return info

def xbmcdate(inputdate): #Convert a date in "%d/%m/%y" format to an XBMC friendly format
 return time.strftime(xbmc.getRegion( "datelong" ).replace( "DDDD,", "" ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" ).strip(), time.strptime(inputdate,"%d/%m/%y"))

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
   #info["Aired"] = time.strftime("%Y-%m-%d", time.strptime(aired.group(1),"%d/%m/%y"))
   info["Aired"] = xbmcdate(aired.group(1))
   info["Date"] = info["Aired"]
   #info["Year"] = int(time.strftime("%Y", info["Aired"]))
  duration = re.search("\(([0-9]+:[0-9]{2})\)", ad.contents[1])
  if duration:
   #info["Duration"] = duration.group(2)
   info["Duration"] = time.strftime("%M", time.strptime(duration.group(1), "%M:%S"))
  return info

def imageinfo(image): #Search an image for its HREF
 if image:
  info = dict()
  info["Thumb"] = image['src']
  #alttitle = image['title']
  return info

def itemtitle(Title, PlotOutline): #Build a nice title from the program title and sub-title (given as PlotOutline)
 if PlotOutline:
  Title = "%s - %s" % (Title, PlotOutline)
 return Title








# URL manipulation 

def constructStackURL(playlist): #Build a URL stack from multiple URLs for the XBMC player
 uri = ""
 for url in playlist:
  url.replace(',',',,')
  if len(uri)>0:
   uri = uri + " , " + url
  else:
   uri = "stack://" + url
 return(uri)

def base_url(provider): #Build a base website URL for a given site (c4tv or tv3)
 return "%s.%s.%s" % (urls["BASE1"], provider, urls["BASE2"])

def rtmp(provider): #Build an RTMP URL for a given site (c4tv or tv3)
 if provider == "c4tv":
  return "%s/%s/%s" % (urls["RTMP1"], "c4", urls["RTMP2"])
 else:
  return "%s/%s/%s" % (urls["RTMP1"], provider, urls["RTMP2"])






# XBMC Manipulation

def addlistitem(info, folder = 0): #Add a list item (media file or folder) to the XBMC page
 if checkdict(info, ("Title", "Icon", "Thumb", "FileName")):
  liz = xbmcgui.ListItem(info["Title"], iconImage = info["Icon"], thumbnailImage = info["Thumb"])
  liz.setInfo(type = "Video", infoLabels = info)
  if not folder:
   liz.setProperty("IsPlayable", "true")
  xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = info["FileName"], listitem = liz, isFolder = folder)








#Create pages of folders (for categories, etc)

def INDEX_FOLDERS(): #Create a list of top level folders for the hierarchy view
 folders = dict()
 folders["0"] = localize(30002) # "Categories"
 folders["1"] = localize(30003) # "Channels"
 folders["2"] = localize(30004) # "Genres"
 folders["3"] = localize(30005) # "Shows"
 for index in folders:
  info = defaultinfo(1)
  info["Title"] = folders[index]
  info["Count"] = int(index)
  info["FileName"] = "%s?folder=%s" % (sys.argv[0], folders[index])
  addlistitem(info, 1)

def INDEX_FOLDER(folder): #Create second level folder for the hierarchy view, only showing items for the selected top level folder
 infopages = dict()
 infopages["0"]  = ("63", localize(30002), "tv3", localize(30006)) # Latest
 infopages["1"]  = ("61", localize(30002), "tv3", localize(30007)) # Most Watched
 infopages["2"]  = ("64", localize(30002), "tv3", localize(30008)) # Expiring soon
 infopages["3"]  = ("70", localize(30002), "atoz", "A - Z")
 infopages["4"]  = ("71", localize(30003), "tv3", "TV3")
 infopages["5"]  = ("72", localize(30003), "c4tv", "C4")
 infopages["6"]  = ("65", localize(30004), "tv3", localize(30009)) # Comedy
 infopages["7"]  = ("66", localize(30004), "tv3", localize(30010)) # Drama
 infopages["8"]  = ("67", localize(30004), "tv3", localize(30011)) # News/Current affairs
 infopages["9"]  = ("68", localize(30004), "tv3", localize(30012)) # Reality
 infopages["10"] = ("82", localize(30004), "tv3", localize(30013)) # Sports
 infopages["11"] = ("80", localize(30002), "tv3", localize(30014)) # All
 #infopages["12"] = ("74", "RSS", "tv3", "RSS Feeds")
 #infopages["13"] = ("81", "Categories", "tv3", "C4 Highlights")
 #infopages["13"] = ("73", "Categories", "tv3", "All (Small)")
 for index in infopages:
  if infopages[index][1] == folder:
   info = defaultinfo(1)
   info["Title"] = infopages[index][3]
   info["Count"] = int(index)
   info["FileName"] = "%s?cat=%s&catid=%s" % (sys.argv[0], infopages[index][2], infopages[index][0])
   addlistitem(info, 1)
 if folder == "Shows":
  INDEX_SHOWS("tv3")

def INDEX(provider): #Create a list of top level folders as scraped from TV3's website
 doc = gethtmlpage("%s/tabid/56/default.aspx" % (base_url(provider))) #Get our HTML page with a list of video categories
 if doc:
  a_tag = SoupStrainer('a')
  html_atag = BeautifulSoup(doc, parseOnlyThese = a_tag)
  links = html_atag.findAll(attrs={"rel": "nofollow", "href": re.compile(urls["CAT_RE"])}) #, "title": True
  if len(links) > 0:
   count = 0
   for link in links:
    info = defaultinfo(1)
    info["Title"] = link.string
    caturl = link['href']
    catid = re.search('%s([0-9]+)' % (urls["CAT_RE"]), caturl).group(1)
    if info["Title"] == "Title (A - Z)":
     cat = "atoz"
    elif info["Title"] == "TV3 Shows":
     cat = "tv3"
    elif info["Title"] == "C4TV Shows":
     cat = "c4tv"
    else:
     cat = "tv"
    if catid:
     info["Count"] = count
     count += 1
     info["FileName"] = "%s?cat=%s&catid=%s" % (sys.argv[0], cat, catid)
     addlistitem(info, 1)
  else:
   sys.stderr.write("Couldn't find any categories")
 else:
  sys.stderr.write("Couldn't get index webpage")

def INDEX_SHOWS(provider): #Create a second level list of TV Shows from a TV3 webpage
 doc = gethtmlpage("%s/Shows/tabid/64/Default.aspx" % ("http://www.tv3.co.nz")) #Get our HTML page with a list of video categories
 if doc:
  html_divtag = BeautifulSoup(doc)
  linksdiv = html_divtag.find('div', attrs = {"id": "pw_8171"})
  if linksdiv:
   links = linksdiv.findAll('a')
   if len(links) > 0:
    count = 0
    for link in links:
     info = defaultinfo(1)
     info["Title"] = link.string.strip()
     catid = link['href']
     if info["Title"] == "60 Minutes": #The URL on the next line has more videos
      info["FileName"] = "%s?cat=%s&title=%s&catid=%s" % (sys.argv[0], "shows", urllib.quote(info["Title"]), urllib.quote(catid)) #"http://ondemand.tv3.co.nz/Default.aspx?TabId=80&cat=22"
     else:
      info["FileName"] = "%s?cat=%s&title=%s&catid=%s" % (sys.argv[0], "shows", urllib.quote(info["Title"]), urllib.quote(catid))
     info["Count"] = count
     count += 1
     addlistitem(info, 1)
   else:
    sys.stderr.write("Couldn't find any videos in list")
  else:
   sys.stderr.write("Couldn't find video list")
 else:
  sys.stderr.write("Couldn't get index webpage")








# HTML Scrapers for different page styles

def add_item_div(soup, provider, count): #Scrape items from a div-style HTML page
 baseurl = base_url(provider)
 info = defaultinfo()
 info["Studio"] = provider
 link = soup.find("a", attrs={"href": re.compile(baseurl)})
 if link:
  href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, urls["VIDEO1"], urls["VIDEO2"], urls["VIDEO3"]), link['href'])
  if href:
   if link.string:
    title = link.string.strip()
    if title <> "":
     info["TVShowTitle"] = title
     image = soup.find("img", attrs={"src": re.compile(urls["IMG_RE"]), "title": True})
     if image:
      info.update(imageinfo(image))
     se = soup.find("span", attrs={"class": "title"})
     if se:
      info.update(seasonepisode(se))
     date = soup.find("span", attrs={"class": "dateAdded"})
     if date:
      info.update(dateduration(date))
     info["Title"] = itemtitle(info["TVShowTitle"], info["PlotOutline"])
     info["Count"] = count
     plot = soup.find("div", attrs={"class": "left"}).string
     if plot:
      if plot.strip() <> "":
       info["Plot"] = unescape(plot.strip())
     info["FileName"] = "%s?id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
     addlistitem(info, 0)

def add_item_show(soup, provider, count, title): #Scrape items from a show-style HTML page
 info = defaultinfo()
 info["Studio"] = provider
 bold = soup.find('b')
 if bold:
  link = bold.find("a", attrs={"href": re.compile(urls["FEEDBURNER_RE"])})
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
     image = soup.find("img", attrs={"src": re.compile(urls["IMG_RE"])})
     if image:
      info.update(imageinfo(image))
     info.update(seasonepisode(link))
     info["Title"] = itemtitle(info["TVShowTitle"], info["PlotOutline"])
     info["Count"] = count
     if urltype == "tv3":
      href = re.search("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (base_url("tv3"), urls["VIDEO1"], urls["VIDEO2"], urls["VIDEO3"]), link['href'])
      if href:
       info["FileName"] = "%s?id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
     elif urltype == "other":
      info["FileName"] = "%s?id=%s&info=%s" % (sys.argv[0], urllib.quote(link["href"]), urllib.quote(str(info)))
     addlistitem(info, 0)

def add_item_table(soup, provider, count, title): #Scrape items from a table-style HTML page
 info = defaultinfo()
 info["Studio"] = provider
 link = soup.find('a')
 if link:
  if link.string:
   plot = link.string.strip()
   if plot <> "":
    info["PlotOutline"] = plot
    info["TVShowTitle"] = title
    info.update(seasonepisode(link))
    info["Title"] = itemtitle(info["TVShowTitle"], info["PlotOutline"])
    info["Count"] = count
    href = re.search("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (base_url("tv3"), urls["VIDEO1"], urls["VIDEO2"], urls["VIDEO3"]), link['href'])
    if href:
     info["FileName"] = "%s?id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
    addlistitem(info, 0)

def add_item_atoz(soup, provider, count): #Scrape items from an AtoZ-style HTML page
 baseurl = base_url(provider)
 info = defaultinfo()
 info["Studio"] = provider
 link = soup.h5.find("a", attrs={"href": re.compile(baseurl)})
 if link:
  href = re.match("%s/(.*?)/%s/([0-9]+)/%s/([0-9]+)/%s/([0-9]+)/" % (baseurl, urls["VIDEO1"], urls["VIDEO2"], urls["VIDEO3"]), link['href'])
  if href:
   if link.string:
    title = link.string.strip()
    if title <> "":
     info["TVShowTitle"] = title
     info.update(imageinfo(soup.find("img", attrs={"src": re.compile(urls["IMG_RE"]), "title": True})))
     info.update(seasonepisode(soup.contents[4]))
     info["Title"] = itemtitle(info["TVShowTitle"], info["PlotOutline"])
     info["Plot"] = unescape(soup.find("span", attrs={"class": "lite"}).string.strip())
     info["Count"] = count
     info["FileName"] = "%s?id=%s&info=%s" % (sys.argv[0], "%s,%s,%s,%s" % (href.group(1), href.group(2), href.group(3), href.group(4)), urllib.quote(str(info)))
     addlistitem(info, 0)













# Create pages listing Episodes that can be played

def SHOW_EPISODES(catid, provider): #Show video items from a normal TV3 webpage
 doc = gethtmlpage("%s%s%s" % (base_url("tv3"), urls["CAT"], catid))
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

def SHOW_SHOW(catid, title, provider): #Show video items from a TV Show style TV3 webpage
 baseurl = ""
 if catid[:4] <> "http":
  baseurl = urls["TV3"]
 geturl = "%s%s" % (baseurl, catid)
 doc = gethtmlpage(geturl)
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
 doc = gethtmlpage("%s%s%s" % (base_url("tv3"), urls["CAT"], catid))
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
  doc = gethtmlpage("%s/%s/%s/%s/%s/%s/%s/%s/%s" % (base_url(info["Studio"]), ids[0], urls["VIDEO1"], ids[1], urls["VIDEO2"], ids[2], urls["VIDEO3"], ids[3], urls["VIDEO4"]))
 else:
  doc = gethtmlpage("id")
 if doc:
  #videoid = re.search('var video ="/\*transfer\*([0-9]+)\*([0-9A-Z]+)";', doc)
  videoid = re.search('var video ="/\*(.*?)\*([0-9]+)\*(.*?)";', doc)
  if videoid:
   videoplayer = re.search('var fo = new FlashObject\("(http://static.mediaworks.co.nz/(.*?).swf)', doc)
   if videoplayer:
    playlist=list()
    #if __addon__.getSetting('advert') == 'true':
     #playlist.append(ad)
    quality = "330K"
    if __addon__.getSetting('hq') == 'true':
     quality = "700K"
    rtmpurl = '%s/%s/%s/%s_%s' % (rtmp(info["Studio"]), videoid.group(1), videoid.group(2), urllib.quote(videoid.group(3)), quality)
    sys.stderr.write("RTMP URL: %s" % (rtmpurl))
    swfverify = ' swfUrl=%s swfVfy=true' % (videoplayer.group(1))
    sys.stderr.write("Flash Player: %s" % (videoplayer.group(1)))
    playlist.append(rtmpurl + swfverify)
    if len(playlist) > 1:
     uri = constructStackURL(playlist)
    elif len(playlist) == 1:
     uri = playlist[0]
    liz = xbmcgui.ListItem(id, iconImage = info["Icon"], thumbnailImage = info["Thumb"])
    liz.setInfo( type = "Video", infoLabels = info)
    liz.setProperty("IsPlayable", "true")
    liz.setPath(uri)
    xbmcplugin.setResolvedUrl(handle = int(sys.argv[1]), succeeded = True, listitem = liz)
   else:
    sys.stderr.write("Couldn't get video player URL")
  else:
   sys.stderr.write("Couldn't get video RTMP URL")
 else:
  sys.stderr.write("Couldn't get video webpage")








# Decide what to run based on the plugin URL

params = cgi.parse_qs(urlparse.urlparse(sys.argv[2])[4])
if params:
 if params.get("folder", "") <> "":
  INDEX_FOLDER(params["folder"][0])
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
  #xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL)
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
 elif params.get("cat", "") <> "":
  if params["cat"][0] == "tv":
   SHOW_EPISODES(params["catid"][0], "tv3")
  elif params["cat"][0] == "atoz":
   SHOW_ATOZ(params["catid"][0], "tv3")
  elif params["cat"][0] == "tv3":
   SHOW_EPISODES(params["catid"][0], "tv3")
  elif params["cat"][0] == "c4tv":
   SHOW_EPISODES(params["catid"][0], "c4tv")
  elif params["cat"][0] == "shows":
   SHOW_SHOW(urllib.unquote(params["catid"][0]), urllib.unquote(params["title"][0]), "tv3")
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
  #xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_DATE)
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL)
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
  xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_EPISODE)
  xbmcplugin.setContent(handle = int(sys.argv[1]), content = "episodes")
  xbmcplugin.endOfDirectory(int(sys.argv[1]))
 elif params.get("id", "") <> "":
  RESOLVE(params["id"][0], eval(urllib.unquote(params["info"][0])))
else:
 if __addon__.getSetting('folders') == 'true':
  INDEX_FOLDERS()
 else:
  INDEX("tv3")
 xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
 #xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
 xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL)
 xbmcplugin.endOfDirectory(int(sys.argv[1]))


