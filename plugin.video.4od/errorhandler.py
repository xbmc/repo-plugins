import xbmc
import xbmcgui

from xbmcaddon import Addon
from xbmc import log

__PluginName__  = 'plugin.video.4od'
__addon__ = Addon(__PluginName__)
__language__ = __addon__.getLocalizedString

class ErrorCodes:

	ERROR_GETTING_EPISODE_LIST 	= 30790 # Error getting episode list web page
	ERROR_GETTING_CATEGORY_PAGE 	= 30795 # Error getting category web page
	ERROR_GETTING_STREAM_INFO_XML	= 30810 # Error getting stream info xml
	UNABLE_TO_FIND_MP4		= 30550 # Unable to find MP4 video file to play
	ERROR_GETTING_YOUTUBE_SHOW	= 30820 # Error getting youtube show page
	ERROR_GETTING_YOUTUBE_SEASON	= 30825 # Error getting youtube season playlist page
	CANNOT_DETERMINE_SHOW_NUMBERS	= 30830 # Cannot determine season and episode numbers
	ERROR_GETTING_SEARCH_WEB_PAGE	= 30835 # Error getting search web page
	CANT_FIND_PATTERN_IN_STRING	= 30705 # Can't find pattern in string
	ERROR_GETTING_PROGRAMME_PAGE	= 30805 # Error getting programme list web page
	EXCEPTION_RESOLVING_SWFPLAYER	= 30730 # Exception resolving swfPlayer URL
	CHANGE_SOCKET_TIMEOUT		= 30860 # Change the socket timeout in the plugin setting if you see this problem a lot
	UNABLE_TO_FIND_YOUTUBE_ID	= 30930 # Unable to find Youtube id
	WRONG_CONTENT_DELIVERY_NETWORK	= 30945 # Wrong content delivery network

# TODO Rename. variables are too similar in meaning: Summary, Heading, Overview
# TODO Replace with try/catches
class ErrorHandler:

	def __init__(self, method, errorCode, messageLog = None, messageHeading = 'Error'):

		self.method 		= method
		self.errorCode 		= errorCode
		self.messageSummary 	= __language__(errorCode)
		self.messageLog 	= messageLog
		self.messageHeading 	= messageHeading
		self.processed		= False

	def getCode():
		return self.errorCode

	def isProcessed():
		return self.processed

	def insertSpaces(self, string, position):
		if len(string) > position:
			ind = string.rfind(' ', 0, position)
			if ind != -1:
				 string = string[:ind] + '\n' + string[ind:]

		return string

	def splitSpaces(self, string, position):
		if len(string) > position:
			ind = string.rfind(' ', 0, position)
			if ind != -1:
				 return (string[:ind], string[ind:])

		return (string, '')


	def process(self, messageHeading = None, messageOverview = '', level = xbmc.LOGDEBUG):
		self.messageSummary = self.insertSpaces(self.messageSummary, 50)
		(self.messageSummary, messageSummary2) = self.splitSpaces(self.messageSummary, 100)

		if messageHeading is not None:
			self.messageHeading = messageHeading

		if len(messageOverview) > 0:
			self.messageOverview = messageOverview + ' - ' + self.messageSummary 
		else:
			self.messageOverview = self.messageSummary


		if self.messageLog is not None:
			log('In %s: %s: %s\n%s' % (self.method, self.messageHeading, self.messageOverview, self.messageLog), level)
		else:
			log('In %s: %s: %s' (self.method, self.messageHeading, self.messageOverview), level)

		if level == xbmc.LOGERROR:
			dialog = xbmcgui.Dialog()
			dialog.ok(self.messageHeading, self.messageSummary, messageSummary2,'See log for details')
		elif level == xbmc.LOGWARNING:
			# See log for details
			xbmc.executebuiltin('XBMC.Notification(4oD %s, %s)' % (self.messageHeading, __language__(30700)))

		self.processed = True
