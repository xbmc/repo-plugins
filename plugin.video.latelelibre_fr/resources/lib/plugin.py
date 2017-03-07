# _*_ coding: utf-8 _*_

'''
   plugin: library class for XBMC video add-ons.
   Copyright (C) 2014 José Antonio Montes (jamontes)

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
   These class methods are called from the main add-on module, aimed to ease
   and simplify the add-on development process.
   Release 0.1.3
'''

# First of all We must import all the libraries used for plugin development.
import sys, urllib, re, os
import xbmcplugin, xbmcaddon, xbmcgui, xbmcaddon, xbmc

class Plugin():

    def __init__(self,  plugin_id='', show_thumb_as_fanart=True):
        self.pluginpath = sys.argv[0]
        self.pluginhandle = int(sys.argv[1])
        self.pluginparams = sys.argv[2]
        self.plugin_id = plugin_id
        self.debug_enable = False # The debug logs are disabled by default.
        self.plugin_settings = xbmcaddon.Addon(id=self.plugin_id)
        self.translation = self.plugin_settings.getLocalizedString
        self.root_path = self.plugin_settings.getAddonInfo('path')
        self.fanart_file = os.path.join(self.root_path, "fanart.jpg")
        self.show_thumb_as_fanart = show_thumb_as_fanart


    def get_plugin_settings(self):
        """This is a getter method to return the settings method reference."""
        return self.plugin_settings


    def get_plugin_translation(self):
        """This is a getter method to return the translation method reference."""
        return self.translation


    def get_system_language(self):
        """This method returns the GUI language."""
        return xbmc.getLanguage()


    def set_debug_mode(self, debug_flag=""):
        """This method sets the debug_enable flag to log everything if debug option within add-on settings is activated."""
        self.debug_enable = debug_flag in ("true", True)


    def set_fanart(self):
        """This method setup the file and global plugin fanart."""
        xbmcplugin.setPluginFanart(self.pluginhandle, self.fanart_file)


    def log(self, message):
        """This method logs the messages into the main XBMC log file, only if debug option is activated from the add-on settings.
        This method is called from the main add-on module."""
        if self.debug_enable:
            try:
                xbmc.log(msg=message, level=xbmc.LOGNOTICE)
            except:
                xbmc.log('%s: log this line is not possible due to encoding string problems' % self.plugin_id, level=xbmc.LOGNOTICE)


    def _log(self, message):
        """This method logs the messages into the main XBMC log file, only if debug option is activated from the add-on settings.
        This method is privated and only called from other methods within the class."""
        if self.debug_enable:
            try:
                xbmc.log(msg=message, level=xbmc.LOGNOTICE)
            except:
                xbmc.log('%s: _log this line is not possible due to encoding string problems' % self.plugin_id, level=xbmc.LOGNOTICE)


    def get_plugin_parms(self):
        """This method gets all the parameters passed to the plugin from XBMC API and retuns a dictionary.
        Example: plugin://plugin.video.atactv/?parametro1=valor1&parametro2=valor2&parametro3"""
        params = sys.argv[2]

        pattern_params  = re.compile('[?&]([^=&]+)=?([^&]*)')
        options = dict((parameter, urllib.unquote_plus(value)) for (parameter, value) in pattern_params.findall(params))
        self._log("get_plugin_parms " + repr(options))
        return options


    def get_plugin_path(self, **kwars):
        """This method returns the add-on path URL encoded along with all its parameters."""
        return sys.argv[0] + '?' + urllib.urlencode(kwars)


    def get_url_decoded(self, url):
        """This method returns the URL decoded."""
        self._log('get_url_decoded URL: "%s"' % url)
        return urllib.unquote_plus(url)


    def get_url_encoded(self, url):
        """This method returns the URL encoded."""
        self._log('get_url_encoded URL: "%s"' % url)
        return urllib.quote_plus(url)


    def set_view_mode(self, viewid):
        """This method sets the view mode into the video list."""
        self._log("set_view_mode mode: " + viewid)
        xbmc.executebuiltin('Container.SetViewMode('+viewid+')')


    def set_content_list(self, contents="episodes"):
        """This method sets the video contents for the video list."""
        self._log("set_content_list contents: " + contents)
        xbmcplugin.setContent(self.pluginhandle, contents)


    def set_plugin_category(self, genre=''):
        """This method sets the plugin genre for the video list."""
        xbmcplugin.setPluginCategory(self.pluginhandle, genre)


    def get_keyboard_text(self, prompt):
        """This method gets an input text from the keyboard."""
        self._log('get_keyboard_text prompt: "%s"' % prompt)

        keyboard = xbmc.Keyboard('', prompt)
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            self._log("get_keyboard_text input text: '%s'" % keyboard.getText())
            return keyboard.getText()
        else:
            # Close directory as empty result.
            xbmcplugin.endOfDirectory(self.pluginhandle, succeeded=True, updateListing=False, cacheToDisc=False)
            return ""


    def add_items(self, items, updateListing=False):
        """This method adds the list of items (links and folders) to the add-on video list."""
        item_list = []
        for item in items:
            if item['IsPlayable']: # It is a link
                link_item = xbmcgui.ListItem(item['info']['title'], iconImage = "DefaultVideo.png", thumbnailImage = item['thumbnail'])
                link_item.setInfo(type = "Video", infoLabels = item['info'])
                link_item.setProperty('IsPlayable', 'true')
                link_item.setProperty('Fanart_Image', item['thumbnail'] if self.show_thumb_as_fanart else self.fanart_file)
            else: # It is a folder
                link_item = xbmcgui.ListItem(item['info']['title'], iconImage = "DefaultFolder.png", thumbnailImage = '')
                link_item.setInfo(type = "Video", infoLabels = item['info'])
                link_item.setProperty('Fanart_Image', self.fanart_file)
            item_list.append((item['path'], link_item, not item['IsPlayable']))
        xbmcplugin.addDirectoryItems(self.pluginhandle, item_list, len(item_list))
        xbmcplugin.endOfDirectory(self.pluginhandle, succeeded=True, updateListing=updateListing, cacheToDisc=True)
        #xbmcplugin.setContent(self.pluginhandle, 'episodes')
        xbmcplugin.setContent(self.pluginhandle, 'movies')


    def showWarning(self, message):
        """This method shows a popup window with a notices message through the XBMC GUI during 5 secs."""
        self._log("showWarning message: %s" % message)
        xbmc.executebuiltin('XBMC.Notification(Info:,' + message + ',6000)')


    def play_resolved_url(self, url = ""):
        """This method plays the video file pointed by the URL passed as argument."""
        self._log("play_resolved_url pluginhandle = [%s] url = [%s]" % (self.pluginhandle, url))
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(self.pluginhandle, True, listitem)
