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
   These funtions are called from the main plugin module, aimed to ease and
   simplify the plugin development process.
   Release 0.1.5
'''

# First of all We must import all the libraries used for plugin development.
import sys, re, urllib, urllib2, json
import xbmcplugin, xbmcaddon, xbmcgui, xbmcaddon, xbmc

debug_enable = False # The debug logs are disabled by default.


def get_plugin_settings(plugin_id=""):
    """This is a getter function to return the settings method reference."""
    return xbmcaddon.Addon(id=plugin_id)


def get_system_language():
    """This function returns the current GUI language."""
    return xbmc.getLanguage()


def set_debug_mode(debug_flag=""):
    """This function sets the debug_enable flag to log everything if debug option within add-on settings is activated."""
    global debug_enable
    if debug_flag == "true":
        debug_enable = True


def log(message):
    """This function logs the messages into the main XBMC log file, only if debug option is activated from the add-on settings.
    This function is called from the main add-on module."""
    if debug_enable:
        try:
            xbmc.log(msg=message, level=xbmc.LOGNOTICE)
        except:
            xbmc.log(msg='WARNING: log this line from attatc_tv is not possible due to encoding string problems', level=xbmc.LOGNOTICE)


def get_plugin_parms():
    """This function gets all the parameters passed to the plugin from XBMC API and retuns a dictionary.
    Example: plugin://plugin.video.atactv/?parametro1=valor1&parametro2=valor2&parametro3"""
    params = sys.argv[2]
    log("get_plugin_parms " + str(params))

    pattern_params  = re.compile('[?&]([^=&]+)=?([^&]*)')
    options = dict((parameter, urllib.unquote_plus(value)) for (parameter, value) in pattern_params.findall(params))

    log("get_plugin_parms " + repr(options))
    return options


def get_url_decoded(url):
    """This function returns the URL decoded."""
    log('get_url_decoded URL: "%s"' % url)
    return urllib.unquote_plus(url)


def get_url_encoded(url):
    """This function returns the URL encoded."""
    log('get_url_encoded URL: "%s"' % url)
    return urllib.quote_plus(url)


def get_keyboard_text(prompt):
    """This function gets an input text from the keyboard."""
    log('get_keyboard_text prompt: "%s"' % prompt)

    keyboard = xbmc.Keyboard('', prompt)
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        log("get_keyboard_text input text: '%s'" % keyboard.getText())
        return keyboard.getText()
    else:
        return ""


def carga_web(url):
    """This function loads the html code from a webserver and returns it into a string."""
    log('carga_web URL: "%s"' % url)

    MiReq = urllib2.Request(url) # We use the Request method because we need to add a header into the HTTP GET to the web site.
    # We have to tell the web site we are using a real browser.
    MiReq.add_header('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0') # This is a true Firefox header.
    MiConex = urllib2.urlopen(MiReq) # We open the HTTP connection to the URL.
    MiHTML = MiConex.read() # We load all the HTML contents from the web page and store it into a var.
    MiConex.close() # We close the HTTP connection as we have all the info required.

    return MiHTML


def get_redirect(url):
    """This function gets the http redirect address from an URL. This is necesary with some web sites,
    because the former function follows the redirect link, and the info with the video file is missed."""
    log('get_redirect URL: "%s"' % url)

    MiConex = urllib.urlopen(url) # Opens the http connection to the URL.
    MiHTML = MiConex.geturl() # Gets the URL redirect link and stores it into MiHTML.
    MiConex.close() # Close the http connection as we get what we need.

    return MiHTML


def find_multiple(text,pattern):
    """This function allows us to find multiples matches from a regexp into a string."""
    log("find_multiple pattern=" + pattern)

    pat_url_par = re.compile(pattern, re.DOTALL)

    return pat_url_par.findall(text)


def find_first(text,pattern):
    """This function gets back the first match from a regexp into a string."""
    log("find_first pattern=" + pattern)

    pat_url_par = re.compile(pattern, re.DOTALL)
    try:
        return  pat_url_par.findall(text)[0]
    except:
        return ""


def addDir(action = "", title = "", url = "", thumbnail = "", reset_cache = "no"):
    """This function adds a directory entry into the XBMC GUI throught the API."""
    log('addDir action = "%s" url = "%s" thumbnail = "%s" reset_cache = "%s"' % (action, url, thumbnail, reset_cache))

    dir_url = '%s?action=%s&reset_cache=%s&url=%s' % (sys.argv[0], action, reset_cache, urllib.quote_plus(url))
    dir_item = xbmcgui.ListItem(title, iconImage = "DefaultFolder.png", thumbnailImage = thumbnail)
    dir_item.setInfo(type = "Video", infoLabels = {"Title": title})
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = dir_url, listitem = dir_item, isFolder = True)


def addLink(action = "", title = "", plot = "", url = "", thumbnail = ""):
    """This function adds a video link entry into the XBMC GUI throught the API."""
    log("addLink action = [" + action + "] title = [" + title + "] plot = [" + plot + "] url = [" + url + "] thumbnail = [" + thumbnail + "]")

    link_url = '%s?action=%s&url=%s' % (sys.argv[0], action, urllib.quote_plus(url))
    link_item = xbmcgui.ListItem(title, iconImage = "DefaultVideo.png", thumbnailImage = thumbnail)
    link_item.setInfo(type = "Video", infoLabels = {"Title": title, "Plot": plot})
    link_item.setProperty('IsPlayable', 'true')
    return xbmcplugin.addDirectoryItem(handle = int(sys.argv[1]), url = link_url, listitem = link_item, isFolder = False)


def close_dir(pluginhandle, succeeded=True, updateListing=False, cacheToDisc=True):
    """This function closes the directory created with all the item list previously added."""
    log("close_dir pluginhadle: %s updateListing: %s cacheToDisc: %s" % (pluginhandle, updateListing, cacheToDisc))
    xbmcplugin.endOfDirectory(pluginhandle, succeeded=succeeded, updateListing=updateListing, cacheToDisc=cacheToDisc)


def showWarning(message):
    """This funtion shows a popup window with a notices message through the XBMC GUI during 6 secs."""
    log("showWarning message: %s" % message)
    xbmc.executebuiltin('XBMC.Notification(Info:,' + message + '!,6000)')


def play_resolved_url(pluginhandle= "", url = ""):
    """This function plays the video file pointed by the URL passed as argument."""
    log("play_resolved_url pluginhandle = [%s] url = [%s]" % (pluginhandle, url))
    listitem = xbmcgui.ListItem(path=url)
    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
