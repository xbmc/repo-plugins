# -*- coding: utf-8 -*-
# KodiAddon (La Capi TV)
#
from t1mlib import t1mAddon
import json
import re
import xbmcplugin, xbmcaddon
import xbmcgui
import sys
import xbmc
import requests

settings = xbmcaddon.Addon(id="plugin.video.lacapitv")
cuenta = ""
path = ""
if settings.getSetting('activa') == "true":
	path ="p/"
	cuenta = settings.getSetting('username') + ":" + settings.getSetting('password') + "@"
html = requests.get('https://'+cuenta+'play.lacapi.tv/'+path+'show.json').text

class myAddon(t1mAddon):
	def getAddonMenu(self,url,ilist):
		a = json.loads(html)
		for b in a['shows']:
			 name = b['titulo']
			 url = b['slug']
			 thumb = b['poster']
			 fanart = thumb
			 infoList = {'mediatype':'tvshow',
									 'TVShowTitle': name,
									 'Title': name,
									 'Plot': b['descripcion']}
			 ilist = self.addMenuItem(name,'GE', ilist, url, thumb, fanart, infoList, isFolder=True)
		return(ilist)

	def getAddonEpisodes(self,url,ilist):
		a = json.loads(html)
		for c in a['shows']:
			if c['slug'] != url:
				continue
			for b in c["capitulo"]:
				name = b['titulo']
				thumb = b['poster']
				fanart = thumb
				url = b['video']
				mensaje = ""
				if (b['privado']) and path == "" :
					mensaje="\r\n\r\nPara ver el video completo cree una cuenta en play.lacapi.tv"
				infoList = {'mediatype':'episode',
								'Title': name,
								'TVShowTitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
								'Plot': b['descripcion'] + mensaje,
								'Duration': 0,
								'Episode': 0 ,
								'Premiered':  b['privado'] }
				ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
		return(ilist)

	def getAddonVideo(self,url):
		liz = xbmcgui.ListItem(path = url, offscreen=True)
		#liz.setMimeType('video/webm')
		xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
