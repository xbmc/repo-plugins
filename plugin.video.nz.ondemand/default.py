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

import os, cgi, sys, tools, urlparse, urllib, xbmcaddon

# Setup global variables

addon = xbmcaddon.Addon(id = sys.argv[0][9:-1])
localize = addon.getLocalizedString











def INDEX():
 channels = dict()
 channels["0"] = "TV3"
 channels["1"] = "TVNZ"
 if addon.getSetting('Ziln_hide') == "false":
  channels["2"] = "Ziln"
 #channels["3"] = "iSKY"
# streamingchannels = dict()
# streamingchannels["0"] = "Shine"
# streamingchannels["1"] = "Parliament"
 count = len(channels) + 1 #+ len(streamingchannels)
 for index in channels:
  info = tools.defaultinfo(1)
  info["Title"] = channels[index]
  info["Thumb"] = os.path.join(addon.getAddonInfo('path'), "resources/images/%s.png" % channels[index])
  info["Count"] = int(index)
  info["FileName"] = "%s?ch=%s" % (sys.argv[0], channels[index])
  tools.addlistitem(int(sys.argv[1]), info, "resources/images/%s.jpg" % channels[index], 1, count)
 if addon.getSetting('Parliament_hide') == "false":
  import parliament
  parliament.RESOLVE("Parliament", count)
 if addon.getSetting('Shine_hide') == "false":
  import shine
  shine.RESOLVE("Shine", count)

# Decide what to run based on the plugin URL

params = cgi.parse_qs(urlparse.urlparse(sys.argv[2])[4])
if params:
 if params["ch"][0] == "TV3":
  import tv3
  if params.get("folder", "") <> "":
   tv3.INDEX_FOLDER(params["folder"][0])
   tools.addsorting(int(sys.argv[1]), ["unsorted", "label"])
  elif params.get("cat", "") <> "":
   if params["cat"][0] == "tv":
    tv3.SHOW_EPISODES(params["catid"][0], "tv3")
    tools.addsorting(int(sys.argv[1]), ["unsorted", "date", "label", "runtime", "episode"], "episodes")
   elif params["cat"][0] == "atoz":
    tv3.SHOW_ATOZ(params["catid"][0], "tv3")
    tools.addsorting(int(sys.argv[1]), ["unsorted", "date", "label", "runtime", "episode"], "tvshows")
   elif params["cat"][0] == "tv3":
    tv3.SHOW_EPISODES(params["catid"][0], "tv3")
    tools.addsorting(int(sys.argv[1]), ["unsorted", "date", "label", "runtime", "episode"], "episodes")
   elif params["cat"][0] == "c4tv":
    tv3.SHOW_EPISODES(params["catid"][0], "c4tv")
    tools.addsorting(int(sys.argv[1]), ["unsorted", "date", "label", "runtime", "episode"], "episodes")
   elif params["cat"][0] == "shows":
    tv3.SHOW_SHOW(urllib.unquote(params["catid"][0]), urllib.unquote(params["title"][0]), "tv3")
    tools.addsorting(int(sys.argv[1]), ["unsorted", "date", "label", "runtime", "episode"], "episodes")
  elif params.get("id", "") <> "":
   tv3.RESOLVE(params["id"][0], eval(urllib.unquote(params["info"][0])))
  else:
   if addon.getSetting('TV3_folders') == 'true':
    tv3.INDEX_FOLDERS()
   else:
    tv3.INDEX("tv3")
   tools.addsorting(int(sys.argv[1]), ["unsorted", "label"])
 elif params["ch"][0] == "TVNZ":
  import tvnz
  if params.get("type", "") <> "":
   if params["type"][0] == "shows":
    tvnz.EPISODE_LIST(params["id"][0])
    tools.addsorting(int(sys.argv[1]), ["label"], "episodes")
   elif params["type"][0] == "singleshow":
    tvnz.SHOW_EPISODES(params["id"][0])
    tools.addsorting(int(sys.argv[1]), ["date"], "episodes")
   elif params["type"][0] == "alphabetical":
    tvnz.SHOW_LIST(params["id"][0])
    tools.addsorting(int(sys.argv[1]), ["label"], "tvshows")
   elif params["type"][0] == "distributor":
    tvnz.SHOW_DISTRIBUTORS(params["id"][0])
    tools.addsorting(int(sys.argv[1]), ["label"], "tvshows")
   elif params["type"][0] == "video":
    tvnz.RESOLVE(params["id"][0], eval(urllib.unquote(params["info"][0])))
  else:
   tvnz.INDEX()
   tools.addsorting(int(sys.argv[1]), ["label"])
 elif params["ch"][0] == "Ziln":
  import ziln
  if params.get("folder", "") <> "":
   if params["folder"][0] == "channels":
    ziln.PROGRAMMES("channel", "")
    tools.addsorting(int(sys.argv[1]), ["label"])
   elif params["folder"][0] == "search":
    ziln.SEARCH()
    tools.addsorting(int(sys.argv[1]), ["label"])
  elif params.get("channel", "") <> "":
   ziln.PROGRAMMES("video", params["channel"][0])
   tools.addsorting(int(sys.argv[1]), ["label"])
  elif params.get("video", "") <> "":
   ziln.RESOLVE(params["video"][0]) #, eval(urllib.unquote(params["info"][0]))
   tools.addsorting(int(sys.argv[1]), ["label"])
  else:
   ziln.INDEX()
   tools.addsorting(int(sys.argv[1]), ["label"])
 elif params["ch"][0] == "Shine":
  import shine
  shine.RESOLVE(params["ch"][0])
# elif params["ch"][0] == "Parliament":
#  import parliament
#  parliament.RESOLVE(params["ch"][0], eval(urllib.unquote(params["info"][0])))
# elif params["ch"][0] == "iSKY":
#  import isky
#  isky.INDEX()
 else:
  sys.stderr.write("Invalid Channel ID")
else:
 INDEX()
 tools.addsorting(int(sys.argv[1]), ["unsorted", "label"])