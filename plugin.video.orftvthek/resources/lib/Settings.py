import xbmcaddon

__addon__ = xbmcaddon.Addon()


def blacklist():
    return __addon__.getSetting('enableBlacklist') == 'true'


def forceView():
    return __addon__.getSetting('forceView') == 'true'


def localizedString(translation_id):
    return __addon__.getLocalizedString(translation_id)


def serviceAPI():
    return __addon__.getSetting('useServiceAPI') == 'true'


def subtitles():
    return __addon__.getSetting('useSubtitles') == 'true'


def userAgent():
    return __addon__.getSetting('userAgent')


def autoPlayPrompt():
    return __addon__.getSetting("autoPlayPrompt") == "true"


def playAllPlaylist():
    return __addon__.getSetting('usePlayAllPlaylist') == 'true'
