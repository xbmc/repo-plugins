import xbmc
from xbmc import log

import utils

__flashVer1__ = "WIN 11,2,202,243"
__flashVer2__ = "WIN\\2011,2,202,243"
__pageUrl__ = "http://www.channel4.com"


class RTMP:
	def __init__(self):
		self.url = None
		self.auth = None
                self.app = None
                self.playPath = None
                self.swfPlayer = None

		self.rtmpdumpPath = None
                self.savePath = None
		
		self.pageUrl = __pageUrl__

	def setDetailsFromURI(self, streamURI, auth, swfPlayer):
		log('setDetailsFromURI streamURI: ' + streamURI, xbmc.LOGDEBUG)
		log('setDetailsFromURI swfPlayer: ' + swfPlayer, xbmc.LOGDEBUG)

		log('setDetailsFromURI auth: ' + auth, xbmc.LOGDEBUG)

		(self.url, error) = utils.findString('setDetailsFromURI', '(.*?)mp4:', streamURI)##LL
#		(self.url, error) = utils.findString('setDetailsFromURI', '(.*?)/mp4:', streamURI)##AK
		if error is not None:
			return error

		self.url = self.url.replace( '.com/', '.com:1935/' )

		(self.app, error) = utils.findString('setDetailsFromURI', '.com/(.*?)mp4:', streamURI)##LL
#		(self.app, error) = utils.findString('setDetailsFromURI', '.com/(.*?)/mp4:', streamURI)##AK
		if error is not None:
			return error

		##self.app = self.app + "?ovpfv=1.1&" + auth
		self.app = self.app + "?" + auth

		(self.playPath, error) = utils.findString('setDetailsFromURI', '(mp4:.*)', streamURI)
		if error is not None:
			return error

		self.playPath = self.playPath + '?' + auth

		self.swfPlayer = swfPlayer
		self.auth = auth

		log ("setDetailsFromURI url: " + self.url, xbmc.LOGDEBUG)
		log ("setDetailsFromURI app: " + self.app, xbmc.LOGDEBUG)
		log ("setDetailsFromURI playPath: " + self.playPath, xbmc.LOGDEBUG)
		log ("setDetailsFromURI auth: " + self.auth, xbmc.LOGDEBUG)

		return None

	#def setDownloadPath(self, savePath):
	#	self.savePath = savePath
	def setDownloadDetails(self, rtmpdumpPath, savePath):
                self.rtmpdumpPath = rtmpdumpPath
		self.savePath = savePath
	
		log ("setDownloadDetails rtmpdumpPath: " + self.rtmpdumpPath, xbmc.LOGDEBUG)


	def getParameters(self):
		args = [
			"--rtmp", '"%s"' % self.url,
			"--app", '"%s"' % self.app,
			"--flashVer", '"WIN 11,2,202,243"',
			"--pageUrl", '"http://www.channel4.com"',
			"--swfVfy", '"%s"' % self.swfPlayer,
			"--conn", "Z:",
			"--playpath", '"%s"' % self.playPath,
			"-o", '"%s"' % self.savePath
			]

		command = ' '.join(args)

		log("command: " + command, xbmc.LOGDEBUG)
		return command

	def getPlayUrl(self):

###		playURL = "%s?ovpfv=1.1&%s playpath=%s swfurl=%s swfvfy=true" % (self.url,self.auth,self.playPath,self.swfPlayer)
		playURL = "%s?%s app=%s tcurl=%s playpath=%s swfurl=%s flashver=%s pageurl=%s swfvfy=true" % (self.url,self.auth, self.app, self.url,self.playPath,self.swfPlayer, __flashVer2__, self.pageUrl)
###		playURL = "%s?%s playpath=%s swfurl=%s pageurl=%s swfvfy=true" % (self.url,self.auth,self.playPath,self.swfPlayer, self.pageUrl)

		log("playURL: " + playURL, xbmc.LOGDEBUG)
		return playURL

	

