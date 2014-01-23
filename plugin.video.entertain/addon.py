# -*- coding: utf-8 -*-
# Copyright 2014 Leo Moll
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Source: http://grinch.itg-em.de/entertain/faq/allgemein/multicastadressliste/
#

import sys
import xbmc, xbmcplugin, xbmcgui, xbmcaddon

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.video.entertain'
FANART = xbmcaddon.Addon(id=ADDON_ID).getAddonInfo('path') + '/fanart.jpg'

# -- Settings -----------------------------------------------
settings = xbmcaddon.Addon(id=ADDON_ID)
quality = 1 + int(settings.getSetting("quality"))
channelimage = int(settings.getSetting("channelimage"))
categories = 1 + int(settings.getSetting("categories"))

# -- I18n ---------------------------------------------------
language = xbmcaddon.Addon(id=ADDON_ID).getLocalizedString

# -- Functions ----------------------------------------------
def getIconUrl(filename=False):
	return getResourceUrl('icons', filename)


def getThumbnailUrl(filename=False):
	return getResourceUrl('thumbnails', filename)


def getPosterUrl(filename=False):
	return getResourceUrl('poster', filename)


def getFanartUrl(filename=False):
	return getResourceUrl('fanart', filename)


def getResourceUrl(reskind, filename=False):
	if (not filename):
		filename = 'default.jpg'
	retUrl = xbmcaddon.Addon(id=ADDON_ID).getAddonInfo('path') + '/resources/' + reskind + '/' + filename
	return xbmc.translatePath(retUrl)


def addEntertainChannel(url,name,all=False,icon=False,thumbnail=False,poster=False,fanart=False,plot='',genre=language(30090),year='2014',duration='90',hdurl=False,chancat=1):
	if (chancat & categories):
		if (not hdurl):
			addChannel(url,name,all,icon,thumbnail,poster,fanart,plot,genre,year,duration)
		else:
			if (quality & 1):
				addChannel(url,name,all,icon,thumbnail,poster,fanart,plot,genre,year,duration)
			if (quality & 2):
				addChannel(hdurl,name + " HD",all,icon,thumbnail,poster,fanart,plot,genre,year,duration)


def addChannel(url,name,all=False,icon=False,thumbnail=False,poster=False,fanart=False, plot='', genre=language(30090),year='2014',duration='90'):
	iconUrl = getIconUrl(icon if (icon) else all)
	thumbnailUrl = getThumbnailUrl(thumbnail if (thumbnail) else all)
	posterUrl = getPosterUrl(poster if (poster) else all)
	fanartUrl = getFanartUrl(fanart if (fanart) else all)
	logoUrl = thumbnailUrl if ( channelimage ) else posterUrl
	li = xbmcgui.ListItem(name, iconImage=iconUrl, thumbnailImage=logoUrl)
	li.setProperty('IsPlayable', 'true')
	li.setProperty('Poster_Image', posterUrl)
	li.setProperty('Fanart_Image', fanartUrl)
	li.setInfo(type = 'Video', infoLabels = {
		"Title": name,
		"Plot": plot,
		"Year": year,
		"Genre": genre,
		"Duration": duration,
		"Art(thumb)": thumbnailUrl,
		"Art(poster)": posterUrl,
		"Art(fanart)": fanartUrl
		 })
	xbmcplugin.addDirectoryItem(int(sys.argv[1]), url, li, False)
	
	
	

# -- Main Code ----------------------------------------------

# TODO: can't figure out how to set fanart for root/back folder of plugin
# http://trac.xbmc.org/ticket/8228? 
xbmcplugin.setPluginFanart(int(sys.argv[1]), FANART)
xbmcplugin.setContent(int(sys.argv[1]), 'movies')

# -- General Channels
if (settings.getSetting("cat_general") == "true"):
	# -- Public Channels
	addEntertainChannel ('rtp://@239.35.10.4:10000', 'Das Erste', year='1954', plot=language(30101), all='das-erste.jpg', hdurl='rtp://@239.35.10.1:10000')
	addEntertainChannel ('rtp://@239.35.10.5:10000', 'ZDF', year='1963', plot=language(30102), all='zdf.jpg', hdurl='rtp://@239.35.10.2:10000')
	# -- RTL Group
	addEntertainChannel ('rtp://@239.35.20.10:10000', 'RTL', year='1984', genre=language(30090), plot=language(30130), chancat=2)
	addEntertainChannel ('rtp://@239.35.20.11:10000', 'VOX', year='1993', genre=language(30090), plot=language(30131), chancat=2)
	addEntertainChannel ('rtp://@239.35.20.22:10000', 'RTL II', year='1993', genre=language(30090), plot=language(30132), chancat=2)

# -- Regional Channels
if (settings.getSetting("cat_regional") == "true"):
	# -- Public Channels
	addEntertainChannel ('rtp://@239.35.10.13:10000', 'BR Nord', year='1949', genre=language(30091), plot=language(30103), all='BR.jpg')
	addEntertainChannel ('rtp://@239.35.10.7:10000', 'BR Süd', year='1949', genre=language(30091), plot=language(30103), all='BR.jpg', hdurl='rtp://@239.35.10.49:10000')
	addEntertainChannel ('rtp://@239.35.10.8:10000', 'hr-fernsehen', genre=language(30091), plot=language(30124), all='hr.jpg', hdurl='rtp://@239.35.10.60:10000')
	addEntertainChannel ('rtp://@239.35.10.9:10000', 'MDR Sachsen', year='1992', genre=language(30091), plot=language(30104), all='mdr.jpg', hdurl='rtp://@239.35.10.61:10000')
	addEntertainChannel ('rtp://@239.35.10.29:10000', 'MDR Sachsen-Anhalt', year='1992', genre=language(30091), plot=language(30104), all='mdr.jpg')
	addEntertainChannel ('rtp://@239.35.10.30:10000', 'MDR Thüringen', year='1992', genre=language(30091), plot=language(30104), all='mdr.jpg')
	addEntertainChannel ('rtp://@239.35.10.10:10000', 'NDR Niedersachsen', year='1954', genre=language(30091), plot=language(30105), hdurl='rtp://@239.35.10.50:10000')
	addEntertainChannel ('rtp://@239.35.10.31:10000', 'NDR Hamburg', year='1954', genre=language(30091), plot=language(30105))
	addEntertainChannel ('rtp://@239.35.10.32:10000', 'NDR Mecklenburg-Vorpommern', year='1954', genre=language(30091), plot=language(30105))
	addEntertainChannel ('rtp://@239.35.10.33:10000', 'NDR Schleswig-Holstein', year='1954', genre=language(30091), plot=language(30105))
	addEntertainChannel ('rtp://@239.35.10.12:10000', 'Radio Bremen TV', year='1945', genre=language(30091), plot=language(30106))
	addEntertainChannel ('rtp://@239.35.10.14:10000', 'rbb Berlin', year='2003', genre=language(30091), plot=language(30107), hdurl='rtp://@239.35.10.62:10000')
	addEntertainChannel ('rtp://@239.35.10.34:10000', 'rbb Brandenburg', year='2003', genre=language(30091), plot=language(30107))
	addEntertainChannel ('rtp://@239.35.10.15:10000', 'SR Fernsehen', year='1957', genre=language(30091), plot=language(30108))
	addEntertainChannel ('rtp://@239.35.10.16:10000', 'SWR Baden-Würtenberg', year='1998', genre=language(30091), plot=language(30109), hdurl='rtp://@239.35.10.51:10000')
	addEntertainChannel ('rtp://@239.35.10.17:10000', 'SWR Rheinland-Pfalz', year='1998', genre=language(30091), plot=language(30109), hdurl='rtp://@239.35.10.52:10000')
	addEntertainChannel ('rtp://@239.35.10.18:10000', 'WDR Köln', year='1956', genre=language(30091), plot=language(30110), hdurl='rtp://@239.35.10.53:10000')
	addEntertainChannel ('rtp://@239.35.10.35:10000', 'WDR Aachen', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.36:10000', 'WDR Bielefeld', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.37:10000', 'WDR Bonn', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.38:10000', 'WDR Dortmund', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.39:10000', 'WDR Duisburg', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.40:10000', 'WDR Düsseldorf', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.41:10000', 'WDR Essen', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.42:10000', 'WDR Münster', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.43:10000', 'WDR Siegen', year='1956', genre=language(30091), plot=language(30110))
	addEntertainChannel ('rtp://@239.35.10.44:10000', 'WDR Wuppertal', year='1956', genre=language(30091), plot=language(30110))
	# -- RTL Group
	addEntertainChannel ('rtp://@239.35.20.5:10000', 'RTL NRW', year='1984', genre=language(30091), plot=language(30130), chancat=2)
	addEntertainChannel ('rtp://@239.35.20.6:10000', 'RTL HB NDS', year='1984', genre=language(30091), plot=language(30130), chancat=2)
	addEntertainChannel ('rtp://@239.35.20.63:10000', 'RTL HH SH', year='1984', genre=language(30091), plot=language(30130), chancat=2)
	addEntertainChannel ('rtp://@239.35.20.64:10000', 'RTL Hessen', year='1984', genre=language(30091), plot=language(30130), chancat=2)

# -- Cultural Channels
if (settings.getSetting("cat_cultural") == "true"):
	# -- Public Channels
	addEntertainChannel ('rtp://@239.35.10.6:10000', '3sat', year='1984', genre=language(30092), plot=language(30111), all='3sat.jpg', hdurl='rtp://@239.35.10.47:10000')
	addEntertainChannel ('rtp://@239.35.10.20:10000', 'ARTE', year='1991', genre=language(30092), plot=language(30112), all='arte.jpg', hdurl='rtp://@239.35.10.3:10000')
	addEntertainChannel ('rtp://@239.35.10.21:10000', 'Einsfestival', year='1997', genre=language(30092), plot=language(30113), hdurl='rtp://@239.35.10.58:10000')
	addEntertainChannel ('rtp://@239.35.10.23:10000', 'zdf.kultur', year='2011', genre=language(30092), plot=language(30114), hdurl='rtp://@239.35.10.54:10000')

# -- Special Interest
if (settings.getSetting("cat_special") == "true"):
	# -- Public Channels
	addEntertainChannel ('rtp://@239.35.10.19:10000', 'KiKa', year='1997', genre=language(30093), plot=language(30115), hdurl='rtp://@239.35.10.11:10000')
	addEntertainChannel ('rtp://@239.35.10.22:10000', 'PHOENIX', year='1997', genre=language(30093), plot=language(30116), hdurl='rtp://@239.35.10.48:10000')
	addEntertainChannel ('rtp://@239.35.10.24:10000', 'BR-alpha', year='1998', genre=language(30093), plot=language(30117))
	addEntertainChannel ('rtp://@239.35.10.26:10000', 'EinsPlus', year='1997', genre=language(30093), plot=language(30118), hdurl='rtp://@239.35.10.59:10000')
	# -- RTL Group
	addEntertainChannel ('rtp://@239.35.20.39:10000', 'Super RTL', year='1995', genre=language(30093), plot=language(30133), chancat=2)
	addEntertainChannel ('rtp://@239.35.20.59:10000', 'RTLNITRO', year='2012', genre=language(30093), plot=language(30135), chancat=2)

# -- News Channels
if (settings.getSetting("cat_news") == "true"):
	# -- Public Channels
	addEntertainChannel ('rtp://@239.35.20.44:10000', 'Deutsche Welle', year='1992', genre=language(30094), plot=language(30120))
	addEntertainChannel ('rtp://@239.35.10.25:10000', 'tagesschau24', year='1997', genre=language(30094), plot=language(30121), hdurl='rtp://@239.35.10.63:10000')
	addEntertainChannel ('rtp://@239.35.10.28:10000', 'ZDFinfo', year='1997', genre=language(30094), plot=language(30122), hdurl='rtp://@239.35.10.56:10000')
	addEntertainChannel ('rtp://@239.35.10.27:10000', 'ZDFneo', year='2009', genre=language(30094), plot=language(30123), hdurl='rtp://@239.35.10.55:10000')
	# -- RTL Group
	addEntertainChannel ('rtp://@239.35.20.47:10000', 'n-tv', year='1992', genre=language(30094), plot=language(30134), chancat=2)


xbmcplugin.endOfDirectory(int(sys.argv[1]))

