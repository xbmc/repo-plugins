import socket,urllib,urllib2,httplib,os
from xml.dom import minidom
from traceback import print_exc
import xbmc,xbmcaddon
import sys,time

__addon__			= sys.modules[ "__main__" ].__addon__
__dbg__				= sys.modules[ "__main__" ].__dbg__
__logprefix__		= sys.modules[ "__main__" ].__logprefix__

#defines
GET_SPEED			= "downloadspeed"
GET_SPEEDLIMIT		= "speedlimit"
GET_ISRECONNECT		= "isreconnect"
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

ACTION_ENA_RECONNECT	= "11 enable reconnect"
ACTION_DIS_RECONNECT	= "12 set reconnect"
ACTION_ENA_PREMIUM		= "13 enable premium"
ACTION_DIS_PREMIUM		= "14 disable premium"

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
	ACTION_ENA_RECONNECT:	30072,
	ACTION_DIS_RECONNECT:	30073,
	ACTION_ENA_PREMIUM:		30074,
	ACTION_DIS_PREMIUM:		30075,
	ACTION_JD_UPDATE:		30066,
	ACTION_JD_RESTART:		30067,
	ACTION_JD_SHUTDOWN:		30068
}


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
	ip_adress = str(__addon__.getSetting("ip_adress"+setting_suffix))
	ip_port = str(__addon__.getSetting("ip_port"+setting_suffix))
	use_hostname = __addon__.getSetting("use_hostname"+setting_suffix) == "true"
	hostname = str(__addon__.getSetting("hostname"+setting_suffix))
	
	if (use_hostname):
		urlPrefix = 'http://' + hostname + ':' + ip_port
	else:
		urlPrefix = 'http://' + ip_adress + ':' + ip_port
	
	return urlPrefix

def _http_query(query):
	try:
		result = _http_query_with_urlprefix(query, _get_urlprefix(""))
	except JDError, error:
		use_conn2 = __addon__.getSetting("use_conn2") == "true"
		if (use_conn2):
			result = _http_query_with_urlprefix(query, _get_urlprefix("2"))
		else:
			raise error
	return result

# determine the current remote control api version (nightly or stable)
nightly = False
try:
	if (int(_http_query("/get/rcversion")) > 9568 ):
		nightly = True
except: pass

# Get Info #

def load_pkglist(which):
	if (nightly):
		if (which == "finishedlist"):
			getStr = "finished/list"
		else:
			getStr = "all/list"
	else:
		getStr = which
	
	result = _http_query('/get/downloads/%s' % getStr)
	
	return result

def get_pkglist(which):
	pkgxml = load_pkglist(which)
	
	xmldoc = minidom.parseString(pkgxml)
	if (nightly):
		itemlist = xmldoc.getElementsByTagName('packages')
	else:
		itemlist = xmldoc.getElementsByTagName('package')
	pkglist = []
	for item in itemlist :
		package = {}
		package["name"] = item.attributes['package_name'].value
		package["eta"] = item.attributes['package_ETA'].value
		package["size"] = item.attributes['package_size'].value
		package["percent"] = item.attributes['package_percent'].value
			
		# HACK: try to improve packagename
		package["display"] = package["name"]
		if (package["name"].startswith("Added ")):
			files = item.getElementsByTagName('file')
			if (len(files)>0):
				filename = files[0].attributes['file_name'].value
				if (".part" in filename):
					package["display"] = filename.split(".part")[0]
				else:
					package["display"] = filename
			
		pkglist.append(package)
	return pkglist

def get_filelist(which):
	pkgxml = load_pkglist("alllist")
	
	xmldoc = minidom.parseString(pkgxml)
	if (nightly):
		packages = xmldoc.getElementsByTagName('packages')
	else:
		packages = xmldoc.getElementsByTagName('package')
	filelist = []
	for pkgitem in packages:
		if (pkgitem.attributes['package_name'].value == which):
			files = pkgitem.getElementsByTagName('file')
			for fileitem in files:
				file = {}
				file["name"] =		fileitem.attributes['file_name'].value
				file["percent"] =	fileitem.attributes['file_percent'].value
				file["speed"] =		fileitem.attributes['file_speed'].value
				file["status"] =	fileitem.attributes['file_status'].value
				filelist.append(file)
	return filelist

def get(x):
	if x == GET_SPEED:
		getStr = '/get/speed'
	if x == GET_SPEEDLIMIT:
		getStr = '/get/speedlimit'
	if x == GET_ISRECONNECT:
		getStr = '/get/isreconnect'
	if x == GET_STATUS:
		getStr = '/get/downloadstatus'
	if x == GET_CURRENTFILECNT:
		if (nightly):
			getStr = '/get/downloads/current/count'
		else:
			getStr = '/get/downloads/currentcount'
	
	result = _http_query(getStr)
	if result.startswith("0"): result = 'none'
	return result

# Actions #
def getAvailableActions(status):
	actions = ALL_ACTIONS.keys();
	
	actions.sort();
	
	if STATE_NOTRUNNING in status: 
		for i in [ACTION_STOP,ACTION_PAUSE,ACTION_SPEEDLIMIT,ACTION_MAXDOWNLOADS]:
			actions.remove(i)
	elif STATE_RUNNING in status:
		actions.remove(ACTION_START)
	elif STATE_STOPPING in status: # no status changes possible 
		for i in [ACTION_START,ACTION_STOP,ACTION_PAUSE,ACTION_TOGGLE,ACTION_SPEEDLIMIT,ACTION_MAXDOWNLOADS]:
			actions.remove(i)
			
	# handle reconnect action
	if get(GET_ISRECONNECT) == "true":
		actions.remove(ACTION_ENA_RECONNECT)
	else:
		actions.remove(ACTION_DIS_RECONNECT)
	
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
	if x == ACTION_RECONNECT:
		actionStr = '/action/reconnect'
	if (nightly):
		if x == ACTION_SPEEDLIMIT:
			actionStr = '/set/download/limit/' + str(limit)
		if x == ACTION_MAXDOWNLOADS:
			actionStr = '/set/download/max/' + str(limit)
		if x == ACTION_ENA_RECONNECT:
			actionStr = '/set/reconnect/true'
		if x == ACTION_DIS_RECONNECT:
			actionStr = '/set/reconnect/false' 
		if x == ACTION_ENA_PREMIUM:
			actionStr = '/set/premium/true'
		if x == ACTION_DIS_PREMIUM:
			actionStr = '/set/premium/false'
		if x == ACTION_JD_UPDATE:
			if (limit==1):
				actionStr = '/action/forceupdate'
			else:
				actionStr = '/action/update'
	else:
		if x == ACTION_SPEEDLIMIT:
			actionStr = '/action/set/download/limit/' + str(limit)
		if x == ACTION_MAXDOWNLOADS:
			actionStr = '/action/set/download/max/' + str(limit)
		if x == ACTION_ENA_RECONNECT:
			actionStr = '/action/set/reconnectenabled/false' # interface is wrong, expects the opposite values
		if x == ACTION_DIS_RECONNECT:
			actionStr = '/action/set/reconnectenabled/true' # interface is wrong, expects the opposite values
		if x == ACTION_ENA_PREMIUM:
			actionStr = '/action/set/premiumenabled/true'
		if x == ACTION_DIS_PREMIUM:
			actionStr = '/action/set/premiumenabled/false'
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
	grabber = __addon__.getSetting("add_use_grabber")
	start = __addon__.getSetting("add_start")
	# add link
	# Parameter 'start' is not supported with rc-version 9568!
	#_http_query('/action/add/container/grabber' + str(grabber) + '/start' + str(start) + '/' + str(link))
	result = _http_query('/action/add/container/grabber' + str(grabber) + '/' + str(link))
	
	force_start()
	
	return result

# Links separated by spaces, won't work, call this functions for each link separately
def action_addlink(link):
	# get settings
	grabber = __addon__.getSetting("add_use_grabber")
	start = __addon__.getSetting("add_start")
	# prepare link - quote special chars, e.g '?'
	link = urllib.quote(link)
	# restore double point (won't work atm)
	link = link.replace( '%3A', ':' )
	# add link
	result = _http_query('/action/add/links/grabber' + str(grabber) + '/start' + str(start) + '/' + str(link))
	
	force_start()
	
	return result

# Links separated by spaces, won't work, but as parameters (&l1=<link1>&l2=<link2>&...) it works (in r9568)
# expects multiple links separated by '|'
def action_addlinklist(linklist):
	# get settings
	grabber = __addon__.getSetting("add_use_grabber")
	start = __addon__.getSetting("add_start")
	
	links = ""
	first = True
	idx=0
	for link in linklist.split(" "):
		# prepare link - quote special chars, e.g '?'
		link = urllib.quote(link)
		# restore double point (won't work atm)
		link = link.replace( '%3A', ':' )
		# add link
		if (first):
			links = "?l"
			first = False
		else:
			links += "&l"
		links += str(idx) + "=" + link
		idx += 1
	
	result = _http_query('/action/add/links/grabber' + str(grabber) + '/start' + str(start) + '/' + str(links))
	
	force_start()
	
	return result

def action_addlinks_from_file(filename):
	txt_file = open(filename,'r')
	lines= txt_file.readlines()
	
	for line in lines:
		action_addlink(line)
	return "%d link(s) added" % (len(lines), )

# HACK: fixes problem, that jd already stopped again before the links are added to the dl list (decrypting takes a few seconds) 
def force_start():
	if (__addon__.getSetting("add_start") == "1"):
		now = time.time();
		while ((get(GET_STATUS) != STATE_RUNNING or get(GET_SPEED) == "none") and now + 20.0 > time.time()): # try for a maximum of 20 seconds to start jd
			action(ACTION_START)
			time.sleep(4.0)