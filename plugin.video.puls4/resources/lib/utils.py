#!/usr/bin/python
# -*- coding: utf-8 -*-
# don't move this
from future.standard_library import install_aliases
install_aliases()

from .app_common import translate
import urllib.parse
import time
import sys
import re
import datetime

if sys.version_info >= (3, 0, 0):
    string_types = str,
else:
    string_types = basestring,


_timeStampFormat = '%d.%m.%Y %H:%M:%S'


def toStr(string):
    if sys.version_info < (3, 0, 0):
        if isinstance(string, unicode):
            return string.encode('utf-8')

    if not checkIsString(string):
        string = string.decode('utf-8')
    return string


def checkIsString(string):
    return isinstance(string, string_types)


def encodeUrl(url):
    return urllib.parse.urlencode(url)


def unquoteUrl(url):
    return urllib.parse.unquote(url)


def cleanhtml(text):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', text)
    return cleantext


def cleanText(string):
    string = toStr(string).replace('\\n', '').replace('&#160;', ' ').replace('&Ouml;', 'Ö').replace('&ouml;', 'ö')\
        .replace('&szlig;', 'ß').replace('&Auml;', 'Ä').replace('&auml;', 'ä').replace('&Uuml;', 'Ü')\
        .replace('&uuml;', 'ü').replace('&quot;', '"').replace('&amp;', '&').replace('&#039;', '´')
    return cleanhtml(string)


def translateDay(day):
    sw = {'monday': translate(30005),
          'tuesday': translate(30006),
          'wednesday': translate(30007),
          'thursday': translate(30008),
          'friday': translate(30009),
          'saturday': translate(30010),
          'sunday': translate(30011),
          'montag': translate(30005),
          'dienstag': translate(30006),
          'mittwoch': translate(30007),
          'donnerstag': translate(30008),
          'freitag': translate(30009),
          'samstag': translate(30010),
          'sonntag': translate(30011)}
    return sw.get(day.lower(), day)


def dateFromTimeStamp(timeStamp):
    return datetime.datetime.fromtimestamp(timeStamp).strftime(_timeStampFormat)


def formatAiredString(airedDate):

    if isinstance(airedDate, bytes,):
        airedDate = airedDate.decode('utf-8')

    if checkIsString(airedDate):
        try:
            airedDate = datetime.datetime.strptime(airedDate, _timeStampFormat)
        except TypeError:
            airedDate = datetime.datetime(
                *(time.strptime(airedDate, _timeStampFormat)[0:6]))

    return '%s, %02d.%02d.%d - %d:%02d' % (translateDay(airedDate.strftime('%A')), airedDate.day, airedDate.month, airedDate.year, airedDate.hour, airedDate.minute)


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split('&')
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict
