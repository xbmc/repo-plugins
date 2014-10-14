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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.	If not, see <http://www.gnu.org/licenses/>.
#

# -- Imports ------------------------------------------------
import json,os,sys,urlparse,urllib,urllib2
import xbmc,xbmcplugin,xbmcgui,xbmcaddon

# -- Constants ----------------------------------------------
ADDON_ID = 'plugin.audio.rautemusik'

# -- Settings -----------------------------------------------
settings = xbmcaddon.Addon(id=ADDON_ID)

# -- I18n ---------------------------------------------------
language = xbmcaddon.Addon(id=ADDON_ID).getLocalizedString

# -- Functions ----------------------------------------------

# -- Classes ------------------------------------------------
class RauteMusik(xbmcaddon.Addon):

	def __init__ (self):
#		xbmcaddon.Addon.__init__(self,id=ADDON_ID)
		self.language	= self.getLocalizedString
		self.addon_id	= self.getAddonInfo('id')
		self.icon	= self.getAddonInfo('icon')
		self.fanart	= self.getAddonInfo('fanart')
		self.version	= self.getAddonInfo('version')
		self.path	= self.getAddonInfo('path')

	def log(self,message,level=xbmc.LOGDEBUG):
		xbmc.log("[%s-%s]: %s" %(self.addon_id, self.version, message), level=level)

	def notice(self,message):
		self.log(message,xbmc.LOGNOTICE)

	def warning(self,message):
		self.log(message,xbmc.LOGWARNING)

	def error(self,message):
		self.log(message,xbmc.LOGERROR)

	def build_url(self,query):
		return self.base_url + '?' + urllib.urlencode(query)

	def getResourceUrl(self,reskind,filename=None):
		if filename is None:
			filename = 'default.jpg'
		retUrl = '{0}/resources/{1}/{2}'.format(self.path,reskind,filename)
		if os.path.exists(retUrl):
			return xbmc.translatePath(retUrl)
		retUrl = '{0}/resources/{1}/default.jpg'.format(self.path,reskind)
		return xbmc.translatePath(retUrl)

	def getIconUrl(self,filename=None):
		return self.getResourceUrl('icons',filename)

	def getThumbnailUrl(self,filename=None):
		return self.getResourceUrl('thumbnails',filename)

	def getPosterUrl(self,filename=None):
		return self.getResourceUrl('poster',filename)

	def getFanartUrl(self,filename=None):
		return self.getResourceUrl('fanart',filename)

	def addCategory(self,key,value):
		im = '{0}.jpg'.format(key)
		li = xbmcgui.ListItem(
			self.getLocalizedString (value['nameid']),
			iconImage = self.getIconUrl (im)
		)
		li.setProperty(
			'Fanart_Image',
			self.getFanartUrl (im)
		)
		xbmcplugin.addDirectoryItem(
			handle = self.addon_handle,
			url = self.build_url({
				'mode': "genre",
				'genre': key
			}),
			listitem = li,
			isFolder = True
		)

	def addCategories(self):
		for key, value in self.genres.iteritems():
			if self.getSetting(key) == "true":
				self.addCategory(key,value)
		xbmcplugin.endOfDirectory(self.addon_handle)

	def addStation(self,key,value):
		im = '{0}.jpg'.format(key)
		li = xbmcgui.ListItem(
			self.getLocalizedString (value['nameid']),
			iconImage = self.getIconUrl (im)
		)
		li.setLabel2(self.getLocalizedString (value['descriptionid']))
		li.setProperty(
			'Poster_Image',
			self.getPosterUrl (im)
		)
		li.setProperty(
			'Fanart_Image',
			self.getFanartUrl (im)
		)
		li.setProperty('IsPlayable', 'true')
		li.setInfo(type = 'Music', infoLabels = {
			"Title": self.getLocalizedString (value['nameid'])
		})
		xbmcplugin.addDirectoryItem(
			handle = self.addon_handle,
			url = value['url'],
			listitem = li,
			isFolder = False
		)

	def isStationEnabled(self,station):
		for key, value in self.genres.iteritems():
			if self.getSetting(key) == "true":
				if station.get(key,False):
					return True
		return False
		
	def addStations(self,genre):
		for key, value in self.channels.iteritems():
			if genre is None:
				if self.isStationEnabled(value):
					self.addStation(key,value)
			elif value.get(genre,False):
				self.addStation(key,value)
		xbmcplugin.endOfDirectory(self.addon_handle)

	def Init(self):
		self.base_url		= sys.argv[0]
		self.addon_handle	= int(sys.argv[1])
		self.args		= urlparse.parse_qs(sys.argv[2][1:])
		self.channels		= {}
		self.genres		= {}
		# xbmcplugin.setContent(addon_handle, 'music')
		try:
			channels = open ('{0}/resources/channels.json'.format(self.path), 'r')
			result = json.load(channels)
			channels.close()
			if isinstance(result,dict):
				self.channels	= result.get("channels",{})
				self.genres	= result.get("genres",{})
		except Exception as e:
			self.error('Error while loading channels: {0}'.format(e))

	def Do(self):
		mode = self.args.get('mode', None)
		if mode is None:
			if self.getSetting("hiermenu") == "true":
				self.addCategories()
			else:
				self.addStations(None)
		elif mode[0] == "genre":
			genre = self.args.get('genre',[None])
			self.addStations(genre[0])

	def Exit(self):
		pass

# -- Main Code ----------------------------------------------
addon = RauteMusik()
addon.Init()
addon.Do()
addon.Exit()
del addon
