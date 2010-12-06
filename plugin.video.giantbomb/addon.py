# Giant Bomb Addon for XBMC v1.0.0
# Copyright (C) 2010 Anders Bugge
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

# Contact Info
# E-Mail: whimais@gmail.com

# Thanks To
# http://www.whiskeymedia.com/
# http://www.giantbomb.com/
# http://www.comicvine.com/

_id='plugin.video.giantbomb'
_resdir = "special://home/addons/" + _id + "/resources"
_datadir = "special://profile/addon_data/" + _id

# SYS imports
import sys
import urllib

# XBMC imports
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# Simplejson
sys.path.append(_resdir + "/lib/whimai")
import simplejson as json

# API interface imports
sys.path.append( _resdir + "/lib/")
import whimai.wm as wm
import whimai.gb as gb

# Variables
template_url = "http://media.giantbomb.com/video/%(url)s"
justin_url = "http://api.justin.tv/api/channel/archives/giantbomb.json?limit=%(lim)s&offset=%(off)s"
settings_url = "http://whimais.googlecode.com/svn/plugin%20data/branches/giantbomb%20-%20xbmc/giantbomb_settings.json"

settings_file_backup = _resdir + "/data/settings.backup"
settings_script = _resdir + "/lib/settings.py"
settings_file = _datadir + "/settings.json"
video_file = _datadir + "/video.dat"

mon = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06", "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
startswith = "?url=&mode=2&name="
search_cat_pos = 1

class Main:
	
	def __init__( self ):
		self.__settings__ = xbmcaddon.Addon(id=_id)
		self.__language__ = self.__settings__.getLocalizedString
		bug_cQuality = self.__settings__.getSetting('vquality')
		
		self._path = sys.argv[ 0 ]
		self._handle = int(sys.argv[ 1 ])
		self._argv = sys.argv[ 2 ]
			
		if not self._argv:
			self.__settings__.setSetting('isSearch', "")
			self.updateVideoList()
			self.__settings__.setSetting('t_cat', str(self.cat))
			for i in range(len(self.cat)):
				self.addDir(self.cat[i]["name"])
				
		elif self._argv.startswith(startswith):
			name = urllib.unquote_plus( self._argv[ len(startswith): ] )
			self.cat = eval(self.__settings__.getSetting('t_cat'))
			must = False
			
			if name == "Search" and self.__settings__.getSetting('isSearch') == "":
				self.__settings__.setSetting('isSearch', "1")
				keyboard = xbmc.Keyboard( "", self.__language__(30101), False )
				keyboard.doModal()
				if ( keyboard.isConfirmed() ):
					filt = keyboard.getText().rsplit(" ")
					self.cat[search_cat_pos]["filters"] = filt
					self.__settings__.setSetting('t_cat', str(self.cat))
				must = True
			
			elif self.__settings__.getSetting('isSearch') == "1":
				name = "Search"
				must = True
			
			else:
				self.__settings__.setSetting('isSearch', "")
			
			# Add videos
			for i in range(len(self.cat)):
				if name == self.cat[i]["name"]:
					self.addVideosFile(self.cat[i]["filters"], must)
					break
		
			# Add sort methods
			xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_DATE)
			xbmcplugin.addSortMethod(self._handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
			
			# Add catagory
			xbmcplugin.setPluginCategory(self._handle,name)
		
		xbmcplugin.endOfDirectory(self._handle, cacheToDisc=False)
		self.__settings__.setSetting('vquality',bug_cQuality)
	
	def addLink(self, name, url, iconimage, date, deck, totalItems):
		liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name , "Date": date, "Plot": deck} )
		ok=xbmcplugin.addDirectoryItem(handle=self._handle,url=url,listitem=liz,totalItems=int(totalItems))
		return ok
	
	def addDir(self, name):
		u=self._path+"?url="+urllib.quote_plus('')+"&mode="+str(2)+"&name="+urllib.quote_plus(name)
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage='')
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		liz.addContextMenuItems([(self.__language__(30100),"XBMC.RunScript(%s)" % settings_script,)], True)
		ok=xbmcplugin.addDirectoryItem(handle=self._handle,url=u,listitem=liz,isFolder=True)
		return ok
		
	def addVideosFile(self, filt, mustPassAllFilters=False):
		# Justin.tv list
		if (filt == ["live_cat"]):
			try:
				# Checking Justin.tv
				limit = 100
				offset = 0
				done = False
				j_list = []
				while done == False:
					s = urllib.urlopen( justin_url%{ 'lim': limit , 'off': offset } )
					tmp = eval( s.read() )
					if len(tmp) is 0:
						done = True
					else:
						j_list.extend( tmp )
						offset += limit
			
			except:
				print "JUSTIN UPDATE ERROR"
				return
			
			else:
				print "JUSTIN UPDATE OK"
				
				total = len( j_list )
				video_count = 0
				for i in range(0, len(j_list)):
					video_count += 1
					try:
					    name = j_list[i]["title"]
					except:
						name = "Archived video stream from " + j_list[i]["created_on"]
					url = j_list[i]["video_file_url"]
					image = j_list[i]["image_url_medium"]
					date = j_list[i]["created_on"][8:10] + "-" + mon[j_list[i]["created_on"][4:7]] + "-" + j_list[i]["created_on"][24:28]
					deck = "Archived video stream from " + j_list[i]["created_on"]
					self.addLink(name, url, image, date, deck, (total*video_count)/(i+1))
			
			return 
		
		# Get video quality setting
		cQuality = self.__settings__.getSetting('vquality')
		if (cQuality == "true") :
			endString = "_1500.mp4"
		else:
			endString = "_700.mp4"
	
		# Read to the data file
		try:
			FILE = open(video_file, 'r+')
			file_content = FILE.read()
			FILE.close()
			total = json.loads(file_content, object_hook=wm.E('total').as_e)
			videos = json.loads(file_content, object_hook=wm.E('videos').as_e)
			
			# Test file integrati
			if total != len(videos):
				raise ValueError
			
		except:
			print "ERROR IN DATA FILE"
			FILE = open(video_file, 'w')
			FILE.write("")
			FILE.close()
			return
		
		video_count = 0
		for i in range(0,total):
			found = False
			name = videos[i]["name"]
		
			# All videos
			if (filt == ""):
				found = True
				
			# Latest
			elif (filt == ["latest_cat"]):
				if (i>total-26):
					found = True
					
			# Custom catagories
			else:
				for x in range(0, len(filt)):
					if( name.lower().find(filt[x].lower()) != -1):
						found = True
					else:
						if mustPassAllFilters is True:
							found = False
							break
			
			if (found is True):
				video_count += 1
				url = template_url%{ 'url': videos[i]["url"].replace(".mp4",endString) }
				image = videos[i]["image"]["super_url"]
				date = videos[i]["publish_date"][8:10] + '-' + videos[i]["publish_date"][5:7] + '-' + videos[i]["publish_date"][0:4]
				deck = videos[i]["deck"].encode('utf-8')
				self.addLink(name, url, image, date, deck, (total*video_count)/(i+1))
				
	def updateVideoList(self):
		pDialog = xbmcgui.DialogProgress()
		pDialog.create(self.__language__(30102),self.__language__(30103),self.__language__(30104))
			
		# Settings
		SETT = ""
		load_local = False
		if self.__settings__.getSetting('ucat'):
			# Get settings from web
			try:
				s = urllib.urlopen( settings_url )
				SETT = s.read()
				
				#Check if data is ok
				json.loads(SETT, object_hook=wm.E('categories').as_e)[0]
			
			except:
				print "SETTINGS UPDATE ERROR"
				load_local = True
			
			else:
				print "SETTINGS UPDATE OK"
				FILE = open( settings_file, 'w' )
				FILE.write( SETT )
				FILE.close()
		else:
			load_local = True
		
		if load_local is True:
			# Load settings from file
			try:
				# Read settings from local file
				FILE = open( settings_file, 'r+' )
				SETT = FILE.read()
				FILE.close()
				
			except:
				print "SETTINGS FILE ERROR, LOADING BACKUP"
				# Read settings from local backup file
				FILE = open( settings_file_backup, 'r+' )
				SETT = FILE.read()
				FILE.close()
	
			else:
				print "SETTINGS FILE OK"
			
		# Collectiong categori information
		self.cat = json.loads(SETT, object_hook=wm.E('categories').as_e)
	
		# Init video list setup and get total number of videos
		list = gb.List("videos")
		list.extra = "field_list=deck,image,name,publish_date,url&sort=publish_date"
		ok = list.update(0,0)
		if ok is False:
			print "ERROR UPDATING VIDEO DATA"
			del pDialog
			return
		
		total = list.getTotal()
	
		videos = []
		limit = 100
		
		# Compare total to local total
		try:
			FILE = open(video_file, 'r+')
			file_content = FILE.read()
			FILE.close()
			offset = json.loads(file_content, object_hook=wm.E('total').as_e)
			
			# Test file integrati
			if offset != len(json.loads(file_content, object_hook=wm.E('videos').as_e)):
				raise ValueError
				
			# Test video filename
			if( file_content.find(".flv") != -1):
				print "OLD FILENAMES"
				raise ValueError
			
		except:
			print "ERROR IN DATA FILE"
			offset = 0
		
		# if no new videos return
		if total == offset:
			print "NO NEW VIDEOS"
			del pDialog
			return
			
		# get old videos from file
		if offset != 0:
			try:
				videos.extend(json.loads(file_content, object_hook=wm.E('videos').as_e))
				
				# Remove videos from the latest date
				last_date = videos[len(videos)-1]["publish_date"][0:10]
				for i in range(len(videos)-1,0,-1):
					if videos[i]["publish_date"][0:10] != last_date:
						break
					del videos[i]
				offset = len(videos)
			
			except:
				print "ERROR IN DATA FILE"
				videos = []
				offset = 0
		
		start_cnt = offset
		total_cnt = total - offset	
		# get the remaning videos
		while (offset < total):
			if pDialog.iscanceled():
				del pDialog
				return
				
			ok = list.update(offset,limit)
			if ok is False:
				print "ERROR UPDATING VIDEO DATA"
				del pDialog
				return
			
			videos.extend(list.results)
			offset += limit
			i_pct = int(( float(offset-start_cnt) / float(total_cnt))*100.0+0.5)
			pDialog.update(i_pct, self.__language__(30105), self.__language__(30104)) 
			
		# Create json formated video data and write to file
		video_list = { 'total': total, 'videos': videos }
		FILE = open(video_file, 'w')
		FILE.write( json.dumps( video_list ) )
		FILE.close()
		
		del pDialog

if ( __name__ == "__main__" ):
	Main()

