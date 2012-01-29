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

import xbmcgui, xbmcplugin, xbmcaddon

from icecast_common import *
from icecast_init import *

__settings__  = xbmcaddon.Addon(id='plugin.audio.icecast')
__language__  = __settings__.getLocalizedString
__addonname__ = "Icecast"
__addonid__   = "plugin.audio.icecast"
__author__    = "Assen Totin <assen.totin@gmail.com>"
__credits__   = "Team XBMC"

sqlite_con, sqlite_cur, sqlite_is_empty, use_sqlite = initSQLite()

params=getParams()

try:
  mode = params["mode"]
except:
  mode = 0

try:
  mod_recent = params["mod_recent"]
except:
  mod_recent = 0

try:
  setting = params["setting"]
except:
  setting = 0

try:
  fav_action = params["fav_action"]
except:
  fav_action = 0

if use_sqlite == 1:
  from icecast_sql import *
  timestamp_expired = timestampExpired(sqlite_cur)
  if (sqlite_is_empty == 1) or (timestamp_expired == 1):
    xml, dialog_was_canceled = readRemoteXML()
    if dialog_was_canceled == 0:
      dom = parseXML(xml)
      DOMtoSQLite(dom, sqlite_con, sqlite_cur)
      putTimestamp(sqlite_con, sqlite_cur)

elif use_sqlite == 0:
  from icecast_dom import * 
  timestamp_expired = timestampExpired()
  if timestamp_expired == 1:
    xml, dialog_was_canceled = readRemoteXML()
    if dialog_was_canceled == 0:
      writeLocalXML(xml)
      putTimestamp()
  elif timestamp_expired == 0:
    xml = readLocalXML()
  dom = parseXML(xml)

# Mode selector
if mode == "search":
  query = readKbd()
  if use_sqlite == 1:
    doSearch(sqlite_cur, query)
  else:
    doSearch(dom, query)
  sort()

elif mode == "list":
  if use_sqlite == 1:
    buildGenreList(sqlite_cur)
  else:
    buildGenreList(dom)
  sort(True)

elif mode == "genre":
  if use_sqlite == 1:
    timestamp_expired = timestampExpired(sqlite_cur)
    if timestamp_expired == 1:
      xml, dialog_was_canceled = readRemoteXML()
      if dialog_was_canceled == 0:
        dom = parseXML(xml)
        DOMtoSQLite(dom, sqlite_con, sqlite_cur)
        putTimestamp(sqlite_con, sqlite_cur)
    buildLinkList(sqlite_cur, params["genre"])
  else:
    timestamp_expired = timestampExpired()
    if timestamp_expired == 1:
      xml, dialog_was_canceled = readRemoteXML()
      if dialog_was_canceled == 0:
        writeLocalXML(xml)
        putTimestamp()
    else:
      xml = readLocalXML()
    dom = parseXML(xml)
    buildLinkList(dom, params["genre"])
  sort()

elif mode == "settings":
  if setting != 0:
    updateSettings(sqlite_con, sqlite_cur, setting, params["val"])
  showSettings(sqlite_cur, setting)

elif mode == "recent":
  showRecent(sqlite_cur)
  sort()

elif mode == "favourites":
  if fav_action == "open":
    showFavourite(sqlite_cur, params["url"])
  elif fav_action == "remove":
    delFavourite(sqlite_con, sqlite_cur, params["url"])
  elif fav_action == "add":
    addFavourite(sqlite_con, sqlite_cur, params["url"])
  else:
    fav_msg = favMessage(sqlite_cur)
    if fav_msg == 1:
      dialog = xbmcgui.Dialog()
      dialog.ok(__language__(30098), __language__(30105))
    elif fav_msg == 2:
      dialog = xbmcgui.Dialog()
      dialog.ok(__language__(30098), __language__(30106))
    else:
      showFavourites(sqlite_cur)  

elif mode == "play":
  if use_sqlite == 1:
    if fav_action == "open":
      # Add a 'play' link
      bitrate = getBitrate(sqlite_cur, params["url"])
      addLink(__language__(30101), params["url"], bitrate, 0)
      # Add a 'add to favourites' link
      u = "%s?mode=favourites&url=%s&fav_action=add" % (sys.argv[0], params["url"])
      liz = xbmcgui.ListItem(__language__(30099), iconImage="DefaultAudio.png", thumbnailImage="")
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
      sortUnsorted()
      #xbmcplugin.endOfDirectory(int(sys.argv[1]))
    else:
      if mod_recent == 0:
        addRecent(sqlite_con, sqlite_cur, params["url"])
      playLink(params["url"])
  else:
    playLink(params["url"])

else:
  u = "%s?mode=list" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30090), iconImage="DefaultMusicGenres.png", thumbnailImage="")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  u = "%s?mode=search" % (sys.argv[0],)
  liz=xbmcgui.ListItem(__language__(30091), iconImage="DefaultFolder.png", thumbnailImage="")
  xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  if use_sqlite == 1:
    u = "%s?mode=recent" % (sys.argv[0],)
    liz=xbmcgui.ListItem(__language__(30104), iconImage="DefaultMusicRecentlyPlayed.png", thumbnailImage="")
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

    u = "%s?mode=favourites" % (sys.argv[0])
    liz=xbmcgui.ListItem(__language__(30098), iconImage="DefaultMusicPlaylists.png", thumbnailImage="")
    fav_msg = favMessage(sqlite_cur)
    if fav_msg == 0:
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    else:
      xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)

    u = "%s?mode=settings" % (sys.argv[0],)
    liz=xbmcgui.ListItem(__language__(30095), iconImage="DefaultAddonMusic.png", thumbnailImage="")
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

  xbmcplugin.endOfDirectory(int(sys.argv[1]))

