import tools, urllib, string, re, sys, time, xbmcaddon, xbmcgui, xbmcplugin
from BeautifulSoup import BeautifulSoup, SoupStrainer, BeautifulStoneSoup
from xml.dom import minidom

ziln_urls = dict()
ziln_urls["ZILN"] = 'http://www.ziln.co.nz'
ziln_urls["RTMP1"] = 'rtmp://flash1.e-cast.co.nz'
ziln_urls["RTMP2"] = 'ecast'
ziln_urls["RTMP3"] = 'mp4:/ziln'
ziln_urls["Fanart"] = 'resources/images/Ziln.jpg'

def INDEX(type, urlext):
 if type == "channel":
  folder = 1
  url = ziln_urls["ZILN"]
 elif type == "video":
  folder = 0
  #url = "%s/channel/%s" % (ziln_urls["ZILN"], urlext)
  url = "%s/assets/php/slider.php?channel=%s" % (ziln_urls["ZILN"], urlext)
 doc = tools.gethtmlpage(url)
 if doc:
  if type == "channel":
   div_tag = SoupStrainer('div')
   html_divtag = BeautifulSoup(doc, parseOnlyThese = div_tag)
   programmes = html_divtag.findAll(attrs={'class' : 'programmes'})
  elif type == "video":
   div_tag = SoupStrainer('body')
   html_divtag = BeautifulSoup(doc, parseOnlyThese = div_tag)
   programmes = html_divtag.findAll(attrs={'class' : 'slider slider-small'})
  if len(programmes) > 0:
   for programme in programmes:
    list = programme.find('ul')
    listitems = list.findAll('li')
    if len(listitems) > 0:
     count = 0
     for listitem in listitems:
      link = listitem.find('a', attrs={'href' : re.compile("^/%s/" % type)})
      if link.img:
       if re.search("assets/images/%ss/" % type, link.img["src"]):
        info = tools.defaultinfo(1)
        #info["Title"] = link.img["alt"]
        if listitem.p.string:
         info["Title"] = listitem.p.string.strip()
        else:
         info["Title"] = link.img["alt"]
        info["Thumb"] = "%s/%s" % (ziln_urls["ZILN"], link.img["src"])
        info["Count"] = count
        count += 1
        #channelurl = re.search("/%s/(.*)" % type, link["href"]).group(1)
        channelurl = re.search("assets/images/%ss/([0-9]*?)-mini.jpg" % type, link.img["src"]).group(1)
        #infourl = "&info=%s" % urllib.quote(str(info))
        info["FileName"] = "%s?ch=Ziln&%s=%s" % (sys.argv[0], type, urllib.quote(channelurl))
        tools.addlistitem(info, ziln_urls["Fanart"], folder)
  else:
   sys.stderr.write("Couldn't find any programs")
 else:
  sys.stderr.write("Couldn't get page")
   
def PROGRAMMES(type, urlext):
 if type == "channel":
  folder = 1
  url = ziln_urls["ZILN"]
 elif type == "video":
  folder = 0
  url = "%s/channel/%s" % (ziln_urls["ZILN"], urlext)
 doc = tools.gethtmlpage(url)
 if doc:
  div_tag = SoupStrainer('div')
  html_divtag = BeautifulSoup(doc, parseOnlyThese = div_tag)
  programmes = html_divtag.findAll(attrs={'class' : 'programmes'})
  if len(programmes) > 0:
   for programme in programmes:
    iframe = programme.find('iframe')
    url = "%s%s" % (ziln_urls["ZILN"], iframe["src"])
    doc = tools.gethtmlpage(url)
    listitems = list.findAll('li')
    if len(listitems) > 0:
     count = 0
     for listitem in listitems:
      link = listitem.find('a', attrs={'href' : re.compile("^/%s/" % type)})
      if link.img:
       if re.search("assets/images/%ss/" % type, link.img["src"]):
        info = tools.defaultinfo(1)
        #info["Title"] = link.img["alt"]
        if listitem.p.string:
         info["Title"] = listitem.p.string.strip()
        else:
         info["Title"] = link.img["alt"]
         #info["Title"] = listitem.find('p').contents[0]
        info["Thumb"] = "%s/%s" % (ziln_urls["ZILN"], link.img["src"])
        info["Count"] = count
        count += 1
        channelurl = re.search("/%s/(.*)" % type, link["href"]).group(1)
		#infourl = "&info=%s" % urllib.quote(str(info))
        info["FileName"] = "%s?ch=Ziln&%s=%s" % (sys.argv[0], type, urllib.quote(channelurl))
        tools.addlistitem(info, ziln_urls["Fanart"], folder)

def RESOLVE(index): #, info
 doc = tools.gethtmlpage("%s/playlist/null/%s" % (ziln_urls["ZILN"], index))
 if doc:
  soup = BeautifulStoneSoup(doc)
  #tools.message(soup.find('media:content')["url"])
  #minidom.parseString(doc).documentElement.getElementsByTagName("media:content")[0].attributes["url"].value
  info = tools.defaultinfo(0)
  info["Title"] = soup.find('item').title.contents[0]
  info["Thumb"] = soup.find('jwplayer:image').contents[0]
  info["Plot"] = soup.find('description').contents[0]
  uri = "%s%s" % (ziln_urls["ZILN"], soup.find('media:content')["url"])
  tools.addlistitem(info, ziln_urls["Fanart"], 0, 1, uri)
  #liz=xbmcgui.ListItem(path=uri)
  #return(xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=liz))
  #dom.getElementsByTagName("title")[0]
  #dom.getElementsByTagName("title")[1]
  #dom.getElementsByTagName("jwplayer:image")[0]
  #dom.getElementsByTagName("media:content")[0]
