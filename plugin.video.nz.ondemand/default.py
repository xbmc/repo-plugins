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

import os, cgi, sys, urlparse, urllib
import xbmcaddon, xbmcgui, xbmcplugin

import resources.tools as tools
import resources.config as config

#tools.initaddon()

settings = config.__settings__


def tv3():
 from resources.channels.tv3 import tv3 as tv3class
 tv3 = tv3class()
 if params.get("folder", "") != "":
  tv3.folderindex(params["folder"][0])
 elif params.get("cat", "") != "":
  if params["cat"][0] == "tv":
   tv3.episodes(params["catid"][0], "tv3")
  elif params["cat"][0] == "atoz":
   tv3.atoz(params["catid"][0], "tv3")
  elif params["cat"][0] == "tv3":
   tv3.episodes(params["catid"][0], "tv3")
  elif params["cat"][0] == "four":
   tv3.episodes(params["catid"][0], "four")
  elif params["cat"][0] == "shows":
   tv3.show(urllib.unquote(params["catid"][0]), urllib.unquote(params["title"][0]), "tv3")
 elif params.get("id", "") != "":
  tv3.play(params["id"][0], params["provider"][0], params["info"][0])
 else:
  if config.__settings__.getSetting('TV3_folders') == 'true':
   tv3.index()
  else:
   tv3.index(False)

def tvnz():
 from resources.channels.tvnz import tvnz as tvnzclass
 tvnz = tvnzclass()
 if params.get("info", "") != "":
  tvnz.play(params["id"][0], params["info"][0])
 elif not "type" in params:
  tvnz.index()
 else:
  if params["type"][0] == "shows":
   tvnz.episodes(params["id"][0])
  elif params["type"][0] == "singleshow":
   tvnz.episodes(params["id"][0])
  elif params["type"][0] == "alphabetical":
   tvnz.show(params["id"][0])
  elif params["type"][0] == "distributor":
   tvnz.SHOW_DISTRIBUTORS(params["id"][0])
   tools.addsorting(["label"], "tvshows")
  elif params["type"][0] == "search":
   tvnz.search()

def choicetv():
 from resources.channels.choicetv import choicetv as choicetvclass
 choicetv = choicetvclass()
 if params.get("type", "") != "":
  choicetv.index(params["type"][0], params["id"][0])
 elif params.get("view", "") != "":
  choicetv.play(params["view"][0])
 else:
  choicetv.index()

def ziln():
 from resources.channels.ziln import ziln as zilnclass
 ziln = zilnclass()
 if params.get("folder", "") != "":
  if params["folder"][0] == "channels":
   ziln.programmes("channel", "")
  elif params["folder"][0] == "search":
   ziln.search()
 elif params.get("channel", "") != "":
  ziln.programmes("video", params["channel"][0])
 elif params.get("video", "") != "":
  ziln.play(params["video"][0])
 else:
  ziln.index()

def nzonscreen():
 from resources.channels.nzonscreen import nzonscreen as nzonscreenclass
 nzonscreen = nzonscreenclass()
 if params.get("page", "") != "":
  nzonscreen.page(urllib.unquote(params["filter"][0]), params["page"][0])
 elif params.get("filter", "") != "":
  if params["filter"][0] == "search":
   nzonscreen.search()
  else:
   nzonscreen.index(urllib.unquote(params["filter"][0]))
 elif params.get("bitrates", "") != "":
  nzonscreen.bitrates(params["bitrates"][0])
 elif params.get("title", "") != "":
  nzonscreen.play(params["title"][0], params["info"][0])
 else:
  nzonscreen.index()



# Decide what to run based on the plugin URL

params = cgi.parse_qs(urlparse.urlparse(sys.argv[2])[4])
if params:
 if params.get("item", "") != "":
  xbmcitems = tools.xbmcItems()
  xbmcitems.decode(params["item"][0])
 else:
  if params["ch"][0] == "TV3":
   tv3()
  elif params["ch"][0] == "TVNZ":
   tvnz()
  elif params["ch"][0] == "ChoiceTV":
   choicetv()
  elif params["ch"][0] == "Ziln":
   ziln()
  elif params["ch"][0] == "NZOnScreen":
   nzonscreen()
# elif params["ch"][0] == "iSKY":
# https://www.skytv.co.nz/skyid/rest/login?skin=isky
# POST:
# email
# password
# elif params["ch"][0] == "Quickflix":
# https://secure.quickflix.co.nz/Partial/Secure/Standard/Login
# POST:
# LoginEmail
# LoginPassword
# elif params["ch"][0] == "IGLOO":
  elif params["ch"][0] == "Prime":
   from resources.channels.prime import prime as primeclass
   prime = primeclass()
  else:
   sys.stderr.write("Invalid Channel ID")
else:
 channels = dict()
 channels["TV3"] = "Latest TV On Demand video from both TV3 and FOUR."
 #channels["TVNZ"] = "Ready when you are."
 channels["Prime"] = "Prime News: First At 5:30 brings you the top news and sports stories from New Zealand and around the world."
 channels["NZOnScreen"] = "The online showcase of New Zealand television, film and music video."
 channels["Ziln"] = "Ziln links the audience reach of broadband internet with a potentially limitless amount of targetted live streaming and View On Demand TV/video content."
 channels["ChoiceTV"] = "Choice TV's programming centres on entertainment, information and lifestyle content from around the world."
 xbmcitems = tools.xbmcItems()
 for channel, description in channels.iteritems():
  if not settings.getSetting('%s_hide' % channel) == "true":
   item = tools.xbmcItem()
   item.fanart = os.path.join('extrafanart', "%s.jpg" % channel)
   item.info["Title"] = channel
   item.info["Thumb"] = os.path.join(settings.getAddonInfo('path'), "resources/images/%s.png" % channel)
   item.info["Plot"] = description
   item.info["FileName"] = "%s?ch=%s" % (sys.argv[0], channel)
   xbmcitems.items.append(item)
 if not settings.getSetting('Parliament_hide') == "true":
  from resources.channels.parliament import parliament as parliamentclass
  parliament = parliamentclass()
  xbmcitems.items.append(parliament.item())
 if not settings.getSetting('Shine_hide') == "true":
  from resources.channels.shine import shine as shineclass
  shine = shineclass()
  xbmcitems.items.append(shine.item())
 xbmcitems.sorting.append('UNSORTED')
 xbmcitems.addall()

