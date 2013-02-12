#     Copyright 2011 Joachim Basmaison, Cyril Leclerc
#
#     This file is part of xbmc-qobuz.
#
#     xbmc-qobuz is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     xbmc-qobuz is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.   See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with xbmc-qobuz.   If not, see <http://www.gnu.org/licenses/>.

import xbmcplugin
import xbmcgui

from progress import Progress
import time
from debug import log
from gui.util import lang
from exception import QobuzXbmcError as Qerror

class Directory():
    """This class permit to add item to Xbmc directory or store nodes 
        that we retrieve while building our tree
        
        Parameters:
        root: node, The root node
        nodeList: list, list of node (empty list by default)
        
        Named parameters:
            withProgress: bool, if set to false no Xbmc progress is displayed
        
        Note: After init you can set some optional parameters:
            asList: Don't put item to Xbmc Directory
            replaceItem: When attaching context menu to item, control if
                we are replacing Xbmc Default menu
    """
    def __init__(self, root, nodeList = [], **ka):
        self.nodes = []
        self.label = "Qobuz Progress / "
        self.root = root
        self.asList = False
        self.handle = None
        self.put_item_ok = True
        withProgress = True
        if 'withProgress' in ka:
            if ka['withProgress']:
                withProgress = True
            else:
                withProgress = False
        self.Progress = Progress(withProgress)
        self.total_put = 0
        self.started_on = time.time()
        self.Progress.create(self.label + root.get_label())
        self.update({'count': 0, 'total':100}, lang(40000))
        self.line1 = ''
        self.line2 = ''
        self.line3 = ''
        self.percent = 0
        self.content_type = 'files'
        self.nodes = nodeList
        self.replaceItems = False
        self.asLocalURL = False

    def __del__(self):
        """Cleaning our tree on delete
            @attention: may be useless
        """
        try:
            for node in self.nodes:
                node.delete_tree()
            self.nodes = None
            self.root.delete_tree()
            self.root = None
        except:
            print "Something went wrong while deleting tree"
        
            
    def elapsed(self):
        """Return elapsed time since directory has been created
        """
        return time.time() - self.started_on

    def add_node(self, node):
        """Adding node to node list if asList=True or putting item
        into Xbmc directory
        * @attention: broken, Raise exception if user has canceled progress
        """
        if self.Progress.iscanceled():
            raise Qerror(who=self, what="build_down_canceled")
            return False
        if self.asList:
            self.nodes.append(node)
            self.total_put += 1
            return True
        return self.__add_node(node)
       
    def __add_node(self, node):
        """Helper: Add node to xbmc.Directory
            Parameter:
            node: node, node to add
        """
        if self.is_canceled() : 
            return False
        item = node.makeListItem(replaceItems=self.replaceItems)
        if not item:
            return False
        url = node.make_url(asLocalURL=self.asLocalURL)
        if not self.add_to_xbmc_directory(url=url,
                                item=item,
                                is_folder=node.is_folder):
            self.put_item_ok = False
            return False
        return True

    def update(self, gData, line1, line2='', line3=''):
        """Update progress bar associated with this directory
        
            Parameters:
            gData: Dictionary object that keep information across call
            line1: progress line 1
            line2: progress line 2
            line3: progress line 3
        """
        percent = 100
        total = gData['total']
        count = gData['count']
        if total and count:
            percent = count * (1 + 100 / total)
        else:
            percent = count
            if percent > 100:
                percent = 100
        labstat = '[%05i]' % (self.total_put)
        self.line1 = labstat
        self.line2 = line2
        self.line3 = line3
        self.percent = percent
        line1 = "[%05i] %s" % (self.total_put, line1)
        self.Progress.update(percent, line1, line2, line3)
        return True

    def is_canceled(self):
        """Return is_canceled value from our progress dialog
        """
        return self.Progress.iscanceled()

    def _xbmc_item(self, **ka):
        """Make xbmc item
            Named parameters:
                label: string, label for this item
                image: string, image for this item
                url  : string, url for this item
        """
        return xbmcgui.ListItem(
            ka['label'],
            ka['label'],
            ka['image'],
            ka['image'],
            ka['url'])

    def add_to_xbmc_directory(self, **ka):
        """Add item to Xbmc Directory
            Named parameters:
                url: string
                item: xbmc.ListItem
                is_folder: bool
        """
        if not xbmcplugin.addDirectoryItem(self.handle,
                                    ka['url'],
                                    ka['item'],
                                    ka['is_folder'],
                                    self.total_put):
            return False
        self.total_put += 1    
        return True

    def close(self):
        """Close our directory
            * close progress dialog ...
        """
        if self.Progress:
            self.Progress.close()
            self.Progress = None

    def end_of_directory(self, forceStatus=None):
        """This will tell xbmc that our plugin has finished, and that
        he can display our items
        """
        success = True
        if forceStatus != None:
            success = forceStatus
        if not self.put_item_ok or (self.total_put == 0):
            success = False
        if not self.asList:
            xbmcplugin.setContent(
                                  handle=self.handle, 
                                  content=self.content_type)
            xbmcplugin.endOfDirectory(handle=self.handle,
                                  succeeded=success,
                                  updateListing=False,
                                  cacheToDisc=success)
        self.update({'count': 100, 'total':100}, lang(40003), 
                    "%s : %s items" % (lang(40002), str(self.total_put)))
        self.close()
        return self.total_put

    def set_content(self, content):
        """Set Xbmc directory content
        """
        self.content_type = content
