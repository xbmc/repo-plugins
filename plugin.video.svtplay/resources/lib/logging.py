from __future__ import absolute_import,unicode_literals
import xbmc # pylint: disable=import-error

def log(msg, loglevel=xbmc.LOGDEBUG):
    log_str = "[plugin.video.svtplay] {}".format(msg)
    try:
        # Python 3 handles unicode as is
        xbmc.log(log_str, loglevel)
    except UnicodeEncodeError:
        # Python 2 needs to encode unicode to str
        xbmc.log(log_str.encode("utf-8"), loglevel)

def error(msg):
    log(msg, xbmc.LOGERROR)