#/*
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
import os, urllib2, string, re, htmlentitydefs, time, unicodedata

from xml.sax.saxutils import unescape
from xml.dom import minidom
from urllib import quote_plus

__XBMC_Revision__ = xbmc.getInfoLabel('System.BuildVersion')
__settings__      = xbmcaddon.Addon(id='plugin.audio.icecast')
__language__      = __settings__.getLocalizedString
__version__       = __settings__.getAddonInfo('version')
__cwd__           = __settings__.getAddonInfo('path')
__addonname__    = "Icecast"
__addonid__      = "plugin.audio.icecast"
__author__	= "Assen Totin <assen.totin@gmail.com>"
__credits__        = "Team XBMC"

BASE_URL = 'http://dir.xiph.org/yp.xml'

CHUNK_SIZE = 65536

CACHE_FILE_NAME = 'icecast.cache'
TIMESTAMP_FILE_NAME = 'icecast.timestamp'
TIMESTAMP_THRESHOLD = 86400

DB_FILE_NAME = 'icecasl.sqlite'
DB_CREATE_TABLE_STATIONS = 'CREATE TABLE stations (server_name VARCHAR(255), listen_url VARCHAR(255), bitrate VARCHAR(255), genre VARCHAR(255));'
DB_CREATE_TABLE_UPDATES = 'CREATE TABLE updates (unix_timestamp VARCHAR(255));'

# Init function for SQLite
def initSQLite():
  sqlite_file_name = getSQLiteFileName()
  sqlite_con = sqlite.connect(sqlite_file_name)
  sqlite_cur = sqlite_con.cursor()
  try:
    sqlite_cur.execute(DB_CREATE_TABLE_STATIONS)
    sqlite_cur.execute(DB_CREATE_TABLE_UPDATES)
    putTimestampSQLite(sqlite_con, sqlite_cur)
    sqlite_is_empty = 1
  except:
    sqlite_is_empty = 0
  return sqlite_con, sqlite_cur, sqlite_is_empty

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
  if  not os.path.exists(path):
    os.makedirs(path)
  return path

# Compose the cache file name
def getCacheFileName():
  cache_file_dir = getUserdataDir()
  cache_file_name = os.path.join(cache_file_dir,CACHE_FILE_NAME)
  return cache_file_name

# Compose the timestamp file name
def getTimestampFileName():
  cache_file_dir = getUserdataDir()
  timestamp_file_name = os.path.join(cache_file_dir,TIMESTAMP_FILE_NAME)
  return timestamp_file_name

# Compose the SQLite database file name
def getSQLiteFileName():
  cache_file_dir = getUserdataDir()
  db_file_name = os.path.join(cache_file_dir,DB_FILE_NAME)
  return db_file_name

# Read the XML list from IceCast server
def readRemoteXML():
  # Create a dialog
  global dialog_was_canceled
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
  return xml

# Parse XML to DOM
def parseXML(xml):
  dom = minidom.parseString(xml)
  return dom

# Read the XML file form local cache
def readLocalXML():
  cache_file_name = getCacheFileName()
  f = open(cache_file_name,'rb')
  xml = f.read()
  f.close()
  return xml

# Overwrite the local cache
def writeLocalXML(xml):
  cache_file_name = getCacheFileName() 
  f = open(cache_file_name,'wb')
  f.write(xml)
  f.close()

# Populate SQLite table
def DOMtoSQLite(dom, sqlite_con, sqlite_cur):
  sqlite_cur.execute("DELETE FROM stations")
  sqlite_con.commit()

  entries = dom.getElementsByTagName("entry")
  for entry in entries:

    listen_url_objects = entry.getElementsByTagName("listen_url")
    for listen_url_object in listen_url_objects:
      listen_url = getText(listen_url_object.childNodes)
      listen_url = re.sub("'","&apos",listen_url)

    server_name_objects = entry.getElementsByTagName("server_name")
    for server_name_object in server_name_objects:
      server_name = getText(server_name_object.childNodes)
      server_name = re.sub("'","&apos",server_name)

    bitrate_objects = entry.getElementsByTagName("bitrate")
    for bitrate_object in bitrate_objects:
      bitrate = getText(bitrate_object.childNodes)

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

      for genre_name_single in genre_name.split():
        genre_name_single = re.sub("'","&apos",genre_name_single)
        sql_query = "INSERT INTO stations (server_name, listen_url, bitrate, genre) VALUES ('%s','%s','%s','%s')" % (server_name, listen_url, bitrate, genre_name_single)
        sqlite_cur.execute(sql_query)

  sqlite_con.commit()

# Build the list of genres from DOM
def buildGenreListDom(dom):
  genre_hash = {}
  genres = dom.getElementsByTagName("genre")
  for genre in genres:
    genre_name = getText(genre.childNodes)
    for genre_name_single in genre_name.split():
      if genre_hash.has_key(genre_name_single):
        genre_hash[genre_name_single] += 1
      else:
        genre_hash[genre_name_single] = 1
  for key in sorted(genre_hash.keys()):
    addDir(key, genre_hash[key])

# Build the list of genres from SQLite
def buildGenreListSQLite(sqlite_cur):
  sqlite_cur.execute("SELECT genre, COUNT(*) AS cnt FROM stations GROUP BY genre")
  for genre, cnt in sqlite_cur: 
    addDir(genre, cnt)

# Add a genre to the list
def addDir(genre_name, count):
  u = "%s?genre=%s" % (sys.argv[0], genre_name,)
  # Try to unescape HTML-encoding; some strings need two passes - first to convert "&amp;" to "&" and second to unescape "&XYZ;"!
  genre_name = unescapeString(genre_name)
  genre_name_and_count = "%s (%u streams)" % (genre_name, count)
  liz = xbmcgui.ListItem(genre_name_and_count, iconImage="DefaultFolder.png", thumbnailImage="")
  liz.setInfo( type="Music", infoLabels={ "Title": genre_name_and_count,"Size": int(count)} )
  liz.setProperty("IsPlayable","false");
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  return ok

# Build list of links in a given genre from DOM
def buildLinkListDom(dom, genre_name_orig):
  entries = dom.getElementsByTagName("entry")

  for entry in entries:

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

    if genre_name.find(genre_name_orig) > -1 :

      listen_url_objects = entry.getElementsByTagName("listen_url")
      for listen_url_object in listen_url_objects:
        listen_url = getText(listen_url_object.childNodes)

      server_name_objects = entry.getElementsByTagName("server_name")
      for server_name_object in server_name_objects:
        server_name = getText(server_name_object.childNodes)

      bitrate_objects = entry.getElementsByTagName("bitrate")
      for bitrate_object in bitrate_objects:
        bitrate = getText(bitrate_object.childNodes)

      addLink(server_name, listen_url, bitrate)

# Build list of links in a given genre from SQLite
def buildLinkListSQLite(sqlite_cur, genre_name_orig):
  sql_query = "SELECT server_name, listen_url, bitrate FROM stations WHERE genre='%s'" % (genre_name_orig)
  sqlite_cur.execute(sql_query)
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate)

# Add a link inside of a genre list
def addLink(server_name, listen_url, bitrate):
  ok = True
  # Try to unescape HTML-encoding; some strings need two passes - first to convert "&amp;" to "&" and second to unescape "&XYZ;"!
  server_name = unescapeString(server_name)
  listen_url = unescapeString(listen_url)
  # Try to fix all incorrect values for bitrate (remove letters, reset to 0 etc.)
  bitrate = re.sub('\D','',bitrate)
  try: 
    bit = int(bitrate)
  except:
    bit = 0
  u = "%s?play=%s" % (sys.argv[0], listen_url,)
  liz = xbmcgui.ListItem(server_name, iconImage="DefaultVideo.png", thumbnailImage="")
  liz.setInfo( type="Music", infoLabels={ "Title": server_name,"Size": bit} )
  liz.setProperty("IsPlayable","false");
  ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
  return ok

# Get a search query from keyboard
def readKbd():
  kb = xbmc.Keyboard("", __language__(30092), False)
  kb.doModal()
  if (kb.isConfirmed() and len(kb.getText()) > 2):
    return kb.getText()

# Do a search in DOM
def doSearchDom(dom, query):
  entries = dom.getElementsByTagName("entry")

  for entry in entries:

    genre_objects = entry.getElementsByTagName("genre")
    for genre_object in genre_objects:
      genre_name = getText(genre_object.childNodes)

    server_name_objects = entry.getElementsByTagName("server_name")
    for server_name_object in server_name_objects:
      server_name = getText(server_name_object.childNodes)

    if ((genre_name.find(query) > -1) or (server_name.find(query) > -1)) :

      listen_url_objects = entry.getElementsByTagName("listen_url")
      for listen_url_object in listen_url_objects:
        listen_url = getText(listen_url_object.childNodes)

      bitrate_objects = entry.getElementsByTagName("bitrate")
      for bitrate_object in bitrate_objects:
        bitrate = getText(bitrate_object.childNodes)

      addLink(server_name, listen_url, bitrate)

# Do a search in SQLite
def doSearchSQLite(sqlite_cur, query):
  sql_query = "SELECT server_name, listen_url, bitrate FROM stations WHERE (genre LIKE '@@@%s@@@') OR (server_name LIKE '@@@%s@@@')" % (query, query)
  sql_query = re.sub('@@@','%',sql_query)
  sqlite_cur.execute(sql_query)
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate)

# Play a link
def playLink(listen_url):
  log("PLAY URL: %s" % listen_url )   
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
def sort(dir = False):
  if dir:
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
  else:
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X" )
    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X" )
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

# Functions to read and write unix timestamp to database or file
def putTimestampSQLite(sqlite_con, sqlite_cur):
  unix_timestamp = int(time.time())
  sql_line = "INSERT INTO updates (unix_timestamp) VALUES (%u)" % (unix_timestamp)
  sqlite_cur.execute(sql_line)
  sqlite_con.commit()

def putTimestampDom():
  unix_timestamp = int(time.time())
  timestamp_file_name = getTimestampFileName()
  f = open(timestamp_file_name, 'w')
  f.write(str(unix_timestamp))
  f.close()

def getTimestampSQLite(sqlite_cur): 
  sqlite_cur.execute("SELECT unix_timestamp FROM updates ORDER BY unix_timestamp DESC LIMIT 1")
  #unix_timestamp = sqlite_cur.fetchall()
  for unix_timestamp in sqlite_cur:
    return int(unix_timestamp[0])

def getTimestampDom():
  timestamp_file_name = getTimestampFileName()
  try: 
    f = open(timestamp_file_name, 'r')
    unix_timestamp = f.read()
    f.close()
    unix_timestamp = int(unix_timestamp)
  except:
    unix_timestamp = 0
  return unix_timestamp

# Timestamp wrappers
def timestampExpiredSQLite(sqlite_cur):
  current_unix_timestamp = int(time.time())
  saved_unix_timestamp = getTimestampSQLite(sqlite_cur)
  if (current_unix_timestamp - saved_unix_timestamp) > TIMESTAMP_THRESHOLD :
    return 1
  return 0

def timestampExpiredDom():
  current_unix_timestamp = int(time.time())
  saved_unix_timestamp = getTimestampDom()
  if (current_unix_timestamp - saved_unix_timestamp) > TIMESTAMP_THRESHOLD :
    return 1
  return 0

# MAIN 

# SQLite support - if available
try:
  # First, try built-in sqlite in Python 2.5 and newer:
  from sqlite3 import dbapi2 as sqlite
  log_notice("Using built-in SQLite via sqlite3!")
  use_sqlite = 1
except:
  # No luck so far: try the external sqlite
  try:
    from pysqlite2 import dbapi2 as sqlite
    log_notice("Using external SQLite via pysqlite2!")
    use_sqlite = 1
  except: 
    use_sqlite = 0
    log_notice("SQLite not found -- reverting to older (and slower) text cache.")

params=getParams()

try:
  genre = params["genre"]
except:
  genre = "0";
try:
  initial = params["initial"]
except:
  initial = "0";
try:
  play = params["play"]
except:
  play = "0";

igenre = len(genre)
iplay = len(play)
iinitial = len(initial)

dialog_was_canceled = 0

if igenre > 1 :
  if use_sqlite == 1:
    sqlite_con, sqlite_cur, sqlite_is_emtpy = initSQLite()
    timestamp_expired = timestampExpiredSQLite(sqlite_cur)
    if timestamp_expired == 1:
      xml = readRemoteXML()
      if dialog_was_canceled == 0: 
        dom = parseXML(xml)
        DOMtoSQLite(dom, sqlite_con, sqlite_cur)
        putTimestampSQLite(sqlite_con, sqlite_cur)
    buildLinkListSQLite(sqlite_cur, genre)
  else :
    timestamp_expired = timestampExpiredDom()
    if timestamp_expired == 1:
      xml = readRemoteXML()
      if dialog_was_canceled == 0:
        writeLocalXML(xml)
        putTimestampDom()
    else: 
      xml = readLocalXML()
    dom = parseXML(xml)
    buildLinkListDom(dom, genre)
  sort()

elif iinitial > 1:
  if use_sqlite == 1:
    sqlite_con, sqlite_cur, sqlite_is_empty = initSQLite()
    timestamp_expired = timestampExpiredSQLite(sqlite_cur)
    if (sqlite_is_empty == 1) or (timestamp_expired == 1):
      xml = readRemoteXML()
      if dialog_was_canceled == 0:
        dom = parseXML(xml)
        DOMtoSQLite(dom, sqlite_con, sqlite_cur)
        putTimestampSQLite(sqlite_con, sqlite_cur)

  elif use_sqlite == 0:
    timestamp_expired = timestampExpiredDom()
    if timestamp_expired == 1:
      xml = readRemoteXML()
      if dialog_was_canceled == 0:
        writeLocalXML(xml)
        putTimestampDom()
    elif timestamp_expired == 0:
      xml = readLocalXML()
    dom = parseXML(xml)

  if initial == "search":
    query = readKbd()
    if use_sqlite == 1:
      doSearchSQLite(sqlite_cur, query)
    else:
      doSearchDom(dom, query)
    sort()
  elif initial == "list":
    if use_sqlite == 1:
      buildGenreListSQLite(sqlite_cur)
    else:
      buildGenreListDom(dom)
    sort(True)
         
elif iplay > 1:
  playLink(play)
  
else:
  u = "%s?initial=list" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30090), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  u = "%s?initial=search" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30091), iconImage="DefaultFolder.png", thumbnailImage="")
  ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))
