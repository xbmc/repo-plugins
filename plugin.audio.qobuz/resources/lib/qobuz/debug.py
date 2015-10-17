'''
    qobuz.debug
    ~~~~~~~~~~~

    :part_of: xbmc-qobuz
    :copyright: (c) 2012 by Joachim Basmaison, Cyril Leclerc
    :license: GPLv3, see LICENSE for more details.
'''
__debugging__ = True
ourlog = None
LOGDEBUG = None
LOGNOTICE = None
LOGERROR = None
LOGSEVERE = None

try:
    import xbmc  # @UnresolvedImport
    import xbmcaddon  # @UnresolvedImport
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
