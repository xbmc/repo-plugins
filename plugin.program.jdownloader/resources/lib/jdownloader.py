# script constants
__addonID__			= "plugin.program.jdownloader"

import socket,urllib,urllib2,httplib,os
from xml.dom import minidom
from traceback import print_exc
import xbmc,xbmcaddon
import sys

__dbg__				= sys.modules[ "__main__" ].__dbg__
__logprefix__		= sys.modules[ "__main__" ].__logprefix__

#defines
GET_SPEED			= "downloadspeed"
GET_SPEEDLIMIT		= "speedlimit"
GET_STATUS			= "status"
GET_CURRENTFILECNT	= "currentfilecount"

STATE_RUNNING		= "RUNNING"
STATE_NOTRUNNING	= "NOT_RUNNING"
STATE_STOPPING		= "STOPPING"

ACTION_START			= "01 start"
ACTION_STOP				= "02 stop"
ACTION_PAUSE			= "03 pause"
ACTION_TOGGLE			= "04 toggle"

ACTION_SPEEDLIMIT		= "05 speed limit"
ACTION_MAXDOWNLOADS		= "06 max downloads"

ACTION_ADD_LINKS		= "07 add links"
ACTION_ADD_DLC			= "08 add dlc"

ACTION_RECONNECT		= "10 reconnect"

ACTION_JD_UPDATE		= "20 update JDownloader"
ACTION_JD_RESTART		= "21 restart JDownloader"
ACTION_JD_SHUTDOWN		= "22 shutdown JDownloader"

ALL_ACTIONS = {
	ACTION_START:			30060,
	ACTION_STOP:			30061,
	ACTION_PAUSE:			30062,
	ACTION_TOGGLE:			30063,
	ACTION_SPEEDLIMIT:		30064,
	ACTION_MAXDOWNLOADS:	30065,
	ACTION_ADD_LINKS:		30069,
	ACTION_ADD_DLC:			30070,
	ACTION_RECONNECT:		30071,
	ACTION_JD_UPDATE:		30066,
	ACTION_JD_RESTART:		30067,
	ACTION_JD_SHUTDOWN:		30068
}

Addon =  xbmcaddon.Addon(id=__addonID__)
BASE_RESOURCE_PATH = xbmc.translatePath( Addon.getAddonInfo( "Profile" ) )
# make sure addon_data dir exists
try: os.mkdir(BASE_RESOURCE_PATH)
except: pass

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

def _http_query_with_urlprefix(query,urlPrefix):
	request = urlPrefix+query
	if __dbg__:
		print __logprefix__ + "httpQuery: " + repr(request)
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


def _get_urlprefix(setting_suffix):
	# load settings
	ip_adress = str(Addon.getSetting("ip_adress"+setting_suffix))
	ip_port = str(Addon.getSetting("ip_port"+setting_suffix))
	use_hostname = Addon.getSetting("use_hostname"+setting_suffix) == "true"
	hostname = str(Addon.getSetting("hostname"+setting_suffix))
	
	if (use_hostname):
		urlPrefix = 'http://' + hostname + ':' + ip_port
	else:
		urlPrefix = 'http://' + ip_adress + ':' + ip_port
	
	return urlPrefix

def _http_query(query):
	try:
		result = _http_query_with_urlprefix(query, _get_urlprefix(""))
	except JDError, error:
		use_conn2 = Addon.getSetting("use_conn2") == "true"
		if (use_conn2):
			result = _http_query_with_urlprefix(query, _get_urlprefix("2"))
		else:
			raise error
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
	if x == ACTION_RECONNECT:
		actionStr = '/action/reconnect'
	if x == ACTION_JD_UPDATE:
		actionStr = '/action/update/force%s/' % str(limit)
	if x == ACTION_JD_RESTART:
		actionStr = '/action/restart'
	if x == ACTION_JD_SHUTDOWN:
		actionStr = '/action/shutdown'

	result = _http_query(actionStr)
	return result

def action_addcontainer(link):
	# get settings
	grabber = Addon.getSetting("add_use_grabber")
	start = Addon.getSetting("add_start")
	# add link
	# Parameter 'start' is not supported with rc-version 9568!
	#_http_query('/action/add/container/grabber' + str(grabber) + '/start' + str(start) + '/' + str(link))
	result = _http_query('/action/add/container/grabber' + str(grabber) + '/' + str(link))
	return result

# Links seperated by spaces, won't work, call this functions for each link seperatly
def action_addlink(link):
	# get settings
	grabber = Addon.getSetting("add_use_grabber")
	start = Addon.getSetting("add_start")
	# prepare link - quote special chars, e.g '?'
	link = urllib.quote(link)
	# restore double point (won't work atm)
	link = link.replace( '%3A', ':' )
	# add link
	result = _http_query('/action/add/links/grabber' + str(grabber) + '/start' + str(start) + '/' + str(link))
	return result

def action_addlinks_from_file(filename):
	txt_file = open(filename,'r')
	lines= txt_file.readlines()
	
	for line in lines:
		action_addlink(line)
	return "%d link(s) added" % (len(lines), )