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

import xbmcaddon, xbmcgui, xbmcplugin
import time

from xml.dom import minidom

from icecast_common import * 

__settings__  = xbmcaddon.Addon(id='plugin.audio.icecast')
__language__  = __settings__.getLocalizedString

# Show settings menu (SQL version only)
def showSettings(sqlite_cur, update_listing):
  settings_hash = {}
  val_new = 0
  txt = ''
  sqlite_cur.execute("SELECT name, val FROM settings")
  for name, val in sqlite_cur:
    settings_hash[name] = val

  # Favourites: 30098
  if settings_hash.has_key('30098'):
    if settings_hash['30098'] == '1':
      txt = "%s %s" % (__language__(30097),__language__(30098))
      val_new = 0
    elif settings_hash['30098'] == '0':
      txt = "%s %s" % (__language__(30096), __language__(30098))
      val_new = 1

    u = "%s?mode=settings&setting=%s&val=%s" % (sys.argv[0], '30098', val_new)
    liz = xbmcgui.ListItem(txt, iconImage="DefaultAddonMusic.png", thumbnailImage="")
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  if update_listing == 0:
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
  else:
    xbmcplugin.endOfDirectory(int(sys.argv[1]), updateListing=True)

def updateSettings(sqlite_con, sqlite_cur, settings, val):
  sql_query = "UPDATE settings SET val=%s WHERE name=%s" % (val, settings)
  sqlite_cur.execute(sql_query)
  sqlite_con.commit()

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

# Build the list of genres from SQLite
def buildGenreList(sqlite_cur):
  sqlite_cur.execute("SELECT genre, COUNT(*) AS cnt FROM stations GROUP BY genre")
  for genre, cnt in sqlite_cur: 
    addDir(genre, cnt)

# Build list of links in a given genre from SQLite
def buildLinkList(sqlite_cur, genre):
  fav_enabled = isFavEnabled(sqlite_cur)
  sql_query = "SELECT server_name, listen_url, bitrate FROM stations WHERE genre='%s' GROUP BY listen_url" % (genre)
  sqlite_cur.execute(sql_query)
  for server_name, listen_url, bitrate in sqlite_cur:
    if fav_enabled == 0:
      addLink(server_name, listen_url, bitrate, 0)
    else:
      u = "%s?mode=play&url=%s&fav_action=open" % (sys.argv[0], listen_url)
      liz = xbmcgui.ListItem(server_name, iconImage="DefaultFolder.png", thumbnailImage="")
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

# Build list of links - recently played
def showRecent(sqlite_cur):
  sqlite_cur.execute("SELECT server_name, listen_url, bitrate FROM recent ORDER BY unix_timestamp DESC LIMIT 20")
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate, 1)

# Add recentrly played entry
def addRecent(sqlite_con, sqlite_cur, listen_url):
  unix_timestamp = int(time.time())
  sql_query = "INSERT INTO recent (server_name, listen_url, bitrate, genre, unix_timestamp) SELECT server_name, listen_url, bitrate, genre,'%s' FROM stations WHERE listen_url='%s' LIMIT 1" % (unix_timestamp, listen_url)
  sqlite_cur.execute(sql_query)
  sqlite_con.commit()

# Is 'favourites' setting on or off?
def isFavEnabled(sqlite_cur):
  sqlite_cur.execute("SELECT val FROM settings WHERE name='30098'")
  for val in sqlite_cur:
    return int(val[0])

# Can we show favourites, or shoudl we show a help message?
def favMessage(sqlite_cur):
  fav_enabled = isFavEnabled(sqlite_cur)
  sqlite_cur.execute("SELECT COUNT(*) AS cnt FROM favourites")
  for cnt in sqlite_cur:
    counter = int(cnt[0])
  if (fav_enabled == 0) and (counter == 0):
    return 1
  elif (fav_enabled == 1) and (counter == 0):
    return 2 
  else:
    return 0

# Build list of links - favourites
def showFavourites(sqlite_cur):
  fav_enabled = isFavEnabled(sqlite_cur)
  sqlite_cur.execute("SELECT server_name, listen_url, bitrate FROM favourites")
  for server_name, listen_url, bitrate in sqlite_cur:
    if fav_enabled == 0:
      addLink(server_name, listen_url, bitrate, 0)
    else:
      u = "%s?mode=favourites&url=%s&fav_action=open" % (sys.argv[0], listen_url)
      liz = xbmcgui.ListItem(server_name, iconImage="DefaultFolder.png", thumbnailImage="")
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
  if fav_enabled == 0:
    sort()
  else:
    sort(True)

# Show one favourite
def showFavourite(sqlite_cur, listen_url):
  fav_enabled = isFavEnabled(sqlite_cur)
  sql_query = "SELECT server_name, bitrate FROM favourites WHERE listen_url='%s'" % (listen_url)
  sqlite_cur.execute(sql_query)
  for server_name, bitrate in sqlite_cur:
    if fav_enabled == 0:
      addLink(server_name, listen_url, bitrate, 0)
    else:
      # Add a 'play' link
      addLink(__language__(30101), listen_url, bitrate, 0)
      # Add a 'remove' link
      u = "%s?mode=favourites&url=%s&fav_action=remove" % (sys.argv[0], listen_url)
      liz = xbmcgui.ListItem(__language__(30100), iconImage="DefaultAudio.png", thumbnailImage="")
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
  if fav_enabled == 0:
    sort()
  else:
    sortUnsorted()

# Add favourite to DB
def addFavourite(sqlite_con, sqlite_cur, listen_url):
  sql_query = "SELECT COUNT(*) AS cnt FROM favourites WHERE listen_url='%s'" % (listen_url)
  sqlite_cur.execute(sql_query)
  for cnt in sqlite_cur:
    res = int(cnt[0])
  if res == 0:
    sql_query = "INSERT INTO favourites (server_name, listen_url, bitrate, genre) SELECT server_name, listen_url, bitrate, genre FROM stations WHERE listen_url='%s'" % (listen_url)
    sqlite_cur.execute(sql_query)
    sqlite_con.commit()
  dialog = xbmcgui.Dialog()
  dialog.ok(__language__(30099), __language__(30102))

# Remove favourite from DB
def delFavourite(sqlite_con, sqlite_cur, listen_url):
  sql_query = "DELETE FROM favourites WHERE listen_url='%s'" % (listen_url)
  sqlite_cur.execute(sql_query)
  sqlite_con.commit()
  dialog = xbmcgui.Dialog()
  dialog.ok(__language__(30100), __language__(30102))

# Do a search in SQLite
def doSearch(sqlite_cur, query):
  sql_query = "SELECT server_name, listen_url, bitrate FROM stations WHERE (genre LIKE '@@@%s@@@') OR (server_name LIKE '@@@%s@@@')" % (query, query)
  sql_query = re.sub('@@@','%',sql_query)
  sqlite_cur.execute(sql_query)
  for server_name, listen_url, bitrate in sqlite_cur:
    addLink(server_name, listen_url, bitrate, 0)

# Get bitrate by URL
def getBitrate(sqlite_cur, listen_url):
  sql_query = "SELECT bitrate FROM stations WHERE listen_url='%s'" % (listen_url)
  sqlite_cur.execute(sql_query)
  for bitrate in sqlite_cur:
    return bitrate[0]

# Functions to read and write unix timestamp to database or file
def putTimestamp(sqlite_con, sqlite_cur):
  unix_timestamp = int(time.time())
  sql_line = "INSERT INTO updates (unix_timestamp) VALUES (%u)" % (unix_timestamp)
  sqlite_cur.execute(sql_line)
  sqlite_con.commit()

def getTimestamp(sqlite_cur): 
  sqlite_cur.execute("SELECT unix_timestamp FROM updates ORDER BY unix_timestamp DESC LIMIT 1")
  #unix_timestamp = sqlite_cur.fetchall()
  for unix_timestamp in sqlite_cur:
    return int(unix_timestamp[0])

# Timestamp wrappers
def timestampExpired(sqlite_cur):
  current_unix_timestamp = int(time.time())
  saved_unix_timestamp = getTimestamp(sqlite_cur)
  if (current_unix_timestamp - saved_unix_timestamp) > TIMESTAMP_THRESHOLD :
    return 1
  return 0

