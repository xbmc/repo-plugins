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
import xbmcplugin, xbmcaddon, xbmcgui, xbmc, xbmcaddon


# This function returns the plugin settings object to main module.
def get_plugin_settings(plugin_id=""):
    return xbmcaddon.Addon(id=plugin_id)
    

debug_enable = False # The debug logs are disabled by default.

# This function sets the debug_enable var to log everything if debug option is true.
def set_debug_mode(debug_flag=""):
    global debug_enable
    if debug_flag == "true":
        debug_enable = True


# This function logs the messages into the main XBMC log file. Called from main plugin module.
def log(message):
    if debug_enable:
        xbmc.log(message.encode('ascii', 'ignore'))


# This function logs the messages into the main XBMC log file. Called from the libraries module by other functions.
def _log(message):
    if debug_enable:
        xbmc.log("lutils." + message.encode('ascii', 'ignore'))


# This function gets all the parameters passed to the plugin from XBMC API and retuns a dictionary.
def get_plugin_parms():
    params = sys.argv[2]
    _log("get_plugin_parms " + str(params))

    pattern_params  = re.compile('[?&]([^=&]+)=?([^&]*)')
    options = dict((parameter, urllib.unquote_plus(value)) for (parameter, value) in pattern_params.findall(params))

    _log("get_plugin_parms " + repr(options))
    return options


# This function loads the html code from a webserver and returns it into a string.
def carga_web(url, headers=""):
    _log("carga_web " + url)

    MiReq = urllib2.Request(url) # We have to use this method as we need to add some headers.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # Firefox header.
    for key in headers:
        MiReq.add_header(key, headers[key])
    MiConex = urllib2.urlopen(MiReq) # Opens the http connection to the URL.
    MiHTML = MiConex.read() # Gets all the html contents from the URL and stores it into a variable.
    MiConex.close() # Close the http connection as we get what we need.

    return MiHTML


# This function gets the http redirect address from an URL. This is necesary with some web sites, as bliptv, because the former function follows the redirect link, and the info with the video file is missed.
def get_redirect(url):
    _log("get_redirect " + url)

    MiConex = urllib.urlopen(url) # Opens the http connection to the URL.
    MiHTML = MiConex.geturl() # Gets the URL redirect link and stores it into MiHTML.
    MiConex.close() # Close the http connection as we get what we need.

    return MiHTML


# This function returns a json object collected from the web into a dictionary.
def get_json_dict(MiJSON):
    return json.loads(MiJSON)


# This function cleans the date field obtained from the emissions JSON video list.
def limpia_fecha(date):
    fecha = date.split(",")
    dia = fecha[1][1:].replace("..","")
    hora = fecha[2][1:8]
    _log("limpia_fecha (%s %s)"  % (dia, hora))
    return "(%s %s)" % (dia, hora)


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
def addDir(action = "", title = "", url = "", thumbnail = "", referer = ""):
    _log("addDir action = [" + action + "] url = [" + url + "] thumbnail = [" + thumbnail + "]")

    if referer:
        dir_url = '%s?action=%s&url=%s&referer=%s' % (sys.argv[0], action, urllib.quote_plus(url), urllib.quote_plus(referer))
    else:
        dir_url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(url))

    dir_item = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = thumbnail)
    dir_item.setInfo(type = "Video", infoLabels = {"Title": title})
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = dir_url, listitem = dir_item, isFolder = True)


# This function adds a video link entry into the XBMC GUI throught the API
def addLink(action = "", title = "", plot = "", url = "", thumbnail = ""):
    _log("addLink action = [" + action + "] url = [" + url + "] thumbnail = [" + thumbnail + "]")

    link_url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(url))
    link_item = xbmcgui.ListItem(title, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail)
    link_item.setInfo(type = "Video", infoLabels = {"Title": title, "Plot": plot})
    link_item.setProperty('IsPlayable', 'true')
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = link_url, listitem = link_item, isFolder = False)


# This function closes the directory created with all the item list previously added.
def close_dir(pluginhandle):
    _log("close_dir pluginhadle: %s" % pluginhandle)
    xbmcplugin.endOfDirectory(pluginhandle)


# This funtion shows a popup window with a notices message through the XBMC GUI during 5 secs.
def showWarning(message):
    _log("showWarning message: %s" % message)
    xbmc.executebuiltin('XBMC.Notification(Info:,' + message + '!,6000)')


# This function plays the video file pointed by the URL passed as argument.
def play_resolved_url(pluginhandle= "", url = ""):
    _log("play_resolved_url pluginhandle = [%s] url = [%s]" % (pluginhandle, url))
    listitem = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
