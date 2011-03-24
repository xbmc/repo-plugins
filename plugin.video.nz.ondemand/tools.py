# Generic functions

import sys, re

def message(message, title = "Warning"): #Show an on-screen message (useful for debugging)
 import xbmcgui
 dialog = xbmcgui.Dialog()
 if message:
  if message <> "":
   dialog.ok(title, message)
  else:
   dialog.ok("Message", "Empty message text")
 else:
  dialog.ok("Message", "No message text")

def gethtmlpage(url, useragent = "ie9"): #Grab an HTML page
 import urllib2
 sys.stderr.write("Requesting page: %s" % (url))
 req = urllib2.Request(url)
 newheader = 'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)'
 if useragent == "ps3":
  newheader = 'Mozilla/5.0 (PLAYSTATION 3; 3.55)'
 req.add_header('User-agent', newheader)
 response = urllib2.urlopen(req)
 doc = response.read()
 response.close()
 return doc

def unescape(s): #Convert escaped HTML characters back to native unicode, e.g. &gt; to > and &quot; to "
 from htmlentitydefs import name2codepoint
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
 import time, xbmc
 return time.strftime(xbmc.getRegion( "datelong" ).replace( "DDDD,", "" ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" ).strip(), time.strptime(inputdate,"%d/%m/%y"))

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

# XBMC Manipulation

def addlistitems(id, infoarray, fanart = "fanart.jpg", folder = 0, path = ""):
 total = len(infoarray)
 #total = len(infoarray.viewkeys())
 i = 0
 #for listitem in infoarray:
 for listkey, listitem in infoarray.items():
  #listitem["Count"] = i
  i += 1
  addlistitem(id, listitem, fanart, folder, total, path)

def addlistitem(id, info, fanart = "fanart.jpg", folder = 0, total = 0, path = ""): #Add a list item (media file or folder) to the XBMC page
 import xbmcgui, xbmcplugin, xbmcaddon, os
 liz = xbmcgui.ListItem(info["Title"], iconImage = info["Icon"], thumbnailImage = info["Thumb"])
 addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])
 liz.setProperty('fanart_image', os.path.join(addon.getAddonInfo('path'), fanart))
 liz.setInfo(type = "Video", infoLabels = info)
 if not folder:
  liz.setProperty("IsPlayable", "true")
 if path == "":
  if xbmcplugin.addDirectoryItem(handle = id, url = info["FileName"], listitem = liz, isFolder = folder, totalItems = total):
   return 1
  else:
   return 0
 else:
  liz.setPath(path)
  try:
   xbmcplugin.setResolvedUrl(handle = id, succeeded = True, listitem = liz)
  except:
   message("Boo, couldn't play.")
    


def addsorting(id, methods, mediacontent = ""):
 import xbmcplugin
 for method in methods:
  if method == "unsorted":
   xbmcplugin.addSortMethod(handle = id, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
  elif method == "count":
   xbmcplugin.addSortMethod(handle = id, sortMethod = xbmcplugin.SORT_METHOD_PROGRAM_COUNT)
  elif method == "date":
   xbmcplugin.addSortMethod(handle = id, sortMethod = xbmcplugin.SORT_METHOD_DATE)
  elif method == "label":
   xbmcplugin.addSortMethod(handle = id, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
  elif method == "runtime":
   xbmcplugin.addSortMethod(handle = id, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_RUNTIME)
  elif method == "episode":
   xbmcplugin.addSortMethod(handle = id, sortMethod = xbmcplugin.SORT_METHOD_EPISODE)
 if mediacontent <> "":
  xbmcplugin.setContent(handle = id, content = mediacontent)
 xbmcplugin.endOfDirectory(id)

