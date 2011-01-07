# Copyright 2011 Jonathan Beluch.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import urlparse
import asyncore, socket
import os
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import sys
import pickle
from urllib import quote_plus, unquote_plus, urlencode
from cStringIO import StringIO
from xbmccommon import XBMCDialogCancelled, parse_url_qs, XBMCVideoPluginException
from urlparse import urlparse

class XBMCVideoPluginHandler(object):
    '''This is a base class for a handler.  Subclass this and define
    a run method.'''
    def __init__(self, argv0, argv1, argsdict):
        self.argv0 = argv0
        self.argv1 = int(argv1)
        self.args = argsdict

    def run(self):
        raise NotImplementedError
         

class XBMCVideoPlugin(object):
    '''This is a class to help handle routine tasks for a video plugin
    such as adding directories and/or movies to the UI.'''
    
    def __init__(self, modes, plugin_id=None, default_handler=None, plugin_name='XBMC Video Plugin'):
        self.plugin_id = plugin_id
        self.plugin_name = plugin_name
        self.addon = xbmcaddon.Addon(id=self.plugin_id)
        self.dp = None
        #set the default mode, when the plugin is first called, there will be no qs arguments
        #use user_specified default_handler, else pick the first handler in the modes list
        self.default_handler = default_handler or modes[0][1] 
        self.modes = dict(modes)

        #parse command line parameters into a dictionary
        self.argv0 = sys.argv[0]
        self.argv1 = int(sys.argv[1])

        #parse params from qs, also include the pickled fragment
        self.params = parse_url_qs(sys.argv[2], pickled_fragment=True)

    def getls(self, stringid):
        return self.addon.getLocalizedString(stringid)
            
    def set_resolved_url(self, url):
        li = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(self.argv1, True, li)

    def getString(self, strid):
        return self.addon.getLocalizedString(strid)

    def special_url(self, argv0, params):
        '''Creates a special url resolving this XBMC plugin.  If a val in the params
        dict is not an instance of basestring, it is added to a special dict which will
        then be pickled and placed in the fragment identifier section of the url'''
        pickled = {}
        qs_params = {}
        for key, val in params.items():
            if not(isinstance(val, basestring)):
                #not a string so pickle it
                pickled[key] = val
            else:
                qs_params[key] = val
        #now pickle the pickle dict and add to qs
        return '%s?%s#%s' % (argv0, urlencode(qs_params), quote_plus(pickle.dumps(pickled)))
    
    def make_directory_item(self, d, isfolder=False, make_plugin_url=False):
        url = d.get('url')
        if make_plugin_url:
            url = self.special_url(self.argv0, d)

        li = xbmcgui.ListItem(d.get('name'))

        #Ensure there are items in the info dict or XBMC throws an error
        if 'info' in d.keys() and len(d['info']) > 1: 
            li.setInfo('video', d.get('info'))

        if 'icon' in d.keys(): li.setIconImage(d.get('icon'))
        if 'tn' in d.keys(): li.setThumbnailImage(d.get('tn'))

        if not isfolder:
            li.setProperty('IsPlayable', 'true')

        return (url, li, isfolder)

    def add_resolvable_dirs(self, dirs, end=True):
        _dirs = [self.make_directory_item(d, isfolder=False, make_plugin_url=True) for d in dirs]
        xbmcplugin.addDirectoryItems(self.argv1, _dirs, len(_dirs))
        if end == True: 
            xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)
        
    def add_videos(self, lis, end=True):
        """Takes a list of directory items which will be added as
        videos in the XBMC UI.  Each directory item is a dictionary
        containing the following key/value pairs:
            name = title of the video
            url = url of the video
            info = a dict object with key/val pairs. Info can be found
                in the xbmc documentation (optional)
            icon = url to an icon (optional)
            tn = url to a thumbnail (optional)
        The second parameter the function takes is 'end'.  This
        simply defines whether or not to call 
        xbmcplugin.endOfDirectory()
        """
        #needs to be tested
        #_lis = [self._make_directory_item(li, False) for li in lis]
        _lis = [self.make_directory_item(li, isfolder=True, make_plugin_url=True) for li in lis]
        xbmcplugin.addDirectoryItems(self.argv1, _lis, len(_lis))
        if end == True: 
            xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)   
    
    def add_dirs(self, dirs, end=True):
        """Takes a list of directory items which will be added as
        folders in the XBMC UI.  Each directory item is a dictionary
        containing the following key/value pairs:
            name = title of the list item 
            url = url of the folder contents (usu a link back to the plugin)
            info = a dict object with key/val pairs. Info can be found
                in the xbmc documentation (optional)
            icon = url to an icon (optional)
            tn = url to a thumbnail (optional)
        The second parameter the function takes is 'end'.  This
        simply defines whether or not to call 
        xbmcplugin.endOfDirectory()
        """
        #_dirs = [self._make_directory_item(d, True) for d in dirs]
        _dirs = [self.make_directory_item(d, isfolder=True, make_plugin_url=True) for d in dirs]
        xbmcplugin.addDirectoryItems(self.argv1, _dirs, len(_dirs))
        if end == True: 
            xbmcplugin.endOfDirectory(self.argv1, cacheToDisc=True)
               
    def run(self):
        #use the mode parameter if available, if not use the default handler
        handler = self.default_handler
        mode = self.params.get('mode')
        if mode:
            #verify mode is in the self.modes dict, should we fail silently here and use default?
            assert mode in self.modes.keys(), 'Specified mode %s not found in self.modes' % mode
            handler = self.modes[mode]

        #create instance of the current handler and call its run method
        #current_handler = self.modes[mode](self.argv0, self.argv1, self.params)
        current_handler = handler(self.argv0, self.argv1, self.params)
        try:
            current_handler.run()
        #if there is any kind of non-recoverable error in the process of playing the video
        #raise an instance of XBMCVideoPluginException and a dialog box will be displayed 
        #informing the user
        #python 2.4 except clause syntax
        except XBMCVideoPluginException, e:
            dialog = xbmcgui.Dialog()
            ok = dialog.ok('XBMC', e.value)
        except XBMCDialogCancelled:
            #user cancelled the dialog progress
            pass
