import os
import re
import urllib2
import sys
import inspect
import unicodedata

from time import mktime,strptime

import xbmc
from xbmcaddon import Addon

from loggingexception import LoggingException

def to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
         if not isinstance(obj, unicode):
             obj = unicode(obj, encoding)
    elif isinstance(obj, int) or isinstance(obj, long) or isinstance(obj, float)  or obj is None:
             obj = unicode(obj)
    return obj

def log(msg, level = xbmc.LOGNOTICE, method = None):
    try:
        if method is None:
            method = inspect.stack()[1][3]
            
        if isinstance(msg, unicode):
            xbmc.log((u"%s : '%s'" % (method, msg)).encode('utf8'), level)
        else:
            xbmc.log(to_unicode((u"%s : '%s'" % (method, msg))).encode('utf8'), level)
    except ( Exception ) as e:
        xbmc.log(u"FALLBACK %s : '%s'" % (method, repr(msg)), level)

#def log(msg, level = xbmc.LOGNOTICE):
#	if isinstance(msg, unicode):
#		xbmc.log(msg.encode('utf8'), level)
#	else:
#		xbmc.log(to_unicode(msg).encode('utf8'), level)

# Return true if date is later than 12 Aug 2012
def isRecentDate(dateString):
	try:
		dateCompare = mktime(strptime(dateString, u"%d %b %Y"))

		if dateCompare > __Aug12__:
			return True

	except ( Exception ) as e:
		if dateString is None:
			dateString = 'None'

		xbmc.log ( u'Exception: ' + to_unicode(e) + ', dateString: ' + to_unicode(dateString), xbmc.LOGERROR )

	return False

def findString(method, pattern, string, flags = (re.DOTALL | re.IGNORECASE)):
    try:
        match = re.search( pattern, string, flags )
    
        if match is not None:
    		return match.group(1)
    except (Exception) as exception:
        raise LoggingException.fromException(exception)
            
	# Limit logging of string to 1000 chars
    limit = 1000
    messageLog = u"\nPattern - \n%s\n\nString - \n%s\n\n" % (pattern, string[0:limit])
    logException = LoggingException(u"utils.findString", "Can't find pattern in string\n\n" + messageLog)

    raise logException 


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

def replace_non_alphanum(data):
    p = re.compile(r'[^0-9A-Za-z]+')
    return p.sub('', data)

def valueIfDefined(value, name = None):
    try:
        if name is None:
            return value
        else:
            return name + ": " + value
    except NameError:
        if name is None:
            return ""
        else:
            return name + ": Not defined"

def isVariableDefined(variable):
    try:
        variable
        return True
    except NameError:
        return False
    
def extractJSON(text):
    start = text.index('(') + 1
    end = text.rindex(')')
    
    return text[start:end]


def drepr(x, sort = True, indent = 0):
    if isinstance(x, dict):
        r = '{\n'
        for (key, value) in (sorted(x.items()) if sort else x.iteritems()):
            r += (' ' * (indent + 4)) + repr(key) + ': '
            r += drepr(value, sort, indent + 4) + ',\n'
        r = r.rstrip(',\n') + '\n'
        r += (' ' * indent) + '}'
    elif hasattr(x, '__iter__'):
        r = '[\n'
        for value in (sorted(x) if sort else x):
            r += (' ' * (indent + 4)) + drepr(value, sort, indent + 4) + ',\n'
        r = r.rstrip(',\n') + '\n'
        r += (' ' * indent) + ']'
    else:
        r = repr(x)
    return r

def normalize(text):
    if isinstance(text, str):
        try:
            text = text.decode('utf8')
        except:
            try:
                text = text.decode('latin1')
            except:
                text = text.decode('utf8', 'ignore')
            
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore')

