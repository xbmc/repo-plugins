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

def videoQuality(quality_list):
    default_return_index = 2
    videoQuality = int(__addon__.getSetting('videoQuality'))
    try:
        return quality_list[int(videoQuality)]
    except:
        return quality_list[default_return_index]
	 
def autoPlayPrompt():
	return __addon__.getSetting("autoPlayPrompt") == "true"
