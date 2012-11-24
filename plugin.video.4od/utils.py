import re
import urllib2

from time import mktime,strptime

import xbmc
from xbmc import log

from errorhandler import ErrorCodes
from errorhandler import ErrorHandler

# Only used if we fail to parse the URL from the website
__SwfPlayerDefault__ = 'http://www.channel4.com/static/programmes/asset/flash/swf/4odplayer-11.31.2.swf'
__Aug12__ = mktime(strptime("12 Aug 2012", "%d %b %Y"))

# Return true if date is later than 12 Aug 2012
def isRecentDate(dateString):
	try:
		dateCompare = mktime(strptime(dateString, "%d %b %Y"))

		if dateCompare > __Aug12__:
			return True

	except ( Exception ) as e:
		if dateString is None:
			dateString = 'None'

		xbmc.log ( 'Exception: ' + str(e) + ', dateString: ' + str(dateString), xbmc.LOGERROR )

	return False

def findString(method, pattern, string, flags = (re.DOTALL | re.IGNORECASE)):
	match = re.search( pattern, string, flags )
	#match = None ###
	if match is not None:
		return (match.group(1), None)

	# Limit logging of string to 1000 chars
	limit = 1000
	# Can't find pattern in string
	messageLog = "\nPattern - \n%s\n\nString - \n%s\n\n" % (pattern, string[0:limit])

	return (None, ErrorHandler(method, ErrorCodes.CANT_FIND_PATTERN_IN_STRING, messageLog))



def GetSwfPlayer( html ):
	log ("html size:" + str(len(html)), xbmc.LOGDEBUG)

	error = None

	(swfRoot, error) = findString('GetSwfPlayer', 'var swfRoot = \'(.*?)\'', html)
	if error is None:

		(fourodPlayerFile, error) = findString('GetSwfPlayer', 'var fourodPlayerFile = \'(.*?)\'', html)
		if error is None:

			#TODO Find out how to get the "asset/flash/swf/" part dynamically
			swfPlayer = "http://www.channel4.com" + swfRoot + "asset/flash/swf/" + fourodPlayerFile

			try:
				# Resolve redirect, if any
				req = urllib2.Request(swfPlayer)
				res = urllib2.urlopen(req)
				swfPlayer = res.geturl()
			except Exception, e:
				# Exception resolving swfPlayer URL
				error = ErrorHandler('GetSwfPlayer', ErrorCodes.EXCEPTION_RESOLVING_SWFPLAYER, str(e))

	if error is not None:
		swfPlayer = __SwfPlayerDefault__
		# Unable to determine swfPlayer URL. Using default: 
		error.process(__language__(30520), __SwfPlayerDefault__, xbmc.LOGWARNING)
	
	return swfPlayer


def remove_leading_slash(data):
    p = re.compile(r'/')
    return p.sub('', data)

def remove_square_brackets(data):
    p = re.compile(r' \[.*?\]')
    return p.sub('', data)

def remove_brackets(data):
    p = re.compile(r' \(.*?\)')
    return p.sub('', data)

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def remove_extra_spaces(data):
    p = re.compile(r'\s+')
    return p.sub(' ', data)





