'''
   YouTube plugin for XBMC
   Copyright (C) 2010-2011 Tobias Ussing And Henrik Mosgaard Jensen

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys, os, string
import xbmc

class YouTubeUtils:
	__settings__ = sys.modules[ "__main__" ].__settings__
	__language__ = sys.modules[ "__main__" ].__language__
	__plugin__ = sys.modules[ "__main__" ].__plugin__
	__dbg__ = sys.modules[ "__main__" ].__dbg__
	
	PR_VIDEO_QUALITY = __settings__.getSetting("pr_video_quality") == "true"
	VALID_CHARS = "-_.() %s%s" % (string.ascii_letters, string.digits)
	USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"
	THUMBNAIL_PATH = os.path.join( __settings__.getAddonInfo('path'), "thumbnails" )
	
	# This function raises a keyboard for user input
	def getUserInput(self, title = "Input", default="", hidden=False):
		result = None

		# Fix for when this functions is called with default=None
		if not default:
			default = ""
		
		keyboard = xbmc.Keyboard(default, title)
		keyboard.setHiddenInput(hidden)
		keyboard.doModal()
		
		if keyboard.isConfirmed():
			result = keyboard.getText()
		
		return result
	
	# Converts the request url passed on by xbmc to the plugin into a dict of key-value pairs  
	def getParameters(self, parameterString):
		commands = {}
		splitCommands = parameterString[parameterString.find('?')+1:].split('&')
		
		for command in splitCommands: 
			if (len(command) > 0):
				splitCommand = command.split('=')
				key = splitCommand[0]
				value = splitCommand[1]
				commands[key] = value
		
		return commands
	
	def replaceHtmlCodes(self, str):
		
		str = str.strip()
		str = str.replace("&amp;", "&")
		str = str.replace("&quot;", '"')
		str = str.replace("&hellip;", "...")
		str = str.replace("&gt;",">")
		str = str.replace("&lt;","<")
		str = str.replace("&#39;","'")

		return str
	
	# This function implements a horrible hack related to python 2.4's terrible unicode handling
	def makeAscii(self, str):
		try:
			return str.encode('ascii')
		except:
			if self.__dbg__:
				print self.__plugin__ + " makeAscii hit except on : " + repr(str)
			s = ""
			for i in str:
				try:
					i.encode("ascii")
				except:
					continue
				else:
					s += i
			return s
	
	# Shows a more user-friendly notification
	def showMessage(self, heading, message):
		duration = ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10][int(self.__settings__.getSetting( 'notification_length' ))]) * 1000
		xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ( heading, message, duration) )
	
	# Resolves the full thumbnail path for the plugins skins directory
	def getThumbnail( self, title ):
		if (not title):
			title = "DefaultFolder.png"
		
		thumbnail = os.path.join( sys.modules[ "__main__" ].__plugin__, title + ".png" )
		
		if ( not xbmc.skinHasImage( thumbnail ) ):
			thumbnail = os.path.join( self.THUMBNAIL_PATH, title + ".png" )
			if ( not os.path.isfile( thumbnail ) ):
				thumbnail = "DefaultFolder.png"	
		
		return thumbnail
	
	# Transforms a list of video id's to a pipe delimited string
	def arrayToPipeDelimitedString(self, input):
		pipedItems = ""
		for item in input:
			pipedItems += item + "|"
		return pipedItems
	
	# Standardised error handler
	def showErrorMessage(self, title = "", result = "", status = 500):
		if title == "":
			title = self.__language__(30600)
		if result == "":
			result = self.__language__(30617)
			
		if ( status == 303):
			self.showMessage(title, result)
		else :
			self.showMessage(title, self.__language__(30617))
	
	# generic function for building the item url filters out many item params to reduce unicode problems
	def buildItemUrl(self, item_params = {}, url = ""):
		blacklist = ("path","thumbnail", "Overlay", "icon", "next", "content" , "editid", "summary", "published","count","Rating","Plot","Title","new_results_function")
		for key, value in item_params.items():
			if key not in blacklist:
				url += key + "=" + value + "&"
		return url
	
	# Prints usefull information about and item
	def interrogate(self, item):
		if hasattr(item, '__name__'):
			print "NAME:    ", item.__name__
		if hasattr(item, '__class__'):
			print "CLASS:   ", item.__class__.__name__
		print "ID:      ", id(item)
		print "TYPE:    ", type(item)
		print "VALUE:   ", repr(item)
		print "CALLABLE:",
		if callable(item):
			print "Yes"
		else:
			print "No"
		
		if hasattr(item, '__doc__'):
			doc = getattr(item, '__doc__')
			if doc:
				doc = doc.strip()
				firstline = doc.split('\n')[0]
				print "DOC:     ", firstline
	
	# Adds a default next folder to a result set
	def addNextFolder(self, items = [], params = {}):
		get = params.get
		item = {"Title":self.__language__( 30509 ), "thumbnail":"next", "next":"true", "page":str(int(get("page", "0")) + 1)} 
		for k, v in params.items():
			if (k != "thumbnail" and k != "Title" and k != "page" and k != "new_results_function"):
				item[k] = v
		items.append(item)
	
if __name__ == '__main__':	
	sys.exit(0)
