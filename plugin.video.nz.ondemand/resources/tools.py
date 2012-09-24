# Generic functions

import sys, re, os
import resources.config as config
settings = config.__settings__
# import xbmc # http://xbmc.sourceforge.net/python-docs/xbmc.html
import xbmcgui # http://xbmc.sourceforge.net/python-docs/xbmcgui.html
import xbmcplugin # http://xbmc.sourceforge.net/python-docs/xbmcplugin.html

#def initaddon:
# import shutil, os
# shutil.rmtree(__cache__)
# os.mkdir(__cache__)

class webpage:
 def __init__(self, url = "", agent = 'ps3', cookie = "", type = ""):
  self.doc = ""
  self.agent = agent
  self.cookie = cookie
  self.type = type
  if url:
   self.url = url
   self.get(url)

 def get(self, url):
  import urllib2
  opener = urllib2.build_opener()
  urllib2.install_opener(opener)
  print "Requesting URL: %s" % (url)
  req = urllib2.Request(url)
  req.add_header('User-agent', self.fullagent(self.agent))
  if self.cookie:
   req.add_header('Cookie', self.cookie)
  if self.type:
   req.add_header('content-type', self.type)
  try:
   response = urllib2.urlopen(req, timeout = 20)
   self.doc = response.read()
   response.close()
  except urllib2.HTTPError, err:
   sys.stderr.write("urllib2.HTTPError requesting URL: %s" % (err.code))
  else:
   return self.doc

 def xml(self):
  from xml.dom import minidom
  #from xml.parsers.expat import ExpatError
  try:
   document = minidom.parseString(self.doc)
   if document:
    self.xmldoc = document.documentElement
    return self.xmldoc
  except: # ExpatError: # Thrown if the content contains just the <xml> tag and no actual content. Some of the TVNZ .xml files are like this :(
   return False

 def html(self):
  from BeautifulSoup import BeautifulSoup
  try:
   return BeautifulSoup(self.doc)
  except:
   pass

 def fullagent(self, agent):
  if agent == "ps3":
   return 'Mozilla/5.0 (PLAYSTATION 3; 3.55)'
  elif agent == 'iphone':
   return 'Mozilla/5.0 (iPhone; U; CPU like Mac OS X; en) AppleWebKit/420+ (KHTML, like Gecko) Version/3.0 Mobile/1C25 Safari/419.3'
  elif agent == 'ipad':
   return 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'
  else: # Chrome
   return 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16'



class xbmcItem:
 def __init__(self):
  self.path = ""
  self.info = dict()
  self.info["Icon"] = "DefaultVideo.png"
  self.info["Thumb"] = ""
  self.playable = False
  self.urls = dict()
  self.units = "kbps"
  self.channel = ""
  self.fanart = ""

 def applyURL(self, bitrate):
  if bitrate in self.urls:
   self.info["FileName"] = self.urls[bitrate]

 def stack(self, urls): #Build a URL stack from multiple URLs for the XBMC player
  if len(urls) == 1:
   return urls[0]
  elif len(urls) > 1:
   return "stack://" + " , ".join([url.replace(',', ',,').strip() for url in urls])
  return False

 def sxe(self):
  if 'Season' in self.info and 'Episode' in self.info:
   return str(self.info["Season"]) + "x" + str(self.info["Episode"]).zfill(2)
  return False

 def unescape(self, s): #Convert escaped HTML characters back to native unicode, e.g. &gt; to > and &quot; to "
  from htmlentitydefs import name2codepoint
  return re.sub('&(%s);' % '|'.join(name2codepoint), lambda m: unichr(name2codepoint[m.group(1)]), s)

 def titleplot(self): #Build a nice title from the program title and sub-title (given as PlotOutline)
  if self.info['PlotOutline']:
   self.info['Title'] = "%s - %s" % (self.info['TVShowTitle'], self.info['PlotOutline'])

 def url(self, urls = False, quality = 'High'): # Low, Medium, High
  if not urls:
   urls = self.urls
  if quality == 'Medium' and len(self.urls) > 2:
   del urls[max(urls.keys())]
  if quality == 'Low':
   return self.stack(urls[min(urls.keys())])
  else:
   return self.stack(urls[max(urls.keys())])

 def encode(self):
  return self._encode(self)

 def infoencode(self):
  return self._encode(self.info)

 def _encode(self, toencode):
  import pickle, urllib
  return urllib.quote(pickle.dumps(toencode))

 def decode(self, item):
  self.bitrates(self._decode(item))

 def infodecode(self, info):
  self.info = self._decode(info)

 def _decode(self, todecode):
  import pickle, urllib
  return pickle.loads(urllib.unquote(todecode))


class xbmcItems:
 def __init__(self, channel = ""):
  self.items = list()
  self.fanart = "fanart.jpg"
  self.channel = ""
  if channel:
   self.channel = channel
   self.fanart = os.path.join('extrafanart', channel + '.jpg')
  self.sorting = ["UNSORTED", "LABEL"] # ALBUM, ALBUM_IGNORE_THE, ARTIST, ARTIST_IGNORE_THE, DATE, DRIVE_TYPE, DURATION, EPISODE, FILE, GENRE, LABEL, LABEL_IGNORE_THE, MPAA_RATING, NONE, PLAYLIST_ORDER, PRODUCTIONCODE, PROGRAM_COUNT, SIZE, SONG_RATING, STUDIO, STUDIO_IGNORE_THE, TITLE, TITLE_IGNORE_THE, TRACKNUM, UNSORTED, VIDEO_RATING, VIDEO_RUNTIME, VIDEO_TITLE, VIDEO_YEAR
  self.type = ""

 def _listitem(self, item):
  if hasattr(item, 'info'):
   listitem = xbmcgui.ListItem(label = item.info["Title"], iconImage = item.info["Icon"], thumbnailImage = item.info["Thumb"])
   try:
    listitem.setProperty('fanart_image', os.path.join(settings.getAddonInfo('path'), item.fanart))
   except:
    listitem.setProperty('fanart_image', os.path.join(settings.getAddonInfo('path'), self.fanart))
   listitem.setInfo(type = "video", infoLabels = item.info)
   return listitem
  else:
   sys.stderr.write("No Item Info")

 def _add(self, item, total = 0): #Add a list item (media file or folder) to the XBMC page
  # http://xbmc.sourceforge.net/python-docs/xbmcgui.html#ListItem
  listitem = self._listitem(item)
  if listitem:
   if item.channel:
    channel = item.channel
   else:
    channel = self.channel
   itemFolder = True
   if item.playable:
    if settings.getSetting('%s_quality_choose' % channel) != 'true':
      itemFolder = False
   if 'FileName' in item.info:
    if not sys.argv[0] in item.info['FileName']:
     itemFolder = False
   else:
    if len(item.urls) > 0:
     if len(item.urls) == 1:
      itemFolder = False
      item.info['FileName'] = item.urls.itervalues().next()
     else:
      if settings.getSetting('%s_quality_choose' % channel) == 'false':
       itemFolder = False
       item.info['FileName'] = self.quality(item.urls, channel)
      else:
       item.info['FileName'] = '%s?item=%s' % (sys.argv[0], item.encode())
   if not itemFolder:
    listitem.setProperty('mimetype', 'video/x-msvideo')
    listitem.setProperty("IsPlayable", "true")
   return xbmcplugin.addDirectoryItem(handle = config.__id__, url = item.info["FileName"], listitem = listitem, isFolder = itemFolder, totalItems = total)

 def addindex(self, index, total = 0):
  self._add(self, self.items[index], total)

 def add(self, total):
  self._add(self.items[-1], total)

 def addall(self):
  total = len(self.items)
  for item in self.items:
   self._add(item, total)
  self.sort()

 def resolve(self, item, channel):
  if settings.getSetting('%s_quality_choose' % channel) == 'true':
   self.bitrates(item)
  else:
   if 'FileName' in item.info:
    self.play(item.info['FileName'])
   else:
    self.play(self.quality(item.urls, channel))

 def play(self, url):
  listitem = xbmcgui.ListItem()
  listitem.setPath(url)
  listitem.setProperty('mimetype', 'video/x-msvideo')
  listitem.setProperty('IsPlayable', 'true')
  try:
   xbmcplugin.setResolvedUrl(handle = config.__id__, succeeded = True, listitem = listitem)
  except:
   pass
   #self.message("Couldn't play item.")

 def bitrates(self, sourceitem):
  total = len(sourceitem.urls)
  for bitrate, url in sourceitem.urls.iteritems():
   item = xbmcItem()
   try:
    item.fanart = sourceitem.fanart
   except:
    pass
   item.info = sourceitem.info.copy()
   item.info['Title'] += " (" + str(bitrate) + " " + sourceitem.units + ")"
   item.info['FileName'] = self.stack(url)
   #item.urls[bitrate] = (self.stack(url))
   self.items.append(item)
  self.addall()

  def itemtobitrates(self, item):
   itemtoitems(decode(item))

 def sort(self):
  import xbmcplugin
  for method in self.sorting:
   xbmcplugin.addSortMethod(handle = config.__id__, sortMethod = getattr(xbmcplugin, "SORT_METHOD_" + method))
   #xbmcplugin.addSortMethod(handle = config.__id__, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
  if self.type:
   xbmcplugin.setContent(handle = config.__id__, content = self.type)
  xbmcplugin.endOfDirectory(config.__id__)

 def search(self):
  import xbmc
  keyboard = xbmc.Keyboard("", "Search for a Video")
  #keyboard.setHiddenInput(False)
  keyboard.doModal()
  if keyboard.isConfirmed():
   return keyboard.getText()
  return False

 def quality(self, urls, channel): # Low, Medium, High
  quality = settings.getSetting('%s_quality' % channel)
  if quality in ['High', 'Medium', 'Low']:
   if len(urls) > 0:
    if quality == 'Medium' and len(urls) > 2:
     del urls[max(urls.keys())]
    if quality == 'Low':
     return self.stack(urls[min(urls.keys())])
    else:
     return self.stack(urls[max(urls.keys())])
  return self.stack(urls[max(urls.keys())])

 def decode(self, item):
  self.bitrates(self._decode(item))

 def _decode(self, todecode):
  import pickle, urllib
  return pickle.loads(urllib.unquote(todecode))

 def stack(self, urls): #Build a URL stack from multiple URLs for the XBMC player
  if str(type(urls)) == "<type 'str'>":
   return urls
  if len(urls) == 1:
   return urls[0]
  elif len(urls) > 1:
   return "stack://" + " , ".join([url.replace(',', ',,').strip() for url in urls])
  return False

 def message(self, message, title = "Warning"): #Show an on-screen message (useful for debugging)
  import xbmcgui
  dialog = xbmcgui.Dialog()
  if message:
   if message != "":
    dialog.ok(title, message)
   else:
    dialog.ok("Message", "Empty message text")
  else:
   dialog.ok("Message", "No message text")

 def log(self, message):
  sys.stderr.write(message)




def xbmcdate(inputdate, separator = "/"): #Convert a date in "%d/%m/%y" format to an XBMC friendly format
 import time, xbmc
 return time.strftime(xbmc.getRegion("datelong").replace("DDDD,", "").replace("MMMM", "%B").replace("D", "%d").replace("YYYY", "%Y").strip(), time.strptime(inputdate, "%d" + separator + "%m" + separator + "%y"))



