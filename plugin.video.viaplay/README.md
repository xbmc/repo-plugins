# Viaplay Kodi plugin #
Before reading any further, please note that this plugin is unoffical and is not endorsed or supported by Viaplay in any way. Not all features are supported or thoroughly tested and may not work as intended.

If you're interested in helping out with the developement, please just send me a pull request. If you're reporting a bug, please enable add-on debugging and attach the log. Feedback and constructive input are of course always welcome.

This plugin was written based on Viaplay's JSON API.


## Dependencies: ##
 * Requests 2.x (http://mirrors.kodi.tv/addons/jarvis/script.module.requests)
 * dateutil 2.x (http://mirrors.kodi.tv/addons/jarvis/script.module.dateutil)

This plugin supports Kodi Jarvis or later. While it may work on older versions, no support will be offered.

# Features: #
 * Support for Sweden, Denmark, Norway and Finland
 * Internal video playback
 * Categories
 * Movies
 * TV shows
 * Kids
 * Sports
 * Subtitles
 * Search
 * A-Ö alphabetical listing
 
Currently unsupported features:
 * Store
 * Viasat TV To Go
 * Starred
 * Activity list
 
## Known issues: ##
#### No audio on live sports ####
This is due to a bug in Kodi/ffmpeg. Viaplay uses HLS v4 for live sports and supplies the audio as an external track. Unfortunately, this is currently not working properly in Kodi. However, with Krypton and its new input stream add-ons, a fix is hopefully just around the corner.
 
