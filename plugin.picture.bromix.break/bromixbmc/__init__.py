"""
Version 2.0.7 (2014.07.25)
- ADD: addImage(...) will also set the setInfo('pictures'...) info labels

Version 2.0.6 (2014.07.20)
- ADD: addImage(...)

Version 2.0.5 (2014.07.19)
- ADD: executebuiltin(function)
- ADD: addSortMethod(sort_method) for add sorting

Version 2.0.4 (2014.07.15)
- ADD: decodeHtmlText(text) for decoding html escaped text

Version 2.0.3 (2014.07.13)
- ADD: getSettingAsInt

Version 2.0.2 (2014.07.10)
- FIX: Android won't return a valid language so I added a default value 

Version 2.0.1 (2014.07.08)
- complete restructuring

Version 1.0.2 (2014.06.25)
- added 'getFavorites', 'addFavorite' and 'removeFavorite'
- set the encoding for the favorite routines to utf-8
- removed 'duration' and 'plot' from addVideoLink -> therefore use 'additionalInfoLabels'

Version 1.0.1 (2014.06.24)
- added support for helping with favorites
- initial release
"""

import locale
import re
import sys
import urlparse
import HTMLParser

import xbmc

from plugin import Plugin
from keyboard import Keyboard

def getFormatDateShort(year, month, day):
    date_format = xbmc.getRegion('dateshort')
    date_format = date_format.replace('%d', day)
    date_format = date_format.replace('%m', month)
    date_format = date_format.replace('%Y', year)
    return date_format

def executebuiltin(function):
    xbmc.executebuiltin(function)

def stripHtmlFromText(text):
    return re.sub('<[^<]+?>', '', text)

def decodeHtmlText(text):
    hp = HTMLParser.HTMLParser()
    return hp.unescape(text)

def getParam(name, default=None):
    args = urlparse.parse_qs(sys.argv[2][1:])
    value = args.get(name, None)
    if value and len(value)>=1:
        return value[0]
    
    return default

def getLanguageId(default='en-US'):
    result = default
    
    try:
        language = locale.getdefaultlocale()
        if language and len(language)>=1 and language[0]:
            result = language[0].replace('_', '-')
    except:
        # do nothing
        pass
    
    return result