#/*
# *   Copyright (C) 2010 Mark Honeychurch
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

import os, sys, urllib, urllib2, htmllib, string, unicodedata, re, time, urlparse, cgi, md5, sha, xbmcgui, xbmcplugin, xbmcaddon

__addon__ = xbmcaddon.Addon(id = sys.argv[0][9:-1])
localize  = __addon__.getLocalizedString

xbmcplugin.setPluginCategory(int(sys.argv[1]), 'CCTV')
#xbmcplugin.setPluginFanart(int(sys.argv[1]), os.path.join(sys.path[0], 'fanart.jpg'))

# Multiple servers
# Cycle?
# Montage?

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

def defaultinfo(folder = 0): #Set the default info for folders (1) and videos (0). Most options have been hashed out as they don't show up in the list and are grabbed from the media by the player
 info = dict()
 if folder:
  info["Icon"] = "DefaultFolder.png"
 else:
  info["Icon"] = "DefaultVideo.png"
  info["VideoCodec"] = "mp4v"
 info["Thumb"] = ""
 return info

def checkdict(info, items): #Check that all of the list "items" are in the dictionary "info"
 for item in items:
  if info.get(item, "##unlikelyphrase##") == "##unlikelyphrase##":
   sys.stderr.write("Dictionary missing item: %s" % (item))
   return 0
 return 1

def addlistitem(info, total = 0, folder = 0): #Add a list item (media file or folder) to the XBMC page
 if checkdict(info, ("Title", "Icon", "Thumb", "FileName")):
  liz = xbmcgui.ListItem(info["Title"], iconImage = info["Icon"], thumbnailImage = info["Thumb"])
  liz.setProperty('fanart_image', os.path.join(sys.path[0], 'fanart.jpg'))
  liz.setInfo(type = "Video", infoLabels = info)
  if not folder:
   liz.setProperty("IsPlayable", "true")
  xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = info["FileName"], listitem = liz, isFolder = folder, totalItems = total)

def calculateaspect(width, height):
 aspect = int(width)/int(height)
 if aspect <= 1.35:
  return "1.33"
 elif aspect <= 1.68:
  return "1.66"
 elif aspect <= 1.80:
  return "1.78"
 elif aspect <= 1.87:
  return "1.85"
 elif aspect <= 2.22:
  return "2.20"
 else:
  return "2.35"

def geturl(path):
 server = __addon__.getSetting('server').strip("/").strip()
 path = path.strip("/").strip()
 url = "http://%s/%s/" % (server, path)
 return url

def mysql_password(str):
 pass1 = sha.new(str).digest()
 pass2 = sha.new(pass1).hexdigest()
 return "*" + pass2.upper()

def mysql_old_password(password):
 nr = 1345345333
 add = 7
 nr2 = 0x12345671
 for c in (ord(x) for x in password if x not in (' ', '\t')):
  nr^= (((nr & 63)+add)*c)+ (nr << 8) & 0xFFFFFFFF
  nr2= (nr2 + ((nr2 << 8) ^ nr)) & 0xFFFFFFFF
  add= (add + c) & 0xFFFFFFFF
 return "%08x%08x" % (nr & 0x7FFFFFFF,nr2 & 0x7FFFFFFF)


def createauthstring():
 authurl = ""
 videoauthurl = ""
 if __addon__.getSetting('auth') == 'true':
  if __addon__.getSetting('hash') == 'true':
   myIP = ""
   if __addon__.getSetting('ip') == 'true':
    if __addon__.getSetting('thisip') == 'true':
     myIP = xbmc.getIPAddress()
    else:
     myIP = __addon__.getSetting('otherip')
   nowtime = time.localtime()
   hashtime = "%s%s%s%s" % (nowtime[3], nowtime[2], nowtime[1] - 1, nowtime[0] - 1900)
   sys.stderr.write("Time (for hash): %s" % hashtime)
   hashable = "%s%s%s%s%s" % (__addon__.getSetting('secret'), __addon__.getSetting('username'), mysql_password(__addon__.getSetting('password')), myIP, hashtime)
   hash = md5.new(hashable).hexdigest()
   authurl = "&auth=%s" % (hash)
   videoauthurl = authurl
  else:
   authurl = "&username=%s&password=%s&action=login" % (__addon__.getSetting('username').strip(), __addon__.getSetting('password').strip())
   videoauthurl = "&user=%s&pass=%s" % (__addon__.getSetting('username').strip(), __addon__.getSetting('password').strip())
 return authurl, videoauthurl
 
def listcameras():
 zmurl = geturl(__addon__.getSetting('zmurl'))
 cgiurl = geturl(__addon__.getSetting('cgiurl'))
 authurl, videoauthurl = createauthstring()
 url = "%s?skin=classic%s" % (zmurl, authurl)
 sys.stderr.write("Grabbing URL: %s" % url)
 doc = gethtmlpage(url)
 match = re.compile('<form name="loginForm"').findall(doc)
 if len(match) > 0:
  sys.stderr.write(localize(30200))
  message(localize(30201), localize(30200))
  __addon__.openSettings(url = sys.argv[0])
  sys.exit()
 else:
  match = re.compile("'zmWatch([0-9]+)', 'watch', ([1-9][0-9]+), ([1-9][0-9]+) \); return\( false \);" + '"' + ">(.*?)</a>").findall(doc)
  if len(match) > 0:
   qualityurl = "&bitrate=%s&maxfps=%s" % (__addon__.getSetting('bitrate'), __addon__.getSetting('fps'))
   for id, width, height, name in match:
    info = defaultinfo()
    info["Title"] = name
    info["VideoResolution"] = width
    info["Videoaspect"] = calculateaspect(width, height)
    info["FileName"] = "%snph-zms?monitor=%s&mode=mpeg&format=asf%s%s" % (cgiurl, id, qualityurl, videoauthurl)
    info["Thumb"] = "%snph-zms?monitor=%s&mode=single%s" % (cgiurl, id, videoauthurl)
    addlistitem(info, len(match), 0)
  else:
   sys.stderr.write(localize(30202))
   message(localize(30202))

listcameras()
xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
xbmcplugin.addSortMethod(handle = int(sys.argv[1]), sortMethod = xbmcplugin.SORT_METHOD_LABEL)
xbmcplugin.endOfDirectory(int(sys.argv[1]))