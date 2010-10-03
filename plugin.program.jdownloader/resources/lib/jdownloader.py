# script constants
__addonID__			= "plugin.program.jdownloader"

import socket,urllib2,httplib,os
from xml.dom import minidom
from traceback import print_exc
import xbmc,xbmcaddon
import sys

#defines
GET_SPEED			= "downloadspeed"
GET_SPEEDLIMIT		= "speedlimit"
GET_STATUS			= "status"
GET_CURRENTFILECNT	= "currentfilecount"

STATE_RUNNING		= "RUNNING"
STATE_NOTRUNNING	= "NOT_RUNNING"
STATE_STOPPING		= "STOPPING"

ACTION_START	= "1 start"
ACTION_STOP		= "2 stop"
ACTION_PAUSE	= "3 pause"
ACTION_TOGGLE	= "4 toggle"

ACTION_SPEEDLIMIT	= "5 speed limit"
ACTION_MAXDOWNLOADS	= "6 max downloads"

ACTION_JD_UPDATE	= "7 update JDownloader"
ACTION_JD_RESTART	= "8 restart JDownloader"
ACTION_JD_SHUTDOWN	= "9 shutdown JDownloader"

ALL_ACTIONS = {
	ACTION_START:		30060,
	ACTION_STOP:		30061,
	ACTION_PAUSE:		30062,
	ACTION_TOGGLE:		30063,
	ACTION_SPEEDLIMIT:	30064,
	ACTION_MAXDOWNLOADS:30065,
	ACTION_JD_UPDATE:	30066,
	ACTION_JD_RESTART:	30067,
	ACTION_JD_SHUTDOWN:	30068
}

Addon =  xbmcaddon.Addon(id=__addonID__)
BASE_RESOURCE_PATH = xbmc.translatePath( Addon.getAddonInfo( "Profile" ) )

# load settings
ip_adress = str(Addon.getSetting("ip_adress"))
ip_port = str(Addon.getSetting("ip_port"))

urlPrefix = 'http://' + ip_adress + ':' + ip_port

class JDError(Exception):
	 def __init__(self, message='', original=None):
		  Exception.__init__(self, message)
		  self.message = message
		  self.original = original

	 def __str__(self):
		  if self.original:
			original_name = type(self.original).__name__
			return '%s Original exception: %s, "%s"' % (self.message, original_name, self.original.args)
		  else:
			return self.message

def _http_query(query):
	request = urlPrefix+query
	request_count = 0
	while True:
		error_data = ""
		try:
			try:
				socket.setdefaulttimeout(10)
				response = urllib2.urlopen(request)
				break
			except urllib2.URLError, error:
				raise JDError('Failed to connect to server.')
			except httplib.BadStatusLine, error:
				if (request_count > 1):
					raise JDError('Failed to request %s "%s".' % (self.url, query))
		finally:
			if error_data:
				self._debug_response(error, error_data)
		request_count = request_count + 1
	result = response.read()
	response.close()
	return result

# Get Info #

# As long as only the package info gets parsed, it doesn't matter which list gets loaded (currentlist,alllist,finishedlist)
# These three only differ in means of listed files, the package information is always the same.
# Due to that, the smallest will be used: currentlist
def get_downloadlist(x):
	xmlfile = os.path.join( BASE_RESOURCE_PATH , "dlist.xml" )
	try:
		#result = _http_query('/get/downloads/%s' % x)
		result = _http_query('/get/downloads/currentlist')
		
		fileObj = open(xmlfile,"w")
		fileObj.write(result)
		fileObj.close()
		
		xmldoc = minidom.parseString(result)
		itemlist = xmldoc.getElementsByTagName('package')
		filelist = []
		for s in itemlist :
			package = {}
			package["Name"] = s.attributes['package_name'].value + " "
			package["Eta"] = s.attributes['package_ETA'].value+ " "
			package["Size"] = s.attributes['package_size'].value+ " "
			package["Percentage"] = s.attributes['package_percent'].value
			filelist.append(package)
		return filelist
		#return(packageName, packageEta, packageSize, packagePercentage) debug	
	except IOError:
		print_exc()
		return 'error'


def get(x):
	if x == GET_SPEED:
		getStr = '/get/speed'
	if x == GET_SPEEDLIMIT:
		getStr = '/get/speedlimit'
	if x == GET_STATUS:
		getStr = '/get/downloadstatus'
	if x == GET_CURRENTFILECNT:
		getStr = '/get/downloads/currentcount'
	
	result = _http_query(getStr)
	if result.startswith("0"): result = 'none'
	return result

# Actions #

def getAvailableActions():
	actions = ALL_ACTIONS.keys();
	
	actions.sort();
	
	status = get(GET_STATUS)
	if STATE_NOTRUNNING in status: 
		for i in [ACTION_STOP,ACTION_PAUSE,ACTION_SPEEDLIMIT,ACTION_MAXDOWNLOADS]:
			actions.remove(i)
	elif STATE_RUNNING in status:
		actions.remove(ACTION_START)
	elif STATE_STOPPING in status: # no status changes possible 
		for i in [ACTION_START,ACTION_STOP,ACTION_PAUSE,ACTION_TOGGLE,ACTION_SPEEDLIMIT,ACTION_MAXDOWNLOADS]:
			actions.remove(i)
	return actions

def action( x , limit = "0" ):
	if x == ACTION_START:
		actionStr = '/action/start'
	if x == ACTION_STOP:
		actionStr = '/action/stop'
	if x == ACTION_PAUSE:
		actionStr = '/action/pause'
	if x == ACTION_TOGGLE:
		actionStr = '/action/toggle'
	if x == ACTION_SPEEDLIMIT:
		actionStr = '/action/set/download/limit/' + str(limit)
	if x == ACTION_MAXDOWNLOADS:
		actionStr = '/action/set/download/max/' + str(limit)
	if x == ACTION_JD_UPDATE:
		actionStr = '/action/update/force%s/' % str(limit)
	if x == ACTION_JD_RESTART:
		actionStr = '/action/restart'
	if x == ACTION_JD_SHUTDOWN:
		actionStr = '/action/shutdown'

	result = _http_query(actionStr)
	return result

def action_addcontainer(grabber,start,link):
	_http_query('/action/add/container/grabber' + str(grabber) + '/start' + str(start) + '/' + str(link))

# Links must be seperated by spaces
def action_addlinks(grabber,start,link):
	_http_query('/action/add/links/grabber' + str(grabber) + '/start' + str(start) + '/' + str(link))
