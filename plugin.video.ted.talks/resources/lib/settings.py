"""
Contains constants that we initialize to the correct values at runtime.
"""
import model.language_mapping as language_mapping

username = 'Ted'
password = 'Ted'
download_mode = True
download_path = '/tmp/'
enable_subtitles = True
xbmc_language = 'English'
subtitle_language = 'en'

def init():
    import xbmc, xbmcaddon
    addon = xbmcaddon.Addon(id='plugin.video.ted.talks')
    global username, password, download_mode, download_path, enable_subtitles, xbmc_language, subtitle_language
    username = addon.getSetting('username')
    password = addon.getSetting('password')
    download_mode = addon.getSetting('downloadMode')
    download_path = addon.getSetting('downloadPath')
    enable_subtitles = addon.getSetting('enable_subtitles')
    xbmc_language = xbmc.getLanguage()
    subtitle_language = addon.getSetting('subtitle_language')

def get_subtitle_languages():
    '''
    Returns list of ISO639-1 language codes in order of preference,
    or None if disabled.
    '''
    if enable_subtitles == 'false':
        return None
    if not subtitle_language.strip():
        return language_mapping.get_language_code(xbmc_language)
    else:
        return [code.strip() for code in subtitle_language.split(',') if code.strip()]

