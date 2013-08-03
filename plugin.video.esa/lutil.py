# _*_ coding: utf-8 _*_

'''
   lutil: library functions for XBMC video plugins.
   Copyright (C) 2013 José Antonio Montes (jamontes)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

   Description:
   These funtions are called from the main plugin module, aimed to ease and simplify the plugin development process.
   Release 0.1.3
'''

# First of all We must import all the libraries used for plugin development.
import sys, re, urllib, urllib2, json
import xbmcplugin, xbmcaddon, xbmcgui, xbmcaddon, xbmc

debug_enable = False # The debug logs are disabled by default.

# This function returns the plugin settings object to main module.
def get_plugin_settings(plugin_id=""):
    return xbmcaddon.Addon(id=plugin_id)


# This function returns the current system language.    
def get_system_language():
    return xbmc.getLanguage()


# This function sets the debug_enable var to log everything if debug option is true.
def set_debug_mode(debug_flag=""):
    global debug_enable
    if debug_flag == "true":
        debug_enable = True


# This function logs the messages into the main XBMC log file. Called from main plugin module.
def log(message):
    if debug_enable:
        print "%s" % message


# This function logs the messages into the main XBMC log file. Called from the libraries module by other functions.
def _log(message):
    if debug_enable:
        print "lutils.%s" % message


# This function gets all the parameters passed to the plugin from XBMC API and retuns a dictionary.
# Example:
# plugin://plugin.video.atactv/?parametro1=valor1&parametro2=valor2&parametro3
def get_plugin_parms():
    params = sys.argv[2]
    _log("get_plugin_parms " + str(params))

    pattern_params  = re.compile('[?&]([^=&]+)=?([^&]*)')
    options = dict((parameter, urllib.unquote_plus(value)) for (parameter, value) in pattern_params.findall(params))

    _log("get_plugin_parms " + repr(options))
    return options


# This function returns the URL decoded.
def get_url_decoded(url):
    _log('get_url_decoded URL: "%s"' % url)
    return urllib.unquote_plus(url)


# This function returns the URL encoded.
def get_url_encoded(url):
    _log('get_url_encoded URL: "%s"' % url)
    return urllib.quote_plus(url)


# This function gets an input text from the keyboard.
def get_keyboard_text(prompt):
    _log('get_keyboard_text prompt: "%s"' % prompt)
    
    keyboard = xbmc.Keyboard('', prompt)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        _log("get_keyboard_text input text: '%s'" % keyboard.getText())
        return keyboard.getText()
    else:
        return ""


# This function loads the html code from a webserver and returns it into a string.
def carga_web(url):
    _log("carga_web " + url)

    MiReq = urllib2.Request(url) # We use the Request method because we need to add a header into the HTTP GET to the web site.
    # We have to tell the web site we are using a real browser.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # This is a true Firefox header.
    MiConex = urllib2.urlopen(MiReq) # We open the HTTP connection to the URL.
    MiHTML = MiConex.read() # We load all the HTML contents from the web page and store it into a var.
    MiConex.close() # We close the HTTP connection as we have all the info required.

    return MiHTML


# This function allows us to find multiples matches from a regexp into a string.
def find_multiple(text,pattern):
    _log("find_multiple pattern=" + pattern)

    pat_url_par = re.compile(pattern, re.DOTALL)
   
    return pat_url_par.findall(text)


# This function gets back the first match from a regexp into a string.
def find_first(text,pattern):
    _log("find_first pattern=" + pattern)

    pat_url_par = re.compile(pattern, re.DOTALL)
    try:
        return  pat_url_par.findall(text)[0]
    except:
        return ""


# This function adds a directory entry into the XBMC GUI throught the API
def addDir(action = "", title = "", url = "", thumbnail = "", reset_cache = "no"):
    _log('addDir action = "%s" url = "%s" thumbnail = "%s" reset_cache = "%s"' % (action, url, thumbnail, reset_cache))

    dir_url = '%s?action=%s&reset_cache=%s&url=%s' % (sys.argv[0], action, reset_cache, urllib.quote_plus(url))
    dir_item = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = thumbnail)
    dir_item.setInfo(type = "Video", infoLabels = {"Title": title})
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = dir_url, listitem = dir_item, isFolder = True)


# This function adds a video link entry into the XBMC GUI throught the API
def addLink(action = "", title = "", plot = "", url = "", thumbnail = ""):
    _log("addLink action = [" + action + "] title = [" + title + "] plot = [" + plot + "] url = [" + url + "] thumbnail = [" + thumbnail + "]")

    link_url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(url))
    link_item = xbmcgui.ListItem(title, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail)
    link_item.setInfo(type = "Video", infoLabels = {"Title": title, "Plot": plot})
    link_item.setProperty('IsPlayable', 'true')
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = link_url, listitem = link_item, isFolder = False)


# This function closes the directory created with all the item list previously added.
def close_dir(pluginhandle, succeeded=True, updateListing=False, cacheToDisc=True):
    _log("close_dir pluginhadle: %s updateListing: %s cacheToDisc: %s" % (pluginhandle, updateListing, cacheToDisc))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=succeeded, updateListing=updateListing, cacheToDisc=cacheToDisc)


# This funtion shows a popup window with a notices message through the XBMC GUI during 5 secs.
def showWarning(message):
    _log("showWarning message: %s" % message)
    xbmc.executebuiltin('XBMC.Notification(Info:,' + message + '!,6000)')


# This function plays the video file pointed by the URL passed as argument.
def play_resolved_url(pluginhandle= "", url = ""):
    _log("play_resolved_url pluginhandle = [%s] url = [%s]" % (pluginhandle, url))
    listitem = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
