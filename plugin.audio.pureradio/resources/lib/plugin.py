# _*_ coding: utf-8 _*_

import sys, re, os
from urllib.parse import urlencode, quote_plus, unquote_plus
import xbmcplugin, xbmcaddon, xbmcgui, xbmcaddon, xbmc

class Plugin():

    def __init__(self,  plugin_id='', show_thumb_as_fanart=False):
        self.pluginpath = sys.argv[0]
        self.pluginhandle = int(sys.argv[1])
        self.pluginparams = sys.argv[2]
        self.plugin_id = plugin_id
        self.plugin_type = 'Audio' if 'audio' in plugin_id else 'Music'
        self.debug_enable = True # The debug logs are disabled by default.
        # addon functions
        self.plugin_settings = xbmcaddon.Addon(id=self.plugin_id)
        self.translation = self.plugin_settings.getLocalizedString
        self.root_path = self.plugin_settings.getAddonInfo('path')

    def get_plugin_settings(self):
        """Getter method for settings method"""
        return self.plugin_settings

    def get_plugin_translation(self):
        """Getter method for translation method"""
        return self.translation

    def get_system_language(self):
        """Getter method for language method"""
        return xbmc.getLanguage()

    def set_debug_mode(self, debug_flag=""):
        """ debug mode, see init section """
        self.debug_enable = debug_flag in ("true", True)

    def log(self, message):
        """Logs the messages into the main XBMC log file"""
        if self.debug_enable:
            try:
                xbmc.log(msg=message, level=xbmc.LOGINFO)
            except:
                xbmc.log('%s: log this line is not possible due to encoding string problems' % self.plugin_id, level=xbmc.LOGINFO)

    def _log(self, message):
        """ This method is privated and only called from other methods within the class"""
        if self.debug_enable:
            try:
                xbmc.log(msg=message, level=xbmc.LOGINFO)
            except:
                xbmc.log('%s: _log this line is not possible due to encoding string problems' % self.plugin_id, level=xbmc.LOGINFO)

    def get_plugin_parms(self):
        """This method gets all the parameters passed to the plugin from KODI API and retuns a dictionary"""
        params = sys.argv[2]
        pattern_params  = re.compile('[?&]([^=&]+)=?([^&]*)')
        options = dict((parameter, unquote_plus(value)) for (parameter, value) in pattern_params.findall(params))
        self._log("get_plugin_parms " + repr(options))
        return options

    def get_plugin_path(self, **kwars):
        """Returns the add-on path URL encoded along with all its parameters."""
        return sys.argv[0] + '?' + urlencode(kwars)

    def get_url_decoded(self, url):
        """Returns the URL decoded."""
        self._log('get_url_decoded URL: "%s"' % url)
        return unquote_plus(url)


    def get_url_encoded(self, url):
        """Returns the URL encoded."""
        self._log('get_url_encoded URL: "%s"' % url)
        return quote_plus(url)

    def add_items(self, items, updateListing=False):
        """Adds the list of items (links and folders) to the add-on media list."""
        item_list = []
        for item in items:
            link_item = xbmcgui.ListItem(item.get('info').get('title'))
            thumbnailImage = item.get('thumbnail', '')
            if thumbnailImage:
                link_item.setArt({ 'thumb': thumbnailImage })
            if item.get('IsPlayable', False):
                link_item.setProperty('IsPlayable', 'true')
            link_item.setLabel(item.get('label', item.get('info').get('title')))
            link_item.setLabel2(item.get('label', item.get('info').get('title')))
            link_item.setInfo(type = self.plugin_type, infoLabels = item.get('info'))
            item_list.append((item.get('path'), link_item, not item.get('IsPlayable', False)))
        xbmcplugin.addDirectoryItems(self.pluginhandle, item_list, len(item_list))
        xbmcplugin.endOfDirectory(self.pluginhandle, succeeded=True, updateListing=updateListing, cacheToDisc=True)

    def showWarning(self, message):
        """Shows a popup window in the XBMC GUI for 5 seconds"""
        self._log("showWarning message: %s" % message)
        xbmcgui.Dialog().notification(self.plugin_id, message, xbmcgui.NOTIFICATION_INFO, 6000)

    def play_resolved_url(self, url = ""):
        """Plays the media file pointed by the URL passed as argument."""
        self._log("play_resolved_url pluginhandle = [%s] url = [%s]" % (self.pluginhandle, url))
        listitem = xbmcgui.ListItem(path=url)
        return xbmcplugin.setResolvedUrl(self.pluginhandle, True, listitem)
