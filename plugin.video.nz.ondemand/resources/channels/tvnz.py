import re, sys, time

from xml.dom import minidom

import resources.tools as tools
import resources.config as config
settings = config.__settings__
from resources.tools import webpage

class tvnz:
 def __init__(self):
  self.base = sys.argv[0]
  self.channel = "TVNZ"
  self.urls = dict()
  self.urls['base'] = 'http://tvnz.co.nz'
  self.urls['content'] = 'content'
  self.urls['page'] = 'ps3_xml_skin.xml'
  self.urls['search'] = 'search'
  self.urls['play'] = 'ta_ent_smil_skin.smil?platform=PS3'
  self.urls['episodes'] = '_episodes_group'
  self.urls['extras'] = '_extras_group'
  self.urls['playerKey'] = 'AQ~~,AAAA4FQHurk~,l-y-mylVvQmMeQArl3N6WrFttyxCZNYX'
  self.urls['publisherID'] = 963482467001
  
# http://tvnz.co.nz/video
  self.urls['const'] = 'f86d6617a68b38ee0f400e1f4dc603d6e3b4e4ed'
  self.urls['experienceID'] = 1029272630001
  self.urls['playerID'] = str(self.urls['experienceID'])
  
# http://tvnz.co.nz/ondemand/xl
  self.urls['const_PS3'] = 'c533b8ff14118661efbd88d7be2520a0427d3b62'
  self.urls['const2_PS3'] = '2823513dd61191c88af73bcacb66fd8e5d7d79bc'
  self.urls['experienceID_PS3'] = 1257248093001
  
  self.urls['PS3'] = 'http://tvnz.co.nz/ondemand/xl'
  #self.urls['PS3'] = 'http://tvnz.co.nz/stylesheets/ps3/entertainment/flash/ps3Flash.swf'
  self.urls['contentID'] = 'http://tvnz.co.nz/ondemand/xl'
  #self.urls['contentID'] = 'http://tvnz.co.nz/ondemand/xl&dynamicStreaming=true&isSlim=true&isSlim=1?smoothing=true&playerHeight=512&playerWidth=640&videoSmoothing=true'
  self.urls['swfUrl'] = 'http://admin.brightcove.com/viewer/us20120920.1336/federatedVideoUI/BrightcovePlayer.swf'
  self.urls['swfUrl_PS3'] = 'http://admin.brightcove.com/viewer/us20120920.1336/federatedSlim/BrightcovePlayer.swf?uid=' + str(long(time.time() * 1000))
  #self.urls['swfUrl_PS3'] = 'http://admin.brightcove.com/viewer/us20120920.1336/federatedSlim/BrightcovePlayer.swf'
  #self.urls['swfUrl_PS3'] = 'http://c.brightcove.com/services/viewer/federated_f9?&playerWidth=640&playerHeight=512&dynamicStreaming=true&isSlim=true&playerKey=AQ%7E%7E%2CAAAA4FQHurk%7E%2Cl-y-mylVvQmMeQArl3N6WrFttyxCZNYX&playerID=1257248093001&videoSmoothing=true&isSlim=1?smoothing=true'
  #self.urls['swfUrl_PS3'] = 'http://tvnz.co.nz/stylesheets/ps3/entertainment/flash/ps3Flash.swf'

  self.PS3 = True
  self.IOS = True
  self.bitrate_min = 400000
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

 def index(self):
  page = webpage(self.url("ps3_navigation")) # http://tvnz.co.nz/content/ps3_navigation/ps3_xml_skin.xml
  xml = self._xml(page.doc)
  if xml:
   for stat in xml.getElementsByTagName('MenuItem'):
    type = stat.attributes["type"].value
    if type in ('shows', 'alphabetical'): #, 'distributor'
     m = re.search('/([0-9]+)/',stat.attributes["href"].value)
     if m:
      item = tools.xbmcItem()
      info = item.info
      info["Title"] = stat.attributes["title"].value
      info["FileName"] = "%s?ch=%s&type=%s&id=%s" % (self.base, self.channel, type, m.group(1))
      self.xbmcitems.items.append(item)
   item = tools.xbmcItem() # Search
   info = item.info
   info["Title"] = "Search"
   info["FileName"] = "%s?ch=TVNZ&type=%s" % (self.base, "search")
   self.xbmcitems.items.append(item)
  else:
   sys.stderr.write("No XML Data")
  self.xbmcitems.addall()

 def show(self, id, search = False):
  if search:
   import urllib
   url = "%s/%s/%s?q=%s" % (self.urls['base'], self.urls['search'], self.urls['page'], urllib.quote_plus(id))
  else:
   url = self.url(id)
  page = webpage(url)
  xml = self._xml(page.doc)
  if xml:
   for show in xml.getElementsByTagName('Show'):
    se = re.search('/content/(.*)_(episodes|extras)_group/ps3_xml_skin.xml', show.attributes["href"].value)
    if se:
     if se.group(2) == "episodes":
      #videos = int(show.attributes["videos"].value) # Number of Extras
	  #episodes = int(show.attributes["episodes"].value) # Number of Episodes
      #channel = show.attributes["channel"].value
      item = tools.xbmcItem()
      info = item.info
      info["FileName"] = "%s?ch=%s&type=singleshow&id=%s%s" % (self.base, self.channel, se.group(1), self.urls['episodes'])
      info["Title"] = show.attributes["title"].value
      info["TVShowTitle"] = info["Title"]
      #epinfo = self.firstepisode(se.group(1))
      #if epinfo:
      # info = dict(epinfo.items() + info.items())
      self.xbmcitems.items.append(item)
  #self.xbmcitems.type = "tvshows"
  self.xbmcitems.addall()

 def search(self):
  results = self.xbmcitems.search()
  if results:
   self.show(results, True)

 def episodes(self, id):
  page = webpage(self.url(id))
  if page.doc:
   xml = self._xml(page.doc)
   if xml:
    #for ep in xml.getElementsByTagName('Episode').extend(xml.getElementsByTagName('Extra')):
    #for ep in map(xml.getElementsByTagName, ['Episode', 'Extra']):
    count = xml.getElementsByTagName('Episode').length
    for ep in xml.getElementsByTagName('Episode'):
     item = self._episode(ep)
     if item:
      self.xbmcitems.items.append(item)
      if self.prefetch:
       self.xbmcitems.add(count)
    for ep in xml.getElementsByTagName('Extras'):
     item = self._episode(ep)
     if item:
      self.xbmcitems.items.append(item)
    #self.xbmcitems.sorting.append("DATE")
    #self.xbmcitems.type = "episodes"
    #self.xbmcitems.addall()
    if self.prefetch:
     self.xbmcitems.sort()
    else:
     self.xbmcitems.addall()


 def firstepisode(self, id):
  page = webpage(self.url(id + self.urls['episodes']))
  if page.doc:
   xml = self._xml(page.doc)
   if xml:
    item = self._episode(xml.getElementsByTagName('Episode')[0])
    if item:
     return item.info
  return False

 def _episode(self, ep):
  #se = re.search('/([0-9]+)/', ep.attributes["href"].value)
  se = re.search('([0-9]+)', ep.attributes["href"].value)
  if se:
   item = tools.xbmcItem()
   link = se.group(1)
   if ep.firstChild:
    item.info["Plot"] = ep.firstChild.data.strip()
   title = ep.attributes["title"].value
   subtitle = ep.attributes["sub-title"].value
   if not subtitle:
    titleparts = title.split(': ', 1) # Some Extras have the Title and Subtitle put into the title attribute separated by ': '
    if len(titleparts) == 2:
     title = titleparts[0]
     subtitle = titleparts[1]
   sxe = ""
   episodeparts = ep.attributes["episode"].value.split('|')
   if len(episodeparts) == 3:
    #see = re.search('Series ([0-9]+), Episode ([0-9]+)', episodeparts[0].strip()) # Need to catch "Episodes 7-8" as well as "Epsiode 7". Also need to catch episode without series
    see = re.search('(?P<s>Se(ries|ason) ([0-9]+), )?Episodes? (?P<e>[0-9]+)(-(?P<e2>[0-9]+))?', episodeparts[0].strip())
    if see:
     try:
      item.info["Season"]  = int(see.group("s"))
     except:
      item.info["Season"] = 1
     item.info["Episode"] = int(see.group("e"))
    sxe = item.sxe()
    if not sxe:
      sxe = episodeparts[0].strip() # E.g. "Coming Up" or "Catch Up"
    date = self._date(episodeparts[1].strip())
    if date:
     item.info["Date"] = date
    item.info["Premiered"] = episodeparts[1].strip()
    item.info["Duration"] = self._duration(episodeparts[2].strip())
   item.info["TVShowTitle"] = title
   item.info["Title"] = " ".join((title, sxe, subtitle)) #subtitle
   item.info["Thumb"] = ep.attributes["src"].value
   if self.prefetch:
    item.urls = self._geturls(link)
   else:
    item.playable = True
    item.info["FileName"] = "%s?ch=%s&id=%s&info=%s" % (self.base, self.channel, link, item.infoencode())
   return item
  else:
   sys.stderr.write("_episode: No se")

 def play(self, id, encodedinfo):
  item = tools.xbmcItem()
  item.infodecode(encodedinfo)
  item.fanart = self.xbmcitems.fanart
  item.urls = self._geturls(id)
  self.xbmcitems.resolve(item, self.channel)

 def _geturls(self, id):
  urls = dict()
  if self.PS3:
   rtmpdata = self.get_clip_info_ps3(int(id))
   for rendition in rtmpdata:
    if self.IOS:
     urls[rendition["encodingRate"]] = 'hls+' + rendition["defaultURL"]
     #urls[rendition["encodingRate"]] = 'apple' + rendition["defaultURL"]
    else:
     urls[rendition["encodingRate"]] = rendition["defaultURL"] + ' swfVfy=true swfUrl=' + self.urls['swfUrl_PS3']
  else:
   rtmpdata = self.get_clip_info(int(id), 'http://tvnz.co.nz/beyond-the-darklands/s5-ep4-video-5091613')
   for rendition in rtmpdata:
    urls[rendition["encodingRate"]] = rendition["defaultURL"] + ' swfUrl=' + self.urls['swfUrl_PS3']
  return urls

 def _printResponse(self, env, response):
  import pprint
  pp = pprint.PrettyPrinter()
  print "pprint env:"
  pp.pprint(env)
  print "pprint env.bodies:"
  pp.pprint(env.bodies)
  print "pprint response:"
  pp.pprint(response)
  print "pprint programmedContent:"
  pp.pprint(response['programmedContent'])
  print "pprint videoPlayer:"
  pp.pprint(response['programmedContent']['videoPlayer'])
  print "pprint mediaDTO:"
  pp.pprint(response['programmedContent']['videoPlayer']['mediaDTO'])
  print "pprint renditions:"
  pp.pprint(response['programmedContent']['videoPlayer']['mediaDTO']['renditions'])

 def get_clip_info(self, contentID, url):
  import pyamf
  #from pyamf import register_class
  from pyamf import remoting
  import httplib
  conn = httplib.HTTPConnection("c.brightcove.com")
  pyamf.register_class(ViewerExperienceRequest, 'com.brightcove.experience.ViewerExperienceRequest')
  pyamf.register_class(ContentOverride, 'com.brightcove.experience.ContentOverride')
  viewer_exp_req = ViewerExperienceRequest(url, [ContentOverride(contentID)], self.urls['experienceID'], "")
  env = remoting.Envelope(amfVersion = 3)
  env.bodies.append(("/1",  remoting.Request(target = "com.brightcove.experience.ExperienceRuntimeFacade.getDataForExperience", body = [self.urls['const'], viewer_exp_req], envelope = env)))
  #conn.request("POST", "/services/messagebroker/amf?playerKey=" + self.urls['playerKey'], str(remoting.encode(env).read()), {'content-type': 'application/x-amf'})
  conn.request("POST", "/services/messagebroker/amf?playerId=" + self.urls['playerID'], str(remoting.encode(env).read()), {'content-type': 'application/x-amf'})
  resp = conn.getresponse().read()
  response = remoting.decode(resp).bodies[0][1].body
  return response['programmedContent']['videoPlayer']['mediaDTO']['renditions']

 def get_clip_info_ps3(self, contentID):
  import pyamf
  #from pyamf import register_class
  from pyamf import remoting
  import httplib
  conn = httplib.HTTPConnection("c.brightcove.com")
  env = remoting.Envelope(amfVersion = 3)
  env.bodies.append(("/1",  remoting.Request(target = "com.brightcove.player.runtime.PlayerMediaFacade.findMediaByReferenceId", body = [self.urls['const2_PS3'], self.urls['experienceID_PS3'], str(contentID), self.urls['publisherID']], envelope = env)))
  conn.request("POST", "/services/messagebroker/amf?playerKey=" + self.urls['playerKey'], str(remoting.encode(env).read()), {'content-type': 'application/x-amf'})
  resp = conn.getresponse().read()
  response = remoting.decode(resp).bodies[0][1].body
  if self.IOS:
   return response['IOSRenditions']
  else:
   return response['renditions']

 def advert(self, chapter):
  advert = chapter.getElementsByTagName('ref')
  if len(advert):
   # fetch the link - it'll return a .asf file
   page = webpage(advert[0].attributes['src'].value)
   if page.doc:
    xml = self._xml(page.doc)
    if xml:
     # grab out the URL to the actual flash ad
     for flv in xml.getElementsByTagName('FLV'):
      if flv.firstChild and len(flv.firstChild.wholeText):
       return(flv.firstChild.wholeText)

 def _duration(self, dur):
  # Durations are formatted like 0:43:15
  minutes = 0
  parts = dur.split(":")
  if len(parts) == 3:
   try:
    minutes = int(parts[0]) * 60 + int(parts[1])
   except:
    pass
  return str(minutes)

 def _date(self, str):
  import datetime
  # Dates are formatted like 23 Jan 2010.
  # Can't use datetime.strptime as that wasn't introduced until Python 2.6
  formats = ["%d %b %y", "%d %B %y", "%d %b %Y", "%d %B %Y"]
  for format in formats:
   try:
    return datetime.datetime.strptime(str, format).strftime("%d.%m.%Y")
   except:
    pass
  return False

class ContentOverride(object):
 #def __init__(self, contentId = 0, contentType = 0, target = 'videoList'):
 def __init__(self, contentId = 0, contentType = 0, target = 'videoPlayer'):
  self.contentType = contentType
  self.contentId = contentId
  self.target = target
  self.contentIds = None
  self.contentRefId = None
  self.contentRefIds = None
  self.featureId = float(0)
  self.featuredRefId = None

class ViewerExperienceRequest(object):
 def __init__(self, URL, contentOverrides, experienceId, playerKey, TTLToken = ''):
  self.TTLToken = TTLToken
  self.URL = URL
  self.deliveryType = float(0)
  self.contentOverrides = contentOverrides
  #self.contentOverrides = []
  self.experienceId = experienceId
  self.playerKey = playerKey
