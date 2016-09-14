# Viaplay Kodi plugin #
Before reading further, please note that this plugin is unoffical and is not endorsed or supported by Viaplay in any way. Not all features are supported or thoroughly tested and may not work as intended.

If you're interested in helping out with the development, then please just send me a pull request. If you're reporting a bug, make sure you've enabled debugging in both the addon settings as well as in Kodi and attached the log. Feedback and constructive input are of course always welcome.

This plugin was written based on Viaplay's JSON API.


## Dependencies: ##
This plugin is available in the official Kodi repository and all dependencies will be installed automatically when installed from there. However, if you're installing straight from git, please make sure you've got the following modules installed:
 * Requests >= 2.9.1 (http://mirrors.kodi.tv/addons/jarvis/script.module.requests)
 * iso8601 (http://mirrors.kodi.tv/addons/jarvis/script.module.iso8601)
 * m3u8 >= 0.2.10 (http://mirrors.kodi.tv/addons/jarvis/script.module.m3u8)

This plugin supports Kodi Jarvis or later. While it may work fine on older versions as well, it is unsupported and you're encouraged to upgrade.

# Features: #
 * Support for Sweden, Denmark, Norway and Finland
 * Internal video playback
 * Categories
 * Movies
 * TV shows
 * Kids
 * Sports
 * Store
 * Subtitles
 * Search
 * A-Ö alphabetical listing
 * Parental control
 
Currently unsupported features:

 * Viasat TV To Go
 * Starred
 * Activity list
 * ... And quite possibly more that I'm forgetting about!
 
## Known issues: ##
#### No audio on live sports ####
This is due to a bug in Kodi/ffmpeg (http://trac.kodi.tv/ticket/16670). Viaplay uses HLS v4 for live sports and supplies the audio as an external track. Unfortunately, this is currently not working in Kodi. However, with Krypton and its new input stream add-ons, a fix/workaround is hopefully just around the corner.
