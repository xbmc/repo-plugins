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
   Release 0.1.1
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
        xbmc.log("lutils.%s" % message.encode('ascii', 'ignore'))

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


# This function loads the html code from a webserver and returns it into a string.
def carga_web(url):
    _log("carga_web " + url)

    MiReq = urllib2.Request(url) # esto funciona de forma diferente porque metemos una cabecera.
    # Tenemos que hacer creer a la web que usamos un navegador de usuario real.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # Cabecera del Firefox.
    MiConex = urllib2.urlopen(MiReq) # abrimos una conexion con la URL
    MiHTML = MiConex.read() # Chupamos TODO el contenido de la pagina web y lo salvamos en una variable
    MiConex.close() # Cerramos la conexion con la pagina web, pues ya tenemos toda la info que necesitamos.

    return MiHTML


# This function gets the http redirect address from an URL. This is necesary with some web sites, as bliptv, because the former function follows the redirect link, and the info with the video file is missed.
def get_redirect(url):
    _log("get_redirect " + url)

    MiConex = urllib.urlopen(url) # Opens the http connection to the URL.
    MiHTML = MiConex.geturl() # Gets the URL redirect link and stores it into MiHTML.
    MiConex.close() # Close the http connection as we get what we need.

    return MiHTML


# This function sends a http GET with XMLHttpRequest, and gets back a JSON from the web server stored into a dict. 
def get_json(url):
    _log("get_json " + url)

    MiReq = urllib2.Request(url)
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0')
    MiReq.add_header('Accept', 'application/json, text/javascript, */*')
    MiReq.add_header('Accept-Encoding', 'deflate')
    MiReq.add_header('X-Requested-With', 'XMLHttpRequest')
    MiReq.add_header('Referer', 'http://www.tv5mondeplus.com/videos')
    MiReq.add_header('Cookie', 'ns_cookietest=true; ns_session=true')

    MiConex = urllib2.urlopen(MiReq)
    MiJSON = MiConex.read()
    MiConex.close()

    return json.loads(MiJSON)


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
def addDir(action = "", title = "", url = "", thumbnail = ""):
    _log("addDir action = [" + action + "] title = [" + title + "] url = [" + url + "] thumbnail = [" + thumbnail + "]")

    dir_url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(url))
    dir_item = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = thumbnail)
    dir_item.setInfo(type = "Video", infoLabels = {"Title": title})
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = dir_url, listitem = dir_item, isFolder = True)


# This function adds a video link entry into the XBMC GUI throught the API
def addLink(action = "", title = "", plot = "", url = "", thumbnail = ""):
    _log("addDir action = [" + action + "] title = [" + title + "] plot = [" + plot + "] url = [" + url + "] thumbnail = [" + thumbnail + "]")

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
