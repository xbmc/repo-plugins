# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import os, urllib2
import re, htmlentitydefs, time, unicodedata, sys

from xml.sax.saxutils import unescape
from xml.dom import minidom

__settings__   = xbmcaddon.Addon(id='plugin.audio.icecast')
__language__   = __settings__.getLocalizedString
__addonname__  = "Icecast"

TIMESTAMP_THRESHOLD = 86400
BASE_URL = 'http://dir.xiph.org/yp.xml'
CHUNK_SIZE = 65536

# Parse XML to DOM
def parseXML(xml):
  dom = minidom.parseString(xml)
  return dom

# Parse XML line
def getText(nodelist):
  rc = []
  for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
      rc.append(node.data)
  return ''.join(rc)

# Obtain the full path of "userdata/add_ons" directory
def getUserdataDir():
  path = xbmc.translatePath(__settings__.getAddonInfo('profile'))
  if not os.path.exists(path):
    os.makedirs(path)
  return path

# Read the XML list from IceCast server
def readRemoteXML():
  # Create a dialog
  dialog_was_canceled = 0
  dialog = xbmcgui.DialogProgress()
  dialog.create(__language__(30093), __language__(30094))
  dialog.update(1)

  # Download in chunks of CHUNK_SIZE, update the dialog
  # URL progress bar code taken from triptych (http://stackoverflow.com/users/43089/triptych):
  # See original code http://stackoverflow.com/questions/2028517/python-urllib2-progress-hook
  response = urllib2.urlopen(BASE_URL);
  total_size = response.info().getheader('Content-Length').strip()
  total_size = int(total_size)
  bytes_so_far = 0
  str_list = []
  xml = ''

  while 1:
    chunk = response.read(CHUNK_SIZE)
    bytes_so_far += len(chunk)

    if not chunk: break

    if (dialog.iscanceled()):
      dialog_was_canceled = 1
      break

    # There are two a bit faster ways to do this: pseudo files (not sure how portable?) and list comprehensions (lazy about it).
    # As the performance penalty is not that big, I'll stay with the more straightforward: list + join
    str_list.append(chunk)

    percent = float(bytes_so_far) / total_size
    val = int(percent * 100)
    dialog.update(val)

  response.close()

  if dialog_was_canceled == 0:
    xml = ''.join(str_list)
    dialog.update(100)
    time.sleep(1)

  dialog.close
  return xml, dialog_was_canceled

# Add a genre to the list
def addDir(genre_name, count):
  u = "%s?mode=genre&genre=%s" % (sys.argv[0], genre_name)
  # Try to unescape HTML-encoding; some strings need two passes - first to convert "&amp;" to "&" and second to unescape "&XYZ;"!
  genre_name = unescapeString(genre_name)
  genre_name_and_count = "%s (%u streams)" % (genre_name, count)
  liz = xbmcgui.ListItem(genre_name_and_count, iconImage="DefaultFolder.png", thumbnailImage="")
  liz.setInfo( type="Music", infoLabels={ "Title": genre_name_and_count,"Size": int(count)} )
  liz.setProperty("IsPlayable","false");
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

# Add a link inside of a genre list
def addLink(server_name, listen_url, bitrate, from_recent):
  # Try to unescape HTML-encoding; some strings need two passes - first to convert "&amp;" to "&" and second to unescape "&XYZ;"!
  server_name = unescapeString(server_name)
  listen_url = unescapeString(listen_url)
  # Try to fix all incorrect values for bitrate (remove letters, reset to 0 etc.)
  bitrate = re.sub('\D','',bitrate)
  try: 
    bit = int(bitrate)
  except:
    bit = 0
  if from_recent == 1:
    u = "%s?mode=play&url=%s&mod_recent=1" % (sys.argv[0], listen_url)
  else :
    u = "%s?mode=play&url=%s" % (sys.argv[0], listen_url)
  liz = xbmcgui.ListItem(server_name, iconImage="DefaultAudio.png", thumbnailImage="")
  liz.setInfo(type="Music", infoLabels={ "Title":server_name, "Size":bit})
  liz.setProperty("IsPlayable","false");
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)

# Get a search query from keyboard
def readKbd():
  kb = xbmc.Keyboard("", __language__(30092), False)
  kb.doModal()
  if (kb.isConfirmed() and len(kb.getText()) > 2):
    return kb.getText()

# Play a link
def playLink(listen_url):
  log("PLAY URL: %s" % listen_url)   
  xbmc.Player().play(listen_url)

# Read command-line parameters
def getParams():
  param=[]
  paramstring=sys.argv[2]
  if len(paramstring)>=2:
    params=sys.argv[2]
    cleanedparams=params.replace('?','')
    if (params[len(params)-1]=='/'):
      params=params[0:len(params)-2]
    pairsofparams=cleanedparams.split('&')
    param={}
    for i in range(len(pairsofparams)):
      splitparams={}
      splitparams=pairsofparams[i].split('=')
      if (len(splitparams))==2:
        param[splitparams[0]]=splitparams[1]
  return param

# Logging
def log(msg):
  xbmc.log("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGDEBUG )

# Log NOTICE
def log_notice(msg):
  xbmc.log("### [%s] - %s" % (__addonname__,msg,),level=xbmc.LOGNOTICE )
 
# Sorting
def sort(dir=False):
  if dir:
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_SIZE)
  else:
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X")
  xbmcplugin.endOfDirectory(int(sys.argv[1]))        

def sortUnsorted(dir=False):
  if dir:
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED)
  else:
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_UNSORTED, label2Mask="%X")
  xbmcplugin.endOfDirectory(int(sys.argv[1]))

# Unescape escaped HTML characters
def unescapeHTML(text):
  def fixup(m):
    text = m.group(0)
    if text[:2] == "&#":
      # character reference
      try:
        if text[:3] == "&#x":
          return unichr(int(text[3:-1], 16))
        else:
          return unichr(int(text[2:-1]))
      except ValueError:
        pass
    else:
      # named entity
      try:
        text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
      except KeyError:
        pass
    return text # leave as is
  # Try to avoid broken UTF-8
  try:
    text = unicode(text, 'utf-8')
    ret = re.sub("&#?\w+;", fixup, text)
  except: 
    ret = text
  return ret

def unescapeXML(text):
  try:
    ret = unescape(text, {"&apos;": "'", "&quot;": '"'})
  except:
    ret = text
  return ret

# Unesacpe wrapper
def unescapeString(text):
  pass1 = unescapeHTML(text)
  pass2 = unescapeHTML(pass1)
  pass3 = unescapeXML(pass2)
  return pass3


