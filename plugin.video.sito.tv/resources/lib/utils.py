# -*- coding: utf-8 -*-
import os
from kodiswift import xbmc

COLOR_WHITE = 'FFFFFFFF'
COLOR_DISABLED = 'FF808080'
MOVIES_COLOR = 'FFFFFFFF'  # White
TVSHOWS_COLOR = 'FFFFFFFF'  # White
GENRE_COLOR = 'FFFFFFFF'  # White
ALPHABET_COLOR = 'FFFFFFFF'  # White
COLLECTIONS_COLOR = 'FFFFFFFF'  # White
SEARCH_COLOR = 'FFB8E986'  # Yellow
LAST_VIEWED_COLOR = 'FFB8E986'  # Yellow
NEW_LABEL_COLOR = 'FFFF0000'  # Simple red

BITX_PACKAGE = 'tv.bitx.media'
BITIX_PLAY_LINK = 'https://play.google.com/store/apps/details?id=tv.bitx.media&referrer=utm_source%3Dkodi.sito.tv'


def log(txt, level=xbmc.LOGWARNING):
    message = '%s: %s' % ('SiTo.tv', str(txt).encode('ascii', 'ignore'))
    xbmc.log(msg=message, level=level)


def is_android():
    android_env = False
    try:
        android_env = 'XBMC_ANDROID_APK' in os.environ.data
    except Exception as e:
        log("is_android error: %s" % e, level=xbmc.LOGWARNING)

    return xbmc.getCondVisibility("system.platform.android") or android_env


def get_os_name():
    try:
        if is_android():
            return "android"
        elif xbmc.getCondVisibility("system.platform.linux"):
            return "linux"
        elif xbmc.getCondVisibility("system.platform.xbox"):
            return "xbox"
        elif xbmc.getCondVisibility("system.platform.windows"):
            return "windows"
        elif xbmc.getCondVisibility("system.platform.osx"):
            return "darwin"
        elif xbmc.getCondVisibility("system.platform.ios"):
            return "ios"
        elif xbmc.getCondVisibility("system.platform.atv2"):
            # Apple TV 2
            return "atv2"
    except Exception as ex:
        log("get_os_name error: %s" % ex, level=xbmc.LOGERROR)
    return "unknown"


def open_web_url(url):
    if not is_android():
        try:
            import webbrowser
            webbrowser.open_new(url)
        except Exception as ex:
            log("open_web_url error: %s" % ex, level=xbmc.LOGERROR)
    else:
        xbmc.executebuiltin('XBMC.StartAndroidActivity(,"android.intent.action.VIEW", ,"%s")' % url)


def is_bitx_installed():
    bitx_is_installed = False
    try:
        bitx_package_path = os.popen('pm path %s' % BITX_PACKAGE).read()
        if bitx_package_path:
            bitx_is_installed = True
        log("BitX application path: %s" % bitx_package_path, level=xbmc.LOGINFO)
    except Exception as e:
        log("Android pm path error: %s" % e, level=xbmc.LOGERROR)
    return bitx_is_installed


def start_bitx(magnet_link):
    if is_android() and is_bitx_installed():
        # noinspection PyBroadException
        try:
            notice(_lang(33027), _lang(33026))

            # StartAndroidActivity(package,[intent,dataType,dataURI])
            # Launch an Android native app with the given package name.
            # Optional parms (in order): intent, dataType, dataURI.
            # example: StartAndroidActivity(com.android.chrome,android.intent.action.VIEW,,http://kodi.tv/)	v13 Addition
            intent = "android.intent.action.VIEW"
            xbmc.executebuiltin('XBMC.StartAndroidActivity("%s", "%s", , "%s")' % (bitx_package, intent, magnet_link))
            return
        except Exception as ex:
            log("Android intent error: %s" % ex, level=xbmc.LOGERROR)

    if os_is_android:
        xbmcgui.Dialog().ok(_lang(33028), _lang(33029))

    open_web_url(BITIX_PLAY_LINK)