#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>..
__debugging__ = True
ourlog = None
LOGDEBUG = None
LOGNOTICE = None
LOGERROR = None
LOGSEVERE = None

try:
    import xbmc
    import xbmcaddon
    ourlog = xbmc.log
    LOGDEBUG = xbmc.LOGDEBUG
    LOGNOTICE = xbmc.LOGNOTICE
    LOGERROR = xbmc.LOGERROR
    LOGSEVERE = xbmc.LOGSEVERE
    __debugging__ = False
    if xbmcaddon.Addon(id='plugin.audio.qobuz').getSetting('debug') == 'true':
        __debugging__ = True
except:
    LOGDEBUG = '[DEBUG]'
    LOGNOTICE = '[NOTICE]'
    LOGERROR = '[ERROR]'
    LOGSEVERE = '[SEVERE]'

    def logfunc(msg, lvl):
        print lvl + msg
    ourlog = logfunc

def log(obj, msg, lvl=LOGNOTICE):
    """Base for all logging function, run in/out Xbmc
        Inside Xbmc loggin functions use xbmc.log else they just print
        message to STDOUT
    """
    if not __debugging__:
        return
    name = None
    if isinstance(obj, basestring):
        name = obj
    else:
        try:
            name = obj.__class__.__name__
        except:
            name = type(obj)
    ourlog('[Qobuz/' + str(name) + "] " + msg, lvl)

def warn(obj, msg):
    """facility: LOGERROR
    """
    log(obj, msg, LOGERROR)

def info(obj, msg):
    """facility: LOGNOTICE
    """
    log(obj, msg, LOGNOTICE)

def debug(obj, msg):
    """facility: LOGDEBUG
    """
    log(obj, msg, LOGDEBUG)

def error(obj, msg):
    """facility: LOGSEVERE
    """
    log(obj, msg, LOGSEVERE)
