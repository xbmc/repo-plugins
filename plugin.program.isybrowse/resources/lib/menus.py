'''
    ISY Browser for XBMC
    Copyright (C) 2012 Ryan M. Kraus

    LICENSE:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
    DESCRIPTION:
    This Python Module contains classes and functions useful in 
    assembling the XBMC on-screen menus for the ISY Browser addon.
    
    WRITTEN:    11/2012
'''

import xbmcgui
import xbmcplugin

import shared
import images
import urls

class main(object):
    '''
    main(handle, browsing, events_enabled, addr)
    
    DESCRIPTION:
    This class represents the menus for the ISY
    Browser XBMC addon. The inputs required are 
    the handle for the addon run, the browsing
    parameter to specify what the user is 
    currently navigating (None, nodes, programs),
    a boolean value called events_enabled that
    specifies whether the ISY Events addon is
    installed, and the address the user is 
    navigating.
    '''
    listing = []
    browsing = None
    addr = ''
    handle = -1
    events_enabled = False

    def __init__(self, handle, browsing, events_enabled, addr):
        self.browsing = browsing
        self.addr = addr
        self.handle = handle
        self.events_enabled = events_enabled
    
        if browsing == None:
            self._createRoot()
        elif browsing == 'nodes':
            self._createNodes()
        elif browsing == 'programs':
            self._createPrograms()
            
    def _createRoot(self):
        '''
        _createRoot()
        
        DESCRIPTION:
        Creates the root directory.
        '''
        item = {'name': shared.translate(34001), 
            'browsing': 'nodes',
            'node_type': 'folder',
            'context_menu': [],
            'image_key': 'folder',
            'node_addr': None,
            'node_action': None, 
            'node_parent': None}
        self.listing.append(item)
        item = {'name': shared.translate(34002), 
            'browsing': 'programs',
            'node_type': 'folder',
            'context_menu': [],
            'image_key': 'folder',
            'node_addr': None,
            'node_action': None,
            'node_parent': None}
        self.listing.append(item)

        if self.events_enabled:
            item = {'name': shared.translate(34003), 
                'browsing': None,
                'node_type': 'builtin',
                'context_menu': [],
                'image_key': 'folder',
                'node_addr': 'service.script.isyevents',
                'node_action': 'config',
                'node_parent': None}
            self.listing.append(item)
        
    def _createNodes(self):
        '''
        _createNodes()
        
        DESCRIPTION:
        Creates a menu displaying nodes and 
        folders of nodes.
        '''
        # get isy nodes
        nodes = shared.isy.BrowseNodes(self.addr)
        
        # assemble listing
        for name in nodes.keys():
            # pull node basic data
            type = nodes[name][0]
            child = nodes[name][1]
            parent = self.addr
            
            # compile the image key and action commands
            image = type
            action = None
            if type == 'node':
                action = 'toggle'
                status = max([0, float(nodes[name][2])]) / 255.0 * 100
                if status == 0:
                    image += '_0'
                elif status < 20:
                    image += '_20'
                elif status < 40:
                    image += '_40'
                elif status < 60:
                    image += '_60'
                elif status < 80:
                    image += '_80'
                else:
                    image += '_100'
            elif type == 'group':
                action = 'on'
                
            # compile the context menu
            context = createContext(type != 'folder', type == 'node', type =='node', False)
            
            self.listing.append({'name': name, 
                'image_key': image, 
                'node_addr': child, 
                'node_type': type, 
                'node_action': action, 
                'node_parent': parent,
                'context_menu': context,
                'browsing': 'nodes'})
        
    def _createPrograms(self):
        '''
        _createPrograms()
        
        DESCRIPTION:
        Creates a menu containing programs and
        folders containing programs.
        '''
        # get isy programs
        nodes = shared.isy.BrowsePrograms(self.addr)
        
        # assemble listing
        for name in nodes.keys():
            # pull node basic data
            type = nodes[name][0]
            child = nodes[name][1]
            parent = self.addr
            
            # compile the image key and action commands
            image = type
            action = None
            if type=='program':
                action = 'run'
                
            # compile the context menu
            context = createContext(False, False, False, type != 'folder', True)
            
            self.listing.append({'name': name, 
                'image_key': image, 
                'node_addr': child, 
                'node_type': type, 
                'node_action': action, 
                'node_parent': parent,
                'context_menu': context,
                'browsing': 'programs'})
        
    def sendToXbmc(self):
        '''
        sendToXbmc()
        
        DESCRIPTION:
        Sends the menu to XBMC.
        '''
        for item in self.listing:
            # create item to add to menu
            icon = images.getImage(item['image_key'])
            listItem = xbmcgui.ListItem(item['name'], iconImage=icon)
            
            # assemble link url
            params = shared.__params__
            params['addr'] = item['node_addr']
            params['type'] = item['node_type']
            params['cmd'] = item['node_action']
            params['parent'] = item['node_parent']
            params['browsing'] = item['browsing']
            url = urls.CreateUrl(shared.__path__, **params)
                
            # create the item's context menu
            context = []
            for context_item in item['context_menu']:
                context_url = urls.CreateUrl(
                    shared.__path__,
                    addr=item['node_addr'],
                    type=item['node_type'],
                    cmd=context_item[1], 
                    parent=item['node_parent'])
                context.append((context_item[0], 'XBMC.RunPlugin(' + context_url + ')'))
                
            listItem.addContextMenuItems(context, replaceItems=True)
            
            # add item to menu
            xbmcplugin.addDirectoryItem(
                handle=self.handle, 
                url=url, 
                listitem=listItem, 
                isFolder=item['node_action']==None)

    def show(self):
        '''
        show()
        
        DESCRIPTION:
        Shows the menu on the screen.
        '''
        xbmcplugin.endOfDirectory(handle=self.handle, updateListing=False, cacheToDisc=False)
       
def createContext(onoff=False, toggle=False, dim=False, run=False, program=False):
    '''
    createContext(onoff, dim, run)
    
    DESCRIPTION:
    Creates a context menu for a menu item.
    There are four sections to a context menu
    that can be toggled by input. There is the
    On/Off section, the Dim Controls section,
    the Program Run section, and the Show Info
    section.
    '''
    # max items = 10
    menu = []
    
    if onoff:
        new_items = [
            (shared.translate(32001), 'on'), 
            (shared.translate(32002), 'off'),  
            (shared.translate(32004), 'faston'), 
            (shared.translate(32005), 'fastoff')]
        for item in new_items:
            menu.append(item)
            
    if toggle:
        new_items = [
            (shared.translate(32003), 'toggle')]
        for item in new_items:
            menu.append(item)
            
    if dim:
        new_items = [
            #(shared.translate(32006), 'bright'), 
            #(shared.translate(32007), 'dim'),
            (shared.translate(32008), 'on25'),
            (shared.translate(32009), 'on50'),
            (shared.translate(32010), 'on75'),
            (shared.translate(32011), 'on100')]
        for item in new_items:
            menu.append(item)
    
    if run:
        new_items = [
            (shared.translate(32013), 'run'), 
            (shared.translate(32014), 'then'), 
            (shared.translate(32015), 'else')]
        for item in new_items:
            menu.append(item)
    
	if program:
		menu.append((shared.translate(32012), 'pinfo'))
	else:
		menu.append((shared.translate(32012), 'info'))
	
    return menu